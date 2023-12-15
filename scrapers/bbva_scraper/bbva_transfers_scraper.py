from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_scraper.bbva_netcash_transfers_scraper import BBVANetcashTransfersScraper


__version__ = '1.0.1'

__changelog__ = """
1.0.1
deleted unused imports
1.0.0
init
"""


class BBVATransfersScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    due to too different scraping approaches"""

    scraper_name = 'BBVATransfersScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.access_type_scraper = None  # type: Optional[BasicScraper]
        if self.access_type == 'BBVA net cash':
            #self.access_type_scraper = BBVANetcashTransfersScraperMov(scraper_params_common, proxies)
            self.access_type_scraper = BBVANetcashTransfersScraper(scraper_params_common, proxies)
            self.logger.info('Select BBVANetcashTransfersScraper scraper')
        else:
            self.logger.error('UNSUPPORTED access type: {}'.format(self.access_type))

    def main(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
