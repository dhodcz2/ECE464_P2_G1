import unittest
# from remaining_faults import Fault
# from remaining_faults import Fault
import functools
from time import time
from functools import singledispatch, lru_cache
from typing import List, Type, Union, Any, Dict, Optional, Tuple, Iterable, Iterator, Set, Generator


class Value:
    # __slots__ = 'value', 'key'

    __init__map = {0: 0, "0": 0, '1': 1, 1: 1, "D": "D", "d": "D",
                   "D'": "D'", "d'": "D'", "U": "U", "u": "U"}

    __key__map = {0: "_zero", 1: "_one", 'U': '_unknown', "D'": "_dprime", 'D': '_d'}

    @lru_cache(5)
    def __new__(cls, value):
        return super(Value, cls).__new__(cls)

    def __init__(self, value: Union[str, int]):
        try:
            self.value = Value.__init__map[value]
        except KeyError:
            raise Value(f"Cannot be turned into Value: {value}")
        self.key = self.__key__map[self.value]

    @lru_cache(25)
    def __eq__(self, other):
        return self is other

    @lru_cache(5)
    def __invert__(self) -> 'Value':
        if self is value_0:
            return value_1
        elif self is value_1:
            return value_0
        elif self is value_D:
            return value_DP
        elif self is value_DP:
            return value_D
        else:
            return value_U

    @lru_cache(5)
    def __bool__(self):
        if self is value_U:
            return False
        else:
            return True

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    @functools.cached_property
    def propagates_fault(self) -> bool:
        if self is value_0 or self is value_1 or self is value_U:
            return False
        else:
            return True


value_1 = Value(1)
value_0 = Value(0)
value_D = Value("D")
value_DP = Value("D'")
value_U = Value("U")


class Gate:
    def __subclasscheck__(self, subclass):
        return subclass in (AndGate, InputFault, NandGate, OrGate, NorGate, XorGate, XnorGate,
                            BuffGate, NotGate, FlipFlop)

    # __slots__ = 'name', 'type', 'node', 'input_names', 'value', 'value_new', '_zero', \
    #              '_one', '_unknown', '_dprime', '_d'
    def __init__(self, name: str):
        self.name = name
        self.type: str = "WIRE"
        self.node: Optional[Node] = None
        self.input_names: List[str] = []
        self.value: Value = value_U
        self.value_new: Value = value_U

        self._zero = False
        self._one = False
        self._unknown = False
        self._dprime = False
        self._d = False

    def __repr__(self):
        return f"{self.name} = {self.value}"

    @property
    def input_nodes(self) -> List['Node']:
        return self.node.input_nodes

    @property
    def output_nodes(self) -> List['Node']:
        return self.node.output_nodes

    def update(self):
        self.value = self.value_new

    def _reset_logic(self):
        self._zero = False
        self._one = False
        self._unknown = False
        self._dprime = False
        self._d = False

    def logic(self) -> Value:
        return self.value

    @property
    def stuck_at(self):
        return self.node.stuck_at


class Node:
    # __slots__ = 'gate', 'input_nodes', 'output_nodes', 'stuck_at', 'vector_assignment', \
    # 'type', 'corridor', 'implication'
    def __init__(self, gate: Gate):
        gate.node = self
        self.gate: Union[Gate, FlipFlop] = gate
        self.input_nodes: List[Node, InputFault] = []
        self.output_nodes: List[Node, InputFault] = []
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
        if not stuck_at:
            return value
        elif stuck_at is value_1:
            if value is value_0:
                return value_DP
            else:
                return value
        else:
            if value is value_1:
                return value_D
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

    # @property
    # def propagation_path(self) -> Generator[Set['Node'], None, None]:
    #     yield (frontier := {self})
    #     while (frontier := {
    #         output_node for node
    #         in frontier
    #         for output_node in node.output_nodes
    #     }):
    #         yield frontier
    @functools.cached_property
    def propagation_path(self) -> List[Set['Node']]:
        result = [frontier := {self}]
        while (frontier := {
            output_node for node
            in frontier
            for output_node in node.output_nodes
        }):
            result.append(frontier)
        return result

    @functools.cached_property
    def outputs_that_are_not_flip_flops(self) -> List['Node']:
        return [output_node for output_node in self.output_nodes if not isinstance(output_node.gate, FlipFlop)]


