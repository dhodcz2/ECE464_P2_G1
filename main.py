from faults import Fault, CircuitSimulator
import unittest
from testvector import TestVectorGenerator, TestVector
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-v', '--verbose', type=bool, default=True, help='verbose simulator')
    parser.add_argument('-s', '--seed', type=int, default=0x12345789abc, help='seed for tv generation')
    parser.add_argument('-t', '--taps', type=list, default=[], help='tuple in LFSR')
    parser.add_argument('-c', '--counter', type=bool, default=False, help="Use the counter instead of PRPG")
    args = parser.parse_args()

    circuit_simulator = CircuitSimulator(args=args)
    fault_list = circuit_simulator.generate_fault_list()
    bit_length = len(circuit_simulator.nodes.input_nodes)
    test_vectors = TestVectorGenerator(seed=args.seed, input_bits=bit_length, taps=args.taps)() \
        if not args.counter else TestVectorGenerator.from_counter(seed=args.seed, input_bits=bit_length)

    print("--- derived full fault list: ---")
    print(f"tv list has {len(test_vectors)} tvs:")
    print(test_vectors, '\n')



    result = circuit_simulator.fault_coverage(test_vectors=test_vectors, faults=fault_list)
