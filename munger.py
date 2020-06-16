#!/usr/bin/env python3

""" This module provides a collection of utilities for creating a madlibs-
style digest of news headlines and stories from a variety of feeds and 
scraped web pages.
"""

import os
import re
import datetime
import time
import json
import pickle
import spacy
from spacy.lang.en import English
from spacy.tokens import Doc, Span, Token
from spacy.matcher import PhraseMatcher
from collections import deque
from scrapers import Trends, Aggregator, APHeadlines, APArticle 



def load_or_refresh_ag():
    cached = datetime.date.today().strftime("tmp/ag_%Y%m%d.pkl")
    if os.path.isfile(cached):
        with open(cached, "rb") as pkl:
            ag = pickle.load(pkl)
    else:
        ag = Aggregator()
        ag.collect_ap_headlines()

        for url in [h[1] for h in ag.headlines if h[0] == 'Sports']:
            try:
                ag.fetch_ap_article(url)
            except:
                continue
            if len(ag.stories) >= 2:
                break

        for story in ag.stories:
            # ditch unpicklable
            story.driver = None

        with open(cached, "wb") as pkl:
            pickle.dump(ag, pkl)
        
    return ag


ag = load_or_refresh_ag()

nlp = spacy.load("en_core_web_sm")

Doc.set_extension("title", default=None)
Doc.set_extension("byline", default=None)
Doc.set_extension("timestamp", default=None)
Doc.set_extension("dateline", default=None)

docs = []
for i, story in enumerate(ag.stories):
    docs.append((nlp("\n".join(story.content))))
    docs[i]._.title = story.title
    docs[i]._.byline = story.byline
    docs[i]._.timestamp = story.timestamp




