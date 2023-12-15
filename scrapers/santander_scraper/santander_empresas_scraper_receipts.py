from typing import List, Tuple

from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MovementParsed, MovementScraped,
    ScraperParamsCommon
)
from . import receipts_helpers
from .santander_empresas_scraper import SantanderEmpresasScraper

__version__ = '1.1.0'
__changelog__ = """
1.1.0
_product_to_fin_ent_id (similar to SantanderEmpresasNuevoReceiptsScraper)
  to use in receipts_helpers
1.0.0
init
"""


class SantanderEmpresasReceiptsScraper(SantanderEmpresasScraper):
    """
    Implements download_receipts
    """

    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    scraper_name = 'SantanderEmpresasReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.is_receipts_scraper = True

    @staticmethod
    def _product_to_fin_ent_id(product_id: str) -> str:
        """For correspondence
        ES6800496738531030617076 -> 0049 6738 51 2516180464
        """
        if not product_id:
            return ''
        return '{} {} {} {}'.format(
            product_id[-20:-16],
            product_id[-16:-12],
            product_id[-12:-10],
            product_id[-10:]
        )

    def download_receipts(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            account_parsed: AccountParsed,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed]) -> Tuple[bool, List[MovementScraped]]:
        return self.basic_download_receipts_common(
            s,
            account_scraped,
            movements_scraped,
            movements_parsed,
            meta={'scraper': self, 'account_parsed': account_parsed}
        )

    def download_movement_receipt(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> str:
        return receipts_helpers.download_movement_receipt(
            s,
            account_scraped,
            movement_scraped,
            movement_parsed,
            meta
        )
