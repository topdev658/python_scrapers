import argparse
import datetime
import logging
import os
import time
import traceback
from collections import defaultdict
from concurrent import futures
from threading import Lock
from typing import Dict, Any, List, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import state_reset
from custom_libs.db import db_funcs
from custom_libs.db import queue_simple
from custom_libs.log import log, log_err
from custom_libs.scrape_logger import ScrapeLogger
from project import fin_entities_ids as fids
from project import result_codes
from project import settings
from project.custom_types import (
    DBCustomer, DBCustomerToUpdateState, DBFinancialEntityAccess,
    DBFinancialEntityAccessWithCodesToUpdateState,
    ResultCode, RunnerOnDemandParams, ScraperParamsCommon,
)
from scrapers.abanca_scraper.abanca_scraper import AbancaScraper
from scrapers.alphabank_scraper.alphabank_scraper import AlphaBankScraper
from scrapers.arquiabanca_scraper.arquiabanca_scraper import ArquiaBancaScraper
from scrapers.banca_march_scraper.banca_march_scraper import BancaMarchScraper
from scrapers.banco_caminos_scraper.banco_caminos_scraper import BancoCaminosScraper
from scrapers.banco_cooperativo_scraper_from_ruralvia.banco_cooperativo_scraper import (
    BancoCooperativoScraper
)
from scrapers.banco_montepio_scraper.banco_montepio_scraper import BancoMontepioScraper
from scrapers.bancofar_scraper_from_banco_caminos.bancofar_scraper import BancofarScraper
from scrapers.bank_of_america_scraper.bank_of_america_scraper import BankOfAmericaScraper
from scrapers.bankia_scraper_from_caixa.bankia_scraper import BankiaScraper
from scrapers.bankinter_scraper.bankinter_scraper import BankinterScraper
from scrapers.bankoa_scraper_from_ruralvia.bankoa_scraper import BankoaScraper
from scrapers.bantierra_scraper_from_ruralvia.bantierra_scraper import BantierraScraper
from scrapers.bbva_continental_scraper.bbva_continental_scraper import BBVAContinentalScraper
from scrapers.bbva_scraper.bbva_scraper import BBVAScraper
from scrapers.bmn_scraper_from_bankia.bmn_scraper import BancoMareNostrumScraper
from scrapers.bnp_paribas_scraper.bnp_paribas_scraper import BNPParibasScraper
from scrapers.bpi_scraper.bpi_scraper import BPIScraper
from scrapers.bradesco_scraper.bradesco_scraper import BradescoScraper
from scrapers.caixa_callosa_scraper_from_cajamar.caixa_callosa_scraper import CaixaCallosaScraper
from scrapers.caixa_geral_depositos.caixa_geral_depositos_scraper import CaixaGeralDepositosScraper
from scrapers.caixa_geral_scraper_from_abanca.caixa_geral_scraper import CaixaGeralScraper
from scrapers.caixa_guissona.caixa_guissona_scraper import CaixaGuissonaScraper
from scrapers.caixa_popular_scraper_from_ruralvia.caixa_popular_scraper import CaixaPopularScraper
# from scrapers.caixa_scraper.caixa_scraper import CaixaScraper
from scrapers.caixa_scraper.caixa_regular_scraper import CaixaScraper
from scrapers.caixaltea_from_cajamar.caixaltea_scraper import CaixAlteaScraper
from scrapers.caixarural_vilareal_scraper_from_cajamar.caixarural_vilareal_scraper import CaixaRuralVilarealScraper
from scrapers.caja_almendralejo_scraper.caja_almendralejo_scraper import CajaAlmendralejoScraper
from scrapers.caja_ingenieros_scraper_from_caixa_geral.caja_ingenieros_scraper import CajaIngenierosScraper
from scrapers.caja_rural_castilla_scraper_from_ruralvia.caja_rural_castilla_scraper import (
    CajaRuralCastillaScraper
)
from scrapers.caja_rural_central_scraper_from_ruralvia.caja_rural_central import CajaRuralCentralScraper
from scrapers.caja_rural_de_aragon_scraper_from_ruralvia.caja_rural_de_aragon_scraper import CajaRuralDeAragonScraper
from scrapers.caja_rural_de_navarra_scraper_from_ruralvia.caja_rural_de_navarra_scraper import (
    CajaRuralDeNavarraScraper
)
from scrapers.caja_rural_del_sur_scraper_from_ruralvia.caja_rural_del_sur_scraper import CajaRuralDelSurScraper
from scrapers.caja_rural_granada_scraper_from_ruralvia.caja_rural_granada_scraper import CajaRuralGranadaScraper
from scrapers.caja_rural_salamanca_scraper_from_ruralvia.caja_rural_salamanca_scraper import CajaRuralSalamancaScraper
from scrapers.caja_rural_soria_scraper_from_ruralvia.caja_rural_soria_scraper import CajaRuralSoriaScraper
from scrapers.caja_rural_zamora_scraper_from_ruralvia.caja_rural_zamora_scraper import CajaRuralZamoraScraper
from scrapers.cajamar_scraper.cajamar_scraper import CajamarScraper
from scrapers.cajasur_from_kutxa.cajasur_scraper import CajasurScraper
from scrapers.castilla_la_mancha_liberbank_from_liberbank.castilla_la_mancha_liberbank_scraper import (
    CastillaLaManchaLiberbankScraper
)
from scrapers.credito_agricola_scraper.credito_agricola_scraper import CreditoAgricolaScraper
from scrapers.deutschebank_scraper.deutschebank_scraper import DeutscheBankScraper
from scrapers.ebn_scraper.ebn_scraper import EbnScraper
from scrapers.eurobic_scraper.eurobic_scraper import EuroBicScraper
from scrapers.eurocaja_rural_scraper.eurocaja_rural_scraper import EurocajaRuralScraper
from scrapers.fiare_banca_etica_scraper_from_ruralvia.fiare_banca_etica_scraper import FiareBancaEticaScraper
from scrapers.global_caja_scraper_from_ruralvia.global_caja_scraper import GlobalCajaScraper
# from scrapers.iber_caja_scraper.iber_caja_scraper import IberCajaScraper
from scrapers.iber_caja_scraper.iber_caja_newweb_scraper import IberCajaScraper
from scrapers.ing_scraper.ing_multicontract_scraper import IngMulticontractScraper
from scrapers.inversis_scraper.inversis_scraper import InversisScraper
from scrapers.kutxabank_scraper.kutxa_scraper import KutxaScraper
from scrapers.laboral_kutxa_scraper.laboral_kutxa_scraper import LaboralKutxaScraper
from scrapers.liberbank_scraper.liberbank_scraper import LiberbankScraper
from scrapers.novobanco_scraper.novobanco_scraper import NovobancoScraper
from scrapers.openbank_scraper.openbank_scraper import OpenbankScraper
from scrapers.pastor_from_popular.pastor_scraper import PastorScraper
from scrapers.paypal_scraper.paypal_scraper import PayPalScraper
from scrapers.pichincha_scraper_from_ruralvia.pichincha_scraper import PichinchaScraper
from scrapers.popular_dominicano_scraper.popular_dominicano_scraper import PopularDominicanoScraper
# from scrapers.popular_scraper.popular_scraper import PopularScraper
from scrapers.popular_scraper_from_santander.popular_scraper import PopularScraper
from scrapers.postfinance_scraper.postfinance_scraper import PostfinanceScraper
from scrapers.rbs_scraper.rbs_scraper import RBSScraper
from scrapers.renta4banco_scraper.renta4banco_scraper import Renta4BancoScraper
from scrapers.ruralvia_scraper.ruralvia_scraper import RuralviaScraper
from scrapers.sabadell_miami_scraper.sabadell_miami_scraper import SabadellMiamiScraper
from scrapers.sabadell_scraper.sabadell_scraper import SabadellScraper
from scrapers.sabadell_uk_scraper.sabadell_uk_scraper import SabadellUKScraper
from scrapers.santander_brasil_scraper.santander_brasil_scraper import SantanderBrasilScraper
from scrapers.santander_chile_scraper.santander_chile_scraper import SantanderChileScraper
from scrapers.santander_scraper.santander_scraper import SantanderScraper
from scrapers.santander_totta_scraper.santander_totta_scraper import SantanderTottaScraper
from scrapers.santander_mexico_scraper.santander_mexico_scraper import SantanderMexicoScraper
from scrapers.societe_generale_scraper.societe_generale_scraper import SocieteGeneraleScraper
from scrapers.targo_scraper.targo_scraper import TargoScraper
from scrapers.triodos_scraper.triodos_scraper import TriodosScraper
from scrapers.unicaja_scraper_new.unicaja_scraper import UnicajaScraper
from scrapers.volkswagenbank_scraper_from_caixa_geral.volkswagenbank_scraper import VolkswagenBankScraper
from scrapers.caixa_rural_burriana_scraper_from_cajamar.caixa_rural_burriana_scraper import CaixaRuralBurrianaScraper
from scrapers.banca_pueyo_scraper.banca_pueyo_scraper import BancaPueyoScraper

