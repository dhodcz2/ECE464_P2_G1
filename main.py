from faults import Fault, CircuitSimulator, List
import unittest
from testvector import TestVectorGenerator, TestVector
import argparse
from typing import Union, List
from interface import prompt_arguments


class Args:
    bench: str
    verbose: bool
    seed: str
    taps: List[int]
    counter: bool
    prompt: bool
    graph: bool


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-s', '--seed', type=str, default='0x123456789abc', help='seed for tv generation')
    parser.add_argument('-t', '--taps', type=list, default=[2, 7], help='tuple in LFSR')
    parser.add_argument("-c", "--counter", dest="counter", action="store_true", default=False)
    parser.add_argument("--no-prompt", dest="prompt", action="store_false", default=True)
    parser.add_argument("-g", "--graph", dest="graph", default=False, action="store_true")
    parser.add_argument('--no-verbose', default=True, dest="verbose", action="store_false")
    args = parser.parse_args()
    if args.seed.startswith('0x'):
        args.seed = int(args.seed, 16)
    elif args.seed.startswith('0b'):
        args.seed = int(args.seed, 2)
    else:
        args.seed = int(args.seed)
    if args.prompt:
        new_args = prompt_arguments()
        for attribute, new_value in new_args.items():
            setattr(args, attribute, new_value)
    circuit_simulator = CircuitSimulator(**vars(args))
    input_bits = len(circuit_simulator.nodes.input_nodes)
    test_vectors = TestVectorGenerator(args.seed, input_bits, args.taps)() if not args.counter else \
        TestVectorGenerator.from_counter(args.seed, input_bits)
    test_vectors = [test_vector[:input_bits] for test_vector in test_vectors]
    if args.graph:
        result = circuit_simulator.run_batches(args.seed)
        if args.verbose:
            print()
    else:
        result = circuit_simulator.run_batch(args.seed, args.taps)
        if args.verbose:
            print()
