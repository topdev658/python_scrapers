from typing import Optional, Union

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult
from scrapers._basic_scraper.basic_scraper import BasicScraper
from .santander_empresas_leasing_scraper__nuevo import SantanderEmpresasNuevoLeasingScraper

__version__ = "1.0.0"
__changelog__ = """
1.0.0
init
"""


class SantanderLeasingScraper(BasicScraper):
    """The class used to launch concrete scraper basing on access type
    due to too different scraping approaches

    For now, only accesses with 'Empresas (nuevo)' access type
    can download receipts.
    All access types use regular scrapers without receipts functionality.

    More over:
    only 'Empresas (nuevo)' WITH multicontract could download receipts
    (also, from website it is possible to download receipts
    only for 'Empresas (nuevo)' with multicontract,
    example -u 286616 -a 18101)
    """

    scraper_name = 'SantanderLeasingScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if access_type == 'Empresas (nuevo)':
            scraper = SantanderEmpresasNuevoLeasingScraper(scraper_params_common, proxies)
        else:
            self.logger.error('UNSUPPORTED access type: {}'.format(self.access_type))

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
