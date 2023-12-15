"""
main_launcher_leasing launches ONLY leasing scrapers,
"""

import main_launcher

from project import fin_entities_ids as fids
from scrapers.bankinter_scraper.bankinter_leasing_scraper import BankinterLeasingScraper
from scrapers.bbva_scraper.bbva_leasing_scraper import BBVALeasingScraper
from scrapers.bbva_scraper.bbva_es_empresas_leasing_scraper import BBVAEsEmpresasLeasingScraper
from scrapers.bankoa_scraper_from_ruralvia.bankoa_leasing_scraper import BankoaLeasingScraper
from scrapers.santander_scraper.santander_empresas_leasing_scraper__nuevo import SantanderEmpresasNuevoLeasingScraper

__version__ = '1.5.0'

__changelog__ = """
1.5.0 2023.07.28
JFM SantanderEmpresasNuevoScraper for leasing contracts and fees downloading
1.4.0
Changed to BBVAEsEmpresasLeasingScraper from BBVALeasingScraper to get invoice number for fees
1.3.0
JFM: BankoaLeasingScraper for leasing contracts and fees downloading
1.2.0
DAF: BBVALeasingScraper for leasing contracts and fees downloading
1.1.0
DAF: BankinterLeasingScraper for leasing contracts and fees downloading
"""

if __name__ == '__main__':

    print('main_launcher_leasing: set FIN_ENTITY_ID_TO_SCRAPER ONLY for leasing scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.BANKINTER: BankinterLeasingScraper,
        fids.BBVA: BBVAEsEmpresasLeasingScraper,
        fids.BANKOA: BankoaLeasingScraper,
        fids.SANTANDER: SantanderEmpresasNuevoLeasingScraper,
    }

    print('main_launcher_leasing: start main_launcher')
    main_launcher.main('main_launcher_leasing')
