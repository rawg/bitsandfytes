# -*- coding: utf-8 -*-
import pandas as pd
import os
from csv import QUOTE_MINIMAL

input_filename  = "input.csv" #os.path.join("input-files", "1.10x10.csv")
output_filename = "output.csv" #os.path.join("output", "1.10x10-output.csv")

def jSim(*args):
    if not all([type(s) == set for s in args]):
        return None
    elif len(args) == 0:
        return None
    elif len(args) == 1:
        return float(1)
    else:
        numerator = len(set.intersection(*args))
        denominator = len(set.union(*args))
        result = numerator / denominator
        return result

def articlesInCategory(pairs_frame, category_name):
    return pairs_frame.groupby(by="category").get_group(category_name).article.values

def articlesInCategorySet(pairs_frame, category_name):
    return set(pairs_frame.groupby(by="category").get_group(category_name).article.values)

def combineCats(input_filename, output_filename, cat_size_threshold=None):
    print("\n\nStarting with input file:", input_filename)

    capairs = pd.read_csv(input_filename, header=0, names=["category","article"], encoding="utf8")

    if cat_size_threshold == None:
        cat_size_threshold = len(capairs)


    # Just some demo bits
    #articles_by_category = capairs.groupby(by="category")
    #articlecount_by_category = articles_by_category.aggregate(len)
    #categories_by_article = capairs.groupby(by="article")
    #categorycount_by_article = categories_by_article.aggregate(len)

    print("\n--------- Merging categories ---------")

    all_groups = capairs.groupby(by="category").groups
    all_groups_set = set(capairs.groupby(by="category").groups)

    replacements = dict()

    for inspect_category in all_groups:
        articlecount_by_category = capairs.groupby(by="category").aggregate(len)

        inspect_set_size = articlecount_by_category.loc[inspect_category].article
        print("\nLooking for cats to merge with '{cat}' (size {catsize})".format(cat=inspect_category, catsize=inspect_set_size))

        if inspect_set_size <= cat_size_threshold:
            inspect_set = articlesInCategorySet(capairs, inspect_category)

            for hungry_category in all_groups:
                hungry_set_size = articlecount_by_category.loc[hungry_category].article

                if inspect_category != hungry_category and inspect_set_size <= hungry_set_size:
                    hungry_set = articlesInCategorySet(capairs, hungry_category)

                    if hungry_category not in replacements and jSim(inspect_set, hungry_set) > 0.75:
                        """try:
                            print("(remove) capairs.replace({{'category': {{ {to_replace}: {replace_with} }} }})".format(
                                to_replace=inspect_category, replace_with=hungry_category))
                            capairs.replace({'category': {inspect_category: hungry_category}}, inplace=True)
                        except ValueError:
                            # if inspect_category == hungry_category, just let it be
                            pass"""
                        replacements.update({inspect_category: hungry_category})

                        #print(capairs.category.nunique(), "categories remain")
                        #print(capairs.category.count(), "pairs remain")
                        #break
        print("---------")

    for to_replace, replace_with in sorted(replacements.items()):
        print("( merge) replace {to_replace} with {replace_with}".format(to_replace=to_replace, replace_with=replace_with))
        capairs.replace({'category': {to_replace: replace_with}}, inplace=True)

    capairs.drop_duplicates(inplace=True)
    print(capairs.category.nunique(), "categories remain")
    print(capairs.category.count(), "pairs remain")

    #capairs.to_csv(output_filename, index=False, encoding="utf8", quoting=QUOTE_MINIMAL)


    print("\n--------- Removing categories ---------")

    all_groups = capairs.groupby(by="category").groups
    all_groups_set = set(capairs.groupby(by="category").groups)

    replacements = dict()

    for inspect_category in all_groups:
        articlecount_by_category = capairs.groupby(by="category").aggregate(len)

        inspect_set_size = articlecount_by_category.loc[inspect_category].article
        print("\nLooking for cats to consume '{cat}' (size {catsize})".format(cat=inspect_category, catsize=inspect_set_size))

        if inspect_set_size <= cat_size_threshold:
            inspect_set = articlesInCategorySet(capairs, inspect_category)

            for hungry_category in all_groups:
                hungry_set_size = articlecount_by_category.loc[hungry_category].article

                if inspect_category != hungry_category and inspect_set_size <= hungry_set_size:
                    hungry_set = articlesInCategorySet(capairs, hungry_category)

                    if hungry_category not in replacements and inspect_set.issubset(hungry_set):
                        """try:
                            print("(remove) capairs.replace({{'category': {{ {to_replace}: {replace_with} }} }})".format(
                                to_replace=inspect_category, replace_with=hungry_category))
                            capairs.replace({'category': {inspect_category: hungry_category}}, inplace=True)
                        except ValueError:
                            # if inspect_category == hungry_category, just let it be
                            pass"""
                        replacements.update({inspect_category: hungry_category})

                        #print(capairs.category.nunique(), "categories remain")
                        #print(capairs.category.count(), "pairs remain")
                        #break
        print("---------")

    for to_replace, replace_with in sorted(replacements.items()):
        print("(remove) replace {to_replace} with {replace_with}".format(to_replace=to_replace, replace_with=replace_with))
        capairs.replace({'category': {to_replace: replace_with}}, inplace=True)

    capairs.drop_duplicates(inplace=True)
    print(capairs.category.nunique(), "categories remain")
    print(capairs.category.count(), "pairs remain")

    capairs.to_csv(output_filename, index=False, encoding="utf8", quoting=QUOTE_MINIMAL)
    print("\nWrote to output file:", output_filename)

    return capairs

pairs = combineCats(input_filename, output_filename)
