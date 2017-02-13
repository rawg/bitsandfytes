#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Category reduction validator.

Example:
    Import the ``validate`` function into your app or use directly from the command line::

        $ python validate.py -i path/to/source.csv -o path/to/results.csv

"""

from common import jaccard, TallyCollection
from unionfind import UnionFind

import argparse
import csv
import logging

logging.basicConfig(level=logging.WARN)


class Taxonomy(object):
    """A taxonomy of categories to articles.

    Args:
        infile (str): The full path to an input file location
        headers (bool): Auto-detect headers. Set to False to disable.
    """
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
            if not headers or (head[0] != "category" or head[1] != "article"):
                csvfile.seek(0)

            for cat, skill in reader:
                self.add(cat, skill)

def validate(source, output, threshold=0.75, headers=True):
    """Validate and score the results of category elimination.

    Args:
        source (str): The path to the source data in CSV.
        output (str): The path to the output data in CSV.
        threshold (float): The minimum Jaccard similarity required to
            merge categories.
        headers (bool): Auto-detect headers.

    Returns:
        Tuple[bool, int, int, int, str]: A tuple containing the results
            of validation and scoring. Elements are success, removed pairs,
            removed categories, super categories, and message (used to
            describe failures).

    """
    def results(success=False, pairs=0, cats=0, supercats=0, msg=None):
        return (success, pairs, cats, supercats, msg)

    def error(msg):
        return results(False, 0, 0, 0, msg)

    src = Taxonomy(source)
    out = Taxonomy(output)

    # 1. Confirm that all skills are present
    if src.skills != out.skills:
        return error("Some skills are missing")

    # 2. Confirm that no new categories were introduced.
    if len(out.cats - src.cats) != 0:
        return error("Categories were introduced")

    missing = src.cats - out.cats
    grown = [cat for cat in out.cats if src.cat_arts[cat] != out.cat_arts[cat]]
    survivors = src.cats - missing - set(grown)

    if len(grown) > 0:
        if len(missing) == 0:
            return error("Some categories have additional articles, but no " +
                  "categories were removed")
        maybe = {}
        merges = {}

        # 3. Confirm that categories were not split while merging.
        for m in missing:
            found = False
            for g in grown:
                # The original category is a subset of the super category
                if src.cat_arts[m] < out.cat_arts[g]:
                    found = True
                    maybe.setdefault(g, set())
                    maybe[g].add(m)

            if not found:
                for s in survivors:
                    if src.cat_arts[m] <= src.cat_arts[s]:
                        found = True
                        break

                if not found:
                    # The original category's articles cannot all be found in
                    # one super category, meaning the category was split.
                    return error("Category '%s' appears to have been split" % m)

        # 4. Confirm that at least one set of possible valid merges contains
        #    all of the articles in each super category.
        for m in maybe:
            cats = list(maybe[m]) + [m] # be sure to consider the supercat
            uf = UnionFind(cats)
            for i in range(0, len(cats)):
                for j in range(i + 1, len(cats)):
                    artsi = src.cat_arts[cats[i]]
                    artsj = src.cat_arts[cats[j]]
                    print(artsi, artsj)

                    if jaccard(artsi, artsj) > threshold:
                        uf.union(cats[i], cats[j])

            sets = uf.sets()
            found = False
            for cats in sets:
                arts = set()
                for cat in cats:
                    arts = arts | src.cat_arts[cat]

                if arts == out.cat_arts[m]:
                    found = True

            if not found:
                return error("Not all categories merged into %s are connected" % m)

    # success, pairs removed, categories removed, super categories, error message
    return results(True, src.pairs - out.pairs, len(src.cats) - len(out.cats), len(grown), None)


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



