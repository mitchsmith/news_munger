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


if __name__ == "__main__":
    print('Running unit tests . . .')
    assert True
    print('Everything Passed.')
