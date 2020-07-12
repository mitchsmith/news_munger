#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helper functions and nltk-based NLP classes and utiities """

import os
import subprocess
import re
import datetime
import time
import json
import pickle
import nltk
try:
    from nltk.corpus import stopwords
except:
    nltk.download('stopwords')
    nltk.download('punkt') 
    from nltk.corpus import stopwords
from nltk.corpus import names
from nltk.tokenize import word_tokenize
from nltk.chunk import ChunkParserI
from nltk.chunk.util import conlltags2tree
from collections import deque


FEMININE_TITLES = (
        'Chairwoman',
        'Councilwoman',
        'Congresswoman',
        'Countess',
        'Dame',
        'Empress',
        'Lady',
        'Mrs',
        'Mrs.',
        'Miss',
        'Miss.',
        'Ms',
        'Ms.'
        'Mme',
        'Mme.',
        'Madam',
        'Madame',
        'Mother',
        'Princess',
        'Queen',
        'Sister',
      )

MASCULINE_TITLES = (
        'Archduke',
        'Ayatollah',
        'Count',
        'Emperor',
        'Father',
        'Imam',
        'King',
        'Lord', 
        'Master',
        'Mr',
        'Mr.',
        'Prince',
        'Sir',
     )

GENERIC_TITLES = (
        'Admiral',
        'Apostle',
        'Archbishop',
        'Bishop',
        'Captain',
        'Cardinal',
        'Chairman',
        'Chancellor',
        'Chef',
        'Chief',
        'Colonel',
        'Commissioner',
        'Councillor',
        'Councilman',
        'Congressman',
        'Corporal',
        'Deacon',
        'Doctor',
        'Dr.',
        'Dr',
        'Elder',
        'General',
        'Governor',
        'Gov.',
        'Gov',
        'Governor-General',
        'Justice',
        'Mahatma',
        'Major',
        'Mayor',
        'Minister',
        'Nurse',
        'Ombudsman',
        'Pastor',
        'Pharaoh',
        'Pope',
        'President',
        'Professor',
        'Prof.',
        'Prof',
        'Rabbi',
        'Reverend',
        'Representative',
        'Rep',
        'Rep.',
        'Saint',
        'Secretary',
        'Senator',
        'Sen.',
        'Sen',
        'Sergeant',
        'Sultan',
        'Swami',
    )

PRESIDENTIOSITUDE = (
        '17 Time Winner of the Q-Anonopiac Popularity Pole',
        'Adored Dispicable',
        'Beloved Orange Dumpling',
        'Chaste Keeper of American Great-Againness',
        'Chief Scientist of the United States',
        'Chosen One',
        'Delightful Fellow',
        'Elected Leader of the Free World',
        'Engorged Effigy of Himself',
        'First Citizen of the Flies',
        'Friend to the Obsequious',
        'Friend to the Downtrodden and the White',
        'Friend to Mankind',
        'God Most High',
        'God King',
        'Grand Wizard of the USA',
        'His Royal Highness',
        'Inspirer of Adoration and Dispair',
        'Jingoistic Ringleader on High',
        'Kindness and Compassion Incarnate,'
        'Lord of All Three Branches',
        'Most High King',
        'Our Overlord and Savior',
        'Paragon of Truthiness',
        'President of the United States',
        'President of the United States of America',
        'Quite High IQ Person',
        'Rex Devi Felis',
        'Right Man for the Nut Job',
        'Simply the Best President Ever',
        'Super Stable Genius',
        'The Great and Powerful',
        'The Toast of Tyrants',
        'The Suseptible but Invulnerable',
        'The Unimpeachable',
        'Unabashed Racialist',
        'Very High IQ Person Indeed',
        "Wastern Civilization's Most Impressive Puppet",
    )




