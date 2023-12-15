"""
main_launcher_n43 launches ONLY n43 scrapers
IMPORTANT
Can't use it for 'scrape all customers' approach because N43 accesses are mostly
for customers those are not in ActiveCustomersForNightlyBatch.
So, always run it with explicit -u and/or -a args.
For nightly scraping use main_launcher_n43_nightly_batch - it will call this script
with specific -a args.
"""

import main_launcher
from custom_libs.log import log
from project import fin_entities_ids as fids
from scrapers.abanca_scraper.abanca_n43_scraper import AbancaN43Scraper
from scrapers.arquiabanca_scraper.arquiabanca_n43_scraper import ArquiaBancaN43Scraper
from scrapers.banca_march_scraper.banca_march_n43_scraper import BancaMarchN43Scraper
from scrapers.bancofar_scraper_from_banco_caminos.bancofar_n43_scraper import BancofarN43Scraper
from scrapers.bankia_scraper_from_caixa.bankia_n43_scraper import BankiaN43Scraper
from scrapers.bankinter_scraper_new.bankinter_n43_scraper import BankinterN43Scraper
from scrapers.bankoa_scraper_from_ruralvia.bankoa_n43_scraper import BankoaN43Scraper
from scrapers.bantierra_scraper_from_ruralvia.bantierra_n43_scraper import BantierraN43Scraper
from scrapers.bbva_scraper.bbva_n43_scraper import BBVAN43Scraper
from scrapers.caixa_guissona.caixa_guissona_n43_scraper import CaixaGuissonaN43Scraper
from scrapers.caixa_scraper.caixa_n43_scraper import CaixaN43Scraper
from scrapers.caja_rural_central_scraper_from_ruralvia.caja_rural_central_n43_scraper import CajaRuralCentralN43Scraper
from scrapers.caja_rural_de_navarra_scraper_from_ruralvia.caja_rural_de_navarra_n43_scraper import (
    CajaRuralDeNavarraN43Scraper
)
from scrapers.caja_rural_del_sur_scraper_from_ruralvia.caja_rural_del_sur_n43_scraper import CajaRuralDelSurN43Scraper
from scrapers.caja_rural_granada_scraper_from_ruralvia.caja_rural_granada_n43_scraper import CajaRuralGranadaN43Scraper
from scrapers.caja_rural_zamora_scraper_from_ruralvia.caja_rural_zamora_n43_scraper import CajaRuralZamoraN43Scraper
from scrapers.cajamar_scraper.cajamar_n43_scraper import CajamarN43Scraper
from scrapers.cajasur_from_kutxa.cajasur_n43_scraper import CajasurN43craper
from scrapers.eurocaja_rural_scraper_from_ruralvia.eurocaja_rural_n43_scraper import EurocajaRuralN43Scraper
from scrapers.global_caja_scraper_from_ruralvia.global_caja_n43_scraper import GlobalCajaN43Scraper
from scrapers.iber_caja_scraper.iber_caja_newweb_n43_scraper import IberCajaN43Scraper
from scrapers.kutxabank_scraper.kutxa_n43_scraper import KutxaN43Scraper
from scrapers.laboral_kutxa_scraper.laboral_kutxa_n43_scraper import LaboralKutxaN43Scraper
from scrapers.liberbank_scraper.liberbank_n43_scraper import LiberbankN43Scraper
from scrapers.pichincha_scraper_from_ruralvia.pichincha_n43_scraper import PichinchaN43Scraper
from scrapers.popular_scraper_from_santander.popular_n43_scraper import PopularN43Scraper
from scrapers.ruralvia_scraper.ruralvia_n43_scraper import RuralviaN43Scraper
from scrapers.sabadell_scraper.sabadell_n43_scraper import SabadellN43Scraper
from scrapers.santander_scraper.santander_n43_scraper import SantanderN43Scraper
from scrapers.targo_scraper.targo_n43_scraper import TargoN43Scraper
from scrapers.unicaja_scraper_new.unicaja_n43_scraper import UnicajaN43Scraper

__version__ = '2.14.0'

