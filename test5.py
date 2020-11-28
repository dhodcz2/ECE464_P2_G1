
from contextlib import contextmanager

@contextmanager
def context():
    print("Entered")
    yield
    print("Exited")


def use_context():
    with context():
        print("returned True")
        return True


def test_context():
    if use_context():
        print("Got True")

test_context()
