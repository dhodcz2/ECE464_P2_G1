from nodes import Node, Value


class Fault:
    __slots__ = ('node', 'input_node', 'stuck_at')

    def __init__(self, node: Node, stuck_at: Value, input_node: Node = None):
        self.node = node
        self.input_node = input_node
        self.stuck_at = stuck_at

    def __repr__(self):
        if self.input_node:
            return "%s-%s-%s" % (self.node.name, self.input_node.name, self.stuck_at)
        else:
            return "%s-%s" % (self.node.name, self.stuck_at)

    def __hash__(self):
        return hash(repr(self))

    # def __eq__(self, fault: str):
    #     return repr(self) == fault