class InputFault(Node):
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


class AndGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "AND"

    def logic(self) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            if node.value is value_0:
                return value_0
            self.__dict__[node.value.key] = True
        return self._logic(self._d, self._dprime, self._unknown)

    @staticmethod
    @lru_cache(8)
    def _logic(_d, _dprime, _unknown):
        if _d and _dprime:
            return value_0
        elif _unknown:
            return value_U
        elif _d:
            return value_D
        elif _dprime:
            return value_DP
        return value_1


class NandGate(AndGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NAND"

    def logic(self) -> Value:
        return ~(super().logic())


class OrGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "OR"

    def logic(self) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            if node.value is value_1:
                return value_1
            self.__dict__[node.value.key] = True
        return self._logic(self._d, self._dprime, self._unknown)

    @staticmethod
    @lru_cache(25)
    def _logic(_d, _dprime, _unknown):
        if _d and _dprime:
            return value_1
        elif _unknown:
            return value_U
        elif _d:
            return value_D
        elif _dprime:
            return value_DP
        else:
            return value_0


class NorGate(OrGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NOR"

    def logic(self) -> Value:
        return ~(super().logic())


class XorGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "XOR"

    _xor_map = {
        value_1: True,
        value_DP: True,
        value_D: True
    }

    def logic(self) -> Value:
        self._reset_logic()
        d_acceptable = True
        dprime_acceptable = True
        for node in self.input_nodes:
            if self._one and node.value is value_1:
                return value_0
            elif self._dprime and node.value is value_DP:
                dprime_acceptable = False
            elif self._dprime and node.value is value_D:
                d_acceptable = False
            self.__dict__[node.value.key] = True
        return self._logic(self._one, self._d, self._dprime, self._unknown,
                           d_acceptable, dprime_acceptable)

    @staticmethod
    @lru_cache(64)
    def _logic(one, d, dprime, unknown, d_acceptable, dprime_acceptable):
        if unknown:
            return value_U
        if dprime and d:
            if one:
                return value_0
            elif d_acceptable and dprime_acceptable:
                return value_1
            elif d_acceptable:
                return value_D
            elif dprime_acceptable:
                return value_DP
            else:
                return value_0
        elif dprime:
            if one:
                return value_D
            elif dprime_acceptable:
                return value_DP
            else:
                return value_0
        elif d:
            if one:
                return value_DP
            elif d_acceptable:
                return value_D
            else:
                return value_0
        else:
            return value_0


class XnorGate(XorGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "XNOR"

    def logic(self) -> Value:
        return ~(super(XnorGate, self).logic())


class BuffGate(Gate):
    def __init__(self, name: str):
        super(BuffGate, self).__init__(name)
        self.type = "BUFF"

    def logic(self) -> Value:
        return self.input_nodes[0].value


class NotGate(BuffGate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "NOT"

    def logic(self) -> Value:
        return ~self.input_nodes[0].value


class FlipFlop(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "DFF"
        self.data = value_U
        self.data_new = value_U

    def logic(self) -> Value:
        return self.input_nodes[0].value

    @property
    def value(self) -> Value:
        return self.data

    @value.setter
    def value(self, val: Value):
        self.data_new = val

    @property
    def value_new(self):
        return self.data_new

    @value_new.setter
    def value_new(self, val: Value):
        self.data_new = val

    def capture(self):
        self.data = self.data_new

    def clear(self):
        self.data = self.node.vector_assignment
        self.data_new = self.node.vector_assignment
