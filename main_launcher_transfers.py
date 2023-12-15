"""
main_launcher_transfers launches ONLY transfers scrapers,
it's different to main_launcher_receipts that launches
redefined receipts scrapers AND regular scrapers.
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.bbva_scraper.bbva_transfers_scraper import BBVATransfersScraper
from scrapers.bankinter_scraper.bankinter_transfers_scraper import BankinterTransfersScraper

__version__ = '1.1.0'
__changelog__ = """
1.1.0
BankinterTransfersScraper for transfers
1.0.0
BBVATransfersScraper for transfers
"""

if __name__ == '__main__':

    print('main_launcher_transfers: set FIN_ENTITY_ID_TO_SCRAPER ONLY for transfers scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.BBVA: BBVATransfersScraper,
        fids.BANKINTER: BankinterTransfersScraper,
    }

    print('main_launcher_transfers: start main_launcher')
    main_launcher.main('main_launcher_transfers')
