#!/usr/bin/env python3

""" This module provides a collection of utilities for creating a madlibs-
style digest of news headlines and stories from a variety of feeds and 
scraped web pages.
"""

import os
import re
import time
import datetime
import json
import requests
import urllib.request
from urllib.request import urlopen
from bs4 import BeautifulSoup
from collections import deque

class WikiPerson():
    
    """   """
    
    def __init__(self, url):
        
        """   """
        
        html = urlopen(url)
        self.url = url
        self.found = False
        self.fictional = False
        self.ambiguous = False
        self.alt_url = None
        self.born = None
        self.bio = None
        
        if html.getcode() == 200:
            self.soup = BeautifulSoup(html, 'html.parser')
            for p in self.soup.findAll('p'):
                bd = re.search(r"\([^\)]*(born )([\w\s]+;)?\s*(.+?\d{4})", p.text)
                if bd:
                    self.found = True
                    if bd.groups()[1]:
                        self.born = bd.groups()[1][:-1]
                    self.birth_date = bd.groups()[2]
                    self.bio = p
                    break
                elif re.search(r"fictional character", p.text):
                    self.found = True
                    self.fictional = True
                    self.bio = p
                    break
                elif re.match(r"This article is about", p.text):
                    self.found = True
                    sef.ambiguous = True
                    self.alt_url = "https://en.wikipedia.org{}".format(
                            p.find(a).attrs['href']
                            )
                else:
                    continue

    def __repr__(self):
        return "<WikiPerson {}>".format(self.full_name)

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



