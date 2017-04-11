package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"path/filepath"
)

func main() {
	inFile := ""
	//inFile = "c:/users/dt12944/downloads/category-article.csv"
	//inFile = "c:/users/dt12944/downloads/multiple-merges.csv"
	//inFile = "c:/users/dt12944/downloads/remix.csv"
	//inFile = "c:/users/dt12944/downloads/redundant-removals.csv"

	if len(os.Args) == 2 {
		inFile = os.Args[1]
	}

	if len(inFile) < 1 {
		log.Fatal("Must supply target file on command line")
	}

	dir, file := filepath.Split(inFile)
	outFile := dir + "jsk_" + file

	fmt.Println("Processing file   : ", inFile)
	fmt.Println("Saving results to : ", outFile)

	reducer := Reducer{}
	reducer.parseFile(inFile)
	reducer.eliminate()
	reducer.merge()
	reducer.save(outFile)
}

// we use go's map[type]bool as a set
// making use of go's map nil value property for bool (false)
// map[item] returns true if it exists, false if it does not
// also it's easier to delete an item from a map than a slice

type article struct {
	name string
	cats map[*category]bool
}

type category struct {
	name string
	sc *superCategory
	arts map[*article]bool
}

func  (c * category) canEliminate() bool {
	// we can eliminate this category if all of the articles have at least one additional category
	for a := range c.arts {
		if len(a.cats) == 1 {
			return false
		}
	}
	return true
}

type superCategory struct {
	cats []*category		// don't need a set here
}

func (sc *superCategory) merge(sc2 *superCategory) {
	for _, c := range sc2.cats {
		sc.cats = append(sc.cats, c)
		c.sc = sc
	}
}

type Reducer struct {
	// these maps are for lookup
	cats map[string]*category
	arts map[string]*article
	// the active super categories, start with one per category
	// merge as needed, removing the eliminated one (map makes it easier to eliminate than slices
	// could use linked list
	scs  map[*superCategory]bool
}

func (reducer *Reducer) parseFile(fileName string) {

	fp, err := os.Open(fileName)
	if err != nil {
		log.Fatal(err)
	}
	defer fp.Close()

	r := csv.NewReader(fp)
	r.LazyQuotes = true
	rawData, err := r.ReadAll()
	if err != nil {
		log.Fatal(err)
	}
	reducer.cats = make(map[string]*category)
	reducer.arts = make(map[string]*article)
	reducer.scs = make(map[*superCategory]bool)

	id := 1
	for idx, row := range rawData {
		if idx == 0 && "category" == row[0] {
			// skip header row if there
			continue
		}
		a := reducer.arts[row[1]]
		if a == nil {
			a = &article{name: row[1], cats: make(map[*category]bool)}
			reducer.arts[row[1]] = a
		}
		c := reducer.cats[row[0]]
		if c == nil {
			c = &category{name: row[0], arts: make(map[*article]bool)}
			reducer.cats[row[0]] = c
			// every super category starts out with only one category
			sc := &superCategory{}
			c.sc = sc
			sc.cats = append(sc.cats, c)
			reducer.scs[sc] = true
			id++
		}
		a.cats[c] = true
		c.arts[a] = true
	}

}

// look for any category whose articles have at least one additional category
// the following is not deterministic - you can get a different result each time you
// run it.  this is caused because the order we eliminate items matters
// the way GO implements it map you get a different iteration order each time,
// tried sorting it by size but didn't seem much of a difference
// TODO : determine best order to eliminate categories
func (reducer *Reducer) eliminate() bool {
	change := false

	for _, c := range reducer.cats {
		if c.canEliminate() {
			// remove the category from the articles
			for a := range c.arts {
				delete(a.cats, c)
			}
			// remove the category
			delete(reducer.cats, c.name)
			delete(reducer.scs, c.sc)
			change = true
		}
	}
	return change
}

// determine what other categories this category could be merged with
func (reducer *Reducer) merge() bool {
	change := false
	for _, c := range reducer.cats {
		// walk through each article associated with the category and see what other
		// categories those articles are associated with,
		// when we count them that will also give us the intersection number
		candidates := make(map[*category]int)
		for a := range c.arts {
			for otherC := range a.cats {
				// we're not interested if the other category is us
				// TODO : add check to see if we've already looked at this pair and not met merging criteria
				if c != otherC {
					candidates[otherC] = candidates[otherC] + 1
				}
			}
		}
		// we now have a list of other categories that we share articles with
		for otherC, count := range candidates {
			// we may have merged categories already so check
			if c.sc == otherC.sc {
				continue
			}
			jaccard := float64(count) / float64(len(c.arts)+len(otherC.arts)-count)
			if jaccard > 0.75 {
				// merge the two super categories, does not matter which one remains since we'll calculate the name later
				sc := c.sc
				sc2 := otherC.sc
				sc.merge(sc2)
				delete(reducer.scs, sc2)
				change = true
			}
		}
	}
	return change
}

func (reducer *Reducer) save(outFile string) {
	out, err := os.Create(outFile)
	if err != nil {
		log.Fatal("could not create file : ", outFile, "   : ", err)
	}
	defer out.Close()
	// we will walk through all the categories in this each super category
	// the one that has the most articles will name the super categories
	// a set will be created of all the articles from each of the categories, eliminating duplicates
	// that will then be our pairs
	for sc := range reducer.scs {
		maxSize := 0
		articles := make(map[*article]bool)
		cName := ""

		for _, c := range sc.cats {
			// the name of the super-category is the category with the most original articles
			if len(c.arts) > maxSize {
				cName = c.name
				maxSize = len(c.arts)
			}
			// collect the articles in a set so we cn eliminate duplicates
			for a := range c.arts {
				articles[a] = true
			}
		}
		w := csv.NewWriter(out)
		for a := range articles {
			w.Write([]string{cName,a.name})
		}
		w.Flush()
	}
}
