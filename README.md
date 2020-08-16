# news_munger
A collection of utilities for creating a madlibs-style digest of news
headlines and stories from a variety of feeds and scraped web pages.

It is a silly program, whose central purpose is to help determine whether
anything its developer learned twenty years ago as a graduate student in
Linguistics can be of any use in the field of Natural Language Processing
as it is currently practiced.

The jury is still out.

# Main Components:

**scrapers.py** 

Provides extensible web scrapers for wikipedia and a variety of news sites.
Where possible, light-weight bs4-based scrapers are preferred, but for sites
such as google and APNews.com that make heavy use javascipt to embed and
diplay text content, this module provides Selenium/gekodriver based scrapers
via the HeavyScraper base class.

**munger.py**

This module provides all of the NLP functionality using both NLTK and spaCy.
Its main components are DocumentCatalog, which collects and indexes news 
articles after performing the initial tokenization, pos-tagging, NER, and
dependency tree analysis, and the Munger, which which provides a variety of
methods for dismantling the phrasal constituents of sentences and recombining
them in hopefully amusing ways. 

**newsbreak.py**

Provides Munger subclasses MadLib and ExquisiteCorpse, as well as the cli.
As of now, only ExquisiteCorpse if operational; the cli is in progress.

## Caveat:

This program relies on a couple of dependencies, especially Selenium and
gekodriver, but also the spaCy language model that includes word vectors,
which are both large and resource intensive. While it would be fun to have
built it as a web app, creating a container for it within the limits of any
of the free-tier hosting I'm aware of doesn't seem feasable.

# Instalation

1. **Make sure Firefox is installed** - Selenium will run it headless and
in incognito mode.

2. **Install gekodriver** - Use the method appropriate to your OS. There is
also an auto-installer available via PyPi:
[https://pypi.org/project/geckodriver-autoinstaller/](https://pypi.org/project/geckodriver-autoinstaller/)

3. **Clone this repo**

4. **Install in a virtualenv with python 3.8** - Python 3.6.x will also work,
but be sure to edit the Pipfile first.

    
        cd news_munger
        pipenv install


5. **From the terminal, run newsbreak.py** - This will fetch today's headlines
and aggregate around 16 of the top stories. Be patient, this can take a while.
Once the program exits, subsequent instantiation of DocumentCatalog will load
the contents from a pickle stored in tmp/

# Usage
The newsbreak cli is not yet written. To generate an Exquisite Corpse in the
python shell, import everything from newsbreak.py, instantiate a new 
DocumentCatalog, then an ExquisiteCorpse object, then call it's build method:

    from newsbreak import *
    
    catalog = DocumentCatalog()
    corpse = ExquisiteCorpse(catalog.documents)
    corpse.build()



# Help
The docstrings should be fairly complete and accurate at this point.


CLASSES
    munger.Munger(builtins.object)
        ExquisiteCorpse
        MadLib
    
    class ExquisiteCorpse(munger.Munger)
     |  ExquisiteCorpse(documents)
     |  
     |  A fake news article composed of sentence fragments gleaned from the day's
     |  headlines, in the style of surrealist party game 'Exquisite Corpse'.
     |  See: https://en.wikipedia.org/wiki/Exquisite_corpse
     |  
     |  Method resolution order:
     |      ExquisiteCorpse
     |      munger.Munger
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, documents)
     |      Declare headline, document, sentence and sub_sentences attrbutes;
     |      generate a list of repeated sentence roots
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  build(self)
     |      Munge news stories to create an esquisite cadavre.
     |  
     |  save(self)
     |      Write the cadavre to a file.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from munger.Munger:
     |  
     |  balance_quotes(self, sentence)
     |      Ballance double quotes using spaCy token attributes
     |  
     |  extract_quoted(self, sentence)
     |      Extract quoted elements and return a list of sentence tuples
     |  
     |  fetch_subtrees(self, lemma)
     |      Create a dict of left and right hand children for a given root.
     |  
     |  find_mungeable_sentences(self)
     |      Fetch all sentence roots and their doc and sent indexes
     |  
     |  munge_beings(self, sentence, sentence_b=None)
     |      TODO: Need to further investgate how to disambiguate and handle
     |      copular, existential and auxilliary uses and agreement. With luck,
     |      I'll also gain insights on how to deal with modals.
     |  
     |  munge_children(self, sentence, *args, **kwargs)
     |      Sequentially replace subtree of each child of root
     |  
     |  munge_on_roots(self, sentence_a=None, sentence_b=None)
     |      Join left hand side of sentence a with the right hand side of senence b,
     |      or with a randomly chosen sentence with a similar root lemma.
     |  
     |  munge_sayings(self, sentence_a, sentence_b=None)
     |      Munge 'say' sentence by swapping quotiations or by munging children
     |  
     |  picka_sentence(self, doc_id=None, **kwargs)
     |      Choose a compatible sentence, or a random one.
     |  
     |  swap_quotes(self, sentence)
     |      Insert randomly root-munged sentences in place of quotations
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties inherited from munger.Munger:
     |  
     |  headline
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from munger.Munger:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class MadLib(munger.Munger)
     |  MadLib(documents)
     |  
     |  Method resolution order:
     |      MadLib
     |      munger.Munger
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  build(self)
     |      NOT IMPLEMENTED
     |      This method is a stub.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from munger.Munger:
     |  
     |  __init__(self, documents)
     |      Declare headline, document, sentence and sub_sentences attrbutes;
     |      generate a list of repeated sentence roots
     |  
     |  balance_quotes(self, sentence)
     |      Ballance double quotes using spaCy token attributes
     |  
     |  extract_quoted(self, sentence)
     |      Extract quoted elements and return a list of sentence tuples
     |  
     |  fetch_subtrees(self, lemma)
     |      Create a dict of left and right hand children for a given root.
     |  
     |  find_mungeable_sentences(self)
     |      Fetch all sentence roots and their doc and sent indexes
     |  
     |  munge_beings(self, sentence, sentence_b=None)
     |      TODO: Need to further investgate how to disambiguate and handle
     |      copular, existential and auxilliary uses and agreement. With luck,
     |      I'll also gain insights on how to deal with modals.
     |  
     |  munge_children(self, sentence, *args, **kwargs)
     |      Sequentially replace subtree of each child of root
     |  
     |  munge_on_roots(self, sentence_a=None, sentence_b=None)
     |      Join left hand side of sentence a with the right hand side of senence b,
     |      or with a randomly chosen sentence with a similar root lemma.
     |  
     |  munge_sayings(self, sentence_a, sentence_b=None)
     |      Munge 'say' sentence by swapping quotiations or by munging children
     |  
     |  picka_sentence(self, doc_id=None, **kwargs)
     |      Choose a compatible sentence, or a random one.
     |  
     |  swap_quotes(self, sentence)
     |      Insert randomly root-munged sentences in place of quotations
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties inherited from munger.Munger:
     |  
     |  headline
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from munger.Munger:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

DATA
    nlp = <spacy.lang.en.English object>
    parser = ArgumentParser(prog='bpython', usage=None, descr...atter'>, c...

FILE
    /home/john/Projects/python_projects/news_munger/newsbreak.py

