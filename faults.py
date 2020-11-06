from typing import List, Union, Dict, NamedTuple
from dataclasses import dataclass
import circuitsimulator
from nodes import Value, Node, DummyNode
from testvector import TestVector, TestVectorGenerator
from copy import copy, deepcopy
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

    def __repr__(self):
        return f"{self.node.name}-" + \
               (f"{self.input_node.name}-" if self.input_node else '') + f"{self.stuck_at}"

    # representation : __repr__
    # string: __str__
    # representation is supposed to be simple
    # string is

    def __hash__(self):
        return hash((str(self), str(self.stuck_at)))

    def __eq__(self, other: Union[str, 'Fault']):
        if type(other) == Fault:
            return other.node == self.node and other.stuck_at == self.stuck_at \
                   and other.input_node == self.input_node
        elif type(other) == str:
            return other == self.__repr__()


class CircuitSimulator(circuitsimulator.CircuitSimulator):
    def __init__(self, args):
        super(CircuitSimulator, self).__init__(args=args)
        self.args = args
        self.faults: List[Fault] = []

    @staticmethod
    def local_faults(node: Node) -> List[Fault]:
        input_node: Node

        return [Fault(node, stuck_at=Value(0)),
                Fault(node, stuck_at=Value(1))] + \
               [fault for faults in [[
                   Fault(node, input_node=input_node, stuck_at=Value(0)),
                   Fault(node, input_node=input_node, stuck_at=Value(1)),
               ] for input_node in node.input_nodes]
                # if len(input_node.output_nodes) > 1]
                for fault in faults]

    def generate_fault_list(self) -> List[Fault]:
        result = [fault for faults in [
            self.local_faults(node) for node in self.nodes
        ] for fault in faults]
        with open(f"_{self.args.bench}_faults.txt", 'w') as f:
            for fault in result:
                f.write(str(fault) + ', ')
        return result

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

        self.faults.append(fault)
        if fault.input_node:
            dummy_node = DummyNode(fault.input_node)
            dummy_node.input_nodes = fault.input_node.input_nodes
            dummy_node.output_nodes = [fault.node]
            dummy_node.stuck_at = fault.stuck_at
            fault.node.input_nodes.remove(fault.input_node)
            fault.node.input_nodes.append(dummy_node)
            self.nodes.dummy_nodes.update({dummy_node.name: dummy_node})
            # self.nodes.faulty_nodes.append(dummy_node)

        else:
            fault.node.stuck_at = fault.stuck_at
            # self.nodes.faulty_nodes.append(fault.node)

    def detect_fault(self, test_vector: TestVector) -> bool:
        """Returns: True if, when applying the given test vector, a fault may be detected"""
        self.simulate()
        for output_node in self.nodes.output_nodes.values():
            if output_node == "D" or output_node == "D'":
                return True
        return False

    def detect_faults(self, test_vector: TestVector, faults: List[Fault]) -> List[Fault]:
        def test(fault: Fault) -> bool:
            """Note: the entire circuit is not being reset, just the faults. I believe this can
            decrease simulation time."""
            self.reset()
            # if self.args.verbose:
            # print(f"Now applying {test_vector} to the remaining {len(faults)} faults:")
            # print(faults, "...\n")

            for input_node, value in zip(self.nodes.input_nodes.values(), test_vector):
                input_node.set(value)
            self.induce_fault(fault)
            if self.detect_fault(test_vector):
                if self.args.verbose:
                    print(f"Fault {fault} detected by {test_vector}")
                return True
            else:
                if self.args.verbose:
                    print(f"Fault {fault} UNdetected by {test_vector}")
                return False

        return [fault for fault in faults if test(fault)]

    def fault_coverage(self, test_vectors: List[TestVector], faults: List[Fault]) -> NamedTuple:
        @dataclass
        class Result:
            remaining_faults: List[Fault]
            fault_coverage_all: Dict[TestVector, List[Fault]]
            fault_coverage_list: Dict[TestVector, List[Fault]]

        remaining_faults = faults
        fault_coverage_all = {}
        fault_coverage_list = {}
        for test_vector in test_vectors:
            if self.args.verbose:
                print(f"Now applying {test_vector} to the remaining {len(remaining_faults)} faults:",
                      '\n', remaining_faults, '...', '\n', sep='')
            detected_faults = self.detect_faults(test_vector, remaining_faults)
            print()
            fault_coverage_all.update({test_vector: detected_faults})
            fault_coverage_list.update(
                {test_vector: [fault for fault in detected_faults if fault not in remaining_faults]})
            remaining_faults = [fault for fault in remaining_faults if fault not in detected_faults]

        result = Result(remaining_faults, fault_coverage_all, fault_coverage_list)

        with open(f"_{self.args.bench}_remainingfaults.txt", 'w', newline='') as f:
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

        if self.args.verbose:
            print(f"Final UNDETECTED: {len(remaining_faults)} faults: {remaining_faults}")

        return result

    def simulate(self) -> None:

        iteration_printer = self.IterationPrinter(self.nodes)
        for iteration in self:
            pass
            # if 'a-0' in self.faults and self.nodes['a'].value == "D" and self.nodes['b'].value == 1:
            #     print()
            # if 'h-f-0' in self.faults and self.nodes['b'] == 0 and self.nodes['c'] == 1 and self.nodes['a'] == 0:
            #     print()
            # if self.args.verbose:
            #     iteration_printer(self.nodes)
        # if (self.args.verbose):
        #     print(iteration_printer)
        # self.detect_faults()
        # """Simulates the circuit consisting of nodes."""
        # for iteraion in self:
        #     TODO: Log the iteration
        # pass

    def reset(self):
        for node in self.nodes:
            node.reset()
        for dummy_node in self.nodes.dummy_nodes.values():
            dummy_node.output_nodes[0].input_nodes.append(dummy_node.genuine)
            dummy_node.output_nodes[0].input_nodes.remove(dummy_node)
            # del dummy_node
        self.nodes.dummy_nodes.clear()
        self.faults.clear()

        # for faulty_node in self.nodes.faulty_nodes:
        #     if type(faulty_node) == Node:
        #         faulty_node.stuck_at = None
        #     elif type(faulty_node) == DummyNode:
        #         faulty_node.output_nodes[0].input_nodes.append(faulty_node.genuine)
        #         faulty_node.output_nodes[0].input_nodes.remove(faulty_node)
        #         del faulty_node
