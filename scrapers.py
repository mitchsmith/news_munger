#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" This module provides scrapers for a variety of feeds and web pages. """

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from helpers import kill_firefox, fix_double_quotes

### Bs4 based scrapers ###


class WikiPerson:

    """Information about a person entity gleaned from Wikipedia """

    def __init__(self, name_or_url):
        if re.search(r"^http", name_or_url):
            self.url = name_or_url
            self.name = re.sub(r"_", " ", self.url.split(r"\/")[-1])
        else:
            self.name = name_or_url
            self.url = "https://wikipedia.org/wiki/{}".format(
                re.sub(r"\s+", "_", name_or_url)
            )
        request = requests.get(self.url)
        self.found = False
        self.canonical_name = None
        self.bio = None

        if request.status_code == 200:
            soup = BeautifulSoup(request.text, "html.parser")
            self.canonical_name = soup.find("h1").text
            for element in soup.findAll("p"):
                bold = [b.text for b in element.findAll("b")]
                if bold:
                    self.found = True
                    self.bio = element
                    if self.canonical_name not in bold:
                        self.canonical_name = bold[0]
                    break
            del soup

    @property
    def full_name(self):

        """Person's full name """

        if self.found:
            return self.bio.find("b").text
        return None

    @property
    def gender(self):

        """Person's gender (if discoverable) """

        if re.search(r"\s[Ss]he\s|\s[Hh]er\s", self.bio.text):
            return "Female"

        if re.search(r"\s+[Hh]e\s|\s[Hh]is\s", self.bio.text):
            return "Male"

        return "Unspecified"

    def __repr__(self):
        return "<WikiPerson {}>".format(self.full_name)


class WikiOrg:

    """Information about an orgaization entity gleaned from Wikipedia """

    # pylint: disable=too-many-instance-attributes
    # Eight is reasonable in this case.

    # pylint: disable=too-few-public-methods
    # Wiki lookups are like french eggs: one is 'un oeuf'

    def __init__(self, name_or_url):

        """Scrape available org info from wikipedia """

        self.determiner = False
        if re.search(r"^http", name_or_url):
            self.url = name_or_url
            self.name = re.sub(r"_", " ", self.url.split(r"\/")[-1])
        else:
            if re.search(r"^the\s+", name_or_url, flags=re.IGNORECASE):
                self.determiner = True
            self.name = re.sub(r"^the\s+", "", name_or_url, flags=re.IGNORECASE)
            self.url = "https://wikipedia.org/wiki/{}".format(
                re.sub(r"\s+", "_", self.name)
            )
        self.canonical_name = None
        self.abbr = None
        self.found = False
        self.description = None

        request = requests.get(self.url)

        if request.status_code == 200:
            soup = BeautifulSoup(request.text, "html.parser")
            self.canonical_name = soup.find("h1").text
            for element in soup.findAll("p"):
                self.bold = [b.text for b in element.findAll("b")]
                if self.canonical_name and self.canonical_name in self.bold:
                    self.found = True
                    self.description = element
                    try:
                        if re.search(r"^[A-Z\.]+", self.bold[1]):
                            self.abbr = self.bold[1]
                    except IndexError:
                        pass
                    break

            del soup

    def __repr__(self):
        return "<WikiOrg {}>".format(self.canonical_name)


class WikiGPE:

    """Information about an geopolitical entity gleaned from Wikipedia """

    # pylint: disable=too-few-public-methods
    # Wiki lookups are like french eggs: one is 'un oeuf'

    def __init__(self, name_or_url):

        """Scrape available geo-political entity info fromm wikipedia """

        self.determiner = False
        if re.search(r"^http", name_or_url):
            self.url = name_or_url
            self.name = re.sub(r"_", " ", self.url.split(r"\/")[-1])
        else:
            if re.search(r"^the\s+", name_or_url, flags=re.IGNORECASE):
                self.determiner = True
            self.name = re.sub(r"^the\s+", "", name_or_url, flags=re.IGNORECASE)
            self.url = "https://wikipedia.org/wiki/{}".format(
                re.sub(r"\s+", "_", self.name)
            )
        self.canonical_name = None
        self.abbr = None
        self.found = False
        self.description = None

        request = requests.get(self.url)
        if request.status_code == 200:
            soup = BeautifulSoup(request.text, "html.parser")
            self.canonical_name = soup.find("h1").text
            for element in enumerate(soup.findAll("p")):
                bold = [b.text for b in element.findAll("b")]
                if self.canonical_name and self.canonical_name in bold:
                    self.found = True
                    self.description = element
                    try:
                        if re.search(r"^[A-Z\.]+", bold[1]):
                            self.abbr = bold[1]
                    except IndexError:
                        pass

                    break

            del soup

    def __repr__(self):
        return "<WikiGPE {}>".format(self.canonical_name)


