import csv
import os.path

inputFile = 'input/input.csv'
hashOutFile = os.path.join('output', 'hashPaths.txt')
resultOutFile = os.path.join('output','result.csv')

# For joining homogeneous categories
items = {}
weights = {}
sizes = {}
homo = {}

# For removing redundant categories
catsToArts = {}
artsToCounts = {}
finalCats = set()

# Evaluation metric
jCount = 0
jLtCount = 0

# Parses the CSV, and produces the relevant data structures
def loadFile():
	global items, weights, sizes
	filename = inputFile
	totalUniqueItems = 0
	totalUniqueCats = 0
	
	items = {}
	weights = {}
	sizes = {}
	catsToArts = {}
	artsToCounts = {}
	
	with open(filename, 'r') as f:
		reader = csv.reader(f)
		try:
			#skip header
			next(reader, None)

			for row in reader:
				tui, tuc = processRow(row)
				totalUniqueItems += tui
				totalUniqueCats += tuc
			
		except csv.Error as e:
			print("csv error")
			print(e)
	
	print
	print("we have %s unique articles" % totalUniqueItems)
	print("we have %s unique categories " % totalUniqueCats)
	print

# Parses a row of the CSV, updating the relevant data structures
def processRow(row):
	global items, sizes, catsToArts, artsToCounts
	category = row[0]
	article = row[1]
	totalUniqueItems = 0
	totalUniqueCats = 0
	isInCategory = False
	
	if not (category in sizes):
		catsToArts[category] = set()
		sizes[category] = 0
		totalUniqueCats = 1
	elif (article in catsToArts[category]):
		isInCategory = True
	
	if not (article in items):
		items[article] = [category]
		totalUniqueItems = 1
		artsToCounts[article] = 0
	elif not (isInCategory):
		buildWeights(items[article], category)
		items[article].append(category)
	
	if not (isInCategory):
		catsToArts[category].add(article)
		artsToCounts[article] += 1
		sizes[category] += 1
	
	return totalUniqueItems, totalUniqueCats

# Constructs a weight table between each category
def buildWeights(list, newCat):
	global weights
	key = ''
	a = ''
	b = ''
	
	for cat in list:
		if cat > newCat:
			key = cat + ',' + newCat
	 		a = cat
			b = newCat
		else :
			key = newCat + ',' + cat
 			a = newCat
			b = cat
		
		if not (key in weights):
			weights[key] = {
				'w' : 0,
				'a' : a,
				'b' : b,
			}
		
		weights[key]['w'] += 1

# Finds homogenous categories, and produces merge trees
def findHomo():
	global homo, jCount, jLtCount
	jaccardWeights = 0
	jaccard = 0
	k = 0
	
	for key in weights:
		k += 1
		weight = weights[key]['w']
		catA = weights[key]['a']
		catB = weights[key]['b']
		sizeA = sizes[catA]
		sizeB = sizes[catB]
		
		jaccard = float(weight) / float(sizeA + sizeB - weight)
		
		if jaccard > 0.75:
			jaccardWeights += 1
			
			# Tracks percent of Jaccard scores in [0.75, 100)
			# Used as an additional evaluation metric
			jCount += 1
			if jaccard < 1:
				jLtCount += 1
			
			if sizeA > sizeB:
				homo[catB] = catA
			elif sizeB > sizeA:
				homo[catA] = catB
			else:
				if catA > catB:
					homo[catA] = catB
				else:
					homo[catB] = catA
	
	print('there are %s weights in total' % k)
	print('there are %s weights which passed jaccard test' % jaccardWeights)
	print

# Flattens the merge trees into child -> root mapping
def optomizeHomo():
	global homo
	a = 0
	optoCat = []
	cat = ''
	hashPaths = ''
	
	for origCat in homo:
		a += 1
		optoCat = []
		cat = origCat
		hashPaths += cat
		
		while cat in homo:
			optoCat.append(cat)
			cat = homo[cat]
			hashPaths += ' -> ' + cat
		hashPaths += '\n'
		
		for littleCat in optoCat:
			homo[littleCat] = cat
	
	print('there are a total of %s homogeneous categories' % a)
	print
	f = open(hashOutFile, 'w')
	f.write(hashPaths)
	f.close()

# Updates the data structures used in deletion, relative to the flattened homogenous trees
def updateDeletionList():
	global catsToArts, artsToCounts
	
	for cat in catsToArts:
		if cat in homo:
			littleCat = catsToArts[cat]
			bigCat = catsToArts[homo[cat]]
			
			catsToArts[homo[cat]] = bigCat.union(littleCat)
			
			for art in bigCat.intersection(littleCat):
				artsToCounts[art] -= 1
			
			catsToArts[cat] = set()

