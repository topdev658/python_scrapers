import random
import time
import datetime
from collections import OrderedDict
from typing import List, Dict

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped, AccountParsed

from .laboral_kutxa__banca_online_scraper import LaboralKutxaBancaOnlineScraper


__version__ = '3.2.0'

__changelog__ = """
3.2.0 2023.04.04
process_account: used UTC datetime at POST request parameters, to emulate web behaviour
3.1.0
process_account: used 1 day less for dates at POST request parameters, to emulate web behaviour
3.0.0
refactor file name from laboral_kutxa_n43_scraper.py
2.0.0
multi-contract support (by parent)
process_account:
    new func signature 
    use position_id_param
1.0.0
init
"""


class LaboralKutxaN43BancaOnlineScraper(LaboralKutxaBancaOnlineScraper):
    fin_entity_name = 'LABORAL_KUTXA'
    scraper_name = 'LaboralKutxaN43BancaOnlineScraper'


    def __init__(self,
                     scraper_params_common: ScraperParamsCommon,
                     proxies=project_settings.DEFAULT_PROXIES) -> None:
            super().__init__(scraper_params_common, proxies)
            self.access_id = ''
            self.n43_contents = []

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]) -> None:
        # No need to save accounts_scraped by parent's process_access, do nothing
        return

    def process_account(
            self,
            s: MySession,
            lkid_param: str,
            accounts_scraped_dict: Dict[str, AccountScraped],
            account_parsed: AccountParsed) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']
        account_scraped = accounts_scraped_dict[fin_ent_account_id]

        # Don't process if already got errors for previous accounts
        if not self.is_success:
            return False

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        fin_ent_account_id_for_n43_dates = account_scraped.AccountNo[4:]

        # VB: possible err: date_to > max_allowed_date by the website
        # in this case need to change date calculation approach
        # (see dev_n43/30_resp_contaning_n43_err.json)
        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id_for_n43_dates
        )

        if not is_active_account:
            time.sleep(1.0 + random.random())
            return True  # already reported

        self.logger.info('{}: process_account for N43 from {} to {}'.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        req_n43_url = 'https://lkweb.laboralkutxa.com/srv/api/cuentas/{}/movimientos/aeb43'.format(
            account_parsed['position_id_param']
        )

        # Web uses UTC datetime params for POST request
        # SUMMER: WEB DATE SELECTOR -> POST REQUEST PARAMS
        #  Desde 06/03/2023 -> fechaDesde: 2023-03-05T22:00:00.000Z
        #  Hasta 06/03/2023 -> fechaHasta: 2023-03-05T22:00:00.000Z
        # WINTER: WEB DATE SELECTOR -> POST REQUEST PARAMS
        #  Desde 06/03/2023 -> fechaDesde: 2023-03-05T23:00:00.000Z
        #  Hasta 06/03/2023 -> fechaHasta: 2023-03-05T23:00:00.000Z
        now_timestamp = time.time()
        offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
        date_from_for_filter = date_from - offset
        date_to_for_filter = date_to - offset
        # If UTC datetime is not specified, returns file without movements of last day
        req_filter_n43_params = OrderedDict([
            ('fechaDesde', '{}T{}:00:00.000Z'.format(date_from_for_filter.strftime('%Y-%m-%d'), date_from_for_filter.hour)),  # 2021-04-26T22:00:00.000Z
            ('fechaHasta', '{}T{}:00:00.000Z'.format(date_to_for_filter.strftime('%Y-%m-%d'), date_to_for_filter.hour)),  # 2021-06-23T22:00:00.000Z
            ('id', account_parsed['position_id_param']),
        ])

        self.logger.info('{}: dates for POST request from {} to {} to avoid files without movements'.format(
            fin_ent_account_id,
            req_filter_n43_params['fechaDesde'],
            req_filter_n43_params['fechaHasta'],
        ))

        # see 20_resp_n43_as_json.json
        resp_containing_n43 = s.post(
            req_n43_url,
            data=req_filter_n43_params,
            headers=self.basic_req_headers_updated({
                'origen': 'web',
                'lkid': lkid_param,
            }),
            proxies=self.req_proxies,
        )

        try:
            n43_text = resp_containing_n43.json().get('aeb43', '')
        except Exception as _e:
            self.basic_log_wrong_layout(
                resp_containing_n43,
                "{}: got invalid resp_containing_n43 (not a JSON response)".format(fin_ent_account_id)
            )
            self.is_success = False
            return False

        n43_content = n43_text.encode('UTF-8')

        if not (n43_text and n43_funcs.validate(n43_content)):
            self.basic_log_wrong_layout(
                resp_containing_n43,
                "{}: got invalid resp_containing_n43 (wrong N43 content)".format(fin_ent_account_id)
            )
            self.is_success = False
            return False

        if not n43_funcs.validate_n43_structure(n43_text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    fin_ent_account_id,
                    resp_containing_n43.text
                )
            )
            # Still True to allow download other files, because it's not a scraping error
            return True

        self.n43_contents.append(n43_content)
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, lkid_param, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_access(s, lkid_param)

        self.basic_log_time_spent('GET N43')

        if not self.is_success:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
