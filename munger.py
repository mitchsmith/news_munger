#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This module provides a collection of utilities for creating a madlibs-
style digest of news headlines and stories from a variety of feeds and 
scraped web pages.
"""

import os
import re
import random
import datetime
import time
import json
import pickle
import spacy
import lemminflect
from spacy.lang.en import English
from spacy.tokens import Doc, Span, Token
from spacy.matcher import Matcher
from collections import deque
from itertools import islice
from scrapers import Trends, Aggregator, APHeadlines, APArticle
from scrapers import WikiPerson, WikiOrg, WikiGPE
from helpers import find_duplicates, kill_firefox
from helpers import GENERIC_TITLES, FEMININE_TITLES, MASCULINE_TITLES, PRESIDENTIOSITUDE
from gtts import  list_voices, text_to_mp3

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
    
    """A person as identified in spacy doc ents """
    
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

        """Include uniqe name varients in the list of aliases """

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

        """Normalize and include additional info (Not yet implemented) """

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
    
    """An organization as identified in spacy doc ents """

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
    
    """An geopolitical entity as identified in spacy doc ents """
    
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

    """Base Class for named entity document scanner """
    
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

    """Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        super().__init__()
        self._entity_type = "PERSON"
        self._people = []

    def scan(self, document):

        """Locate PERSON entities and instantiate Person objects """

        super().scan(document)
        
        for entity in self._entities.keys():
            person = Person(entity)
            try:
                person.lookup()
            except:
                pass
            self._people.append(person)


    def get_person_info(self, person):
        
        """Try to determine gender, etc. from the most complete PERSON reference.
        
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
    
    """Location, labeling, and collation of named ORG entities """

    def __init__(self):
        super().__init__()
        self._entity_type = "ORG"
        self._orgs = []

    def scan(self, document):

        """Locate ORG entities and instantiate Person objects """

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
    
    """Location, labeling, and collation of named GPE entities """

    def __init__(self):
        super().__init__()
        self._entity_type = "GPE"
        self._gpes = []

    def scan(self, document):

        """Locate GPE entities and instantiate Person objects  """

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
    
    """Collections of named Entities extracted from across muntiple docs """

    def __init__(self, document_list, *args, **kwargs):
        if type(document_list) != list:
            raise TypeError
        self.documents = document_list
        self.created_at = datetime.datetime.now().isoformat()
        self.people = []
        self.orgs = []
        self.gpes = []
        self.subj_np_forms = {}
        self.np_complement_forms = {}

    def collect_people(self):

        """Collect list of Person objects """

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
 
        """Collect list of Organization objects """

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
        
        """Collect list of Organization objects """
        
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

    
    def collect_subj_np_forms(self):
        
        """ """
        
        for i, d in enumerate(self.documents):
            for j, sent in enumerate([s for s in d.sents]):
                idx = [t.orth_ for t in sent].index(sent.root.orth_)
                try:
                    self.subj_np_forms[
                            "-".join([t.dep_ for t in sent[:idx]])
                            ].append((sent.root, i, j, idx))
                except KeyError:
                    self.subj_np_forms[
                            "-".join([t.dep_ for t in sent[:idx]])
                            ] = [(sent.root, i, j, idx)]



    def collect_np_complement_forms(self):
        
        """ """
        
        for i, d in enumerate(self.documents):
            for j, sent in enumerate([s for s in d.sents]):
                idx = [t.orth_ for t in sent].index(sent.root.orth_) + 1
                try:
                    self.np_complement_forms[
                            "-".join([t.dep_ for t in sent[idx:]])
                            ].append((sent.root, i, j, idx))
                except KeyError:
                    self.np_complement_forms[
                            "-".join([t.dep_ for t in sent[idx:]])
                            ] = [(sent.root, i, j, idx)]



    def similar_subj_nps(self, common_form):
        
        """ """

        subjects = {}
        if common_form in self.common_subj_forms:
            for tup in [
                            t for t
                            in self.subj_np_forms[common_form]
                            if t[0].pos_ == "VERB"
                        ]:
                doc = self.documents[tup[1]]
                subjects[tup] = [snt for snt in doc.sents][tup[2]][:tup[3]]
        return subjects


    def similar_np_complements(self, common_form):
        
        """ """

        complements = {}
        if common_form in self.common_complement_forms:
            for tup in [
                            t for t
                            in self.np_complement_forms[common_form]
                            if t[0].pos_ == "VERB"
                        ]:
                doc = self.documents[tup[1]]
                complements[tup] = [snt for snt in doc.sents][tup[2]][:tup[3]]
        return complements
 

    @property
    def common_subj_forms(self):
        return [
                k for k
                in self.subj_np_forms.keys()
                if len(self.subj_np_forms[k]) > 1
               ]

    @property
    def common_complement_forms(self):
        return [
                k for k
                in self.np_complement_forms.keys()
                if len(self.np_complement_forms[k]) > 1
               ]
        
    
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
        self.title = None
        self.sentences =[]
        self.fragments = []

        if "docs" in kwargs.keys():
            pass
        elif not catalog.people:
            catalog.collect_people()

        self.focus = sorted(
                catalog.people,
                key=lambda p: len(p.appears_in),
                reverse=True
                )[0]
        print(self.focus)


    def choose_next_sentence(self, frag):
        pass
    
    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.name)




"""
for i, d in enumerate(catalog.documents):
    for j, s in enumerate(d.sents):
        if s.root.lemma_ == "say":
            idx = [t.orth_ for t in s].index(s.root.orth_) + 1
            print("... {} {}".format(s.root, s[idx+1:]))


