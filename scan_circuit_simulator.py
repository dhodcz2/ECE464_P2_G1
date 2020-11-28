from circuitsimulator_redone import *
from itertools import zip_longest


class ScanCircuitSimulator(CircuitSimulator):

    @staticmethod
    def identical(first: List[Value], second: List[Value]) -> bool:
        return all(val1 is val2 for val1, val2 in zip(first, second))

    def scan_in(self, test_vector: TestVector):
        for node, value in zip(self.nodes.scan_in_nodes, test_vector):
            node.vector_assignment = value
            node.value = value

    def scan_out(self) -> List[Value]:
        return [node.value for node in self.nodes.scan_out_nodes]

    def propagate(self, path: Iterable[Set['ScanNode']]):
        try:
            for nodes in path:
                for node in nodes:
                    node.logic()
                for node in nodes:
                    node.update()
            self.nodes.capture()
        except:
            print()

    def propagate_generator(self, path: Iterable[Set[Node]]) -> Generator[Set[Node], None, None]:
        for nodes in path:
            for node in nodes:
                node.logic()
            for node in nodes:
                node.update()
            yield nodes
        self.nodes.capture()

    def apply_vector(self, test_vector: TestVector):
        for node, value in zip(self.nodes.input_nodes.values(), test_vector):
            node.vector_assignment = value
            node.value = value
        propagate(self.nodes.input_propagation_path)

    @contextmanager
    def apply_fault(self, fault: Fault) -> Generator[Value, None, None]:
        self.fault = fault
        if fault.input_node:
            self.nodes.faulty_node = InputFault(fault.node, fault.input_node, fault.stuck_at)
        else:
            fault.node.stuck_at = fault.stuck_at
            self.nodes.faulty_node = fault.node
        self.propagate(self.nodes.fault_propagation_path)
        yield
        self.nodes.faulty_node.local_reset()
        for flip_flop in self.nodes.flip_flops:
            flip_flop.local_reset()
        self.propagate(self.nodes.fault_propagation_path)

    def detect_fault(self, fault: Fault) -> List[Value]:
        with self.apply_fault(fault):
            return self.scan_out()

    def detect_faults(self, tv: TestVector) -> List[Fault]:
        self.apply_vector(tv)
        propagate(self.nodes.input_propagation_path)
        scan_out = self.scan_out()
        return [
            fault for fault in self.faults
            if not self.identical(scan_out, self.detect_fault(fault))
        ]

    def detect_and_eliminate_faults(self, tv: TestVector, faults: Set[Fault]) -> List[Fault]:
        known_faults = self.tv_lookup[tv]
        detected_faults = faults.intersection(known_faults)
        undetected_faults = faults.difference(known_faults)
        self.apply_vector(tv)
        scan_out = self.scan_out()
        detected_faults.update(
            fault for fault in undetected_faults
            if self.identical(scan_out, self.detect_fault(fault))
        )
        faults.difference_update(detected_faults)
        return list(detected_faults)

    def compile(self, gates: CircuitSimulator.LineParser.Gates):
        self.nodes = self.Nodes()
        for name, gate in gates.gates.items():
            node = ScanNode(gate)
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

    class Nodes(CircuitSimulator.Nodes):
        def __init__(self):
            self.input_nodes: OrderedDict[str, ScanNode] = collections.OrderedDict()
            self.intermediate_nodes: Dict[str, ScanNode] = {}
            self.output_nodes: OrderedDict[str, ScanNode] = collections.OrderedDict()
            self.flip_flops: List[ScanNode] = []
            self.faulty_node: Union[InputFault, Node, None] = None

        @functools.cached_property
        def input_propagation_path(self) -> List[Set['ScanNode']]:
            result = [frontier := {
                output_node for node
                in self.scan_in_nodes
                for output_node in node.outputs_that_are_not_flip_flops
            }]
            while (frontier := {
                output_node for node
                in frontier
                for output_node in node.outputs_that_are_not_flip_flops
            }):
                result.append(frontier)
            return result

        @functools.cached_property
        def flip_flop_propagation_path(self) -> List[Set['ScanNode']]:
            result = [frontier := {
                output_node for node
                in self.flip_flops
                for output_node in node.outputs_that_are_not_flip_flops
            }]
            while (frontier := {
                output_node for node
                in frontier
                for output_node in node.outputs_that_are_not_flip_flops
            }):
                result.append(frontier)
            return result

        @staticmethod
        def node_propagation_path(node: Node) -> Generator[Set[Node], None, None]:
            yield (
                frontier := {*node.output_nodes}
            )
            while (frontier := {
                output_node for node
                in frontier
                for output_node in node.outputs_that_are_not_flip_flops
            }):
                yield frontier

        @property
        def fault_propagation_path(self) -> Generator[Set['ScanNode'], None, None]:
            a: Set[ScanNode]
            b: Set[ScanNode]
            for a, b in zip_longest(
                self.node_propagation_path(self.faulty_node), self.flip_flop_propagation_path, fillvalue={}
            ):
                yield a.union(b)


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

    @property
    def propagation_path(self) -> Generator[Set['Node'], None, None]:
        return self.output_nodes[0].propagation_path
