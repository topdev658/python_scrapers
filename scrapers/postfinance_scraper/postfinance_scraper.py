from typing import Tuple

from custom_libs import myrequests
from custom_libs.myrequests import MySession, Response
from project import result_codes
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon
from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '0.2.0'

__changelog__ = """
0.2.0
Log -> Not implemented
removed 'WIP' code
0.1.0
init
"""


class PostfinanceScraper(BasicScraper):

    scraper_name = 'PostFinanceScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    # TODO WIP, see origin/vb-postfinance-init

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = myrequests.session()
        resp_login_step2 = Response()
        reason = 'Not implemented'
        return s, resp_login_step2, False, False, reason

    def process_access(self, s: MySession, resp_logged_in: Response) -> bool:
        return True

    def main(self):
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        is_success = self.process_access(s, resp_logged_in)
        self.basic_log_time_spent('GET MOVEMENTS')
        if not is_success:
            return result_codes.ERR_COMMON_SCRAPING_ERROR, None

        return self.basic_result_success()