class APArticle:

    """ AP Article contents fetched and scraped from the specified url."""

    def __init__(self, url):

        """Fetch and scrape news article

        ARGS:
            url (required)
        """
        self.url = url
        self._title = None
        self._byline = None
        self._timestamp = None
        self._content = None
        request = requests.get(url)
        if request.status_code == 200:
            print("Article page loaded from {}".format(self.url))
            by_pat = re.compile(r"bylines")
            time_pat = re.compile(r"timestamp", flags=re.IGNORECASE)
            story_pat = re.compile(
                r"^.*?storyHTML\"\:\"\\+u003cp>(.*)\}?", flags=re.MULTILINE
            )
            soup = BeautifulSoup(request.text, "html.parser")
            self._title = soup.find("title").text
            for span in (s for s in soup.find_all("span") if "class" in s.attrs):
                for class_name in span.attrs["class"]:
                    if by_pat.search(class_name):
                        self._byline = span.text
                    if time_pat.search(class_name):
                        self._timestamp = span.attrs["data-source"]
            print("Title: {}".format(self._title))
            print("Byline: {}".format(self._byline))

            story_html = re.sub(r"\\+u003c", "<", story_pat.search(request.text)[1])
            story_html = re.sub(r"\\+", "", story_html)
            soup = BeautifulSoup(story_html, "html.parser")
            paragraphs = [fix_double_quotes(p.text) for p in soup.find_all("p")]

            end = sorted([p for p in paragraphs if re.match(r"^_+$", p)], key=len)[0]
            self._content = {
                "html": story_html,
                "text": "\n".join(paragraphs[: paragraphs.index(end)]),
            }

    @property
    def title(self):

        """Article title (headline) """
        return self._title

    @property
    def byline(self):

        """Article byline """
        return self._byline

    @property
    def timestamp(self):

        """Artice timestamp """
        return self._timestamp

    @property
    def content(self):
        """Dict containing the article's text and html """
        return self._content

    def __repr__(self):
        return "<APArticle object: title={}, timestamp={}, url={}>".format(
            self.title, self.timestamp, self.url
        )


### Selenium based scrapers ###


class HeavyScraper:

    """A resource intensive, selemium-based Soup-Nazi countermeasure

    (Base class for scrapers requiring gekodriver instead of Beautiful Soup)
    """

    # pylint: disable=too-few-public-methods
    # These scrapers are meant to be instantiated once and discarded

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
        return "<HeavyScraper object: url={}>".format(self.url)


class Trends(HeavyScraper):

    """Top Google Search terms scraped from Google Trends"""

    url = "https://trends.google.com/trends/trendingsearches/daily?geo=US"

    def __init__(self):

        """ Fetch search terms and immediately close the marionette driver"""
        super().__init__(self.url)
        self.driver.get(self.url)
        self._trends = [
            (
                topic.text.split("\n")[1],
                topic.text.split("\n")[2],
                topic.text.split("\n")[6],
            )
            for topic in self.driver.find_elements_by_class_name("feed-item")
        ]
        self.driver.close()
        self.driver.quit()
        kill_firefox()
        del self.driver

    @property
    def trends(self):
        """List of tuples containing data scraped fro feet-items """
        return self._trends

    @property
    def ngrams(self):
        """Trending colocations fro google searches """
        return [n[0] for n in self._trends]

    def __repr__(self):
        return "<Trends object: url={}>".format(self.url)


