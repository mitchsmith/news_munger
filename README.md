# news_munger
A collection of utilities for creating a madlibs-style digest of news headlines and stories from a variety of feeds and scraped web pages.


NAME
    munger

DESCRIPTION
    This module provides a collection of utilities for creating a madlibs-
    style digest of news headlines and stories from a variety of feeds and 
    scraped web pages.

CCLLAASSSSEESS
    munger.Munger(builtins.object)
        ExquisiteCorpse
        MadLib
    
    class EExxqquuiissiitteeCCoorrppssee(munger.Munger)
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
     |  ____iinniitt____(self, documents)
     |      Declare headline, document, sentence and sub_sentences attrbutes;
     |      generate a list of repeated sentence roots
     |  
     |  ____rreepprr____(self)
     |      Return repr(self).
     |  
     |  bbuuiilldd(self)
     |      Munge news stories to create an esquisite cadavre.
     |  
     |  ssaavvee(self)
     |      Write the cadavre to a file.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from munger.Munger:
     |  
     |  bbaallaannccee__qquuootteess(self, sentence)
     |      Ballance double quotes using spaCy token attributes
     |  
     |  eexxttrraacctt__qquuootteedd(self, sentence)
     |      Extract quoted elements and return a list of sentence tuples
     |  
     |  ffeettcchh__ssuubbttrreeeess(self, lemma)
     |      Create a dict of left and right hand children for a given root.
     |  
     |  ffiinndd__mmuunnggeeaabbllee__sseenntteenncceess(self)
     |      Fetch all sentence roots and their doc and sent indexes
     |  
     |  mmuunnggee__bbeeiinnggss(self, sentence, sentence_b=None)
     |      TODO: Need to further investgate how to disambiguate and handle
     |      copular, existential and auxilliary uses and agreement. With luck,
     |      I'll also gain insights on how to deal with modals.
     |  
     |  mmuunnggee__cchhiillddrreenn(self, sentence, *args, **kwargs)
     |      Sequentially replace subtree of each child of root
     |  
     |  mmuunnggee__oonn__rroooottss(self, sentence_a=None, sentence_b=None)
     |      Join left hand side of sentence a with the right hand side of senence b,
     |      or with a randomly chosen sentence with a similar root lemma.
     |  
     |  mmuunnggee__ssaayyiinnggss(self, sentence_a, sentence_b=None)
     |      Munge 'say' sentence by swapping quotiations or by munging children
     |  
     |  ppiicckkaa__sseenntteennccee(self, doc_id=None, **kwargs)
     |      Choose a compatible sentence, or a random one.
     |  
     |  sswwaapp__qquuootteess(self, sentence)
     |      Insert randomly root-munged sentences in place of quotations
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties inherited from munger.Munger:
     |  
     |  hheeaaddlliinnee
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from munger.Munger:
     |  
     |  ____ddiicctt____
     |      dictionary for instance variables (if defined)
     |  
     |  ____wweeaakkrreeff____
     |      list of weak references to the object (if defined)
    
    class MMaaddLLiibb(munger.Munger)
     |  MadLib(documents)
     |  
     |  Method resolution order:
     |      MadLib
     |      munger.Munger
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  ____rreepprr____(self)
     |      Return repr(self).
     |  
     |  bbuuiilldd(self)
     |      NOT IMPLEMENTED
     |      This method is a stub.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from munger.Munger:
     |  
     |  ____iinniitt____(self, documents)
     |      Declare headline, document, sentence and sub_sentences attrbutes;
     |      generate a list of repeated sentence roots
     |  
     |  bbaallaannccee__qquuootteess(self, sentence)
     |      Ballance double quotes using spaCy token attributes
     |  
     |  eexxttrraacctt__qquuootteedd(self, sentence)
     |      Extract quoted elements and return a list of sentence tuples
     |  
     |  ffeettcchh__ssuubbttrreeeess(self, lemma)
     |      Create a dict of left and right hand children for a given root.
     |  
     |  ffiinndd__mmuunnggeeaabbllee__sseenntteenncceess(self)
     |      Fetch all sentence roots and their doc and sent indexes
     |  
     |  mmuunnggee__bbeeiinnggss(self, sentence, sentence_b=None)
     |      TODO: Need to further investgate how to disambiguate and handle
     |      copular, existential and auxilliary uses and agreement. With luck,
     |      I'll also gain insights on how to deal with modals.
     |  
     |  mmuunnggee__cchhiillddrreenn(self, sentence, *args, **kwargs)
     |      Sequentially replace subtree of each child of root
     |  
     |  mmuunnggee__oonn__rroooottss(self, sentence_a=None, sentence_b=None)
     |      Join left hand side of sentence a with the right hand side of senence b,
     |      or with a randomly chosen sentence with a similar root lemma.
     |  
     |  mmuunnggee__ssaayyiinnggss(self, sentence_a, sentence_b=None)
     |      Munge 'say' sentence by swapping quotiations or by munging children
     |  
     |  ppiicckkaa__sseenntteennccee(self, doc_id=None, **kwargs)
     |      Choose a compatible sentence, or a random one.
     |  
     |  sswwaapp__qquuootteess(self, sentence)
     |      Insert randomly root-munged sentences in place of quotations
     |  
     |  ----------------------------------------------------------------------
     |  Readonly properties inherited from munger.Munger:
     |  
     |  hheeaaddlliinnee
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from munger.Munger:
     |  
     |  ____ddiicctt____
     |      dictionary for instance variables (if defined)
     |  
     |  ____wweeaakkrreeff____
     |      list of weak references to the object (if defined)

DDAATTAA
    nnllpp = <spacy.lang.en.English object>
    ppaarrsseerr = ArgumentParser(prog='bpython', usage=None, descr...atter'>, c...

FFIILLEE
    /home/john/Projects/python_projects/news_munger/newsbreak.py

