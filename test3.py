from typing import List, Iterator, Set
from copy import copy
import functools
from time import time


#
#
# def remove_first(x: List[int]):
#     x.pop()
#
#
# test = [1, 2, 3]
# remove_first(test)
# assert len(test) == 33
#
# from time import time
#
# x = [1, 2, 3]
# begin = time()
# for _ in range(0, 10000):
#     x[0]
# print(time() - begin)
#
# begin = time()
# for _ in range(0, 10000):
#     next(iter(x))
# print(time() - begin)
#
# from functools import singledispatch
#
#
# @singledispatch
# def p(variable):
#     raise NotImplementedError
#
#
# @p.register(str)
# def _(variable: str):
#     print("String")
#
#
# @p.register(int)
# def _(variable: int):
#     print("Int")
#

class Struct:
    member: int

    def __init__(self, m):
        self.member = m

    def __hash__(self):
        return hash(self.member)


class OuterStruct:
    structs: List[Struct]

    def __init__(self, structs: List[Struct]):
        self.structs = structs

    def __iter__(self):
        for struct in self.structs:
            yield struct.member

    # def struct_members(self):
    #     for struct in self.structs:
    #         yield struct.member
    # @functools.cached_property
    def outerstruct_generator(self) -> Iterator:
        return copy(self._outerstruct_generator)

    @functools.cached_property
    def _outerstruct_generator(self) -> Iterator:
        return (
            struct.member
            for struct in self.structs
        )


# x: Set[Struct] = {Struct(0), Struct(1), Struct(2)}
x = OuterStruct([Struct(0), Struct(1), Struct(2)])

# for member in x.struct_members:
#     print(member)
# x.structs[0].member = 4
# x.structs[1].member = 5
# x.structs[2].member = 6
# print("here")
# for member in x.struct_members:
#     print(member)
#
# def by_iterator():
#     global x
#     result = 0
#     for member in (struct.member for struct in x):
#         result += member
#
#
# def by_vector():
#     global x
#     result = 0
#     for struct in x:
#         result += struct.member
#
#
def by_getitem():
    global x
    result = 0
    for struct in x.structs:
        result += struct.member


def by_cached_iterator():
    global x
    result = 0
    for member in x:
        result += member
    # for member in x.struct_members():
    #     result += member
def by_class_generator():
    global x
    result = 0
    for member in x.outerstruct_generator():
        result += member


begin = time()
for _ in range(0, 10000):
    # by_iterator()
    by_getitem()
print(time() - begin)

begin = time()
for _ in range(0, 10000):
    # by_vector()
    # by_cached_iterator()
    by_class_generator()
print(time() - begin)
