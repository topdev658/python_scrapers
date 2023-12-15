import random
import time
from collections import OrderedDict
from typing import List
from urllib.parse import urljoin

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped
from . import parse_helpers
from .unicaja_scraper import UnicajaScraper

__version__ = '1.1.0'

__changelog__ = """
1.1.0
process_account: get date_from date_to with "basic_get_n43_dates_and_account_status"
don't download for inactive account
1.0.0
stable
0.5.0
more logs
0.4.0
use process_access
can download N43s
0.3.0
process_account: no movements signs, deleted unused post
0.2.0
_save_n43s (to allow changes by children)
_log_time_spent (to allow changes by children)
0.1.0
init
"""

NO_MOVEMENTS_SIGNS = [
    "NO EXISTEN MOVIMIENTOS",
]


class UnicajaN43Scraper(UnicajaScraper):
    fin_entity_name = 'UNICAJA'
    scraper_name = "UnicajaN43Scraper"

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.is_success = True

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]) -> None:
        # No need to save accounts_scraped by parent's process_access, do nothing
        return

    def process_account(self, s: MySession, resp: Response, account_scraped: AccountScraped) -> bool:
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        self.logger.info('{}: process account for N43'.format(fin_ent_account_id))

        # Open movements filter page first to get necessary post param
        # FICHERO DE MOVIMIENTOS
        req_filter_form_url = urljoin(
            self._get_host(),
            '/univia/servlet/ControlServlet?o=csbcta&p=1&M1=empr-tesoreria'
            '&M2=mi-tesoreria&M3=consultas-mis-cuentas&M4=cuentas-movcsb-tesoreria'
        )

        resp_filter_form = s.get(
            req_filter_form_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        ppp_param = parse_helpers.get_ppp_param_for_account_processing(
            resp_filter_form.text,
            account_scraped.FinancialEntityAccountId
        )

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )

        if not is_active_account:
            time.sleep(1.0 + random.random())
            return True

        d_from, m_from, y_from = date_from.strftime("%d/%m/%Y").split('/')
        d_to, m_to, y_to = date_to.strftime("%d/%m/%Y").split('/')

        self.logger.info('{}: process_account for N43 from {} to {}'.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        req_url = urljoin(self._get_host(), '/univia/servlet/ControlServlet')

        # Filter by account and dates,
        # Returns a page with link to download N43 file
        req_n43_filtered_params = OrderedDict([
            ('p', '2'),
            ('numMovDesdeSiguiente', '1'),
            ('discriminante', '01'),
            ('ppp', ppp_param),  # '001'
            ('diaDesde', d_from),
            ('mesDesde', m_from),
            ('anoDesde', y_from),
            ('diaHasta', d_to),
            ('mesHasta', m_to),
            ('anoHasta', y_to),
            ('o', 'csbcta'),
            ('x', '40'),
            ('y', '13')
        ])

        # Necessary to download N43 file then
        _resp_n43_filtered = s.post(
            req_url,
            data=req_n43_filtered_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        req_n43_file_params = OrderedDict([
            ('o', 'csbcta'),
            ('p', '3'),
            ('ppp', ppp_param),
            ('diaDesde', d_from),
            ('mesDesde', m_from),
            ('anoDesde', y_from),
            ('diaHasta', d_to),
            ('mesHasta', m_to),
            ('anoHasta', y_to),
        ])

        resp_n43_file = s.get(
            req_url,
            params=req_n43_file_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            stream=True
        )

        try:
            n43_text = resp_n43_file.text
            if any(marker in n43_text for marker in NO_MOVEMENTS_SIGNS):
                self.logger.warning(
                    "{}: N43 no movements detected, no file generated. Skip. CONTENT:\n{}".format(
                        fin_ent_account_id,
                        resp_n43_file.text
                    ))
                self.is_success = True
                return True

        except Exception as _e:
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid resp_containing_n43".format(fin_ent_account_id)
            )
            self.is_success = False
            return False
        n43_content = n43_text.encode('UTF-8')

        if not (n43_text and n43_funcs.validate(n43_content)):
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid res_n43 (wrong N43 content)".format(fin_ent_account_id)
            )
            self.is_success = False
            return False

        if not n43_funcs.validate_n43_structure(n43_text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    fin_ent_account_id,
                    resp_n43_file.text
                )
            )
            # Still True to allow download other files, because it's not a scraping error
            return True

        self.n43_contents.append(n43_content)
        self.logger.info('{}: downloaded N43 file'.format(fin_ent_account_id))
        return True

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
        self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET N43 FILES')

        if not self.is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
