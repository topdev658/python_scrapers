from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '1.0.1'

__changelog__ = """
1.0.1
optimize imports
1.0.0
init
"""


class BancoCooperativoScraper(RuralviaScraper):
    """
    Basic functions from RuralviaScraper
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BancoCooperativoScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.logger.info('Scraper started')
