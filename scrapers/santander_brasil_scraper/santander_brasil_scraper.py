from typing import Optional

from project import settings as project_settings
from project.custom_types import ScraperParamsCommon, MainResult

from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.santander_brasil_scraper.santander_brasil_default_scraper import SantanderBrasilDefaultScraper
from scrapers.santander_brasil_scraper.santander_brasil_novo_scraper import SantanderBrasilNovoScraper


__version__ = '2.1.0'
__changelog__ = """
2.1.0
upd type hints
err if unsupported scraper instead of exn
2.0.0
moved previous SantanderBrasilScraper to SantanderBrasilDefaultScraper
added support for SantanderBrasilNovoScraper
1.0.0
init
"""


class SantanderBrasilScraper(BasicScraper):
    """The class used to launch concrete scraper based on access type
    because of two different scraping approaches.
    It doesn't provides shared methods to keep more clear structure
    and to avoid recursive inheritance.
    It inherits BasicScraper only for self.access_type and to pass
    external type checks.
    """

    scraper_name = 'SantanderBrasilScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        # only to provide access_type
        super().__init__(scraper_params_common, proxies)

        scraper = None  # type: Optional[BasicScraper]
        if self.access_type == 'Pessoa Jurídica':
            self.logger.info('Select SantanderBrasilDefaultScraper scraper')
            scraper = SantanderBrasilDefaultScraper(scraper_params_common, proxies)
        elif self.access_type == 'Pessoa Juridica (Novo)':
            self.logger.info('Select SantanderBrasilNovoScraper scraper')
            scraper = SantanderBrasilNovoScraper(scraper_params_common, proxies)
        else:
            self.logger.error('Unsupported access type: {}'.format(self.access_type))

        self.access_type_scraper = scraper

    def main(self) -> MainResult:
        if not self.access_type_scraper:
            return self.basic_result_common_scraping_error()

        return self.access_type_scraper.main()
