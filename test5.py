from functools import lru_cache
import weakref
class Struct:
    member: int
    @lru_cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, m: int):
        self.member = m

    def __hash__(self):
        return hash(1)


x = {Struct(1), Struct(2)}

x.add(Struct(3))
x

