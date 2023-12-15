from typing import Optional

from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, MainResult
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.abanca_scraper.abanca_beabanca_receipts_scraper import AbancaBeAbancaReceiptsScraper
from scrapers.abanca_scraper.abanca_portugal_receipts_scraper import AbancaPortugalReceiptsScraper

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'

__version__ = '1.3.0'

__changelog__ = """
1.3.0 2023.10.20
init: added AbancaPortugalScraper
1.2.0
init: start regular AbancaGoAbancaScraper when there is no appropriate receipts scraper
1.0.0
"""


class AbancaReceiptsScraper(BasicScraper):

    scraper_name = 'AbancaReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if access_type == 'Banca electrónica empresas':
            scraper = AbancaBeAbancaReceiptsScraper(scraper_params_common, proxies)
        elif access_type == 'Banca Eletrónica de Empresas':
            scraper = AbancaPortugalReceiptsScraper(scraper_params_common, proxies)
        else:
            self.logger.error('Unimplemented access type: {}'.format(self.access_type))
            return

        self.logger.info(
            'Select {} scraper basing on access type "{}"'.format(
                scraper.scraper_name,
                self.access_type
            )
        )
        self.access_type_scraper = scraper

    def main(self) -> MainResult:
        self.logger.info('main: started')
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()