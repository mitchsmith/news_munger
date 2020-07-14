#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This module provides scrapers for a variety of feeds and web pages. """

import os
import re
import time
import datetime
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from collections import deque
from helpers import kill_firefox

### Bs4 based scrapers ###

class WikiPerson():
    
    """Information about a person entity gleaned from Wikipedia """
    
    def __init__(self, name_or_url):
        if re.search(r"^http", name_or_url):      
            self.url = name_or_url
            self.name = re.sub(r'_', " ", self.url.split(r'\/')[-1])
        else:
            self.name = name_or_url
            self.url = "https://wikipedia.org/wiki/{}".format(
                            re.sub(r"\s+", "_", name_or_url)
                            )
        request = requests.get(self.url)
        self.found = False
        self.fictional = False
        self.ambiguous = False
        self.alt_url = None
        self.born = None
        self.died = None
        self.bio = None
        self.bold = None
        
        if request.status_code == 200:
            soup = BeautifulSoup(request.text, 'html.parser')
            self.canonical_name = soup.find('h1').text
            for i, p in enumerate(soup.findAll('p')):
                self.bold = [b.text for b in p.findAll('b')]
                if self.bold:
                    self.found = True
                    self.bio = p
                    if self.canonical_name not in self.bold:
                        self.canonical_name = self.bold[0]
                    break
            del soup

    @property
    def full_name(self):
        if self.found:
            return self.bio.find('b').text
        return None

    @property
    def gender(self):
        if re.search(r"\s[Ss]he\s|\s[Hh]er\s", self.bio.text):
            return "Female"
        elif re.search(r"\s+[Hh]e\s|\s[Hh]is\s", self.bio.text):
            return "Male"
        else:
            return "Unspecified"

    @property
    def age(self):
        if self.found and self.birth_date:
            age = datetime.datetime.now() - datetime.datetime.strptime(
                    self.birth_date,
                    "%B %d, %Y"
                    )
            return int( age.days // 365.25)

        return "Unknown"

    def __repr__(self):
        return "<WikiPerson {}>".format(self.full_name)


class WikiOrg():
    
    """Information about an orgaization entity gleaned from Wikipedia """
    
    def __init__(self, name_or_url):
        self.determiner = False
        if re.search(r"^http", name_or_url):      
            self.url = name_or_url
            self.name = re.sub(r'_', " ", self.url.split(r'\/')[-1])
        else:
            if re.search(r'^the\s+', name_or_url, flags=re.IGNORECASE):
                self.determiner = True
            self.name = re.sub(r'^the\s+', '', name_or_url, flags=re.IGNORECASE)
            self.url = "https://wikipedia.org/wiki/{}".format(
                            re.sub(r"\s+", "_", self.name)
                            )   
        request = requests.get(self.url)
        self.canonical_name = None
        self.abbr = None
        self.found = False
        self.fictional = False
        self.ambiguous = False
        self.alt_url = None
        self.description = None
        self.bold = None
        
        if request.status_code == 200:
            soup = BeautifulSoup(request.text, 'html.parser')
            self.canonical_name = soup.find('h1').text
            for i, p in enumerate(soup.findAll('p')):
                self.bold = [b.text for b in p.findAll('b')]
                if self.canonical_name and self.canonical_name in self.bold:
                    self.found = True
                    self.description = p
                    try:
                        if re.search(r'^[A-Z\.]+', self.bold[1]):
                            self.abbr = self.bold[1]
                    except:
                        pass
                    break
            del soup
                    
    def __repr__(self):
        return "<WikiOrg {}>".format(self.canonical_name)


class WikiGPE():
    
    """Information about an geopolitical entity gleaned from Wikipedia """
    
    def __init__(self, name_or_url):
        self.determiner = False
        if re.search(r"^http", name_or_url):      
            self.url = name_or_url
            self.name = re.sub(r'_', " ", self.url.split(r'\/')[-1])
        else:
            if re.search(r'^the\s+', name_or_url, flags=re.IGNORECASE):
                self.determiner = True
            self.name = re.sub(r'^the\s+', '', name_or_url, flags=re.IGNORECASE)
            self.url = "https://wikipedia.org/wiki/{}".format(
                            re.sub(r"\s+", "_", self.name)
                            )   
        request = requests.get(self.url)
        self.canonical_name = None
        self.abbr = None
        self.found = False
        self.fictional = False
        self.ambiguous = False
        self.alt_url = None
        self.description = None
        self.bold = []       
        if request.status_code == 200:
            soup = BeautifulSoup(request.text, 'html.parser')
            self.canonical_name = soup.find('h1').text
            for i, p in enumerate(soup.findAll('p')):
                self.bold = [b.text for b in p.findAll('b')]
                if self.canonical_name and self.canonical_name in self.bold:
                    self.found = True
                    self.description = p
                    try:
                        if re.search(r'^[A-Z\.]+', self.bold[1]):
                            self.abbr = self.bold[1]
                    except:
                        pass
                    break
            del soup
                    
    def __repr__(self):
        return "<WikiGPE {}>".format(self.canonical_name)


### Selenium based scrapers ###

class HeavyScraper:
    """A resource intensive, selemium-based Soup-Nazi countermeasure

    (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
    """

    def __init__(self, url=None):
        """ARGS: url ; DEFAULT: None """
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
    """Top Google Search terms scraped from Google Trends"""

    url = "https://trends.google.com/trends/trendingsearches/daily?geo=US"

    def __init__(self):
        """ Fetch search terms and immediately close the marionette driver"""

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
        kill_firefox()
        del self.driver
    
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
    
    topic_list = []
    url = "https://apnews.com/"
    def __init__(self, topic_id=0):
        """ Fetch topics and immediatly close the marionette driver.
        
        If the topic_id arg is supplied, headlines filed under that
        topic are also retrieved before closing the marionette driver.
        """
        super().__init__(self.url)
        self.driver.get(self.url)
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
                    print("Failed to load headline")
                    pass
        
        self.driver.close()
        kill_firefox
        del self.driver

    def __repr__(self):
        return '<APHeadlines object: url={}>'.format(self.url)


class APArticle(HeavyScraper):
    """ AP Article contents fetched and scraped from the specified url."""
    
    def __init__(self, url):
        """ Fetch and scrape news article and close the marionette driver.

        ARGS:
            url (required)
        """
        self.url = url
        super().__init__(self.url)
        print("Loading {} ...".format(self.url))
        self.driver.get(self.url)
        print("Article page loaded from {}".format(self.driver.current_url))
        time.sleep(3)
        self._title = self.driver.title
        self._byline = ''
        try:
            self._byline = [
                [e.location_once_scrolled_into_view, e][1]
                for e in self.driver.find_elements_by_tag_name("span")
                if re.match("^.*byline", e.get_attribute("className"))
            ][0].text
        except:
            pass
        print("Byline: {}".format(self._byline))
        if not self._byline:
            self._byline = [
                [e.location_once_scrolled_into_view, e][1]
                for e in self.driver.find_elements_by_tag_name("div")
                if re.match("^.+byline", e.get_attribute("className"))
            ][0].text

        self._timestamp = self.driver.find_element_by_class_name(
                "Timestamp"
                ).get_attribute("data-source")
        self._content = [
            [s.location_once_scrolled_into_view, s.text][1]
            for s in self.driver.find_elements_by_tag_name("p")
        ]
        self.driver.close()    
        kill_firefox()
        del self.driver
 
    @property
    def title(self):
        return self._title
    
    @property
    def byline(self):
        return self._byline

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def content(self):
        return self._content
    
    def __repr__(self):
        return "<APArticle object: title={}, timestamp={}, url={}>".format(
                self.title, self.timestamp, self.url
                )


class Aggregator():
    """ Collect News Headlines and Stories  """

    def __init__(self):
        """ Delcare private vars and retrieve the topic list  """  

        self._topics =[]
        self._headlines = []
        self._stories = []
        try:
            if os.path.isfile('topics.json'):
                self.restore_ap_topics()
            else:
                self.refresh_ap_topics()
        except Exception as ex:
            print(ex)

    def refresh_ap_topics(self):
        """ Collects the list of AP News topics and caches it """
        
        try:
            t = APHeadlines()
            self._topics = t.topic_list
            self.cache_ap_topics()
        except Exception as ex:
            print(ex)

    def cache_ap_topics(self):
        """ Dumps self._.topics too json file  """
        
        with open('topics.json', 'w+') as outfile:
            json.dump(self._topics, outfile)

    def restore_ap_topics(self):
        """ Reads previously cached topics back into self._topics """
        
        try:
            with open('topics.json', 'r') as infile:
                self._topics = json.load(infile)
        except Exception as ex:
            print("Can't read from 'topics.json': {}".format(ex))


    def collect_ap_headlines(self):
        """ Collects AP Headlines by topic in self._hadlines.
        
        Retruns self._headlines
        """
        
        self._headlines = []
        for topic in self._topics:
            try:
                t = APHeadlines(topic[0])
                self._headlines.extend(t.headlines)
            except Exception as ex:
                print(ex)
                kill_firefox()
                time.sleep(3)
                continue

        return self._headlines

    def cache_headlines(self):
        """ Dumps self._headlines to json file  """
        
        if os.path.exists('headlines.json'):
            os.rename('headlines.json', 'headlines.bak')
        with open('headlines.json', 'w+') as outfile:
            json.dump(self._headlines, outfile)

    def restore_headlines(self):
        """ Reads previously cached headlines back into self._headlines """
        
        try:
            with open('headlines.json', 'r') as infile:
                self._headlines = json.load(infile)
        except Exception as ex:
            print("Can't read from 'headlines.json': {}".format(ex))

    def fetch_ap_article(self, url):
        """ Fetches a new APArticle and appends its content to stories
        
        ARGS: url
        """
        
        if re.search(r"apnews", url):
            try:
                article = APArticle(url)
                self._stories.append(article)
            except Exception as ex:
                kill_firefox()
                time.sleep(3)
                print("Unable to retrieve article", ex)

    @property
    def topics(self):
        return self._topics
    
    @property
    def headlines(self):
        return self._headlines

    @property
    def stories(self):
        return self._stories

    def __repr__(self):
        return "<Aggregator object - properties: {}>".format(
                "'topics', 'headlines', 'stories'"
                )


if __name__ == "__main__":
    """ run unit tests  """
    # import unittest
    # from tests import TestSeleniumScrapers
    # from tests import TestAggregator
    # unittest.main()

    pass





