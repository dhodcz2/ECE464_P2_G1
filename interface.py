from dataclasses import dataclass

@dataclass
class Args:
    bench: str
    verbose: bool
    seed: int
    taps: list
    counter: int

def prompt_arguments() -> Args:
    args = Args()
    args.verbose # set
