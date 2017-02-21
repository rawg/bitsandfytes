#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Category reduction validator.

Validation:
    1. All articles are present.
    2. No new categories were introduced.
    3. All super categories can be explained as a set of categories in which
       each has a suitable Jaccard similarity with at least one other.
    3.1. Super categories have the label of the largest contributing category.
"""
import csv
#import logging
from itertools import combinations

from .common import jaccard
from .unionfind import UnionFind

class Taxonomy(object):
    """A taxonomy of categories to articles.

    Args:
        infile (str): The full path to an input file location
        headers (bool): Auto-detect headers. Set to False to disable.
    """
    def __init__(self, infile=None, headers=True):
        self.cat_arts = {}
        self.arts = set()
        self.cats = set()
        self.pairs = 0
        if infile is not None:
            self.read(infile, headers)

    def add(self, cat, art):
        self.cat_arts.setdefault(cat, set())
        self.cat_arts[cat].add(art)
        self.arts.add(art)
        self.cats.add(cat)
        self.pairs += 1

    def read(self, infile, headers=True):
        with open(infile, "r") as csvfile:
            reader = csv.reader(csvfile)

            head = next(reader)
            if not headers or (head[0] != "category" or head[1] != "article"):
                csvfile.seek(0)

            for cat, art in reader:
                self.add(cat, art)


def all_combinations(ls, minlength=2):
    """Return all combinations of elements in a list"""
    ret = [ls]

    for length in range(minlength, len(ls)):
        combs = list(combinations(ls, length))
        for c in combs:
            ret.append(list(c))

    return ret

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
    src = Taxonomy(source)
    out = Taxonomy(output)

    def results(success=False, pairs=0, cats=0, supercats=0, merges=0, msg=None):
        return {
            "success": success,
            "pairs": pairs,
            "cats": cats,
            "supercats": supercats,
            "merges": merges,
            "message": msg}

    def error(msg):
        return results(False, 0, 0, 0, 0, msg)

    def union_find(cats, debug=False):
        """Return a UnionFind of homogeneous categories"""
        cats = list(cats)
        uf = UnionFind(cats)
        for i in range(0, len(cats)):
            for j in range(i + 1, len(cats)):
                artsi = src.cat_arts[cats[i]]
                artsj = src.cat_arts[cats[j]]

                if jaccard(artsi, artsj) > threshold:
                    uf.union(cats[i], cats[j])

        return uf


    # 1. Confirm that all articles are present
    if len(src.arts - out.arts) != 0:
        return error("Some articles are missing: %s..." % ", ".join(list(src.arts - out.arts)[:10]))

    # 2. Confirm that no new categories were introduced.
    if len(out.cats - src.cats) != 0:
        return error("Categories were introduced")

    missing = src.cats - out.cats
    grown = [cat for cat in out.cats if src.cat_arts[cat] != out.cat_arts[cat]]
    merges = {}

    if len(grown) > 0:
        if len(missing) == 0:
            return error("Some categories have additional articles, but no " +
                         "categories were removed")

        # Identify possible merge candidates as categories whose articles are a
        # subset of the super category.
        maybe = {}
        for m in missing:
            for g in grown:
                if src.cat_arts[m] < out.cat_arts[g]:
                    maybe.setdefault(g, set())
                    maybe[g].add(m)

        # 3. Confirm that at least one set of possible valid merges contains
        #    all of the articles in each super category.
        for g in maybe: # {g: [c1, c2, c3, ...]}
            # Map possible merge operations in a union-find
            uf = union_find(list(maybe[g]) + [g]) # be sure to consider the supercat
            sets = uf.sets(unary=False, contains=g)

            merges[g] = []

            for union in sets:
                for cats in all_combinations(union):
                    uf = union_find(cats).sets(unary=False, contains=g)
                    for union2 in uf:
                        #max_len = 0
                        arts = set()

                        for cat in union2:
                            #max_len = max(max_len, len(src.cat_arts[cat]))
                            arts = arts | src.cat_arts[cat]

                        all_arts = arts == out.cat_arts[g]
                        #labeled = len(src.cat_arts[m]) >= max_len

                        if all_arts: # and homogeneous: #and labeled
                            merges[g].append(cats)

            if len(merges[g]) == 0:
                return error("Not all categories merged into %s are connected by homogeneity OR the category label is wrong" % g)

    pairs = src.pairs - out.pairs
    cats = len(src.cats) - len(out.cats)
    supercats = len(grown)
    mergeops = sum([min([len(c) for c in merges[m]]) - 1 for m in merges.keys()])

    return results(True, pairs, cats, supercats, mergeops, None)





