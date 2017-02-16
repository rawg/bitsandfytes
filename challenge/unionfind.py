#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


"""

import unittest

from collections import OrderedDict

class UnionFind(object):
    """A Union-Find data structure, aka a Disjoint-Set."""
    def __init__(self, items):
        # items[k] = position in sketch
        self.items = OrderedDict()
        i = 0
        for k in items:
            self.items[k] = i
            i += 1

        # pos[n] = item in position
        self.pos = list(self.items.keys())

        self.sketch = [i for i in range(0, len(items))]

    def union(self, items, parent=None):
        if type(items) is not list: #not hasattr(items, '__iter__') or type(items) is str:
            if type(items) is str:
                items = [items]
            else:
                items = list(items)

        if parent is None:
            p = self.sketch[self.items[items[0]]]
        else:
            p = self.items[parent]

        if parent not in items and parent is not None:
            items += [parent]

        # Find any parents at the locations of each item for replacement later.
        find = []
        for key in items:
            find.append(self.sketch[self.items[key]])

        # for each index, value in sketch
        for i, v in enumerate(self.sketch):
            # for each item (key)
            for replace in find:
                # if value in sketch matches a replacement value, change its
                # parent to match the new parent. This merges sets.
                if self.sketch[i] == replace:
                    self.sketch[i] = p

    def connected(self, item1, item2):
        return self.parent(item1) == self.parent(item2)

    def is_uniform(self):
        for i in range(1, len(self.sketch)):
            if self.sketch[i] != self.sketch[0]:
                return False
        return True

    def parent(self, child):
        i = self.items[child]
        return self.pos[self.sketch[i]]

    def sets(self, unary=True, contains=None):
        r = {}
        for i, v in enumerate(self.sketch):
            idx = self.pos[i]
            head = self.pos[v]

            r.setdefault(head, [])
            r[head].append(idx)

        ret = []
        for itm in r.items():
            single = unary or len(itm[1]) > 1
            has = contains is None or contains in itm[1]
            if single and has:
                ret.append(itm[1])
        return ret


    def children(self):
        r = {}
        for i, v in enumerate(self.sketch):
            if i != v:
                parent = self.pos[v]
                r.setdefault(parent, [])
                r[parent].append(self.pos[i])

        return r

    def __str__(self):
        return " ".join([self.pos[i] for i in self.sketch])

class UnionFindTest(unittest.TestCase):
    def test_union_parent(self):
        ls = ["a", "b", "c", "d"]
        uf = UnionFind(ls)
        uf.union("b", "a")
        self.assertEqual(uf.parent("b"), "a")

    def test_union(self):
        ls = ["a", "b", "c", "d"]
        uf = UnionFind(ls)
        uf.union(["b", "a"])
        self.assertEqual(uf.parent("b"), uf.parent("a"))

    def test_ordering(self):
        ls = ['networks', 'video hosting', 'internet television', 'peercasting', 'copyright law', 'streaming media systems', 'internet broadcasting', 'video on demand', 'entertainment websites', 'youtube', 'video on demand services']
        uf1 = UnionFind(ls)
        uf2 = UnionFind(ls)

        ops = ["networks -> streaming media systems",
            "copyright law -> streaming media systems",
            "peercasting -> streaming media systems",
            "entertainment websites -> youtube",
            "video hosting -> youtube",
            "entertainment websites -> video hosting",
            "copyright law -> networks",
            "networks -> peercasting",
            "copyright law -> peercasting",
            "internet broadcasting -> internet television",
            "internet television -> video on demand services"]
        for op in ops:
            l, r = op.split(" -> ")
            uf2.union(r, l)
            uf1.union(l, r)

        self.assertEqual(len(uf1.sets()), len(uf2.sets()))

    def test_children(self):
        ls = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        uf = UnionFind(ls)
        uf.union(["a", "e"], "b")
        uf.union(["h", "i"], "c")
        children = uf.children()
        self.assertEqual(2, len(children))
        self.assertEqual(children["b"], ["a", "e"])
        self.assertEqual(children["c"], ["h", "i"])

    def test_connected(self):
        ls = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        uf = UnionFind(ls)
        uf.union(["a", "c", "e"], "b")
        self.assertTrue(uf.connected("a", "e"))
        self.assertTrue(uf.connected("a", "b"))
        self.assertFalse(uf.connected("a", "f"))

    def test_disjoint_parent(self):
        ls = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
        uf = UnionFind(ls)
        uf.union(["a", "b"])
        uf.union(["c", "d"])
        uf.union(["b", "c"])
        self.assertEqual(uf.parent("a"), uf.parent("d"))

    def test_str(self):
        uf = UnionFind(["a", "b", "c"])
        uf.union("a", "c")
        self.assertEqual(str(uf), "c b c")

    def test_is_uniform(self):
        ls = ["a", "b", "c", "d"]
        uf = UnionFind(ls)
        self.assertFalse(uf.is_uniform())
        uf.union(["a", "b", "c"])
        self.assertFalse(uf.is_uniform())
        uf.union(["c", "d"])
        self.assertTrue(uf.is_uniform())

    def test_sets(self):
        ls = ["a", "b", "c", "d", "e", "f"]
        uf = UnionFind(ls)
        uf.union(["a", "b", "c"])
        uf.union(["d", "e"])
        self.assertEqual(len(uf.sets()), 3)
        sets = sorted([v for v in uf.sets()], key=lambda x: len(x))
        self.assertEqual(sets[0], ["f"])
        self.assertEqual(sets[1], ["d", "e"])
        self.assertEqual(sets[2], ["a", "b", "c"])

    def test_sets_unary(self):
        ls = ["a", "b", "c", "d", "e", "f"]
        uf = UnionFind(ls)
        uf.union(["a", "b", "c"])
        uf.union(["d", "e"])
        self.assertEqual(len(uf.sets(unary=False)), 2)
        sets = sorted([v for v in uf.sets(unary=False)], key=lambda x: len(x))
        self.assertEqual(sets[0], ["d", "e"])
        self.assertEqual(sets[1], ["a", "b", "c"])

    def test_sets_contains(self):
        ls = ["a", "b", "c", "d", "e", "f"]
        uf = UnionFind(ls)
        uf.union(["a", "b", "c"])
        uf.union(["d", "e"])
        self.assertEqual(len(uf.sets(contains="b")), 1)
        sets = sorted([v for v in uf.sets(contains="b")], key=lambda x: len(x))
        self.assertEqual(sets[0], ["a", "b", "c"])

if __name__ == '__main__':
    unittest.main()
