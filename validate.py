#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Category reduction validator.

Example:

    $ python validate.py -i path/to/source.csv -o path/to/results.csv

"""
import argparse
import logging
from challenge.validate import validate

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Validate submission output.")
    parser.add_argument("-i", "--input", help="input (original source) data file", default="category-article.csv", required=False)
    parser.add_argument("-o", "--output", help="output data file", default="reduced.csv", required=False)

    parser.add_argument("--threshold", help="merge threshold as minimum Jaccard similarity", default=0.75, type=float, required=False)

    parser.add_argument("--headers", help="detect column headers", action="store_true")
    parser.add_argument("--no-headers", action="store_false", dest="headers")
    parser.set_defaults(headers=True)

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    score = validate(args.input, args.output, args.threshold, args.headers)
    if not score["success"]:
        print("[FAIL] %s" % score["message"])
        exit(1)
    else:
        print("[PASS] %i pairs and %i categories removed. %i super categories found after at least %i merges." % (score["pairs"], score["cats"], score["supercats"], score["merges"]))
