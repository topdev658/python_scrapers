from custom_libs.db import queue_simple
from scrapers.santander_scraper.santander_scraper import SantanderScraper
from tests.helpers import test_helpers
from tests.helpers.basic_test_case import BasicTestCase


def tearDownModule():
    """should be included in each ...tests.py file for graceful shutdown"""
    print('Finished tests in the module')
    queue_simple.wait_finishing()


class SantanderScraperTestCase(BasicTestCase):
    scraper = test_helpers.new_scraper_for_tests(
        SantanderScraper,
        customer_id=149727,
        fin_ent_access_id=9602,
        date_from='01/09/2018',
        date_to='10/09/2018'
    )

    def test_accounts_num(self):
        self.assertGreaterEqual(test_helpers.uploaded_accounts_num(self.scraper), 7)

    def test_movements_num(self):
        self.assertGreaterEqual(test_helpers.uploaded_movements_num(self.scraper), 1)

    def test_movements_num_per_account(self):
        expect = {}
        uploaded = test_helpers.uploaded_movements_per_account_num(self.scraper)
        for a, m in expect:
            self.assertGreaterEqual(uploaded[a], m)

# You can add more test cases here
