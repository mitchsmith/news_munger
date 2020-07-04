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
from nltk.tokenize import word_tokenize
from nltk.chunk import ChunkParserI
from nltk.chunk.util import conlltags2tree
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from collections import deque
from helpers import kill_firefox

FEMININE_TITLES = (
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
        'Dr.',
        'Dr',
        'Elder',
        'General',
        'Governor',
        'Gov.',
        'Gov',
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
        'Prof.',
        'Prof',
        'Rabbi',
        'Reverend',
        'Representative',
        'Rep',
        'Rep.',
        'Saint',
        'Secretary',
        'Senator',
        'Sen.',
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
        'Elected Leader of the Free World',
        'Engorged Effigy of Himself',
        'First Citizen of the Flies',
        'Friend to the Obsequious',
        'Friend to the Downtrodden and the White',
        'Friend to Mankind',
        'God Most High',
        'God King',
        'Grand Wizard of the USA',
        'His Royal Highness',
        'Inspirer of Adoration and Dispair',
        'Jingoistic Ringleader on High',
        'Kindness and Compassion Incarnate,'
        'Lord of All Three Branches',
        'Most High King',
        'Our Overlord and Savior',
        'Paragon of Truthiness',
        'President of the United States',
        'President of the United States of America',
        'Quite High IQ Person',
        'Rex Devi Felis',
        'Right Man for the Nut Job',
        'Simply the Best President Ever',
        'Super Stable Genius',
        'The Great and Powerful',
        'The Toast of Tyrants',
        'The Suseptible but Invulnerable',
        'The Unimpeachable',
        'Unabashed Racialist',
        'Very High IQ Person Indeed',
        "Wastern Civilization's Most Impressive Puppet",
    )


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



class PersonChunker(ChunkParserI):
    """Named Entity Recognizer for PERSON category."""
    
    def __init__(self): 
        """ Monkey patch the defailt nltk names onject  """
        
        self.name_set = set(names.words() + ['Trump', 'Alexandria']) 
        # TODO:
        # Implement a more robut way of adding names to nltk corpus"


    def _include_titles(self, iobs):
        """Ammend PERSON entities to include personal or professional titles.
        
        ARGS:
            iobs (required) list of iob tag 3-tuples

        RETURNS:
            lest of iob tag 3-tuples
        """
        
        expansion = []
        for i, ent in enumerate(iobs):
            expansion.append(list(ent))
            if i > 0 and ent[2] == 'B-PERSON':
                if iobs[i-1][0] in set(
                        GENERIC_TITLES + FEMININE_TITLES + MASCULINE_TITLES
                        ):
                    expansion[i-1][2] = 'B-PERSON'
                    expansion[i][2] = 'I-PERSON'
        if [tuple(e) for e in expansion] != iobs:
            expansion = self._include_titles([tuple(e) for e in expansion])

        return [tuple(e) for e in expansion]


    def parse(self, tagged_sent, simple=False): 
        """Apply PERSON labels to person names in supplied pos-tagged sentence.
        
        ARGS:
            tagged_sent (required) list of pos tag tuples
            simple (default = False) set True to prevent including titles
        
        RETURNS:
            list of iob tag 3-tuples
        """  
        
        iobs = [] 
        in_person = False
        for word, tag in tagged_sent: 
            if in_person and tag == 'NNP': 
                iobs.append((word, tag, 'I-PERSON')) 
            elif word in self.name_set: 
                iobs.append((word, tag, 'B-PERSON')) 
                in_person = True
            else: 
                iobs.append((word, tag, 'O')) 
                in_person = False
        
        if simple:
            return iobs

        return self._include_titles(iobs)


    def parse_tree(self, tagged_sent, simple=False):
        """Apply PERSON labels to person names in supplied pos-tagged sentence,

        (Same as parse(), but returns sentence as an nltk Tree object)
        
        ARGS:
            tagged_sent (required) list of pos tag tuples
            simple      (default = False) set True to prevent including titles

        RETURNS:
            Tree object
        """
        
        return conlltags2tree(self.parse(tagged_sent, simple))

    def __repr__(self):
        return "<PersonChunker object - methods: {}>".format(
                "'parse', 'parse_tree'"
                )