class PersonChunker(ChunkParserI):
    """Named Entity Recognizer for PERSON category."""
    
    def __init__(self): 
        """ Monkey patch the defailt nltk names onject  """
        
        self.name_set = set(names.words() + ['Trump', 'Alexandria']) 
        # TODO:
        # Implement a more robut way of adding names to nltk corpus"


    def _include_titles(self, iobs):
        """Ammend PERSON entities to include personal or professional titles.
        
        ARGS:
            iobs (required) list of iob tag 3-tuples

        RETURNS:
            lest of iob tag 3-tuples
        """
        
        expansion = []
        for i, ent in enumerate(iobs):
            expansion.append(list(ent))
            if i > 0 and ent[2] == 'B-PERSON':
                if iobs[i-1][0] in set(
                        GENERIC_TITLES + FEMININE_TITLES + MASCULINE_TITLES
                        ):
                    expansion[i-1][2] = 'B-PERSON'
                    expansion[i][2] = 'I-PERSON'
        if [tuple(e) for e in expansion] != iobs:
            expansion = self._include_titles([tuple(e) for e in expansion])

        return [tuple(e) for e in expansion]


    def parse(self, tagged_sent, simple=False): 
        """Apply PERSON labels to person names in supplied pos-tagged sentence.
        
        ARGS:
            tagged_sent (required) list of pos tag tuples
            simple (default = False) set True to prevent including titles
        
        RETURNS:
            list of iob tag 3-tuples
        """  
        
        iobs = [] 
        in_person = False
        for word, tag in tagged_sent: 
            if in_person and tag == 'NNP': 
                iobs.append((word, tag, 'I-PERSON')) 
            elif word in self.name_set: 
                iobs.append((word, tag, 'B-PERSON')) 
                in_person = True
            else: 
                iobs.append((word, tag, 'O')) 
                in_person = False
        
        if simple:
            return iobs

        return self._include_titles(iobs)


    def parse_tree(self, tagged_sent, simple=False):
        """Apply PERSON labels to person names in supplied pos-tagged sentence,

        (Same as parse(), but returns sentence as an nltk Tree object)
        
        ARGS:
            tagged_sent (required) list of pos tag tuples
            simple      (default = False) set True to prevent including titles

        RETURNS:
            Tree object
        """
        
        return conlltags2tree(self.parse(tagged_sent, simple))

    def __repr__(self):
        return "<PersonChunker object - methods: {}>".format(
                "'parse', 'parse_tree'"
                )


