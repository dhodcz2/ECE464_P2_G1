from nodes import *


class Value(Value):
    @lru_cache(3)
    def extend(self):
        if self is value_1:
            return value_11
        elif self is value_0:
            return value_00
        elif self is value_U:
            return value_UU
        else:
            raise ValueError("%s" % self)


class HighResolutionValue:
    __slots__ = 'value'

    @lru_cache(9)
    def __new__(cls, good: Value, bad: Value):
        return super(HighResolutionValue, cls).__new__(cls)

    def __init__(self, good: Value, bad: Value):
        self.value = (good, bad)

    def __eq__(self, other: 'HighResolutionValue'):
        return self is other

    def __getitem__(self, item) -> Value:
        return self.value[item]

    @lru_cache(9)
    def _repr(self) -> str:
        if self.value[0] is self.value[1]:
            return str(self.value[0])
        else:
            return '/'.join(str(value) for value in (self.value[0], self.value[1]))

    def __repr__(self):
        return self._repr

    def __hash__(self):
        return hash("%s%s" % (self.value[0], self.value[1]))

    # @functools.cached_property
    # def __invert__map(self) -> Dict['HighResolutionValue', 'HighResolutionValue']:
    #     return {
    #         value_00: value_11, value_11: value_00, value_01: value_10, value_10: value_01,
    #         value_UU: value_UU, value_U1: value_U0, value_U0: value_U1
    #     }

    @lru_cache(9)
    def __invert__(self) -> 'HighResolutionValue':
        return HighResolutionValue(~self.value[0], ~self.value[1])
        # return self.__invert__map[self]

    @property
    def good(self) -> Value:
        return self.value[0]

    @property
    def bad(self) -> Value:
        return self.value[1]


value_UU = HighResolutionValue(Value('U'), Value('U'))
value_11 = HighResolutionValue(Value(1), Value(1))
value_00 = HighResolutionValue(Value(0), Value(0))
value_10 = HighResolutionValue(Value(1), Value(0))
value_01 = HighResolutionValue(Value(0), Value(1))
value_U1 = HighResolutionValue(Value('U'), Value(1))
value_U0 = HighResolutionValue(Value('U'), Value(0))
value_1U = HighResolutionValue(Value(1), Value('U'))
value_0U = HighResolutionValue(Value(0), Value('U'))


class Node(Node):
    def __init__(self, gate: Gate):
        gate.node = self
        self.gate = gate
        self.input_nodes: List['Node', InputFault] = []
        self.output_nodes: List['Node', InputFault] = []
        self.stuck_at: Optional[Value] = None
        self.type = "INTERM."
        self.vector_assignment: HighResolutionValue = value_UU
        self.implication = value_UU

    @property
    def value(self) -> HighResolutionValue:
        return self.gate.value

    @value.setter
    def value(self, val: HighResolutionValue):
        self.gate.value = val

    @property
    def value_new(self) -> HighResolutionValue:
        return self.gate.value_new

    @value_new.setter
    def value_new(self, val: HighResolutionValue):
        self.gate.value_new = val

    def logic(self):
        self.value_new = self.propagate_fault(self.gate.logic(), self.stuck_at)

    @staticmethod
    @lru_cache(27)
    def propagate_fault(value: HighResolutionValue, stuck_at: Value):
        if stuck_at:
            return HighResolutionValue(value[0], stuck_at)
        else:
            return HighResolutionValue(value[0], value[1])

    @lru_cache(9)
    def propagates_fault(self) -> bool:
        if self is value_01 or self is value_10 or self is value_U0 or self is value_U1:
            return True
        else:
            return False


class Gate(Gate):
    def __init__(self, name: str):
        self.name = name
        self.type: str = "WIRE"
        self.node: Optional[Node] = None
        self.input_names: List[str] = []
        self.value: HighResolutionValue = value_UU
        self.value_new: HighResolutionValue = value_UU
        self._zero = False
        self._one = False
        self._unknown = False
        self._dprime = False
        self._d = False

    @property
    def input_nodes(self) -> List[Node]:
        return self.node.input_nodes

    @property
    def output_nodes(self) -> List[Node]:
        return self.node.output_nodes

    def _logic(self, index) -> Value:
        # return self.input_nodes[0].value[index]
        return self.value[index]

    def logic(self) -> HighResolutionValue:
        return HighResolutionValue(self._logic(0), self._logic(1))

    def update(self):
        self.value = self.value_new


class InputFault(InputFault):
    def __init__(self, output_node: Node, node: Node, stuck_at: Value):
        super(InputFault, self).__init__(output_node, node, stuck_at)


class AndGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "AND"

    def _logic(self, index) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            if node.value[index] is value_0:
                return value_0
            self.__dict__[node.value_key] = True
        return self._logic(self._unknown)

    @staticmethod
    @lru_cache(2)
    def __logic(_unknown):
        if _unknown:
            return value_U
        else:
            return value_1


class NandGate(AndGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NAND"

    def logic(self) -> HighResolutionValue:
        return ~super(NandGate, self).logic()


class OrGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "OR"

    def _logic(self, index) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            if node.value[index] is value_0:
                return value_0
            self.__dict__[node.value_key] = True
        return self._logic(self._unknown)

    @staticmethod
    @lru_cache(2)
    def __logic(_unknown):
        if _unknown:
            return value_U
        else:
            return value_0


class NorGate(OrGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NOR"

    def logic(self) -> HighResolutionValue:
        return ~super(OrGate, self).logic()


class XorGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "XOR"

    def _logic(self, index) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            if self._one and node.value is value_1:
                return value_0
            self.__dict__[node.value.key] = True
        return self.__logic(self._one, self._unknown)

    @staticmethod
    @lru_cache(4)
    def __logic(_one, _unknown):
        if _unknown:
            return value_U
        elif _one:
            return value_1
        else:
            return value_0


class XnorGate(XorGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "XNOR"

    def logic(self) -> HighResolutionValue:
        return ~super(XorGate, self).logic()


class BuffGate(Gate):
    def __init(self, name: str):
        super(BuffGate, self).__init__(name)
        self.type = "BUFF"

    def logic(self) -> HighResolutionValue:
        return self.input_nodes[0].value


class NotGate(BuffGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NOT"

    def logic(self) -> HighResolutionValue:
        return ~self.input_nodes[0].value


class FlipFlop:
    def __init__(self, name: str):
        self.name = name
        self.type: str = "WIRE"
        self.node: Optional[Node] = None
        self.input_names: List[str] = []
        self.data: HighResolutionValue = value_UU
        self.value_new: HighResolutionValue = value_UU
        self.vector_assignment: HighResolutionValue = value_UU

    @property
    def input_nodes(self) -> List[Node]:
        return self.node.input_nodes

    @property
    def output_nodes(self) -> List[Node]:
        return self.node.output_nodes

    @property
    def value(self):
        return self.data

    @value.setter
    def value(self, val: HighResolutionValue):
        pass

    def logic(self) -> HighResolutionValue:
        return self.input_nodes[0].value

    def capture(self):
        self.value = self.value_new
