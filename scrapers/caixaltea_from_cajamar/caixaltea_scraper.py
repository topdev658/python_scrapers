from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.cajamar_scraper.cajamar_scraper import CajamarScraper

__version__ = '1.2.0'

__changelog__ = """
1.2.0
ssl_cert = True
1.1.0
custom ssl_cert
1.0.0
init
"""


class CaixAlteaScraper(CajamarScraper):
    """
    All functions from Cajamar with specific scraper and req params
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        self.scraper_name = 'CaixAlteaScraper'
        super().__init__(scraper_params_common, proxies)

        self.base_url = 'https://www.grupocooperativocajamar.es/'
        self.entidad_param = '3045'
        self.ssl_cert = True

        self.logger.info('Scraper started')
