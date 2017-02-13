#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


"""

from common import jaccard, TallyCollection
from unionfind import UnionFind

import argparse
import csv
import logging

logging.basicConfig(level=logging.WARN)


class Tree(object):
    def __init__(self, infile=None, headers=True):
        self.cat_arts = {}
        self.skills = set()
        self.cats = set()
        self.pairs = 0
        if infile is not None:
            self.read(infile, headers)

    def add(self, cat, skill):
        self.cat_arts.setdefault(cat, set())
        self.cat_arts[cat].add(skill)
        self.skills.add(skill)
        self.cats.add(cat)
        self.pairs += 1

    def read(self, infile, headers=True):
        with open(infile, "r") as csvfile:
            reader = csv.reader(csvfile)

            head = next(reader)
            if head[0] != "category" or head[1] != "article":
                csvfile.seek(0)

            for cat, skill in reader:
                self.add(cat, skill)


def validate(source, output, threshold=0.75, headers=True):
    def error(msg):
        return (False, 0, 0, 0, msg)

    src = Tree(source)
    out = Tree(output)

    # Confirm that all skills are present
    if src.skills != out.skills:
        error("Some skills are missing")

    # Confirm that all categories are present and no new categories
    # were created.
    if len(out.cats - src.cats) != 0:
        error("Categories were introduced")


    missing = src.cats - out.cats
    grown = [cat for cat in out.cats if src.cat_arts[cat] != out.cat_arts[cat]]

    if len(grown) > 0:
        if len(missing) == 0:
            error("Some categories have more articles, but no categories " +
                  "were removed")
        maybe = {}

        # Identify categories that may have been merged by looking for their
        # contents in another category.
        for m in missing:
            found = False
            for g in grown:
                if src.cat_arts[m] < out.cat_arts[g]:
                    found = True
                    maybe.setdefault(g, set())
                    maybe[g].add(m)

            if not found:
                error("Category '%s' appears to have been split" % m)

        # Verify that at least one set of possible valid merges contains
        # all of the articles in the super category.
        for m in maybe:
            uf = UnionFind(maybe[m])
            cats = list(maybe[m])
            for i in range(0, len(cats)):
                for j in range(i + 1, len(cats)):
                    artsi = src.cat_arts[cats[i]]
                    artsj = src.cat_arts[cats[j]]

                    if jaccard(artsi, artsj) > args.threshold:
                        uf.union(cats[i], cats[j])

            sets = uf.sets()
            found = False
            for cats in sets:
                arts = set()
                for cat in cats:
                    arts = arts | src.cat_arts[cat]

                if arts == out.cat_arts[m]:
                    found = True
                    break

            if not found:
                error("Not all categories merged into %s are connected" % m)

    # success, pairs removed, categories removed, super categories, error message
    return (True, src.pairs - out.pairs, len(src.cats) - len(out.cats), len(grown), None)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Validate submission output.")
    parser.add_argument("-s", "--source", help="source data file", default="category-article.csv", required=False)
    parser.add_argument("-o", "--output", help="output data file", default="reduced.csv", required=False)

    parser.add_argument("--threshold", help="merge threshold as minimum Jaccard similarity", default=0.75, type=float, required=False)

    parser.add_argument("--headers", help="read and write column headers", action="store_true")
    parser.add_argument("--no-headers", action="store_false", dest="headers")
    parser.set_defaults(headers=True)

    args = parser.parse_args()

    score = validate(args.source, args.output, args.threshold, args.headers)
    if not score[0]:
        print("[FAIL] %s" % score[4])
        exit(1)
    else:
        print("[PASS] %i pairs and %i categories removed. %i super categories found." % (score[1], score[2], score[3]))


