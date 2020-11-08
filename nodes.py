import unittest
from typing import List, Type, Union, NamedTuple, Any
from dataclasses import dataclass
from copy import copy, deepcopy

class Value(object):
    @property
    def value(self):
        return self._value

    def __init__(self, value: Union[str, int]):
        if value == 0 or value == '0':
            self._value = 0
        elif value == 1 or value == '1':
            self._value = 1
        elif value == "D" or value == "d":
            self._value = "D"
        elif value == "D'" or value == "d'":
            self._value = "D'"
        elif value == "U" or value == "u":
            self._value = "U"
        else:
            raise ValueError(f"Cannot be turned into error: {value}")

    def __eq__(self, other):
        if self.value == 1:
            if other == 1 or other == '1':
                return True
        elif self.value == 0:
            if other == 0 or other == '0':
                return True
        elif self.value == 'U':
            if other == 'U' or other == 'u':
                return True
        elif self.value == 'D':
            if other == 'd' or other == 'D':
                return True
        elif self.value == "D'":
            if other == "d'" or other == "D'":
                return True
        return False

    def __and__(self, other):
        if self == 1:
            if other == 1:
                return Value('1')
            if other == 'U':
                return Value('U')
        return Value('0')

    def __or__(self, other):
        if self == 1 or other == 1:
            return Value(1)
        if self == 'U' or other == 'U':
            return Value('U')
        return Value(0)

    def __invert__(self):
        if self == 1:
            return Value(0)
        if self == 0:
            return Value(1)
        if self == 'D':
            return Value("D'")
        if self == "D'":
            return Value('D')
        return Value('U')

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    # def __hash__(self):
    #     return hash(self.value)


class Node(object):
    def __init__(self, gate: 'Gate'):
        self.gate: Gate = gate
        self.gate.node: Node = self
        # self.name: str = gate.name
        self.gate_type: str = gate.type
        self.update = gate.update
        self.logic = gate.logic
        self.type: str = 'wire'
        self.input_nodes: List[Node] = []
        self.output_nodes: List[Node] = []
        self.stuck_at: Union[None, Value] = None

    @property
    def name(self):
        return self.gate.name

    @property
    def value(self):
        return self.gate.value

    @value.setter
    def value(self, value: Value):
        self.gate.value = value

    @property
    def value_new(self):
        return self.gate.value_new

    @value_new.setter
    def value_new(self, value: Value):
        self.gate.value_new = value

    @property
    def input_names(self):
        return [input_node.name for input_node in self.input_nodes]

    def __eq__(self, other: Union['Node', Any]):
        if type(other) == Node:
            if self.name == other.name:
                return True
            else:
                return False
        else:
            if self.value == other:
                return True
            else:
                return False
        # if self.value == other:
        #     return True
        # else:
        #     return False

    def __repr__(self):
        return self.name
        # return "repr"

    def __str__(self):
        return f"{self.type}\t{self.name} = {self.value}"

    def __hash__(self):
        return hash(self.name)

    # def __del__(self):
    #     del self.gate

    def reset(self):
        self.value = Value('U')
        self.value_new = Value('U')
        self.stuck_at = None

    def set(self, value: Value):
        self.value = value
        self.value_new = value

    def show_update(self):
        return ", ".join([str(node.value) for node in self.input_nodes]) + \
               f"equals {self.value}"


class DummyNode(Node):
    def __init__(self, node: Node, stuck_at: Value):
        self.genuine = node
        gate_copy = copy(node.gate)
        super(DummyNode, self).__init__(gate=gate_copy)
        self.input_nodes = node.input_nodes
        self.stuck_at = stuck_at

    @property
    def name(self):
        return self.genuine.name + " Dummy"





    # @property
    # def value(self):







