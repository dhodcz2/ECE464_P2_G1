from faults import Fault, CircuitSimulator
from testvector import TestVectorGenerator, TestVector
import argparse
import sys, os, functools
import csv
from functools import wraps


# def write_csv(function):
#     func_name = function.__name__
#
#     def wrapper(*args):
#         result = function(*args)
#         if func_name == "fault_coverage_all":
#             with open(f"_{args.bench}_remainingfaults.csv", 'w', newline='') as f:
#                 w = csv.writer(f, delimeter='\t', lineterminator='\n')
#                 w.writerow([str(fault) for fault in result.remaining_faults])
#             with open(f"_{args.bench}_faultcoverage.csv", 'w', newline='') as f:
#                 w = csv.writer(f, delimeter='\t', lineterminator='\n')
#                 w.writerows([[
#                     tv, faults
#                 ] for tv, faults in result.fault_coverage_all.items()])
#
#         return result
#
#     return wrapper()


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
    result = circuit_simulator.fault_coverage(test_vectors=test_vectors, faults=fault_list)