FIN_ENTITY_ID_TO_SCRAPER = {
    fids.BBVA: BBVAScraper,
    fids.KUTXABANK: KutxaScraper,
    fids.BANCOPOPULAR: PopularScraper,
    fids.BANKIA: BankiaScraper,
    fids.CAIXA: CaixaScraper,
    fids.SANTANDER: SantanderScraper,
    fids.SABADELL: SabadellScraper,
    fids.DEUTSCHE_BANK: DeutscheBankScraper,
    fids.BANKINTER: BankinterScraper,
    fids.CAJA_RURAL: RuralviaScraper,
    fids.GLOBAL_CAJA: GlobalCajaScraper,
    fids.CAJA_RURAL_CASTILLA_LA_MANCHA: CajaRuralCastillaScraper,
    fids.CAIXA_POPULAR: CaixaPopularScraper,
    fids.PICHINCA: PichinchaScraper,
    fids.IBER_CAJA: IberCajaScraper,
    fids.CAJAMAR: CajamarScraper,
    fids.ABANCA: AbancaScraper,
    fids.LIBERBANK: LiberbankScraper,
    fids.CAIXA_GERAL: CaixaGeralScraper,
    fids.LABORAL_KUTXA: LaboralKutxaScraper,
    fids.ING: IngMulticontractScraper,
    fids.TARGO: TargoScraper,
    fids.OPENBANK: OpenbankScraper,
    fids.BANTIERRA: BantierraScraper,
    fids.CAJA_RURAL_GRANADA: CajaRuralGranadaScraper,
    fids.TRIODOS: TriodosScraper,
    fids.NOVOBANCO: NovobancoScraper,
    fids.BANCO_MARE_NOSTRUM: BancoMareNostrumScraper,
    fids.VOLKSWAGENBANK: VolkswagenBankScraper,
    fids.BANCO_CAMINOS: BancoCaminosScraper,
    fids.BANCA_MARCH: BancaMarchScraper,
    fids.CASTILLA_LA_MANCHA_LIBERBANK: CastillaLaManchaLiberbankScraper,
    fids.UNICAJA: UnicajaScraper,
    fids.CAJA_RURAL_DEL_SUR: CajaRuralDelSurScraper,
    fids.CAJASUR: CajasurScraper,
    fids.ARQUIABANCA: ArquiaBancaScraper,
    fids.PASTOR: PastorScraper,
    fids.CAIXALTEA: CaixAlteaScraper,
    fids.FIARE_BANCA_ETICA: FiareBancaEticaScraper,
    fids.CAJA_INGENIEROS: CajaIngenierosScraper,
    fids.BANKOA: BankoaScraper,
    fids.RENTA4BANCO: Renta4BancoScraper,
    fids.SOCIETE_GENERALE: SocieteGeneraleScraper,
    fids.CAIXARURAL_VILAREAL: CaixaRuralVilarealScraper,
    fids.BNP_PARIBAS: BNPParibasScraper,
    fids.BBVA_CONTINENTAL: BBVAContinentalScraper,
    fids.SANTANDER_BRASIL: SantanderBrasilScraper,
    fids.CAJA_RURAL_DE_NAVARRA: CajaRuralDeNavarraScraper,
    fids.CAJA_RURAL_SORIA: CajaRuralSoriaScraper,
    fids.CAJA_RURAL_SALAMANCA: CajaRuralSalamancaScraper,
    fids.CAJA_RURAL_ZAMORA: CajaRuralZamoraScraper,
    fids.SANTANDER_CHILE: SantanderChileScraper,
    fids.BANK_OF_AMERICA: BankOfAmericaScraper,
    fids.BANCOPOPULAR_DOMINICANO: PopularDominicanoScraper,
    fids.SANTANDER_TOTTA: SantanderTottaScraper,
    fids.RBS: RBSScraper,
    fids.BANCO_COOPERATIVO: BancoCooperativoScraper,
    fids.EUROCAJA_RURAL: EurocajaRuralScraper,
    fids.ALPHABANK: AlphaBankScraper,
    fids.BPI: BPIScraper,
    fids.EUROBIC: EuroBicScraper,
    fids.CREDITO_AGRICOLA: CreditoAgricolaScraper,
    fids.CAIXA_GERAL_DEPOSITOS: CaixaGeralDepositosScraper,
    fids.BANCO_MONTEPIO: BancoMontepioScraper,
    fids.BRADESCO: BradescoScraper,
    fids.SABADELL_MIAMI: SabadellMiamiScraper,
    fids.CAJA_ALMENDRALEJO: CajaAlmendralejoScraper,
    fids.BANCOFAR: BancofarScraper,
    fids.CAJA_RURAL_CENTRAL: CajaRuralCentralScraper,
    fids.SABADELL_UK: SabadellUKScraper,
    fids.CAIXA_CALLOSA: CaixaCallosaScraper,
    fids.INVERSIS: InversisScraper,
    fids.EBN: EbnScraper,
    fids.CAIXA_GUISSONA: CaixaGuissonaScraper,
    fids.POSTFINANCE: PostfinanceScraper,
    fids.SANTANDER_MEXICO: SantanderMexicoScraper,
    fids.PAYPAL: PayPalScraper,
    fids.CAIXA_BURRIANA: CaixaRuralBurrianaScraper,
    fids.BANCA_PUEYO: BancaPueyoScraper,
    fids.CAJA_RURAL_DE_ARAGON: CajaRuralDeAragonScraper,
    fids.ABANCA_PORTUGAL: AbancaScraper
}

