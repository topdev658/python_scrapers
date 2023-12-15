from typing import List

from custom_libs.myrequests import Response
from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon)
from scrapers.sabadell_miami_scraper.sabadell_miami_scraper import SabadellMiamiScraper
from . import parse_helpers

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class SabadellUKScraper(SabadellMiamiScraper):
    scraper_name = 'SabadellUKScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.base_url = 'https://www.bancosabadelluk.com/txempbsl/'
        self.init_url = 'https://www.bancosabadelluk.com/cs/Satellite/BancoSabadellUK/Companies/4000000966702/es/'
        self.req_param_date_fmt = '%d/%m/%Y'
        self.movement_date_fmt = '%d/%m/%Y'
        self.country_code = 'GBR'

    def _get_accounts_parsed_wo_balance_from_dropdown(self, resp_accounts: Response) -> List[dict]:
        accounts_parsed_wo_balance = parse_helpers.get_accounts_parsed_wo_balance(resp_accounts.text)
        return accounts_parsed_wo_balance
