from project import settings as project_settings
from project.custom_types import ScraperParamsCommon

from scrapers.caixa_scraper.caixa_regular_receipts_scraper import CaixaReceiptsScraper
from .bankia_scraper import BankiaScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class BankiaReceiptsScraper(BankiaScraper, CaixaReceiptsScraper):
    """
    All functions from BankiaScraper, then from CaixaReceiptsScraper
    """

    scraper_name = 'BankiaReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')

    @staticmethod
    def _product_to_fin_ent_id(product_id: str) -> str:
        """For BANKIA correspondence
        ES6800496738531030617076 -> 00496738531030617076
        """
        assert len(product_id) == 24
        return product_id[4:]
