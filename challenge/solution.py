#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


"""

from common import jaccard, TallyCollection
from unionfind import UnionFind

import argparse
import csv
import logging
import operator
import random


logging.basicConfig(level=logging.INFO)


# Parse command line arguments
parser = argparse.ArgumentParser(description="Reduce category-article pairs.")
parser.add_argument("-i", "--infile", help="input file", default="category-article.csv", required=False)
parser.add_argument("-o", "--outfile", help="output file", default="reduced.csv", required=False)

parser.add_argument("--threshold", help="merge threshold as minimum Jaccard similarity", default=0.75, type=float, required=False)
parser.add_argument("--handicap", help="handicap (0.0-1.0)", default=0.0, type=float, required=False)

parser.add_argument("--headers", help="read and write column headers", action="store_true")
parser.add_argument("--no-headers", action="store_false", dest="headers")
parser.set_defaults(headers=True)

parser.add_argument("--remove", help="remove categories", action="store_true")
parser.add_argument("--no-remove", action="store_false", dest="remove")
parser.set_defaults(remove=True)

parser.add_argument("--merge", help="merge categories", action="store_true")
parser.add_argument("--no-merge", action="store_false", dest="merge")
parser.set_defaults(merge=True)

args = parser.parse_args()

# Globals...
cat_arts = {}
cat_counts = {}
skill_counts = TallyCollection()
ncats = 0
start_pairs = 0
rm_ops = 0
mg_ops = 0

# Read input data
with open(args.infile, "r") as csvfile:
    reader = csv.reader(csvfile)

    if args.headers:
        next(reader)

    for cat, skill in reader:
        cat_arts.setdefault(cat, set())
        cat_arts[cat].add(skill)

        cat_counts.setdefault(cat, 0)
        cat_counts[cat] += 1

        skill_counts.inc(skill)
        start_pairs += 1

logging.debug("Loaded input data")


def remove():
    """Remove categories

    1. Sort list by # articles
    2. For each category...
    2.1. Approach list in ascending order UNTIL # articles > 1
          This prioritizes the elimination of one-hit wonders
    2.2. Approach list in descending order
          This prioritizes removing categories with large numbers of
          category-article pairs.
    3. Validate that all skills in category exist in other categories
    4. Remove category if 3 is true
    """

    def rm(cat):
        global rm_ops
        if random.random() >= args.handicap:
            logging.info("REMOVE: %s" % cat)
            rm_ops += 1
            skill_counts.decr(cat_arts[cat])
            del cat_counts[cat]
            del cat_arts[cat]
        else:
            logging.info("HANDICAP: Skipping removal of %s" % cat)

    approach = sorted(cat_counts.items(), key=operator.itemgetter(1))

    # Search in ascending order to start with one article categories
    for i, v in enumerate(approach):
        cat, narts = v

        if narts > 1:
            approach = approach[i+1:]
            break

        if skill_counts.nonzero(cat_arts[cat]):
            rm(cat)

    # Once unary categories have been searched, reverse the order and
    # search larger categories first. Note: `reversed()` does not create a copy.
    for i, v in enumerate(reversed(approach)):
        cat, narts = v
        if skill_counts.nonzero(cat_arts[cat]):
            rm(cat)


def merge():
    """Merge categories."""
    global mg_ops
    cats = list(cat_arts.keys())
    uf = UnionFind(cats)
    ncats = len(cat_arts)

    for i in range(0, ncats):
        for j in range(i + 1, ncats):
            cat1, cat2 = cats[i], cats[j]

            if jaccard(cat_arts[cat1], cat_arts[cat2]) > args.threshold:
                uf.union([cat1, cat2])

    sets = uf.sets()
    for group in sets:
        mg_ops += len(group) - 1

        size = 0
        parent = None
        for cat in group:
            l = len(cat_arts[cat])
            if l > size:
                size = l
                parent = cat

        for cat in group:
            if cat != parent:
                if random.random() >= args.handicap:
                    logging.info("MERGE: %s -> %s" % (cat, parent))
                    skill_counts.decr(cat_arts[cat] & cat_arts[parent])
                    cat_arts[parent] |= cat_arts[cat]
                    del cat_arts[cat]
                else:
                    logging.info("HANDICAP: Skipping merge of %s -> %s" % (child, parent))


if args.remove:
    remove()

if args.merge:
    merge()


end_pairs = sum([len(cat_arts[arts]) for arts in cat_arts])

print("Removed %i of %i pairs; %i remain." % (start_pairs - end_pairs, start_pairs, end_pairs))
print("Remove operations: %i" % rm_ops)
print("Merge operations: %i" % mg_ops)

with open(args.outfile, "w") as csvfile:
    writer = csv.writer(csvfile)

    if args.headers:
        writer.writerow(["category", "article"])

    for cat in cat_arts:
        for art in cat_arts[cat]:
            writer.writerow([cat, art])
