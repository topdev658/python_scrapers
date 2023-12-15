import random
import time
import urllib.parse
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import (MOVEMENTS_ORDERING_TYPE_ASC, MovementParsed,
                                  ScraperParamsCommon, MainResult)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.popular_dominicano_scraper import parse_helpers

__version__ = '1.4.0'
__changelog__ = """
1.4.0
extra delay for reqs
only confirmed proxies
has_failed_accounts
conditional basic_result_common_scraping_error
1.3.0
call basic_upload_movements_scraped with date_from_str
1.2.0
use basic_new_session
upd type hints
fmt
1.1.0
MAX_CONCURRENT_WORKERS = 1
Check later, maybe some IPs were banned due to concurrent processing, prevent new bans
1.0.0
init
"""

REQUEST_FAILED_MARKERS = [
    'En estos momentos su requerimiento no pudo ser atendido. Por favor trate más tarde',
    'temporarily unavailable'
]

CREDENTIALS_ERROR_MARKER = 'Confirme su usuario y contraseña y digítelos nuevamente'

MAX_CONCURRENT_WORKERS = 1


class PopularDominicanoScraper(BasicScraper):
    scraper_name = 'PopularDominicanoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        # Manually confirmed proxies (scraped w/o Incapsula)
        self.req_proxies = self.req_proxies[:3]
        # As process_account can be interrupted before parsed fin_ent_account_id
        # then we'll use access-level flag for final result code (bcs account will get WRN_STATE_RESET)
        self.has_failed_accounts = False

    def _delay(self):
        time.sleep(0.5 + random.random())

    def _req_get_w_attempts(self, s: MySession, url: str,
                            req_params: Optional[Dict[str, str]] = None,
                            failure_msg: str = '') -> Tuple[bool, MySession, Response]:
        """Checks resp for REQUEST_FAILED_MARKERS and retries if necessary.
        Useful for concurrent processing.

        :returns (is_success, myrequests.Session, myrequests.Response)"""
        resp = Response()
        for i in range(1, 6):
            resp = s.get(url, params=req_params,
                         headers=self.req_headers,
                         proxies=self.req_proxies)

            if not any(marker in resp.text for marker in REQUEST_FAILED_MARKERS):
                # success by text markers
                return True, s, resp

            self.logger.warning('{}: failed attempt #{} for url {}. Repeat'.format(failure_msg, i, url))
            self._delay()

        self.logger.error("{}: failed for url {}. Skip.\nRESPONSE:\n{}".format(failure_msg, url,
                                                                               resp.text))
        return False, s, resp

    def login(self) -> Tuple[MySession, Response, bool, bool]:
        s = self.basic_new_session()
        resp_init = s.get(
            'https://www.popularenlinea.com/personas/Paginas/Home.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        resp_params = OrderedDict([
            ('fldEmpresaParam', self.username),
            ('fldNombreParam', self.username_second),
            ('fldPasswordParam', self.userpass)
        ])

        resp_logged_in = s.post(
            'https://www.bpd.com.do/banco.popular.aspx?Login',
            data=resp_params,
            headers=self.req_headers,
            proxies=self.req_proxies

        )
        # Buenos Dias or Buenas Tardes
        is_logged = all(marker in resp_logged_in.text for marker in ('Buen', 'Salir'))
        is_credentials_error = CREDENTIALS_ERROR_MARKER in resp_logged_in.text

        return s, resp_logged_in, is_logged, is_credentials_error

    def process_company(self, s: MySession, resp_logged_in: Response) -> bool:
        account_details_urls = parse_helpers.get_account_details_urls(resp_logged_in.text,
                                                                      resp_logged_in.url)

        organization_title = parse_helpers.get_organization_title(resp_logged_in.text)

        self.logger.info("Company '{}' has {} accounts".format(organization_title,
                                                               len(account_details_urls)))
        # should process each account to get IBAN
        for acc_url in account_details_urls:
            ok = self.process_account(s, acc_url, organization_title)
            if not ok:
                self.has_failed_accounts = True
        return True

    def process_account(self, s: MySession, account_details_url: str, organization_title: str) -> bool:

        # 1st get account_scraped.
        # It is possible to get account_no only form details page
        self._delay()
        self.logger.info('Process account for {}'.format(account_details_url))
        ok, s, resp_account_details = self._req_get_w_attempts(
            s,
            account_details_url,
            failure_msg="can't open resp_account_details"
        )
        if not ok:
            # can't call set_movements_scraping_finished bcs fin_ent_account_id is unknonw
            return False

        ok, account_parsed = parse_helpers.get_account_parsed(resp_account_details.text, self.logger)
        if not ok:
            # can't call set_movements_scraping_finished bcs fin_ent_account_id is unknonw
            return False

        account_scraped = self.basic_account_scraped_from_account_parsed(
            organization_title,
            account_parsed,
            country_code=account_parsed['country_code'],
            account_no_format=account_parsed['account_no_format']
        )

        self.logger.info('Got account {} from details page {}'.format(
            account_scraped,
            account_details_url
        ))

        self.basic_upload_accounts_scraped([account_scraped])
        self.basic_log_time_spent('{}: GET BALANCE'.format(account_scraped.FinancialEntityAccountId))

        # 2nd get movements
        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # expect
        # req_movs_params = OrderedDict([
        #     ('_SOURCESCREEN', ''),
        #     ('nfm', '2'),
        #     ('pID', req_movs_params_raw['pID']),  # 489...515 (114 chars)
        #     ('f', req_movs_params_raw['f']),  # 321...445 (69 chars)
        #     ('isGet', '1'),
        #     ('_SmallAmt', ''),
        #     ('_BigAmt', ''),
        #     ('_RefNum', ''),
        #     ('SerialNum', ''),
        #     ('_Type', '3'),
        #     ('_View', ''),
        #     ('_STARTDATE', '03/01/2019'),
        #     ('_ENDDATE', '08/02/2019')
        # ])
        _, req_movs_params = extract.build_req_params_from_form_html_patched(
            resp_account_details.text,
            'DatesForm',
            is_ordered=True
        )

        req_movs_params['_STARTDATE'] = date_from_str  # '03/01/2019'
        req_movs_params['_ENDDATE'] = self.date_to_str  # '08/02/2019'

        movements_parsed_asc = []  # type: List[MovementParsed]

        req_movs_url = 'https://www.bpd.com.do/banco.popular.aspx'

        # loop for pagination
        # some accounts returns all movements at one page (usd) but some paginated (dop)
        page = 1
        while True:
            self.logger.info('{}: open movements_filtered page {}'.format(
                fin_ent_account_id,
                page
            ))

            failure_msg = "{}: page {}: can't open resp_movements_filtered with params {}".format(
                fin_ent_account_id,
                page,
                req_movs_params
            )
            ok, s, resp_movs_filtered = self._req_get_w_attempts(
                s,
                req_movs_url,
                req_params=req_movs_params,
                failure_msg=failure_msg
            )
            if not ok:
                self.basic_set_movements_scraping_finished(fin_ent_account_id, result_codes.ERR_UNEXPECTED_RESPONSE)
                return False

            movements_parsed_from_page_asc = parse_helpers.get_movements_parsed(
                resp_movs_filtered.text,
                self.logger
            )

            movements_parsed_asc += movements_parsed_from_page_asc
            # has pagination
            if any(marker in resp_movs_filtered.text for marker in ('Página', 'P&aacute;gina')):
                req_movs_next_page_link = parse_helpers.get_page_link(resp_movs_filtered.text, page + 1)
                if not req_movs_next_page_link:
                    # no more pages
                    break
                req_movs_params = OrderedDict(
                    urllib.parse.parse_qsl(req_movs_next_page_link.split('?')[1], True)
                )
                self._delay()
                page += 1
                continue

            # no pagination
            break

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed_asc,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str,
                                       movements_scraped=movements_scraped,
                                       date_to_str=self.date_to_str)

        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url,
                                                                      resp_logged_in.text)

        self.process_company(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')

        if self.has_failed_accounts:
            return self.basic_result_common_scraping_error()

        return self.basic_result_success()
