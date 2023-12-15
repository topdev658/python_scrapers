from typing import Tuple
from project import settings as project_settings
from .santander_empresas_scraper import SantanderEmpresasScraper
from .santander_empresas_n43_scraper__nuevo import SantanderEmpresasNuevoN43Scraper
from project.custom_types import ScraperParamsCommon
from custom_libs.myrequests import MySession, Response

__version__ = '1.0.0'
__changelog__ = """
1.0.0
init
"""


class SantanderEmpresasN43Scraper(SantanderEmpresasNuevoN43Scraper):
    """
    Uses:
        - all methods except login() from SantanderEmpresasNuevoN43Scraper
        - login() method from SantanderEmpresasScraper (old web)
    """
    scraper_name = 'SantanderEmpresasN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.__oldweb_scraper = SantanderEmpresasScraper(scraper_params_common, proxies=proxies)

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        return self.__oldweb_scraper.login()
