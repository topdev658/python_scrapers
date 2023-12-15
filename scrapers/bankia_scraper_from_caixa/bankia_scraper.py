from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountScraped, AccountParsed
from scrapers.caixa_scraper.caixa_regular_scraper import CaixaScraper

__version__ = '1.1.0'

__changelog__ = """
1.1.0
use _update_related_account_info
1.0.0
init
"""


class BankiaScraper(CaixaScraper):
    """
    All functions from CaixaScraper
    with specific scraper's name
    """

    scraper_name = 'BankiaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')

    def _get_username(self) -> str:
        if self.access_type == 'Contrato':
            # '0001' + Nº de Contrato
            return self.username + self.username_second
        elif self.access_type == 'Seudónimo':
            return self.username
        raise NotImplementedError

    def _update_related_account_info(
            self,
            account_scraped: AccountScraped,
            account_parsed: AccountParsed) -> bool:
        """CaixaFromBnkia accounts have information about BankiaAccount
        by account_alias - it contains part of the former account_no
        """
        bankia_related_account_info = account_parsed.get('account_alias', '')
        self.basic_update_related_account_info(
            account_scraped,
            bankia_related_account_info
        )
        return True

    @staticmethod
    def _get_fin_ent_account_id(account_parsed: dict) -> str:
        """ES6800496738531030617076 -> 00496738531030617076"""
        account_no = account_parsed['account_no']
        if not account_no:
            return ''  # will be handled by the scraper
        assert len(account_no) == 24
        return account_parsed['account_no'][4:]
