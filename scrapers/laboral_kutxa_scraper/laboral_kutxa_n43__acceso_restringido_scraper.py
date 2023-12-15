from datetime import datetime, timedelta
import random
import time
from typing import Dict, List

from custom_libs.myrequests import MySession, Response
from custom_libs import n43_funcs, iban_builder
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped
from .laboral_kutxa__acceso_restringido_scraper import LaboralKutxaAccesoRestringidoScraper

from . import parse_helpers_n43__acceso_restringido as parse_helpers_n43


__version__ = '1.6.0'

__changelog__ = """
1.6.0
download_n43_files: add optional parameter 
to download N43 without updating N43_content
1.5.0
login: moved to laboral_kutxa__acceso_restringido_scraper.py
1.4.0
download_n43_files
1.3.0
process_account, resp_n43_form
1.2.0
process_access
1.1.0
login
1.0.0
init
"""


RESP_ERR_SIGNS = [
    'Su tarjeta no se halla operativa, diríjase a su sucursal habitual e infórmese de su situación.',
]


class LaboralKutxaN43AccesoRestringidoScraper(LaboralKutxaAccesoRestringidoScraper):
    fin_entity_name = 'LABORAL_KUTXA'
    scraper_name = 'LaboralKutxaN43AccesoRestringidoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.access_id = ''
        self.n43_contents = []

    def download_n43_files(self, s: MySession, req_data: Dict, update_n43_content=True):
        self.req_headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.req_headers["Referer"] = "https://lknet.laboralkutxa.com/Consultas/" \
                                      "C020_Sel.asp?Id={}&DesdeMenu=**&CodReducida={}".format(self.access_id, self.username_second)

        resp_n43_file = s.post(
            'https://lknet.laboralkutxa.com/Consultas/C020_Csb43.asp',
            data=req_data,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if update_n43_content:
            if not n43_funcs.validate(resp_n43_file.content):
                self.logger.error("Error downloading N43. RESPONSE: {}".format(
                    resp_n43_file.text
                ))
                return False

            self.n43_contents.append(resp_n43_file.text.encode('UTF-8'))
            return True
        else:
            download_success = True
            if not n43_funcs.validate(resp_n43_file.content):
                self.logger.error("Error getting complete account number. RESPONSE: {}".format(
                    resp_n43_file.text
                ))
                download_success = False

            return download_success, resp_n43_file

    def process_account(
            self, s: MySession,
            account: str,
            req_data: Dict,
    ) -> bool:

        account_no = parse_helpers_n43.get_account_number(account)

        yesterday = datetime.today() - timedelta(days=1)

        y_date_from_str = yesterday.strftime('%d%m%Y')
        y_day_from, y_month_from, y_year_from = yesterday.strftime('%d/%m/%Y').split('/')

        y_date_to_str = yesterday.strftime('%d%m%Y')
        y_day_to, y_month_to, y_year_to = yesterday.strftime('%d/%m/%Y').split('/')

        req_data["codredudate_fromcida"] = self.username_second
        req_data["lcuenta"] = account
        req_data["cuenta1"] = account_no
        req_data["count"] = "1"
        req_data["FECHAINICIO"] = y_date_from_str  # '01082022'
        req_data["FECHAFIN"] = y_date_to_str  # '25092022'
        req_data["cuentaA"] = account
        req_data["diadesde"] = y_day_from  # '01'
        req_data["mesdesde"] = y_month_from  # '08'
        req_data["yeardesde"] = y_year_from  # '2022'
        req_data["diahasta"] = y_day_to  # '25'
        req_data["meshasta"] = y_month_to  # '09'
        req_data["yearhasta"] = y_year_to  # '2022'

        ok, resp_n43_file = self.download_n43_files(s, req_data, update_n43_content=False)

        if not ok:
            return ok

        entity_code, branch_code, account_number = parse_helpers_n43.get_complete_account(resp_n43_file.text)
        control_digit = iban_builder._dc(entity_code, branch_code, account_number)

        complete_account_no = entity_code + branch_code + control_digit + account_number

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(complete_account_no)
        if not is_active_account:
            time.sleep(1.0 + random.random())
            return True  # already reported
        fin_ent_account_id = account_no
        self.logger.info('{}: process_account for N43 from {} to {}'.format(
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        date_from_str = date_from.strftime('%d%m%Y')
        day_from, month_from, year_from = date_from.strftime('%d/%m/%Y').split('/')

        date_to_str = date_to.strftime('%d%m%Y')
        day_to, month_to, year_to = date_to.strftime('%d/%m/%Y').split('/')

        req_data["FECHAINICIO"] = date_from_str  # '01082022'
        req_data["FECHAFIN"] = date_to_str   # '25092022'
        req_data["diadesde"] = day_from  # '01'
        req_data["mesdesde"] = month_from  # '08'
        req_data["yeardesde"] = year_from  # '2022'
        req_data["diahasta"] = day_to  # '25'
        req_data["meshasta"] = month_to  # '09'
        req_data["yearhasta"] = year_to  # '2022'

        ok = self.download_n43_files(s, req_data)

        if not ok:
            self.logger.error('N43 downloading for account {} not successful'.format(account))

        return ok

    def process_access_for_43(self, s: MySession,resp_logged_in: Response) -> bool:
        self.access_id = parse_helpers_n43.get_access_id(resp_logged_in.text)

        req_params = {
            'Id': self.access_id,
            'DesdeMenu': '**',
            'CodReducida': self.username_second
        }

        req_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'frame',
            'Sec-Fetch-Site': 'same-origin',
            'Set-Fetch-Mode': 'navigate',
            'TE': 'trailers'
        }

        # request to required intermediate frame
        # 20_resp_logo.html
        resp_logo = s.get(
            'https://lknet.laboralkutxa.com/nuevoacceso/logo.asp',
            headers=req_headers,
            proxies=self.req_proxies
        )

        req_headers['Referer'] = 'https://lknet.laboralkutxa.com/reducida/checklogon.asp'

        # request to required intermediate frame
        # 30_resp_accesso.html
        resp_acceso = s.get(
            'https://lknet.laboralkutxa.com/nuevoacceso/AccesoRestringido.asp',
            params={
                'Id': self.access_id
            },
            headers=req_headers,
            proxies=self.req_proxies
        )

        req_headers['Referer'] = 'https://lknet.laboralkutxa.com/nuevoacceso/AccesoRestringido.asp?Id={}'.format(self.access_id)
        req_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        menu_data = {
            'Id': self.access_id,
            'cfrm': 'sup',
            'codreducida': self.username_second,
            'MenuNuevoCtas': 'False'
        }

        # request to required intermediate frame with menu
        # contains links to other frames with movements
        # 40_resp_menu.html
        resp_menu = s.post(
            'https://lknet.laboralkutxa.com/menu/menuR.asp',
            data=menu_data,
            headers=req_headers,
            proxies=self.req_proxies
        )

        req_headers['Referer'] = 'https://lknet.laboralkutxa.com/menu/menuR.asp'
        req_headers.pop('Content-Type', None)

        resp_form_n43 = s.get(
            'https://lknet.laboralkutxa.com/Consultas/C020_Sel.asp',
            params=req_params,
            headers=req_headers,
            proxies=self.req_proxies
        )

        accounts = parse_helpers_n43.get_accounts(resp_form_n43.text)

        self.req_headers = req_headers

        req_data = parse_helpers_n43.get_filter_form_params(resp_form_n43.text)

        for account in accounts:
            self.process_account(s, account, req_data)

        return True

    def _upload_accounts_scraped(self, accounts_scraped: List[AccountScraped]) -> None:
        # No need to save accounts_scraped by parent's process_access, do nothing
        return

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

        ok = self.process_access_for_43(s, resp_logged_in)
        self.basic_log_time_spent('GET N43')

        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()