## Requirements

* Java 8
* sbt

## Usage

    $ sbt assembly
    $ cat input.csv | java -jar hack.jar > output.csv

Status messages are printed to `stderr`. Data printed to `stdout` can be given
to the validator.

## Notes

You can change how many states are explored by providing a `-b NUM` parameter.
This controls how many states are selected at each iteration. The default value
is 40.

For most data sets, values above 20 provide no improvement in final score but
might take longer to run. The program takes 15s at `-b 20` for all inputs except
`category-article.csv` (which takes 2m 30s).

The default was chosen to provide a reasonable buffer above the next highest score
on the leaderboard (for `category-article.csv`) while finishing in under 5m.

Runtime is probably linear in the number of categories and linear (with a low
coefficient) in the number of articles. This is because each category is
represented as a bit vector as long as the total number of articles: doubling
the number of categories probably doubles the number of bit vector operations,
and doubling the number of articles doubles their length.