_version_ = '34.3.0'

_changelog_ = """
34.3.0 2023.11.08
main: Fixed n43 logs for nightly. Added -n argument to indicate all n43 accesses.
34.2.0 2023.11.07
main: added logger_prefix to log file_name. This makes log file be named with 'n43' and 'receipts' as expected.
34.1.0 2023.10.18
AbancaPortugalScraper
34.0.0 2023.08.18
main: added check for --receipts-accesses new argument. If provided then overwrite fin_ent_access_ids with 
values returned from db_funcs.AccessFuncs.get_all_receipts_customer_financial_entity_accesses_ids() 
parse_cmdline_args: added command line argument --receipts-accesses', '-r' to be used with main_launcher_receipts.py
without -a or -u. This will get from DB only accesses with receipts download configured.
33.9.0 2023.07.13
CajaRuralDeAragonScraper
33.8.0
BancaPueyoScraper
33.7.0
renamed caja_rural_central_scraper_from_ruralvia.caja_rural_central from caja_rural_central_from_ruralvia.caja_rural_cenral
33.6.0
settings: 
    now use 
        MAX_CONCURRENT_USERS_SCRAPING, MAX_CONCURRENT_FIN_ENTITIES_SCRAPING 
    instead of 
        IS_CONCURRENT_USERS_PROCESSING, IS_CONCURRENT_FINANCIAL_ENTITIES_PROCESSING, 
        MAX_FIN_ENTITIES_CONCURRENT_SCRAPING
33.5.0
CaixaRuralBurrianaScraper
33.4.0
use unicaja_scraper_new
33.3.0
use LaboralKutxaNewWebScraper
33.2.0
check_and_get_log_folder_path() with notification and fallback folder
33.1.0
logger arg for get_fin_ent_accesses_all_customers_scraping, get_fin_ent_accesses_to_scrape 
33.0.2
scrape_specific_customer: 
    proper handling for fin_ent_access_ids=None while gen accesses_str 
33.0.1
removed unused params
33.0.0
Scraper kind support
32.7.0
bancofar_scraper_from_banco_caminos
32.6.0
bankia_scraper_from_caixa
32.5.0
use MAIN_LAUNCHER_LOG_FOLDER
32.4.0
PayPalScraper
32.3.0
'No scraper found' wrn -> err
32.2.0
PostfinanceScraper
SantanderMexicoScraper
32.1.0
CaixaGuissonaScraper
32.0.1
scrape_specific_accesses: fixed 'no access found' detector  
32.0.0
--access-ids parameter (many accesses at once)
removed old changelog 
31.4.0
EbnScraper
31.3.0
renamed CajaEspanaScraper to UnicajaScraper
deleted CajaDueroScraper
31.2.0
log names: _u _a info
31.1.0
IberCajaScraper from iber_caja_newweb_scraper
31.0.0
launcher_id param
30.4.1
upd log msgs
30.4.0
InversisScraper
30.3.1
more log msgs
30.3.0
CaixaCallosaScraper
30.2.0
_process_scraper: wait for equal access finishing and continue; works for concurrent scraping
30.1.0
entry point scrape() with different modes
30.0.0
detect equal access scraping collisions
removed old changelog
"""

