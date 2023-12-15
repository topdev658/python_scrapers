"""
main_launcher_checks launches ONLY checks scrapers,
it's different to main_launcher_receipts that launches
redefined receipts scrapers AND regular scrapers.
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.bbva_scraper.bbva_checks_scraper import BBVAChecksScraper
from scrapers.sabadell_scraper.sabadell_checks_scraper import SabadellChecksScraper
from scrapers.santander_scraper.santander_checks_scraper import SantanderChecksScraper
__version__ = '1.2.0'

__changelog__ = """
1.2.0
SantanderChecksScraper for check downloading
1.1.0
SabadellChecksScraper for check downloading
1.0.0
BBVAChecksScraper for check downloading
"""

if __name__ == '__main__':

    print('main_launcher_checks: set FIN_ENTITY_ID_TO_SCRAPER ONLY for checks scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.BBVA: BBVAChecksScraper,
        fids.SABADELL: SabadellChecksScraper,
        fids.SANTANDER: SantanderChecksScraper
    }

    print('main_launcher_checks: start main_launcher')
    main_launcher.main('main_launcher_checks')
