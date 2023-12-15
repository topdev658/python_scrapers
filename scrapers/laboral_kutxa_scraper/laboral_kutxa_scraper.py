from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult, AccountScraped, AccountParsed

from scrapers._basic_scraper.basic_scraper import BasicScraper
from .laboral_kutxa__banca_online_scraper import LaboralKutxaBancaOnlineScraper
from .laboral_kutxa__acceso_restringido_scraper import LaboralKutxaAccesoRestringidoScraper

__version__ = '1.0.0'

__changelog__ = """
1.0.0
init, new content after renaming
"""

class LaboralKutxaScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    due to too different scraping approaches"""

    scraper_name = 'LaboralKutxaScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)
        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]

        if access_type == 'Banca online':
            scraper = LaboralKutxaBancaOnlineScraper(scraper_params_common, proxies)
            self.access_type_scraper = scraper
        elif self.access_type == 'Acceso restringido':
            scraper = LaboralKutxaAccesoRestringidoScraper(scraper_params_common, proxies)
            self.access_type_scraper = scraper
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
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
