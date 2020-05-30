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

    #def test_collect_and_cache_ap_headlines(self):
    #    self.ag.collect_ap_headlines()
    #    self.hlcount = len(self.ag._headlines)
    #    if self.hlcount > 0:
    #        if os.path.isfile('headlines.json'):
    #            os.rename('headlines.json', 'headlines.bak')
    #    self.ag.cache_headlines()
    #    self.assertTrue(
    #                    self.hlcount > 0,
    #                    "no headline data was feched"
    #                   )

    #def test_cache_headlines(self):
    #    self.assertTrue(
    #               os.path.isfile('headlines.json'),
    #               "cache file not found"
    #              ) 

    def test_restore_headlines_(self):
        self.ag.restore_headlines()
        self.assertTrue(len(self.ag._headlines) > 0, "no headlines were loaded")

    def test_fetch_story_appends_to_stories(self):
        self.assertTrue(False, "Finish writing this test!")


