from typing import List, Union

import circuitsimulator
import nodes


class Fault(object):
    """Can be typecast to str """

    def __init__(self, node: nodes.Node, input: nodes.Node = None, stuck_at: nodes.Value = None, ):
        self.node = node
        self.input = input
        self.stuck_at = stuck_at

    def __str__(self):
        return f"{self.node.name}-" + f"{self.input.name}-" if self.input else "" + str(self.stuck_at)


class CircuitSimulator(circuitsimulator.CircuitSimulator):
    def __init__(self, args):
        self.args = args


    def fault_list(self, log=False) -> List[Fault]:
        """@param log: log the results in a text file"""
        result: List[Fault] = []
        node: nodes.Node
        # TODO: There may be more logic to this than just output fault and input faults.
        for node in self.nodes:
            result.append(Fault(node, stuck_at=nodes.Value("D")))
            result.append(Fault(node, stuck_at=nodes.Value("D'")))
            input_node: nodes.Node
            for input_node in node.input_nodes:
                result.append(Fault(node, input_node, nodes.Value("D")))
                result.append(Fault(node, input_node, nodes.Value("D'")))
        if log:
            with open(self.args.faultlist, 'w') as f:
                # TODO: this could probably be done better
                f.write(result)
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
                input=self.nodes[parameters[1]] if parameters[2] else None,
                stuck_at=nodes.Value("D") if parameters[2] == '0' else nodes.Value("D'") if parameters[2]
                else nodes.Value("D") if parameters[1] == '0' else nodes.Value("D'")
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

    def detect_faults(self, test_vectors: List[str]) -> List[str]:
        """
        Return a list of valid test vectors
        """
        result: List[str] = []
        test_vector: str
        for test_vector in test_vectors:
            if len(test_vector) != len(self.nodes.input_nodes):
                if len(test_vector) < len(self.nodes.input_nodes):
                    raise ValueError(f"{test_vector} too small")
                else:
                    raise ValueError(f"{test_vector} too large")
            input_node: nodes.Node
            value: str
            for input_node, value in zip(self.nodes.input_nodes, [value for value in test_vector]):
                input_node.value = nodes.Value(value)
            #             TODO: logging
            iteration_printer = self.IterationPrinter(self.nodes)
            for iteration in self:
                iteration_printer(self.nodes)
            output_node: nodes.Node
            # Value objects are initialized outside the for loop to save CPU
            stuck_at_0 = nodes.Value("D")
            stuck_at_1 = nodes.Value("D'")
            for output_node in self.nodes.output_nodes:
                if output_node.value == stuck_at_0 or output_node.value == stuck_at_1:
                    result.append(test_vector)
        return result

