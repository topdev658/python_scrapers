from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper

__version__ = '2.0.1'

__changelog__ = """
2.0.1
fmt
2.0.0
new project structure
"""


class BantierraScraper(RuralviaScraper):
    """
    all functions from RuralviaScraper with specific scraper's name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BantierraScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
        self.logger.info('Scraper started')