class PersonScanner():
    """ Location, labeling, and collation of named PERSON entities """

    def __init__(self):
        """ Instantiate a new PersonChunker instance and declare vars"""
        
        self._chunker = PersonChunker()
        self._person_refs = []
        self._people = []
        self._document_array = []
        self._trees = []

    def scan(self, document):
        """ Tokenize text into paragraphs, sentences and pos-taged words
        
        The result is then stored in self._document_array.

        ARGS:
            document (required) minimally sturctured text
        """
        
        for para in document:
            tp = nltk.pos_tag(word_tokenize(para))
            tagged_sents = self.get_tagged_sents(tp)
            self._document_array.append(tagged_sents)
            for s in tagged_sents:
                tree = self._chunker.parse_tree(s)
                self._trees.append(tree)
        for tree in self._trees:
            name_tags = [
                         ' '.join([n[0] for n in t])
                         for t in tree.subtrees()
                         if t.label() == 'PERSON'
                        ] 
            self._person_refs.extend(name_tags)
            self._people.extend(sorted(set(
                    [n for n in name_tags if len(n.split(' ')) > 1]
                )))

    def locate_person_refs(self, person):
        """ Index and collate PERSON by location in self._document_array
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            dict of the form {'namesegmment': [(i,j,k), ...]} 
        """
        
        refs = {}
        noms = person.split(' ')
        for nom in noms:
            refs[nom] = []
            for i, p in enumerate(self._document_array):
                for j, s in enumerate(p):
                    haystack = [t[0] for t in s]
                    if nom in haystack:
                        while haystack:
                            try:
                                k = haystack.index(nom)
                                refs[nom].append((i, j, k))
                                haystack = haystack[k+1:]
                            except ValueError:
                                break
                        tree_index = sum([len(p) for p in self._document_array[:i]]) + j
                        context = [
                                   t for t in self._trees[tree_index].subtrees()
                                   if t.label() == 'PERSON'
                                   and nom in [tag[0] for tag in t]
                                  ]
                        for c in context:
                            if len(c) > len(noms):
                                aka =' '.join([tup[0] for tup in c])
                                return self.locate_person_refs(aka)
        return refs

    def get_person_info(self, person):
        """ try to determine gender, etc. from the most complete PERSON reference.
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            dict containing discoverable PERSON attributes
        """

        gender = None
        honorific = None
        role = None
        first = None
        middle = None
        last = None
        suffix = None
        tokens = deque([p for p in person.split(' ') if re.search(r'\w+', p)])
        if tokens[0] in MASCULINE_TITLES:
            honorific = tokens.popleft()
            gender = "Male"
        elif tokens[0] in FEMININE_TITLES:
            honorific = tokens.popleft()
            gender = "Female"
        if tokens[0] in GENERIC_TITLES:
            role = tokens.popleft();
        elif re.match(r'\w\w+\.', tokens[0]):
            role = tokens.popleft()
        # At this point, element 0 should be either the first name or initial.
        if tokens[0] in names.words('female.txt'):
            if not gender:
                gender = 'Female'
        if tokens[0] in names.words('male.txt'):
            if not gender:
                gender = 'Male'
            elif not honorific:
                gender = 'Unknown'
        first = tokens.popleft()
        try:
            # Check for suffix: 'Esq.', 'Jr.'. 'Sr. etc. 
            if re.match(r'.+\.|Junior|Senior|[IVX]+$', tokens[-1]):
                suffix = tokens.pop()
        except IndexError:
            pass
        else:
            if tokens:
                last = tokens.pop()
            if tokens:
                middle = ' '.join(tokens)
        if honorific and not last:
            last = first
            first = None
        return {
                    'gender': gender,
                    'honorific': honorific,
                    'role': role,
                    'first': first,
                    'middle': middle,
                    'last': last,
                    'suffix': suffix,
                }

    def permute_names(self, person):
        """ Assemble possible forms of address based on available PERSON info.
        
        ARGS:
            person (required) string: all or part of the person's full name

        RETURNS:
            list of variations on PERSON's name
        """

        permutations = []
        flagged = False
        refs = self.locate_person_refs(person)
        info = self.get_person_info(' '.join(refs.keys()))
        parts = [x for x in info.keys() if info[x]]
        if len(parts) == 1 and 'first' in parts:
            parts[0] = 'last'
            info['last'] = info['firt']
            info['first'] = None
            skip = 0
        if not [x for x in ['honorific', 'role'] if x in parts]:
            if info['gender'] == 'Female':
                info['honorific'] = 'Ms.'
            elif info['gender'] == 'Male':
                info['honorific'] = "Mr."
            parts.append('honorific')
        if 'first' in parts:
            permutations.append(info['first'])
            skip = 1
        else:
            skip = 0
        if 'last' in parts:
            permutations.append(info['last'])
        if 'first' in parts and 'last' in parts:
            permutations.append("{} {}".format(info['first'], info['last']))
        if 'middle' in parts:
            if len(info['middle'].split(' ')) > 1:
                # consider this suspect, but deal with it later
                flagged = True
                permutations.append(
                    "{} {} {}".format(info['first'], info['middle'], info['last'])
                    )
        end = len(permutations)
        for el in [x for x in ['honorific', 'role'] if x in parts]:
            prefixes = []
            for p in permutations[skip:end]:
                prefixes.append("{} {}".format(info[el], p))
            permutations.extend(prefixes)
        if 'suffix' in parts:
            suffixed = []
            for p in permutations:
                suffixed.append("{} {}".format(p, info['suffix']))
        return permutations


    def get_tagged_sents(self, batch):
        """Split pos_tagged paragraphs into sentences.
        
        ARGS:
            batch (required) list of pos_tags
        
        RETURNS: list of lists of pos_tags (tagged_sentences) 
        """
        
        tagged_sents = []
        try:
            sep = batch.index(('.', '.')) + 1
        except ValueError:
            batch.append(('.', '.')) 
            tagged_sents.append(batch)
            return tagged_sents

        if sep < len(batch):
            first, remnant = (batch[:sep], batch[sep:])
            tagged_sents.append(first)
            tagged_sents.extend(self.get_tagged_sents(remnant))
        else:
            tagged_sents.append(batch)
        return tagged_sents


    @property
    def person_refs(self):
        return self._person_refs

    @property
    def people(self):
        return self._people
    
    @property
    def document_array(self):
        return self._document_array
    
    @property
    def trees(self):
        return self._trees

    def __repr__(self):
        return "<PersonScanner {}>".format(" ".join(self._person_refs.keys()))


