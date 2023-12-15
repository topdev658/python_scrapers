import random
import time
import urllib.parse
from datetime import timedelta

from custom_libs import extract, date_funcs
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountParsed
from . import parse_helpers
from .bancofar_scraper import BancofarScraper

__version__ = '2.1.0'

__changelog__ = """
2.1.0
parse_helpers: fixed calc account_no (new layout)
fixed is_active_account (basic_get_n43_dates_and_account_status is used with IBAN arg)
2.0.0
process_contract_for_n43
process_account_for_n43
1.0.0
stable
0.2.0
process_account
download_n43
0.1.0
Add login
"""


class BancofarN43Scraper(BancofarScraper):
    scraper_name = 'BancofarN43Scraper'
    fin_entity_name = 'BANCOFAR'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def process_contract_for_n43(self, s: MySession, resp_logged_in: Response) -> bool:
        ok, accounts_parsed = parse_helpers.get_accounts_parsed(resp_logged_in.text)
        if not ok:
            self.basic_log_wrong_layout(resp_logged_in, "Can't get accounts_parsed. Abort")
            return False

        self.logger.info('Got {} account(s): {}'.format(len(accounts_parsed), accounts_parsed))

        for account_parsed in accounts_parsed:
            ok = self.process_account_for_n43(s, resp_logged_in, account_parsed)
            if not ok:
                return False

        return True

    def process_account_for_n43(
            self,
            s: MySession,
            resp_accs: Response,
            account_parsed: AccountParsed) -> bool:

        fin_ent_account_id = account_parsed['financial_entity_account_id']
        _, _, is_active_account = self.basic_get_n43_dates_and_account_status(
            account_parsed['account_no']
        )
        if not is_active_account:
            return True  # already reported

        date_from = (
            self.last_successful_n43_download_dt
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )
        date_to = date_funcs.today() - timedelta(days=1)

        date_from_str = date_from.strftime('%d%m%Y')
        date_to_str = date_to.strftime('%d%m%Y')

        self.basic_log_process_account(
            fin_ent_account_id,
            date_from_str=date_from.strftime('%d/%m/%Y'),
            date_to_str=date_to.strftime('%d/%m/%Y')
        )
        _, req_movs_params = extract.build_req_params_from_form_html_patched(
            resp_accs.text,
            'datos'
        )

        if not req_movs_params:
            self.basic_log_wrong_layout(
                resp_accs,
                "{}: can't get req_movs_params. Skip process_account".format(fin_ent_account_id)
            )
            return False

        req_movs_params['GCUENTA'] = fin_ent_account_id
        req_movs_params['FECINI'] = date_from_str
        req_movs_params['FECFIN'] = date_to_str

        req_mov_url = urllib.parse.urljoin(self._auth_url(), 'not5838_d_5838m.action')
        for i in range(3):
            resp_movs = s.post(
                req_mov_url,
                data=req_movs_params,
                headers=self.req_headers,
                proxies=self.req_proxies,
                timeout=20
            )
            if 'NO HAY DATOS PARA ESA SELECCION' in resp_movs.text:
                self.logger.info("{}: 'no movements' marker detected".format(fin_ent_account_id))
                return True
            if self._check_selected_account(resp_movs, fin_ent_account_id):
                break
            # wait before the next attempt
            self.logger.warning("{}: can't switch to correct account in resp_mov. Retry".format(
                fin_ent_account_id
            ))
            time.sleep(1 + random.random())
        else:
            self.logger.error("{}: can't switch to correct account in resp_mov. Abort".format(
                fin_ent_account_id
            ))
            self.basic_set_movements_scraping_finished(fin_ent_account_id)
            return False
        self.download_n43(s, resp_movs, fin_ent_account_id)
        return True

    def download_n43(self,
                     s: MySession,
                     resp_movs: Response,
                     fin_ent_account_id: str) -> bool:

        _, req_n43_params = extract.build_req_params_from_form_html_patched(
            resp_movs.text,
            'Q43CLI'
        )
        req_43_url = urllib.parse.urljoin(
            self._auth_url(),
            'aontDescargaInforme_Q43C_d_0.action'
        )
        self.logger.info("{}: starting to download N43 file".format(fin_ent_account_id))
        resp_n43_file = s.post(
            req_43_url,
            data=req_n43_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
            timeout=20
        )
        n43_text = resp_n43_file.text
        n43_content = n43_text.encode('UTF-8')

        if not n43_funcs.validate(n43_content):
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid resp_n43. Abort".format(
                    fin_ent_account_id
                )
            )
            return False
        if not n43_funcs.validate_n43_structure(n43_text):
            self.logger.warning(
                "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                    fin_ent_account_id,
                    resp_n43_file.text
                )
            )
            return True

        self.n43_contents.append(n43_content)

        return True

    def main(self) -> MainResult:
        self.logger.info('Main: started')

        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        ok = self.process_contract_for_n43(s, resp_logged_in)

        self.basic_log_time_spent('GET N43 FILES')

        if not ok:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
