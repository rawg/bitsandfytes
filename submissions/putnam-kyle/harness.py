#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Harness to run code fight submission

Example:

    $ python harness.py -i path/to/source.csv -o path/to/results.csv

"""
import argparse
import os
import shutil
from os.path import basename

parser = argparse.ArgumentParser(description="Code fight scoring harness.")

parser.add_argument("-i", "--input", help="input (original source) data file")
parser.add_argument("-o", "--output", help="output data file")

args = parser.parse_args()

shutil.copyfile(args.input, "input.csv")
# $ cat input.csv | java -jar hack.jar > output.csv
stat = os.system("cat input.csv | java -jar hack.jar > output.csv")

if stat == 0:
    os.rename("output.csv", args.output)

os.remove("input.csv")

exit(stat)
