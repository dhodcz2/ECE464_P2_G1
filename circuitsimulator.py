from _collections import OrderedDict
from typing import List, Dict, Union, Tuple

import nodes
from nodes import Node
import exceptions
from re import match


def generate_line(node: Node) -> str:
    """
    Parameters
    ----------
    node: Node
        The node to for which a text line is to be generated

    Returns
    -------
    str:
        A line representing relevant information for a node.

    """
    line: str = node.type.ljust(11) + \
                node.name.ljust(8) + \
                (node.gate_type.ljust(8) if node.gate_type else "" + ', '.join(node.input_names)).ljust(20) + \
                str(node.value).ljust(3)
    return line


class CircuitSimulator(object):
    class IterationPrinter(object):
        """
        An abstraction that allows for more compact printing of nodes.
        When the IterationPrinter is initialized with nodes, it generates an
        informative list of strings corresponding to the nodes. Then,
        call() is run to append to the end of a line, a new chronological node value.
        """

        def __init__(self, _nodes: List[Node]):
            self.iteration = 0
            self.lines = [generate_line(node) for node in _nodes]
            header = "Type".ljust(8) + "Variable".ljust(11) + \
                     "Logic".ljust(8) + "Inputs".ljust(9) + "Initial".ljust(3)
            self.lines.insert(0, header)

        def __iter__(self):
            for line in self.lines:
                yield line

        def __str__(self):
            string = ""
            for line in self:
                string += line + "\n"
            return string

        def __call__(self, _nodes):
            self.iteration += 1
            self.lines[0] += "\t" + str(self.iteration)
            i = 0
            for node in _nodes:
                self.lines[i + 1] += "\t" + str(node.value)
                i += 1

    class LineParser(object):
        """Parses a circuit.bench file"""

        def __init__(self, bench):
            self.file = bench
            self.pattern_gate = "(\S+) = ([A-Z]+)\((.+)\)"
            self.pattern_io = "([A-Z]+)\((.+)\)"
            self.gates = []
            self.input_names = []
            self.output_names = []
            self.gate_map = {"AND": nodes.AndGate, "OR": nodes.OrGate, "NAND": nodes.NandGate, "XNOR": nodes.XnorGate,
                             "NOR": nodes.NorGate, "BUFF": nodes.BuffGate, "XOR": nodes.XorGate, "NOT": nodes.NotGate}

        def parse_file(self):
            """
            Parses all the lines in a file
            :return: Returns a LineParser object to be referenced by the outside class
            """
            with open(self.file) as f:
                for line in f:
                    self.parse_line(line)
            return self

        def parse_line(self, line: str):

            if groups := match(self.pattern_gate, line):
                name = groups.group(1)
                gate_type = self.gate_map[groups.group(2)]
                if not gate_type:
                    raise exceptions.ParseLineError(line)
                inputs = groups.group(3).split(', ')
                self.gates.append(gate_type(name, inputs))
            elif groups := match(self.pattern_io, line):
                io = groups.group(1)
                name = groups.group(2)
                if io == "INPUT":
                    self.input_names.append(name)
                    self.gates.append(nodes.Gate(name))
                elif io == "OUTPUT":
                    self.output_names.append(name)
                else:
                    raise exceptions.ParseLineError(line)
            elif line.startswith('#') or line == '\n':
                pass
            else:
                raise exceptions.ParseLineError(line)

    class Nodes(object):
        """
        A list of ordered dictionaries; allows for user to reference a specific node by name, iterate across
        the nodes in order of input_nodes, intermediate_nodes, and output_nodes, or directly access those node subsets.

        Attributes:
            input_nodes (OrderedDict):
            intermediate_nodes (OrderedDict):
            output_nodes (OrderedDict):
            faulty_nodes (Dict):
        """

        def __doc__(self):
            """Data structure abstraction that is essentially a list of ordered dictionaries;
            allows for the user to reference a specific node by name, iterate across the nodes in order
            of input_nodes, intermediate_nodes, and output_nodes, or directly access those node subsets.


            """

        def __init__(self):
            self.input_nodes: OrderedDict[str, Node] = OrderedDict()
            self.intermediate_nodes: OrderedDict[str, Node] = OrderedDict()
            self.output_nodes: OrderedDict[str, Node] = OrderedDict()
            self.faulty_nodes: List[Tuple[Node, Node]] = []

        def __contains__(self, item: Node):
            if item in self.intermediate_nodes:
                return True
            if item in self.input_nodes:
                return True
            if item in self.output_nodes:
                return True
            return False

        def __getitem__(self, item: Node):
            if item in self.intermediate_nodes:
                return self.intermediate_nodes[item]
            elif item in self.input_nodes:
                return self.input_nodes[item]
            elif item in self.output_nodes:
                return self.output_nodes[item]
            raise KeyError

        def __iter__(self):
            for node in self.input_nodes.values():
                yield node
            for node in self.intermediate_nodes.values():
                yield node
            for node in self.output_nodes.values():
                yield node

        def __str__(self):
            string = ''
            for node in self:
                string += f"\n{node}"
            return string

    def __init__(self, args):
        self.nodes = self.Nodes()
        self.args = args
        self.parser = self.LineParser(args.bench)
        self.compile(self.parser.parse_file())
        self.faulty_node = None

    def __next__(self):
        """In each iteration, the nodes' values are updated to represent the result of the
        input nodes with their logic."""
        self.iteration += 1
        updated_nodes = 0
        for node in self.nodes:
            node.logic()
            if node.value != node.value_new:
                updated_nodes += 1
        if updated_nodes == 0:
            raise StopIteration
        for node in self.nodes:
            node.update()
        if self.iteration == 0:
            self.iteration += 1
            return "Initial values" + str(self.nodes)
        return "Iteration # " + str(self.iteration) + ": " + str(self.nodes)

    def __iter__(self):
        self.iteration = -1
        return self

    def __str__(self):
        """Returns a string of all the nodes"""
        string = ''
        for node in self.nodes:
            string += f"{node}\n"

    def compile(self, lineparser: LineParser):
        """Compiles a functioning circuit of **Node** nodes from a LineParser object"""
        for gate in lineparser.gates:
            node = Node(gate)
            if node.name in lineparser.input_names:
                node.type = 'input'
                self.nodes.input_nodes.update({node.name: node})
            elif node.name in lineparser.output_names:
                node.type = 'output'
                self.nodes.output_nodes.update({node.name: node})
            else:
                self.nodes.intermediate_nodes.update({node.name: node})
        # Update Node member vectors input_nodes and output_nodes, which hold references to connected nodes
        for node in self.nodes:
            for input_name in node.gate.input_names:
            # for input_name in [input_node.name for input_node in node.input_nodes]
                self.nodes[node.name].input_nodes.append(self.nodes[input_name])
                self.nodes[input_name].output_nodes.append(self.nodes[node.name])

    def prompt(self):
        """Prompts user for input values"""
        line = self.args.testvec
        if not line:
            line = input("Start simulation with input values (return to exit):")
            if not line:
                return False
        input_values = [letter for letter in list(str(line)) if letter != ' ']
        final_inputs = []
        for chars in range(len(input_values)):  # check for D'
            if input_values[chars] != 'd' and input_values[chars] != 'D':
                if input_values[chars] != "'":
                    final_inputs.append(input_values[chars])
            else:
                D_index = chars
                if D_index + 1 < len(input_values) and input_values[D_index + 1] == "'":
                    final_inputs.append("D'")
                else:
                    final_inputs.append(input_values[chars])  # this will always be a single D
        for character, node in zip(final_inputs, self.nodes.input_nodes.values()):
            node.set(nodes.Value(character))
        self.induce_fault()
        return True

    def simulate(self):
        """Simulates the circuit consisting of **Node** nodes."""

        iteration_printer = self.IterationPrinter(self.nodes)
        for iteration in self:
            iteration_printer(self.nodes)
        print(iteration_printer)
        self.detect_faults()

    def induce_fault(self):
        def noop():
            pass

        fault_pattern = "(.)+=([0,1])"
        if self.args.fault:
            _match = match(fault_pattern, self.args.fault)

            if (_match := match(fault_pattern, self.args.fault)):
                try:
                    self.faulty_node: Node = self.nodes[_match[1]]
                    value = {"0": nodes.Value('D'), "1": nodes.Value("D'")}[_match[2]]
                    self.faulty_node.set(value)
                    self.faulty_node.logic = noop
                except KeyError:
                    print("Node name not found in nodes")
        if not self.faulty_node:
            while True:
                node_name = input("Which node do you want to be faulty? (return to skip) ")
                if node_name == "":
                    break
                try:
                    self.faulty_node: Node = self.nodes[node_name]
                except KeyError:
                    print("Name not found in nodes")
                    continue
                while True:
                    fault_value = input(f"Which value do you want node {self.faulty_node.name} to be stuck at? (1/0) ")
                    try:
                        self.faulty_node.set(
                            {"0": nodes.Value('D'), "1": nodes.Value("D'")}[fault_value]
                        )
                        self.faulty_node.logic = noop
                        break
                    except KeyError:
                        print("Invalid value: try again")
                break

    def detect_faults(self):
        if self.faulty_node:
            print(f"Fault {self.faulty_node.name}-SA-",
                  0 if self.faulty_node.value == 'D' else 1 if self.faulty_node.value == "D'" else ValueError(), sep='')
            if any(node == "D" or node == "D'" for node in self.nodes.output_nodes.values()):
                print(f"detected with input {self.args.testvec}, at output nodes:")
                faulty_outputs = [node for node in self.nodes.output_nodes.values() if node == "D" or node == "D'"]
                for node in faulty_outputs:
                    print(str(node) + "\n")
            else:
                print(f"Undetected with {self.args.testvec}")

    def reset(self):
        """Iterate across all the nodes in the circuit, resetting them if they were made to be faulty."""
        for node in self.nodes:
            node.reset()
