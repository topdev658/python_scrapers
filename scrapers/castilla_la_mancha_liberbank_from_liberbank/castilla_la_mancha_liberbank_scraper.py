from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.liberbank_scraper.liberbank_scraper import LiberbankScraper

__version__ = '4.0.1'

__changelog__ = """
4.0.1
fmt
4.0.0
all functions from LiberbankScraper
removed unused
3.1.0
more 'credentials error' markers
3.0.0
new project structure
2.0.0
parse movements from excel in basic scraper
1.1.1
remove unused
1.1.0
use self._get_movements_parsed() instead of self.get_movements_parsed_func
1.0.0
basic impl
"""


class CastillaLaManchaLiberbankScraper(LiberbankScraper):
    """
    All functions from LiberbankScraper with redefined
        self.scraper_name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        self.scraper_name = 'CastillaLaManchaLiberbankScraper'
        super().__init__(scraper_params_common, proxies)
