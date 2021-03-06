#!/usr/bin/env python

import sys
import operator

# Break a file into words.
def words(fileobj):
    for line in fileobj:
        for word in line.split():
            yield word

# Only record the top N
threshold = 100

counts = {}

total = 0
with open('/dev/stdin', 'r') as f:
    wordgen = words(f)
    for word in wordgen:
        if True: # len(word) <= 8:
            counts[word] = counts.get(word, 0) + 1
            total += 1

ignore = [] # ["the", "and", "be", "are", "is", "an", "a", "it", "we", "The", "from", "will", "can", "that", "to", "by"]

print "{",
totalSoFar = 0
printedSoFar = 0

for word in sorted(counts, key=counts.get, reverse=True):
    totalSoFar = totalSoFar + 1 # counts[word]
    if totalSoFar <= threshold:
        if word not in ignore:
            if printedSoFar > 0:
                print ", ",
            print repr(word) + ' : ' + str(counts[word]),
            printedSoFar = printedSoFar + 1
        
print "}"
    
