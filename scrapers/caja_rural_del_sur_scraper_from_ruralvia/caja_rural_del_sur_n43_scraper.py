from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_n43_scraper import RuralviaN43Scraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class CajaRuralDelSurN43Scraper(RuralviaN43Scraper):
    """
    all functions from RuralviaScraper with specific scraper's name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='CajaRuralDelSurN43Scraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.logger.info('Scraper started')
