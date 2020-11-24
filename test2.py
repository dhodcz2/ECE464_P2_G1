from typing import List, Union
from nodes import Value
from time import time
from random import randint
from dataclasses import dataclass

values = [Value(0), Value(1), Value('U'), Value("D"), Value("D'")]


# class TestClass:
#     def __init__(self):
#         self.values = [randint(1, 5) for _ in range(0, 2)]
#
#     def __repr__(self):
#         return str(self.values)


@dataclass
class Count:
    true = 0
    false = 0

    @classmethod
    def by_ifelse(cls, a: List[Value], b: List[Value]):
        obj = cls()
        for xval, yval in zip(a, b):
            if xval == 0 and yval == 0:
                obj.true += 1
            elif xval == 1 and yval == 1:
                obj.true += 1
            elif xval == "U" and yval == "U":
                obj.true += 1
            elif xval == "D" and yval == "D":
                obj.true += 1
            elif xval == "D'" and yval == "D'":
                obj.true += 1
            else:
                obj.false += 1
        return obj

    @classmethod
    def by_map(cls, a: List[Value], b: List[Value]):
        obj = cls()
        for xval, yval in zip(a, b):
            member = base[xval].get(yval, 'false')
            setattr(obj, member, getattr(obj, member) + 1)
        #     obj.__dict__[
        #         base[xval].get(yval, 'false')
        #     ] += 1
        return  obj

    @classmethod
    def by_map_string(cls, a: List[Value], b: List[Value]):
        obj = cls()
        for xval, yval in zip(a, b):
            member = base_string[str(xval)].get(str(yval), 'false')
            setattr(obj, member, getattr(obj, member) + 1)
        #     obj.__dict__[
        #         base[xval].get(yval, 'false')
        #     ] += 1
        return  obj


base_string = {
    0: {'0': 'true'},
    1: {'1': 'true'},
    'U': {'U': 'true'},
    "D": {"D": 'true'},
    "D'": {"D'": 'true'}
}

base = {
    Value(0): {Value(0): 'true'},
    Value(1): {Value(1): 'true'},
    Value('U'): {Value("U"): 'true'},
    Value("D"): {Value("D"): 'true'},
    Value("D'"): {Value("D'"): 'true'}
}

@dataclass
class Input:
    zero = False
    one = False
    unknown = False
    d = False
    dprime = False

if __name__ == '__main__':
    start = time()
    input = Input()
    end = time()
    print(end - start)
    start = time()
    zero = False
    one = False
    unknown = False
    d = False
    dprime = False
    zero = True
    one = True
    unknown = True
    one = True
    d = True
    zero = True
    one = True
    unknown = True
    dprime = True
    zero = False
    one = False
    unknown = False
    d = False
    dprime = False

    end = time()
    print(end - start)
    # x: List[Value] = [values[randint(0, 4)] for _ in range(0, 1000)]
    # y: List[Value] = [values[randint(0, 4)] for _ in range(0, 1000)]
    # start = time()
    # by_map = Count.by_map(x, y)
    # end = time()
    # print(f"By map: {end - start}")
    # start = time()
    # by_ifelse = Count.by_ifelse(x, y)
    # end = time()
    # print(f"By ifelse: {end - start}")
    # start = time()
    # by_map_string = Count.by_map_string(x, y)
    # end = time()
    # print(f"By map_string: {end - start}")
from time import time
from random import randint
ints = []
ones = []

start = time()
for _ in range(1, 100000):
    rint = randint(1, 2)
    if rint == 1:
        ones.append(rint)
end = time()
print(end - start)

ints = []
ones = []
start = time()
for _ in range(1, 100000):
    rint = randint(1, 2)
ones = [n for n in ints if n == 1]
end = time()
print(end - start)