class Gate(object):
    def __init__(self, name: str, inputs=[]):
        self.input_names: List[str] = inputs
        self.name: str = name
        self.type: str = ''
        self.node: Union[Node, None] = None
        self._value: Value = Value('U')
        self._value_new: Value = Value('U')


    #     return hash(self.name)

    def __repr__(self):
        return self.name

    def propagate(self, value):
        if value == 1 and self.stuck_at == 0:
            return Value("D")
        elif value == 0 and self.stuck_at == 1:
            return Value("D'")
        else:
            return value

    @property
    def value(self) -> Value:
        return self.propagate(self._value)



    @value.setter
    def value(self, value: Value):
        self._value = value

    @property
    def value_new(self) -> Value:
        return self.propagate(self._value_new)

    @value_new.setter
    def value_new(self, value: Value):
        self._value_new = value

    @property
    def input_nodes(self) -> List[Node]:
        return self.node.input_nodes

    @property
    def output_nodes(self) -> List[Node]:
        return self.node.output_nodes

    @property
    def stuck_at(self) -> Union[None, Value]:
        return self.node.stuck_at

    def update(self):
        if self.value_new == 1 and self.stuck_at == 0:
            self.value = Value("D")
        elif self.value_new == 0 and self.stuck_at == 1:
            self.value = Value("D'")
        else:
            self.value = self.value_new

    def logic(self):
        # Do not change
        pass

    @dataclass
    class Count:
        zero: int = 0
        one: int = 0
        unknown: int = 0
        d: int = 0
        dprime: int = 0
        input: int = 0

    @property
    def count(self) -> Count:
        count = self.Count()
        for node in self.input_nodes:
            count.input += 1
            if node == 0:
                count.zero += 1
            elif node == 1:
                count.one += 1
            elif node == "d'":
                count.dprime += 1
            elif node == "d":
                count.d += 1
            elif node == 'u':
                count.unknown += 1
            else:
                raise ValueError
        return count


class AndGate(Gate):
    def __init__(self, name, inputs=[]):
        super(AndGate, self).__init__(name, inputs)
        self.type = "AND"

    def logic(self):
        count = self.count
        if count.zero:
            self.value_new = Value(0)
        elif count.unknown:
            self.value_new = Value('U')
        elif count.d and count.dprime:
            self.value_new = Value(0)
        elif count.d:
            self.value_new = Value("D")
        elif count.dprime:
            self.value_new = Value("D'")
        else:
            self.value_new = Value(1)


class NandGate(AndGate):
    def __init__(self, name, inputs=[]):
        super(AndGate, self).__init__(name, inputs)
        self.type = "NAND"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class OrGate(Gate):
    def __init__(self, name, inputs=[]):
        super(OrGate, self).__init__(name, inputs)
        self.type = "OR"

    def logic(self):
        count = self.count
        if count.one:
            self.value_new = Value(1)
        elif count.d and count.dprime:
            self.value_new = Value(1)
        elif count.unknown:
            self.value_new = Value('U')
        elif count.d:
            self.value_new = Value("D")
        elif count.dprime:
            self.value_new = Value("D'")
        else:
            self.value_new = Value(0)


class NorGate(OrGate):
    def __init__(self, name, inputs=[]):
        super(OrGate, self).__init__(name, inputs)
        self.type = "NOR"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class NotGate(Gate):
    def __init__(self, name, inputs=[]):
        super(NotGate, self).__init__(name, inputs)
        self.type = "NOT"

    def logic(self):
        self.value_new = ~self.input_nodes[0].value


class XorGate(Gate):
    def __init__(self, name, inputs=[]):
        super(XorGate, self).__init__(name, inputs)
        self.type = "XOR"

    def logic(self):
        count = self.count
        if count.one > 1:
            return Value(0)
        elif count.unknown >= 1:
            return Value("U")
        elif count.one == 1:
            return Value(1)
        elif count.d == 1 and count.dprime == 1:
            return Value(1)
        elif count.d == 1:
            return Value("D")
        elif count.dprime == 1:
            return Value("D'")
        else:
            return Value(0)


