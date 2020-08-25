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
import string
import pickle
from collections import deque
from itertools import islice
import spacy
from nltk.corpus import names, verbnet
from spacy.tokens import Doc
from spacy.matcher import Matcher
from scrapers import Aggregator
from scrapers import WikiPerson, WikiOrg, WikiGPE
from helpers import find_duplicates, irreg_inflect
from helpers import GENERIC_TITLES, FEMININE_TITLES, MASCULINE_TITLES

print("\nLoading spaCy English vocabulary with medium word vectors . . .")
nlp = spacy.load("en_core_web_md")
print("Done.\n")


# Classes


class Munger:

    """
    Base class for MadLib, ExquisiteCorpse, or other fake news generators.
    """

    def __init__(self, documents):

        """
        Declare headline, document, sentence and sub_sentences attrbutes;
        generate a list of repeated sentence roots
        """

        self._headline = None
        self._documents = documents
        self._sentences = self.find_mungeable_sentences()
        self._sub_sentencess = []
        self._popular_roots = sorted(
            self._sentences.keys(), key=lambda k: len(self._sentences[k]), reverse=True
        )

    def build(self):

        """
        NOT IMPLEMENTED
        This method is a stub.

        """

    def fetch_subtrees(self, lemma):

        """Create a dict of left and right hand children for a given root. """

        # pylint: disable=invalid-name
        # Will change when refactoring

        subtrees = {"left": dict(), "right": dict()}
        alternatives = []
        if lemma not in self._sentences.keys():
            # check verbnet
            vnids = verbnet.classids(lemma)
            alternatives = []
            for vnid in vnids:
                for lem in verbnet.lemmas(vnid):
                    if lem in self._popular_roots:
                        alternatives.append(lem)
            if not alternatives:
                alternatives = self._popular_roots

            token1 = nlp(lemma)
            tokens = nlp(" ".join(alternatives))
            lemma = sorted(
                [(t.lemma_, t.similarity(token1)) for t in tokens],
                key=lambda n: n[1],
                reverse=True,
            )[0][0]

        for i, j in self._sentences[lemma]:
            s = next(islice(self._documents[i].sents, j, None))
            for left in s.root.lefts:
                k = left.dep_
                if k in subtrees["left"].keys():
                    subtrees["left"][k].append((i, j, [t for t in left.subtree]))
                elif k != "punct":
                    subtrees["left"][k] = [(i, j, [t for t in left.subtree])]
            for right in s.root.rights:
                k = right.dep_
                if k in subtrees["right"].keys():
                    subtrees["right"][k].append((i, j, [t for t in right.subtree]))
                elif k != "punct":
                    subtrees["right"][k] = [(i, j, [t for t in right.subtree])]

        return subtrees

    def munge_on_roots(self, sentence_a=None, sentence_b=None):

        """
        Join left hand side of sentence a with the right hand side of senence b,
        or with a randomly chosen sentence with a similar root lemma.
        """

        # pylint: disable=invalid-name
        # Will change when refactoring

        if sentence_a:
            s1 = sentence_a
            if sentence_b:
                s2 = sentence_b
            else:
                s2 = self.picka_sentence(lemma=s1[2], exclude=[(s1[0], s1[1])])
        else:
            s1 = self.picka_sentence()
            s2 = self.picka_sentence(lemma=s1[2], exclude=[(s1[0], s1[1])])

        for s in [s1, s2]:
            if s[-1].root.lemma_ == "say" or [t for t in s[3] if t.is_quote]:
                return self.munge_on_roots()

        lefts = []
        rights = []
        root_text = "{} ".format(s2[-1].root._.inflect(s1[-1].root.tag_))
        for left in s1[-1].root.lefts:
            lefts.append("".join([t.text_with_ws for t in left.subtree]))
        for right in s2[-1].root.rights:
            rights.append(
                "".join(
                    [
                        t.text_with_ws
                        if t.dep_ != "conj"
                        else re.sub(
                            r"\S+", t._.inflect(s1[-1].root.tag_), t.text_with_ws
                        )
                        for t in right.subtree
                    ]
                )
            )
            # 10, 27; 0, 14

        munged = next(
            islice(
                nlp("{}{}{}".format("".join(lefts), root_text, "".join(rights))).sents,
                0,
                None,
            )
        )
        return (None, None, munged.root.lemma_, munged)

    def extract_quoted(self, sentence):

        """
        Extract quoted elements and return a list of sentence tuples
        """

        # pylint: disable=invalid-name
        # Will change when refactoring

        s = sentence[-1]
        hasq = deque([t for t in s if t.orth_ in ["“", "”"]])
        if len(hasq) % 2:
            sent = balance_quotes(sentence)
            return self.extract_quoted(sent)
        parts = []
        while hasq:
            lq = hasq.popleft()
            rq = hasq.popleft()
            start = lq.i - s.start + 1
            end = rq.i - s.start
            part = "".join([t.text_with_ws for t in s[start:end]])
            parts.append(part)

        text = re.sub(r"\s+", " ", " ".join(parts))
        sub_sents = [(None, None, ss.root.lemma_, ss) for ss in nlp(text).sents]

        return sub_sents

    def swap_quotes(self, sentence):

        """Insert randomly root-munged sentences in place of quotations """

        # pylint: disable=invalid-name
        # Will change when refactoring

        s = sentence
        hasq = deque([t for t in s[-1] if t.orth_ in ["“", "”"]])
        swaps = None
        if hasq:
            if len(hasq) % 2:
                s = balance_quotes(s)
                return self.swap_quotes(s)
            sub_sents = self.extract_quoted(s)
            swaps = []
            for ss in sub_sents:
                swaps.append(self.munge_on_roots(ss))
            text = ""
            ri = -1
            while hasq:
                left = hasq.popleft()
                right = hasq.popleft()
                li = left.i - s[-1].start + 1
                ri = right.i - s[-1].start
                parts = []
                if len(hasq) == 0:
                    for swap in swaps:
                        parts.extend(ss.text_with_ws for ss in swap[-1])
                    repl = re.sub(r"[\s\n]+", " ", " ".join(parts), flags=re.MULTILINE)
                elif len(swaps) == len(hasq) / 2:
                    repl = re.sub(
                        r"\n", "", swaps[0][-1].text_with_ws, flags=re.MULTILINE
                    )
                    del swaps[0]
                else:
                    try:
                        # pylint: disable=bare-except
                        # Too many ways this can break to list them all
                        spl = [
                            t.i - swaps[0].start for t in swaps[0] if t.orth_ == ","
                        ][0]
                        repl, swaps[0] = swaps[0][:spl], swaps[0][spl:]
                    except:
                        repl = "Just kidding,"

                text += "".join([t.text_with_ws for t in s[-1]][:li])
                text += repl

            text += "".join([t.text_with_ws for t in s[-1]][ri:])

            new_sent = next(islice(nlp(text).sents))[0]
            sentence = (None, None, new_sent.root.lemma_, new_sent)

        return sentence

    def munge_sayings(self, sentence_a, sentence_b=None):

        """
        Munge 'say' sentence by swapping quotiations or by munging children
        """

        # pylint: disable=invalid-name
        # Will change when refactoring

        sentences = [sentence_a, sentence_b]
        for s in sentences:
            if s:
                hasq = deque([t for t in s[-1] if t.orth_ in ["“", "”"]])
                if hasq:
                    if len(hasq) % 2:
                        s = balance_quotes(s)
                        return self.munge_sayings(s)
                    return self.swap_quotes(s)

                return self.munge_children(s)

        return sentences[0]

    def munge_beings(self, sentence):

        """
        TODO: Need to further investgate how to disambiguate and handle
        copular, existential and auxilliary uses and agreement. With luck,
        I'll also gain insights on how to deal with modals.
        """

        return sentence

    def munge_children(self, sentence, *args, **kwargs):

        """Sequentially replace subtree of each child of root """

        # pylint: disable=invalid-name
        # Will change when refactoring

        s = sentence[-1]
        lemma = s.root.lemma_
        workon = ["left", "right"]
        deps = []
        infl_tag = s.root.tag_
        infl_cntx = s

        if "left" in args:
            del workon[1]
        elif "right" in args:
            del workon[0]

        if "deps" in kwargs.keys():
            deps = kwargs["deps"]

        subtrees = self.fetch_subtrees(lemma)
        elements = []
        cursor = 0

        for hand in workon:
            if deps:
                keys = deps
            else:
                keys = subtrees[hand].keys()

            if hand == "left":
                nodes = s.root.lefts
            else:
                nodes = s.root.rights
                cursor = s.root.i - s.start + 1

            for child in (c for c in nodes if c.dep_ in keys and c.dep != "punct"):
                tree = [t for t in child.subtree]
                li = tree[0].i - s.start
                ri = tree[-1].i - s.start
                elements.extend([t.text_with_ws for t in s][cursor:li])
                choices = [
                    stree
                    for stree in subtrees[hand][child.dep_]
                    if stree[0] != sentence[0] or stree[1] != sentence[1]
                ]
                try:
                    r = random.choice(choices)
                    if child.dep_ == "nsubj":
                        infl_cntx = next(
                            islice(self._documents[r[0]].sents, r[1], None)
                        )
                        infl_tag = infl_cntx.root.tag_

                    elements.extend([t.text_with_ws for t in r[-1]])
                    cursor = ri + 1
                except IndexError:
                    pass

            if hand == "left":
                # TOTO: move this to it's own method after figuring out 'be'
                elements.append(s.root.text_with_ws)
                if s.root.lemma_ in ["be", "do", "have", "say"]:
                    t = 0  # present
                    n = 0  # singular
                    p = 2  # 3rd person

                    subj = [c for c in infl_cntx.root.lefts if c.dep_ == "nsubj"]
                    if subj:
                        if subj[0].tag_ in ["NNS", "NNPS"]:
                            n = 1
                        elif subj[0].tag_ == "PRP":
                            if subj[0].lower_ == "you":
                                p = 1
                            if subj[0].lower_ == "i":
                                p = 0
                            if subj[0].lower_ == "we":
                                p = 0
                                n = 1

                        if "conj" in [c.dep_ for c in subj[0].subtree]:
                            n = 1

                    if infl_tag == "VBG":
                        repl = s.root._.inflect("VBG")
                    else:
                        if infl_tag == "VBD":
                            t = 1
                        repl = irreg_inflect(s.root.lemma_, [t, n, p])

                    re.sub(r"{}".format(s.root.orth_), repl, elements[-1])
                else:
                    re.sub(
                        r"{}".format(s.root.orth_),
                        s.root._.inflect(infl_tag),
                        elements[-1],
                    )

                cursor += 1

        elements.extend(t.text_with_ws for t in s[cursor:])

        return sent_from_wordlist(elements)

    def picka_sentence(self, doc_id=None, **kwargs):

        """
        Choose a compatible sentence, or a random one.
        """

        if doc_id:
            doc_list = [doc_id]
        elif "doc_list" in kwargs.keys():
            doc_list = kwargs["doc_list"]
        elif "focus" in kwargs.keys():
            doc_list = kwargs["focus"].appears_in
        else:
            doc_list = [n for n in range(len(self._documents))]
        if "exclude" in kwargs.keys():
            exclude = kwargs["exclude"]
        else:
            exclude = []
        if "lemma" in kwargs.keys():
            lemma = kwargs["lemma"]
            if lemma in self._popular_roots:
                s_list = list(set(self._sentences[lemma]) - set(exclude))
                if s_list:
                    random.shuffle(s_list)
                    d_index, s_index = s_list[0]
                    sent = next(islice(self._documents[d_index].sents, s_index, None))
                    return (d_index, s_index, lemma, sent)
                # check verbnet
                vnids = verbnet.classids(lemma)
                alternatives = []
                for vnid in vnids:
                    for lem in verbnet.lemmas(vnid):
                        if lem in self._popular_roots:
                            alternatives.extend(self._sentences[lem])
                if alternatives:
                    # use these to continue
                    d_index, s_index = alternatives[random.randrange(len(alternatives))]
                    sent = next(islice(self._documents[d_index].sents, s_index, None))
                    lemma = sent.root.lemma_

                    return (d_index, s_index, lemma, sent)

                return ()

        d_index = doc_list[random.randrange(len(doc_list))]
        print("d: {}".format(d_index))
        s_list = list(
            set(
                [
                    (d_index, s)
                    for s in range(len([x for x in self._documents[d_index].sents]))
                ]
            )
            - set(exclude)
        )
        random.shuffle(s_list)
        s_index = s_list[0][1]
        sent = next(islice(self._documents[d_index].sents, s_index, None))
        lemma = sent.root.lemma_

        return (d_index, s_index, lemma, sent)

    def find_mungeable_sentences(self):

        """ Fetch all sentence roots and their doc and sent indexes """

        s_roots = []
        for doc in self._documents:
            s_roots.extend([s.root for s in doc.sents])
        # list all lemmas occurring more than once as sentence roots
        root_lemmas = find_duplicates([r.lemma_ for r in s_roots])
        # locate sentences with identical root lemmas by document and sentence index
        sentences = {k: [] for k in root_lemmas}
        for i, doc in enumerate(self._documents):
            for j, sent in enumerate(doc.sents):
                if sent.root.lemma_ in root_lemmas:
                    sentences[sent.root.lemma_].append((i, j))
        return sentences

    @property
    def headline(self):

        """ Headline """

        if self._headline:
            return self._headline
        return "Headless Corpse Found in Library"

    def __repr__(self):
        return "<Munger: {}>".format(self.headline)


