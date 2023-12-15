import random
import time
from collections import OrderedDict
from datetime import datetime
from typing import Tuple, Optional

from custom_libs import extract
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers_n43
from .bankia_scraper import BankiaScraper

__version__ = '1.7.0'

__changelog__ = """
1.7.0
delays before & after _open_filter_form for more stable account selecting
1.6.0
main: don't check for get_n43_last_successful_result_date_of_access() 
  (now implemented in self.basic_scrape_for_n43())
1.5.0
use basic_save_n43s
1.4.0
use basic_scrape_for_n43
self.fin_entity_name
1.3.1
upd log msg
1.3.0
several attempts to filter_n43, increased delays between accounts
1.2.0
use self.is_success due to usage of parent process_access
1.1.0
use basic_get_n43_dates_and_account_status
1.0.0
init
"""

NO_N43_MARKER = ('NO ES POSIBLE FACILITAR LA INFORMACI&Oacute;N SOLICITADA. '
                 'COMPRUEBE SI TIENE UNA PETICI&Oacute;N REALIZADA PARA ESTA CUENTA')


class BankiaN43Scraper(BankiaScraper):
    fin_entity_name = 'BANKIA'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankiaN43Scraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        # Parent's process_access expects event_number instead of 'ok'
        # and then it returns True even is failed during company processing,
        # so, let's set the flag here
        self.is_success = True

    def process_company(
            self,
            s: MySession,
            resp_logged_in: Response,
            event_number: int,
            company_param: Optional[str] = None) -> int:

        # account_no = 'ES0420381830136000255776'
        ok, org_title = self.get_organization_title(s, company_param)
        resp_filter_form = self._open_filter_form(s, company_param)
        ok, account_nos = parse_helpers_n43.get_account_nos_for_n43(resp_filter_form.text)
        self.logger.info(
            "{}: got {} accounts for N43: {}".format(
                org_title,
                len(account_nos),
                account_nos
            )
        )
        if not ok:
            self.basic_log_wrong_layout(
                resp_filter_form,
                "Can't get account_nos"
            )
            self.is_success = False
            return event_number

        ix_max = len(account_nos) - 1
        for ix, account_no in enumerate(account_nos):
            ok = self.process_account_for_n43(s, company_param, resp_filter_form, account_no)
            if not ok:
                self.is_success = False
                return event_number
            if ix < ix_max:  # don't open filter_form after the last acc
                time.sleep(3 + random.random())
                resp_filter_form = self._open_filter_form(s, company_param)  # need to refresh
                # It's very critical to use this delay.
                # Otherwise while processing many accounts (-a 2206)
                # it may fail at filter_n43 step (when can't select correct account).
                # If that error appears often, then need to
                # increae this delay.
                time.sleep(3 + random.random())
        return event_number

    def _open_filter_form(self, s: MySession, company_param: Optional[str]) -> Response:
        # This URL is never opened in Web, but it's a referer...

        company_param_str = '&j_gid_indice={}'.format(company_param) if company_param else ''
        referer = ('https://oficinaempresas.bankia.es/nbole/bole/sib-war-1.0/gf2/GID/products/GF3/products/'
                   'norma43/list.html?opcsubmenu=N43A&origen=OIE2{}'.format(company_param_str))

        req_filter_form_url = ('https://ficheros.bankia.es/sib-war-1.0/gf2/GID/products/GF3/products/'
                               'norma43/list.html')

        req_params = OrderedDict([
            ('j_gid_indice', company_param),
            ('opcsubmenu', 'N43A'),
            ('origen', 'OIE2'),
        ])

        resp_filter_form = s.get(
            req_filter_form_url,
            params=req_params,  # <-- GET params
            headers=self.basic_req_headers_updated({
                'Referer': referer,
            }),
            proxies=self.req_proxies,
        )

        return resp_filter_form

    def _validate_selected_account(self, resp_text: str, account_no: str) -> bool:
        """Checks for pattern
        # <option value="ES7420384222576000042453" selected="selected">ES7420384222576000042453</option>
        """
        found = extract.re_first_or_blank(
            '<option value="{}" selected="selected">'.format(account_no),
            resp_text
        )  # type: str
        return bool(found)

    def _filter_n43(
            self,
            s: MySession,
            company_param: Optional[str],
            resp_filter_form: Response,
            account_no: str,
            date_from: datetime,
            date_to: datetime) -> Tuple[bool, bool, Response]:
        """:returns (is_success, has_n43, resp_filtered)"""

        df, mf, yf = date_from.strftime('%d/%m/%Y').split('/')
        dt, mt, yt = date_to.strftime('%d/%m/%Y').split('/')

        # for a linter
        resp_filter_n43_step1 = Response()

        for attempt in range(1, 4):
            # initial 'SUBMIT' query
            # 20_resp_no_43_data.html
            # 30_resp_continueForm.html
            req_filter_n43_step1_url = resp_filter_form.url  # 'https://ficheros.bankia.es/sib-war-1.0/products/GF3/products/norma43/list.html?execution=e1s2'
            req_filter_n43_step1_params = OrderedDict([
                ('peticionSelected.cuentaCargo', account_no),  # ES0420381830136000255776
                ('downloadFileType', 'txt'),
                ('date-box', ['', '']),
                ('fromDate.dia', df),  # '01'
                ('fromDate.mes', mf),  # '01'
                ('fromDate.anyo', yf),  # '2021'
                ('toDate.dia', dt),  # '20'
                ('toDate.mes', mt),  # '01'
                ('toDate.anyo', yt),  # '2021'
                ('_eventId_search', '')
            ])
            resp_filter_n43_step1 = s.post(
                req_filter_n43_step1_url,
                data=req_filter_n43_step1_params,
                headers=self.basic_req_headers_updated({
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': resp_filter_form.url,
                }),
                proxies=self.req_proxies,
            )

            if self._validate_selected_account(resp_filter_n43_step1.text, account_no):
                break  # stop on success

            # If getting this error too often, then increase delay between accounts in process_company()
            self.logger.warning('{}: attempt #{}: selected wrong account. Retry'.format(
                account_no,
                attempt
            ))
            time.sleep(3 * attempt + random.random())
            resp_filter_form = self._open_filter_form(s, company_param)
            time.sleep(3 * attempt + random.random())

        else:
            self.basic_log_wrong_layout(
                resp_filter_n43_step1,
                '{}: selected wrong account'.format(account_no)
            )
            return False, False, resp_filter_n43_step1

        if NO_N43_MARKER in resp_filter_n43_step1.text:
            self.logger.info("{}: 'no N43 (no movs)' marker detected. Skip".format(account_no))
            has_n43 = False
            return True, has_n43, resp_filter_n43_step1

        time.sleep(1.0 + random.random())  # to allow the backend prepare N43 response
        # click 'CONTINUE'
        # 40_resp_n43_download.html
        req_filter_n43_step2_url = resp_filter_n43_step1.url
        req_filter_n43_step2_params = req_filter_n43_step1_params.copy()
        del req_filter_n43_step2_params['_eventId_search']
        req_filter_n43_step2_params['_eventId_continue'] = ''
        resp_filter_n43_step2 = s.post(
            req_filter_n43_step2_url,
            data=req_filter_n43_step2_params,
            headers=self.basic_req_headers_updated({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': resp_filter_n43_step1.url,
            }),
            proxies=self.req_proxies,
        )
        has_n43 = True

        ok = ('Iniciada descarga del fichero de movimientos' in resp_filter_n43_step2.text
              and NO_N43_MARKER not in resp_filter_n43_step2.text)

        if not ok:
            self.basic_log_wrong_layout(
                resp_filter_n43_step2,
                "{}: resp_filter_43_step2: wrong response detected".format(account_no)
            )

        return ok, has_n43, resp_filter_n43_step2

    def process_account_for_n43(
            self,
            s: MySession,
            company_param: Optional[str],
            resp_filter_form: Response,
            account_no: str) -> bool:

        fin_ent_account_id = account_no[4:]

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )

        if not is_active_account:
            time.sleep(1.0 + random.random())
            return True  # already reported

        ok, has_n43, resp_filtered = self._filter_n43(
            s,
            company_param,
            resp_filter_form,
            account_no,
            date_from,
            date_to
        )
        if not ok:
            return False  # already reported
        if not has_n43:
            return True  # already reported
        ok = self.download_n43_file(s, resp_filtered, account_no)
        if not ok:
            return False  # already reported
        return True

    def download_n43_file(self, s: MySession, resp_prev: Response, account_no: str) -> bool:
        req_n43_url = ('https://ficheros.bankia.es/sib-war-1.0/norma43/download/'
                       'consulta43.html?cuentaCargo={}'.format(account_no))
        resp_n43 = s.get(
            req_n43_url,
            headers=self.basic_req_headers_updated({
                'Referer': resp_prev.url
            }),
            proxies=self.req_proxies,
        )

        if not n43_funcs.validate(resp_n43.content):
            self.basic_log_wrong_layout(
                resp_n43,
                "{}: got invalid resp_n43".format(account_no)
            )
            return False

        self.n43_contents.append(resp_n43.content)

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
        if self.is_success:
            self.basic_save_n43s(
                self.fin_entity_name,
                self.n43_contents
            )

        self.basic_log_time_spent('GET N43')

        if not self.is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
