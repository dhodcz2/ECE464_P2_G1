from typing import List, Tuple, Set, Union
import numpy
from nodes import Value
import unittest


class TestVector(object):
    def __init__(self, string: str):
        self.values: List[Value] = []
        for char in string:
            assert char == '0' or char == '1'
            self.values.append(Value(char))

    def __str__(self):
        return '0b' + str(value for value in self.values)

    def __iter__(self) -> Value:
        for bit in self.values:
            yield bit

    def __len__(self) -> int:
        return len(self.values)

    def __add__(self, other: 'TestVector') -> 'TestVector':
        result: TestVector = TestVector()


class LFSR(object):
    def __init__(self, q: Union[str, int]):
        self._q = {
            int: q,
            str: int(q, 2)
        }[type(q)]
        self._h: Set[int]

    @property
    def h(self) -> Tuple[int]:  # example:
        return (1,) + tuple(1 if n in self._h else 0 for n in range(1, 8))

    @h.setter
    def h(self, other: Tuple[int]):
        self._h = set(other)

    @property
    def q(self) -> Tuple[int]:  # example: 18
        q = [int(b) for b in format(self._q, "08b")]
        q.reverse()
        return tuple(q)

    @q.setter
    def q(self, other: Union[int, str]):
        self._q = {
            int: other,
            str: int(other, 2),
        }[type(other)]

    @property
    def h_array(self) -> numpy.ndarray:
        h = self.h
        return numpy.array([
            [0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, h[1]],
            [0, 1, 0, 0, 0, 0, 0, h[2]],
            [0, 0, 1, 0, 0, 0, 0, h[3]],
            [0, 0, 0, 1, 0, 0, 0, h[4]],
            [0, 0, 0, 0, 1, 0, 0, h[5]],
            [0, 0, 0, 0, 0, 1, 0, h[6]],
            [0, 0, 0, 0, 0, 0, 1, h[7]]], dtype=bool)

    @property
    def q_array(self) -> numpy.ndarray:
        q = self.q
        return numpy.array([
            [q[0]],
            [q[1]],
            [q[2]],
            [q[3]],
            [q[4]],
            [q[5]],
            [q[6]],
            [q[7]]], dtype=bool)

    @classmethod
    def taps(cls, h: Tuple[int]):
        cls._h = tuple(h)

    def __call__(self, *args, **kwargs) -> TestVector:
        dot_product = self.h_array.dot(self.q_array)
        binary_result = ''
        for x in range(8):
            if dot_product[x]:
                binary_result += '1'
            else:
                binary_result += '0'
        result = int(binary_result, 2)
        self.q = result
        return TestVector(result)

        # result =
        # self.q = int(binary_result, 2)
        # return
        # result = str((1 if b else 0 for b in self.h_array.dot(self.q_array)))
        # self.q = result
        # return TestVector(result)


class TestVectorGenerator(object):
    def __init__(self, seed: int, input_bits: int, taps: Tuple[int] = ()):
        self.input_bits = input_bits
        LFSR.taps(taps)
        seed_bits = input_bits if input_bits > seed.bit_length() else seed.bit_length()
        lfsr_bits = self.input_bits // 8 + \
                    8 if self.input_bits % 8 else 0
        binary_seed = format(seed, f"0{lfsr_bits}b")
        self.LFSRs = [LFSR(binary_seed[lfsr_bits - n - 8: lfsr_bits - n]) for n in range(0, lfsr_bits, 8)]

    def __call__(self, *args, **kwargs) -> List[TestVector]:
        test_vector_count = 2 ** self.input_bits if 2 ** self.input_bits < 100 else 100
        lfsr_count = len(self.LFSRs)
        return [self.LFSRs[n % lfsr_count]() for n in range(0, test_vector_count)]
        # it should be first.result + second.result + third.result, and then



class LFSRTest(unittest.TestCase):
    def setUp(self) -> None:
        super(LFSRTest, self).setUp()

    def test1(self):
        seed = 0x12
        input_bits = 4
        taps = tuple([1, 2, 3])
        tvg = TestVectorGenerator(seed, input_bits, taps)
        test_vectors = tvg()
        self.assertEqual(len(test_vectors), 16)  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)))  # check that all are unique

# class Counter(object):
#     def __init__(self, seed, n_bit):
#         self.seed = seed
#
#     @classmethod
#     def

# class Employee(object):
#
#     @classmethod
#     def set_starting_salary(cls, salary:int):
#         cls.starting_salary = salary
#




if __name__ == '__main__':
    unittest.main()
