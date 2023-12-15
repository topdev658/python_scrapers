from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.popular_scraper.popular_scraper import PopularScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class PastorScraper(PopularScraper):
    """
    All functions from Popular with specific scraper name and basic urls
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        self.scraper_name = 'PastorScraper'
        super().__init__(scraper_params_common, proxies)

        self.base_url = 'https://www2.bancopastor.es/'
        self.login_url_prefix = 'https://www2.bancopastor.es/eai_logon_pastor/'

        self.logger.info('Scraper started')
