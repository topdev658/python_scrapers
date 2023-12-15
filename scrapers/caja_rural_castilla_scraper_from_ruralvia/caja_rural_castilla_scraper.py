from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers.eurocaja_rural_scraper_from_ruralvia.eurocaja_rural_scraper import EurocajaRuralScraper

__version__ = '3.0.1'

__changelog__ = """
3.0.1
fmt
3.0.0
inherits EurocajaRuralScraper
2.0.0
new project structure
"""


class CajaRuralCastillaScraper(EurocajaRuralScraper):
    """
    All functions from EurocajaRuralScraper with specific scraper's name
    """

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='CajaRuralCastillaScraper') -> None:
        super().__init__(scraper_params_common, proxies, scraper_name)
