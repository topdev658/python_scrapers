from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.kutxabank_scraper.kutxa_scraper import KutxaScraper

__version__ = '2.3.1'

__changelog__ = """
2.3.1
scraper name as cls attr
2.3.0
upd self.login_init_url
2.2.0
updated login_step1_url
2.1.0
pinpad_url
2.0.0
new project structure
"""


class CajasurScraper(KutxaScraper):
    """
    All functions from KutxaScraper with specific scraper name, urls and login_activador_param
    """
    scraper_name = 'CajasurScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

        self.base_url = 'https://www.cajasur.es'
        self.login_init_url = 'https://portal.cajasur.es/cs/Satellite/cajasur/es/empresas-0'
        self.login_step1_url = ('https://www.cajasur.es/NASApp/BesaideNet2/Gestor?PORTAL_CON_DCT=SI'
                                '&PRESTACION=login&FUNCION=directoportal&ACCION=control&destino=')
        self.login_activador_param = 'MP'
        self.pinpad_url = ('https://www.cajasur.es/NASApp/BesaideNet2/Gestor'
                           '?PRESTACION=login&FUNCION=login&ACCION=directoportalImage&idioma=ES&i=28')

        self.logger.info('Scraper started')
