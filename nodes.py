import unittest
import functools
import copy
from time import time
from random import randint
from functools import singledispatch, lru_cache
from itertools import zip_longest
from typing import List, Type, Union, Any, Dict, Optional, Tuple, Iterable, Iterator, Set
from dataclasses import dataclass


class Value:
    @lru_cache(5)
    def __new__(cls, value):
        return super(Value, cls).__new__(cls)

    __init__map = {0: 0, "0": 0, '1': 1, 1: 1, "D": "D", "d": "D",
                   "D'": "D'", "d'": "D'", "U": "U", "u": "U"}

    __key__map = {0: "_zero", 1: "_one", 'U': '_unknown', "D'": "_dprime", 'D': '_d'}

    def __init__(self, value: Union[str, int]):
        try:
            self._value = Value.__init__map[value]
        except KeyError:
            raise Value(f"Cannot be turned into Value: {value}")
        self.key = self.__key__map[self.value]

    def __eq__(self, other):
        return self is other

    @property
    def value(self):
        return self._value

    @functools.cached_property
    def __invert__map(self) -> Dict['Value', 'Value']:
        return {
            value_0: value_1,
            value_1: value_0,
            value_U: value_U,
            value_D: value_DP,
            value_DP: value_D
        }

    def __invert__(self) -> 'Value':
        return self.__invert__map[self]

    def __bool__(self):
        return False if self is value_U else True

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __hash__(self):
        return hash(self.value)

    def __iter__(self):
        yield self

    def __getitem__(self, item):
        return self.value


value_1 = Value(1)
value_0 = Value(0)
value_D = Value("D")
value_DP = Value("D'")
value_U = Value("U")


class HighResolutionValue:
    @functools.cached_property
    def __new__map(self):
        return {
            (value_1, value_1): value_1,
            (value_0, value_0): value_0,
            (value_1, value_0): value_D,
            (value_0, value_1): value_DP,
            (value_U, value_U): value_U
        }

    @classmethod
    @lru_cache(4)
    def hrv_is_not_redundant(cls):
        return super(HighResolutionValue, cls).__new__(cls)

    def __new__(cls, values: Tuple[Value, Value]):
        return cls.__new__map.get(
            values, cls.hrv_is_not_redundant()
        )
        # return HighResolutionValue.__new__map.get(
        #     values, cls.hrv_is_not_redundant()
        # )

    def __init__(self, values: Tuple[Value, Value]):
        self.value = values

    def __eq__(self, other: Union['HighResolutionValue']):
        for self_value, other_value in zip_longest(self, other):
            if self_value != other_value:
                return False
        return True

    def __bool__(self):
        return True

    def __repr__(self):
        return str(self.value[0]) + '/' + str(self.value[1])

    def __hash__(self):
        return hash(str(self))

    def __getitem__(self, item) -> Value:
        return self.value[item]

    @property
    def good(self):
        return self.value[0]

    @property
    def bad(self):
        return self.value[1]


class Gate:
    def __init__(self, name: str):
        self.name = name
        self.type: str = ''
        self.node: Optional[Node] = None
        self.input_names: List[str] = []
        self.value: Union[Value, HighResolutionValue] = value_U
        self.value_new: Union[Value, HighResolutionValue] = value_U

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

    def _set_true(self, x):
        self.__dict__[x] = True

    def _reset_logic(self):
        self._zero = False
        self._one = False
        self._unknown = False
        self._dprime = False
        self._d = False

    def logic(self) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            self.__dict__[node.value.key] = True
        # return self.input_nodes[0].value
        return self.value

    def logic_high_res(self, index: int) -> Value:
        self._reset_logic()
        for node in self.input_nodes:
            setattr(self, Gate._logic_map[node.value[index]], True)
        return self.input_nodes[0].value[0]

    @property
    def stuck_at(self):
        return self.node.stuck_at

class Node:
    def __init__(self, gate: Gate):
        gate.node = self
        self.gate = gate
        self.input_nodes: List[Node] = []
        self.output_nodes: List[Node] = []
        self.stuck_at: Optional[Value] = None
        self.vector_assignment: Optional[Value] = None

    def __getitem__(self, item: int) -> Value:
        return self.value[item]

    def __repr__(self):
        return self.name

    def __str__(self):
        return f"{self.type}{self.name} = {self.value}"

    def __hash__(self):
        return hash(self.name)

    @property
    def type(self) -> str:
        return self.gate.type

    @property
    def name(self) -> str:
        return self.gate.name

    @property
    def value(self) -> Union[Value, HighResolutionValue]:
        return self.gate.value

    @value.setter
    def value(self, val: Union[Value, HighResolutionValue]):
        self.gate.value = val

    @property
    def value_new(self) -> Union[Value, HighResolutionValue]:
        return self.gate.value_new

    @value_new.setter
    def value_new(self, val: Union['Value', HighResolutionValue]):
        self.gate.value_new = val

    def reset(self):
        self.gate.value = value_U
        self.gate.value_new = value_U

    def undo_fault(self):
        self.reset_fault_corridor()
        self.stuck_at = None
        if self.vector_assignment:
            self.value = self.vector_assignment
            self.value_new = self.vector_assignment

    def logic(self):
        self.value_new = self.propagate_fault(self.gate.logic(), self.stuck_at)

    def update(self):
        self.value = self.value_new

    def propagate_high_resolution(self):
        self.value_new = HighResolutionValue(
            (self.gate.logic_high_res(0), self.gate.logic_high_res(1))
        )

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

    def reset_fault_corridor(self):
        self.reset()
        for node in self.output_nodes:
            node.reset()
            node.reset_fault_corridor()


