import main_launcher
from project import fin_entities_ids as fids
from scrapers.abanca_scraper.abanca_receipts_scraper import AbancaReceiptsScraper
from scrapers.abanca_scraper.abanca_portugal_receipts_scraper import AbancaPortugalReceiptsScraper
from scrapers.banca_march_scraper.banca_march_receipts_scraper import BancaMarchReceiptsScraper
from scrapers.bankia_scraper_from_caixa.bankia_receipts_scraper import BankiaReceiptsScraper
from scrapers.bankinter_scraper.bankinter_receipts_scraper import BankinterReceiptsScraper
from scrapers.bbva_scraper.bbva_receipts_scraper import BBVAReceiptsScraper
from scrapers.caixa_scraper.caixa_regular_receipts_scraper import CaixaReceiptsScraper
from scrapers.caja_rural_de_aragon_scraper_from_ruralvia.caja_rural_de_aragon_receipts_scraper import \
    CajaRuralDeAragonReceiptsScraper
from scrapers.caja_rural_de_navarra_scraper_from_ruralvia.caja_rural_de_navarra_receipts_scraper import (
    CajaRuralDeNavarraReceiptsScraper
)
from scrapers.cajamar_scraper.cajamar_receipts_scraper import CajamarReceiptsScraper
from scrapers.cajasur_from_kutxa.cajasur_receipts_scraper import CajasurReceiptsScraper
from scrapers.deutschebank_scraper.deutschebank_receipts_scraper import DeutscheBankReceiptsScraper
from scrapers.global_caja_scraper_from_ruralvia.global_caja_receipts_scraper import GlobalCajaReceiptsScraper
from scrapers.iber_caja_scraper.iber_caja_newweb_receipts_scraper import IberCajaReceiptsScraper
from scrapers.kutxabank_scraper.kutxa_receipts_scraper import KutxaReceiptsScraper
from scrapers.laboral_kutxa_scraper.laboral_kutxa_receipts_scraper import LaboralKutxaReceiptsScraper
from scrapers.liberbank_scraper.liberbank_receipts_scraper import LiberbankReceiptsScraper
from scrapers.popular_scraper_from_santander.popular_receipts_scraper import PopularReceiptsScraper
from scrapers.ruralvia_scraper.ruralvia_receipts_scraper import RuralviaReceiptsScraper
from scrapers.sabadell_scraper.sabadell_receipts_scraper import SabadellReceiptsScraper
from scrapers.santander_scraper.santander_receipts_scraper import SantanderReceiptsScraper
from scrapers.targo_scraper.targo_receipts_scraper import TargoReceiptsScraper
from scrapers.unicaja_scraper_new.unicaja_receipts_scraper import UnicajaReceiptsScraper
from scrapers.caja_rural_granada_scraper_from_ruralvia.caja_rural_granada_receipts_scraper import (
    CajaRuralGranadaReceiptsScraper
)
from scrapers.caja_rural_central_scraper_from_ruralvia.caja_rural_central_receipts_scraper import (
    CajaRuralCentralReceiptsScraper
)
from scrapers.caja_rural_del_sur_scraper_from_ruralvia.caja_rural_del_sur_receipts_scraper import (
    CajaRuralDelSurReceiptsScraper
)
from scrapers.caja_ingenieros_scraper_from_caixa_geral.caja_ingenieros_receipts_scraper import (
    CajaIngenierosReceiptsScraper
)
from scrapers.pichincha_scraper_from_ruralvia.pichincha_receipts_scraper import PichinchaReceiptsScraper

__version__ = '1.32.0'

__changelog__ = """
1.32.0 2023.10.20
AbancaPortugalReceiptsScraper
1.31.0 2023.07.13
CajaRuralDeAragonReceiptsScraper
1.30.0 2023.06.30
added GlobalCajaReceiptsScraper
1.29.0 2023.06.14
PichinchaReceiptsScraper
1.28.0 2023.04.25
CajaIngenierosReceiptsScraper
1.27.0
CajaRuralGranadaReceiptsScraper
CajaRuralCentralReceiptsScraper
CajaRuralDelSurReceiptsScraper
1.26.0
use new UnicajaReceiptsScraper
1.25.0
disabled old-web-based UnicajaReceiptsScraper (not working)
1.24.0
bankia_scraper_from_caixa
1.23.0
TargoReceiptsScraper
1.22.0
PopularReceiptsScraper
1.21.0
renamed CajaEspanaReceiptsScraper to UnicajaReceiptsScraper
1.20.0
enabled IberCajaReceiptsScraper from iber_caja_newweb_receipts_scraper
1.19.0
disabled IberCajaReceiptsScraper
1.18.0
CajasurReceiptsScraper
1.17.0
CajaRuralDeNavarraReceiptsScraper
1.16.0
KutxaReceiptsScraper
1.15.0
RuralviaReceiptsScraper
1.14.0
CajamarReceiptsScraper
1.13.0
CajaEspanaReceiptsScraper
UnicajaReceiptsScraper
1.12.0
IberCajaReceiptsScraper
1.11.0
AbancaReceiptsScraper
1.10.0
LaboralKutxaReceiptsScraper
1.9.0
LiberbankReceiptsScraper
1.8.0
DeutscheBankReceiptsScraper
1.7.0
BancaMarchReceiptsScraper
1.6.1
fmt
1.6.0
SantanderReceiptsScraper
1.5.0
call main_launcher with logger_prefix
1.4.1
BBVAReceiptsScraper for RECEIPTS downloading
1.4.0
DAF: BBVAReceiptsScraper for check downloading
1.3.0
DAF: CaixaReceiptsScraper
1.2.0
BankinterReceiptsScraper
1.1.0
SabadellReceiptsScraper
1.0.0
BankiaReceiptsScraper
"""

if __name__ == '__main__':
    print('main_launcher_receipts: redefine FIN_ENTITY_ID_TO_SCRAPER')

    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.BANKIA] = BankiaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.BANKINTER] = BankinterReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.BBVA] = BBVAReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAIXA] = CaixaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.SABADELL] = SabadellReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.SANTANDER] = SantanderReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.BANCA_MARCH] = BancaMarchReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.DEUTSCHE_BANK] = DeutscheBankReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.LIBERBANK] = LiberbankReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.LABORAL_KUTXA] = LaboralKutxaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.ABANCA] = AbancaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.IBER_CAJA] = IberCajaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.UNICAJA] = UnicajaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJAMAR] = CajamarReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL] = RuralviaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.KUTXABANK] = KutxaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL_DE_NAVARRA] = CajaRuralDeNavarraReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJASUR] = CajasurReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.BANCOPOPULAR] = PopularReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.TARGO] = TargoReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL_GRANADA] = CajaRuralGranadaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL_CENTRAL] = CajaRuralCentralReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL_DEL_SUR] = CajaRuralDelSurReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_INGENIEROS] = CajaIngenierosReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.PICHINCA] = PichinchaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.GLOBAL_CAJA] = GlobalCajaReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.CAJA_RURAL_DE_ARAGON] = CajaRuralDeAragonReceiptsScraper
    main_launcher.FIN_ENTITY_ID_TO_SCRAPER[fids.ABANCA_PORTUGAL] = AbancaPortugalReceiptsScraper

    print('main_launcher_receipts: start main_launcher')
    main_launcher.main('main_launcher_receipts')
