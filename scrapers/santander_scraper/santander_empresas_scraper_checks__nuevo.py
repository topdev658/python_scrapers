from typing import List, Tuple

from project import settings as project_settings
from project.custom_types import (
    CheckParsed, AccountScraped, MovementScraped, ScraperParamsCommon
)
from . import checks_helpers
from .santander_empresas_scraper__nuevo import SantanderEmpresasNuevoScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
inherit from SantanderOrgWFilialesScraper instead of SantanderOrgWFilialesNuevoLoginScraper
use checks_helpers
"""


class SantanderEmpresasNuevoChecksScraper(SantanderEmpresasNuevoScraper):
    scraper_name = 'SantanderEmpresasNuevoChecksScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def download_checks(
            self,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped]) -> Tuple[bool, List[CheckParsed]]:
        return checks_helpers.download_checks(
            self,
            account_scraped,
            movements_scraped
        )
