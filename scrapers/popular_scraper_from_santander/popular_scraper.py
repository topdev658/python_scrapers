from typing import List, Tuple

from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, AccountParsed
from scrapers.santander_scraper.santander_empresas_scraper__nuevo import (
    SantanderEmpresasNuevoScraper
)

__version__ = '1.2.0'

__changelog__ = """
1.2.0
_get_accounts_parsed: upd due to changes method of parent SantanderEmpresasNuevoScraper
1.1.1
parse helpers: use correct parse_helpers_santander_nuevo
1.1.0
inherit renamed SantanderEmpresasNuevoScraper
1.0.0
init
"""


class PopularScraper(SantanderEmpresasNuevoScraper):
    """
    All functions from SantanderOrgWFilialesNuevoLoginScraper
    with specific scraper's name
    """

    scraper_name = 'PopularScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.logger.info('Scraper started')

    def _get_accounts_parsed(self, s: MySession, org_title: str) -> Tuple[bool, List[AccountParsed]]:
        ok, accounts_parsed = super()._get_accounts_parsed(s, org_title)
        if not ok:
            return False, []  # already reported
        # Mutate each account_parsed
        # for back comp with prev Popular format
        for acc in accounts_parsed:
            acc['financial_entity_account_id'] = acc['account_no']
        return True, accounts_parsed

