from collections import OrderedDict
from datetime import timedelta
from urllib.parse import urljoin

from custom_libs import date_funcs
from custom_libs import n43_funcs
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from . import parse_helpers
from . import parse_helpers_n43
from .custom_types import N43FromList
from .liberbank_scraper import LiberbankScraper

__version__ = '1.3.0'

__changelog__ = """
1.3.0
adopted for night scraping: date_to = today - 1, date_from = last success date
1.2.0
parse_helpers_n43.get_n43s_from_list: warn about files with unsupported extensions
1.1.0 
date_to = today, date_from = last success date + 1 day
1.0.0
stable
0.1.0
init
"""


class LiberbankN43Scraper(LiberbankScraper):
    fin_entity_name = 'LIBERBANK'
    scraper_name = "LiberbankN43Scraper"

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        self.is_success = True

    def process_access_for_n43(
            self,
            s: MySession,
            resp_logged_in: Response,
            caja_param: str,
            camino_param: str) -> bool:

        # All files available at once.
        # No filter available.

        # Last available file date = today,
        # BUT it appears AFTER night scraping, thus,
        # only today-1 can be used as date_to for night scraping

        # 11.06 (Fri) - first run: date_from=today-init offset, date_to=10.06
        # 12.06 (Sat) - date_from=11.06, date_to=11.06
        # 13.06 (Sun) - no executions (or failure)
        # 14.06 (Mon) - date_from 12.06, date_to 13.06
        date_to = date_funcs.today() - timedelta(days=1)
        date_from = (
            self.last_successful_n43_download_dt
            if self.last_successful_n43_download_dt
            else date_funcs.today() - timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )

        self.logger.info('process_access_for_n43: date_from={}, date_to={}'.format(
            date_from.date(),
            date_to.date()
        ))

        llamada_param = parse_helpers.get_llamada_param(resp_logged_in.text)

        req_n43s_params = OrderedDict([
            ('LLAMADA', llamada_param),
            ('CLIENTE', self.username),
            ('CAJA', caja_param),
            ('CAMINO', camino_param)
        ])

        resp_n43s = s.post(
            'https://bancaadistancia.liberbank.es/BEWeb/2048/5048/not9902_d_COMUN.action',
            data=req_n43s_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        try:
            resp_n43s_json = resp_n43s.json()
        except Exception as _e:
            self.basic_log_wrong_layout(
                resp_n43s,
                "Can't get resp_n43s_json"
            )
            self.is_success = False
            return False

        n43s_from_list = parse_helpers_n43.get_n43s_from_list(resp_n43s_json, self.logger)

        n43s_to_download = [
            f for f in n43s_from_list
            if (date_from.date() <= f.date <= date_to.date())
        ]
        n43s_to_download.reverse()  # to asc

        # See 20_resp_n43_files.json
        # /BEWeb/2048/5048/ont9907_d_COMUN.action;jsessionid=o1r1W4azV_YPJS3IqNbuUXWI.tlima
        req_n43_file_link = resp_n43s_json['ONT9907d']
        req_n43_file_url = urljoin(resp_n43s.url, req_n43_file_link)
        for n43_from_list in n43s_to_download:
            ok = self.download_n43_file(
                s,
                n43_from_list,
                req_n43_file_url=req_n43_file_url,
                llamada_param=llamada_param,
                caja_param=caja_param
            )
            if not ok:
                return False

        return True

    def download_n43_file(
            self,
            s: MySession,
            n43_from_list: N43FromList,
            req_n43_file_url: str,
            llamada_param: str,
            caja_param: str) -> bool:

        n43_from_list_str = '{} (created {})'.format(
            n43_from_list.fichero,
            n43_from_list.date.strftime(project_settings.SCRAPER_DATE_FMT)
        )

        req_n43_file_params = OrderedDict([
            ('LLAMADA', llamada_param),
            ('CLIENTE', self.username),
            ('IDIOMA', '1'),
            ('CAJA', caja_param),
            ('OPERAC', '9907'),
            ('CTASEL', ''),
            ('CTAFOR', ''),
            ('FICHERO', n43_from_list.fichero),  # F0810237.Q43
            ('ZIP', 'NO'),
        ])

        resp_n43_file = s.get(
            req_n43_file_url,
            params=req_n43_file_params,
            headers=self.req_headers,
            proxies=self.req_proxies,
        )

        n43_text = resp_n43_file.text
        n43_content = n43_text.encode('UTF-8')

        if not (n43_text and n43_funcs.validate(n43_content)):
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid resp_n43 (wrong N43 content)".format(n43_from_list_str)
            )
            self.is_success = False
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
        self.logger.info('Downloaded N43 file: {}'.format(n43_from_list_str))
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, caja_param, camino_param = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_unknown_reason(
                resp_logged_in.url,
                resp_logged_in.text
            )

        self.process_access_for_n43(s, resp_logged_in, caja_param, camino_param)
        self.basic_log_time_spent('GET N43 FILES')

        if not self.is_success:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
