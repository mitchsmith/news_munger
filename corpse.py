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



