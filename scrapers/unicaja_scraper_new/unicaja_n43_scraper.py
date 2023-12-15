from typing import Dict, List

from custom_libs import n43_funcs
from custom_libs.myrequests import MySession
from project import settings as project_settings
from project.custom_types import AccountScraped, AccountParsed, ScraperParamsCommon, MainResult
from .unicaja_scraper import UnicajaScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""

NO_MOVEMENTS_MARKERS = [
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

    def process_account(
            self, s: MySession,
            token: str,
            org_title: str,
            account_parsed: AccountParsed,
            accounts_scraped_dict: Dict[str, AccountScraped]) -> bool:
        if not self.is_success:
            return False

        fin_ent_account_id = account_parsed['financial_entity_account_id']

        date_from, date_to, is_active_account = self.basic_get_n43_dates_and_account_status(
            fin_ent_account_id
        )

        if not is_active_account:
            return True

        self.logger.info('{}: {}: process_account for N43 from {} to {}'.format(
            org_title,
            fin_ent_account_id,
            date_from.strftime(project_settings.SCRAPER_DATE_FMT),
            date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        ))

        req_n43_params = {
            'ppp': account_parsed['ppp_param'],
            'fechadesde': date_from.strftime('%Y-%m-%d'),  # '2022-02-28',
            'fechahasta': date_to.strftime('%Y-%m-%d'),  # '2022-06-01',
        }

        resp_n43_file = s.post(
            'https://univia.unicajabanco.es/services/rest/api/cuentas/movimientos/ficheroCSB',
            data=req_n43_params,
            headers=self.basic_req_headers_updated({
                'tokenCSRF': token,
            }),
            proxies=self.req_proxies
        )

        n43_text = resp_n43_file.text
        if any(marker in n43_text for marker in NO_MOVEMENTS_MARKERS):
            self.logger.warning(
                "{}: N43 no movements detected, no file generated. Skip. CONTENT:\n{}".format(
                    fin_ent_account_id,
                    resp_n43_file.text
                ))
            return True

        n43_content = n43_text.encode('UTF-8')

        if not n43_funcs.validate(n43_content):
            self.basic_log_wrong_layout(
                resp_n43_file,
                "{}: got invalid res_n43 (wrong N43 content)".format(fin_ent_account_id)
            )
            self.is_success = False  # don't allow further scraping
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
        self.logger.info('{}: {}: downloaded N43 file'.format(org_title, fin_ent_account_id))
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
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()

    def scrape(self) -> MainResult:
        return self.basic_scrape_for_n43()
