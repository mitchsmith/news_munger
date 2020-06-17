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

class PersonScanner():
    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        """ Instantiate a new PersonScanner instance and declare vars"""
        
        self._person_refs = []
        self._people = []
        self.document = None

    def scan(self, document):
        """ Locate PERSON entities and identify individuals
        
        Results are stored in self._person_refs and self._people

        ARGS:
            document (required) str or spacy.Doc instance
        """
        
        if type(document) != Doc:
            if type(document) == str:
                self.document = nlp(document)
            else:
                raise TypeError("PersonScanner.scan requires str or Doc")
        else:    
            self.document = document

        # variants = set(
        #        [ent.text for ent in self.document.ents if ent.label_ == PERSON]
        #        )
        names = {}

        for n in reversed(
                    sorted([
                            ent.text.split(' ')
                            for ent
                            in document.ents
                            if ent.label_ == "PERSON"
                           ], key=lambda lst: len(lst)
                          )
                        ):
            if " ".join(n) not in names.keys():
                found = False
                print("{} not in names.keys.".format(" ".join(n)))
                for k in names.keys():
                    if re.search(" ".join(n), k):
                        print("re match in name keys")
                        names[k].append(" ".join(n))
                        found = True
                        break
        if not found:
             names[" ".join(n)] = [" ".join(n)]
        
        return names


    @property
    def person_refs(self):
        return self._person_refs

    @property
    def people(self):
        return self._people
    
    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._person_refs.keys()))



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


def interleave_sentences(doc1, doc2):
    text = ""
    newlines = re.compile(r"(\n+$)")
    articles = sorted([doc1, doc2], key=lambda doc: len([s for s in doc.sents]))
    for i, sentence in enumerate(articles[0].sents):
        if i % 2 == 0:
            text += sentence.text
        else:
            alttext = newlines.sub(
                                   newlines.search(sentence.text).groups()[0],
                                   [s for s in articles[1].sents][i].text
                                  )
            text += alttext
        
    return nlp(text)
                




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




