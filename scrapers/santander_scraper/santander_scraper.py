from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from .santander_empresas_scraper import SantanderEmpresasScraper
from scrapers.santander_scraper.santander_empresas_scraper__nuevo import SantanderEmpresasNuevoScraper
from scrapers.santander_scraper.santander_particulares_scraper import SantanderParticularesScraper

__version__ = "2.2.0"
__changelog__ = """
2.2.0
Particulares (CIF) support
2.1.2
more type hints
2.1.1
new imports (renamed files)
2.1.0
SantanderOrgWFilialesNuevoLoginScraper
2.0.0
Facade that calls SantanderParticularesScraper or SantanderOrgWFililesScraper basing on access type
"""


class SantanderScraper(BasicScraper):
    scraper_name = 'SantanderScraper'

    """The class used to launch concrete scraper basing on access type
    due to too different scraping approaches"""

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if 'Particulares' in access_type:  # 'Particulares' and 'Particulares (CIF)'
            scraper = SantanderParticularesScraper(scraper_params_common, proxies)
        elif access_type == 'Empresas (nuevo)':
            scraper = SantanderEmpresasNuevoScraper(scraper_params_common, proxies)
        else:
            scraper = SantanderEmpresasScraper(scraper_params_common, proxies)

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
