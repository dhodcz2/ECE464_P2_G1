import circuitsimulator
import faults
import testvector
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bench', type=str, default='circuit.bench', help='input bench file')
    parser.add_argument('-v', '--verbose', type=bool, default=True, help='verbose simulator')
    # parser.add_argument('--log_faultlist', type=str, default="log_faultlist.txt" )
    parser.add_argument('--faultlist', type=str, default="faultlist.txt")
    parser.add_argument('--faultcoverage', type=str, default="faultcoverage.json")
    parser.add_argument('--tvlist', type=str, default="tvlist.txt")
    # parser.add_argument('--s', type=int, )
    # parser.add_argument('-t', '--testvec', type=str, default=None, help='test vector')
    # parser.add_argument('-f', '--fault', type=str, default=None, help='faulty node to be created (format: --fault=x=0)')
    args = parser.parse_args()

    circuit_simulator = faults.CircuitSimulator(args) # original under circuitsimulator.CircuitSimulator
    # circuit_simulator.prompt()
    # circuit_simulator.simulate()
    fault_list = circuit_simulator.fault_list(log=True)


