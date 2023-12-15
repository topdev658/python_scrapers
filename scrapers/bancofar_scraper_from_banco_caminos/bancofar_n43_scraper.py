from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers.ruralvia_scraper.ruralvia_n43_scraper import RuralviaN43Scraper
from .bancofar_scraper import BancofarScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init
"""


class BancofarN43Scraper(BancofarScraper, RuralviaN43Scraper):
    scraper_name = 'BancofarN43Scraper'
    fin_entity_name = 'BANCOFAR'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)

    def main(self) -> MainResult:
        self.logger.info('Main: started')

        # 1 contract support now
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login_to_sso()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        # From Ruralvia
        ok = self.process_access_for_n43(s, resp_logged_in)

        self.basic_log_time_spent('GET N43 FILES')

        if not ok:
            return self.basic_result_common_scraping_error()

        self.basic_save_n43s(
            self.fin_entity_name,
            self.n43_contents
        )
        return self.basic_result_success()
