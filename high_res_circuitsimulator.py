from high_res_nodes import *
from circuitsimulator import *


class HighResCircuitSimulator(CircuitSimulator):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        gates = self.LineParser(kwargs['bench']).parse_file()
        self.nodes = self.compile(gates)
        self.faulty_node: Optional[Node, InputFault ] = None
        self.fault: Optional[Fault] = None
        self.active_nodes: Set[Node] = set()
        self.leftover_nodes: Set[Node] = set()
        self.faulty_node: Set[Node] = set()
        self.tv = None
        self.tv_lookup: DefaultDict[TestVector, Set[Fault]] = defaultdict(self)

    @functools.cached_property
    def initial_frontier(self) -> Set[Node]:
        return {
            output_node for node
            in self.nodes.input_nodes.values()
            for output_node in node.output_nodes
        }.union(
            output_node for node
            in self.nodes.flip_flops
            for output_node in node.output_nodes
        )

    @functools.cached_property
    def scan(self) -> List[Node]:
        return [*self.nodes.input_nodes, *self.nodes.flip_flops]

    def detect_faults(self, test_vector: TestVector) -> List[Fault]:
        self.apply_vector(test_vector)
        result: List[HighResolutionValue]

    def apply_vector(self, test_vector: TestVector):
        self.active_nodes = self.initial_frontier.copy()
        nodes = itertools.chain(self.nodes.input_nodes.values(), self.nodes.flip_flops)
        for node, value in zip(nodes, test_vector):
            node.vector_assignment = value
            node.value = node.vector_assignment

    @functools.cached_property
    def ff_length(self) -> int:
        return len(self.nodes.flip_flops)

    @functools.cached_property
    def flip_flop_resolution_length(self) -> int:
        """How many cycles must be run for a fault to be detected in any flip flop"""
        try:
            return max(
                self._flip_flop_length(flip_flop)
                for flip_flop in self.nodes.flip_flops
            )
        except ValueError:
            return 0

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

    class LineParser(CircuitSimulator.LineParser):
        @functools.cached_property
        def gate_map(self):
            return {"AND": AndGate, "OR": OrGate, "NAND": NandGate, "XNOR": XnorGate,
                    "NOR": NorGate, "BUFF": BuffGate, "XOR": XorGate, "NOT": NotGate,
                    "DFF": FlipFlop}

