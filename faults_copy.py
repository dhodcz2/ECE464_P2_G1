from typing import List, Union, Dict, Tuple, TypedDict, NamedTuple
from dataclasses import dataclass

import circuitsimulator
from nodes import Value, Node
from testvector import TestVector, TestVectorSeed
import copy
import csv
import logging


class FaultLogger(type):
    def init(cls, *args):
        super().__init__(*args)
        # Explicit name mangling
        logger_attribute_name = '_' + cls.__name__ + '__logger'
        # Logger name derived accounting for inheritance for the bonus marks
        logger_name = '.'.join([c.__name__ for c in cls.mro()[2::-1]])
        setattr(cls, logger_attribute_name, logging.getLogger(logger_name))


class Fault(object):
    """ Fault abstraction as an alternative to working with strings
    
    Attributes:
        node (Node): Reference to the node that the fault is occurring around.
        input_node (Node, None): Reference to the input node that is faulty, if any.
        stuck_at (Value): The value that the input is stuck it, if there is an input;
            otherwise, the value the node is stuck at.

    Raises:
        ValueError:
            if `input` is not an input_node of `node`, or if `stuck_at` is not a correct value.
    """

    def __init__(self, node: Node, input_node: Node = None, stuck_at: Value = None, ):
        """
        Args:
            node (Node): Reference to the node that the fault is occurring around.
            input_node (Node, None): Reference to the input node that is faulty, if any.
                stuck_at (Value): The value that the input is stuck it, if there is an input;
            otherwise, the value the node is stuck at.
        """
        if input_node and input_node not in node.input_nodes:
            raise ValueError(f"{input_node.name} not in {node.name} inputs")
        if stuck_at != 0 and stuck_at != 1:
            raise (ValueError(f"{stuck_at} is not a correct fault value"))
        self.node = node
        self.input_node = input_node
        self.stuck_at = stuck_at

    def __repr__(self):
        return f"{self.node.name}-" + \
               (f"{self.input_node.name}-" if self.input_node else '') + \
               str(self.stuck_at)

    def __str__(self):
        # example: 'f-g-1'
        return f"{self.node.name}-" + \
               (f"{self.input_node.name}-" if self.input_node else '') + \
               str(self.stuck_at)


class CircuitSimulator(circuitsimulator.CircuitSimulator, metaclass=FaultLogger):
    def __init__(self, args):
        super(CircuitSimulator, self).__init__(args)
        logging.basicConfig(level=logging.INFO, filename=f"_{args.bench}.log",
                            format='%(asctime)s :: %(levelname)s :: %(message)s')

    @staticmethod
    def local_faults(node: Node) -> List[Fault]:

        result: List[Fault] = [Fault(node, stuck_at=Value(0)),
                               Fault(node, stuck_at=Value(1))]
        for input_node in node.input_nodes:
            if len(input_node.output_nodes) > 1:  # Fanout
                result.append(Fault(node, input_node, stuck_at=Value(1)))
                result.append(Fault(node, input_node, stuck_at=Value(0)))
            # else:
            #     logging.INFO("")
        return result

    def fault_list(self) -> List[Fault]:
        """Generate the full list of single-stuck-at faults (without repetition)"""
        result: List[Fault] = []
        for node in self.nodes:
            result += self.local_faults(node)
        with open(f"_{self.args.bench}_faultlist.txt", 'w', newline='') as f:
            for fault in result:
                f.write(f"{fault}, ")
        return result

    def induce_fault(self, fault: Union[Fault, str]):
        if not isinstance(fault, str) or isinstance(fault, Fault):
            raise TypeError(f"is type: {type(fault)}")
        if isinstance(fault, str):
            parameters = fault.split('-')
            fault = Fault(
                node=self.nodes[parameters[0]],
                input_node=self.nodes[parameters[1]] if parameters[2] else None,
                stuck_at=Value(parameters[2]) if parameters[2] else Value(parameters[1])
            )
            if fault.stuck_at != 0 and fault.stuck_at != 1:
                raise ValueError(f"Fault {fault} stuck at wrong value")

        if fault.input_node:
            input_fault = copy.copy(fault.input_node)
            input_fault.stuck_at = fault.stuck_at
            input_fault.output_nodes = fault.node
            self.nodes.faulty_nodes.append((input_fault, fault.input_node))
        else:
            fault.node.stuck_at = fault.stuck_at
            self.nodes.faulty_nodes.append((fault.node, None))

    def reset_faults(self):
        for (faulty_node, replacement) in self.nodes.faulty_nodes:
            if replacement:
                faulty_node.output_nodes[0].input_nodes.append(replacement)
                faulty_node.output_nodes[0].input_nodes.remove(faulty_node)
                del faulty_node
            else:
                faulty_node.stuck_at = None

    def detect_fault(self, test_vector: TestVector) -> bool:
        """Returns: True if, when applying the given test vector, a fault may be detected"""
        for input_node, value in zip(self.nodes.input_nodes, test_vector):
            input_node.value = value
        self.simulate()
        for output_node in self.nodes.output_nodes:
            if output_node == "D" or output_node == "D'":
                return True
        return False

    def detect_faults(self, test_vector: TestVector, faults: List[Fault]) -> List[Fault]:
        """Returns: A list of the given faults that may be detected by the given test vector."""
        assert len(test_vector) == len(self.nodes.input_nodes)
        result: List[Fault] = []
        for fault in faults:
            self.induce_fault(fault)
            if self.detect_fault(test_vector):
                result.append(fault)
            self.reset_faults()
        return result

    def fault_coverage(self, test_vectors: List[TestVector], faults: List[Fault]) -> NamedTuple:
        """

        Args:
            test_vectors: test vectors to be tested
            faults: faults to be tested

        Returns:
            NamedTuple:
                remaining_faults: List[Fault]
                fault_coverage: Dict[TestVector, List[Fault]]
        """

        class Result(NamedTuple):
            remaining_faults: List[Fault]
            fault_coverage: Dict[TestVector, List[Fault]]

        result = Result(fault_coverage={}, remaining_faults=[])
        result.remaining_faults = faults
        for test_vector in test_vectors:
            faults_detected = self.detect_faults(test_vector, faults)
            result.fault_coverage.update({test_vector: faults_detected})
            result.remaining_faults = [fault for fault in result.remaining_faults not in faults_detected]
        with open(f"_{self.args.bench}_remainingfaults.csv", 'w', newline='') as f:
            w = csv.writer(f, delimiter='\t', lineterminator='\n')
            w.writerow([str(fault) for fault in result.remaining_faults])
        with open(f"_{self.args.bench}_faultcoverage.csv", 'w', newline='') as f:
            w = csv.writer(f, delimiter='\t', lineterminator='\n')
            for tv, faults in result.fault_coverage.items():
                w.writerow([tv, faults])

        return result

    def simulate(self):
        """Simulates the circuit consisting of **Node** nodes."""
        for iteration in self:
            #  TODO: Log the iteration
            pass
