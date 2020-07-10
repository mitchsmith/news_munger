#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from bs4 import BeautifulSoup
from collections import deque

class WikiPerson():
    
    """   """
    
    def __init__(self, name_or_url):

        """   """

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
        
        if request.status_code == 200:
            self.soup = BeautifulSoup(request.text, 'html.parser')
            self.canonical_name = self.soup.find('h1').text
            for i, p in enumerate(self.soup.findAll('p')):
                bold = [b.text for b in p.findAll('b')]
                if bold:
                    self.found = True
                    self.bio = p
                    if self.canonical_name not in bold:
                        self.canonical_name = bold[0]
                    break

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
    
    """   """
    
    def __init__(self, name_or_url):

        """   """
        if re.search(r"^http", name_or_url):      
            self.url = name_or_url
            self.name = re.sub(r'_', " ", self.url.split(r'\/')[-1])
        else:
            self.name = name_or_url
            self.url = "https://wikipedia.org/wiki/{}".format(
                            re.sub(
                                r"\s+", "_",
                                re.sub(r'^the\s+', '', self.name, flags=re.IGNORECASE)
                            )
                        )
        request = requests.get(self.url)
        self.canonical_name = None
        self.abbr = None
        self.found = False
        self.fictional = False
        self.ambiguous = False
        self.alt_url = None
        self.description = None
        
        if request.status_code == 200:
            self.soup = BeautifulSoup(request.text, 'html.parser')
            self.canonical_name = self.soup.find('h1').text
            for i, p in enumerate(self.soup.findAll('p')):
                bold = [b.text for b in p.findAll('b')]
                if self.canonical_name and self.canonical_name in bold:
                    self.found = True
                    self.description = p
                    try:
                        if re.search(r'^[A-Z\.]+', bold[1]):
                            self.abbr = bold[1]
                    except:
                        pass
                    break
                    
    def __repr__(self):
        return "<WikiOrg {}>".format(self.canonical_name)


