# news_munger
A collection of utilities for creating a madlibs-style digest of news headlines and stories from a variety of feeds and scraped web pages.


NAME
    munger

DESCRIPTION
    This module provides a collection of utilities for creating a madlibs-
    style digest of news headlines and stories from a variety of feeds and 
    scraped web pages.

CLASSES
    builtins.object
        Aggregator
        HeavyScraper
            APArticle
            APHeadlines
            Trends
        PersonScanner
    nltk.chunk.api.ChunkParserI(nltk.parse.api.ParserI)
        PersonChunker
    
    class APArticle(HeavyScraper)
     |  AP Article contents fetched and scraped from the specified url.
     |  
     |  Method resolution order:
     |      APArticle
     |      HeavyScraper
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, url)
     |      Fetch and scrape news article and close the marionette driver.
     |      
     |      ARGS:
     |          url (required)
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  byline
     |  
     |  content
     |  
     |  timestamp
     |  
     |  title
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from HeavyScraper:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class APHeadlines(HeavyScraper)
     |  Scrape AP News Topics and optionally retrieve headlines by topic
     |  
     |  Method resolution order:
     |      APHeadlines
     |      HeavyScraper
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, topic_id=0)
     |      Fetch topics and immediatly close the marionette driver.
     |      
     |      If the topic_id arg is supplied, headlines filed under that
     |      topic are also retrieved before closing the marionette driver.
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  url = 'https://apnews.com/'
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from HeavyScraper:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class Aggregator(builtins.object)
     |  Collect News Headlines and Stories
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Delcare private vars and retrieve the topic list
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  cache_ap_topics(self)
     |      Dumps self._.topics too json file
     |  
     |  cache_headlines(self)
     |      Dumps self._headlines to json file
     |  
     |  collect_ap_headlines(self)
     |      Collects AP Headlines by topic in self._hadlines.
     |      
     |      Retruns self._headlines
     |  
     |  fetch_ap_article(self, url)
     |      Fetches a new APArticle and appends its content to stories
     |      
     |      ARGS: url
     |  
     |  refresh_ap_topics(self)
     |      Collects the list of AP News topics and caches it
     |  
     |  restore_ap_topics(self)
     |      Reads previously cached topics back into self._topics
     |  
     |  restore_headlines(self)
     |      Reads previously cached headlines back into self._headlines
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  headlines
     |  
     |  stories
     |  
     |  topics
    
    class HeavyScraper(builtins.object)
     |  A resource intensive, selemium-based Soup-Nazi countermeasure
     |  
     |  (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, url=None)
     |      ARGS: url ; DEFAULT: None
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class PersonChunker(nltk.chunk.api.ChunkParserI)
     |  Named Entity Recognizer for PERSON category.
     |  
     |  Method resolution order:
     |      PersonChunker
     |      nltk.chunk.api.ChunkParserI
     |      nltk.parse.api.ParserI
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Monkey patch the defailt nltk names onject
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  parse(self, tagged_sent, simple=False)
     |      Apply PERSON labels to person names in supplied pos-tagged sentence.
     |      
     |      ARGS:
     |          tagged_sent (required) list of pos tag tuples
     |          simple (default = False) set True to prevent including titles
     |      
     |      RETURNS:
     |          list of iob tag 3-tuples
     |  
     |  parse_tree(self, tagged_sent, simple=False)
     |      Apply PERSON labels to person names in supplied pos-tagged sentence,
     |      
     |      (Same as parse(), but returns sentence as an nltk Tree object)
     |      
     |      ARGS:
     |          tagged_sent (required) list of pos tag tuples
     |          simple      (default = False) set True to prevent including titles
     |      
     |      RETURNS:
     |          Tree object
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from nltk.chunk.api.ChunkParserI:
     |  
     |  evaluate(self, gold)
     |      Score the accuracy of the chunker against the gold standard.
     |      Remove the chunking the gold standard text, rechunk it using
     |      the chunker, and return a ``ChunkScore`` object
     |      reflecting the performance of this chunk peraser.
     |      
     |      :type gold: list(Tree)
     |      :param gold: The list of chunked sentences to score the chunker on.
     |      :rtype: ChunkScore
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from nltk.parse.api.ParserI:
     |  
     |  grammar(self)
     |      :return: The grammar used by this parser.
     |  
     |  parse_all(self, sent, *args, **kwargs)
     |      :rtype: list(Tree)
     |  
     |  parse_one(self, sent, *args, **kwargs)
     |      :rtype: Tree or None
     |  
     |  parse_sents(self, sents, *args, **kwargs)
     |      Apply ``self.parse()`` to each element of ``sents``.
     |      :rtype: iter(iter(Tree))
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from nltk.parse.api.ParserI:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
    
    class PersonScanner(builtins.object)
     |  Location, labeling, and collation of named PERSON entities
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Instantiate a new PersonChunker instance and declare vars
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  get_person_info(self, person)
     |      try to determine gender, etc. from the most complete PERSON reference.
     |      
     |      ARGS:
     |          person (required) string: all or part of the person's full name
     |      
     |      RETURNS:
     |          dict containing discoverable PERSON attributes
     |  
     |  get_tagged_sents(self, batch)
     |      Split pos_tagged paragraphs into sentences.
     |      
     |      ARGS:
     |          batch (required) list of pos_tags
     |      
     |      RETURNS: list of lists of pos_tags (tagged_sentences)
     |  
     |  locate_person_refs(self, person)
     |      Index and collate PERSON by location in self._document_array
     |      
     |      ARGS:
     |          person (required) string: all or part of the person's full name
     |      
     |      RETURNS:
     |          dict of the form {'namesegmment': [(i,j,k), ...]}
     |  
     |  permute_names(self, person)
     |      Assemble possible forms of address based on available PERSON info.
     |      
     |      ARGS:
     |          person (required) string: all or part of the person's full name
     |      
     |      RETURNS:
     |          list of variations on PERSON's name
     |  
     |  scan(self, document)
     |      Tokenize text into paragraphs, sentences and pos-taged words
     |      
     |      The result is then stored in self._document_array.
     |      
     |      ARGS:
     |          document (required) minimally sturctured text
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  document_array
     |  
     |  people
     |  
     |  person_refs
     |  
     |  trees
    
    class Trends(HeavyScraper)
     |  Top Google Search terms scraped from Google Trends
     |  
     |  Method resolution order:
     |      Trends
     |      HeavyScraper
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Fetch search terms and immediately close the marionette driver
     |  
     |  __repr__(self)
     |      Return repr(self).
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  ngrams
     |  
     |  trends
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  url = 'https://trends.google.com/trends/trendingsearches/daily?geo=US'
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from HeavyScraper:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

DATA
    FEMININE_TITLES = ('Chairwoman', 'Councilwoman', 'Congresswoman', 'Cou...
    GENERIC_TITLES = ('Admiral', 'Apostle', 'Archbishop', 'Bishop', 'Capta...
    MASCULINE_TITLES = ('Archduke', 'Ayatollah', 'Count', 'Emperor', 'Fath...
    PRESIDENTIOSITUDE = ('17 Time Winner of the Q-Anonopiac Popularity Pol...
    names = <WordListCorpusReader in '.../corpora/names' (not loaded yet)>
    stopwords = <WordListCorpusReader in '.../corpora/stopwords' (not load...

