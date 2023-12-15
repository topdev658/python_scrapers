import unittest
from typing import List

from custom_libs import state_reset
from custom_libs.db import db_funcs
from custom_libs.db import queue_simple
from project import result_codes
from project import settings as project_settings
from project.custom_types import DBAccount
from project.custom_types import ScraperParamsCommon
from scrapers.banca_march_scraper.banca_march_scraper import BancaMarchScraper


def tearDownModule():
    """should be included in each ...tests.py file for graceful shutdown"""
    print('Finished tests in the module')
    queue_simple.wait_finishing()


class RollbackAccountTestCase(unittest.TestCase):
    """The scraper class and access doesn't matter.
    Better to use scrapers without js-based encrypter
    to launch the test from any place.
    Just need to extract at least 2 movement during from different dates

    We check for self.is_successful_scraping() in the beginning of each test
    to perform tests only if there were no scraping errors

    The test works with the test (prep) DB

    The aim:
    1. test all cases for 'rollback' account functionality

    Test actions:
    1. check particular access and account
    2. delete recent movements (> date_from) of the access from the DB
    3. update the balance of account
    4. scrape to date_from - here we get correct balance and movements for the date_from
    5. test_2_scrape_movements_of_dates:
        scrapes from date_from to date_to - we reproduced expected scraping job
    6. test_3_successful_movements_uploading: reproduces 'no need to rollback' case
    7. delete part of the movements to get inconsistent situation
    8. test_4_cant_rollback: reproduces "can't rollback" case
    9. delete the rest of the movements - here we return to initial state after step 4
    10. test_5_rollback: reproduces 'rollback' case and restores the account's balance and timestamps
    """

    SUCCESSFUL_SCRAPING_RESULT = (result_codes.SUCCESS, None)

    user = 226491
    access = 11121

    date_from = '01/03/2019'
    date_to = '10/03/2019'

    # If we scrape recent movements
    # and then delete them since this date
    # (the movements are partially uploaded)
    # then the scraper can't rollback
    # because it may bring inconsistency
    date_delete_since_cant_rollback = '05/03/2019'

    # If we scrape recent movements
    # and then delete them since this date
    # (no new movements in the DB)
    # then scraper rollbacks the accounts
    date_delete_since_rollback = '02/03/2019'

    # sets the proper the account balance for the main test
    scraper_to_setup_balances = BancaMarchScraper(ScraperParamsCommon(
        date_from_str='',
        date_to_str=date_from,
        db_customer=db_funcs.UserFuncs.get_user_scraping_not_in_progress(user),
        db_financial_entity_access=db_funcs.FinEntFuncs.get_financial_entity_access(access)
    ))

    scraper = BancaMarchScraper(ScraperParamsCommon(
        date_from_str=date_from,
        date_to_str=date_to,
        db_customer=db_funcs.UserFuncs.get_user_scraping_not_in_progress(user),
        db_financial_entity_access=db_funcs.FinEntFuncs.get_financial_entity_access(access)
    ))

    # Main account to test movements.
    # We expect several movements during the period.
    # db id=4503
    # last mov 01/03 temp bal = 29618.82 (add test?)
    fin_ent_account_id = 'ES3400610383750002200116'

    scraping_result = None
    accounts_before = []  # type: List[DBAccount]

    @classmethod
    def setUpClass(cls):
        print("*** Prepare the main test (set up class) ***")
        project_settings.IS_UPDATE_DB = True
        project_settings.IS_PRODUCTION_DB = False
        print('Set project_settings.IS_UPDATE_DB = True\n'
              'project_settings.IS_PRODUCTION_DB = False')

        state_reset.reset_forced(cls.user)
        cls.delete_recent_movements()
        cls.scraping_result = cls.scraper_to_setup_balances.main()

        # part of BasicScraper.scrape() method to use in tests
        cls.scraper.db_connector.update_accounts_scraping_attempt_timestamp()
        cls.accounts_before = cls.scraper.db_connector.get_accounts_saved()
        # end of part of scrape() method

    @classmethod
    def delete_recent_movements(cls):
        """Deletes already scraped movements and updates balances from the last movs"""
        print("** Prepare the balances (delete too old movements and ) **")
        db_accounts = cls.scraper.db_connector.get_accounts_saved()
        db_accounts_upd = []
        for account in db_accounts:
            fin_ent_account_id = account.FinancialEntityAccountId
            cls.scraper.db_connector.delete_movements_since_date(fin_ent_account_id, cls.date_from)
            last_mov = cls.scraper.db_connector.get_last_movement_of_account(fin_ent_account_id)
            acc = [a for a in db_accounts if a.FinancialEntityAccountId == fin_ent_account_id][0]
            acc_dict = acc._asdict()
            acc_dict['Balance'] = last_mov.TempBalance
            db_accounts_upd.append(DBAccount(**acc_dict))
        # set the balance
        cls.scraper.db_connector.accounts_rollback_ts_and_balances(db_accounts_upd)

    @classmethod
    def tearDownClass(cls):
        state_reset.reset_forced(cls.user)
        print('Finished tests for: {}'.format(cls))

    def is_successful_scraping(self) -> bool:
        return self.scraping_result == self.SUCCESSFUL_SCRAPING_RESULT

    def test_1_scrape_to_set_initial_balances(self):
        self.assertTrue(self.is_successful_scraping())

    def test_2_scrape_movements_of_dates(self):
        if self.is_successful_scraping():
            print('*** Scrape movements of dates.. ***')
            self.scraping_result = self.scraper.main()
            self.assertTrue(self.is_successful_scraping())

    def test_3_successful_movements_uploading(self):
        if self.is_successful_scraping():
            print("*** test_successful_movements_uploading ***")
            result = self.scraper._rollback_accounts(self.accounts_before)
            self.assertEqual(result, ([], [], []))

    def test_4_cant_rollback(self):
        if self.is_successful_scraping():
            print("*** test_cant_rollback ***")
            self.scraper.db_connector.delete_movements_since_date(self.fin_ent_account_id,
                                                                  self.date_delete_since_cant_rollback)
            # We expect "can't rollback" because account_before balance != last mov balance
            # This means that unexpected behavior (scraping/DB inconsistency) is detected
            # due to partial uploading or scraping attempts of the account from
            # the different contracts/companies
            (to_rollback, wrong, cant_rollback) = self.scraper._rollback_accounts(self.accounts_before)
            self.assertEqual(to_rollback, [])
            self.assertEqual(len(wrong), 1)
            self.assertEqual(len(cant_rollback), 1)

    def test_5_rollback(self):
        if self.is_successful_scraping():
            print("*** test_rollback ***")
            self.scraper.db_connector.delete_movements_since_date(self.fin_ent_account_id,
                                                                  self.date_delete_since_rollback)
            # We can rollback because account_before balance == last mov balance
            # This means we will rollback to the state before the scraping job is launched
            (to_rollback, wrong, cant_rollback) = self.scraper._rollback_accounts(self.accounts_before)
            self.assertEqual(len(to_rollback), 1)
            self.assertEqual(len(wrong), 1)
            self.assertEqual(cant_rollback, [])
