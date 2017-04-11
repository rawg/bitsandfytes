#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Harness to run code fight submission

Example:

    $ python harness.py -i path/to/source.csv -o path/to/results.csv

"""
import argparse
import os
import shutil
from os.path import basename, dirname, realpath, join

parser = argparse.ArgumentParser(description="Code fight scoring harness.")

parser.add_argument("-i", "--input", help="input (original source) data file")
parser.add_argument("-o", "--output", help="output data file")

args = parser.parse_args()

cwd = dirname(realpath(__file__))
os.chdir(join(cwd, "../../challenge"))
stat = os.system("python solution.py -i %s -o %s" % (args.input, args.output))
os.chdir(cwd)
exit(stat)
