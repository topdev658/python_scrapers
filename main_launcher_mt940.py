"""
main_launcher_pos launches ONLY POS scrapers (saving to pos... tables),
it's different to main_launcher_receipts that launches
redefined receipts scrapers AND regular scrapers.
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.ebury_scraper.ebury_mt940_scraper import EburyMT940Scraper

__version__ = '1.1.0'
__changelog__ = """
1.1.0
fids.EBURY_PRE
1.0.0
EburyMT940Scraper
"""

if __name__ == '__main__':
    log_prefix = 'main_launcher_mt940'

    print('{}: set FIN_ENTITY_ID_TO_SCRAPER ONLY for MT940 scrapers'.format(log_prefix))

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.EBURY: EburyMT940Scraper,
        fids.EBURY_PRE: EburyMT940Scraper,
    }

    print('{}: start main_launcher'.format(log_prefix))
    main_launcher.main(log_prefix, main_launcher.KIND_MT940)
