import sys
import os
import re
import random
import datetime
import time
import json
import spacy
import lemminflect
import nltk
from nltk.corpus import verbnet
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


## Classes ##

class MadLib(Munger):
    
    """  """

    def build(self):
        pass
        

    def __repr__(self):
        return "<MadLib: {}>".format(self.headline)


class ExquisiteCorpse(Munger):
    
    """  """

    def build(self):
        pass
        

    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.headline)




class Munger():

    def __init__(self, documents):
        self._headline = None
        self._documents = documents
        self._sentences = self.find_mungeable_sentences()
        self._popular_roots = sorted(
                self._sentences.keys(),
                key=lambda k: len(self._sentences[k]),
                reverse=True
                )
        self._sub_sentencess = []

    def build(self):
        
        """
        NOT IMPLEMENTED
        This method is a stub.
        
        """
        pass
    
    def munge_on_roots(self, sentence_a=None, sentence_b=None):
        if sentence_a:
            s1 = sentence_a
            if sentence_b:
                s2 = sentence_b
            else:
                s2 = self.picka_sentence(
                        lemma=s1[2],
                        exclude=[(s1[0], s1[1])]
                        )
        else:
            s1 = self.picka_sentence()
            s2 = self.picka_sentence(
                    lemma=s1[2],
                    exclude=[(s1[0], s1[1])]
                    )
    
        if s2[2] in ['say', 'be']:
            return self.munge_children([s1, s2])
    
        lefts = []
        rights = []
        root_text = "{} ".format(s2[-1].root._.inflect(s1[-1].root.tag_))
        for left in s1[-1].root.lefts:
            lefts.append("".join([t.text_with_ws for t in left.subtree]))
        for right in s2[-1].root.rights:
            rights.append("".join([t.text_with_ws for t in right.subtree]))
        return nlp(
                "{}{}{}".format("".join(lefts), root_text, "".join(rights))
                )
    
    
    def munge_sayings(self, sentence_a=None, sentence_b=None):
        return [sentence_a, sentence_b]
    
    
    def munge_beings(self, sentence_a=None, sentence_b=None):
        return [sentence_a, sentence_b]
    
    
    def munge_children(self, sentence_a=None, sentence_b=None):
        return [sentence_a, sentence_b]
    
    
    def picka_sentence(self, doc_id=None, **kwargs):
        
        """
        
        """
    
        if doc_id:
            doc_list = [doc_id]
        elif 'doc_list' in kwargs.keys():
            doc_list = kwargs['doc_list']
        elif 'focus' in kwargs.keys():
            doc_list = kwargs['focus'].appears_in
        else:
            doc_list = [n for n in range(len(self._documents))]
        if 'exclude' in kwargs.keys():
            exclude = kwargs['exclude']
        else:
            exclude = []
        if 'lemma' in kwargs.keys():
            lemma = kwargs['lemma']
            if lemma in self._popular_roots:
                s_list = list(set(self._sentences[lemma]) - set(exclude))
                if s_list:
                    random.shuffle(s_list)
                    d, s = s_list[0]
                    sent = next(islice(self._documents[d].sents, s, None))
                    return (d, s, lemma, sent)
                else:
                    # check verbnet
                    vnids = verbnet.classids(lemma)
                    alternatives = []
                    for vnid in vnids:
                        for lem in verbnet.lemmas(vnid):
                            if lem in self._popular_roots:
                                alternatives.extend(self._sentences[lem])
                    if alternatives:
                        # use these to continue
                        d, s = alternatives[random.randrange(len(alternatives))]
                        sent = next(islice(self._documents[d].sents, s, None))
                        lemma = sent.root.lemma_
                        return (d, s, lemma, sent)
                    return ()
        d = doc_list[random.randrange(len(doc_list))]
        print("d: {}".format(d))
        s_list = list(
                        set(
                            [
                            (d, s)
                            for s
                            in range(len([x for x in self._documents[d].sents]))
                            ]
                            ) - set(exclude)
                    )
        random.shuffle(s_list)
        s = s_list[0][1]
        sent = next(islice(self._documents[d].sents, s, None))
        lemma = sent.root.lemma_
        return (d, s, lemma, sent)
    
    
    def find_mungeable_sentences(self):
        # Fetch all sentence roots
        s_roots = []
        for d in self._documents:
            s_roots.extend([s.root for s in d.sents])
        # list all lemmas occurring more than once as sentence roots
        root_lemmas = find_duplicates([r.lemma_ for r in s_roots])
        # locate sentences with identical root lemmas by document and sentence index
        sentences = {k:[] for k in root_lemmas}
        for i, d in enumerate(self._documents):
            for j, s in enumerate(d.sents):
                if s.root.lemma_ in root_lemmas:
                    sentences[s.root.lemma_].append((i, j))
        return sentences
    
    
    @property
    def headline(self):
        if self._headline:
            return self._headline
        return "Headless Corpse Found in Library"
    
    
    def __repr__(self):
        return "<Munger: {}>".format(self.headline)