class DummyNode(Node):
    def __init__(self, output_node: Node, node: Node, stuck_at: Value):
        self.genuine_node = node
        self.gate = type(node.gate)(node.gate.name)
        self.gate.node = self
        self.input_nodes = node.input_nodes
        self.output_nodes = [output_node]
        self.stuck_at = stuck_at
        for input_node in self.input_nodes:
            input_node.output_nodes.append(self)

    @property
    def name(self):
        return "%s Dummy" % self.genuine_node.name

    def undo_fault(self):
        self.reset_fault_corridor()
        self.output_nodes[0].input_nodes.remove(self)
        self.output_nodes[0].input_nodes.append(self.genuine_node)
        for input_node in self.input_nodes:
            input_node.output_nodes.remove(self)


class AndGate(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "AND"

    def logic(self):
        super(AndGate, self).logic()
        if self._zero:
            return value_0
        elif self._d and self._dprime:
            return value_0
        elif self._d:
            return value_D
        elif self._dprime:
            return value_DP
        else:
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
        super().logic()
        if self._one:
            return value_1
        elif self._d and self._dprime:
            return value_1
        elif self._unknown:
            return value_U
        elif self._d:
            return value_D
        elif self._dprime:
            return value_DP
        else:
            return value_0


class NorGate(OrGate):
    def __init__(self, name):
        super().__init__(name)

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
        # TODO: Optimization
        self._zero = False
        self._one = False
        self._unknown = False
        self._dprime = False
        self._d = False
        d_acceptable = True
        dprime_acceptable = True
        for node in self.input_nodes:
            if self._one and node.value is value_1:
                return value_0
            elif self._dprime and node.value is value_DP:
                dprime_acceptable = False
            elif self._d and node.value is value_D:
                d_acceptable = False
            # setattr(self, Gate._logic_map[value], True)
        if not dprime_acceptable and not d_acceptable:
            return value_0
        elif self._unknown:
            return value_U
        elif self._d and d_acceptable:
            return value_D
        elif self._dprime and dprime_acceptable:
            return value_DP
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
        self.type = "NOR"

    def logic(self) -> Value:
        if isinstance(super(NotGate, self).logic(), type):
            print()
        return ~(super(NotGate, self).logic())


class FlipFlop(Gate):
    def __init__(self, name):
        super().__init__(name)
        self.type = "DFF"
        self.data = value_U

    @property
    def value(self) -> Union[Value, HighResolutionValue]:
        return self.data

    def capture(self):
        self.data = self.value_new


# values_2 = [value_0, value_0, value_0]
# start = time()
# for _ in range(0, 10000):
#     assert values_2[0] is value_0
# end = time()
# print("By is: ", end - start)
# start = time()
# for _ in range(0, 10000):
#     assert values_2[0] == value_0
# end = time()
# print("By =: ", end - start)

# x = HighResolutionValue((value_0, value_U))
# y = HighResolutionValue((value_0, value_U))
# print(x is y)
# a = HighResolutionValue((value_0, value_1))
# print(a is value_DP)

# class Gate:
#     def __init__(self, name: str):
#         self.name = name
#         self.input_names: List[str] = []
#         # self.type: str
#         # self.node: Node = None
#         self.value: Value = value_U
#
#
# class Node:
#     def __init__(self, gate: Gate):
#         self.gate = gate
#         self.gate.node = self
#         self.update = gate.update
# class ValueTest(unittest.TestCase):
#     def test_1(self):
#         self.assertTrue(value_1 is value_1)
#         self.assertTrue(value_U is value_U)
#         self.assertTrue(value_D is value_D)
#         self.assertFalse(value_1 is value_0)
#         self.assertFalse(value_D is value_DP)
#
#     def test_2(self):
#         self.assertTrue(~value_1 is value_0)
#         self.assertTrue(~value_0 is not value_0)
#         self.assertTrue(~value_U is value_U)
#
#     def test_3(self):
#         self.assertTrue(value_1)
#         self.assertTrue(value_D)
#         self.assertFalse(value_U)
#
#
#
# class LogicTest(unittest.TestCase):
#     def setUp(self) -> None:
#         super().setUp()
#         self.zero = Node(Gate('zero'))
#         self.zero.value = value_0
#         self.one = Node(Gate('one'))
#         self.one.value = value_1
#         self.unknown = Node(Gate('unknown'))
#         self.unknown.value = value_U
#         self.sa0 = Node(Gate('sa0'))
#         self.sa0.value = value_D
#         self.sa1 = Node(Gate('sa1'))
#         self.sa1.value = value_DP


if __name__ == '__main__':
    x = [value_0, value_1, value_U, value_DP, value_D, value_1, value_0, value_DP]
    print()
