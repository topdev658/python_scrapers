"""
main_launcher_tpv launches ONLY TPV scrapers (saving to tpv.. tables),
it's different to main_launcher_receipts that launches
redefined receipts scrapers AND regular scrapers.
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.redsys_scraper.redsys_tpv_scraper import RedsysTPVScraper

__version__ = '1.0.1'
__changelog__ = """
1.0.1
udp comment
1.0.0
Redsys for tpv
"""

if __name__ == '__main__':

    print('main_launcher_tpv: set FIN_ENTITY_ID_TO_SCRAPER ONLY for tpv scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.REDSYS: RedsysTPVScraper,
    }

    print('main_launcher_tpv: start main_launcher')
    main_launcher.main('main_launcher_tpv')
