import unittest
from munger import *

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
                         """Expected 'https://apnews.com/apf-entertainment' but url \
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

    def test_collect_and_cache_ap_headlines(self):
        self.ag.collect_ap_headlines()
        self.hlcount = len(self.ag._headlines)
        if self.hlcount > 0:
            if os.path.isfile('headlines.json'):
                os.rename('headlines.json', 'headlines.bak')
        self.ag.cache_headlines()
        self.assertTrue(
                        self.hlcount > 0,
                        "no headline data was feched"
                       )

    def test_cache_headlines(self):
        self.assertTrue(
                   os.path.isfile('headlines.json'),
                   "cache file not found"
                  ) 

    def test_restore_headlines(self):
        self.ag.restore_headlines()
        self.assertTrue(len(self.ag._headlines) > 0, "no headlines were loaded")

    def test_fetch_story_appends_to_stories(self):
        self.ag._stories = []
        try:
            if os.path.isfile('headlines.json'):
                self.ag.restore_headlines()
            else:
                self.ag.collect_ap_headlines()
        except Exception as ex:
            print("Coulnd't load headlines", ex)
        url = [h[1] for h in self.ag._headlines if h[0] == 'Politics'][1]
        self.ag.fetch_ap_article(url)
        self.assertTrue(
                        len(self.ag._stories) == 1,
                        "Failed to retrieve article."
                       )


class TestPersonChunker(unittest.TestCase):
    def setUp(self):
        self.ag = Aggregator()
        self.ag.restore_headlines()
        url = [h[1] for h in self.ag.headlines if h[0] == 'Politics'][0]
        # self.ag.fetch_ap_article(url)
        self.chunker = PersonChunker()

#    def test_chunker_can_chunk(self):
#        self.chunks = [
#                  self.chunker.parse(nltk.pos_tag(word_tokenize(s)), simple=True)
#                  for s in self.ag.stories[0].content[8].split(r'. *')
#                 ]
#        self.assertTrue(len(self.chunks) >= 1, "not chunky enough.")
    
    def test_chunker_labels_first_names(self):
        ts = nltk.pos_tag(word_tokenize(
                "Franklin loves Dunkin Donuts, and so does Sharon."
                ))
        self.chunks = self.chunker.parse(ts, simple=True)
        fnames = [c[0] for c in self.chunks if c[2] == 'B-PERSON']
        self.assertEqual(fnames[0], "Franklin", "Franklin has no label")
        self.assertEqual(fnames[-1], "Sharon", "Sharon has no label")
        self.assertEqual(len(fnames), 2, "found more than two names")

    def test_chunker_labels_last_names(self):
        ts = nltk.pos_tag(word_tokenize("""
                Frank Sharon loves Sharon Frank, but Sharon loves Duncan.
                """
                ))
        self.chunks = self.chunker.parse(ts, simple=True)
        snames = [c[0] for c in self.chunks if c[2] == 'I-PERSON']
        self.assertEqual(snames[0], "Sharon", "Sharon has no label")
        self.assertEqual(snames[-1], "Frank", "Frank has no label")
        self.assertEqual(
                         len(snames),
                         2,
                         "found more than two names: {}".format(snames)
                        )

    def test_chunker_correctly_lables_donuts(self):
        ts = nltk.pos_tag(word_tokenize("""
                Duncan Donuts loves Dunkin Donuts just as much as Frank
                and Sharon do.
                """
                ))
        self.chunks = self.chunker.parse(ts, simple=True)
        fnames = [c[0] for c in self.chunks if c[2] == 'B-PERSON']
        snames = [c[0] for c in self.chunks if c[2] == 'I-PERSON']
        self.assertEqual(
                 fnames,
                 ['Duncan', 'Frank', 'Sharon'],
                 "Expected ['Duncan', 'Frank', 'Sharon']"
                )
        self.assertTrue(len(snames) == 1, "too many donuts! {}".format(snames))

    def test_chunker_can_include_titles(self):
        ts = nltk.pos_tag(word_tokenize("""
                Sen. Bernie Sanders and Rep. Alexandria Ocasio-Cortez are also
                quite fond of donuts.
                """
                ))
        chunks = self.chunker.parse(ts)
        self.assertEqual(chunks[0][2], 'B-PERSON', "element isn't labeled")

    def test_chunker_parse_tree_returns_a_tree(self):
        ts = nltk.pos_tag(word_tokenize("""
                Sen. Bernie Sanders and Rep. Alexandria Ocasio-Cortez are also
                quite fond of donuts.
                """
                ))
        tree = self.chunker.parse_tree(ts)
        self.assertEqual(tree[0].label(), 'PERSON', "element isn't labeled")


class TestPersonScanner(unittest.TestCase):
    """   """
    def setUp(self):
        with open('test_story.json') as infile:
            self.story = json.load(infile)
        self.scanner = PersonScanner()

    def test_can_chunk_sentences(self):
        para = """This paragraph contains three sentenences. This is the second.
        There was one more left at the end before counting this unpunctutated one
        """
        tp = nltk.pos_tag(word_tokenize(para))
        tagged_sents = self.scanner.get_tagged_sents(tp)
        self.assertEqual(len(tagged_sents), 3, "Didn't find all three sentences.")

    def test_scan_gives_one_tree_per_sentence(self):
        self.scanner.scan(self.story)
        self.assertEqual(
                         len(self.scanner._document_array),
                         len(self.story),
                         "expected {} of 29 paragraphs".format(len(self.story))
                        )
        self.assertEqual(
                         len(self.scanner._trees),
                         sum([len(p) for p in self.scanner._document_array]),
                         "tree count doesn't match tagged sentence count"    
                        )
        
    def test_person_scanner_finds_people(self):
        self.scanner.scan(self.story)
        self.assertTrue(self.scanner._people, "Where are all the lovely people?")
        self.assertTrue(
                         'Atlanta Mayor Keisha Lance Bottoms' in
                         self.scanner._people,
                         'Expected "Atlanta Mayor Keisha Lance Bottoms"'
                       )

    def test_pscanner_can_locate_name_refs(self):
        self.scanner.scan(self.story)
        refs = self.scanner.locate_person_refs('Sen. Amy Klobuchar')
        self.assertEqual(len(refs['Klobuchar']), 4, "expected 4 Klobuchar refs")

    def test_pscanner_can_permute_names(self):
        self.assertTrue(False, "Finish defining permute_names()")


