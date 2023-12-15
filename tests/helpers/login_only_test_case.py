import traceback
import unittest

from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '1.1.0'
__changelog__ = """
1.1.0
try/except to fail only in tests
"""


class LoginOnlyTestCase(unittest.TestCase):
    """You should inherit scrapers test classes
    from this class to check only auth possibility
    """
    scraper = None  # type: BasicScraper
    is_logged_in = True
    is_credentials_error = False
    response = None

    @classmethod
    def setUpClass(cls):
        # handle calls for each parent/child
        if not cls.scraper:
            return

        print('Log in now...')

        # For Jenkins: exception wrapper to be able to achieve the tests
        # and fail on assertion instead of exception
        result_tuple = (None, None, False, False)
        try:
            result_tuple = cls.scraper.login()
        except Exception:
            print('HANDLED EXCEPTION: {}'.format(
                traceback.format_exc()
            ))

        cls.response = result_tuple[1]
        cls.is_logged_in = result_tuple[2]
        cls.is_credentials_error = result_tuple[3]

    @classmethod
    def tearDownClass(cls):
        print('Finished tests for: {}'.format(cls))

    def test_is_logged_in(self):
        self.assertEqual(True, self.is_logged_in)

    def test_is_credentails_error(self):
        self.assertEqual(False, self.is_credentials_error)
