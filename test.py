from typing import List, Union
from time import time
from random import randint
from dataclasses import dataclass


class TestClass:
    def __init__(self):
        self.values = [randint(1, 5) for _ in range(0, 2)]

    def __repr__(self):
        return str(self.values)


_count_mapping = {
    1: 'one',
    2: 'two',
    3: 'three',
    4: 'four',
    5: 'five'
}


@dataclass
class Count:
    one: int = 0
    two: int = 0
    three: int = 0
    four: int = 0
    five: int = 0

    @classmethod
    def from_map(cls, test_class: TestClass):
        obj = cls()
        for value in test_class.values:
            obj.__dict__[
                _count_mapping[value]
            ] += 1
        return obj

    @classmethod
    def from_if_else(cls, test_class: TestClass):
        obj = cls()
        for value in test_class.values:
            if value == 1:
                obj.one += 1
            elif value == 2:
                obj.two += 1
            elif value == 3:
                obj.three += 1
            elif value == 4:
                obj.four += 1
            elif value == 5:
                obj.five += 1
        return obj

test_classes = [TestClass() for _ in range(0, 100000)]
begin = time()
counts_by_map = [Count.from_map(test_class) for test_class in test_classes]
end = time()
print(f"By map took {end-begin}")
begin = time()
counts_by_if_else = [Count.from_if_else(test_class) for test_class in test_classes]
end = time()
print(f"By if else took {end-begin}")
print()