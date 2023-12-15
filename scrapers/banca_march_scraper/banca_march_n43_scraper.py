import random
import time
import traceback
from datetime import timedelta
from urllib.parse import urljoin

from custom_libs import date_funcs, n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers_n43
from .banca_march_scraper import BancaMarchScraper
from .custom_types import N43FromList

__version__ = '2.0.0'
__changelog__ = """
2.0.0
upd parse_helpers_n43: get_n43s_from_list(), fixed typing
removed unused attempts
redefined scrape()
fin_entity_name w/o spaces
upd log msgs
renamed vars
fmt
1.0.0
stable
fix process_n43_from_resp dates
0.4.0
Add process_n43_from_resp, download_n43_file
0.3.0
Add dwonload_n43_file
Add N43FromList -> customTypes
0.2.0
Add open_files_pages, parse_helpers_n43.py
0.1.0
mainResult, is logged = True
init
"""


class BancaMarchN43Scraper(BancaMarchScraper):
    fin_entity_name = "BANCA_MARCH"
    scraper_name = "BancaMarchN43Scraper"

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def _open_files_page(self, s: MySession) -> Response:
        """Get all the page in html of the BANCA MARCH/COUNTS/NORMA43/RECEPCION DE ARCHIVOS"""
        req_url_files = ("https://telemarch.bancamarch.es/htmlVersion/XTransManager?"
                         "ts=1629714834060&tr=OP&testnw=H&idioma=0&num=03152&idopmenu=156&origen=principal")
        resp_files = s.get(
            req_url_files,
            params=self._req_params_w_csrf_token(s),
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        return resp_files

    def process_access_for_n43(self, s: MySession) -> bool:
        """PROCESS the html returned of open_files_pages and add the 43_from_list the n43 files"""

        date_to = date_funcs.today()
        date_from = (
            self.last_successful_n43_download_dt + timedelta(days=1)
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )
        self.logger.info('process_access_for_n43: date_from={}, date_to={}'.format(
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        resp_files_list = self._open_files_page(s)
        # ASC
        n43s_from_list = parse_helpers_n43.get_n43s_from_list(resp_files_list.text)

        n43s_to_download = [
            f for f in n43s_from_list
            if date_from.date() <= f.date <= date_to.date()
        ]

        for n43_from_list in n43s_to_download:
            ok = self.download_n43_file(s, n43_from_list)
            if not ok:
                return False

        return True

    def download_n43_file(
            self,
            s: MySession,
            n43_from_list: N43FromList) -> bool:

        if not n43_from_list.link:
            self.logger.error('{}: no link to file. Abort'.format(n43_from_list))
            return False

        n43_from_list_str = n43_from_list.date.strftime(project_settings.SCRAPER_DATE_FMT)

        self.logger.info('download N43 with date: {}'.format(n43_from_list_str))
        try:
            time.sleep((1 + random.random()))
            req_n43_url = urljoin('https://telemarch.bancamarch.es/', n43_from_list.link)
            resp_n43_file = s.get(
                req_n43_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )
            n43_text = resp_n43_file.text
            n43_content = n43_text.encode('UTF-8')

            if not n43_funcs.validate(n43_content):
                self.basic_log_wrong_layout(
                    resp_n43_file,
                    "{}: got invalid resp_n43. Abort".format(n43_from_list_str)
                )
                return False
            if not n43_funcs.validate_n43_structure(n43_text):
                self.logger.warning(
                    "{}: N43 file with broken structure detected. Skip. CONTENT:\n{}".format(
                        n43_from_list_str,
                        resp_n43_file.text
                    )
                )
                # Still True to allow download other files, because it's not a scraping error
                return True
            self.n43_contents.append(n43_content)
            self.logger.info('downloaded N43 file: {}'.format(n43_from_list_str))
            return True

        except Exception as _e:
            self.logger.error(
                "{}: can't download. Abort. HANDLED EXCEPTION: {}".format(
                    str(n43_from_list.date),
                    traceback.format_exc()
                )
            )
            return False

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(resp_logged_in.url, resp_logged_in.text)

        ok = self.process_access_for_n43(s)
        self.basic_log_time_spent('GET N43')
        if not ok:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(self.fin_entity_name, self.n43_contents)
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
