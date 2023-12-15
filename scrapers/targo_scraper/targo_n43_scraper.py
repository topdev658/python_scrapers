import random
from datetime import timedelta
import time
from typing import List
from urllib.parse import urlparse
from urllib.parse import parse_qs

from custom_libs import n43_funcs, date_funcs
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult

from . import parse_helpers_n43
from .targo_scraper import TargoScraper

__version__ = '1.6.0'
__changelog__ = """
1.6.0 2023.11.16
process_access_for_43: detect no N43 file available error (weekend without files)
parse_helpers_n43: get_n43_files_download_info: fixed reg exp to get N43 files
1.5.0 2023.07.10
reactivate_n43_for_download_at_bank, process_access_for_43: upd requests url to targobank.es
1.4.6
process_access_for_43: use offset days = 0 on call to basic_get_n43_dates_for_access as
bank has file names with current day date.
1.4.5
__init__: added default value for __is_detected_inactive_contract_for_n43
process_access_for_43: capture download error and return False status
1.4.4
process_access_for_43: use WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED
1.4.3
process_access_for_43: Reverse files to order by date and get a 
ordered storage name: TES-TARGO-36202-20221117-141815-0.N43
1.4.2
fixed log and call to get_n43_files_download_info:
1.4.1
fixed index logs reactivate_n43_for_download_at_bank: and process_access_for_43:
1.4.0
process_access_for_43: Managed date_to added one day to be used as filter.
Added log traces, code comments, download file retries, 
Refactored:  process_accounts_for_n43:  integrated in process_access_for_43
Some names refactors.
1.3.0
Reactivate files to be downloaded from archive (already downloaded):
reactivate_n43
1.2.0
Filtering N43: filter_n43
Downloading:
process_access_for_n43, download_n43_file, process_accounts_for_n43
1.1.0
N43 status
1.0.0
init TargoN43Scraper
"""

N43_INACTIVE_STATUS_MARKERS = [
    'Su servicio de teletransmisión no está activo. Contacte con su Gestor.',
]

N43_TECH_PROBLEMS_MARKERS = [
    'Problema técnico. Gracias por intentarlo de nuevo algo más tarde.',
]

N43_DOWNLOAD_PROBLEMS_MARKERS = [
    'Le transfert du fichier a échoué',
]