MODE_ALL_CUSTOMERS = 'MODE_ALL_CUSTOMERS'
MODE_ONE_CUSTOMER = 'MODE_ONE_CUSTOMER'
MODE_SOME_ACCESSES = 'MODE_SOME_ACCESSES'

KIND_GENERAL = 'general'
KIND_N43 = 'n43'
KIND_MT940 = 'mt940'


class MainLauncher:
    """
    Main launcher to start the scraping
    Launch it from command line with (or without) arguments.
    Example:
    --------
        '$ ulimit -s unlimited && python3 main_launcher.py -u 97716'
        Note: this approach is used to invoke it from server_for_scraping_on_demand.py

    Command line parameters:
    ------------------------
        --user-id, -u
            Scrape specific customer: user Id.
            If not passed: the all_customers_scraping will start if allowed in settings
        --access-ids, -a
            Scrape specific financial entity access Ids.
            If not passed: all fin ent accesses of the customer (user-id) will be scraped.
            With both -u and -a: only this customer accesses will be scraped
               (skips accesses of other customers)
            With only -a: all given accesses will be scraped
        --from-date, -f
            Optional. Scrape specific customer movements from 'date_from' in dd/mm/yyyy format.
            Default get_date_from function will be used if None
        --to-date, -t
            Optional.Scrape specific customer movements to 'date_to' in dd/mm/yyyy format.
            RESERVED option, not used now (every scraper uses today as date_to)
    Methods:
    --------
        scrape_all_customers_where_scraping_not_in_progress -- for scheduled scraping run
        scrape_specific_customer -- for scraping run on demand
    """

    def __init__(self, logger_prefix: str, launcher_id: str, kind: str):
        self.date_from_str = None  # type: Optional[str]  # get last ScrapedTime from the DB for each account if None
        self.date_to_str = None  # type: Optional[str]  # will be today as default
        self.logger_prefix = logger_prefix
        self.launcher_id = launcher_id
        self.__lock = Lock()
        self.kind = kind

    def scrape_all_customers_where_scraping_not_in_progress(self):
        """Entry point for scheduled scraping"""
        users = db_funcs.UserFuncs.get_all_users_scraping_not_in_progress()
        users_num = len(users)

        logger = ScrapeLogger(
            '{}.scrape_all_customers_where_scraping_not_in_progress'.format(self.logger_prefix),
            'ALL',
            'ALL'
        )

        if settings.MAX_CONCURRENT_USERS_SCRAPING > 1:
            with futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_USERS_SCRAPING) as executor:
                futures_dict = {
                    executor.submit(self._process_user, user, True, None, ix, users_num): user.Id
                    for ix, user in enumerate(users)
                }
                logger.log_futures_exc('_process_user future', futures_dict)
        else:
            for ix, user in enumerate(users):
                self._process_user(
                    user,
                    is_all_customers_scraping=True,
                    user_ix=ix,
                    users_num=users_num
                )

    def scrape_specific_accesses(
            self,
            fin_ent_access_ids: List[int],
            date_from: Optional[str],
            date_to: Optional[str]):
        """Gets the customer_ids by fin_ent_access_ids and then calls scrape_specific_customer as usually"""
        fin_ent_accesses = []  # type: List[DBFinancialEntityAccess]
        for fin_ent_access_id in fin_ent_access_ids:
            fin_ent_access = db_funcs.FinEntFuncs.get_financial_entity_access(fin_ent_access_id)

            if not fin_ent_access:
                log('No access found with id {}'.format(fin_ent_access_id))
                continue

            fin_ent_accesses.append(fin_ent_access)

        # Uniq customers of the accesses
        customer_ids = {fin_ent_access.CustomerId for fin_ent_access in fin_ent_accesses}

        cust_fin_ent_access_ids = defaultdict(list)  # type: Dict[int, List[int]]

        for customer_id in customer_ids:
            for fin_ent_access in fin_ent_accesses:
                if fin_ent_access.CustomerId == customer_id:
                    cust_fin_ent_access_ids[customer_id].append(fin_ent_access.Id)

        if settings.MAX_CONCURRENT_USERS_SCRAPING > 1:
            logger = ScrapeLogger(
                '{}.scrape_specific_accesses'.format(self.logger_prefix),
                str(customer_ids),
                str(fin_ent_access_ids)
            )
            with futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_USERS_SCRAPING) as executor:
                futures_dict = {
                    executor.submit(
                        self.scrape_specific_customer,
                        RunnerOnDemandParams(
                            customer_id=customer_id,
                            date_from_str=date_from,
                            date_to_str=date_to,
                        ),
                        cust_fin_ent_access_ids[customer_id]
                    ): customer_id
                    for customer_id in customer_ids
                }
                logger.log_futures_exc('scrape_specific_accesses future', futures_dict)
        else:
            for customer_id in customer_ids:
                self.scrape_specific_customer(
                    RunnerOnDemandParams(
                        customer_id=customer_id,
                        date_from_str=date_from,
                        date_to_str=date_to,
                    ),
                    cust_fin_ent_access_ids[customer_id]
                )

    def scrape_specific_customer(self,
                                 runner_on_demand_params: RunnerOnDemandParams,
                                 fin_ent_access_ids: List[int] = None):
        """Entry point for scraping on demand"""
        customer_id = runner_on_demand_params.customer_id
        accesses_str = (','.join(str(a) for a in fin_ent_access_ids).strip(',')
                        if fin_ent_access_ids
                        else '')
        log('Scrape {}{}'.format(
            '-u {}'.format(customer_id),
            ' -a {}'.format(accesses_str) if accesses_str else ''
        ))
        self.date_to_str = runner_on_demand_params.date_to_str
        self.date_from_str = runner_on_demand_params.date_from_str
        user = db_funcs.UserFuncs.get_user_scraping_not_in_progress(customer_id)
        if not user:
            log('Scrape_specific_customer: customer with Id {} not found. Exit'.format(customer_id))
            return

        log('Scrape_specific_customer: start scraping for customer {}'.format(customer_id))
        self._process_user(
            user,
            is_all_customers_scraping=False,
            fin_ent_access_ids=fin_ent_access_ids
        )

    def _process_user(self,
                      user: DBCustomer,
                      is_all_customers_scraping: bool,
                      fin_ent_access_ids: List[int] = None,
                      user_ix=0,
                      users_num=0):

        logger = ScrapeLogger('{}._process_user'.format(self.logger_prefix), user.Id, 'ALL')

        if is_all_customers_scraping:
            logger.info('scrape_all_customers: start scraping for customer {} ({}/{})'.format(
                user.Id,
                user_ix,
                users_num
            ))

        datetime_user_scraping_started = date_funcs.now_for_db()
        # Filter by available/allowed accesses
        accesses_to_process = []  # type:  List[DBFinancialEntityAccess]

        # Get accesses to process basing on scraping kind.
        # Need to use different kinds because accesses_available for specific kind
        # is not a subset some very basic list of accesses to process - they all can be very different
        if self.kind == KIND_GENERAL and is_all_customers_scraping:
            accesses_available = db_funcs.FinEntFuncs.get_fin_ent_accesses_all_customers_scraping(
                logger,
                user.Id,
            )
            accesses_to_process = accesses_available

        elif self.kind == KIND_GENERAL:
            accesses_available = db_funcs.FinEntFuncs.get_fin_ent_accesses_to_scrape(logger, user.Id)
            if fin_ent_access_ids:
                accesses_to_process = [a for a in accesses_available if a.Id in fin_ent_access_ids]
            else:
                accesses_to_process = accesses_available

        elif self.kind == KIND_N43:
            accesses_available_n43 = db_funcs.FinEntFuncs.get_fin_ent_accesses_to_scrape_for_n43(user.Id)
            if fin_ent_access_ids:
                accesses_to_process = [
                    db_funcs.FinEntFuncs.get_financial_entity_access(access.Id)
                    for access in accesses_available_n43
                    if access.Id in fin_ent_access_ids
                ]
            else:
                accesses_to_process = [
                    db_funcs.FinEntFuncs.get_financial_entity_access(access.Id)
                    for access in accesses_available_n43
                ]

        elif self.kind == KIND_MT940:
            access_ids_available_mt940 = db_funcs.FinEntFuncs.get_fin_ent_access_ids_to_scrape_for_mt940(user.Id)
            if fin_ent_access_ids:
                accesses_to_process = [
                    db_funcs.FinEntFuncs.get_financial_entity_access(access_id)
                    for access_id in access_ids_available_mt940
                    if access_id in fin_ent_access_ids
                ]
            else:
                accesses_to_process = [
                    db_funcs.FinEntFuncs.get_financial_entity_access(access_id)
                    for access_id in access_ids_available_mt940
                ]

        logger.info('Start. Scrape {} fin_ent accesses: {}'.format(
            len(accesses_to_process),
            accesses_to_process)
        )

        # Update user scraping started
        if settings.IS_UPDATE_DB:
            db_funcs.UserFuncs.update_user_scraping_state(
                DBCustomerToUpdateState(
                    Id=user.Id,
                    ScrapingInProgress=1,
                    ScrapingStartedTimeStamp=datetime_user_scraping_started,
                    ScrapingFinishedTimeStamp=None
                )
            )
        logger.info('db_funcs.UserFuncs.update_user_scraping_state: ScrapingInProgress=1')

        if settings.MAX_CONCURRENT_FIN_ENTITIES_SCRAPING > 1:
            with futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_FIN_ENTITIES_SCRAPING) as executor:
                futures_dict = {
                    executor.submit(self._process_financial_entity_access, user, access):
                        access.FinancialEntityId
                    for access in accesses_to_process
                }
                logger.log_futures_exc('_process_financial_entity future', futures_dict)
        else:
            for access in accesses_to_process:
                self._process_financial_entity_access(user, access)

        # Update user scraping finished
        if settings.IS_UPDATE_DB:
            db_funcs.UserFuncs.update_user_scraping_state(
                DBCustomerToUpdateState(
                    Id=user.Id,
                    ScrapingInProgress=0,
                    ScrapingStartedTimeStamp=datetime_user_scraping_started,
                    ScrapingFinishedTimeStamp=date_funcs.now_for_db(),
                )
            )
        logger.info('Finish. db_funcs.UserFuncs.update_user_scraping_state: ScrapingInProgress=0')

        # Clean up if scraped some accesses of the customer
        if accesses_to_process:
            logger.info("== Set PossibleInactive accounts to 'scraping not in progress' ==")
            if settings.IS_UPDATE_DB:
                db_funcs.AccountFuncs.upd_possible_inactive_set_scraping_state_to_false(user.Id)
            logger.info('== state_reset.reset_forced ==')
            state_reset.reset_forced(user.Id)

    def _process_financial_entity_access(self, user: DBCustomer,
                                         access: DBFinancialEntityAccess):

        logger = ScrapeLogger(
            '{}._process_financial_entity_access'.format(self.logger_prefix),
            user.Id,
            '{} of fin_entity {}'.format(access.Id, access.FinancialEntityId)
        )
        logger.info('start')

        if not access.FinancialEntityAccessId:
            return

        scraper = FIN_ENTITY_ID_TO_SCRAPER.get(access.FinancialEntityId)
        if not scraper:
            logger.error('No scraper found for {}'.format(access.FinancialEntityId))
            return

        self._process_scraper(scraper, user, access)

    def _process_scraper(self, scraper, user: DBCustomer, access: DBFinancialEntityAccess):

        def _upd_fin_ent_access_with_codes_scrap_in_progr(started_at_: str):
            """Update userFinancialEntityAccess scraping started with codes"""

            if settings.IS_UPDATE_DB:
                db_funcs.FinEntFuncs.update_fin_ent_access_scrap_state_with_codes(
                    DBFinancialEntityAccessWithCodesToUpdateState(
                        Id=access.Id,
                        ScrapingInProgress=1,
                        ScrapingStartedTimeStamp=started_at_,
                        ScrapingFinishedTimeStamp=None,
                        HttpStatusResponseCode=999,
                        HttpStatusResponseDescription='Not_implemented',
                        ResponseTesoraliaCode=result_codes.IN_PROGRESS.code,
                        ResponseTesoraliaDescription=result_codes.IN_PROGRESS.description
                    )
                )

        def _upd_fin_ent_access_with_codes_scrap_fin(started_at_: str,
                                                     http_stat_resp_code=999,
                                                     http_stat_resp_cod_descr='Not_implemented',
                                                     result_code: ResultCode = result_codes.SUCCESS):
            """Update userFinancialEntityAccess scraping started with codes"""

            if settings.IS_UPDATE_DB:
                db_funcs.FinEntFuncs.update_fin_ent_access_scrap_state_with_codes(
                    DBFinancialEntityAccessWithCodesToUpdateState(
                        Id=access.Id,
                        ScrapingInProgress=0,
                        ScrapingStartedTimeStamp=started_at_,
                        ScrapingFinishedTimeStamp=date_funcs.now_for_db(),
                        HttpStatusResponseCode=http_stat_resp_code,
                        HttpStatusResponseDescription=http_stat_resp_cod_descr,
                        ResponseTesoraliaCode=result_code.code,
                        ResponseTesoraliaDescription=result_code.description
                    )
                )

        started_at = date_funcs.now_for_db()
        logger = ScrapeLogger(
            '{}._process_scraper'.format(self.logger_prefix),
            user.Id,
            '{} of fin_entity {}'.format(access.Id, access.FinancialEntityId)
        )

        equal_access_ids_in_progress = []  # type: List[int]
        if settings.IS_DETECT_EQUAL_ACCESS_COLLISIONS:
            for i in range(1, 181):  # wait up to 30 min
                equal_access_ids_in_progress = db_funcs.FinEntFuncs.get_equal_access_ids_scraping_in_progress(
                    access
                )
                if equal_access_ids_in_progress:
                    logger.warning('found equal accesses in progress: {}. Wait and retry #{}'.format(
                        equal_access_ids_in_progress,
                        i
                    ))
                    time.sleep(10)
                    continue
                break  # no equal in progress
            else:
                logger.error("couldn't scrape due to continuous equal access processing: {}. Abort".format(
                    equal_access_ids_in_progress
                ))
                _upd_fin_ent_access_with_codes_scrap_fin(
                    started_at,
                    result_code=result_codes.ERR_EQUAL_ACCESS_COLLISION
                )
                logger.info('finish')
                return

        logger.info('start')

        _upd_fin_ent_access_with_codes_scrap_in_progr(started_at)

        scraper_params = ScraperParamsCommon(
            date_from_str=self.date_from_str,
            date_to_str=self.date_to_str,
            db_customer=user,
            db_financial_entity_access=access,
            launcher_id=self.launcher_id
        )

        try:
            s = scraper(scraper_params)
            main_result_code, main_result_data = s.scrape()  # type: Tuple[ResultCode, Any]
            # default = success
            _upd_fin_ent_access_with_codes_scrap_fin(started_at, result_code=main_result_code)
        except Exception as _e:
            logger.error('SCRAPING EXCEPTION: {}'.format(traceback.format_exc()))
            _upd_fin_ent_access_with_codes_scrap_fin(started_at,
                                                     result_code=result_codes.ERR_UNHANDLED_EXCEPTION)

        logger.info('finish')

    def scrape(self,
               mode: str,
               customer_id: int = None,
               fin_ent_access_ids: List[int] = None,
               date_from: str = None,
               date_to: str = None) -> None:
        """Provides scraping process in different modes and then scrapes delayed_accesses"""
        processed = False
        if mode == MODE_ALL_CUSTOMERS:
            processed = True
            self.scrape_all_customers_where_scraping_not_in_progress()
        elif mode == MODE_ONE_CUSTOMER and customer_id:
            processed = True
            self.scrape_specific_customer(
                RunnerOnDemandParams(
                    customer_id=customer_id,
                    date_from_str=date_from,
                    date_to_str=date_to,
                ),
                fin_ent_access_ids
            )
        elif mode == MODE_SOME_ACCESSES and fin_ent_access_ids:
            processed = True
            self.scrape_specific_accesses(fin_ent_access_ids, date_from, date_to)

        if not processed:
            raise Exception("Unknown mode or wrong args for the mode")