class APHeadlines(HeavyScraper):

    """ Scrape AP News Topics and optionally retrieve headlines by topic  """

    # pylint: disable=too-few-public-methods
    # These scrapers are meant to be instantiated once and discarded

    topic_list = []
    url = "https://apnews.com/"

    def __init__(self, topic_id=0):

        """Fetch topics and immediatly close the marionette driver.

        If the topic_id arg is supplied, headlines filed under that
        topic are also retrieved before closing the marionette driver.
        """
        super().__init__(self.url)
        self.driver.get(self.url)
        self.headlines = []
        self.ap_nav = self.driver.find_elements_by_class_name("nav-action")
        print("Got AP Nav")
        time.sleep(3)
        self.ap_nav[1].click()
        time.sleep(3)
        self.topic_nav = self.driver.find_element_by_class_name(
            "TopicsDropdown"
        ).find_elements_by_tag_name("li")
        # create_topic_list
        for index, element in enumerate(self.topic_nav):
            if index > 0:
                self.topic_list.append((index, element.text))

        if topic_id > 0:
            topic = self.topic_nav[topic_id]
            time.sleep(3)
            if not topic.find_element_by_tag_name("a").is_displayed():
                self.ap_nav[1].click()
                time.sleep(1)
            print(
                "Navigating to {}".format(
                    topic.find_element_by_tag_name("a").get_attribute("href")
                )
            )
            topic.find_element_by_tag_name("a").click()
            time.sleep(3)
            self.url = self.driver.current_url
            print("{} is loaded; retrieving headlines ...".format(self.url))
            stories = self.driver.find_elements_by_class_name("FeedCard")
            for story in stories:
                try:
                    # pylint: disable=broad-except
                    # These are triggered by ads and countermeasures
                    # no need to handle; note them and move on
                    if story.location_once_scrolled_into_view:
                        txt = story.text
                        href = story.find_element_by_tag_name("a").get_attribute("href")
                        self.headlines.append((self.driver.title, href, txt))
                except Exception as err:
                    print(f"Failed to load headline:\n{err}")

        self.driver.close()
        self.driver.quit()
        kill_firefox()

    def __repr__(self):
        return "<APHeadlines object: url={}>".format(self.url)


class Aggregator:

    """ Collect News Headlines and Stories  """

    def __init__(self):
        """ Delcare private vars and retrieve the topic list  """

        self._topics = []
        self._headlines = []
        self._stories = []
        if os.path.isfile("topics.json"):
            self.restore_ap_topics()
        else:
            self.refresh_ap_topics()

    def refresh_ap_topics(self):
        """ Collects the list of AP News topics and caches it """

        headlines = APHeadlines()
        self._topics = headlines.topic_list
        self.cache_ap_topics()

    def cache_ap_topics(self):
        """ Dumps self._.topics too json file  """

        with open("topics.json", "w+") as outfile:
            json.dump(self._topics, outfile)

    def restore_ap_topics(self):
        """ Reads previously cached topics back into self._topics """

        with open("topics.json", "r") as infile:
            self._topics = json.load(infile)

    def collect_ap_headlines(self):
        """ Collects AP Headlines by topic in self._hadlines.

        Retruns self._headlines
        """

        self._headlines = []
        for topic in self._topics:
            try:
                # pylint: disable=broad-except
                # These are triggered by ads and countermeasures
                # no need to handle; note them and move on
                top = APHeadlines(topic[0])
                self._headlines.extend(top.headlines)
            except Exception as ex:
                print(ex)
                kill_firefox()
                time.sleep(3)
                continue

        self.cache_headlines()
        return self._headlines

    def cache_headlines(self):
        """ Dumps self._headlines to json file  """

        if os.path.exists("headlines.json"):
            os.rename("headlines.json", "headlines.bak")
        with open("headlines.json", "w+") as outfile:
            json.dump(self._headlines, outfile)

    def restore_headlines(self):
        """ Reads previously cached headlines back into self._headlines """

        try:
            with open("headlines.json", "r") as infile:
                self._headlines = json.load(infile)
        except IOError as err:
            print("Can't read from 'headlines.json': {}".format(err))

    def fetch_ap_article(self, url):
        """ Fetches a new APArticle and appends its content to stories

        ARGS: url

        """

        if re.search(r"apnews", url):
            try:
                # pylint: disable=broad-except
                # These are triggered by ads and countermeasures
                # no need to handle; note them and move on
                article = APArticle(url)
                self._stories.append(article)
            except Exception as ex:
                kill_firefox()
                time.sleep(3)
                print("Unable to retrieve article", ex)

    @property
    def topics(self):
        """List of topics """
        return self._topics

    @property
    def headlines(self):
        """List of headlines """
        return self._headlines

    @property
    def stories(self):
        """List of stories """
        return self._stories

    def __repr__(self):
        return "<Aggregator object - properties: {}>".format(
            "'topics', 'headlines', 'stories'"
        )


if __name__ == "__main__":
    import unittest

    # from tests import TestSeleniumScrapers
    # from tests import TestAggregator

    unittest.main()
