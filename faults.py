import functools
from typing import List, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from nodes import *
from testvector import TestVector, TestVectorGenerator
import csv


class Fault:
    def __init__(self, node: Node, stuck_at: Value, input_node: Node = None):
        # if input_node and input_node not in node.input_nodes:
        #     raise ValueError(f"{input_node.name} not in {node.name} inputs")
        # if stuck_at is not  and stuck_at is not value_1:
        #     raise ValueError(f"{stuck_at} is not a correct fault value")
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

    def __eq__(self, other):
        return hash(self) == hash(other)
