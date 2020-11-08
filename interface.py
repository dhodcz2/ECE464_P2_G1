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
    # try:
    #     bench = str(
    #         input("Provide a bench file name (return to accept circuit.bench by default):\n"))
    # except SyntaxError:
    #     bench = 'circuit.bench'
    #     print(bench)
    # Prompts user for verbose to be enabled or disabled
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
    # option = str(
    #     input("Would you like to see results in the console (y/n):\n"))
    # while True:
    #     if option == 'n':
    #         verbose = False
    #         break
    #     elif option == 'y':
    #         verbose = True
    #         break
    #     else:
    #         option = str(
    #             input("Please enter either a 'y' or 'n':\n"))
    # Prompts user seed in hex, with or without '0x'
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

    # while True:
    #     try:
    #         seed = int(
    #             input("What do you want the seed to be? Enter a hex number:\n"), 16)
    #         break
    #     except ValueError:
    #         print("Input was not a hexadecimal. Please try again. ")
    # print("Using the following seed: ", hex(seed))
    # Prompts user to perform TV List Generation via PRPGs, if no, use LFSR
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

    # option = str(
    #     input("Would you like to generate TV list via PRPGs (y/n):\n"))
    # while True:
    #     if option == 'n':
    #         counter = False
    #         print("Performing TV list generation via LFSR.\n")
    #         break
    #     elif option == 'y':
    #         counter = True
    #         print("Performing TV list generation via PRPGs.\n")
    #         break
    #     else:
    #         option = str(
    #             input("Please enter either a 'y' or 'n':\n"))

    # When PRPG is not desired, prompts user for tabs list with values between 1 and 7, otherwise tabs is left as an empty list
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


    # if counter == False:
    #     while True:
    #         check = True
    #         tapList = input("Enter the taps you want on from 1 to 7, separated by space:\n")
    #         taps = tapList.split()
    #         for tap in taps:
    #             try:
    #                 if int(tap) < 1 or int(tap) > 7:
    #                     check = False
    #                     break
    #             except ValueError:
    #                 check = False
    #                 break
    #         if check:
    #             break
    #         else:
    #             print("Out of range. Please try again. ")
    #     taps = list(dict.fromkeys(taps)) #removes doubles from the list
    #     taps.sort() #sorts list
    #     print("Using the following taps: ")
    #     print(*taps, sep=", ")

    return {"bench": bench, "verbose": verbose, "seed": seed, "taps": taps, "counter": counter}
