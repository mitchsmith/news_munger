#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This module provides a command line interface to news_munger. """

import datetime
import random
import argparse
from munger import DocumentCatalog, Munger

parser = argparse.ArgumentParser()
parser.parse_args()


## Classes ##


class MadLib(Munger):

    """Real soon now. """

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

        """Initialize super; and declare corpse list. """
        super().__init__(documents)
        self.corpses = []

    def build(self):
        """Munge news stories to create an esquisite cadavre. """
        text = ""
        base_index = random.randrange(len(self._documents))
        base = self._documents[base_index]
        sentences = []
        for i, sent in enumerate(base.sents):
            stuple = (base_index, i, sent.root.lemma_, sent)
            if stuple[2] == "say":
                sentence = self.munge_sayings(stuple)
            elif stuple[2] in ["be", "do", "have"]:
                sentence = self.munge_children(stuple)
            else:
                sentence = self.munge_on_roots(stuple)

            sentences.append(sentence)

        self.corpses.append({"title": base._.title, "sentences": sentences})

        text += "\n".join([sent[-1].text_with_ws for sent in sentences])
        print(text)

    def save(self, cadavre=None):

        """ Write the cadavre(s) to a file. """
        filename = datetime.datetime.today().strftime("tmp/exq_%Y%m%d.txt")
        if cadavre:
            corpses = [cadavre]
        else:
            corpses = self.corpses
        with open(filename, "a+") as file:
            for corpse in corpses:
                file.write(f"{corpse['title']}\n\n")
                for sent in corpse["sentences"]:
                    file.write(sent[-1].text_with_ws)
                file.write("\n******\n\n")

    def __repr__(self):
        return "<ExquisiteCorpse: {}>".format(self.headline)


if __name__ == "__main__":

    catalog = DocumentCatalog()

    # Unit Tests #
