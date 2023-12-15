from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.abanca_scraper.abanca_beabanca_scraper import AbancaBeAbancaScraper

__version__ = '1.2.0'

__changelog__ = """
1.2.0
renamed abanca to beabanca
1.1.0
self.must_use_username_second property
1.0.0
init
"""


class CaixaGeralScraper(AbancaBeAbancaScraper):
    """All functions from AbancaScraper with a specific scraper name"""

    scraper_name = 'CaixaGeralScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.must_use_username_second = True
        self.logger.info('Scraper started')
