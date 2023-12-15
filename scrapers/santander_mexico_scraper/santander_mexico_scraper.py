from typing import Tuple
from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper

__version__ = '0.1.0'

__changelog__ = """
0.1.0
Add login
with the log "not implemented"
"""


class SantanderMexicoScraper(BasicScraper):
    scraper_name = 'SantanderMexicoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    # TODO impl

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        resp_logged_in = Response()
        is_logged = False
        is_credentials_error = False
        reason = 'Not implemented'
        return s, resp_logged_in, is_logged, is_credentials_error, reason

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )
        is_success = False
        if not is_success:
            return self.basic_result_common_scraping_error()
        return self.basic_result_success()
