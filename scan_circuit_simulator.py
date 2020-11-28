from circuitsimulator_redone import *


class ScanCircuitSimulator(CircuitSimulator):

    @staticmethod
    def identical(first: List[Value], second: List[Value]) -> bool:
        return all(val1 is val2 for val1, val2 in zip(first, second))

    def scan_in(self, test_vector: TestVector):
        for node, value in zip(self.nodes.scan_in_nodes, test_vector):
            node.vector_assignment = value
            node.value = value

    def scan_out(self) -> List[Value]:


    @staticmethod
    def compile(gates: 'LineParser.Gates') -> 'CircuitSimulator.Nodes':
        """From the LineParser Gates result, construct the nodes of the circuit"""
        nodes_instance = CircuitSimulator.Nodes()
        for name, gate in gates.gates.items():
            node = ScanNode(gate)
            node.type = gates.node_types.get(name, "INTERM.")
            if node.type == "INTERM.":
                nodes_instance.intermediate_nodes[name] = node
            elif node.type == "INPUT":
                nodes_instance.input_nodes[name] = node
            elif node.type == "OUTPUT":
                nodes_instance.output_nodes[name] = node
        for name, input_names in gates.inputs.items():
            nodes_instance[name].input_nodes = [nodes_instance[input_name] for input_name in input_names]
            for input_name in input_names:
                nodes_instance[input_name].output_nodes.append(nodes_instance[name])
        for name, node_type in gates.node_types.items():
            nodes_instance[name].type = node_type

        nodes_instance.flip_flops = {node for node in nodes_instance if isinstance(node, FlipFlop)}
        return nodes_instance


class ScanNode(Node):
    def __init__(self, gate: Gate):
        gate.node = self
        self.gate = gate
        self.input_nodes: List[ScanNode, InputFault] = []
        self.output_nodes: List[ScanNode, InputFault] = []
        self.stuck_at: Optional[Value] = None
        self.vector_assignment: Value = value_U
        self.type = "INTERM."
        self.corridor = False
        self.implication = value_U

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"{self.type}{self.name} = {self.value}"

    def __hash__(self):
        return hash(self.name)

    @property
    def name(self) -> str:
        return self.gate.name

    @property
    def value(self) -> Value:
        return self.gate.value

    @value.setter
    def value(self, val: Value):
        self.gate.value = val

    @property
    def value_new(self) -> Value:
        return self.gate.value_new

    @value_new.setter
    def value_new(self, val: Value):
        self.gate.value_new = val

    def logic(self):
        self.value_new = self.propagate_fault(self.gate.logic(), self.stuck_at)

    def update(self):
        self.value = self.value_new

    def reset(self):
        self.gate.value = self.vector_assignment
        self.gate.value_new = self.vector_assignment
        self.stuck_at = None
        for node in self.output_nodes:
            node.reset()

    def local_reset(self):
        self.gate.value = self.vector_assignment
        self.gate.value_new = self.vector_assignment
        self.stuck_at = None

    @property
    def propagates_fault(self) -> bool:
        """Returns true if the node propagates a fault"""
        return self.value.propagates_fault

    @staticmethod
    @lru_cache(15)
    def propagate_fault(value: Value, stuck_at: Value):
        if stuck_at:
            return stuck_at
        else:
            return value

    @property
    def fault_propagation_path(self) -> Generator[Set['Node'], None, None]:
        frontier = {self}
        yield frontier
        while (any(node.value.propagates_fault for node in frontier) and
               (frontier := {
                   output_node for node
                   in frontier
                   for output_node in node.output_nodes
               })
        ):
            yield frontier

    @property
    def propagation_path(self) -> Generator[Set['Node'], None, None]:
        frontier = {self}
        yield frontier
        while (frontier := {
            output_node for node
            in frontier
            for output_node in node.output_nodes
        }):
            yield frontier


class ScanInputFault(ScanNode):
    __slots__ = 'output_nodes', 'genuine_node', 'stuck_at'

    def __init__(self, output_node: Node, node: Node, stuck_at: Value):
        self.genuine_node = node
        self.output_nodes = [output_node]
        output_node.input_nodes.remove(node)
        output_node.input_nodes.append(self)
        self.stuck_at = stuck_at

    @property
    def name(self):
        return "%s FAULT" % self.genuine_node.name

    def logic(self):
        pass

    def update(self):
        pass

    def reset(self):
        self.output_nodes[0].input_nodes.remove(self)
        self.output_nodes[0].input_nodes.append(self.genuine_node)
        for node in self.output_nodes:
            node.reset()
        # del self

    def local_reset(self):
        self.output_nodes[0].input_nodes.remove(self)
        self.output_nodes[0].input_nodes.append(self.genuine_node)

    @property
    def value(self) -> Value:
        return self.propagate_fault(self.genuine_node.value, self.stuck_at)

    @property
    def fault_propagation_path(self) -> Generator[Set['Node'], None, None]:
        return self.output_nodes[0].fault_propagation_path
        # return self.genuine_node.fault_propagation_path

    @property
    def propagation_path(self) -> Generator[Set['Node'], None, None]:
        return self.output_nodes[0].propagation_path
        # return self.genuine_node.propagation_path
