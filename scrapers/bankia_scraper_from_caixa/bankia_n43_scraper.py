from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.caixa_scraper.caixa_n43_scraper import CaixaN43Scraper
from .bankia_scraper import BankiaScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class BankiaN43Scraper(BankiaScraper, CaixaN43Scraper):
    """
    All functions from BankiaScraper, then from CaixaN43Scraper
    """

    scraper_name = 'BankiaN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')