class Person:

    """A person as identified in spacy doc ents """

    def __init__(self, name=None):
        self.name = name
        self.appears_in = []
        self.bio = None
        self._aka = [name]
        self._dates = []
        self._born = None
        self._died = None
        self._info = None
        self._wikidata = None

    def aka_include(self, alias_list):

        """Include uniqe name varients in the list of aliases """

        aka = self._aka.extend(alias_list)

        self._aka = sorted(set(aka), key=lambda n: len(n.split(" ")), reverse=True)

    def lookup(self):

        """Retrieve and parse available person info from wikipedia """

        wikiperson = WikiPerson(self.name)
        if wikiperson.found:
            try:
                self.bio = nlp(wikiperson.bio.text)
                paren_pat = [
                    {"ORTH": "("},
                    {"ORTH": {"!": ")"}, "OP": "+"},
                    {"ORTH": ")"},
                ]
                paren_matcher = Matcher(nlp.vocab)
                paren_matcher.add("Parenthetical", None, paren_pat)
                try:
                    mid, lpn, rpn = paren_matcher(self.bio)[0]
                    dates = [
                        d
                        for d in self.bio.ents
                        if d.label_ == "DATE" and d[0].i > lpn and d[-1].i < rpn
                    ]
                    self._born = dates[0].orth_
                    if len(dates) > 1:
                        self._died = dates[-1]
                    for date in dates:
                        month = [t.orth_ for t in date if t.is_alpha]
                        day = [
                            t.orth_ for t in date if t.is_digit and len(t.orth_) <= 2
                        ]
                        year = [
                            t.orth_ for t in date if t.is_digit and len(t.orth_) == 4
                        ]
                        dstr = []
                        dfrm = []
                        if day:
                            dstr.append(day[0])
                            dfrm.append("%d")
                        if month:
                            dstr.append(month[0])
                            dfrm.append("%B")
                        dstr.append(year[0])
                        dfrm.append("%Y")
                        self._dates.append(
                            datetime.datetime.strptime(" ".join(dstr), " ".join(dfrm))
                        )
                    del mid
                except IndexError:
                    pass
                self.aka_include(
                    [
                        p.orth_
                        for p in self._bio.ents
                        if p.label_ == "PERSON"
                        # and p[-1].i < rp
                        # TODO: fix or otherwise deal with spacy tokenizer bug:
                        #       eg. lookup("Brett Veach")
                    ]
                )
                self._wikidata = wikiperson
            except AttributeError:
                pass

        return self._wikidata

    def merge_info(self, info):

        """Normalize and include additional info (Not yet implemented) """

        self._info = info

    @property
    def aka(self):

        """ Alternate names (ordered by length) """

        return self._aka

    @property
    def dates(self):

        """ Dates text """

        return self._dates

    @property
    def born(self):

        """ Birth date """
        return self._born

    @property
    def died(self):

        """ Death date """

        return self._died

    @property
    def age(self):

        """ Calculated age """

        if self._dates and self.died:
            return int((self._dates[-1] - self._dates[0]).days // 365.25)
        if self._dates:
            return int((datetime.datetime.now() - self._dates[0]).days // 365.25)

        return None

    @property
    def info(self):

        """ spacy and nltk interpolated data """

        return self._info

    @property
    def wikidata(self):

        """ WikiPerson instance """

        return self._wikidata

    def __repr__(self):
        return "<Person: {}>".format(self.name)


class Organization:

    """An organization as identified in spacy doc ents """

    def __init__(self, name=None):
        self.determiner = False
        if re.search(r"^[Tt]he", name):
            self.determiner = True
        self.name = re.sub(r"[Tt]he\s+", "", name)
        self.canonical_name = None
        self.abbr = None
        self.appears_in = []
        self._aka = []
        self._info = None
        self._wikidata = None
        self._description = None

    def lookup(self):

        """Retrieve and parse available organization info from wikipedia """

        wikiorg = WikiOrg(self.name)
        if wikiorg.found:
            self._wikidata = wikiorg
            self.canonical_name = self._wikidata.canonical_name
            try:
                self._description = nlp(self._wikidata.description.text)
                self.abbr = self._wikidata.abbr
                paren_pat = [
                    {"ORTH": "("},
                    {"ORTH": {"!": ")"}, "OP": "+"},
                    {"ORTH": ")"},
                ]
                paren_matcher = Matcher(nlp.vocab)
                paren_matcher.add("Parenthetical", None, paren_pat)
                try:
                    mid, lpn, rpn = paren_matcher(self._description)[0]
                    if lpn and not self.abbr:
                        if re.search(r"^[A-Z\.]+]$", self._description[lpn:rpn].orth_):
                            self.abbr = self._description[lpn:rpn].orth_
                    elif (
                        lpn
                        and rpn
                        and not re.search(r"^/", self._description[lpn:rpn].orth_)
                    ):
                        self.aka_include([self._description[lpn + 1 : rpn - 1].orth_])
                        del mid
                except IndexError:
                    pass

            except AttributeError:
                pass

            if self.abbr:
                self.aka_include([self.abbr])

            self.aka_include(
                [self._wikidata.canonical_name, self._wikidata.name,]
            )

        return self._wikidata

    def aka_include(self, alias_list):

        """ Extend aka list """

        aka = self._aka.extend(alias_list)
        self._aka = sorted(set(aka), key=lambda n: len(n.split(" ")), reverse=True)

    def merge_info(self, info):

        """ Incorporate new interpolated info (not implemented) """

        self._info = info

    @property
    def aka(self):

        """ Alternate designations """

        return self._aka

    @property
    def info(self):

        """ spacy and nltk interpolations """

        return self._info

    @property
    def wikidata(self):

        """ WikiOrg instance """

        return self._wikidata

    @wikidata.setter
    def wikidata(self, value):
        if isinstance(value) == WikiOrg:
            self._wikidata = value

    def __repr__(self):
        return "<Organization: {}>".format(self.name)


class GeoPoliticalEntity:

    """An geopolitical entity as identified in spacy doc ents """

    def __init__(self, name=None):
        self.determiner = False
        if re.search(r"^[Tt]he", name):
            self.determiner = True
        self.name = re.sub(r"[Tt]he\s+", "", name)
        self.canonical_name = None
        self.isa = None
        self.abbrs = []
        self.appears_in = []
        self._aka = []
        self._info = None
        self._wikidata = None
        self._description = None

    def lookup(self):

        """Retrieve and parse available GPE info from wikipedia """

        wikigpe = WikiGPE(self.name)
        if wikigpe.found:
            self._wikidata = wikigpe
            self.canonical_name = self._wikidata.canonical_name
            description_text = re.sub(r"\[\d+\]", "", self._wikidata.description.text)
            self._description = nlp(description_text)
            isa_pattern = [
                {"LEMMA": "be"},
                {"POS": "DET"},
                {"POS": {"IN": ["NOUN", "ADJ", "PREP"]}, "OP": "*"},
                {"POS": "NOUN"},
            ]
            isa_matcher = Matcher(nlp.vocab)
            isa_matcher.add("ISA", None, isa_pattern)
            try:
                mid, start, end = isa_matcher(self._description)[0]
                self.isa = self._description[start + 2 : end].lower_
                del mid
            except IndexError:
                pass
            for text in self._wikidata.bold:
                if re.search(r"^[A-Z\.]+$", text):
                    self.abbrs.append(text)
                else:
                    self.aka_include([text])

            if self._wikidata.abbr:
                self.abbrs.append(self._wikidata.abbr)

            self.abbrs = sorted(set(self.abbrs), key=len, reverse=True)

            if self.abbrs:
                self.aka_include([self.abbrs])

            self.aka_include(
                [self._wikidata.canonical_name, self._wikidata.name,]
            )

        return self._wikidata

    def aka_include(self, alias_list):

        """List of unique aliases (longest form first) """

        aka = self._aka.extend(alias_list)
        self._aka = sorted(set(aka), key=lambda n: len(n.split(" ")), reverse=True)

    @property
    def wikidata(self):

        """ WikiGPE instance """

        return self._wikidata

    @wikidata.setter
    def wikidata(self, value):
        if isinstance(value) == WikiGPE:
            self._wikidata = value

    def __repr__(self):
        return "<GeoPoliticalEntity: {}>".format(self.name)


class Scanner:

    """Base Class for named entity document scanner """

    def __init__(self):
        self._document = None
        self._entity_type = None
        self._entities = {}

    def scan(self, document):

        """ Locate entities of a given entity type

        ARGS:
            document (required) str or spacy.Doc instance

        RETURNS: A dict of all variants of each entity's name, with
            the longest form of each name as key.
        """

        if isinstance(document) != Doc:
            if isinstance(document) == str:
                self._document = nlp(document)
            else:
                raise TypeError("Scanner.scan requires str or Doc")
        else:
            self._document = document

        for alt_name in sorted(
            [
                ent.text.split(" ")
                for ent in self._document.ents
                if ent.label_ == self._entity_type
            ],
            key=len,
            reverse=True,
        ):
            if " ".join(alt_name) not in self._entities.keys():
                found = False
                print("{} not in self._entities.keys.".format(" ".join(alt_name)))
                for key, entity in self._entities.items():
                    if re.search(" ".join(alt_name), key):
                        print("re match in name keys")
                        entity.append(" ".join(alt_name))
                        found = True
                        break
            if not found:
                entity = [" ".join(alt_name)]

        if self._entity_type == "PERSON":
            self._document._.people = self._entities

        return self._entities

    @property
    def document(self):

        """The scanned document """

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

        # pylint: disable=consider-iterating-dictionary
        # We only need the key in this case
        for entity in self._entities.keys():
            person = Person(entity)
            try:
                person.lookup()
            except TypeError:
                pass
            self._people.append(person)

    @property
    def entities(self):
        """ Return the entities dict as people """
        return self._entities

    @property
    def people(self):
        """ Return the list of people """
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

        """Locate ORG entities and instantiate Org objects """

        super().scan(document)

        # pylint: disable=consider-iterating-dictionary
        # We only need the key to instaniate the Org object
        for entity in self._entities.keys():
            org = Organization(entity)
            try:
                org.lookup()
            except TypeError:
                pass
            self._orgs.append(org)

    @property
    def entities(self):
        """ Return the dict of org entities """
        return self._entities

    @property
    def orgs(self):
        """ Return the list of orgs """
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

        # pylint: disable=consider-iterating-dictionary
        # We only need the key in this case
        for entity in self._entities.keys():
            gpe = GeoPoliticalEntity(entity)
            try:
                gpe.lookup()
            except TypeError:
                pass
            self._gpes.append(gpe)

    @property
    def entities(self):
        """ Return the dict of gpe entities """
        return self._entities

    @property
    def gpes(self):
        """ Return the list of gpes """
        return self._gpes

    def __repr__(self):
        return "<GPEScanner {}>".format(" ".join(self._entities.keys()))


class DocumentCatalog:

    """Collections of named Entities extracted from across muntiple docs """

    def __init__(self):

        """Collect documents and related named entity info """

        try:
            Doc.set_extension("title", default=None)
            Doc.set_extension("byline", default=None)
            Doc.set_extension("timestamp", default=None)
            Doc.set_extension("dateline", default=None)
            Doc.set_extension("people", default=None)
        except ValueError:
            # Reloading pickled
            pass

        self.aggregator = load_or_refresh_ag()
        self.created_at = datetime.datetime.now().isoformat()
        self.documents = []
        self.people = []
        self.orgs = []
        self.gpes = []

        dateline_pattern = re.compile(r"^([A-Z][A-Z ,][^—]*?— )", flags=re.MULTILINE)

        for i, story in enumerate(self.aggregator.stories):
            text = story.content["text"]
            dateline = None
            # pylint disable=bare-except
            # Need to ignore ALL errors, even if not BaseException
            try:
                dateline = dateline_pattern.search(text)[0]
            except:
                pass

            self.documents.append(
                strip_bottoms([(nlp(dateline_pattern.sub("", text)))])[0]
            )

            self.documents[i]._.title = story.title
            self.documents[i]._.byline = story.byline
            self.documents[i]._.dateline = dateline
            self.documents[i]._.timestamp = story.timestamp


    def collect_people(self):

        """Collect list of Person objects """

        scanner = PersonScanner()
        for i, doc in enumerate(self.documents):
            scanner.scan(doc)
            doc_people = scanner.entities
            for key, alt_names in doc_people.items():
                addme = True
                try:
                    idx = [p.name for p in self.people].index(key)
                    if idx:
                        person = self.people[idx]
                        addme = False
                except ValueError:
                    person = Person(key)
                    person.lookup()
                person.aka_include(sorted(set(alt_names)))
                person.appears_in.append(i)
                if addme:
                    self.people.append(person)

    def collect_orgs(self):

        """Collect list of Organization objects """

        scanner = OrgScanner()
        for i, doc in enumerate(self.documents):
            scanner.scan(doc)
            doc_orgs = scanner.entities
            for key, alt_ames in doc_orgs.items():
                addme = True
                try:
                    idx = [o.name for o in self.orgs].index(key)
                    if idx:
                        org = self.orgs[idx]
                        addme = False
                except ValueError:
                    org = Organization(key)
                    org.wikidata = WikiOrg(key)
                org.aka_include(sorted(set(alt_ames)))
                org.appears_in.append(i)
                if addme and org.wikidata.found:
                    self.orgs.append(org)

    def collect_gpes(self):

        """Collect list of Organization objects """

        scanner = GPEScanner()
        for i, doc in enumerate(self.documents):
            scanner.scan(doc)
            doc_gpes = scanner.entities
            for key, alt_names in doc_gpes.items():
                addme = True
                try:
                    idx = [o.name for o in self.gpes].index(key)
                    if idx:
                        gpe = self.gpes[idx]
                        addme = False
                except ValueError:
                    gpe = GeoPoliticalEntity(key)
                    gpe.wikidata = WikiGPE(key)
                gpe.aka_include(sorted(set(alt_names)))
                gpe.appears_in.append(i)
                if addme and gpe.wikidata.found:
                    self.gpes.append(gpe)

    def __repr__(self):
        return "<DocumentCatalog: {}>".format(self.created_at)


# Functions


def balance_quotes(sentence):

    """Ballance double quotes using spaCy token attributes """

    # pylint: disable=invalid-name
    # Will change when refactoring

    sent = sentence[-1]
    hasq = [t for t in sent if t.orth_ in ["“", "”"]]
    text = ""
    center = sent.root.i - sent.start
    lefts = [t.i - sent.start for t in hasq if t.i - sent.start < center]
    elements = [t.text_with_ws for t in sent]
    if len(lefts) % 2:
        if lefts[0] != 0:
            text += "“"
            fixcaps = re.sub(
                r"^\W+(\w+)", r"\1", "".join(elements[: center + 1])
            ).split(" ")
            fixcaps[0] = string.capwords((fixcaps[0]))
            text += " ".join(fixcaps)
        else:
            ri = [
                t.i - sent.start
                for t in sent
                if t.i < sent.root.i and t.dep_ == "punct"
            ][-1] + 1
            text += "".join(elements[:ri])
            text += "”"
            text += "".join(elements[ri : center + 1])
    else:
        text += "".join(elements[: center + 1])

    text += "".join([e for e in elements[center + 1 :] if e not in ["“", "”"]])

    s = next(islice(nlp(text).sents, 0, None))

    return (None, None, s.root.lemma_, s)


def get_person_info(person):

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
    tokens = deque([p for p in person.split(" ") if re.search(r"\w+", p)])
    if tokens[-1] in MASCULINE_TITLES:
        honorific = tokens.popleft()
        gender = "Male"
    elif tokens[-1] in FEMININE_TITLES:
        honorific = tokens.popleft()
        gender = "Female"
    if tokens[-1] in GENERIC_TITLES:
        role = tokens.popleft()
    elif re.match(r"\w\w+\.", tokens[-1]):
        role = tokens.popleft()
    # At this point, element -1 should be either the first name or initial.
    if tokens[-1] in names.words("female.txt"):
        if not gender:
            gender = "Female"
    if tokens[-1] in names.words("male.txt"):
        if not gender:
            gender = "Male"
        elif not honorific:
            gender = "Unknown"
    first = tokens.popleft()
    try:
        # Check for suffix: 'Esq.', 'Jr.'. 'Sr. etc.
        if re.match(r".+\.|Junior|Senior|[IVX]+$", tokens[-2]):
            suffix = tokens.pop()
    except IndexError:
        pass
    else:
        if tokens:
            last = tokens.pop()
        if tokens:
            middle = " ".join(tokens)
    if honorific and not last:
        last = first
        first = None

    return {
        "gender": gender,
        "honorific": honorific,
        "role": role,
        "first": first,
        "middle": middle,
        "last": last,
        "suffix": suffix,
    }


def sent_from_wordlist(elements):

    """ Convert a list of word_texts to a spacy sentence """

    text = " ".join(elements)
    text = re.sub(r"[\n\s]+", " ", text)
    text = re.sub(r"\s+([,\.\!\?])", r"\1", text)
    sent = next(islice(nlp(text).sents, 0, None))

    return (None, None, sent.root.lemma_, sent)


def strip_bottoms(documents):

    """Remove article byline and ads from the article body """

    stripped = []

    for doc in documents:

        try:
            end = [s.root.i for s in doc.sents if s.root.orth_ == "_"][0] - 2
        except IndexError:
            end = -1
        stripped.append(doc[:end].as_doc())
        stripped[-1]._.title = doc._.title
        stripped[-1]._.byline = doc._.byline
        stripped[-1]._.timestamp = doc._.timestamp
        stripped[-1]._.dateline = doc._.dateline
        stripped[-1]._.people = doc._.people

    return stripped


def traverse(node):

    """ Return a depth-first parse tree for a given node """

    if node.n_lefts + node.n_rights > 0:
        return [(node.i, node), [traverse(child) for child in node.children]]

    return (node.i, node)


def load_or_refresh_ag(topic_list=None):

    """Scrape today's news or reload id from the pickle. """

    if topic_list:
        topics = topic_list
    else:
        topics = [
            "Sports",
            "Politics",
            "Entertainment",
            "Lifestyle",
            "Oddities",
            "Travel",
            "Technology",
            "Business",
            "U.S. News",
            "International News",
            "Politics",
            "Religion",
        ]

    cached = datetime.datetime.today().strftime("tmp/ag_%Y%m%d.pkl")
    # cached = "./tmp/ag_20200808.pkl"
    if os.path.isfile(cached):
        with open(cached, "rb") as pkl:
            agg = pickle.load(pkl)
    else:
        agg = Aggregator()
        agg.collect_ap_headlines()
        # agg.restore_headlines()

        for topic in topics:
            failed = 0
            stopat = len(agg.stories) + 2
            for url in [h[1] for h in agg.headlines if h[0] == topic]:
                try:
                    # pylint: disable=broad-except
                    # Article fetching is error prone; skip it and try another
                    agg.fetch_ap_article(url)
                except Exception as err:
                    print(f"Skipping article:\n{err}")
                    time.sleep(3)
                    failed += 1
                    if failed < 4:
                        continue
                    break
                if len(agg.stories) >= stopat:
                    break

        with open(cached, "wb") as pkl:
            pickle.dump(agg, pkl)

    return agg
