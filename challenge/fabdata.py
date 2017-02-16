#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


"""

import argparse
import csv
import logging
import random

logging.basicConfig(level=logging.INFO)


# Parse command line arguments
parser = argparse.ArgumentParser(description="Reduce category-article pairs.")
parser.add_argument("-i", "--infile", help="input file", required=True)
parser.add_argument("-o", "--outfile", help="output file", required=True)

parser.add_argument("--homo", help="number of homogeneous categories", default=100, type=int, required=False)
parser.add_argument("--dupe", help="number of duplicate categories", default=100, type=int, required=False)
parser.add_argument("--uniq", help="number of unique categories", default=10, type=int, required=False)

parser.add_argument("--certain", help="be certain not to reuse categories", action="store_true")
parser.add_argument("--uncertain", action="store_false", dest="certain")
parser.set_defaults(certain=True)
args = parser.parse_args()

cats = set()
arts = set()
output = []

with open(args.infile, "r") as csvfile:
    reader = csv.reader(csvfile)

    head = next(reader)
    if head[0] != "category" or head[1] != "article":
        csvfile.seek(0)

    for cat, art in reader:
        cats.add(cat)
        arts.add(art)

cats = list(cats)
arts = list(arts)

logging.debug("Loaded input data")

def record(cat, art):
    output.append([cat, art])
    if args.certain:
        if cat in cats:
            del cats[cats.index(cat)]
        #if art in arts:
        #    del arts[arts.index(art)]

def record_many(ls):
    for item in ls:
        record(item[0], item[1])


for i in range(0, args.uniq):
    cat = random.choice(cats)
    art = random.choice(arts)
    record(cat, art)


for i in range(0, args.dupe):
    base = random.sample(arts, random.randint(5, 20))
    dupes = []
    for j in range(0, random.randint(1, 5)):
        cat = random.choice(cats)
        dupes.append([cat, art])
    record_many(dupes)


for i in range(0, args.homo):
    base = random.sample(arts, 15)
    for j in range(0, random.randint(1, 5)):
        cat = random.choice(cats)
        extra = random.sample(arts, random.randint(1, 3))
        for art in base + extra:
            record(cat, art)

random.shuffle(output)

with open(args.outfile, "w") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["category", "article"])

    for row in output:
        writer.writerow(row)

