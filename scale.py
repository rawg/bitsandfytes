#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Score all submissions. Ruthlessly.
"""
import argparse
import csv
import logging
import pandas as pd

parser = argparse.ArgumentParser(description="Score submissions.")
parser.add_argument("-i", "--input", help="path to results file", default="scores.csv", required=False)
parser.add_argument("-o", "--output", help="path to output file", default="scores-scaled.csv", required=False)
args = parser.parse_args()

logging.basicConfig(level=logging.INFO)
pd.options.mode.chained_assignment = None  # Silence SettingWithCopyWarning

df = pd.read_csv(args.input)
datasets = df["Dataset"].unique()

scores = {}

def scale(dataset, frame, col, weight=1):
    rs = frame.loc[frame[col] > 0]
    lo = rs[col].min()
    hi = rs[col].max()
    rs[col] -= lo
    rs[col] /= (hi - lo)
    rs[col] *= weight - 1
    rs[col] += 1

    for idx, row in rs.iterrows():
        submission = row["Submission"]
        scores.setdefault(submission, {})
        scores[submission].setdefault(dataset, 0)
        scores[submission][dataset] += row[col]

for dataset in datasets:
    rs = df.loc[df["Dataset"] == dataset]
    scale(dataset, rs, "Categories", 20)
    scale(dataset, rs, "Pairs", 70)

final = {}
print(scores)
with open(args.output, "w") as csvfile:
    writer = csv.writer(csvfile)

    header = ["Submission"] + list(datasets) + ["Overall"]
    writer.writerow(header)

    for submission in scores:
        tot = sum(scores[submission].values())
        avg = tot / len(datasets)
        final[submission] = avg
        out = [submission]
        for ds in datasets:
            if ds in scores[submission]:
                out.append(scores[submission][ds])
            else:
                out.append(0)

        out.append(avg)
        writer.writerow(out)

print(final)