class PersonScanner():
    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        """ Instantiate a new PersonChunker instance and declare vars"""
        
        self._chunker = PersonChunker()
        self._person_refs = []
        self._people = []
        self._document_array = []
        self._trees = []

    def scan(self, document):
        """ Tokenize text into paragraphs, sentences and pos-taged words
        
        The result is then stored in self._document_array.

        ARGS:
            document (required) minimally sturctured text
        """
        
        for para in document:
            tp = nltk.pos_tag(word_tokenize(para))
            tagged_sents = self.get_tagged_sents(tp)
            self._document_array.append(tagged_sents)
            for s in tagged_sents:
                tree = self._chunker.parse_tree(s)
                self._trees.append(tree)
        for tree in self._trees:
            name_tags = [
                         ' '.join([n[0] for n in t])
                         for t in tree.subtrees()
                         if t.label() == 'PERSON'
                        ] 
            self._person_refs.extend(name_tags)
            self._people.extend(sorted(set(
                    [n for n in name_tags if len(n.split(' ')) > 1]
                )))

    def locate_person_refs(self, person):
        """ Index and collate PERSON by location in self._document_array
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            dict of the form {'namesegmment': [(i,j,k), ...]} 
        """
        
        refs = {}
        noms = person.split(' ')
        for nom in noms:
            refs[nom] = []
            for i, p in enumerate(self._document_array):
                for j, s in enumerate(p):
                    haystack = [t[0] for t in s]
                    if nom in haystack:
                        while haystack:
                            try:
                                k = haystack.index(nom)
                                refs[nom].append((i, j, k))
                                haystack = haystack[k+1:]
                            except ValueError:
                                break
                        tree_index = sum([len(p) for p in self._document_array[:i]]) + j
                        context = [
                                   t for t in self._trees[tree_index].subtrees()
                                   if t.label() == 'PERSON'
                                   and nom in [tag[0] for tag in t]
                                  ]
                        for c in context:
                            if len(c) > len(noms):
                                aka =' '.join([tup[0] for tup in c])
                                return self.locate_person_refs(aka)
        return refs

    def get_person_info(self, person):
        """ try to determine gender, etc. from the most complete PERSON reference.
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            dict containing discoverable PERSON attributes
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

    def permute_names(self, person):
        """ Assemble possible forms of address based on available PERSON info.
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            list of variations on PERSON's name
        """

        permutations = []
        flagged = False
        refs = self.locate_person_refs(person)
        info = self.get_person_info(' '.join(refs.keys()))
        parts = [x for x in info.keys() if info[x]]
        if len(parts) == 1 and 'first' in parts:
            parts[0] = 'last'
            info['last'] = info['firt']
            info['first'] = None
            skip = 0
        if not [x for x in ['honorific', 'role'] if x in parts]:
            if info['gender'] == 'Female':
                info['honorific'] = 'Ms.'
            elif info['gender'] == 'Male':
                info['honorific'] = "Mr."
            parts.append('honorific')
        if 'first' in parts:
            permutations.append(info['first'])
            skip = 1
        else:
            skip = 0
        if 'last' in parts:
            permutations.append(info['last'])
        if 'first' in parts and 'last' in parts:
            permutations.append("{} {}".format(info['first'], info['last']))
        if 'middle' in parts:
            if len(info['middle'].split(' ')) > 1:
                # consider this suspect, but deal with it later
                flagged = True
                permutations.append(
                    "{} {} {}".format(info['first'], info['middle'], info['last'])
                    )
        end = len(permutations)
        for el in [x for x in ['honorific', 'role'] if x in parts]:
            prefixes = []
            for p in permutations[skip:end]:
                prefixes.append("{} {}".format(info[el], p))
            permutations.extend(prefixes)
        if 'suffix' in parts:
            suffixed = []
            for p in permutations:
                suffixed.append("{} {}".format(p, info['suffix']))
        return permutations


    def get_tagged_sents(self, batch):
        """Split pos_tagged paragraphs into sentences.
        
        ARGS:
            batch (required) list of pos_tags
        
        RETURNS: list of lists of pos_tags (tagged_sentences) 
        """
        
        tagged_sents = []
        try:
            sep = batch.index(('.', '.')) + 1
        except ValueError:
            batch.append(('.', '.')) 
            tagged_sents.append(batch)
            return tagged_sents

        if sep < len(batch):
            first, remnant = (batch[:sep], batch[sep:])
            tagged_sents.append(first)
            tagged_sents.extend(self.get_tagged_sents(remnant))
        else:
            tagged_sents.append(batch)
        return tagged_sents


    @property
    def person_refs(self):
        return self._person_refs

    @property
    def people(self):
        return self._people
    
    @property
    def document_array(self):
        return self._document_array
    
    @property
    def trees(self):
        return self._trees

    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._person_refs.keys()))


class Conflation():
    """Conflate News Stories """
    def __init__(self, articles, *args):
        
        """   """
        self.conflation = []
        self.scanners = []
        try:
            if type(articles) == list:
                self.articles = articles
            else:
                self.articles = [articles]
                self.articles.extend(args)
            for i, a in enumerate(self.articles):
                if type(a) == APArticle:
                    self.scanners.append(PersonScanner())
                    self.scanners[i].scan(a.content)
                else:
                    raise TypeError("Conflation requires APArticle objects")
        except Exception as err:
            print(err)
            raise



def interweave(conflation):
    """ """
    s1 = conflation.scanners[0]
    s2 = conflation.scanners[1]
    try:
        t1 = s1.trees[:[
                    re.sub(r'___*\.?', '____.', tree2text(t))
                    for t in s1.trees
                   ].index('____.')]
    except ValueError:
        t1 = s1.trees
    try:
        t2 = s2.trees[:[
                    re.sub(r'___*\.?', '____.', tree2text(t))
                    for t in s2.trees
                   ].index('____.')]
    except ValueError:
        t2 = s2.trees
    
    combined = []
    for index, tree in enumerate(
            [t for t in t1 if re.search(r'[A-Za-z]', tree2text(t))]
            ):
        print(index)
        if index % 2 == 0:
            combined.append(tree)
        else:
            combined.append(
                        list(reversed(
                            [t for t in t2 if re.search(r'[A-Za-z]', tree2text(t))]
                        ))[index])
    return combined


def tree2text(tree):
    tags = []
    pnctfix = re.compile("(\s+)([?!:;.,])")
    positions = [p for p in tree.treepositions() if p != () and len(p) == 1]
    for p in positions:
        if type(tree[p[0]]) == tuple:
            tags.append(tree[p[0]][0])
        else:
            tags.append(tree2text(tree[p[0]]))
    txt = pnctfix.sub(r"\2 ", " ".join(tags))
    return re.sub(r"\s+$", "", re.sub(r"\s+", " ", txt))


def load_conflation(ag):
    #ag = Aggregator()
    #ag.restore_headlines()
    #ag.restore_ap_topics()
    url_1 = [h for h in ag.headlines if h[0] == 'Sports'][1][1]
    a1 = APArticle(url_1)
    url_2 = [h for h in ag.headlines if h[0] == 'Sports'][1][2]
    a2 = APArticle(url_2)
    conflation = Conflation(a1, a2)
    # Most commonly referenced name in the first article:
    sorted(
            [
                conflation.scanners[0].locate_person_refs(p)
                for p 
                in conflation.scanners[0].people
            ],
            key=lambda person: sum([len(t) for t in person.values()])
          )[-1]


    return conflation   


def kill_firefox():
    process = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    output, error = process.communicate()
    for line in output.splitlines():
        if "firefox" in str(line):
            pid = int(line.split(None, 1)[0])
            os.kill(pid, 9)


def find_duplicates(mylist):
    a = sorted(mylist)
    b = sorted(set(mylist))
    d = []
    if len(a) <= len(b):
        return d
    for i, c in enumerate(a):
        if c != b[i]:
            d.append(c)
            if len(a[i+1:]) > len(b[i+1:]):
                d.extend(find_duplicates(a[i+1:]))
            break  
    return sorted(set(d))




if __name__ == "__main__":
    """ run unit tests  """
    # import unittest
    # from tests import TestPersonChunker
    # from tests import TestPersonScanner
    # unittest.main()

    # conflation = load_conflation()
    pass

#    conflation.interweave()
#    for p in conflation.conflation:
#        for s in p:
#            print(' '.join([w[0] for w in s]))