def parse_cmdline_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--user-id',
        '-u',
        help='Scrape specific customer: user Id. '
             'If not passed: the all_customers_scraping will start if allowed in settings',
        type=int
    )
    parser.add_argument(
        '--access-ids',
        '-a',
        help='Scrape specific financial entity access Ids. '
             'Use "," as the delimiter. '
             'If not passed: all fin ent accesses of the customer (user-id) will be scraped. '
             'With both -u and -a: only this customer accesses will be scraped '
             '(skips accesses of other customers). '
             'With only -a: all given accesses will be scraped',
        type=str,
        default=''
    )
    parser.add_argument(
        '--from-date',
        '-f',
        help='Scrape specific customer: date_from in dd/mm/yyyy format. Default get_date_from '
             'function will be used if None',
        type=str
    )
    parser.add_argument(
        '--to-date',
        '-t',
        help='Scrape specific customer: date_to in dd/mm/yyyy format. RESERVED option, not used now '
             '(every scraper uses today as date_to).',
        type=str
    )

    parser.add_argument(
        '--concurrent',
        '-c',
        help="Explicitly set 'concurrent scraping' (override project settings)",
        type=str,
        choices=['true', 'false'],
        default=None,
    )

    parser.add_argument(
        '--update-db',
        help="Explicitly set 'update db' (override project settings)",
        type=str,
        choices=['true', 'false'],
        default=None,
    )

    parser.add_argument(
        '--offset',
        '-o',
        help="Override default DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV (prefer it than -f). "
             "Affects the offset only for additional movs, not the offset for initial scraping",
        type=int,
        default=None,
    )

    parser.add_argument(
        '--launcher-id',
        '-l',
        help="Launcher instance ID to use for DB logging",
        type=str,
        default=settings.LAUNCHER_DEFAULT_ID,
    )

    parser.add_argument(
        '--receipts-accesses',
        '-r',
        help="Launcher receipts accesses",
        action='store_true',
        default=None,
    )

    parser.add_argument(
        '--n43-accesses',
        '-n',
        help="Launcher n43 accesses",
        action='store_true',
        default=None,
    )

    args = parser.parse_args()
    return parser, args


