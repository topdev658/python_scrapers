from .cajasur_scraper import CajasurScraper
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.kutxabank_scraper.kutxa_n43_scraper import KutxaN43Scraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class CajasurN43craper(CajasurScraper, KutxaN43Scraper):
    scraper_name = 'CajasurN43craper'
    fin_entity_name = 'CAJASUR'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

