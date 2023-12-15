from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.santander_scraper.santander_empresas_n43_scraper__nuevo import SantanderEmpresasNuevoN43Scraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class PopularN43Scraper(SantanderEmpresasNuevoN43Scraper):
    """
    All functions from SantanderEmpresasNuevoN43Scraper
    with specific scraper's name
    """

    scraper_name = 'PopularN43Scraper'


    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')
