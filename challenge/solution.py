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


logging.basicConfig(level=logging.INFO)


# Parse command line arguments
parser = argparse.ArgumentParser(description="Reduce category-article pairs.")
parser.add_argument("-i", "--infile", help="input file", default="category-article.csv", required=False)
parser.add_argument("-o", "--outfile", help="output file", default="reduced.csv", required=False)

parser.add_argument("--threshold", help="merge threshold as minimum Jaccard similarity", default=0.75, type=float, required=False)

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
        logging.info("REMOVE: %s" % cat)
        skill_counts.decr(cat_arts[cat])
        del cat_counts[cat]
        del cat_arts[cat]

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
    cats = list(cat_arts.keys())
    uf = UnionFind(cats)
    ncats = len(cat_arts)

    for i in range(0, ncats):
        for j in range(i + 1, ncats):
            cat1, cat2 = cats[i], cats[j]

            if jaccard(cat_arts[cat1], cat_arts[cat2]) > args.threshold:
                if cat_counts[cat1] > cat_counts[cat2]:
                    parent, child = cat1, cat2
                else:
                    parent, child = cat2, cat1

                parent2 = uf.parent(child)
                if parent2 != child:
                    if cat_counts[parent2] >= cat_counts[parent]:
                        uf.union([parent, child], parent2)
                    else:
                        uf.union([parent2, child], parent)
                else:
                    uf.union(child, parent)

    children = uf.children()
    for parent in children:
        for child in children[parent]:
            logging.info("MERGE: %s -> %s" % (child, parent))
            rm = cat_arts[parent] & cat_arts[child]
            skill_counts.decr(rm)
            mv = cat_arts[child] - rm
            for m in mv:
                cat_arts[parent].add(m)
            del cat_arts[child]


if args.remove:
    remove()

if args.merge:
    merge()


end_pairs = sum([len(cat_arts[arts]) for arts in cat_arts])

print("Removed %i of %i pairs; %i remain." % (start_pairs - end_pairs, start_pairs, end_pairs))

with open(args.outfile, "w") as csvfile:
    writer = csv.writer(csvfile)

    if args.headers:
        writer.writerow(["category", "article"])

    for cat in cat_arts:
        for art in cat_arts[cat]:
            writer.writerow([cat, art])
