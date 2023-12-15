from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.arquiabanca_scraper.arquiabanca_from_ruralvia_scraper import ArquiaBankaFromRuralviaScraper
from scrapers.arquiabanca_scraper.arquiabanca_red_scraper import ArquiaBancaRedScraper

__version__ = '2.2.0'
__changelog__ = """
2.2.0
err if unknown access type instead of exn
2.1.1
upd type hints
2.1.0
Arquia (nuevo login) support
2.0.1
fixed docs
2.0.0
moved previous ArquiaBancaScraper to ArquiaBancaRedScraper
added support for ArquiaBankaFromRuralviaScraper
1.0.0
init
"""


class ArquiaBancaScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    due to too different scraping approaches"""

    scraper_name = 'ArquiaBanca'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.access_type_scraper = None  # type: Optional[BasicScraper]
        if self.access_type == 'Arquia (via Ruralvia)':
            self.logger.info('Select ArquiaBankaFromRuralviaScraper scraper')
            self.access_type_scraper = ArquiaBankaFromRuralviaScraper(scraper_params_common, proxies)
        elif self.access_type in ['Arquia Red', 'Arquia (nuevo login)']:
            self.logger.info('Select ArquiaBancaRedScraper scraper')
            self.access_type_scraper = ArquiaBancaRedScraper(scraper_params_common, proxies)
        else:
            self.logger.error('Unsupported access type: {}'.format(self.access_type))

    def main(self) -> MainResult:
        if self.access_type_scraper is None:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
