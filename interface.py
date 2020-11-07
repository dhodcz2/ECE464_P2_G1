import dataclasses
from dataclasses import dataclass
from typing import List, Dict


def prompt_arguments() -> Dict:
    bench: str
    verbose: bool
    seed: int
    taps: List[int]
    counter: bool

    return {"bench": bench, "verbose": verbose, "seed": seed, "taps": taps, "counter": counter}