for f in catalog.common_subj_forms:
    subs = []
    preds = []
    for tup in catalog.similar_subj_nps(f):
        print("{} {}".format([s for s in catalog.documents[tup[1]].sents][0][:tup[3],tup[0]))


        subs.append((tup[0], [s for s in catalog.documents[tup[1]].sents][0][:tup[3]]))
        preds.append((tup[0], [s for s in catalog.documents[tup[1]].sents][0][tup[3]+1:]))
    # print(sorted(set(subs)))
    # print(sorted(set(preds)))
    for s in sorted(set(subs)):
        for p in sorted(set(preds)):
            print ("{} {} {}".format(s[1], s[0].orth_, p[1]))
        print("...")


swapable = catalog.similar_subj_nps(catalog.common_subj_forms[1])
sents = []
for k in swapable.keys():
    sent = [s for s in catalog.documents[k[1]].sents][k[2]]
    sents.append((k, sent))

for i, s in enumerate(swapable):
    for j in range(1,len(sents)):
        sent = sents[(i + j) % len(sents)]
        pred = sents[i][1][:s[3]+1]
        comp = sent[1][sent[0][3]+1:]
        print(" ".join([pred.text, comp.text]))
        pred = sents[i][1][:s[3]]
        comp = sent[1][sent[0][3]:]
        print(" ".join([pred.text, comp.text]))




"""



# Functions

def sents_from_common_form(common_form):
    swapable = catalog.similar_subj_nps(common_form)
    sents = []
    for k in swapable.keys():
        sent = [s for s in catalog.documents[k[1]].sents][k[2]]
        sents.append((k, sent))
    new_sents = []
    for i, s in enumerate(swapable):
        for j in range(1,len(sents)):
            sent = sents[(i + j) % len(sents)]
            pred = sents[i][1][:s[3]+1]
            comp = sent[1][sent[0][3]+1:]
            new_sents.append(" ".join([pred.text, comp.text]))
            if len(sents) > 2:
                pred = sents[i][1][:s[3]]
                comp = sent[1][sent[0][3]:]
                new_sents.append(" ".join([pred.text, comp.text]))
    
    return new_sents




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

    """ Swap subjects with direct objects
    
    TODO: Rewrite this spaCily
    """
    if type(document) == Doc:
        doc = document
    elif type(document) == Span:
        doc = document.as_doc()
    elif type(document) == str:
        doc = nlp(document)
    else:
        raise TypeError("The document must be of type str, Doc, or Span.")

    for s in doc.sents:
        new_text = ""
        # find the noun chunks
        nplist = [n for n in s.noun_chunks]
        
        # find the subject
        nsubj = [n for n in nplist if n.root.dep_ =='nsubj']
        if nsubj:
            nsubj = nsubj[0]
        # find the subject's direct object
        dobj = [
                n for n in nplist
                if n.root.dep_ =='dobj'
                and n.root.head == nsubj.root.head
               ]
        if dobj:
            dobj = dobj[0]
        # get sentence text
        text = s.orth_
        # replacement string for new subject
        replacement_s = ''.join(
                [t.text_with_ws for t in dobj if t.dep_ not in ['poss', 'det']]
                )
        print("s {}".format(replacement_s))
        # replacement string for new D.O.
        replacement_o = ''.join(
                [t.text_with_ws for t in nsubj if t.dep_ not in ['poss', 'det']]
                )
        print("o {}".format(replacement_o))
        # temp replacement (shape of original subject)
        tmp_replace = replacement_o
        tmp_replace = ''.join([re.sub(
                 t.orth_, t.shape_, tmp_replace
               ) for t in nsubj if t.dep_ not in ['poss', 'det']])
        print("temp {}".format(tmp_replace))
        # replace orig subj with tmp_replace
        text = re.sub(replacement_o, tmp_replace, text)
        # replace orig D.O. with new subj
        text = re.sub(replacement_s, replacement_o, text)
        # replace tmp subj with new subj
        text = re.sub(tmp_replace, replacement_s, text)

        new_text += text
    return new_text


def strip_bottoms(documents):

    """  """
    stripped = []

    for i, d in enumerate(documents):
        try:
            end = [s.root.i for s in d.sents if s.root.orth_ == "_"][0] -2
        except IndexError:
            end = -1
        stripped.append(d[:end].as_doc())

    return stripped


def swap_main_verbs(doc1, doc2):
    
    """ """
    docs = strip_bottoms([doc1, doc2])
    verb_sets = []
    new_texts = ["", ""]
    for d in docs:
        verb_sets.append(
                        set([
                            s.root.lemma_
                            for s 
                            in d.sents 
                            if s.root.pos_ == "VERB"
                        ])
                    )

    for i, d in enumerate(docs):
        patterns = list(verb_sets[i] - verb_sets[(i + 1) % 2])
        replacements = list(verb_sets[(i + 1) % 2] - verb_sets[i])
        for s in d.sents:
            if s.root.lemma_ in patterns:
                t = s.text_with_ws
                p = s.root.orth_
                r = [
                    x.root._.inflect(s.root.tag_)
                    for x
                    in docs[(i + 1) % 2].sents
                    if x.root.lemma_ == replacements[
                        patterns.index(s.root.lemma_) % len(replacements)
                        ]
                    ][0]
                text = re.sub(p, r, t)
                new_texts[i % 2] += text
            else:
                new_texts[i % 2] += s.text_with_ws
    
    

    return new_texts


def swap_sent_ents(ent_label, *args):

    """ """

    stripped = strip_bottoms(args)
    ent_sets = []
    munged_texts = []

    for d in stripped:
        span_texts = ["".join([
                                t.text_with_ws
                                for t
                                in e
                                if t.dep_ != "det"
                              ]
                             )
                        for e
                        in d.ents
                        if e.label_ == ent_label
                     ]
        ent_sets.append(list(set(span_texts) - {'AP', 'Associated Press'}))
    
    for i, d in enumerate(stripped):
        munged_sents = []
        for j, s in enumerate(d.sents):
            text = s.text_with_ws
            text = re.sub(r"^[A-Z]+ +\(AP\) — ", "", text)
            ents = [e for e in s.ents if e.label_ == ent_label]
            if len(ents) > 0:
                for k, pattern in enumerate(ent_sets[i]):
                    replacement = ent_sets[(i + 1) % 2][k % len(ent_sets[(i + 1) % 2])]
                    replacement = re.sub(" ?$", " ", replacement)
                    text = re.sub(pattern, replacement, text)
                
                munged_sents.append((j, text))

        munged = "".join([s[1] for s in sorted(munged_sents, key=lambda s: s[0])])
        munged = re.sub(r" +"," ", munged)
        munged = re.sub(r" (\W|$)", "", munged)
        munged_texts.append(munged)
    
    return munged_texts


def swap_ents(ent_label, *args):

    """ """

    stripped = strip_bottoms(args)
    ent_sets = []
    new_texts = []
    
    for d in stripped:
        s = ["".join([
                      t.text_with_ws
                      for t
                      in e
                      ]
                      # if t.dep_ != "det"]
                    )
                    for e
                    in d.ents
                    if e.label_ == ent_label
            ]
        ent_sets.append(list(set(s) - {'AP', 'Associated Press'}))

    for i, d in enumerate(stripped):
        text = d.text_with_ws
        replacements = set()
        
        for j, s in enumerate(ent_sets):
            if j != i:
                replacements = replacements.union(set(s))

        for j, pattern in enumerate(ent_sets[i]):
            text = re.sub(
                    pattern,
                    "{} ".format(
                        list(replacements)[j % len(replacements)]
                        ),
                    text
                    )
        new_texts.append(text)
    
    return new_texts


def collect_verbs(documents):

    """Create lists of unique verbs in documents arranged by valence.  """

    allverbs = []
    for doc in documents:
        allverbs.extend(
                    sorted(
                        set(
                            [
                                (v.lemma_, len(
                                    [
                                        t.dep_
                                        for t
                                        in v.children
                                        if t.dep_
                                        in ['nsubj','dobj','xcomp', 'prep']
                                    ]
                                )
                            )
                            for v
                            in doc
                            if v.pos_ == "VERB"
                            and v.is_alpha
                            ]
                           ), key=lambda tup: tup[1]
                         )
                      )
    verbs = [[],[],[]]
    
    for v in set(allverbs):
         try:
             verbs[v[1]].append(nlp(v[0])[0])
         except IndexError:
             verbs[2].append(nlp(v[0])[0])
    return verbs


def collect_verb_lemmas(documents):
    
    """Create single list of unique verb lemmas  """
    
    lemmas = []
    for doc in documents:
        lemmas.extend(
                        [
                            v.lemma_
                            for v
                            in doc
                            if v.pos_ == "VERB"
                            and v.is_alpha
                        ]
                    )
    return [nlp(v)[0] for v in sorted(set(lemmas))]



def scramble_verbs(documents, ranked_verbs=None):

    """   """

    new_texts = []

    if ranked_verbs:
        bags = ranked_verbs
    else:
        bags = collect_verbs(documents)
    
    for i, doc in enumerate(strip_bottoms(documents)):
        new_texts.append(doc.text_with_ws)

        for token in doc:
            if token.pos_ == "VERB" and token.is_alpha:
            #    valence = len([
            #                    t.dep_
            #                    for t
            #                    in token.children
            #                    if t.dep_
            #                    in ['nsubj','dobj','xcomp', 'prep']
            #                  ])
            #    if valence > 2:
            #        valence = 2
                p = token.orth_
                r = [
                        v._.inflect(token.tag_)
                        for v
                        in sorted(
                                    [
                                        tok
                                        for tok
                                        # in bags[valence]
                                        in bags
                                        if tok.lemma_ != token.lemma_
                                    ],
                                    key=lambda s: s.similarity(token)
                                 )
                    ][-3]

                if token.is_title:
                    r = r.title()
                
                new_texts[i] = re.sub(p, r, new_texts[i])
    
    return new_texts


def scramble_verbs_II(documents):
    
    """ """
    
    stripped = strip_bottoms(documents)
    verbs = collect_verb_lemmas(stripped)
    texts = []
    for i, d in enumerate(stripped):
        doctext = []
        for s in d.sents:
            s_text = s.text_with_ws
            for t in s:
                if t.pos_ == "VERB" and t.is_alpha:
                    p = r"( |^)({})(\W|$)".format(t.orth_)
                    choices = sorted(
                                    [tok for tok in verbs if tok.lemma_ != t.lemma_],
                                    key=lambda s: s.similarity(t)
                                    )
                    rpl = choices[-1]._.inflect(t.tag_)
                    if t.is_title:
                        rpl = rpl.title()
                    s_text = re.sub(p, r"\1{}\3".format(rpl), s_text)

            doctext.append(s_text)
                    
        texts.append("".join(doctext))
    return texts

    
def traverse(node):
    if node.n_lefts + node.n_rights > 0:
        return [(node.i, node), [traverse(child) for child in node.children]]
    else:
        return (node.i, node)


def shuffle_and_merge(documents):
    
    """   """

    base = swap_ents("ORG", documents[0], documents[-1])
    munged = []
    for text in base:
        re.sub(r" +", " ", text, re.DOTALL)
        doc = nlp(text)
        munged.append(doc)
        print(len(list(doc.sents)))

    combined = [s.text_with_ws for s in munged[0].sents][:14]
    combined.extend([s.text_with_ws for s in munged[1].sents][-5:])

    return nlp("".join(combined))


def load_or_refresh_ag(topic_list=['Sports', 'Politics']):
    # cached = datetime.datetime.today().strftime("tmp/ag_%Y%m%d.pkl")
    cached = "./tmp/ag_20200710.pkl"
    if os.path.isfile(cached):
        with open(cached, "rb") as pkl:
            ag = pickle.load(pkl)
    else:
        ag = Aggregator()
        ag.collect_ap_headlines()
        
        for top in topic_list:
            failed = 0
            stopat = len(ag.stories) + 2
            for url in [h[1] for h in ag.headlines if h[0] == top]:
                try:
                    ag.fetch_ap_article(url)
                except:
                    kill_firefox()
                    time.sleep(3)
                    failed += 1
                    if failed < 4:
                        continue
                    else:
                        break
                if len(ag.stories) >= stopat:
                    break

        for story in ag.stories:
            # ditch unpicklable
            story.driver = None

        with open(cached, "wb") as pkl:
            pickle.dump(ag, pkl)
        
    return ag



# Execute on import

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
dateline_pattern = re.compile(r"^([A-Z][A-Z ,][^—]*?— )", flags=re.MULTILINE)
for i, story in enumerate(ag.stories):
    text = "\n".join(story.content)
    try:
        dateline = dateline_pattern.search(text)[0]
    except:
        pass
    docs.append((nlp(dateline_pattern.sub("", text))))
    docs[i]._.title = story.title
    docs[i]._.byline = story.byline
    docs[i]._.dateline = dateline
    docs[i]._.timestamp = story.timestamp


# Unit Tests #

if __name__ == "__main__":
    pass



