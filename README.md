
Code Fight: Noisy Categories
============================

We have a lot of new faces in Applied Analytics. It's a good time to do something fun, and what could be more fun than a code fight?

OK, you might argue for paint ball, go karts, indoor skydiving, or Starcraft. But intellectual competitions *are* fun, and they can make an engineering team better.

Wikipedia's data model has articles and categories, with a many-to-many relationship between the two. I was recently working with a set of articles and their categories, and found that many of those categories added little or no information. It would be beneficial to my end problem to remove as many categories as I could without orphaning any articles.

I've attached a sample dataset with ~5,500 categories and ~15,600 category-article pairs. My challenge – for those of you who believe yourselves up to the task – is to minimize the number of category-article pairs by removing whole categorieswithout leaving any articles sans category.

This is a competitive challenge that will *award prizes* for 1st and 2nd places. But to earn the gold, you'll have to beat my solution, which will mean pruning thousands of categories.

Rules
-----
All AAG associates (and perhaps a few outsiders to keep it interesting) are allowed to join in this intellectual brawl.
This challenge will be active starting IMMEDIATELY until one minute after midnight on the 24th. That's 2017-02-24 00:01:00.
I will present my solution in the Data Science Sharing session at 10:00 on the 24th.
You must manage your own time. If you miss any deadlines during the challenge window, not only will you have to answer to Chelsea, but you will be disqualified.
Participation is optional.
You may ask me for help at any time. I will *not* suggest approaches, but I will respond to well-formed questions with broad topics and reference materials.
Your solution must be a program. All languages are fair game, but please don't make the judges (me) install R.
Your solution must accept a CSV file similar to the one provided as input, and write its output to a separate CSV file with the same two column structure. You may hardcode file locations.
Team submissions are permissible, but there can be only one submission per team and your team loyalty must be absolute – no straddling multiple teams!

Operations
----------
There are two operations permitted:
 1. Remove categories
   - Only whole categories are permitted; specific category-article pairs cannot be removed.
   - Remember that all articles must have a category.
 2. Merge homogeneous categories into supercategories
   - Two categories will be considered homogeneous when they contain > 75% of the same articles.
   - Supercategories may contain more than two original categories, provided at least two categories in the newly formed set are homogenous.
   - The resulting supercategories must keep the label of the largest category in the set.

Scoring
-------
 1. 70 points will be awarded based on the total number of category-article pairs removed. The highest score will get the full 70 points and dictate the scale for all other submissions.
 2. 20 points will be awarded based on the total number of categories removed, and scaled in the same manner as 1.
 3. 10 points will be awarded for runtime complexity and style.
   - When judging runtime complexity, you can load the source list into memory and write the result to disk for free provided both are O(n).
   - Style will be judged by the use of algorithms and data structures, not how well you format your code or how descriptive your comments are.
