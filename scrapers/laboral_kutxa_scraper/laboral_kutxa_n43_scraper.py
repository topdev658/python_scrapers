from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult

from scrapers._basic_scraper.basic_scraper import BasicScraper
from .laboral_kutxa_n43__banca_online_scraper import LaboralKutxaN43BancaOnlineScraper
from .laboral_kutxa_n43__acceso_restringido_scraper import LaboralKutxaN43AccesoRestringidoScraper


__version__ = '1.0.0'

__changelog__ = """
1.0.0
init after renaming
"""


class LaboralKutxaN43Scraper(BasicScraper):
    scraper_name = 'LaboralKutxaN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]

        if access_type == 'Banca online':
            scraper = LaboralKutxaN43BancaOnlineScraper(scraper_params_common, proxies)
        elif access_type == 'Acceso restringido':
            scraper = LaboralKutxaN43AccesoRestringidoScraper(scraper_params_common, proxies)
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

    # N43 scrapers override even scrape() (it'll be called earlier than main())
    def scrape(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.scrape()
