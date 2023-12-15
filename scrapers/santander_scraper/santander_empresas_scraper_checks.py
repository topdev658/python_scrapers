from typing import List, Tuple

from project import settings as project_settings
from project.custom_types import (
    CheckParsed, AccountScraped, MovementScraped, ScraperParamsCommon
)
from . import checks_helpers
from .santander_empresas_scraper import SantanderEmpresasScraper

__version__ = '2.0.0'

__changelog__ = """
2.0.0
inherit from SantanderOrgWFilialesScraper instead of SantanderOrganizationsScraper
use checks_helpers
1.1.0
DAF:
Now we use new basic_save_check_collection to transactional insert check collection operation
_delete_check_collections_without_movement_id removed
save_collection_checks removed
1.0.1
fixed save_collection_checks: was basic_basic_check_scraped_from_check_parsed (double 'basic')
1.0.0
DAF: init
parse_helpers.get_check_data_from_extended_description
"""


class SantanderEmpresasChecksScraper(SantanderEmpresasScraper):
    scraper_name = 'SantanderEmpresasChecksScraper'

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