def check_and_get_log_folder_path() -> str:
    """Tries to use target folder defined by settings
    and uses fallback if it's unavailable
    """
    folder_path = os.path.abspath(os.path.join(
        settings.PROJECT_ROOT_PATH,
        settings.MAIN_LAUNCHER_LOG_FOLDER,
    ))
    if os.path.isdir(folder_path):
        return folder_path

    folder_path_fallback = os.path.abspath(os.path.join(
        settings.PROJECT_ROOT_PATH,
        'logs',
    ))
    if not os.path.isdir(folder_path_fallback):
        os.mkdir(folder_path_fallback)
    log_err("The target log folder is not available: '{}'. Using fallback log folder: '{}'".format(
        folder_path,
        folder_path_fallback
    ), is_sentry=True)
    return folder_path_fallback


def main(logger_prefix: str, kind: str = KIND_GENERAL):
    """
    :param logger_prefix: only main_launcher logger prefix (to be changed by specific launchers)
    :param kind: one of KIND_GENERAL, KIND_N43, KIND_MT940
    """
    started_at = time.time()
    args = None  # for graceful 'finally' block
    try:
        parser, args = parse_cmdline_args()
        customer_id = args.user_id  # type: Optional[int]
        fin_ent_access_ids_str = args.access_ids.strip(',')  # type: str
        fin_ent_access_ids = [int(a) for a in fin_ent_access_ids_str.split(',')
                              if fin_ent_access_ids_str]  # type: List[int]
        date_from = args.from_date  # type: Optional[str]
        date_to = args.to_date  # type: Optional[str]
        launcher_id = args.launcher_id  # type: str

        accesses_infix = ''
        if fin_ent_access_ids_str and not args.receipts_accesses and not args.n43_accesses:
            accesses_infix = '_a{}'.format(fin_ent_access_ids_str.replace(',', '-'))
        log_file_name = os.path.abspath(os.path.join(
                check_and_get_log_folder_path(),
                '{}{}{}{}{}__{}.log'.format(
                    logger_prefix,
                    '_u{}'.format(customer_id) if customer_id else '',
                    accesses_infix,
                    '_n43_accesses_{}'.format(args.n43_accesses) if args.n43_accesses else '',
                    '_receipts_accesses_{}'.format(args.receipts_accesses) if args.receipts_accesses else '',
                    datetime.datetime.utcnow().strftime(settings.LOG_FILENAME_DATETIME_FMT)
                )
            ))
        logging.Formatter.converter = time.gmtime  # to use utc always
        logging.basicConfig(
            level=logging.INFO,
            filename=log_file_name,
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

        if args.receipts_accesses:
            fin_ent_access_ids = db_funcs.AccessFuncs.get_all_receipts_customer_financial_entity_accesses_ids()

        if args.concurrent is not None:
            is_concurrent = True if args.concurrent == 'true' else False
            settings.IS_CONCURRENT_SCRAPING = is_concurrent

        if args.update_db is not None:
            is_update_db = True if args.update_db == 'true' else False
            settings.IS_UPDATE_DB = is_update_db

        if args.offset is not None:
            settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV = int(args.offset)
            log('Override: project.settings.<...>DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV = {}'.format(
                settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV
            ))

        log('ACCESSES = {}'.format(accesses_infix))
        log('IS_DEPLOYED = {}'.format(settings.IS_DEPLOYED))
        log('IS_CONCURRENT_SCRAPING = {}'.format(settings.IS_CONCURRENT_SCRAPING))
        log('IS_PRODUCTION_DB = {}'.format(settings.IS_PRODUCTION_DB))
        log('UPDATE_DB = {}'.format(settings.IS_UPDATE_DB))

        if (args.concurrent is not None) or (args.update_db is not None):
            # allow to read the msgs above
            time.sleep(2)

        # Test to avoid unexpected arguments
        if date_from:
            datetime.datetime.strptime(date_from, settings.SCRAPER_DATE_FMT)

        if date_to:
            datetime.datetime.strptime(date_to, settings.SCRAPER_DATE_FMT)

        log('===== The scraping process started with arguments: {} ====='.format(args), is_sentry=True)
        time.sleep(1)

        main_launcher = MainLauncher(logger_prefix, launcher_id, kind=kind)

        if not (customer_id or fin_ent_access_ids):
            if settings.IS_ALLOW_ALL_CUSTOMERS_SCRAPING_RUN:
                log('ALL CUSTOMERS SCRAPING RUN. Args date_from and date_to will be ignored (if passed)')
                # scrape_all_customers_where_scraping_not_in_progress
                main_launcher.scrape(MODE_ALL_CUSTOMERS)
            else:
                log('The all_customers_scraping is not allowed (dev mode). Exit')
        elif fin_ent_access_ids and not customer_id:
            # Scrape only by fin_ent_access_id
            # scrape_specific_access(fin_ent_access_id, date_from, date_to)
            main_launcher.scrape(
                MODE_SOME_ACCESSES,
                fin_ent_access_ids=fin_ent_access_ids,
                date_from=date_from,
                date_to=date_to
            )
        else:
            # Optional fin_ent_access_id
            # scrape_specific_customer
            main_launcher.scrape(
                MODE_ONE_CUSTOMER,
                customer_id=customer_id,
                fin_ent_access_ids=fin_ent_access_ids,
                date_from=date_from,
                date_to=date_to
            )

    finally:
        log('==== queue.wait_finishing and close db connection ====')
        queue_simple.wait_finishing()
        if args is not None:
            log('===== The scraping process finished in {} sec with arguments: {} ====='.format(
                int(time.time() - started_at),
                args
            ))

        # Mostly to allow sentry client send all pending msgs
        time.sleep(3)


if __name__ == '__main__':
    main('main_launcher')
