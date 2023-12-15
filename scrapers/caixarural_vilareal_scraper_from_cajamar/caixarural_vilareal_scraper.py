from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.cajamar_scraper.cajamar_scraper import CajamarScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class CaixaRuralVilarealScraper(CajamarScraper):
    """
    All functions from Cajamar with specific scraper and req params
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        self.scraper_name = 'CaixaRuralVilarealScraper'
        super().__init__(scraper_params_common, proxies)

        self.base_url = 'https://www.grupocooperativocajamar.es/'
        self.entidad_param = '3110'

        # NOTE THE WEB LOGIN REQ
        # contains additional params
        # but if use it then scraping process
        # will fail after successful login step
        # because will be redirected to another ui
        # SO, just use defaults

        # self.custom_login_req_params = {
        #     'LOCHUA': 'Fire#56#1366#0768',
        #     'OPER': '0',
        #     'VERSION': '2',
        #     'ZKENABLED': 'true'
        # }

        self.logger.info('Scraper started')
