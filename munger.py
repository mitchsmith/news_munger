#!/usr/bin/env python3

""" This module provides a collection of utilities for creating a madlibs-
style digest of news headlines and stories from a variety of feeds and 
scraped web pages.
"""

import os
import re
import time
import json
import spacy
from collections import deque
from scrapers import Trends, Aggregator, APHeadlines, APArticle 

nlp = spacy.load("en_core_web_sm")

ag = Aggregator()
ag.collect_ap_headlines()

for url in [h[1] for h in ag.headlines if h[0] == 'Sports']:
    try:
        ag.fetch_ap_article(url)
    except:
        continue
    if len(ag.stories) >= 2:
        break

# Import the Matcher
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
doc = nlp("Upcoming iPhone X release date leaked as Apple reveals pre-orders")

# Initialize the Matcher with the shared vocabulary
matcher = Matcher(nlp.vocab)

# Create a pattern matching two tokens: "iPhone" and "X"
pattern = [{"TEXT": "iPhone"}, {"TEXT": "X"}]

# Add the pattern to the matcher
matcher.add("IPHONE_X_PATTERN", None, pattern)

# Use the matcher on the doc
matches = matcher(doc)
print("Matches:", [doc[start:end].text for match_id, start, end in matches])