class Conflation():
    """Conflate News Stories """
    def __init__(self, articles, *args):
        
        """   """
        self.conflation = []
        self.scanners = []
        try:
            if type(articles) == list:
                self.articles = articles
            else:
                self.articles = [articles]
                self.articles.extend(args)
            for i, a in enumerate(self.articles):
                if type(a) == APArticle:
                    self.scanners.append(PersonScanner())
                    self.scanners[i].scan(a.content)
                else:
                    raise TypeError("Conflation requires APArticle objects")
        except Exception as err:
            print(err)
            raise



def interweave(conflation):
    """ """
    s1 = conflation.scanners[0]
    s2 = conflation.scanners[1]
    try:
        t1 = s1.trees[:[
                    re.sub(r'___*\.?', '____.', tree2text(t))
                    for t in s1.trees
                   ].index('____.')]
    except ValueError:
        t1 = s1.trees
    try:
        t2 = s2.trees[:[
                    re.sub(r'___*\.?', '____.', tree2text(t))
                    for t in s2.trees
                   ].index('____.')]
    except ValueError:
        t2 = s2.trees
    
    combined = []
    for index, tree in enumerate(
            [t for t in t1 if re.search(r'[A-Za-z]', tree2text(t))]
            ):
        print(index)
        if index % 2 == 0:
            combined.append(tree)
        else:
            combined.append(
                        list(reversed(
                            [t for t in t2 if re.search(r'[A-Za-z]', tree2text(t))]
                        ))[index])
    return combined


def tree2text(tree):
    tags = []
    pnctfix = re.compile("(\s+)([?!:;.,])")
    positions = [p for p in tree.treepositions() if p != () and len(p) == 1]
    for p in positions:
        if type(tree[p[0]]) == tuple:
            tags.append(tree[p[0]][0])
        else:
            tags.append(tree2text(tree[p[0]]))
    txt = pnctfix.sub(r"\2 ", " ".join(tags))
    return re.sub(r"\s+$", "", re.sub(r"\s+", " ", txt))


def load_conflation(ag):
    #ag = Aggregator()
    #ag.restore_headlines()
    #ag.restore_ap_topics()
    url_1 = [h for h in ag.headlines if h[0] == 'Sports'][1][1]
    a1 = APArticle(url_1)
    url_2 = [h for h in ag.headlines if h[0] == 'Sports'][1][2]
    a2 = APArticle(url_2)
    conflation = Conflation(a1, a2)
    # Most commonly referenced name in the first article:
    sorted(
            [
                conflation.scanners[0].locate_person_refs(p)
                for p 
                in conflation.scanners[0].people
            ],
            key=lambda person: sum([len(t) for t in person.values()])
          )[-1]


    return conflation   






if __name__ == "__main__":
    """ run unit tests  """
    # import unittest
    # from tests import TestSeleniumScrapers
    # from tests import TestAggregator
    # from tests import TestPersonChunker
    # from tests import TestPersonScanner
    # unittest.main()

    # conflation = load_conflation()
    pass

#    conflation.interweave()
#    for p in conflation.conflation:
#        for s in p:
#            print(' '.join([w[0] for w in s]))





