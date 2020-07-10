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
from scrapersI import WikiPerson, WikiOrg, WikiGPE
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
        self._aka = [name]
        self._dates = []
        self._born = None
        self._died = None
        self._info = None
        self._wikidata = None

    def aka_include(self, alias_list):
        aka = self._aka.extend(alias_list)

        self._aka = sorted(
                set(self._aka),
                key=lambda n: len(n.split(" ")),
                reverse = True
            )
    
    def lookup(self):
        
        """Retrieve and parse available person info from wikipedia """

        wikiperson = WikiPerson(self.name)
        if wikiperson.found:
            try:
                self._bio = nlp(wikiperson.bio.text)
                paren_pat = [{"ORTH": '('}, {"ORTH": {"!": ')'}, "OP": '+'}, {"ORTH": ')'}]
                paren_matcher = Matcher(nlp.vocab)
                paren_matcher.add('Parenthetical', None, paren_pat)
                try:
                    mid, lp, rp = paren_matcher(self._bio)[0]
                    dates = [
                            d for d in self._bio.ents
                            if d.label_ == "DATE"
                            and d[0].i > lp
                            and d[-1].i < rp
                            ]
                    self._born = dates[0].orth_
                    if len(dates) >1:
                        self._died = dates[-1]
                    for date in dates:
                        m = [t.orth_ for t in date if t.is_alpha]
                        d = [t.orth_ for t in date if t.is_digit and len(t.orth_) <= 2]
                        y = [t.orth_ for t in date if t.is_digit and len(t.orth_) == 4]
                        ds = []
                        df = []
                        if d:
                            ds.append(d[0])
                            df.append("%d")
                        if m:
                            ds.append(m[0])
                            df.append("%B")
                        ds.append(y[0])
                        df.append("%Y")
                        self._dates.append(
                                datetime.datetime.strptime(
                                    " ".join(ds),
                                    " ".join(df)
                                    )
                            )
                except IndexError:
                    pass
                self.aka_include([
                    p.orth_ for p in self._bio.ents
                    if p.label_ == "PERSON"
                    #and p[-1].i < rp
                    # TODO: fix or otherwise deal with spacy tokenizer bug:
                    #       eg. lookup("Brett Veach")
                    ])
                self._wikidata = wikiperson
            except AttributeError:
                pass
        
        return self._wikidata

    def merge_info(info):
        self._info = info

    @property
    def aka(self):
        return self._aka

    @property
    def dates(self):
        return (self._dates)

    @property
    def born(self):
        return self._born

    @property
    def died(self):
        return self._died

    @property
    def age(self):
        if self._dates and self.died:
            return int((self._dates[-1] - self._dates[0]).days // 365.25)
        elif self._dates:
            return int((datetime.datetime.now() - self._dates[0]).days // 365.25)

    @property
    def info(self):
        return self._info

    @property
    def wikidata(self):
        return self._wikidata
    
    def __repr__(self):
        return "<Person: {}>".format(self.name)


class Organization():
    
    """  """

    def __init__(self, name=None, *args, **kwargs):
        self.determiner = False
        if re.search(r'^[Tt]he', name):
            self.determiner = True
        self.name = re.sub(r'[Tt]he\s+', '', name)
        self.canonical_name = None
        self.abbr = None
        self.appears_in = []
        self._aka = []
        self._info = None
        self._wikidata = None

    def lookup(self):

        """Retrieve and parse available organization info from wikipedia """

        wikiorg = WikiOrg(self.name)
        if wikiorg.found:
            self._wikidata = wikiorg
            self.canonical_name = self._wikidata.canonical_name
            try:
                self._description = nlp(self._wikidata.description.text)
                self.abbr = self._wikidata.abbr
                paren_pat = [{"ORTH": '('}, {"ORTH": {"!": ')'}, "OP": '+'}, {"ORTH": ')'}]
                paren_matcher = Matcher(nlp.vocab)
                paren_matcher.add('Parenthetical', None, paren_pat)
                try:
                    mid, lp, rp = paren_matcher(self._description)[0]
                    if lp and not self.abbr:
                        if re.search(r'^[A-Z\.]+]$', self._description[lp:rp].orth_):
                            self.abbr = self._description[lp:rp].orth_
                    elif lp and rp and not re.search(r'^/', self._description[lp:rp].orth_):
                        self.aka_include([self._description[lp+1:rp -1].orth_])
                except IndexError:
                    pass
                
            except AttributeError:
                pass
 
            if self.abbr:
                self.aka_include([self.abbr])
                
            self.aka_include([
                    self._wikidata.canonical_name,
                    self._wikidata.name,
                ])
       
        return self._wikidata

    def aka_include(self, alias_list):
        aka = self._aka.extend(alias_list)
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
        if type(value) == WikiOrg:
            self._wikidata = value


    def __repr__(self):
        return "<Organization: {}>".format(self.name)


class GeoPoliticalEntity():
    
    """  """
    
    def __init__(self, name=None, *args, **kwargs):
        self.determiner = False
        if re.search(r'^[Tt]he', name):
            self.determiner = True
        self.name = re.sub(r'[Tt]he\s+', '', name)
        self.canonical_name = None
        self.isa = None
        self.abbrs = []
        self.appears_in = []
        self._aka = []
        self._info = None
        self._wikidata = None

    def lookup(self):

        """Retrieve and parse available GPE info from wikipedia """

        wikigpe = WikiGPE(self.name)
        if wikigpe.found:
            self._wikidata = wikigpe
            self.canonical_name = self._wikidata.canonical_name
            description_text = re.sub(
                        r'\[\d+\]',
                        '',
                        self._wikidata.description.text
                        )
            self._description = nlp(description_text)
            isa_pattern = [
                        {"LEMMA": "be"},
                        {"POS": "DET"},
                        {"POS": {"IN": ['NOUN', 'ADJ', 'PREP']}, "OP": '*'},
                        {"POS": 'NOUN'}
                        ]
            isa_matcher = Matcher(nlp.vocab)
            isa_matcher.add('ISA', None, isa_pattern)
            try:
                mid, start, end = isa_matcher(self._description)[0]
                self.isa = self._description[start+2:end].lower_
            except IndexError:
                pass
            for text in self._wikidata.bold:
                if re.search(r'^[A-Z\.]+$', text):
                    self.abbrs.append(text)
                else:
                    self.aka_include([text])
                
            if self._wikidata.abbr:
                self.abbrs.append(self._wikidata.abbr)

            self.abbrs = sorted(
                        set(self.abbrs),
                        key = lambda a: len(a),
                        reverse = True
                        )
 
            if self.abbrs:
                self.aka_include([self.abbrs])
                
            self.aka_include([
                    self._wikidata.canonical_name,
                    self._wikidata.name,
                ])
       
        return self._wikidata

    def aka_include(self, alias_list):
        aka = self._aka.extend(alias_list)
        self._aka = sorted(
                set(self._aka),
                key=lambda n: len(n.split(" ")),
                reverse = True
            )

    def __repr__(self):
        return "<GeoPoliticalEntity: {}>".format(self.name)


class Scanner():

    """ """
    
    def __init__(self):
        self._document = None
        self._entity_type = None

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

    @property
    def document(self):
        return self._document

    def __repr__(self):
        return "<Scanner {}>".format(" ".join(self._entities.keys()))




class PersonScanner(Scanner):

    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        super().__init__()
        self._entity_type = "PERSON"
        self._people = []

    def scan(self, document):
        super().scan(document)
        
        for entity in self._entities.keys():
            person = Person(entity)
            try:
                person.lookup()
            except:
                pass
            self._people.append(person)


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
    def people(self):
        return self._people
    
    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._entities.keys()))


