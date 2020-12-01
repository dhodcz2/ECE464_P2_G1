from nodes import Node, Value
import functools


class Fault:
    # __slots__ = ('node', 'input_node', 'stuck_at', '_hash')

    def __init__(self, node: Node, stuck_at: Value, input_node: Node = None):
        self.node = node
        self.input_node = input_node
        self.stuck_at = stuck_at

    def __repr__(self):
        if self.input_node:
            return "%s-%s-%s" % (self.node.name, self.input_node.name, self.stuck_at)
        else:
            return "%s-%s" % (self.node.name, self.stuck_at)

    @functools.cached_property
    def hash(self):
        return hash(repr(self))

    def __hash__(self):
        return self.hash

    # def __eq__(self, fault: str):
    #     return repr(self) == fault
