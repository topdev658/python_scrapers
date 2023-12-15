from typing import Optional

from project import settings as project_settings
from project.custom_types import (ScraperParamsCommon, MainResult
)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.abanca_scraper.abanca_goabanca_scraper import AbancaGoAbancaScraper
from scrapers.abanca_scraper.abanca_beabanca_n43_scraper import AbancaBeAbancaN43Scraper

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'

__version__ = '1.2.0'

__changelog__ = """
1.2.0
init: start regular AbancaGoAbancaScraper when there is no appropriate N43 scraper
1.1.0
added scrape: , deleted main:
1.0.0
"""

class AbancaN43Scraper(BasicScraper):
    """Since 201909 date_from must be >= today - 90 days:
    Para acceder a movimientos de más de 90 días de antigüedad,
    por seguridad y de acuerdo a la normativa europea de pagos (PSD2),
    debemos verificar su identidad antes de mostrar información de sus cuentas.
    """

    scraper_name = 'AbancaN43Scraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        super().__init__(scraper_params_common, proxies)

        access_type = self.access_type.strip()
        scraper = None  # type: Optional[BasicScraper]
        if access_type == 'Banca electrónica empresas':
            scraper = AbancaBeAbancaN43Scraper(scraper_params_common, proxies)
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