class OrgScanner(Scanner):
    
    """ """

    def __init__(self):
        super().__init__()
        self._entity_type = "ORG"
        self._orgs = []

    def scan(self, document):
        super().scan(document)
        
        for entity in self._entities.keys():
            org = Organization(entity)
            try:
                org.lookup()
            except:
                pass
            self._orgs.append(org)

    @property
    def orgs(self):
        return self._orgs
 
    def __repr__(self):
        return "<OrgScanner {}>".format(" ".join(self._entities.keys()))
    

class GPEScanner(Scanner):
    
    """ """

    def __init__(self):
        super().__init__()
        self._entity_type = "GPE"
        self._gpes = []

    def scan(self, document):
        super().scan(document)
        
        for entity in self._entities.keys():
            gpe = GeoPoliticalEntity(entity)
            try:
                gpe.lookup()
            except:
                pass
            self._gpes.append(gpe)

    @property
    def gpes(self):
        return self._gpes
 
    def __repr__(self):
        return "<GPEScanner {}>".format(" ".join(self._entities.keys()))


class DocumentCatalog():
    
    """  """

    def __init__(self, document_list, *args, **kwargs):
        if type(document_list) != list:
            raise TypeError
        self.documents = document_list
        self.created_at = datetime.datetime.now().isoformat()
        self.people = []
        self.orgs = []
        self.gpes = []

    def collect_people(self):
        scanner = PersonScanner()
        for i, d in enumerate(self.documents):
            scanner.scan(d)
            doc_people = scanner._entities
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
                    person.lookup()
                person.aka_include(sorted(set(doc_people[full_name])))
                # person.merge_info(scanner.get_person_info(full_name))
                person.appears_in.append(i)
                if addme:
                    self.people.append(person)

    def collect_orgs(self):
        scanner = OrgScanner()
        for i, d in enumerate(self.documents):
            scanner.scan(d)
            doc_orgs = scanner._entities
            for org_name in doc_orgs.keys():
                addme = True
                try:
                    idx = [o.name for o in self.orgs].index(org_name)
                    if idx:
                        org = self.orgs[idx]
                        addme = False
                except ValueError:
                    org = Organization(org_name)
                    org.wikidata = WikiOrg(org_name)
                org.aka_include(sorted(set(doc_orgs[org_name])))
                org.appears_in.append(i)
                if addme and org.wikidata.found:
                    self.orgs.append(org)

    def collect_gpes(self):
        scanner = GPEScanner()
        for i, d in enumerate(self.documents):
            scanner.scan(d)
            doc_gpes = scanner._entities
            for gpe_name in doc_gpes.keys():
                addme = True
                try:
                    idx = [o.name for o in self.gpes].index(gpe_name)
                    if idx:
                        gpe = self.gpes[idx]
                        addme = False
                except ValueError:
                    gpe = GeoPoliticalEntity(gpe_name)
                    gpe.wikidata = WikiGPE(gpe_name)
                gpe.aka_include(sorted(set(doc_gpes[gpe_name])))
                gpe.appears_in.append(i)
                if addme and gpe.wikidata.found:
                    self.gpes.append(gpe)



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



