from typing import Optional, Union

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from .santander_empresas_scraper_checks import SantanderEmpresasChecksScraper
from .santander_empresas_scraper_checks__nuevo import SantanderEmpresasNuevoChecksScraper
from .santander_particulares_scraper import SantanderParticularesScraper

__version__ = "1.1.1"

__changelog__ = """
1.1.1
more type hints
1.1.0
SantanderOrgWFilialesNuevoLoginChecksScraper support
1.0.0
DAF: init
"""


class SantanderChecksScraper(BasicScraper):
    """The class used to launch concrete scraper basing on access type
    due to too different scraping approaches
    """

    scraper_name = 'SantanderChecksScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if access_type == 'Particulares':
            # receipts not implemented for Particulares
            scraper = SantanderParticularesScraper(scraper_params_common, proxies)
        elif access_type == 'Empresas (nuevo)':
            scraper = SantanderEmpresasNuevoChecksScraper(scraper_params_common, proxies)
        else:
            scraper = SantanderEmpresasChecksScraper(scraper_params_common, proxies)

        self.logger.info(
            'Select {} scraper basing on access type "{}"'.format(
                scraper.scraper_name,
                self.access_type
            )
        )
        self.access_type_scraper = scraper

    def main(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
