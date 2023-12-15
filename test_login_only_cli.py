"""
Usage:
python3 test_login_only_cli.py -s AbancaScraper -u 209470 -a 10109
"""

import sys
import unittest

# mostly for scraper classes
from main_launcher import *  # noqa
from scrapers.arquiabanca_scraper.arquiabanca_scraper import ArquiaBancaRedScraper  # noqa
from scrapers.bbva_scraper.bbva_scraper import BBVANetcashScraper  # noqa
from scrapers.santander_scraper.santander_scraper import (
    SantanderEmpresasNuevoScraper,
    SantanderEmpresasScraper,
    SantanderParticularesScraper,
    SantanderScraper
) # noqa
from scrapers.bbva_scraper.bbva_scraper import BBVAParticularesScraper  # noqa
from scrapers.santander_brasil_scraper.santander_brasil_default_scraper import SantanderBrasilDefaultScraper  # noqa

from tests.helpers import test_helpers
from tests.helpers.login_only_test_case import LoginOnlyTestCase

__version__ = '1.1.1'
__changelog__ = """
1.1.1
comment
1.1.0
explicit exit status 1 if failed
"""


def parse_cmdline_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--scraper-class',
        '-s',
        help='Specify the scraper class (e.g. AbancaScraper, BancaMarchScraper)',
        type=str
    )

    parser.add_argument(
        '--user-id',
        '-u',
        help='Scrape specific customer: user Id. '
             'If not passed: the all_customers_scraping will start if allowed in settings',
        type=int
    )
    parser.add_argument(
        '--access-id',
        '-a',
        help='Scrape specific financial entity access Id of the user from "user-id" argument '
             'If not passed: all fin ent accesses will be scraped',
        type=int
    )

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    try:
        cli_args = parse_cmdline_args()
        print('Start the test with args {}'.format(cli_args))

        # Dangerous. Use only in trusted env
        # TODO check the cli_args.scraper_class string
        scraper_class = eval(cli_args.scraper_class)

        print('Got scraper {}'.format(scraper_class.__name__))

        scraper = test_helpers.new_scraper_for_tests(
            scraper_class,
            customer_id=cli_args.user_id,
            fin_ent_access_id=cli_args.access_id
        )
        # Here we set the specific instance of scraper
        LoginOnlyTestCase.scraper = scraper

        # And launching the test
        suite = unittest.TestLoader().loadTestsFromTestCase(LoginOnlyTestCase)
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        sys.exit(not result.wasSuccessful())

    finally:
        queue_simple.wait_finishing()
