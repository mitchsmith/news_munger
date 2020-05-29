# news_munger
A collection of utilities for creating a madlibs-style digest of news headlines and stories from a variety of feeds and scraped web pages.

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
    
    class APArticle(HeavyScraper)
     |  A resource intensive, selemium-based Soup-Nazi countermeasure
     |  (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
     |  
     |  Method resolution order:
     |      APArticle
     |      HeavyScraper
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, url)
     |      Initialize self.  See help(type(self)) for accurate signature.
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
     |      Fetches the list of topics and immediatly closes the marionette
     |      driver. If the topic_id arg is supplied, headlines filed under that
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
     |

    class Aggregator(builtins.object)
     |  Collect News Headlines and Stories
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |      Delcare private vars and retrieve the topic list
     |  
     |  cache_headlines(self)
     |      Dumps self._headlines to json file
     |  
     |  collect_ap_headlines(self)
     |      Collects AP Headlines for each topic and stores them in
     |      self._hadlines. Retruns self._headlines
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
     |  (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
     |  
     |  Methods defined here:
     |  
     |  __init__(self, url=None)
     |      Initialize self.  See help(type(self)) for accurate signature.
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
     |      Fetches a list of trending google search terms and immediately
     |      closes the marionette driver
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
         FEMENIN_TITLES = ('Chairwoman', 'Councilwoman', 'Congresswoman', 'Coun...
         GENERIC_TITLES = ('Admiral', 'Apostle', 'Archbishop', 'Bishop', 'Capta...
         MASCULINE_TITLES = ('Archduke', 'Ayatollah', 'Count', 'Emperor', 'Fath...
         PRESIDENTIOSITUDE = ('17 Time Winner of the Q-Anonopiac Popularity Pol...
         names = <WordListCorpusReader in '.../corpora/names' (not loaded yet)>
         stopwords = <WordListCorpusReader in '.../corpora/stopwords' (not load...