# Scores each category on its deletion priority
# A score close to 1 suggests that most articles in this category have very few categories
# A score close to 0 suggests that most articles in this category have many categories
def findDeletionScore(cat, arts):
	global artsToCounts
	
	occurences = 0
	
	for art in arts:
		occurences += artsToCounts[art]
	
	return float(len(arts)) / float(occurences)

# Compares to categories based on their length and deletion score
# Elements are sorted in ascending order by deletion scores
# Elements with identical scores are sorted in descending order by length
def deletionComparison(x, y):
	if (x["score"] != y["score"]):
		# As scores are floats, the integer return values are manually set
		if x["score"] < y["score"]: return -1
		else: return 1
	else: return y["len"] - x["len"]

# Generates a list of categories which should be included in the output file
def deleteCategories():
	global catsToArts, artsToCounts, finalCats
	
	catList = []
	
	# Generates a weighted list of categories
	for cat in catsToArts:
		arts = catsToArts[cat]
		
		if (len(arts) > 0):
			catList.append({
				'cat': cat,
				'len': len(arts),
				'score': findDeletionScore(cat, arts)
			})
	
	catList = sorted(catList, cmp=deletionComparison)
	
	# Removes all possibly elements in a greedy fashion
	for elt in catList:
		cat = elt["cat"]
		toRemove = True
		
		for art in catsToArts[cat]:
			if (artsToCounts[art] == 1):
				toRemove = False
		
		if toRemove:
			for art in catsToArts[cat]:
				artsToCounts[art] -= 1
		else :
			finalCats.add(cat)

# Generates the output file using the include list, and homogenous mappings
def outputResults():
	global items, weights, sizes, homo
	output = 'category,article\n'
	cat = ''
	bigCat = ''
	d = 0
	totalItems = 0
	
	# Iterate through all items
	for item in items:
		potCats = {}
		
		totalItems += 1
		# For each item in our cat list
		for cat in items[item]:
			# If there is a better group, use that
			if cat in homo:
				cat = homo[cat]
				if cat in potCats:
					d += 1
			if cat in finalCats:
				potCats[cat] = True
			
		# Can add comma / quote checking
		if ',' in item:
			item = '"' + item + '"'
		
		for outCat in potCats:
			if ',' in outCat:
				outCat = '"' + outCat + '"'
			output += outCat.strip() + ',' + item.strip() + '\n'
	
	print('there are a total of %s category-article pairs' % totalItems)
	print('we eliminated a total of %s category-article pairs' % d)
	print
	
	f = open(resultOutFile, 'w')
	f.write(output)
	f.close()
	
	# Reset globals
	items = {}
	weights = {}
	sizes = {}
	homo = {}

# Executes program
def run():
	loadFile()
	findHomo()
	optomizeHomo()
	updateDeletionList()
	deleteCategories()
	outputResults()

# Parses the output CSV as a sanity check
def retest(filename):
	# Stripped down copy of loadFile + process row
	global items, weights, sizes
	totalUniqueItems = 0
	totalUniqueCats = 0
	
	items = {}
	weights = {}
	sizes = {}
	
	with open(filename, 'r') as f:
		reader = csv.reader(f)
		try:
			# Skip header
			next(reader, None)
			
			for row in reader:
				category = row[0]
				article = row[1]
				
				if not (article in items):
					items[article] = True
					totalUniqueItems += 1
				
				if not (category in sizes):
					sizes[category] = True
					totalUniqueCats += 1
					
		except csv.Error as e:
			print("csv error")
	
	print("we have %s unique articles" % totalUniqueItems)
	print("we have %s unique categories" % totalUniqueCats)	
	print

# Performs a difference on the input set of articles and output set of articles
# This acts as a sanity check
def diffFiles(fileA, fileB):
	ACats = set()
	BCats = set()
	AArts = set()
	BArts = set()
	
	with open(fileA, 'r') as f:
		reader = csv.reader(f)
		try:
			# Skip header
			next(reader, None)
			
			for row in reader:
				ACats.add(row[0])
				AArts.add(row[1])
				
		except csv.Error as e:
			print("csv error")
	with open(fileB, 'r') as f:
		reader = csv.reader(f)
		try:
			# Skip header
			next(reader, None)
			
			for row in reader:
				BCats.add(row[0])
				BArts.add(row[1])
				
		except csv.Error as e:
			print("csv error")
	
	print("A - B")
	print(len(AArts))
	print(len(BArts))
	print(AArts.difference(BArts))
	print(BArts.difference(AArts))

# Summerizes which percent of merges resulting from consuming subsets
def jaccardianBalance():
	global jLtCount, jCount
	
	percentUnderOne = float(jLtCount) / float(jCount) * 100
	
	print("%s percent of merges did not consume subsets" % percentUnderOne)
	print

run()
jaccardianBalance()
retest(resultOutFile)
diffFiles(resultOutFile, inputFile)

