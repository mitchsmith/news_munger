#!/usr/bin/env python3

""" This module provides a collection of utilities for creating a madlibs-
style digest of news headlines and stories from a variety of feeds and 
scraped web pages.
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

PRESIDENTIOSITUDE = (
        '17 Time Winner of the Q-Anonopiac Popularity Pole',
        'Adored Dispicable',
        'Beloved Orange Dumpling',
        'Chaste Keeper of American Great-Againness',
        'Chief Scientist of the United States',
        'Chosen One',
        'Delightful Fellow',
        'Duely Elected Leader fo the Free World',
        'Effigy of Himself',
        'First Citizen of the Flies',
        'Friend to the Obsequious',
        'Friend to the Downtrodden and the White',
        'Friend to Mankind',
        'God Most High',
        'God King',
        'Grand Wizard of the USA',
        'His Royal Highness',
        'Inspirer of Adoration and Dispair',
        'Kindness Incarnate,'
        'Most High King',
        'Our Overlord and Savior',
        'Paragon of Honesty',
        'President of the United States',
        'President of the United States of America',
        'Quite High IQ Person',
        'Rex Devi Felis',
        'Right Mand for the Job',
        'Simply the Best President Ever',
        'Stable Genius',
        'The Great and Powerful',
        'The Toast of Tyrants',
        'The Unimpeachable',
        'Unabashed Racist',
        'Very High IQ Person Indeed',
        "Wastern Civilization's Most Impressive Archon",
    )


class HeavyScraper:
    """A resource intensive, selemium-based Soup-Nazi countermeasure
    (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
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
        """ Fetches a list of trending google search terms and immediately
        closes the marionette driver 
        """
        super().__init__(self.url)
        self.driver.get(self.url)
        self._trends = [
                (topic.text.split(
                                  "\n")[1],
                                  topic.text.split("\n")[2],
                                  topic.text.split("\n")[6]
                                 )
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


class APHeadlines(HeavyScraper):
    """ Scrape AP News Topics and optionally retrieve headlines by topic  """
    url = "https://apnews.com/"
    def __init__(self, topic_id=0):
        """ Fetches the list of topics and immediatly closes the marionette
        driver. If the topic_id arg is supplied, headlines filed under that
        topic are also retrieved before closing the marionette driver.
        """
        super().__init__(self.url)
        self.driver.get(self.url)
        self.topic_list = []
        self.headlines = []
        self.ap_nav = self.driver.find_elements_by_class_name('nav-action')
        print("Got AP Nav")
        time.sleep(3)
        self.ap_nav[1].click()
        time.sleep(3)
        self.topic_nav = self.driver.find_element_by_class_name(
                'TopicsDropdown'
                ).find_elements_by_tag_name('li')
        # create_topic_list
        for index, li in enumerate(self.topic_nav):
            if index > 0:
                self.topic_list.append((index, li.text))

        if topic_id > 0:
            topic = self.topic_nav[topic_id]
            time.sleep(3)
            if not topic.find_element_by_tag_name('a').is_displayed():
                self.ap_nav[1].click()
                time.sleep(1)
            print("Navigating to {}".format(
                    topic.find_element_by_tag_name('a').get_attribute('href'))
                )
            topic.find_element_by_tag_name('a').click()
            time.sleep(3)
            self.url = self.driver.current_url
            print("{} is loaded; retrieving headlines ...".format(self.url))
            stories = self.driver.find_elements_by_class_name('FeedCard')
            for story in stories:
                try:
                    loc = story.location_once_scrolled_into_view
                    txt = story.text
                    href = story.find_element_by_tag_name('a').get_attribute('href')
                    self.headlines.append((self.driver.title, href, txt))
                except:
                    pass

        self.driver.close()

    def __repr__(self):
        return '<APHeadlines object: url={}>'.format(self.url)


class Aggregator():
    """   """
    def __init__(self):
        """   """  
        self._topics =[]
        self._headlines = []
        self._stories = []
        try:
            t = APHeadlines()
            self._topics = t.topic_list
        except Exception as ex:
            print(ex)

    def collect_headlines(self):
        for topic in self._topics:
            try:
                t = APHeadlines(topic[0])
                self._headlines.extend(t.headlines)
            except Exception as ex:
                print(ex)

        return self._headlines

    def cache_headlines(self):
        with open('headlines.json', 'w+') as outfile:
            json.dump(self._headlines, outfile)

    def restore_headlines(self):
        try:
            with open('headlines.json', r) as infile:
                self._headlines = json.load(infile)
        except Exception as ex:
            print("Can't read from 'headlines.json': {}".format(ex))

 

if __name__ == "__main__":
    import unittest

    class TestSeleniumScrapers(unittest.TestCase):

        def tearDown(self):
            try:
                self.o.driver.close()
            except:
                pass

        def test_instantiate_heavy_scraper(self):
            """ Test instantiate HeavyScraper object. """
            self.o = HeavyScraper()
            self.assertEqual(
                             repr(self.o),
                             "<HeavyScraper object: url=None>",
                             "incorrect object representation"
                            )
            self.o.driver.close()

        def test_instantiate_trends_object(self):
            """ Test instanttiate Trends object.  """
            print("Fetching trends data; please be patient . . .")
            self.o = Trends()
            self.assertEqual(
                repr(self.o),
                "<Trends object: url=https://trends.google.com/trends/trendingsearches/daily?geo=US>",
                "incorrect object representation"
                )
            self.assertTrue(len(self.o.ngrams) > 0, "no data was fetched")

        def test_instantiate_apheadlines(self):
            """ Test instantiate APHeadlines object  """
            print("Fetching AP News topics data; please be patient . . .")
            self.o = APHeadlines()
            self.assertEqual(
                    repr(self.o),
                    "<APHeadlines object: url=https://apnews.com/>",
                    "incorrect object representation"
                    )
            self.assertTrue(len(self.o.topic_list) > 0, "no data was fetched")
            self.assertEqual(
                             self.o.topic_list[1][1],
                             "Entertainment",
                             "Expected 'Entertainment' but got '{}'".format(
                                    self.o.topic_list[1][1]
                                    )
                            )

        def test_scrape_ap_headlines_by_topic(self):
            """ Test APHeadlines can retrieve headlines for a given topic  """
            print("Fetching topic headlines'; please be EXTRA patient . . .")
            self.o = APHeadlines(2)
            time.sleep(3)
            self.assertEqual(
                             self.o.url,
                             "https://apnews.com/apf-entertainment",
                             """Expected 'https://apnews.com/apf-entertainment' but url
                             is '{}'
                             """.format(self.o.url)
                            )
            
            self.assertTrue(len(self.o.headlines) > 0, "no data was fetched")
 

    class TestAggregator(unittest.TestCase):
        """   """
        def setUp(self):
            self.ag = Aggregator()


        def test_new_aggregator_retrieves_topics(self):
            self.assertTrue(len(self.ag._topics) > 0, "no topic data was fetched")



    unittest.main()

