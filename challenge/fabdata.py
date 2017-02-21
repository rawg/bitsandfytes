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
parser.add_argument("-i", "--infile", help="input file", required=False, default=None)
parser.add_argument("-o", "--outfile", help="output file", required=True)

parser.add_argument("--homo", help="number of homogeneous categories", default=100, type=int, required=False)
parser.add_argument("--dupe", help="number of duplicate categories", default=100, type=int, required=False)
parser.add_argument("--uniq", help="number of unique categories", default=10, type=int, required=False)

parser.add_argument("--certain", help="be (sort of) certain not to reuse categories", action="store_true")
parser.add_argument("--uncertain", action="store_false", dest="certain")
parser.set_defaults(certain=True)

parser.add_argument("-G", "--generate", help="generate article and category names", action="store_true")
parser.add_argument("--cardinality", help="Average category-article cardinality when generating", type=int, default=5)
args = parser.parse_args()


class DataManager(object):
    def __init__(self, certain=True):
        self.output = []
        self.deleted = []
        self.certain = certain
        self.cats = None
        self.arts = None

    def record(self, cat, art):
        self.output.append([cat, art])
        if self.certain:
            if cat in self.cats:
                self.deleted.append(cat)
                del self.cats[self.cats.index(cat)]

    def record_many(self, ls):
        for item in ls:
            self.record(item[0], item[1])

    def _recycle_cats(self):
        self.cats = self.deleted
        self.deleted = []
        logging.debug("Recycled deleted categories")

    def get_cat(self):
        if len(self.cats) == 0:
            self._recycle_cats()
        return random.choice(self.cats)

    def get_cats(self, k):
        if len(self.cats) < k:
            self._recycle_cats()
        return random.sample(self.cats, k)

    def get_art(self):
        return random.choice(self.arts)

    def get_arts(self, k):
        return random.sample(self.arts, k)


class FileManager(DataManager):
    def __init__(self, infile, certain=True):
        super().__init__(certain)

        cats = set()
        arts = set()

        with open(infile, "r") as csvfile:
            reader = csv.reader(csvfile)

            head = next(reader)
            if head[0] != "category" or head[1] != "article":
                csvfile.seek(0)

            for cat, art in reader:
                cats.add(cat)
                arts.add(art)

        self.cats = list(cats)
        self.arts = list(arts)

    def record(self, cat, art):
        super().remove(cat, art)
        if self.certain:
            if cat in self.cats:
                del self.cats[self.cats.index(cat)]


class RandomManager(DataManager):
    def __init__(self, ncats=5000, narts=5000, certain=True):
        super().__init__(certain)

        from nltk.corpus import wordnet as wn
        nouns = list(wn.all_synsets("n"))
        verbs = list(wn.all_synsets("v"))
        adjs  = list(wn.all_synsets("a"))

        def get_word(ls):
            term = random.choice(ls)
            return term.name().split(".")[0].replace("_", " ")

        self.cats = []
        for _ in range(0, ncats):
            self.cats.append("%s %s" % (get_word(adjs), get_word(nouns)))

        self.arts = []
        for _ in range(0, narts):
            self.arts.append("%s %s" % (get_word(verbs), get_word(nouns)))


if not args.generate:
    if args.infile is None:
        logging.fatal("No input file provided!")
        exit(1)
    else:
        datamgr = FileManager(args.infile, args.certain)
else:
    ncats = (args.homo + args.dupe + args.uniq) * 10
    narts = ncats * args.cardinality * 2
    datamgr = RandomManager(ncats, narts, args.certain)

logging.debug("Loaded input data")


# Stand alone entries
for i in range(0, args.uniq):
    cat = datamgr.get_cat()
    art = datamgr.get_art()
    datamgr.record(cat, art)


# Categories with duplicate contents
for i in range(0, args.dupe):
    base = datamgr.get_arts(random.randint(5, 20))
    dupes = []
    for j in range(0, random.randint(1, 5)):
        cat = datamgr.get_cat()
        for art in base:
            dupes.append([cat, art])
    datamgr.record_many(dupes)


# Homogeneous categories
for i in range(0, args.homo):
    base = datamgr.get_arts(15)
    for j in range(0, random.randint(1, 5)):
        cat = datamgr.get_cat()
        extra = datamgr.get_arts(random.randint(1, 3))

        for art in base + extra:
            datamgr.record(cat, art)

random.shuffle(datamgr.output)

with open(args.outfile, "w") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["category", "article"])

    for row in datamgr.output:
        writer.writerow(row)

