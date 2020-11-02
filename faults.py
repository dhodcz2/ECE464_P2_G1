from typing import List, Union, Dict, NamedTuple
import circuitsimulator
from nodes import Value, Node
from testvector import TestVector, TestVectorGenerator
from copy import copy
import csv
import logging
import unittest


class Fault(object):
    def __init__(self, node: Node, stuck_at: Value, input_node: Node = None):
        if input_node and input_node not in node.input_nodes:
            raise ValueError(f"{input_node.name} not in {node.name} inputs")
        if stuck_at != 0 and stuck_at != 1:
            raise ValueError(f"{stuck_at} is not a correct fault value")
        self.node = node
        self.input_node = input_node
        self.stuck_at = stuck_at

    def __str__(self):
        return f"{self.node.name}-" + \
               (f"{self.input_node.name}-" if self.input_node else '') + f"{self.stuck_at}"

    def __hash__(self):
        return hash((str(self), str(self.stuck_at)))
        # return hash(('string', str(self)))


class CircuitSimulator(circuitsimulator.CircuitSimulator):
    def __init__(self, args):
        super(CircuitSimulator, self).__init__(args=args)
        self.args = args

    @staticmethod
    def local_faults(node: Node) -> List[Fault]:
        input_node: Node
        return [Fault(node, stuck_at=Value(0)),
                Fault(node, stuck_at=Value(1))] + \
               [fault for faults in [[
                   Fault(node, input_node=input_node, stuck_at=Value(0)),
                   Fault(node, input_node=input_node, stuck_at=Value(1)),
               ] for input_node in node.input_nodes if len(input_node.output_nodes) > 1]
                for fault in faults]

    def generate_fault_list(self) -> List[Fault]:
        return [fault for faults in [
            self.local_faults(node) for node in self.nodes
        ] for fault in faults]

    def induce_fault(self, fault: Union[Fault, str]) -> None:
        if type(fault) != str and type(fault) != Fault:
            raise TypeError

        # if not isinstance(fault, str) and not isinstance(fault, Fault):
        #     raise TypeError
        if isinstance(fault, str):
            parameters = fault.split('-')
            node = self.nodes[parameters[0]]
            input_node = self.nodes[parameters[1]] if parameters[2] else None
            stuck_at = Value(parameters[2]) if parameters[2] else Value(parameters[1])
            if stuck_at != 0 and stuck_at != 1:
                raise ValueError(f"Invalid stuck-at value: {stuck_at}")
            fault = Fault(node=node, input_node=input_node, stuck_at=stuck_at)
        if fault.input_node:
            input_fault = copy(fault.input_node)
            input_fault.stuck_at = fault.stuck_at
            input_fault.output_nodes = [fault.node]
            fault.node.input_nodes.remove(fault.input_node)
            fault.node.input_nodes.append(input_fault)
            self.nodes.faulty_nodes.append((input_fault, fault.input_node))
        else:
            fault.node.stuck_at = fault.stuck_at
            self.nodes.faulty_nodes.append((fault.node, None))

    def detect_fault(self, test_vector: TestVector) -> bool:
        """Returns: True if, when applying the given test vector, a fault may be detected"""
        self.simulate()
        # self.reset_faults()
        for output_node in self.nodes.output_nodes.values():
            if output_node == "D" or output_node == "D'":
                return True
        # self.reset_faults()
        # self.reset()
        return False

    def detect_faults(self, test_vector: TestVector, faults: List[Fault]) -> List[Fault]:
        def test(fault: Fault) -> bool:
            """Note: the entire circuit is not being reset, just the faults. I believe this can
            decrease simulation time."""
            self.reset()
            for input_node, value in zip(self.nodes.input_nodes.values(), test_vector):
                input_node.set(value)
            self.induce_fault(fault)
            return self.detect_fault(test_vector)

        # result = [fault for fault in faults if test(fault)]
        return [fault for fault in faults if test(fault)]

    def fault_coverage(self, test_vectors: List[TestVector], faults: List[Fault]) -> NamedTuple:
        class Result(NamedTuple):
            remaining_faults: List[Fault] = []
            fault_coverage_all: Dict[TestVector, List[Fault]] = {}
            fault_coverage_list: Dict[TestVector, List[Fault]] = {}

        fault_coverage_all = dict(
            (test_vector, self.detect_faults(test_vector, faults))
            for test_vector in test_vectors
        )
        remaining_faults = faults
        fault_coverage_list = {}

        for _tv, _faults in fault_coverage_all.items():
            _faults = [fault for fault in _faults if fault in remaining_faults]
            remaining_faults = [fault for fault in remaining_faults if fault not in _faults]
            fault_coverage_list.update({_tv: _faults})

        result = Result(remaining_faults, fault_coverage_all, fault_coverage_list)
        with open(f"_{self.args.bench}_remainingfaults.csv", 'w', newline='') as f:
            w = csv.writer(f, delimiter=',', lineterminator='\n')
            w.writerow([str(fault) for fault in result.remaining_faults])
        with open(f"_{self.args.bench}_all.csv", 'w', newline='') as f:
            tv_writer = csv.writer(f, delimiter=',', lineterminator=':')
            fault_writer = csv.writer(f, delimiter=',', lineterminator='\n')
            for tv, faults in result.fault_coverage_all.items():
                tv_writer.writerow([str(tv)])
                fault_writer.writerow(faults)
        with open(f"_{self.args.bench}_list.csv", 'w', newline='') as f:
            tv_writer = csv.writer(f, delimiter=',', lineterminator=':')
            fault_writer = csv.writer(f, delimiter=',', lineterminator='\n')
            for tv, faults in result.fault_coverage_list.items():
                tv_writer.writerow([str(tv)])
                fault_writer.writerow(faults)

        return result

    def simulate(self) -> None:

        iteration_printer = self.IterationPrinter(self.nodes)
        for iteration in self:
            if self.args.verbose:
                iteration_printer(self.nodes)
        if (self.args.verbose):
            print(iteration_printer)
        # self.detect_faults()
        # """Simulates the circuit consisting of nodes."""
        # for iteraion in self:
        #     TODO: Log the iteration
        # pass

    def reset(self):
        for node in self.nodes:
            node.reset()
        for faulty_node, replacement in self.nodes.faulty_nodes:
            if replacement:
                faulty_node.output_nodes[0].input_nodes.remove(faulty_node)
                faulty_node.output_nodes[0].input_nodes.append(replacement)
                del faulty_node
            else:
                faulty_node.stuck_at = None
        self.nodes.faulty_nodes.clear()
