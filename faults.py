from typing import List, Union, Dict

import circuitsimulator
from nodes import Value, Node
from testvector import TestVector, TestVectorSeed
import copy


class Fault(object):
    """ Fault abstraction as an alternative to working with strings
    
    Attributes:
        node (Node): Reference to the node that the fault is occurring around.
        _input (Node, None): Reference to the input node that is faulty, if any.
        stuck_at (Value): The value that the input is stuck it, if there is an input;
            otherwise, the value the node is stuck at.

    Raises:
        ValueError:
            if `input` is not an input_node of `node`, or if `stuck_at` is not a correct value.
    """

    def __init__(self, node: Node, _input: Node = None, stuck_at: Value = None, ):
        """
        Args:
            node (Node): Reference to the node that the fault is occurring around.
            _input (Node, None): Reference to the input node that is faulty, if any.
                stuck_at (Value): The value that the input is stuck it, if there is an input;
            otherwise, the value the node is stuck at.
        """
        if _input not in node.input_nodes:
            raise ValueError(f"{_input.name} not in {node.name} inputs")
        if stuck_at != Value("D") and stuck_at != Value("D'"):
            raise (ValueError(f"{stuck_at} is not a correct fault value"))
        self.node = node
        self.input = _input
        self.stuck_at = stuck_at

    def __str__(self):
        return f"{self.node.name}-" + f"{self.input.name}-" if self.input else "" + str(self.stuck_at)


class CircuitSimulator(circuitsimulator.CircuitSimulator):
    def __init__(self, args):
        self.args = args

    def fault_list(self, log=False) -> List[Fault]:
        """Generate the full list of single-stuck-at faults (without repetition)"""
        result: List[Fault] = []
        node: Node
        # TODO: There may be more logic to this than just output fault and input faults.
        for node in self.nodes:
            result.append(Fault(node, stuck_at=Value("D")))
            result.append(Fault(node, stuck_at=Value("D'")))
            input_node: Node
            for input_node in node.input_nodes:
                result.append(Fault(node, input_node, Value("D")))
                result.append(Fault(node, input_node, Value("D'")))
        if log:
            with open(self.args.faultlist, 'w') as f:
                # TODO: this could probably be done better
                f.write(str(result))
        return result

    def create_fault(self, fault: Union[Fault, str]):
        """
        Creates a fault within the circuit simulator nodes
        @param fault: A fault; either string (b-a-1, b-0) or Fault
        """

        def faulty_update():
            # do nothing
            pass

        if isinstance(fault, str):
            parameters = fault.split('-')
            fault = Fault(
                node=self.nodes[parameters[0]],
                _input=self.nodes[parameters[1]] if parameters[2] else None,
                stuck_at=Value("D") if parameters[2] == '0' else Value("D'") if parameters[2]
                else Value("D") if parameters[1] == '0' else Value("D'")
            )
        if fault.input:
            pass
            # TODO: determine fault propagation for input-based faults
            # TODO: I'm thinking this could be done by changing the logic for that node
        else:
            # TODO: I'm not sure if this will work, but I plan to use this to reset the update()
            fault.node.old_update = fault.node.update
            fault.node.update = faulty_update
            fault.node.value = fault.stuck_at

    # Inputs a list a test vectors
    # Show the number of faults covered by each test vector
    #

    def detect_fault(self, test_vector: TestVector) -> bool:
        """Returns: True if, when applying the given test vector, a fault may be detected"""
        sa_0 = Value(0)
        sa_1 = Value(1)
        for input_node, value in zip(self.nodes.input_nodes, test_vector):
            input_node.value = value
        self.simulate()
        for output_node in self.nodes.output_nodes:
            if output_node == sa_0 or output_node == sa_1:
                return True
        return False

    def detect_faults(self, test_vector: TestVector, faults: List[Fault]) -> List[Fault]:
        """Returns: A list of the given faults that may be detected by the given test vector."""
        assert len(test_vector) == len(self.nodes.input_nodes)
        result: List[Fault] = []
        for fault in faults:
            self.create_fault(fault)
            if self.detect_fault(test_vector):
                result.append(fault)
            self.reset()
        return result

    def fault_coverage(self, test_vectors: List[TestVector], faults: List[Fault]) \
            -> List[Dict[{TestVector: List[Fault]}], List[Fault]]:
        """

        Args:
            test_vectors (List[TestVector]): A list of test vectors to be iterated across.
            faults (List[Fault]): A list of faults to be subiterated across.

        Note:
            Perhaps to professor: Is iteration across each fault, across each test vector, computationally problematic?
            The complexity of this algorithm is 0(n^2), is that an issue?

        Returns:
            A Vector with:
                [0] (Dict[{TestVector: List[Fault]}]: A list of faults covered by each of the test vectors
                [1] (List[Fault]): The remaining list of faults.
        """
        # result: Dict[{TestVector: List[Fault]}]
        fault_coverage: Dict[{TestVector: List[Fault]}] = {}
        remaining_faults = copy.copy(faults)
        for test_vector in test_vectors:
            faults_detected = self.detect_faults(test_vector, faults)
            # TODO: Most efficient way of removing list entries that are
            # TODO: present in both faults_detected and remaining_faults
            fault_coverage[test_vector] = faults_detected

    def simulate(self):
        """Simulates the circuit consisting of **Node** nodes."""
        for iteration in self:
            #  TODO: Log the iteration
            pass
