from typing import List, Dict, Union, Tuple, Set, Any
from collections import OrderedDict
import csv
from testvector import TestVector, TestVectorGenerator
from dataclasses import dataclass
from contextlib import contextmanager
from collections import OrderedDict
from nodes import *
from nodes import Node, Gate, FlipFlop, Value, DummyNode
from faults import Fault
from re import match
import itertools
import functools
import exceptions


def generate_line(node: Node) -> str:
    return node.type.ljust(11) + node.name.ljust(8) + \
           (node.gate.type.ljust(8) if node.gate.type else "" + ', '.join(node.input_nodes)).ljust(20) + \
           str(node.value).ljust(3)


class CircuitSimulator:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        gates = self.LineParser(kwargs['bench']).parse_file()
        self.nodes = self.compile(gates)
        self.faulty_node: Optional[Node, DummyNode]
        self.relevant_nodes: Set[Node] = set()
        # self.relevant_nodes: List[Node] = []

    def __iter__(self):
        self.iteration = itertools.count()
        # self.relevant_nodes = self.nodes.input_nodes.values()
        return self

    def __next__(self):
        if next(self.iteration) < self.cycle_resolution_length:
            relevant_node_set = self.relevant_nodes
            # relevant_node_set = set(self.relevant_nodes)
            # relevant_node_set.difference_update(
            #     output_node for node in relevant_node_set.copy()
            #     for output_node in node.output_nodes
            #     # if node.value is value_U
            # )
            for node in relevant_node_set:
                node.logic()
            for node in relevant_node_set:
                node.update()

            self.relevant_nodes = {
                output_node for node in self.relevant_nodes
                for output_node in node.output_nodes
            }

        else:
            # self.relevant_nodes.clear()
            raise StopIteration

    def __str__(self):
        return itertools.accumulate((f"{node}\n" for node in self.nodes))

    def apply_vector(self, test_vector: TestVector):
        self.relevant_nodes = {
            node for node in (
                output_node for input_node in
                self.nodes.input_nodes.values()
                for output_node in input_node.output_nodes
            )
        }
        for input_node, value in zip(self.nodes.input_nodes.values(), test_vector):
            input_node.value = value
            input_node.vector_assignment = value

    @staticmethod
    def compile(gates: 'LineParser.Gates') -> 'CircuitSimulator.Nodes':
        nodes_instance = CircuitSimulator.Nodes()
        nodes_map = {"INPUT": nodes_instance.input_nodes, "OUTPUT": nodes_instance.output_nodes}
        for name, gate in gates.gates.items():
            node = Node(gate)
            nodes_map.get(gate.type, nodes_instance.intermediate_nodes)[name] = node
        for name, input_names in gates.inputs.items():
            nodes_instance[name].input_nodes = [nodes_instance[input_name] for input_name in input_names]
            for input_name in input_names:
                nodes_instance[input_name].output_nodes.append(nodes_instance[name])

        nodes_instance.flip_flops = {node for node in nodes_instance if isinstance(node, FlipFlop)}
        return nodes_instance

    @staticmethod
    def local_faults(node: Node) -> List[Fault]:
        faults = [Fault(node, Value(0)), Fault(node, Value(1))]
        faults.extend([
            fault for faults in (
                (Fault(node, Value(0), input_node), Fault(node, Value(1), input_node))
                for input_node in node.input_nodes
            )
            for fault in faults
        ])
        return faults

    @functools.cached_property
    def faults(self) -> Set[Fault]:
        faults = {
            fault for faults in
            (self.local_faults(node) for node in self.nodes)
            for fault in faults
        }
        with open("_%s_faults.txt" % self.kwargs['bench'], 'w') as f:
            for fault in faults:
                f.write("%s, " % fault)
        return faults

    @functools.cached_property
    def cycle_resolution_length(self) -> int:
        """How many nodes must be traversed for the cycle to be resolved"""
        count = itertools.count()
        frontier_nodes: Set[Node] = set(self.nodes.input_nodes.values())
        # frontier_nodes = self.nodes.input_nodes.values()
        while frontier_nodes:
            next(count)
            frontier_nodes = {
                node for output_nodes in
                (node.output_nodes for node in frontier_nodes)
                for node in output_nodes
                # if node is not value_U
            }
        return next(count) + 5

    @functools.cached_property
    def flip_flop_resolution_length(self) -> int:
        """How many cycles must be run for a fault to be detected in any flip flop"""
        return max([
                       self._flip_flop_length(flip_flop)
                       for flip_flop in self.nodes.flip_flops
                   ] + [0])

    def _flip_flop_length(self, flip_flop: FlipFlop) -> int:
        """How many cycles must be run for a fault to be detected in the given fault"""
        lengths = []
        frontier_nodes: List[Node] = flip_flop.output_nodes
        traversed_flip_flops: Set[FlipFlop] = {flip_flop}
        for node in frontier_nodes:
            if isinstance(node, FlipFlop):
                lengths.append(self._flip_flop_length(node))
                if node in traversed_flip_flops:
                    raise RuntimeError("A fault would require infinite cycles to be detected")
                traversed_flip_flops.add(node)
            else:
                frontier_nodes.extend(node.output_nodes)
        return max(lengths) if lengths else 1

    @functools.singledispatchmethod
    def induce_fault(self, fault) -> None:
        raise NotImplementedError

    @induce_fault.register
    def _(self, fault: str):
        parameters = fault.split('-')
        node = self.nodes[parameters[0]]
        input_node = self.nodes[parameters[1]] \
            if parameters[2] else None
        stuck_at = Value(int(
            parameters[2] if parameters[2] else parameters[1]
        ))
        if not (stuck_at is Value(0) or stuck_at is Value(1)):
            raise ValueError(f"Invalid stuck-at value: {stuck_at}")
        self.induce_fault(Fault(node, stuck_at, input_node))

    @induce_fault.register
    def _(self, fault: Fault):
        self.fault = fault # for debugging
        if fault.input_node:
            dummy_node = DummyNode(fault.node, fault.input_node, fault.stuck_at)
            fault.node.input_nodes.remove(fault.input_node)
            fault.node.input_nodes.append(dummy_node)
            self.faulty_node = dummy_node
            self.relevant_nodes.add(dummy_node)
            # self.relevant_nodes.append(dummy_node)
        else:
            fault.node.stuck_at = fault.stuck_at
            self.faulty_node = fault.node
            # self.relevant_nodes.append(fault.node)
            self.relevant_nodes.add(fault.node)

    def undo_faults(self):
        self.faulty_node.undo_fault()
        if isinstance(self.faulty_node, DummyNode):
            # self.relevant_nodes.append(self.faulty_node.output_nodes[0])
            self.relevant_nodes.add(self.faulty_node.output_nodes[0])
        else:
            # self.relevant_nodes.append(self.faulty_node)
            self.relevant_nodes.add(self.faulty_node)

    def detect_fault(self, fault: Fault) -> bool:
        # self.undo_faults()
        self.induce_fault(fault)
        self.cycle()
        for output_node in self.nodes.output_nodes.values():
            if output_node.value is value_D or output_node.value is value_DP:
                self.undo_faults()
                return True
        self.undo_faults()
        return False

    # @functools.lru_cache(100)
    def detect_faults(self, test_vector: TestVector) -> List[Fault]:
        self.apply_vector(test_vector)
        return [fault for fault in self.faults if self.detect_fault(fault)]


    def detect_and_eliminate_faults(self, test_vector: TestVector, faults: Set[Fault]) -> Set[Fault]:
        self.apply_vector(test_vector)
        detected_faults = {fault for fault in faults if self.detect_fault(fault)}
        faults.difference_update(detected_faults)
        return detected_faults

    @dataclass
    class Result:
        remaining_faults: Set[Fault]
        fault_coverage_all: List  # [TestVector, List[Fault]]
        fault_coverage_list: List  # [TestVector, List[Fault]]

    def run_batch(self, seed: int, taps: Set[int], get_all_coverage=True, get_list_coverage=True) \
            -> Result:
        input_bits = len(self.nodes.input_nodes)
        test_vectors = TestVectorGenerator(seed, input_bits, taps)() if taps else \
            TestVectorGenerator.from_counter(seed, input_bits)
        test_vectors = [test_vector[:input_bits] for test_vector in test_vectors]
        remaining_faults = self.faults.copy()
        fault_coverage_all: List[Tuple[TestVector, List[Fault]]] = []
        fault_coverage_list: List[Tuple[TestVector, List[Fault]]] = []
        tv: TestVector
        faults: List[Fault]
        if get_all_coverage:
            fault_coverage_all = [
                (tv, faults) for (tv, faults) in (
                    (test_vector, self.detect_faults(test_vector))
                    for test_vector in test_vectors
                )
            ]
        if get_list_coverage:
            fault_coverage_list = [
                (tv, faults) for (tv, faults) in (
                    (test_vector, self.detect_and_eliminate_faults(test_vector, remaining_faults))
                    for test_vector in test_vectors
                )
            ]
        # if get_all_coverage:
        #     fault_coverage_all = [
        #         (tv, faults) for (tv, faults) in
        #         ((test_vector, self.detect_faults(test_vector, self.faults))
        #         for test_vector in test_vectors)
        #     ]
        # if get_list_coverage:
        #     fault_coverage_list =[ test_vector, faults for test_vector, faults in (
        #         [test_vector, self.detect_and_eliminate_faults(test_vector, remaining_faults)]
        #         for test_vector in test_vectors
        #     )
        # fault_coverage_all: OrderedDict[TestVector, List[Fault]]
        # fault_coverage_list: OrderedDict[TestVector, List[Fault]]
        # if get_all_coverage:
        #     fault_coverage_all = OrderedDict([
        #         (test_vector, self.detect_faults(test_vector, self.faults))
        #         for test_vector in test_vectors
        #     ])
        # if get_list_coverage:
        #     fault_coverage_list = OrderedDict([
        #         (test_vector, self.detect_and_eliminate_faults(test_vector, remaining_faults))
        #         for test_vector in test_vectors
        #     ])

        return self.Result(remaining_faults, fault_coverage_all, fault_coverage_list)

    @dataclass
    class Batch:
        name: str
        seed: int
        taps: []

    def cycle(self) -> None:
        for iteration in self:
            pass

    class IterationPrinter:
        def __init__(self, _nodes: List[Node]):
            self.iteration = itertools.count()
            header = "Type".ljust(8) + "Variable".ljust(11) + "Logic".ljust(8) + \
                     "Inputs".ljust(9) + "Initial".ljust(3)
            self.lines = [header] + [generate_line(node) for node in _nodes]

        def __iter__(self):
            for line in self.lines:
                yield line

        def __str__(self):
            return itertools.accumulate((line + '\n' for line in self))

        def __call__(self, _nodes: List[Node]):
            self.lines[0] += '\t' + next(self.iteration)
            for node, index in zip(_nodes, itertools.count(1)):
                self.lines[index] += '\t' + str(node.value)

    class LineParser:
        @dataclass
        class Gates:
            gates: Dict[str, Gate]
            inputs: Dict[str, List[str]]

        def __init__(self, bench):
            self.file = bench
            self.pattern_gate = "(\S+) = ([A-Z]+)\((.+)\)"
            self.pattern_io = "([A-Z]+)\((.+)\)"
            self.gates: Dict[str, Gate] = {}
            self.inputs: Dict[str, List[str]] = {}
            self.types: Dict[str, str] = {}
            self.gate_map = {"AND": AndGate, "OR": OrGate, "NAND": NandGate, "XNOR": XnorGate,
                             "NOR": NorGate, "BUFF": BuffGate, "XOR": XorGate, "NOT": NotGate,
                             "DFF": FlipFlop}

        def parse_file(self) -> Gates:
            with open(self.file) as f:
                for line in f:
                    self.parse_line(line)
            for name, gate in self.gates.items():
                gate.type = self.types.get(name, '')
            return self.Gates(self.gates, self.inputs)

        def parse_line(self, line: str):
            if line.startswith('#') or line == '\n':
                pass
            elif groups := match(self.pattern_gate, line):
                name = groups.group(1)
                inputs = groups.group(3).split(', ')
                gate_type = self.gate_map[groups.group(2)]
                self.gates[name] = gate_type(name)
                self.inputs[name] = inputs
            elif groups := match(self.pattern_io, line):
                io = groups.group(1)
                name = groups.group(2)
                self.types[name] = io
                self.gates.setdefault(name, Gate(name))
                if not io == "INPUT" and not io == "OUTPUT":
                    raise exceptions.ParseLineError(line)
            else:
                raise exceptions.ParseLineError(line)

    class Nodes:
        def __init__(self):
            self.input_nodes: Dict[str, Node] = {}
            self.intermediate_nodes: Dict[str, Node] = {}
            self.output_nodes: Dict[str, Node] = {}
            # self.dummy_nodes: List[DummyNode] = []
            # self.faulty_nodes: List[Node] = []
            self.flip_flops: Set[FlipFlop] = set()

        @functools.cached_property
        def _nodes(self) -> Dict[str, Node]:
            return {**self.input_nodes, **self.intermediate_nodes, **self.output_nodes}

        def __contains(self, item: str):
            return True if self._nodes.get(item) else False

        def __getitem__(self, item: str):
            return self._nodes[item]

        def __iter__(self) -> Node:
            for node in self._nodes.values():
                yield node
            # for node in self.dummy_nodes:
            #     yield node

        def __str__(self):
            return str({
                "input_nodes": self.input_nodes,
                "intermediate_nodes:": self.intermediate_nodes,
                "output_nodes": self.output_nodes,
                # "faulty_nodes": self.faulty_nodes,
                "flip_flops": self.flip_flops
            })

        def __repr__(self):
            return ', '.join(
                [repr(node) for node in (self._nodes.values())]  # +
                # [repr(node) for node in self.dummy_nodes]
            )
