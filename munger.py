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
from scrapersI import Trends, Aggregator, APHeadlines, APArticle
from scrapersII import WikiPerson

nlp = spacy.load("en_core_web_sm")

try:
    Doc.set_extension("title", default=None)
    Doc.set_extension("byline", default=None)
    Doc.set_extension("timestamp", default=None)
    Doc.set_extension("dateline", default=None)
    Doc.set_extension("people", default=None)
except ValueError:
    # Reloading pickled
    pass

class PersonScanner():
    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        """ Instantiate a new PersonScanner instance and declare vars"""
        self._people = {}
        self._document = None

    def scan(self, document):
        """ Locate PERSON entities and identify individuals
        
        ARGS:
            document (required) str or spacy.Doc instance

        RETURNS: A spacy.Doc instance with _.people attribute containing
            a dict of all variants of each person's name, with the longest
            form of each name as key.
        """
        
        if type(document) != Doc:
            if type(document) == str:
                self._document = nlp(document)
            else:
                raise TypeError("PersonScanner.scan requires str or Doc")
        else:    
            self._document = document
        
        self._people = {}

        for n in reversed(
                    sorted([
                            ent.text.split(' ')
                            for ent
                            in self._document.ents
                            if ent.label_ == "PERSON"
                           ], key=lambda lst: len(lst)
                          )
                        ):
            if " ".join(n) not in self._people.keys():
                found = False
                print("{} not in self._people.keys.".format(" ".join(n)))
                for k in self._people.keys():
                    if re.search(" ".join(n), k):
                        print("re match in name keys")
                        self._people[k].append(" ".join(n))
                        found = True
                        break
            if not found:
                self._people[" ".join(n)] = [" ".join(n)]
        
        self._document._.people = self._people
        return self._document

    def lookup_person(self, person_name):
        
        """Retrieve available person info from wikipedia

        ARGS: name (required) str

        RETURNS: WikiPerson instance
        
        """
        self.fullname = person_name
        query_term = self.fullname.replace(" ", "_")
        url = "https://en.wikipedia.org/w/index.php?search=" + query_term
        wikiperson = WikiPerson(url)
        return wikiperson

    def get_person_info(self, person):
        
        """ try to determine gender, etc. from the most complete PERSON reference.
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            dict containing discoverable PERSON attributes

        TODO: Rewrite this in a spacy way
        """

        gender = None
        honorific = None
        role = None
        first = None
        middle = None
        last = None
        suffix = None
        tokens = deque([p for p in person.split(' ') if re.search(r'\w+', p)])
        if tokens[0] in MASCULINE_TITLES:
            honorific = tokens.popleft()
            gender = "Male"
        elif tokens[0] in FEMININE_TITLES:
            honorific = tokens.popleft()
            gender = "Female"
        if tokens[0] in GENERIC_TITLES:
            role = tokens.popleft();
        elif re.match(r'\w\w+\.', tokens[0]):
            role = tokens.popleft()
        # At this point, element 0 should be either the first name or initial.
        if tokens[0] in names.words('female.txt'):
            if not gender:
                gender = 'Female'
        if tokens[0] in names.words('male.txt'):
            if not gender:
                gender = 'Male'
            elif not honorific:
                gender = 'Unknown'
        first = tokens.popleft()
        try:
            # Check for suffix: 'Esq.', 'Jr.'. 'Sr. etc. 
            if re.match(r'.+\.|Junior|Senior|[IVX]+$', tokens[-1]):
                suffix = tokens.pop()
        except IndexError:
            pass
        else:
            if tokens:
                last = tokens.pop()
            if tokens:
                middle = ' '.join(tokens)
        if honorific and not last:
            last = first
            first = None
        return {
                    'gender': gender,
                    'honorific': honorific,
                    'role': role,
                    'first': first,
                    'middle': middle,
                    'last': last,
                    'suffix': suffix,
                }



    @property
    def document(self):
        return self._document

    @property
    def people(self):
        return self._people
    
    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._people.keys()))



def load_or_refresh_ag():
    cached = datetime.datetime.today().strftime("tmp/ag_%Y%m%d.pkl")
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
    
    """ """
    
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
                

def objectify(document):

    """ Swap subjects with direct objects """

    # stub
    pass


ag = load_or_refresh_ag()

docs = []
for i, story in enumerate(ag.stories):
    docs.append((nlp("\n".join(story.content))))
    docs[i]._.title = story.title
    docs[i]._.byline = story.byline
    docs[i]._.timestamp = story.timestamp