class XnorGate(XorGate):
    def __init__(self, name, inputs=[]):
        super(XorGate, self).__init__(name, inputs)
        self.type = "XNOR"

    def logic(self):
        super().logic()
        self.value_new = ~self.value_new


class BuffGate(Gate):
    def __init__(self, name, inputs=[]):
        super(BuffGate, self).__init__(name, inputs)
        self.type = "BUFF"

    def logic(self):
        self.value_new = self.input_nodes[0].value


class LogicTest(unittest.TestCase):
    def setUp(self):
        super(LogicTest, self).setUp()
        self.zero = Node(Gate('zero'))
        self.zero.value = Value(0)
        self.one = Node(Gate('one'))
        self.one.value = Value(1)
        self.unknown = Node(Gate('unknown'))
        self.unknown.value = Value('U')
        self.sa0 = Node(Gate('sa0'))
        self.sa0.value = Value('D')
        self.sa1 = Node(Gate('sa1'))
        self.sa1.value = Value("D'")


class AndTest(LogicTest):
    def setUp(self):
        super(AndTest, self).setUp()
        self.node = Node(AndGate('and'))

    def test_1(self):
        self.node.input_nodes = [self.zero, self.one, self.sa1]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 0, self.node)

    def test_2(self):
        self.node.input_nodes = [self.sa1, self.sa0]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 0, self.node)

    def test_3(self):
        self.node.input_nodes = [self.sa1, self.one]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, "D'", self.node)

    def test_4(self):
        self.node.input_nodes = [self.sa0, self.one]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, "D", self.node)


class NandTest(LogicTest):
    def setUp(self):
        super(NandTest, self).setUp()
        self.node = Node(NandGate('nand'))

    def test_1(self):
        self.node.input_nodes = [self.zero, self.one, self.sa1]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 1, self.node)

    def test_2(self):
        self.node.input_nodes = [self.sa1, self.sa0]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 1, self.node)

    def test_3(self):
        self.node.input_nodes = [self.sa1, self.one]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, "D", self.node)

    def test_4(self):
        self.node.input_nodes = [self.sa0, self.one]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, "D'", self.node)


class OrTest(LogicTest):
    def setUp(self):
        super(OrTest, self).setUp()
        self.node = Node(OrGate('nand'))

    def test_1(self):
        self.node.input_nodes = [self.zero, self.one, self.sa1]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 1, self.node)

    def test_2(self):
        self.node.input_nodes = [self.sa1, self.sa0]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 1, self.node)

    def test_3(self):
        self.node.input_nodes = [self.sa1, self.zero]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, "D'", self.node)

    def test_4(self):
        self.node.input_nodes = [self.sa0, self.sa1]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 1, self.node)

    def test_5(self):
        self.node.input_nodes = [self.sa0, self.unknown]
        self.node.logic()
        self.node.update()
        self.assertEqual(self.node, 'U', self.node)


# class XorTest(LogicTest):
#     def setUp(self):
#         super(XorTest, self).setUp()
#         self.node = Node(XorGate('xor'))
#
#     def test_1(self):
#         self.node.input_nodes = [self.zero, self.one, self.sa1]
#         self.node.logic()
#         self.node.update()
#         self.assertEqual(self.node, "D", self.node)
#
#     def test_2(self):
#         self.node.input_nodes = [self.sa1, self.sa0]
#         self.node.logic()
#         self.node.update()
#         self.assertEqual(self.node, 1, self.node)
#
#     def test_3(self):
#         self.node.input_nodes = [self.sa1, self.zero]
#         self.node.logic()
#         self.node.update()
#         self.assertEqual(self.node, "D'", self.node)

# def test_4(self):
#     self.node.input_nodes = [self.sa1, self.sa1]
#     self.node.logic()
#     self.node.update()
#     self.assertEqual(self.node, 0, self.node)
#
# def test_5(self):
#     self.node.input_nodes = [self.sa0, self.unknown]
#     self.node.logic()
#     self.node.update()
#     self.assertEqual(self.node, 'U', self.node)


if __name__ == '__main__':
    unittest.main()
