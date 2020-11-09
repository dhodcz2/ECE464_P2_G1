import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Set
from os.path import isfile


def prompt_arguments() -> Dict:
    bench: str = "circuit.bench"
    verbose: bool
    response: int
    taps: List[int] = []
    counter: bool = False
    while True:
        response: str = input("Provide a bench file name (return to accept circuit.bench default): ")
        if not response:
            break
        elif isfile(response):
            bench = response
            break
        else:
            print("File not found in working directory; please try again.")
    while True:
        verbose: str = input("Would you like to see results in the console? (Y/N): ")
        if verbose == 'y' or verbose == 'Y':
            verbose: bool = True
            break
        elif verbose == 'n' or verbose == 'n':
            verbose: bool = False
            break
        else:
            print("Invalid response; please try again.")
    while True:
        response: str = input("Enter a hex, decimal, or binary number for the seed: ")
        if response.startswith("0x"):
            try:
                seed: int = int(response, 16)
                break
            except ValueError:
                print("Invalid input; please try again")
        elif response.startswith("0b"):
            try:
                seed = int(response, 2)
                break
            except ValueError:
                print("Invalid input; please try again")
        else:
            try:
                seed: int = int(response)
                break
            except ValueError:
                print("Invalid input; please try again")
    while True:
        option: str = input("Would you like to generate the TV list with LFSR? (Y/N): ")
        if option == 'n' or option == 'N':
            counter = True
            print("Performing TV list generation via counter.")
            break
        elif option == 'y' or option == 'Y':
            counter = False
            print("Performing TV list generation via LFSR.")
            break
        else:
            print("Invalid response; please try again")
    while not counter:
        response: str = input("Enter the taps you want from 1 to 7, separated by a space:")
        try:
            taps: List[int] = [int(tap) for tap in response.split()]
        except:
            print("Invalid entry; please try again")
            continue
        if any(tap < 1 or tap > 7 for tap in taps):
            print("Out of range; please try again.")
            continue
        taps.sort()
        taps: Set = set(taps)
        print("Using the following taps: ")
        print(*taps, sep=', ')
        print('\n')
        break



    return {"bench": bench, "verbose": verbose, "seed": seed, "taps": taps, "counter": counter}
