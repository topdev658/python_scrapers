from project import settings as project_settings
from project.custom_types import ScraperParamsCommon

from scrapers.santander_scraper.santander_empresas_scraper_receipts__nuevo import (
    SantanderEmpresasNuevoReceiptsScraper
)
from .popular_scraper import PopularScraper

__version__ = '1.0.1'

__changelog__ = """
1.0.1
redefined _product_to_fin_ent_id
1.0.0
init
"""


class PopularReceiptsScraper(PopularScraper, SantanderEmpresasNuevoReceiptsScraper):
    """
    All functions from PopularScraper, then from SantanderEmpresasNuevoN43Scraper
    """

    scraper_name = 'PopularReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')

    @staticmethod
    def _product_to_fin_ent_id(product_id: str) -> str:
        """For POPULAR correspondence
        ES6800496738531030617076 -> ES6800496738531030617076
        """
        return product_id
