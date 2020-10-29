from typing import List, Union

from nodes import Value
import nodes
from nodes import Node




class TestVector(object):
    def __init__(self, string: str):
        self.values: List[Value]
        for char in string:
            assert char == '0' or char == '1'
            bit = Value(char)

            self.values.append(bit)

    def __str__(self):
        # TODO: Return a string representation of the test vector, each 4 bits have a space
        "0001 0010 0011 0100"
        pass

    def __iter__(self):
        # TODO: Use the yield keyword to create an iterable, returning the bits of the object
        # TODO: This should work on an outer scope:
        for value in self.values:
            yield
        pass

    def __len__(self):
        pass
        # TODO: return length of values


def rotate_left(number: int, by: int, size: int) -> int:
    return (number << by % size) & (2 ** size) | \
           ((number & (2 ** size - 1)) >> (size - (by % size)))


class TestVectorSeed(object):
    def __init__(self, seed: int, n_bit: int, taps: List[int] = None):
        for tap in taps:
            if tap > n_bit or tap <= 0:
                raise ValueError(f"Invalid tap value: {tap}")

        self.seed = seed
        self.seed_bits = n_bit if n_bit > seed.bit_length() else seed.bit_length()
        self.bits = n_bit
        self.taps = taps

    def __str__(self):
        # TODO: See TestVector.__str__()
        pass

    def __call__(self) -> TestVector:
        # TODO: Implement LFSR, updating self.seed and generating a test vector
        pass

    def update_seed(self):
        # TODO: Rotate seed, and apply taps
        pass
