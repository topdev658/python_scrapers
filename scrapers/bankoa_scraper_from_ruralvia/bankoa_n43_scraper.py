from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.ruralvia_scraper.ruralvia_n43_scraper import RuralviaN43Scraper
from .bankoa_scraper import BankoaScraper

__version__ = '2.0.0'

__changelog__ = """
2.0.0
inherit from BankoaScraper and RuralviaN43Scraper
1.0.0
stable
init
login
"""


class BankoaN43Scraper(BankoaScraper, RuralviaN43Scraper):
    """
    all functions from RuralviaScraper with specific scraper's name
    """
    fin_entity_name = 'BANKOA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankoaN43Scraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
