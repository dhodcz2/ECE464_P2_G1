from typing import List, Union
import numpy as np
from nodes import Value


class TestVector(object):
    def __init__(self, string: str):
        self.values: List[Value]
        for char in string:
            assert char == '0' or char == '1'
            bit = Value(char)
            self.values.append(bit)

    def __str__(self):
        # TODO: Return a string representation of the test vector, each 4 bits have a space
        # "0001 0010 0011 0100"
        a = 0
        temp = ''
        for value in self.values:
            temp += value  # TODO: change to value in case it doesn't work
            a += 1
            if (a % 4 == 0):
                temp += ' '
        return temp

    def __iter__(self):
        # TODO: Use the yield keyword to create an iterable, returning the bits of the object
        # TODO: This should work on an outer scope:
        # test_vector = TestVector('1111')
        # bit: Value
        # for bit in test_vector:
        #     assert bit == 1
        bit: Value
        for bit in self.values:
            assert bit == '1' or bit == '0'
            yield bit
            # how will this end in a loop externally, perhaps use the function in the for loop condition

    def __len__(self):
        # TODO: return length of values
        return len(self.values)


def rotate_left(number: int, by: int, size: int) -> int:
    return (number << by % size) & (2 ** size) | \
           ((number & (2 ** size - 1)) >> (size - (by % size)))


class LFSR(object):
    # lfsr is 8 bits
    def __init__(self, q, n, h, tv):
        self.q = q
        self.n = n
        self.h = h
        self.test_vector = tv

    def poly(self) -> TestVector:
        array_H = np.array([[0, 0, 0, 0, 0, 0, 0, 1],
                            [1, 0, 0, 0, 0, 0, 0, h[1]],
                            [0, 1, 0, 0, 0, 0, 0, h[2]],
                            [0, 0, 1, 0, 0, 0, 0, h[3]],
                            [0, 0, 0, 1, 0, 0, 0, h[4]],
                            [0, 0, 0, 0, 1, 0, 0, h[5]],
                            [0, 0, 0, 0, 0, 1, 0, h[6]],
                            [0, 0, 0, 0, 0, 0, 1, h[7]]], dtype=bool)
        array_Q = np.array([[q[0]],
                            [q[1]],
                            [q[2]],
                            [q[3]],
                            [q[4]],
                            [q[5]],
                            [q[6]],
                            [q[7]]], dtype=bool)
        # qPrime = arrH.dot(arrQ)
        self.q = array_H.dot(array_Q)

        LFSR_1, LFSR_2

        LFSR_1.first_iteration()
        LFSR_2.first_iteration()
        LFSR_1.second_iteration()
        LFSR_2.second_iteration()



class TestVectorSeed(object):
    def __init__(self, seed: int, n_bit: int, taps: List[int] = None):
        self.seed = seed
        for tap in taps:
            if tap > n_bit or tap <= 0:
                raise ValueError(f"Invalid tap value: {tap}")

        self.seed = seed
        self.seed_bits = n_bit if n_bit > seed.bit_length() else seed.bit_length()
        # self.seed_bits = n_bit  # if n_bit > seed.bit_length() else seed.bit_length()
        self.bits = n_bit
        self.taps = taps
        # if seed.bit_length() > n_bit:
        #     self.seed = self.seed >> seed.bit_length() - n_bit

    def __str__(self):
        # TODO: See TestVector.__str__() Check with Daniel
        a = 0
        temp = 0
        tv = bin(self.seed)[2:]
        for char in tv:
            temp += char
            a += 1
            if (a % 4 == 0):
                temp += ' '
        return temp

    # def __call__(self, count: int) -> List[TestVector]:
    #     # TODO: Implement LFSR, updating self.seed and generating a test vector
    #
    #     pass

    def update_seed(self):
        # TODO: Rotate seed, and apply taps
        pass
