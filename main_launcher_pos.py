"""
main_launcher_pos launches ONLY POS scrapers (saving to pos... tables),
it's different to main_launcher_receipts that launches
redefined receipts scrapers AND regular scrapers.
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.sabadell_scraper.sabadell_pos_scraper import SabadellPOSScraper

__version__ = '2.0.0'
__changelog__ = """
2.0.0
SabadellPOSScraper
removed RedsysTPVScraper scraper (it's in main_launcher_tpv)
"""

if __name__ == '__main__':

    print('main_launcher_pos: set FIN_ENTITY_ID_TO_SCRAPER ONLY for POS scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.SABADELL: SabadellPOSScraper
    }

    print('main_launcher_pos: start main_launcher')
    main_launcher.main('main_launcher_pos')
