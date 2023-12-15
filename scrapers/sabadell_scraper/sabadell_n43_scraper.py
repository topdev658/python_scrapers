import random
import time
from collections import OrderedDict
from typing import Tuple

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from .custom_types import AccountFromDropdown
from .sabadell_scraper import SabadellScraper

__version__ = '2.1.0'
__changelog__ = """
2.1.0
increased timeouts (for files with many movs)
2.0.1
restored init
2.0.0
upd init, scraper_name as cls prop
1.6.1
n43_contents: handle non-ascii symbols
1.6.0
process_account_n43: check for movements during the dates (to avoid further err resps)  
1.5.1
process_account_n43: correct date_to (instead of self.date_to)
1.5.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
1.4.0
use basic_save_n43s
1.3.0
use basic_scrape_for_n43
self.fin_entity_name
1.2.1
upd log msg
1.2.0
use basic_get_n43_dates_and_account_status
1.1.0
process_account_n43: detect 'no data' for dates
1.0.0
init
"""


class SabadellN43Scraper(SabadellScraper):
    """The scraper tries to use nuevo access type for
    any access types of Santander accesses.

    It saves N43 docs only of all data were successfully scraped.
    """
    scraper_name = 'SabadellN43Scraper'
    fin_entity_name = 'SABADELL'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

    def process_company(self, s: MySession, resp: Response) -> bool:
        """Overrides"""
        # ok, s, accounts_scraped = self.get_accounts_scraped(s, resp)
        # if not ok:
        #     # already reported
        #     return False

        s, accounts_from_dropdown = self._get_accounts_from_dropdown(s)
        self.logger.info('accounts {}'.format(accounts_from_dropdown))

        for account_from_dropdown in accounts_from_dropdown:
            ok, s = self.process_account_n43(
                s,
                resp,
                account_from_dropdown,
            )
            if not ok:
                return False
            time.sleep(0.1)
        return True

    def process_account_n43(
            self,
            s: MySession,
            resp_prev: Response,
            account_from_dropdown: AccountFromDropdown) -> Tuple[bool, MySession]:
        fin_ent_account_id = account_from_dropdown.account_no  # the same

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )
        if not is_active_account:
            return True, s  # already reported

        date_fmt = '%d/%m/%Y'
        date_from_str = date_from.strftime(date_fmt)
        date_to_str = date_to.strftime(date_fmt)
        day_from, month_from, year_from = date_from_str.split('/')
        day_to, month_to, year_to = date_to_str.split('/')

        # open page with filter, can do mov request only from this page
        # https://www.bancsabadell.com/txempbs/CUMovementsQuery.init.bs?key=E71DB0013187437951606774246948
        # https://www.bancsabadell.com/txempbs/CUMovementsQuery.init.bs?key=E71DB007169074711606773492468
        # https://www.bancsabadell.com/txempbs/CUMovementsQuery.init.bs?key=E71DB0020642387801606772441916
        key = self._get_random_key(s)
        s, resp = self._req_get(
            s,
            'https://www.bancsabadell.com/txempbs/CUMovementsQuery.init.bs?key={}'.format(key)
        )

        req_movs_filtered_params = self._req_movs_filter_params(
            account_from_dropdown,
            date_from_str,
            date_to_str
        )
        req_movs_filtered_url = ('https://www.bancsabadell.com/txempbs/'
                                 'CUExtractOperationsQueryNew.accountDataToQuery.bs?')
        ok, s, resp_movs_filtered = self._filter_movs_with_attempts(
            s,
            fin_ent_account_id,
            1,
            req_movs_filtered_url,
            req_movs_filtered_params
        )
        if not ok:
            return False, s  # already reported

        movements_parsed, _, _ = parse_helpers.parse_movements_from_html(resp_movs_filtered.text)
        if not movements_parsed:
            # N43 downloading raises errs if there are no movs during the dates
            self.logger.info("{}: no movements from {} to {}. Skip N43 downloading".format(
                fin_ent_account_id,
                date_from_str,
                date_to_str
            ))
            return True, s

        # Will be used to detect 'no movements'
        time.sleep(0.5 + random.random())
        req_movs_xml_url = 'https://www.bancsabadell.com/txempbs/CUMovementsQuery.initGetMovements.bs'
        req_movs_xml_params = OrderedDict([
            ('typeCall', '1'),
            ('dateMovFrom.day', ''),
            ('dateMovFrom.month', ''),
            ('dateMovFrom.year', ''),
            ('dateMovTo.day', ''),
            ('dateMovTo.month', ''),
            ('dateMovTo.year', ''),
            ('amountFrom.value', ''),
            ('amountTo.value', ''),
            ('reference', ''),
            ('purpose.handle', ''),
            ('chargeType', '')
        ])

        ok, s, resp_movs_xml = self._filter_movs_with_attempts(
            s,
            fin_ent_account_id,
            1,
            req_movs_xml_url,
            req_movs_xml_params,
        )

        req_n43_init_url = 'https://www.bancsabadell.com/txempbs/SVNorma43.directInit.bs'

        req_n43_init_params = OrderedDict([
            ('account.accountNumber', fin_ent_account_id[-10:]),  # '0002533764'
            ('account.branch', fin_ent_account_id[8:12]),  # '0085'
            ('account.bank', fin_ent_account_id[4:8]),  # '0081'
            ('account.checkDigit', fin_ent_account_id[-12:-10]),  # '69'
            ('account.selectable-index', str(account_from_dropdown.idx)),  # '0'
            ('startDate.day', day_from),
            ('startDate.month', month_from),
            ('startDate.year', year_from),
            ('endDate.day', day_to),
            ('endDate.month', month_to),
            ('endDate.year', year_to),
            ('fromMovQuery', ''),
            ('account.alias', ''),
            ('account.iban.countryCode', fin_ent_account_id[:2]),  # 'ES'
            ('account.iban.accountNumber', fin_ent_account_id[4:]),  # '00810085690002533764'
            ('account.iban.checkDigit', fin_ent_account_id[2:4]),  # '35'
            ('account.BIC', ''),  # BSAB ESBB - not necessary
            ('account.description', ''),  # CUENTA RELACIÓN - not necessary
            ('noRedirect', 'true'),
        ])

        time.sleep(0.5 + random.random())
        _resp_n43_init = s.post(
            req_n43_init_url,
            data=req_n43_init_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=120,  # for -a 32807: ES2100817710080001238426
        )

        req_n43_url = 'https://www.bancsabadell.com/txempbs/SVNorma43.doAttach.bs?'
        req_n43_params = OrderedDict([
            ('dateMovFrom.day', day_from),
            ('dateMovFrom.month', month_from),
            ('dateMovFrom.year', year_from),
            ('dateMovTo.day', day_to),
            ('dateMovTo.month', month_to),
            ('dateMovTo.year', year_to),
            ('orderAccount.BIC', ''),
            ('orderAccount.accountNumber', ''),
            ('orderAccount.description', ''),
            ('orderAccount.checkDigit', ''),
            ('orderAccount.branch', ''),
            ('orderAccount.iban.countryCode', ''),
            ('orderAccount.iban.accountNumber', ''),
            ('orderAccount.iban.checkDigit', ''),
            ('orderAccount.bank', ''),
            ('owner', ''),
            ('orderAccount.selectable-index', str(account_from_dropdown.idx)),
            ('selectedCriteria', "Desde {} Hasta {}.".format(date_from_str, date_to_str)),
            ('selectedAmounts', ''),
            ('selectedPurpose', ''),
            ('selectedReference', ''),
            ('CUExtractOperationsQuery.paginationRows', '100'),
        ])
        time.sleep(0.5 + random.random())
        resp_n43 = s.post(
            req_n43_url,
            data=req_n43_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=120
        )

        resp_n43_content = resp_n43.content
        if not n43_funcs.validate(resp_n43_content):
            # If there are no movements and N43 docs for dates, then the response will
            # have HTML content instead of N43 data.
            # There is no explicit message if there are no N43s.
            # Also, there are no explicit messages if the request has wrong parameters or url
            # (status code is always 200).
            # So, the way to decide that there are no movements and there are no errors
            # is to check both for HTML: resp_movs_xml (it will be HTML too) and resp_n43
            if '<!DOCTYPE' in resp_n43.text and '<!DOCTYPE' in resp_movs_xml.text:
                self.logger.info('{}: dates from {} to {}: no movements and N43 docs'.format(
                    fin_ent_account_id,
                    date_from_str,
                    date_to_str
                ))
                return True, s

            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(fin_ent_account_id)
            )
            return False, s

        self.n43_contents.append(resp_n43.text.encode('UTF-8'))
        self.logger.info('{}: downloaded N43 file with movements from {} to {}'.format(
            fin_ent_account_id,
            date_from_str,
            date_to_str
        ))
        return True, s

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        is_success = self.process_companies(s, resp_logged_in)

        if is_success:
            self.basic_save_n43s(
                self.fin_entity_name,
                self.n43_contents
            )

        self.basic_log_time_spent('GET N43')

        if not is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
