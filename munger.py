#!/usr/bin/env python3

""" This module provides a collection of utilities for creating a madlibs-style digest
of news headlines and stories from a variety of feeds and scraped web pages.
"""

import os
import re
import time
import json
import nltk
try:
    from nltk.corpus import stopwords
except:
    nltk.download('stopwords')
    nltk.download('punkt') 
    from nltk.corpus import stopwords
from nltk.corpus import names
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from collections import deque

FEMENIN_TITLES = (
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
        'Dr',
        'Elder',
        'General',
        'Governor',
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
        'Prof',
        'Rabbi',
        'Reverend',
        'Representative',
        'Rep',
        'Saint',
        'Secretary',
        'Senator',
        'Sen',
        'Sergeant',
        'Sultan',
        'Swami',
    )


class HeavyScraper:
    """A resource intensive, selemium-based Soup-Nazi countermeasure
    (Base class for scrapers that must use gekodriver instead of Beautiful Soup)
    """
    def __init__(self, url=None):
        self.url = url
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        options.add_argument("--incognito")
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(3)

    def __repr__(self):
        return '<HeavyScraper object: url={}>'.format(self.url)


class Trends(HeavyScraper):
    """
    Top Google Search terms scraped from Google Trends
    """
    url = "https://trends.google.com/trends/trendingsearches/daily?geo=US"

    def __init__(self):
        """ Fetches a list of trending google search terms and immediately close the marionette driver  """
        super().__init__(self.url)
        self.driver.get(self.url)
        self._trends = [
                (topic.text.split("\n")[1], topic.text.split("\n")[2], topic.text.split("\n")[6])
                for topic
                in self.driver.find_elements_by_class_name('feed-item')
            ]
        self.driver.close()
    
    @property
    def trends(self):
        return self._trends

    @property
    def ngrams(self):
        return [n[0] for n in self._trends]
 
    def __repr__(self):
        return '<Trends object: url={}>'.format(self.url)



if __name__ == "__main__":
    import unittest

    class TestSeleniumScrapers(unittest.TestCase):

        def test_instantiate_heavy_scraper(self):
            """ Test instantiate HeavyScraper object. """
            o = HeavyScraper()
            self.assertEqual(repr(o), "<HeavyScraper object: url=None>", "incorrect object representation")
            o.driver.close()

        def test_instantiate_trends_object(self):
            print("Fetching data; please be patient . . .")
            o = Trends()
            self.assertEqual(
                    repr(o),
                    "<Trends object: url=https://trends.google.com/trends/trendingsearches/daily?geo=US>",
                    "incorrect object representation"
                    )
            self.assertTrue(len(o.ngrams) > 0, "no data was fetched")
        

    unittest.main()

