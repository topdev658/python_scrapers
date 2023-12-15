import random
import time
from collections import OrderedDict
from typing import Dict

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers.ing_scraper import parse_helpers
from scrapers.ing_scraper import parse_helpers_multicontract
from scrapers.ing_scraper.ing_scraper import IngScraper

__version__ = '1.0.2'

__changelog__ = """
1.0.2
upd type hints
1.0.1
inc timeout
1.0.0
init
"""


class IngMulticontractScraper(IngScraper):
    scraper_name = 'IngMulticontractScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def process_multicontract(
            self,
            s: MySession,
            resp_logged_in: Response,
            contract_params: Dict[str, str],
            ix: int) -> bool:
        # Log in for 2nd and next contracts
        self.logger.info("Process multicontract #{}".format(ix + 1))

        if ix > 0:
            time.sleep(1.0 + random.random())
            s, resp_logged_in, is_logged, is_credentials_error = self.login()

            if not is_logged:
                self.logger.error(
                    "Can't log in to process contract #{}. Skip".format(ix)
                )
                return False

        f_param = parse_helpers.get_f_param(resp_logged_in.text, 'roleSelectionForm')
        req_url = 'https://ing.ingdirect.es/SME/Transactional/faces/views/roleSelection.xhtml?f={}'.format(f_param)

        req_headers = self.req_headers.copy()
        req_headers['Referer'] = resp_logged_in.url

        req_params = OrderedDict([
            ('org.apache.myfaces.trinidad.faces.FORM', 'roleSelectionForm'),
            ('_noJavaScript', 'false'),
            ('javax.faces.ViewState', '!3'),  # hardcoded val, always when just logged in
            ('source', contract_params['source']),
            ('corpId', contract_params['corpId']),
            ('role', contract_params['role']),
            ('indexTabCorporateHome', contract_params['indexTabCorporateHome']),
        ])

        resp_contract = s.post(
            req_url,
            data=req_params,
            headers=req_headers,
            proxies=self.req_proxies,
            timeout=20,
        )

        self.process_contract(s, resp_contract)
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)

        contracts_params = parse_helpers_multicontract.get_contracts_params(resp_logged_in.text)

        # multi-contract
        if contracts_params:
            self.view_state_param_num_start_scrape_account = 4
            for ix, contract_params in enumerate(contracts_params):
                self.process_multicontract(s, resp_logged_in, contract_params, ix)
        # one contract
        else:
            self.process_contract(s, resp_logged_in)

        self.basic_log_time_spent("GET MOVEMENTS")
        return self.basic_result_success()
