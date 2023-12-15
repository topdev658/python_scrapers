from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.cajamar_scraper.cajamar_scraper import CajamarScraper

__version__ = '3.0.0'

__changelog__ = """
3.0.0
use CajamarScraper implemented for the new web
2.0.1
moved scraper name definition
2.0.0
new web
1.0.0
init
"""


class CaixaCallosaScraper(CajamarScraper):
    """
    All functions from Cajamar with specific scraper and req params
    """
    scraper_name = 'CaixaCallosaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.base_url = 'https://www.grupocooperativocajamar.es/'
        # self.entidad_param = '3105'
        self.entidad_param = '0000'
