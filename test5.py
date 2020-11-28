from typing import Set
from itertools import zip_longest
list1 = [{1}, {3}, {5}]
list2 = [{2}, {4}, {6}, {8}, {10}]
a: Set[int]
b: Set[int]
x = [a.union(b) for a, b in zip_longest(list1, list2, fillvalue=set())]
print(x)
