from time import time
from testvector import *
# from circuitsimulator import *
# from circuitsimulator_redone import *
from scan_circuit_simulator import *
from interface import *
import argparse
from nodes import *
import csv

configs = [
    ("n-bit counter", set()),
    ("LFSR no taps", {1}),
    ("LFSR with taps at 2, 4, 5", {2, 4, 5}),
    ("LFSR with taps at 2, 3, 4", {2, 3, 4}),
    ("LFSR with taps at 3, 5, 7", {3, 5, 7})
]


class Args(argparse.Namespace):
    seed: Union[str, int]
    bench: str
    taps: Set[int]
    prompt: bool
    multiprocessing: bool
    verbose: bool
    compare: bool

def fault_coverage_comparison(circuit: Union[CircuitSimulator, ScanCircuitSimulator], args: Type[Args]):
    results = [
        (name, circuit.run_batch(args.seed, taps, get_all_coverage=False, sequential=args.sequential).fault_coverage_list)
        for (name, taps) in configs
    ]
    with open("_%s_seed_%s.csv" % (args.bench, hex(args.seed)), 'w') as f:
        w = csv.writer(f, delimiter=',', lineterminator='\n')
        for (name, fault_coverage_list) in results:
            fault_coverage_list: List[Tuple[TestVector, List[Fault]]]
            w.writerows([name, tv, *faults] for tv, faults in fault_coverage_list)


def fault_coverage(circuit: Union[CircuitSimulator, ScanCircuitSimulator], args: Type[Args]):
    result = circuit.run_batch(args.seed, args.taps, sequential=args.sequential)
    with open("_%s_remaining_faults.csv" % args.bench, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([str(fault) for fault in result.remaining_faults])
    with open("_%s_all.csv" % args.bench, 'w') as f:
        tv_writer = csv.writer(f, delimiter=',', lineterminator=':')
        fault_writer = csv.writer(f, delimiter=',', lineterminator='\n')
        for tv, faults in result.fault_coverage_all:
            tv_writer.writerow([str(tv)])
            fault_writer.writerow(faults)
    with open("_%s_list.csv" % args.bench, 'w') as f:
        tv_writer = csv.writer(f, delimiter=',', lineterminator=':')
        fault_writer = csv.writer(f, delimiter=',', lineterminator='\n')
        for tv, faults in result.fault_coverage_list:
            tv_writer.writerow([str(tv)])
            fault_writer.writerow(faults)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-s', '--seed', type=str, default='0x123456789abc', help='seed for tv generation')
    parser.add_argument('-t', '--taps', type=list, default=[2, 7], help='tuple in LFSR')
    parser.add_argument('--no-prompt', dest='prompt', action='store_false', default=True)
    parser.add_argument('-mp', '--multiprocessing', dest='multiprocessing', default=False, action='store_true')
    parser.add_argument('--no-verbose', dest='verbose', default=True, action='store_false')
    parser.add_argument('-c', '--compare', dest='compare', default=False, action='store_true')
    parser.add_argument('-sq', '--sequential', dest='sequential', default=False, action='store_true')
    args = parser.parse_args(namespace=Args)
    if type(args.seed) is str:
        args.seed = int(args.seed, 16 if args.seed.startswith('0x') else \
            2 if args.seed.startswith('0b') else 1)
    if args.prompt:
        new_args = prompt_arguments()
        for attribute, new_value in new_args.items():
            setattr(args, attribute, new_value)
    with open(args.bench, 'r') as f:
        line: str
        for line in f:
            if line.find("DFF") != -1:
                args.sequential = True
                break
        # pass
    if args.sequential:
        circuit_simulator = ScanCircuitSimulator(**vars(args))
    else:
        circuit_simulator = CircuitSimulator(**vars(args))

    # begin = time()
    if args.compare:
        fault_coverage_comparison(circuit_simulator, args)
    else:
        fault_coverage(circuit_simulator, args)
    # print("Ran in %s" % (time()-begin))

if __name__ == '__main__':
    begin = time()
    for _ in range(0, 1):
        main()
    print(time() - begin)
