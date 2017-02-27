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

# Parse command line arguments
parser = argparse.ArgumentParser(description="Reduce category-article pairs.")
parser.add_argument("-i", "--infile", help="input file", default="category-article.csv", required=False)
parser.add_argument("-o", "--outfile", help="output file", default="reduced.csv", required=False)

parser.add_argument("--threshold", help="merge threshold as minimum Jaccard similarity", default=0.75, type=float)
parser.add_argument("--handicap", help="handicap (0.0-1.0)", default=0.0, type=float)

parser.add_argument("--headers", help="read and write column headers", action="store_true")
parser.add_argument("--no-headers", action="store_false", dest="headers")
parser.set_defaults(headers=True)

parser.add_argument("--remove", help="remove categories", action="store_true")
parser.add_argument("--no-remove", action="store_false", dest="remove")
parser.set_defaults(remove=True)

parser.add_argument("--merge", help="merge categories", action="store_true")
parser.add_argument("--no-merge", action="store_false", dest="merge")
parser.set_defaults(merge=True)

parser.add_argument("--merge-first", help="merge before removing", action="store_true", default=False)

parser.add_argument("-L", "--log-level", help="logging level", choices=["info", "debug", "warning", "error", "critical"],
                    default="info")

args = parser.parse_args()

choices = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}
logging.basicConfig(level=choices[args.log_level])

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

        if skill not in cat_arts[cat]:
            skill_counts.inc(skill)

        cat_arts[cat].add(skill)

        cat_counts.setdefault(cat, 0)
        cat_counts[cat] += 1

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
            logging.debug("DECREMENT %s" % str(cat_arts[cat]))
            rm_ops += 1
            skill_counts.decr(cat_arts[cat])
            del cat_counts[cat]
            del cat_arts[cat]
        else:
            logging.info("HANDICAP: Skipping removal of %s" % cat)

    # Create a vector of categories to attempt to remove. Start with categories
    # that only have one article, then move on to categories sorted by # articles
    # descending.  Once we're through the single article categories, the more
    # articles are in a category the more likely it is to be safe to remove.
    approach = []
    sort = []
    for cat in cat_arts:
        if len(cat_arts[cat]) == 1:
            approach.append(cat)
        else:
            sort.append(cat)
    approach += sorted(sort, reverse=True)

    for cat in approach:
        if skill_counts.can_decr(cat_arts[cat]):
            rm(cat)


def merge():
    """Merge categories."""
    global mg_ops     # dirty :(
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

        if random.random() >= args.handicap:
            for cat in group:
                if cat != parent:
                    logging.info("MERGE: %s -> %s" % (cat, parent))
                    skill_counts.decr(cat_arts[cat] & cat_arts[parent])
                    cat_arts[parent] |= cat_arts[cat]
                    del cat_arts[cat]
        else:
            logging.info("HANDICAP: Skipping merge of %s -> %s" % (cat, parent))


if args.merge_first and args.merge:
    merge()

if args.remove:
    remove()

if not args.merge_first and args.merge:
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
