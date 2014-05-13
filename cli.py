#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on Sat May 10 23:40:17 2014
# @author: Danilo de Jesus da Silva Bellini
"""
CLI for PyTuring (experimental)
"""

from __future__ import unicode_literals, print_function
import argparse, pyturing, io, os, sys

# Python 2.x and 3.x compatibility
if sys.version_info.major == 2:
    input = raw_input
    range = xrange

# Simple argument parsing CLI
parser = argparse.ArgumentParser(description="PyTuring CLI")
parser.add_argument("machine", help="Turing Machine rules source file name")
args = parser.parse_args()
machine_filename = args.machine
if not os.path.isfile(machine_filename):
    parser.error("Machine file not found")

# "Builds" the machine
with io.open(machine_filename, "r", encoding="utf-8") as f:
    tm = pyturing.TuringMachine(f.read())
print("Machine file open {}\n".format(machine_filename))

# Gets some needed inputs
tm.tape = input("Input tape from index 0 (whitespace-separated):\n").split()
moves = int(input("\nAmount of moves (machine instructions to follow): "))
print()

# Run the tape typed as a whitespace-separated line
print("Running the machine from the index {}".format(tm.index))
for move in range(moves):
    tm.move()

# Show the resulting configuration
tape = tm.tape
first, last = min(tape), max(tape)
print("Last m-configuration: {}".format(tm.mconf))
print("Last machine index on the tape: {}".format(tm.index))
print("Resulting tape (from index {first} to {last}):".format(**locals()))
print(" ".join(tape.get(idx, "None") for idx in range(first, last + 1)))
