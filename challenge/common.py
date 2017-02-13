#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


"""

class TallyCollection(object):
    """A dict of counts."""
    def __init__(self):
        self.counts = {}

    def inc(self, key):
        self.counts.setdefault(key, 0)
        self.counts[key] += 1

    def nonzero(self, keys):
        for key in keys:
            if self.counts[key] <= 1:
                return False
        return True

    def decr(self, keys):
        for key in keys:
            self.counts[key] -= 1


def jaccard(set1, set2):
    """Return the Jaccard distance between sets 1 and 2."""
    return len(set1 & set2) / len(set1 | set2)
