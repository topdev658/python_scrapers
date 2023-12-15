from typing import Dict, Type

from custom_libs.db import db_funcs
from project.custom_types import ScraperParamsCommon
from scrapers._basic_scraper.basic_scraper import BasicScraper


class DummyScraper:
    scraper_name = 'DummyScraper'

    def __init__(self):
        print('!!! Replaced by DummyScraper: user/access not found !!!')

    def login(self):
        return None, None, False, False


def uploaded_accounts_num(scraper: BasicScraper) -> int:
    """The number of uploaded accounts (count)"""
    return len(db_funcs.AccountFuncs.get_accounts(scraper.db_financial_entity_access_id))


def uploaded_movements_num(scraper: BasicScraper) -> int:
    """The number of uploaded movements (count)"""
    accounts = db_funcs.AccountFuncs.get_accounts(scraper.db_financial_entity_access_id)
    movements_count_real = 0
    for account in accounts:
        movements = db_funcs.MovementFuncs.get_movements_since_date(
            account.FinancialEntityAccountId,
            scraper.db_customer_id,
            scraper.date_from_param_str
        )
        movements_count_real += len(movements)
    return movements_count_real


def uploaded_movements_per_account_num(scraper: BasicScraper) -> Dict[str, int]:
    """The number of uploaded movements (count) per account
    :return: dict {fin_ent_acc_id: movs_num}
    """
    accounts = db_funcs.AccountFuncs.get_accounts(scraper.db_financial_entity_access_id)
    movs_count_real_dict = {}
    for account in accounts:
        movements = db_funcs.MovementFuncs.get_movements_since_date(
            account.FinancialEntityAccountId,
            scraper.db_customer_id,
            scraper.date_from_param_str
        )
        movs_count_real_dict[account.FinancialEntityAccountId] = len(movements)
    return movs_count_real_dict


def new_scraper_for_tests(scraper_class: Type[BasicScraper],
                          customer_id: int,
                          fin_ent_access_id: int,
                          date_from: str = '',
                          date_to: str = ''):
    db_customer = db_funcs.UserFuncs.get_user_scraping_not_in_progress(customer_id)
    db_financial_entity_access = db_funcs.FinEntFuncs.get_financial_entity_access(
        fin_ent_access_id
    )
    scraper_params = ScraperParamsCommon(
        date_from_str=date_from,
        date_to_str=date_to,
        db_customer=db_customer,
        db_financial_entity_access=db_financial_entity_access
    )

    scraper = (scraper_class(scraper_params)
               if all([db_customer, db_financial_entity_access])
               else DummyScraper())

    return scraper
