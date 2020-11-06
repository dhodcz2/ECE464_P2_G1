from dataclasses import dataclass
from typing import List

@dataclass
class Args:
    bench: str
    verbose: bool
    seed: int
    taps: list
    counter: int

def prompt_arguments() -> Args:
    # fill out args
    bench: str
    verbose: bool
    seed: int
    taps: List[int]
    counter: bool

    return Args(bench=bench, verbose=verbose, seed=seed, taps=taps, counter=counter)

prompt_arguments()