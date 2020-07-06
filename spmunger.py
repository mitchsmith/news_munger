#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import lemminflect
from spacy.lang.en import English
from spacy.tokens import Doc, Span, Token
from spacy.matcher import Matcher, PhraseMatcher
from collections import deque
from scrapersI import Trends, Aggregator, APHeadlines, APArticle
from scrapersI import GENERIC_TITLES, FEMININE_TITLES, MASCULINE_TITLES
from scrapersII import WikiPerson
from gtts import  list_voices, text_to_mp3
from helpers import kill_firefox
from munger import load_or_refresh_ag 

nlp = spacy.load("en_core_web_md")

try:
    Doc.set_extension("title", default=None)
    Doc.set_extension("byline", default=None)
    Doc.set_extension("timestamp", default=None)
    Doc.set_extension("dateline", default=None)
    Doc.set_extension("people", default=None)
except ValueError:
    # Reloading pickled
    pass


# Classes

class Person():
    
    """  """
    
    def __init__(self, name=None, *args, **kwargs):
        self.name = name
        self.appears_in = []
        self._aka = []
        self._info = None
        self._wikidata = None

    def aka_include(self, alias_list):
        self._aka.extend(alias_list)
        self._aka = sorted(
                            set(self._aka),
                            key=lambda n: len(n.split(" ")),
                            reverse = True
                          )
    
    def merge_info(info):
        self._info = info

    @property
    def aka(self):
        return self._aka

    @property
    def info(self):
        return self._info

    @property
    def wikidata(self):
        return self._wikidata
    
    @wikidata.setter
    def wikidata(self, value):
        if type(value) == WikiPerson:
            self._wikidata = value

    def __repr__(self):
        return "<Person: {}>".format(self.name)


class Organization():
    
    """  """

    def __init__(self, name=None, *args, **kwargs):
        self.name = name

    def __repr__(self):
        return "<Organization: {}>".format(self.name)


class GeoPoliticalEntity():
    
    """  """
    
    def __init__(self, name=None, *args, **kwargs):
        self.name = name

    def __repr__(self):
        return "<GeoPoliticalEntity: {}>".format(self.name)


class Scanner():

    """ """
    def __init__(self):
        self._document = None
        self._entity_type = "PERSON"

    def scan(self, document):
        
        """ Locate entities of a given entity type
        
        ARGS:
            document (required) str or spacy.Doc instance

        RETURNS: A dict of all variants of each entity's name, with
            the longest form of each name as key.
        """
        
        if type(document) != Doc:
            if type(document) == str:
                self._document = nlp(document)
            else:
                raise TypeError("Scanner.scan requires str or Doc")
        else:
            self._document = document
        
        self._entities = {}

        for n in reversed(
                    sorted([
                            ent.text.split(' ')
                            for ent
                            in self._document.ents
                            if ent.label_ == self._entity_type
                           ], key=lambda lst: len(lst)
                          )
                        ):
            if " ".join(n) not in self._entities.keys():
                found = False
                print("{} not in self._entities.keys.".format(" ".join(n)))
                for k in self._entities.keys():
                    if re.search(" ".join(n), k):
                        print("re match in name keys")
                        self._entities[k].append(" ".join(n))
                        found = True
                        break
            if not found:
                self._entities[" ".join(n)] = [" ".join(n)]
        
        if self._entity_type == "PERSON":
            self._document._.people = self._entities
        
        return self._entities



class PersonScanner(Scanner):

    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        super().__init__()

    def lookup_person(self, person_name):
        
        """Retrieve available person info from wikipedia

        ARGS: person_name (required) str

        RETURNS: WikiPerson instance
        
        """
        self.fullname = person_name
        # query_term = self.fullname.replace(" ", "_")
        #url = "https://en.wikipedia.org/w/index.php?search=" + query_term
        wikiperson = WikiPerson(person_name)
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
        return self._entities
    
    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._entities.keys()))




class DocumentCatalog():
    
    """  """

    def __init__(self, document_list, *args, **kwargs):
        if type(document_list) != list:
            raise TypeError
        self.documents = document_list
        self.created_at = datetime.datetime.now().isoformat()
        self.people = []
        self.orgs = []

    def collect_people(self):
        scanner = PersonScanner()
        for i, d in enumerate(self.documents):
            doc_people = scanner.scan(d)
            for full_name in doc_people.keys():
                print(full_name)
                addme = True
                try:
                    idx = [p.name for p in self.people].index(full_name)
                    if idx:
                        person = self.people[idx]
                        addme = False
                except ValueError:
                    person = Person(full_name)
                    person.wikidata = scanner.lookup_person(full_name)
                person.aka_include(sorted(set(doc_people[full_name])))
                # person.merge_info(scanner.get_person_info(full_name))
                person.appears_in.append(i)
                if addme:
                    self.people.append(person)

    def collect_orgs(self):
        for i, d in enumerate(self.documents):
            pass


    def __repr__(self):
        return "<DocumentCatalog: {}>".format(self.created_at)


class MadLib():
    
    """  """

    def __init__(self, name=None, *args, **kwargs):
        self.name = name

    def __repr__(self):
        return "<MadLib: {}>".format(self.name)


class ExquisiteCorpse():
    
    """  """

    def __init__(self, name=None, *args, **kwargs):
        self.name = name

    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.name)


  



# Functions


# Execute on module load

ag = load_or_refresh_ag(topic_list=[
                                    'Sports',
                                    'Entertainment',
                                    'Lifestyle',
                                    'Oddities',
                                    'Technology',
                                    'Business',
                                    'International News',
                                    'Politics',
                                    'Religion',
                                    ]
                        )

docs = []
for i, story in enumerate(ag.stories):
    docs.append((nlp("\n".join(story.content))))
    docs[i]._.title = story.title
    docs[i]._.byline = story.byline
    docs[i]._.timestamp = story.timestamp



