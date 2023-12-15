import unittest

from project import settings as project_settings
from scrapers._basic_scraper.basic_scraper import BasicScraper

# hack to redefine project settings to avoid collisions with PROD
project_settings.IS_UPDATE_DB = True
project_settings.IS_PRODUCTION_DB = False
project_settings.IS_SEND_NOTIFICATIONS = False


class BasicTestCase(unittest.TestCase):
    """You should inherit all scrapers test classes
    from this class to obtain initial scraping process
    """
    scraper = None  # type: BasicScraper
    scraping_result_code = '0'  # success
    is_scraped = False

    @classmethod
    def setUpClass(cls):
        # handle calls for each parent/child
        if not cls.scraper or cls.is_scraped:
            return

        print('Scrape now...')
        result, _ = cls.scraper.main()
        cls.scraping_result_code = result.code
        cls.is_scraped = True

    @classmethod
    def tearDownClass(cls):
        print('Finished tests for: {}'.format(cls))

    def setUp(self):
        assert project_settings.IS_PRODUCTION_DB is False
        assert project_settings.IS_UPDATE_DB is True

    def test_scraping_result_code(self):
        self.assertEqual(self.scraping_result_code, '0')
