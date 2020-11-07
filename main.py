from faults import Fault, CircuitSimulator, List
import unittest
from testvector import TestVectorGenerator, TestVector
import argparse
from typing import Union, List
from interface import prompt_arguments


class Args:
    bench: str
    verbose: bool
    seed: int
    taps: List[int]
    counter: bool
    prompt: bool
    graph: bool


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-v', '--verbose', type=bool, default=True, help='verbose simulator')
    parser.add_argument('-s', '--seed', type=str, default='0x123456789abc', help='seed for tv generation')
    parser.add_argument('-t', '--taps', type=list, default=[2, 7], help='tuple in LFSR')
    parser.add_argument("-c", "--counter", dest="counter", action="store_true", default=False)
    parser.add_argument("--no-prompt", dest="prompt", action="store_false", default=True)
    parser.add_argument("-g", "--graph", dest="graph", default=False, action="store_true")
    args = parser.parse_args()
    # args = parser.parse_args(namespace=Args)

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
        # test_vectors = TestVectorGenerator(args.seed, len(circuit_simulator.nodes.input_nodes), args.taps)() if
        result = circuit_simulator.run_batches(test_vectors, args.seed)
        print()
    else:
        result = circuit_simulator.run_batch(test_vectors, args.seed, args.taps)
        print()

