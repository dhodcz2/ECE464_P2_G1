from typing import List

ints = [n for n in range(1, 11)]


def method_1():
    return [
        num for i
        in ints
        for num in range(i * 6 * 5 * 4 * 3 * 2 * 1 % 5, i ** 8)
        if i % 2
    ]


def method_2():
    return [
        num for i
        in (i for i in ints if i % 2)
        for num in range(i * 6 * 5 * 4 * 3 * 2 * 1 % 5, i ** 8)
    ]


assert method_1() == method_2()
