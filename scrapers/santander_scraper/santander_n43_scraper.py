from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from .santander_empresas_n43_scraper import SantanderEmpresasN43Scraper
from .santander_empresas_n43_scraper__nuevo import SantanderEmpresasNuevoN43Scraper

__version__ = "1.0.1"
__changelog__ = """
1.0.1
fixed logger level
1.0.0
Calls SantanderParticularesScraper or SantanderOrgWFililesScraper basing on access type
"""


class SantanderN43Scraper(BasicScraper):
    """The class used to launch concrete scraper basing on access type
    due to too different scraping approaches (mediator)
    """

    scraper_name = 'SantanderN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        self.access_type_scraper = None  # type: Optional[BasicScraper]
        if access_type == 'Empresas (nuevo)':
            self.access_type_scraper = SantanderEmpresasNuevoN43Scraper(scraper_params_common, proxies)
        elif access_type == 'Empresas e Instituciones':  # inst
            self.access_type_scraper = SantanderEmpresasN43Scraper(scraper_params_common, proxies)
        else:
            self.logger.warning('Unsupported access_type for N43 processing: {}'.format(
                access_type
            ))
            return

        self.logger.info(
            'Selected {} scraper basing on access type "{}"'.format(
                self.access_type_scraper.scraper_name,
                self.access_type
            )
        )

    # N43 scrapers override even scrape() (it'll be called earlier than main())
    def scrape(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.scrape()