__changelog__ = """
2.14.0 2023.11.07
main: changed log to print to let log bein initialized at main_launcher main. 
Otherwise log is initializad and descriptor set without custom file name.
2.13.0 2023.06.20
added CajaRuralCentralN43Scraper
2.12.0
TargoN43Scraper
2.11.0
use unicaja_scraper_new
2.10.0
use bankinter_scraper_new
2.9.0
use bancofar_scraper_from_banco_caminos.bancofar_n43_scraper
2.8.0
use scraper kind
2.7.0
ArquiaBancaN43scraper
2.6.0
bankia_scraper_from_caixa
2.5.0
BancoFarN43Scraper
2.4.0
BankoaN43Scraper
2.3.0
CajaRuralGranadaN43Scraper
2.2.0
CaixaGuissonaN43Scraper
2.1.0
BancamarchN43Scraper
2.0.0
access_ids
1.24.0
LiberbankN43Scraper
1.23.0
AbancaN43Scraper
1.22.0
CajasurN43craper
1.21.0
KutxaN43Scraper
1.20.0
PichinchaN43Scraper
1.19.0
BantierraN43Scraper
1.18.0
UnicajaN43Scraper
1.17.0
LaboralKutxaN43Scraper
1.16.0
IberCajaN43Scraper from iber_caja_newweb_n43_scraper
1.15.0
GlobalCajaN43Scraper
1.14.1
disabled Ibercaja
1.14.0
EurocajaRuralN43Scraper
CajaRuralDelSurN43Scraper
CajaRuralDeNavarraN43Scraper
CajaRuralZamoraN43Scraper
1.13.0
PopularN43Scraper
1.12.0
IberCajaN43Scraper
1.11.0
CaixaN43Scraper
1.10.0
SantanderN43Scraper for BANCOPOPULAR
1.9.0
CajamarN43Scraper
1.8.0
BBVAN43Scraper
1.7.0
Ruralvia43Scraper
1.6.0
BankiaN43Scraper
1.5.0
BankinterN43Scraper
1.4.0
SabadellN43Scraper
1.3.0
check for args: -u/-a must be provided
important docs for nightly usage
1.2.0
override FINANCIAL_ENTITIES_TO_SCRAPE (only necessary fids remain)
1.1.0
override green tunnel interval
1.0.0
SantanderN43Scraper
"""

if __name__ == '__main__':
    # Don't allow processing of all accesses similar way as for 'movement scraping',
    # because N43 accesses don't intersect with regular accesses,
    # thus this is not desired behavior for this scraper.
    # But, if you want to scrape exact -u/-a for N43, then it's OK.
    _, args = main_launcher.parse_cmdline_args()
    customer_id = args.user_id
    fin_ent_access_ids = args.access_ids
    if not (customer_id or fin_ent_access_ids):
        print('main_launcher_n43 MUST be used with -u/-a args. '
              'Or use main_launcher_n43_nightly_batch. Exit now')
        exit(0)

    print('main_launcher_n43: set FIN_ENTITY_ID_TO_SCRAPER ONLY for n43 scrapers')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER = {
        fids.SANTANDER: SantanderN43Scraper,
        fids.BANCOPOPULAR: PopularN43Scraper,
        fids.SABADELL: SabadellN43Scraper,
        fids.BANKINTER: BankinterN43Scraper,
        fids.BANKIA: BankiaN43Scraper,
        fids.CAJA_RURAL: RuralviaN43Scraper,
        fids.BBVA: BBVAN43Scraper,
        fids.CAJAMAR: CajamarN43Scraper,
        fids.CAIXA: CaixaN43Scraper,
        fids.IBER_CAJA: IberCajaN43Scraper,
        fids.EUROCAJA_RURAL: EurocajaRuralN43Scraper,
        fids.CAJA_RURAL_DEL_SUR: CajaRuralDelSurN43Scraper,
        fids.CAJA_RURAL_DE_NAVARRA: CajaRuralDeNavarraN43Scraper,
        fids.CAJA_RURAL_ZAMORA: CajaRuralZamoraN43Scraper,
        fids.GLOBAL_CAJA: GlobalCajaN43Scraper,
        fids.LABORAL_KUTXA: LaboralKutxaN43Scraper,
        fids.UNICAJA: UnicajaN43Scraper,
        fids.BANTIERRA: BantierraN43Scraper,
        fids.PICHINCA: PichinchaN43Scraper,
        fids.KUTXABANK: KutxaN43Scraper,
        fids.CAJASUR: CajasurN43craper,
        fids.ABANCA: AbancaN43Scraper,
        fids.LIBERBANK: LiberbankN43Scraper,
        fids.BANCA_MARCH: BancaMarchN43Scraper,
        fids.CAIXA_GUISSONA: CaixaGuissonaN43Scraper,
        fids.CAJA_RURAL_GRANADA: CajaRuralGranadaN43Scraper,
        fids.BANKOA: BankoaN43Scraper,
        fids.BANCOFAR: BancofarN43Scraper,
        fids.ARQUIABANCA: ArquiaBancaN43Scraper,
        fids.TARGO: TargoN43Scraper,
        fids.CAJA_RURAL_CENTRAL: CajaRuralCentralN43Scraper
    }

    # Allow full scraping for N43 scrapers
    # to avoid be affected by general scraper results
    # (for further usage, doesn't make sense until ActiveCustomersForNightlyBatch is used)
    # project_settings.GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING = (0, 24)
    # log('Override: project.settings.GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING = {}'.format(
    #     project_settings.GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING))

    print('main_launcher_n43: start main_launcher')
    main_launcher.main('main_launcher_n43', kind=main_launcher.KIND_N43)
