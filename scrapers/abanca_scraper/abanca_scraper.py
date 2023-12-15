from typing import Optional

from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, MainResult
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.abanca_scraper.abanca_goabanca_scraper import AbancaGoAbancaScraper
from scrapers.abanca_scraper.abanca_online_scraper import AbancaOnlineScraper
from scrapers.abanca_scraper.abanca_portugal_scraper import AbancaPortugalScraper

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'

__version__ = '1.1.0'

__changelog__ = """
1.1.0
added AbancaPortugalScraper
1.0.0
"""

class AbancaScraper(BasicScraper):

    scraper_name = 'AbancaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if access_type == 'GO ABANCA Empresas':
            scraper = AbancaGoAbancaScraper(scraper_params_common, proxies)
        elif access_type == 'Banca electrónica empresas':
            scraper = AbancaOnlineScraper(scraper_params_common, proxies)
        elif access_type == 'Banca Eletrónica de Empresas':
            scraper = AbancaPortugalScraper(scraper_params_common, proxies)
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