class TargoN43Scraper(TargoScraper):
    fin_entity_name = 'TARGO'
    scraper_name = 'TargoN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        self.n43_contents = []  # type: List[bytes]
        self.__is_detected_inactive_contract_for_n43 = False

    def get_n43_filtered(
            self,
            s: MySession,
            n43_filters: dict,
            date_from_str: str,
            date_to_str: str,
            url: str
    ) -> Response:
        json_data = n43_filters
        json_data["[t:dbt%3adate;]data_Fichiers_Recherche_CRITERIA_DAT%255fMIN"] = date_from_str  # '25/07/2022'
        json_data["[t:dbt%3adate;]data_Fichiers_Recherche_CRITERIA_DAT%255fMAX"] = date_to_str  # '01/09/2022'
        json_data["_FID_DoSearch.x"] = random.randint(10, 70)
        json_data["_FID_DoSearch.y"] = random.randint(2, 15)

        filter_url_params = parse_qs(urlparse(url).query)
        req_params = {key: filter_url_params[key][0] for key in filter_url_params}

        n43_files_resp = s.post(
            url,
            headers=self.req_headers,
            params=req_params,
            data=json_data,
            proxies=self.req_proxies
        )

        return n43_files_resp

    def _delay(self, minimal=0.5) -> None:
        time.sleep(minimal + random.random())

    def download_n43_file(self, s: MySession, download_link: str) -> bool:
        self.req_headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        self.req_headers['Accept-Encoding'] = 'gzip, deflate, br'

        for att in range(1, 5):
            self._delay(minimal=att)

            resp_n43_file = s.get(
                download_link.replace('&amp;', '&'),  # needed to fix wrong url encoding
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if n43_funcs.validate(resp_n43_file.content):
                break

                reason = resp_n43_file.text
                for m in N43_DOWNLOAD_PROBLEMS_MARKERS:
                    if m in resp_n43_file.text:
                        reason = m

                self.logger.warning(
                    "att#{}: Can't download N43 file: {}. Retry".format(
                        att,
                        reason
                    )
                )

        else:
            self.logger.error("Can't download N43 file after several attempts. Abort")
            return False  # finally failed

        self.n43_contents.append(resp_n43_file.text.encode('UTF-8'))
        return True

    def reactivate_n43_for_download_at_bank(
            self,
            s: MySession,
            resp_n43_archive: Response,
            date_from_str: str,
            date_to_str: str
    ) -> bool:
        n43_filters = parse_helpers_n43.get_n43_reactivate_form(resp_n43_archive.text)
        n43_form_url = parse_helpers_n43.get_form_action_url(resp_n43_archive.text)

        n43_filters.update(
            {
                "Bool:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_LLIBELL%5fVAL": "false",
                "CB:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_LLIBELL%5fVAL": "on",
                "Bool:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_2__LLIBELL%5fVAL": "false",
                "CB:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_2__LLIBELL%5fVAL": "on"
            }
        )

        # Get files from archive filtered by date.
        resp_n43_filtered = self.get_n43_filtered(s, n43_filters, date_from_str, date_to_str, n43_form_url)

        n43_reactivate_form = parse_helpers_n43.get_n43_reactivate_form(resp_n43_filtered.text)
        n43_files_reactivate_info = parse_helpers_n43.get_n43_files_reactivate_info(resp_n43_filtered.text,
                                                                                    date_from_str, date_to_str)

        reactivate_url = n43_form_url

        reactivate_url_params = parse_qs(urlparse(reactivate_url).query)
        req_params = {key: value[0] for key, value in reactivate_url_params.items()}

        self.logger.info(
            'Found {0} files to reactivate from {1} to {2}'.format(
                len(n43_files_reactivate_info),
                date_from_str,
                date_to_str))

        for index, n43_file_reactivate_info in enumerate(n43_files_reactivate_info):
            self.logger.info('Try to reactivate file {}: {}'.format(index, n43_file_reactivate_info['id']))
            json_data = n43_reactivate_form.copy()
            json_data[n43_file_reactivate_info['reactivate_param']] = ""
            json_data["Bool:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_LLIBELL%5fVAL"] = "false"
            json_data["CB:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_LLIBELL%5fVAL"] = "on"
            json_data["Bool:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_2__LLIBELL%5fVAL"] = "false"
            json_data["CB:data_Fichiers_Recherche_CRITERIA_SEFE04_LCPT%5fLIB_LLCPT%5fLIB_2__LLIBELL%5fVAL"] = "on"
            json_data["[t:dbt%3adate;]data_Fichiers_Recherche_CRITERIA_DAT%255fMIN"] = ""
            json_data["[t:dbt%3adate;]data_Fichiers_Recherche_CRITERIA_DAT%255fMAX"] = ""
            resp_reactivate_n43 = s.post(
                "https://www.targobank.es/es/banque/teletrans/transfert/sefw.aspx",
                params=req_params,
                headers=self.req_headers,
                data=json_data,
                proxies=self.req_proxies
            )
            if resp_reactivate_n43.status_code != 200:
                self.logger.warning('Could not reactivate file {}: {}'.format(index, n43_file_reactivate_info['id']))

        return True

    def process_access_for_43(self, s: MySession, resp_logged_in: Response) -> bool:
        # Bank has file names with current day date so use offset_days=0.
        date_from, date_to = self.basic_get_n43_dates_for_access(offset_days=0)
        date_from_str = date_from.strftime('%d/%m/%Y')
        date_to_str = date_to.strftime('%d/%m/%Y')

        resp_n43_status = s.get(
            'https://www.targobank.es/es/banque/teletrans/transfert/sefw.aspx',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if any(m in resp_n43_status.text for m in N43_INACTIVE_STATUS_MARKERS):
            self.logger.warning(
                'N43 activation status: not activated. Skip '
                'Pls, ask the customer to activate this contract')
            self.__is_detected_inactive_contract_for_n43 = True
            return False

        # After download a file from available the file is archived but can be reactivated and
        # redownloeaded. We search arvhived files at bank and reactivate it if needed. This avoids
        # missing files if customer already downloaded file.
        archive_n43_url = parse_helpers_n43.get_n43_archive_url(resp_n43_status.text)
        resp_archive_n43 = s.get(
            archive_n43_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )
        # Reactivate already donwloaded files based on date_from and date_to
        self.reactivate_n43_for_download_at_bank(s, resp_archive_n43, date_from_str, date_to_str)

        # After reactivating reload page with files.
        page_n43_url = parse_helpers_n43.get_n43_url(resp_n43_status.text)
        resp_n43_page = s.get(
            page_n43_url
        )

        n43_filters = parse_helpers_n43.get_n43_filter_params(resp_n43_page.text)
        form_action_url = parse_helpers_n43.get_form_action_url(resp_n43_page.text)

        # Get files from available to download filtered by date.
        resp_n43_filtered = self.get_n43_filtered(s, n43_filters, date_from_str, date_to_str, form_action_url)

        reason = ''
        for m in N43_TECH_PROBLEMS_MARKERS:
            if m in resp_n43_filtered.text:
                reason = m

        if reason:
            self.logger.error('Can not scrape N43 content due to reason: {}'.format(reason))
            return False

        n43_files_download_info = parse_helpers_n43.get_n43_files_download_info(resp_n43_filtered.text, date_from_str,
                                                                                date_to_str)

        if not n43_files_download_info:
            if date_funcs.is_weekend_day(date_to):
                # Check if N43 file should be available to download as bank doesn't provide
                # N43 file on Sunday and Monday (no movements at weekend)
                self.logger.info("No N43 file available to download: no movements at weekend. Abort".format(date_to))
                return True
            else:
                # No N43 file available to download
                self.logger.error("No N43 file available to download. Try later")
                return False
        else:
            self.logger.info('Found {0} files to download from {1} to {2}'.format(
                len(n43_files_download_info),
                date_from_str,
                date_to_str))

        # Reverse files to order by date and get a ordered storage name: TES-TARGO-36202-20221117-141815-0.N43
        n43_files_download_info.reverse()
        for index, n43_file_download_info in enumerate(n43_files_download_info):
            self.logger.info('Try to download file {}: {}'.format(index, n43_file_download_info['id']))
            ok = self.download_n43_file(s, n43_file_download_info['link'])
            if ok:
                self.logger.info('Successfully downloaded file {}: {}'.format(index, n43_file_download_info['id']))
            else:
                self.logger.error('Could not download file {}: {}'.format(index, n43_file_download_info['id']))
                return False

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

        ok = self.process_access_for_43(s, resp_logged_in)
        self.basic_log_time_spent('GET N43')

        if not ok:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )

        if self.__is_detected_inactive_contract_for_n43:
            return result_codes.WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED, None

        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
