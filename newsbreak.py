#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
parser = argparse.ArgumentParser()
parser.parse_args()

import os
import re
import datetime
import munger
from munger import Aggregator, DocumentCatalog, Munger, load_or_refresh_ag, nlp



## Classes ##


class MadLib(Munger):
    
    """  """

    def build(self):
        pass
        

    def __repr__(self):
        return "<MadLib: {}>".format(self.headline)


class ExquisiteCorpse(Munger):
    
    """
    A fake news article composed of sentence fragments gleaned from the day's
    headlines, in the style of surrealist party game 'Exquisite Corpse'.
    See: https://en.wikipedia.org/wiki/Exquisite_corpse
    
    """

    def __init__(self, documents):
        super().__init__(documents)
        self.corpses = []

    def build(self):
        """Munge news stories to create an esquisite cadavre. """
        text = ""
        base_index = random.randrange(len(self._documents))
        base = self._documents[base_index]
        sentences = []
        for i, s in enumerate(base.sents):
            stuple = (base_index, i, s.root.lemma_, s)
            if stuple[2] == 'say':
                sentence = self.munge_sayings(stuple)
            elif stuple[2] in ['be', 'do', 'have']:
                sentence = self.munge_children(stuple)
            else:
                sentence = self.munge_on_roots(stuple)
                
            sentences.append(sentence)

        self.corpses.append({'title': base._.title, 'sentences': sentences}) 

        text += "\n".join([sent[-1].text_with_ws for sent in sentences])
        print(text)

    def save(self):
        
        """ Write the cadavre to a file. """

        self.filename = datetime.datetime.today().strftime("tmp/exq_%Y%m%d.txt")
        pass




       
    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.headline)





if __name__ == "__main__":
    
    """   
    
    """

    catalog = DocumentCatalog()

    # Unit Tests #

    """
    """


