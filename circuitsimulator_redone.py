from collections import defaultdict
import collections
from faults import *
from nodes import *
from testvector import *
from re import match
import itertools
import functools
import exceptions
from typing import Optional, DefaultDict, List, OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass


def propagate(path: Iterable[Set[Node]]):
    for nodes in path:
        for node in nodes:
            node.logic()
        for node in nodes:
            node.update()


class CircuitSimulator:
    def __init__(self, **kwargs):
        self.faulty_node: Optional[Node, InputFault] = Node
        self.fault: Optional[Fault] = None
        self.tv_lookup: DefaultDict[TestVector, Set[Fault]] = defaultdict(set)
        self.nodes: CircuitSimulator.Nodes
        self.kwargs = kwargs
        self.compile( self.LineParser(kwargs['bench']).parse_file() )
        self.tv: Union[None, TestVector] = None

    @staticmethod
    def local_faults(node: Node) -> List[Fault]:
        """Node SA-0 and SA-1, and on input fault if the input node has fanout"""
        faults = [Fault(node, Value(0)), Fault(node, Value(1))]
        faults.extend(
            fault for faults in (
                (Fault(node, Value(0), input_node), Fault(node, Value(1), input_node))
                for input_node in node.input_nodes
            )
            for fault in faults
        )
        return faults

    @functools.cached_property
    def faults(self) -> Set[Fault]:
        """Full fault list of current circuit"""
        return {
            fault for faults in
            (self.local_faults(node) for node in self.nodes)
            for fault in faults
        }

    # @staticmethod
    def propagate(self, path: Iterable[Set[Node]]):
        # TODO: If you want to have a pretty printout of values you can uncomment self.iteration_printer
        # self.iteration_printer = self.IterationPrinter(self.tv, self.fault, self.nodes)
        for nodes in path:
            for node in nodes:
                node.logic()
            for node in nodes:
                node.update()
            # self.iteration_printer(self.nodes)
        # print(self.iteration_printer)


    @staticmethod
    def propagate_generator(path: Iterable[Set[Node]]) -> Generator[Set[Node], None, None]:
        for nodes in path:
            for node in nodes:
                node.logic()
            for node in nodes:
                node.update()
            yield nodes


    def apply_vector(self, test_vector: TestVector):
        self.tv = test_vector
        for node, value in zip(self.nodes.input_nodes.values(), test_vector):
            node.vector_assignment = value
            node.value = value
        self.propagate(self.nodes.input_propagation_path)

    @contextmanager
    def apply_fault(self, fault: Fault) -> Generator[Value, None, None]:
        self.fault = fault
        if fault.input_node:
            self.nodes.faulty_node = InputFault(fault.node, fault.input_node, fault.stuck_at)
        else:
            fault.node.stuck_at = fault.stuck_at
            self.nodes.faulty_node = fault.node
        backtrack = [nodes for nodes in self.propagate_generator(self.nodes.faulty_node.fault_propagation_path)]
        yield
        self.nodes.faulty_node.local_reset()
        # TODO: Use an integer to specify how many sets should be traversed
        self.propagate(backtrack)


    def detect_fault(self, fault: Fault) -> bool:
        with self.apply_fault(fault):
            return any(node.value.propagates_fault for node in self.nodes.output_nodes.values())

    def detect_faults(self, tv: TestVector) -> List[Fault]:
        self.apply_vector(tv)
        self.propagate(self.nodes.input_propagation_path)
        return [fault for fault in self.faults if self.detect_fault(fault)]

    def detect_and_eliminate_faults(self, tv: TestVector, faults: Set[Fault]) -> List[Fault]:
        known_faults = self.tv_lookup[tv]
        detected_faults = faults.intersection(known_faults)
        undetected_faults = faults.difference(known_faults)
        self.apply_vector(tv)
        detected_faults.update(fault for fault in undetected_faults if self.detect_fault(fault))
        faults.difference_update(detected_faults)
        return list(detected_faults)

    @dataclass
    class Result:
        """Class for keeping track of the results of a batch"""
        remaining_faults: Set[Fault]
        fault_coverage_all: List
        fault_coverage_list: List

        def __init__(self, remaining_faults, fault_coverage_all, fault_coverage_list):
            self.remaining_faults = remaining_faults
            self.fault_coverage_all = fault_coverage_all
            self.fault_coverage_list = fault_coverage_list

    def run_batch(self, seed: int, taps: Set[int], lookup_dict: Dict[TestVector, Set[Fault]] = None,
                  get_all_coverage=True, get_list_coverage=True, sequential=False) -> Result:
        """
        taps = {} -> counter is used
        taps = {1} -> LFSR with no taps is used
        taps = {2, 3, 5} -> LFSR with taps at 2, 3, and 5 is used
        """
        if lookup_dict is None:
            lookup_dict = {}
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
                (test_vector, self.detect_faults(test_vector))
                for test_vector in test_vectors
            ]
        if get_list_coverage:
            fault_coverage_list = [
                (test_vector, self.detect_and_eliminate_faults(test_vector, remaining_faults))
                for test_vector in test_vectors
            ]
        return self.Result(remaining_faults, fault_coverage_all, fault_coverage_list)

    # TODO: 1 cycle with fault, 1 cycle without fault, fault is detected if the PO + FF is different

    class IterationPrinter:
        """Compact printout of the circuit values"""

        class Line:
            len_type: int
            len_name: int
            len_logic: int
            len_inputs: int
            len_initial: int

            def __init__(self, _type: str, name: str, logic: str, inputs: str, initial: str):
                self.type = _type
                self.name = name
                self.logic = logic
                self.inputs = inputs
                self.values: List[str] = [initial]

            def __call__(self, value: str):
                self.values.append(value)

            def __str__(self):
                return self.type.ljust(self.len_type) + \
                       self.name.rjust(self.len_name) + \
                       self.logic.rjust(self.len_logic) + \
                       self.inputs.rjust(self.len_inputs) + \
                       self.values[0].rjust(self.len_initial) + \
                       (''.join(str(value).rjust(6) for value in self.values[1:])).ljust(120)

            @classmethod
            def from_node(cls, node: Node):
                inputs = ', '.join(node.name for node in node.input_nodes)
                return cls(node.type, node.name, node.gate.type, inputs, str(node.value))

        @staticmethod
        def justify_length(strings: Iterable[str]):
            round_up_nearest_tab = (lambda s: len(s) // 4 * 4 + (4 if len(s) % 4 else 0))
            return max(round_up_nearest_tab(string) for string in strings) + 4

        def __init__(self, test_vector: TestVector, fault: Fault, _nodes: Iterable[Node]):
            self.iteration = itertools.count()
            next(self.iteration)
            self.fault = fault
            self.tv = test_vector
            self.detected = False
            self.lines = [self.Line('Type', 'Variable', 'Logic', 'Inputs', 'Initial')]
            self.lines.extend(self.Line.from_node(node) for node in _nodes)
            self.Line.len_type = self.justify_length(line.type for line in self.lines)
            self.Line.len_name = self.justify_length(line.name for line in self.lines)
            self.Line.len_logic = self.justify_length(line.logic for line in self.lines)
            self.Line.len_inputs = self.justify_length(line.inputs for line in self.lines)
            self.Line.len_initial = self.justify_length(line.values[0] for line in self.lines)

        def __str__(self):
            return '\n'.join((
                f"{self.tv}: {self.fault} {'detected' if self.detected else 'undetected'}",
                *(str(line) for line in self.lines)
            ))

        def __call__(self, _nodes: Iterable[Node]):
            """For each node in the circuit, append the value to the printout if it has changed"""
            self.lines[0].values.append(next(self.iteration))
            for line, node in zip(self.lines[1:], _nodes):
                value = str(node.value)
                try:
                    prev_value = next((
                        line_value for line_value in line.values[::-1] if line_value
                    ))
                except StopIteration:
                    prev_value = None
                if prev_value != value:
                    line.values.append(value)
                else:
                    line.values.append('')

        def give_result(self, detected: bool):
            self.detected = detected

    class LineParser:
        @dataclass
        class Gates:
            # gates: OrderedDict[str, Gate]
            gates: OrderedDict[str, Gate]
            inputs: Dict[str, List[str]]
            node_types: Dict[str, str]

            def __init__(self, gates, inputs, node_types):
                self.gates = gates
                self.inputs = inputs
                self.node_types = node_types

        @functools.cached_property
        def gate_map(self):
            return {"AND": AndGate, "OR": OrGate, "NAND": NandGate, "XNOR": XnorGate,
                    "NOR": NorGate, "BUFF": BuffGate, "XOR": XorGate, "NOT": NotGate,
                    "DFF": FlipFlop}

        def __init__(self, bench):
            self.file = bench
            self.pattern_gate = "(\S+) = ([A-Z]+)\((.+)\)"
            self.pattern_io = "([A-Z]+)\((.+)\)"
            self.gates: OrderedDict[str, Gate] = collections.OrderedDict()
            self.inputs: Dict[str, List[str]] = {}
            self.node_types: Dict[str, str] = {}

        def parse_file(self) -> Gates:
            """Parse a circuit bench file"""
            with open(self.file) as f:
                for line in f:
                    self.parse_line(line)
            return self.Gates(self.gates, self.inputs, self.node_types)

        def parse_line(self, line: str):
            """Parse a circuit bench line"""
            if line.startswith('#') or line == '\n':
                pass
            elif groups := match(self.pattern_gate, line):
                # Line matches the format
                # name = GATE(input, input)
                name = groups.group(1)
                inputs = groups.group(3).split(', ')
                gate_type = self.gate_map[groups.group(2)]
                self.gates[name] = gate_type(name)
                self.inputs[name] = inputs
            elif groups := match(self.pattern_io, line):
                # Line matches the format
                # INPUT/OUTPUT(name)
                io = groups.group(1)
                name = groups.group(2)
                self.gates.setdefault(name, Gate(name))
                self.node_types[name] = io
                if not io == "INPUT" and not io == "OUTPUT":
                    raise exceptions.ParseLineError(line)
            else:
                raise exceptions.ParseLineError(line)

    def compile(self, gates: LineParser.Gates):
        self.nodes = CircuitSimulator.Nodes()
        for name, gate in gates.gates.items():
            node = Node(gate)
            node.type = gates.node_types.get(name, "INTERM.")
            if node.type == "INTERM.":
                self.nodes.intermediate_nodes[name] = node
            elif node.type == "INPUT":
                self.nodes.input_nodes[name] = node
            elif node.type == "OUTPUT":
                self.nodes.output_nodes[name] = node
            if node.gate.type == "DFF":
                self.nodes.flip_flops.append(node)
        for name, input_names in gates.inputs.items():
            self.nodes[name].input_nodes = [self.nodes[input_name] for input_name in input_names]
            for input_name in input_names:
                self.nodes[input_name].output_nodes.append(self.nodes[name])
        for name, node_type in gates.node_types.items():
            self.nodes[name].type = node_type
        pass

    class Nodes:
        """A structure of nodes allowing for finding a Node by name, or iterating across specific node types"""

        def __init__(self):
            self.input_nodes: OrderedDict[str, Node] = collections.OrderedDict()
            self.intermediate_nodes: Dict[str, Node] = {}
            self.output_nodes: OrderedDict[str, Node] = collections.OrderedDict()
            self.flip_flops: List[Node] = []
            self.faulty_node: Union[InputFault, Node, None] = None

        def capture(self):
            for flip_flop in self.flip_flops:
                flip_flop.gate.capture()

        @functools.cached_property
        def _nodes(self) -> Dict[str, Node]:
            return {**self.input_nodes, **self.intermediate_nodes, **self.output_nodes}

        @functools.cached_property
        def scan_in_nodes(self) -> List[Union[Node, InputFault]]:
            return [*self.input_nodes.values(), *self.flip_flops]

        @functools.cached_property
        def scan_out_nodes(self) -> List[Union[Node, InputFault]]:
            return [*self.output_nodes.values(), *self.flip_flops]


        def __contains(self, item: str):
            return True if self._nodes.get(item) else False

        def __getitem__(self, item: str):
            return self._nodes[item]

        def __iter__(self) -> Node:
            for node in self._nodes.values():
                yield node

        def __str__(self):
            return str({
                "input_nodes": self.input_nodes,
                "intermediate_nodes:": self.intermediate_nodes,
                "output_nodes": self.output_nodes,
                "flip_flops": self.flip_flops
            })

        def __repr__(self):
            return ', '.join(repr(node) for node in self._nodes.values())

        @functools.cached_property
        def input_propagation_path(self) -> List[Set[Node]]:
            result = [frontier := {
                output_node for node
                in self.input_nodes.values()
                for output_node in node.output_nodes
            }]
            while (frontier := {
                output_node for node
                in frontier
                for output_node in node.output_nodes
            }):
                result.append(frontier)
            return result

