#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Score all submissions. Ruthlessly.
"""
import argparse
import csv
import logging
import os
import shutil
import subprocess
import time

from os.path import basename, dirname, realpath, join
from subprocess import Popen, PIPE

from challenge.validate import validate

parser = argparse.ArgumentParser(description="Score submissions.")
parser.add_argument("-o", "--output", help="path to results file", default="scores.csv", required=False)
parser.add_argument("-t", "--timeout", help="timeout in seconds", default=None, required=False, type=int)
args = parser.parse_args()

logging.basicConfig(filename="scoring.log", level=logging.INFO)

cwd = dirname(realpath(__file__))
submissions = join(cwd, "submissions")
datasets = join(cwd, "datasets/final")

if args.timeout is not None:
    ofile = str(args.timeout) + "-" + args.output
else:
    ofile = args.output

with open(ofile, "w") as csvfile:
    writer = csv.writer(csvfile)

    writer.writerow(["Submission", "Dataset", "Time", "Exit Code",
                     "Successful", "Pairs", "Categories", "Supercategories", "Merges"])

    logging.info("Results file: %s" % args.output)
    logging.info("Timeout: %i" % args.timeout)

    for submission in os.listdir(submissions):   # assumes only directories
        for dataset in os.listdir(datasets):
            if dataset.endswith(".csv"):
                logging.info("Scoring %s on %s" % (submission, dataset))

                inpath = join(datasets, dataset)
                outpath = "/tmp/output.csv"

                os.chdir(join(submissions, submission))
                t = time.time()

                #os.system("python harness.py -i %s -o %s" % (inpath, outpath))
                cmd = ["python", "harness.py", "-i", inpath, "-o", outpath]
                #subprocess.call(cmd, timeout=args.timeout)
                proc = Popen(cmd, stdout=PIPE, stderr=PIPE)

                try:
                    outs, errs = proc.communicate(timeout=args.timeout)
                    ret = proc.returncode

                    ellapsed = time.time() - t
                    r = validate(inpath, outpath)

                    writer.writerow([submission, dataset, ellapsed, ret,
                                     int(r["success"]), r["pairs"], r["cats"],
                                     r["supercats"], r["merges"]])
                    csvfile.flush()

                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                    writer.writerow([submission, dataset, -1, -1, 0, 0, 0, 0, 0])
                    logging.error("Timeout encountered in %s on %s" % (submission, dataset))
