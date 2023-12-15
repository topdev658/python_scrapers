from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.bbva_scraper.bbva_netcash_receipts_scraper import BBVANetcashReceiptsScraper
from scrapers.bbva_scraper.bbva_particulares_scraper import BBVAParticularesScraper

__version__ = '1.2.1'

__changelog__ = """
1.2.1
upd type hints
1.2.0
BBVAParticularesScraper for appropriate access type
1.1.0
exception -> error on unsupported access type
1.0.1
inherits BasicScraper instead of BBVAScraper
fixed scraper_name
1.0.0
init
"""


class BBVAReceiptsScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    due to too different scraping approaches"""

    scraper_name = 'BBVAReceiptsScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        self.access_type_scraper = None  # type: Optional[BasicScraper]
        if self.access_type == 'BBVA net cash':
            self.access_type_scraper = BBVANetcashReceiptsScraper(scraper_params_common, proxies)
            self.logger.info('Select BBVANetcashReceiptsScraper scraper')
        elif self.access_type == 'BBVA Particulares':
            # NOTE: BBVAParticularesScraper, not BBVAParticularesReceiptsScraper (it's not implemented)
            self.access_type_scraper = BBVAParticularesScraper(scraper_params_common, proxies)
            self.logger.info('Select BBVAParticulares scraper')
        else:
            self.logger.error('UNSUPPORTED access type: {}'.format(self.access_type))

    def main(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
