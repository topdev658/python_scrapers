from custom_libs.db import queue_simple
from scrapers.kutxabank_scraper.kutxa_scraper import KutxaScraper
from tests.helpers import test_helpers
from tests.helpers.basic_test_case import BasicTestCase


def tearDownModule():
    """should be included in each ...tests.py file for graceful shutdown"""
    print('Finished tests in the module')
    queue_simple.wait_finishing()


class KutxaScraperTestCase(BasicTestCase):
    scraper = test_helpers.new_scraper_for_tests(
        KutxaScraper,
        customer_id=97716,
        fin_ent_access_id=3440,
        date_from='01/11/2017',
        date_to='10/11/2017'
    )

    def test_accounts_num(self):
        """Checks the number of scraped accounts"""
        self.assertGreaterEqual(test_helpers.uploaded_accounts_num(self.scraper), 22)

    def test_movements_num(self):
        """Checks the number of scraped movements"""
        self.assertGreaterEqual(test_helpers.uploaded_movements_num(self.scraper), 10000)

    def test_movements_num_per_account(self):
        """Checks the number of scraped movements of each account"""
        expect = {}
        uploaded = test_helpers.uploaded_movements_per_account_num(self.scraper)
        for a, m in expect:
            self.assertGreaterEqual(uploaded[a], m)

# You can add more test cases here

# class KutxaScraperTestCase2(BasicTestCase):
# ...
