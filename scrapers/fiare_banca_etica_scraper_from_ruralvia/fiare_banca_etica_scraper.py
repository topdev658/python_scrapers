from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '1.1.0'

__changelog__ = """
1.1.0
custom login_init_url, domain, certs
1.0.1
fmt
1.0.0
init
"""


class FiareBancaEticaScraper(RuralviaScraper):
    """
    all functions from RuralviaScraper with specific scraper's name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='FiareBancaEticaScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.login_init_url = 'https://www.fiarebancaetica.coop/'
        self.domain = 'https://accesoclientes.fiarebancaetica.coop/'
        # Similar to pichincha
        self.ssl_cert_init = False
        self.ssl_cert = False
        self.logger.info('Scraper started')
