from typing import List, List, Set, Union, Tuple, Optional, Iterable
import functools
import itertools
from nodes import Value
import unittest
import copy


class TestVector:
    __slots__ = ('values')
    def __init__(self, values: str = ''):
        self.values = [Value(int(bit)) for bit in values]

    def __repr__(self):
        return ''.join([str(value) for value in self.values])

    def __iter__(self):
        for value in self.values:
            yield value

    def __len__(self):
        return len(self.values)

    def __eq__(self, other: Union['TestVector']):
        for self_bit, other_bit in zip(self, other):
            if self_bit is not other_bit:
                return False
        return True

    def __int__(self):
        return int(repr(self), 2)

    def __hash__(self):
        return hash(repr(self))
        # return hash(int(self))

    def __getitem__(self, item) -> 'TestVector':
        return TestVector.from_values(self.values[item])

    @classmethod
    def from_values(cls, values: Iterable[Value]):
        obj = TestVector()
        obj.values = values
        return obj

    @classmethod
    def from_integers(cls, values: List[int]):
        obj = TestVector()
        obj.values = [Value(value) for value in values]
        return obj


class LFSR:
    h: List[int]

    def __init__(self, q: str):
        self._q = [int(bit) for bit in q]

    def __call__(self, *args, **kwargs) -> List[int]:
        return self.lfsr_algorithm()

    @property
    def q(self) -> List[int]:
        q = self._q
        q.reverse()
        return q

    @q.setter
    def q(self, _q: List[int]):
        self._q = _q

    @classmethod
    def set_taps(cls, h: Set[int]):
        cls.h = [1, *(1 if n in h else 0 for n in range(1, 8))]

    def lfsr_algorithm(self) -> List[int]:
        q = self.q
        h = self.h
        qprime: List[int] = [q[7] * h[0]]
        qprime.extend((q[7] * h[n] ^ q[n - 1] for n in range(1, 8)))
        qprime.reverse()
        self.q = qprime
        return qprime


class TestVectorGenerator:
    def __init__(self, seed: int, input_bits: int, taps: Set[int] = ()):
        LFSR.set_taps(taps)
        self.input_bits = input_bits
        tv_length = self.bits_ceiling(input_bits)
        binary_seed = format(seed, f"0{self.bits_ceiling(seed.bit_length())}b")
        repetitions = tv_length // len(binary_seed) + (1 if tv_length % len(binary_seed) else 0)
        binary_seed = (binary_seed * repetitions)[:tv_length]
        self.lfsrs = [
            LFSR(q) for q in (
                binary_seed[n:n + 8]
                for n in range(0, tv_length, 8)
            )
        ]

    def __call__(self, *args, **kwargs) -> List[TestVector]:
        # result = set()
        # while len(result) < self.tv_count:
        #     tv = TestVector.from_integers([
        #         integer for integers in
        #         (lfsr() for lfsr in self.lfsr)
        #         for integer in integers
        #     ])
        #     if tv[:self.input_bits] not in result:
        #         result.add(tv)


        # result = set()
        # while len(result) < self.tv_count:
        #     tv = TestVector.from_integers([
        #         integer for integers in
        #         (lfsr() for lfsr in self.lfsrs)
        #         for integer in integers
        #     ])

        result = [
            TestVector.from_integers([
                integer for integers in
                (lfsr() for lfsr in self.lfsrs)
                for integer in integers
            ])
            for tv in range(0, self.tv_count)
        ]
        return result

    @functools.cached_property
    def tv_count(self):
        tv_count = 2 ** self.input_bits
        return tv_count if tv_count < 100 else 100

    @staticmethod
    def bits_ceiling(bits: int) -> int:
        return bits // 8 * 8 + (8 if bits % 8 else 0)

    @staticmethod
    def from_counter(seed: int, input_bits: int) -> List[TestVector]:
        tv_count = 2 ** input_bits
        if tv_count > 100:
            tv_count = 100
        seed_length = TestVectorGenerator.bits_ceiling(input_bits) if \
            input_bits > seed.bit_length() else \
            TestVectorGenerator.bits_ceiling(seed.bit_length())
        trimmed_seed = int(format(seed, f"0{seed_length}b")[:input_bits], 2)
        bitstrings = (format((trimmed_seed + n) % tv_count, f"0{input_bits}b")
                      for n in range(0, tv_count))
        result = [TestVector(bitstring) for bitstring in bitstrings]
        with open(f"_testvectors_from_counter.txt", 'w') as f:
            f.writelines([f"{tv}\n" for tv in result])
        return result


class LFSRTest(unittest.TestCase):
    def setUp(self) -> None:
        super(LFSRTest, self).setUp()

    def test1(self):
        seed = 0x1234
        input_bits = 3
        # taps = list([2, 3, 5])
        taps = {2, 3, 5}
        tvg = TestVectorGenerator(seed, input_bits, taps)
        test_vectors = tvg()
        self.assertEqual(len(test_vectors), 8, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')
        test_vectors = TestVectorGenerator.from_counter(seed, input_bits)
        self.assertEqual(len(test_vectors), 8, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')

    def test2(self):
        seed = 0x1
        input_bits = 4
        # taps = list([2, 3, 5])
        taps = {2, 3, 5}
        tvg = TestVectorGenerator(seed, input_bits, taps)
        test_vectors = tvg()
        self.assertEqual(len(test_vectors), 16, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')
        test_vectors = TestVectorGenerator.from_counter(seed, input_bits)
        self.assertEqual(len(test_vectors), 16, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')

    def test3(self):
        seed = 0x12345689ABCDEF
        input_bits = 32
        # taps = list([3])
        taps = {3}
        tvg = TestVectorGenerator(seed, input_bits, taps)
        test_vectors = tvg()
        self.assertEqual(len(test_vectors), 100, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')
        test_vectors = TestVectorGenerator.from_counter(seed, input_bits)
        self.assertEqual(len(test_vectors), 100, 'unexpected length')  # Check that we got 16 test vectors
        self.assertEqual(len(test_vectors), len(set(test_vectors)), 'non-unique elements')


if __name__ == '__main__':
    unittest.main()
