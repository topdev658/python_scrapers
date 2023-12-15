import random
import time
import traceback
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Tuple

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.transfers_linker import TransfersLinker
from custom_libs.myrequests import MySession, Response
from project import fin_entities_ids
from project import settings as project_settings
from project.custom_types import (
    DBTransferAccountConfig, DBTransferFilter, DBMovementConsideredTransfer,
    TransferParsed, TransferScraped, ScraperParamsCommon, MainResult
)
from scrapers.bbva_scraper.bbva_netcash_scraper import BBVANetcashScraper
from . import parse_helpers_netcash_transfers

__version__ = '3.5.3'

__changelog__ = """
3.5.3
upd log msg
3.5.2
continue download when some transfer is not available
3.5.1
call transf_linker with named args
3.5.0
TransfersLinker: upd import path
3.4.0
TransferScraped with TempBalance field
3.3.0
upd log msgs: (use single_date)
3.2.0
apply per day filter on request to bank to avoid pagination error in bank
3.1.0
ALL_TRANSFERS_BANK_CODE support
3.0.0
moved appropriate methods and constants to:
  BasicScraper
  parse_helpers_netcash_receipts
  db_funcs
  project/settings
better logging
better naming for methods and vars (renamed switch.. to open.., resp_accs etc)
fixed: pagination
filter db movs by dates for each acc
fixed: insert transfers in db in proper ASC order
self.fin_entity_name
2.0.0
deep refactoring
1.0.0
init
"""

PROCESS_TRANSFER_MAX_WORKERS = 1

DOWNLOAD_TRANSFERS_RETRY_AFTER_SECONDS = 5

NAVIGATION_TYPE_TRANSFERENCIAS = 'TRANSFERENCIAS'
NAVIGATION_TYPE_MOVIMIENTOS = 'MOVIMIENTOS'

NATIONAL_TRANSFER_BANK_CODE = '0007'
INTERNATIONAL_TRANSFER_BANK_CODE = '0163'
ALL_TRANSFERS_BANK_CODE = 'ALL'

ABONO_VENCIMIENTO_CONFIRMING_BANK_CODE = '0591'
ANTICIPOS_CONFIRMING_BANK_CODE = '0391'

EMPTY_TRANSFER_FIELD_DEFAULT_VALUE = 'N/A'


class BBVANetcashTransfersScraper(BBVANetcashScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BBVANetcashTransfersScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.fin_entity_name = fin_entities_ids.get_fin_entity_name_by_id(self.db_financial_entity_id)

    def _get_transf_scraped_field_value(
            self,
            filters: List[DBTransferFilter],
            transf_parsed: TransferParsed,
            transf_scraped_field_name: str) -> str:
        """Applies filter to transf parsed field to get transf scraped field value"""
        # Expecting 0 or 1 val
        transfer_filters_for_field = [f for f in filters if f.DestinyField == transf_scraped_field_name]
        if not transfer_filters_for_field:
            self.logger.info('{}: no transfer filter. Use default value'.format(transf_scraped_field_name))
            return EMPTY_TRANSFER_FIELD_DEFAULT_VALUE

        transfer_filter_for_field = transfer_filters_for_field[0]  # type: DBTransferFilter

        if transfer_filter_for_field.OriginField in transf_parsed:
            transf_scraped_field_value = transf_parsed[transfer_filter_for_field.OriginField]
        else:
            # use OriginField as default value i.e: NOK for AVIA
            transf_scraped_field_value = transfer_filter_for_field.OriginField

        return transf_scraped_field_value

    def open_tranfs_filter_form_and_get_acc_select_opts(
            self,
            s: MySession) -> Tuple[Response, Dict[str, str]]:
        """
        Navigates to transfers page (Cobros->Transferencias->Transferencias recibidas)

        :return: The position (option) of each account in
                 the list of accounts that can be selected to see account transfers.
                 in shape {account_short_no: account_pos_as_option}
        """

        req_headers = self.basic_req_headers_updated({
            'Connection': 'keep-alive',
            'Referer': 'https://www.bbvanetcash.com/SESKYOP/kyop_mult_web_pub/index-new.html?LOCALE=es_ES'
        })
        req_params = OrderedDict([
            ('pb_cod_prod', '201'),
            ('pb_cod_serv', '8125'),
            ('pb_cod_proc', '89990688'),
            ('LOCALE', 'es_ES'),
            ('pb_cod_ffecha', 'dd/MM/yyyy'),
            ('pb_cod_fimporte', '0.000,00'),
            ('pb_husohora', '(GMT+01:00)'),
            ('pb_xti_comprper', 'S'),
            ('pb_url',
             '+?proceso=TLBHPrHisTraConsultaHistorico'
             '&operacion=TLBHOpHisTraCriteriosSeleccion'
             '&accion=execute'
             '&modoAcceso=4'
             '&codigoServicio=8125'),
            ('pb_segmento', '8'),
            ('xtiTipoProd', 'C'),
            ('pb_isPortalKyop', 'true'),
            ('cod_emp', '20034198'),  # FIXME extract from page (check if is a calculated code)
            ('pb_cod_prod_p', '201'),
            ('kyop-process-id', ''),
            ('referenciaBBVA', ''),
        ])
        # https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/listarResultadoMovNivel2
        # https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE?proceso=TLBHPrHisTraConsultaHistorico&operacion=TLBHOpHisTraCriteriosSeleccion&accion=execute&modoAcceso=4&codigoServicio=8125&isInformationalArchitecture=true
        req_url = ('https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE'
                   '?proceso=TLBHPrHisTraConsultaHistorico'
                   '&operacion=TLBHOpHisTraCriteriosSeleccion'
                   '&accion=execute'
                   '&modoAcceso=4'
                   '&codigoServicio=8125'
                   '&isInformationalArchitecture=true')  # kyos_mult

        resp_transf_filter_form = Response()
        account_select_options = {}  # type: Dict[str, str]
        for attempt in range(1, 4):
            resp_transf_filter_form = s.post(
                req_url,
                data=req_params,
                headers=req_headers,
                proxies=self.req_proxies,
                timeout=30,
            )
            if not (resp_transf_filter_form.status_code == 200
                    and "select name=\"listaCuentas\"" in resp_transf_filter_form.text):
                self.logger.warning(
                    "attempt #{}: can't switch to transfers and get transfers accounts. Retry".format(
                        attempt
                    )
                )
                time.sleep(DOWNLOAD_TRANSFERS_RETRY_AFTER_SECONDS + random.random() * 0.5)
                continue

            ok, account_select_options = parse_helpers_netcash_transfers.get_account_select_options(
                resp_transf_filter_form.text
            )
            if not ok:
                self.logger.warning(
                    "attempt #{}: can't switch to transfers and get transfers accounts. Retry".format(
                        attempt
                    )
                )
                time.sleep(DOWNLOAD_TRANSFERS_RETRY_AFTER_SECONDS + random.random() * 0.5)
                continue
            break
        else:
            # failed all attempts
            self.basic_log_wrong_layout(
                resp_transf_filter_form,
                "Can't switch to transfers and get transfers accounts"
            )

        return resp_transf_filter_form, account_select_options

    def open_acc_transfers(self,
                           s: MySession,
                           account_position: str,
                           date_from: datetime,
                           date_to: datetime,
                           resp_transf_filter_form: Response) -> Tuple[bool, Response]:
        # Navigates to transfers of the specific account pointed by account_position. Account position is the
        # position of the account in the list of accounts with transfers at bank menu.
        date_from_str = date_from.strftime('%Y%m%d')
        date_to_str = date_to.strftime('%Y%m%d')
        req_headers = self.basic_req_headers_updated({
            'Connection': 'keep-alive',
            'Referer': resp_transf_filter_form.url,
        })
        # Need to get the numOPRequest param of form called transferencias. This parameter increments after
        # post requests to bank.
        form_params = extract.build_req_params_from_form_html_patched(
            resp_transf_filter_form.text,
            'transferencias'
        )
        req_params = OrderedDict([
            ('proceso', 'TLBHPrHisTraConsultaHistorico'),
            ('operacion', 'TLBHOpHisTraListaTransferencias'),
            ('accion', 'execute'),
            ('importeDesde', '0'),
            ('importeHasta', '0'),
            ('fechaDesde', date_from_str),
            ('fechaHasta', date_to_str),
            ('numeroCuenta', '0'),
            ('numeroPagina', '1'),
            ('listaAsuntos', account_position + '#'),
            ('numeroAsuntos', '1'),
            ('numOPRequest', form_params[1]['numOPRequest']),
            ('importeD', ''),
            ('importeH', ''),
            ('sel', '2'),
            ('diaDesde', date_from_str[6:8]),
            ('mesDesde', date_from_str[4:6]),
            ('anioDesde', date_from_str[0:4]),
            ('diaHasta', date_to_str[6:8]),
            ('mesHasta', date_to_str[4:6]),
            ('anioHasta', date_to_str[0:4]),
            ('banco', ''),
            ('oficina', ''),
            ('DC', ''),
            ('cuenta', ''),
            ('cuentaNuevaIBAN', ''),
            ('listaCuentas', account_position + '@'),
            ('imported', ''),
            ('importeh', ''),
            ('concepto', '009'),
        ])

        req_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'  # kyos_mult
        success = False
        resp_acc_transfers = Response()
        for attempt in range(1, 4):
            resp_acc_transfers = s.post(
                req_url,
                data=req_params,
                headers=req_headers,
                proxies=self.req_proxies,
                timeout=30,
            )
            if resp_acc_transfers.status_code == 200 and "Transferencias recibidas" in resp_acc_transfers.text:
                success = True
                break
            time.sleep(1 + random.random() * 0.5)
        return success, resp_acc_transfers

    def open_acc_transfers_i(self,
                             s: MySession,
                             fin_ent_account_id: str,
                             page_ix: int,
                             resp_prev: Response) -> Tuple[bool, Response]:
        # Navigates to next page through pagination of transfers of a specific account.
        req_headers = self.basic_req_headers_updated({
            'Connection': 'keep-alive',
            'Referer': resp_prev.url,
        })
        req_params = OrderedDict([
            ('proceso', 'TLBHPrHisTraConsultaHistorico'),
            ('operacion', 'TLBHOpHisTraListaTransferencias'),
            ('accion', 'paginarOperacion'),
            ('indice', ''),
            ('tipoRemesa', ''),
            ('numeroCuenta', '0'),  # FIXME: VB: will fail for many accs?
            ('numeroPagina', str(page_ix)),
            ('esPrimeraLista', ''),
        ])
        req_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'
        result = False
        resp_transfers_i = Response()
        for attempt in range(1, 4):
            resp_transfers_i = s.post(
                req_url,
                data=req_params,
                headers=req_headers,
                proxies=self.req_proxies,
                timeout=30,
            )
            if resp_transfers_i.status_code == 200 and "Transferencias recibidas" in resp_transfers_i.text:
                result = True
                break
            self.logger.warning("{}: can't open page #{} with taransfers. Retry".format(
                fin_ent_account_id,
                page_ix,
            ))
            time.sleep(1 + random.random() * 0.5)
        else:
            self.basic_log_wrong_layout(
                resp_transfers_i,
                "{}: can't open page #{} with transfers".format(fin_ent_account_id, page_ix)
            )
        return result, resp_transfers_i

    def get_acc_transfs_parsed(
            self,
            s: MySession,
            fin_ent_account_id: str,
            single_date_str: str,
            resp_acc_transfers: Response) -> Tuple[bool, MySession, str, List[TransferParsed]]:
        """
        Gets account transfers from transfers menu
        :return: (success, session, resp_url, transfers_parsed)
        """
        req_headers = self.basic_req_headers_updated({
            'Connection': 'keep-alive',
            'Referer': resp_acc_transfers.url,
            'Upgrade-Insecure-Requests': '1'
        })

        req_params = OrderedDict([
            ('proceso', 'TLBHPrHisTraConsultaHistorico'),
            ('operacion', 'TLBHOpHisTraDetalleTransferencia'),
            ('accion', 'execute'),
            ('indice', '0'),
            ('tipoRemesa', ''),
            ('numeroCuenta', '0'),  # FIXME: VB: will fail for many accs?
            ('numeroPagina', '1'),
            ('esPrimeraLista', ''),
        ])
        # https://www.bbvanetcash.com/SESEYOZ/eyoz_mult_web_posicioncuentas_01/listarResultadoMovNivel2
        # https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/PIBEE?proceso=TLBHPrHisTraConsultaHistorico&operacion=TLBHOpHisTraCriteriosSeleccion&accion=execute&modoAcceso=4&codigoServicio=8125&isInformationalArchitecture=true
        req_transfer_url = 'https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet'  # kyos_mult

        transfs_parsed_desc = []  # type: List[TransferParsed]
        resp_transfer = Response()
        resp_acc_transfers_i = resp_acc_transfers
        success = True
        for page_ix in range(1, 100):  # avoid inf loop
            if page_ix > 1:
                ok, resp_acc_transfers_i = self.open_acc_transfers_i(
                    s,
                    fin_ent_account_id,
                    page_ix,
                    resp_transfer  # for referer
                )
                if not ok:
                    break  # already reported

            self.logger.info('{}: {}: page #{}: get transfers'.format(
                fin_ent_account_id,
                single_date_str,
                page_ix
            ))
            transfers_count_in_page = resp_acc_transfers_i.text.count('javascript:lanzaDetalle')
            for transfer_ix in range(transfers_count_in_page):
                req_params['indice'] = str(transfer_ix)
                req_params['numeroPagina'] = str(page_ix)
                for attempt in range(1, 4):
                    resp_transfer = s.post(
                        req_transfer_url,
                        data=req_params,
                        headers=req_headers,
                        proxies=self.req_proxies,
                        timeout=30,
                    )

                    if not (resp_transfer.status_code == 200 and "Detalle de la Transferencia" in resp_transfer.text):
                        self.logger.warning(
                            "{}: attempt #{}: can't get transfer detail for index {}. RETRY".format(
                                fin_ent_account_id,
                                attempt,
                                transfer_ix
                            )
                        )
                        time.sleep(1 + random.random() * 0.5)
                        continue

                    transf_parsed = parse_helpers_netcash_transfers.get_transfer_parsed(resp_transfer.text)
                    transfs_parsed_desc.append(transf_parsed)
                    self.logger.info(
                        '{}: parsed transf {}@{}'.format(
                            fin_ent_account_id,
                            convert.to_float(transf_parsed['Importe Líquido']),
                            transf_parsed['Fecha Valor'],
                        ))
                    break  # successful attempt
                else:
                    # failed attempts
                    self.logger.warning(
                        "{}: can't get all transfers. Failed on details for index {}. Skip".format(
                            fin_ent_account_id,
                            transfer_ix
                        )
                    )
            # / end of 'for transfer_ix in range(transfers_count_in_page)'
            if 'Página Siguiente' not in resp_acc_transfers_i.text:
                self.logger.info('{}: {}: no more pages with transfers'.format(fin_ent_account_id, single_date_str))
                break
        transfs_parsed_asc = list(reversed(transfs_parsed_desc))
        return success, s, resp_transfer.url, transfs_parsed_asc

    def get_transfs_scraped_from_transfs_parsed_in_transfs_menu(
            self,
            transfs_parsed: Dict[int, List[TransferParsed]]) -> Dict[int, List[TransferScraped]]:

        transfs_scraped = {}  # type: Dict[int, List[TransferScraped]]
        try:
            if len(transfs_parsed) <= 0:
                self.logger.info('get_transfs_scraped_from_transfs_parsed_in_transfs_menu 0 transfers parsed')
                return transfs_scraped

            for db_acc_id, acc_transfs_parsed in transfs_parsed.items():
                transfers_filters = self.db_connector.get_active_transfers_filters(
                    db_acc_id,
                    NAVIGATION_TYPE_TRANSFERENCIAS
                )
                filters_transfs_national = [
                    f
                    for f in transfers_filters
                    if f.BankCode == NATIONAL_TRANSFER_BANK_CODE
                ]
                filters_transfs_international = [
                    f
                    for f in transfers_filters
                    if f.BankCode == INTERNATIONAL_TRANSFER_BANK_CODE
                ]

                filters_transfs_all = [
                    f
                    for f in transfers_filters
                    if f.BankCode == ALL_TRANSFERS_BANK_CODE
                ]

                acc_transfs_scraped = []  # type: List[TransferScraped]
                for transf_parsed in acc_transfs_parsed:  # 1 is transfers list of account_id
                    # AVIA considers national transfers different from international transfers.
                    # Other custormes should use "ALL" bank code and all transfers in transfers menu will use same filter
                    if filters_transfs_all:
                        current_filters = filters_transfs_all
                    else:
                        if 'ES' in transf_parsed['Banco y Oficina Ordenante']:
                            current_filters = filters_transfs_national
                        else:
                            current_filters = filters_transfs_international

                    account_order = self._get_transf_scraped_field_value(
                        current_filters,
                        transf_parsed,
                        'AccountOrder'
                    )
                    name_order = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'NameOrder')
                    concept = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Concept')
                    reference = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Reference')
                    description = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Description')
                    observation = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Observation')

                    transfer_scraped = TransferScraped(
                        AccountId=db_acc_id,
                        CustomerId=self.db_customer_id,
                        OperationalDate=date_funcs.convert_date_to_db_format(transf_parsed['Fecha Operación']),
                        ValueDate=date_funcs.convert_date_to_db_format(transf_parsed['Fecha Valor']),
                        Amount=convert.to_float(transf_parsed['Importe Líquido']),
                        TempBalance=None,
                        Currency=transf_parsed['Divisa'],
                        AccountOrder=account_order,
                        NameOrder=name_order,
                        Concept=concept,
                        Reference=reference,
                        Description=description,
                        Observation=observation,
                        IdStatement=None,
                        FinancialEntityName=self.fin_entity_name,
                    )
                    if transfer_scraped.Amount > 0:
                        acc_transfs_scraped.append(transfer_scraped)

                transfs_scraped[db_acc_id] = acc_transfs_scraped
        except Exception as _e:
            self.logger.error(
                'Failed getting transfers scraped from transfers parsed: '
                'HANDLED EXCEPTION: {}'.format(traceback.format_exc())
            )

        return transfs_scraped

    def get_acc_transfs_scraped_in_db(
            self,
            acc_w_transfs_active: DBTransferAccountConfig,
            acc_movs: List[DBMovementConsideredTransfer]) -> List[TransferScraped]:

        # Gets transfers from movements for specific account
        fin_ent_account_id = acc_w_transfs_active.FinancialEntityAccountId
        self.logger.info('{}: get transfers from movements in DB'.format(
            fin_ent_account_id
        ))
        acc_transfs_scraped = []
        try:
            transfers_filters = self.db_connector.get_active_transfers_filters(
                acc_w_transfs_active.AccountId,
                NAVIGATION_TYPE_MOVIMIENTOS
            )

            filters_movs_abono_vencimiento_confirming = [
                f
                for f in transfers_filters
                if f.BankCode == ABONO_VENCIMIENTO_CONFIRMING_BANK_CODE
            ]
            filters_movs_anticipo_confirming = [
                f
                for f in transfers_filters
                if f.BankCode == ANTICIPOS_CONFIRMING_BANK_CODE
            ]

            for mov in acc_movs:
                self.logger.info('{}: creating transfers from DB movement: {}@{} (id={})'.format(
                    fin_ent_account_id,
                    float(mov.Amount),  # drop decimal zeros 719.25000000000000000000
                    mov.OperationalDate.strftime(project_settings.SCRAPER_DATE_FMT),
                    mov.InitialId,
                ))
                current_filters = []
                if "Código: {}".format(ABONO_VENCIMIENTO_CONFIRMING_BANK_CODE) in mov.StatementExtendedDescription:
                    current_filters = filters_movs_abono_vencimiento_confirming
                if "Código: {}".format(ANTICIPOS_CONFIRMING_BANK_CODE) in mov.StatementExtendedDescription:
                    current_filters = filters_movs_anticipo_confirming

                if not current_filters:
                    continue

                transf_parsed = parse_helpers_netcash_transfers.get_transf_parsed_from_mov_extended_description(
                    mov.StatementExtendedDescription
                )
                account_order = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'AccountOrder')
                name_order = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'NameOrder')
                concept = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Concept')
                reference = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Reference')
                description = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Description')
                observation = self._get_transf_scraped_field_value(current_filters, transf_parsed, 'Observation')

                transfer_scraped = TransferScraped(
                    AccountId=mov.AccountId,
                    CustomerId=self.db_customer_id,
                    OperationalDate=mov.OperationalDate.strftime(project_settings.DB_DATE_FMT),
                    ValueDate=mov.ValueDate.strftime(project_settings.DB_DATE_FMT),
                    Amount=round(float(mov.Amount), 2),  # from decimal
                    TempBalance=None,
                    Currency=transf_parsed['Divisa'],
                    AccountOrder=account_order,
                    NameOrder=name_order,
                    Concept=concept,
                    Reference=reference,
                    Description=description,
                    Observation=observation,
                    # str to set 'not linked' (No vinculable) then by TransfersLinker
                    IdStatement=str(mov.InitialId),
                    FinancialEntityName=self.fin_entity_name,
                )
                if transfer_scraped.Amount > 0:
                    acc_transfs_scraped.append(transfer_scraped)

            self.logger.info('{}: got transfers from DB: count={}'.format(
                fin_ent_account_id,
                len(acc_transfs_scraped)
            ))
        except Exception as _e:
            self.logger.error('Failed getting transfers from movements in db: HANDLED EXCEPTION: {}'.format(
                traceback.format_exc()
            ))
        return acc_transfs_scraped

    def get_transfs_scraped_in_db(
            self,
            accs_w_transfs_active: List[DBTransferAccountConfig]) -> Dict[int, List[TransferScraped]]:
        """Gets extra transfers from DB"""
        transfs_scraped = {}  # type: Dict[int, List[TransferScraped]]
        try:
            for acc_w_transfs_active in accs_w_transfs_active:
                date_from = self.basic_get_date_from_for_transfs(acc_w_transfs_active)
                acc_movs_considered_transfers = self.db_connector.get_movs_considered_transfers(
                    acc_w_transfs_active.AccountId,
                    acc_w_transfs_active.FinancialEntityAccountId,
                    date_from
                )  # type: List[DBMovementConsideredTransfer]
                acc_transfs_scraped = self.get_acc_transfs_scraped_in_db(
                    acc_w_transfs_active,
                    acc_movs_considered_transfers
                )
                transfs_scraped[acc_w_transfs_active.AccountId] = acc_transfs_scraped
        except Exception as _e:
            self.logger.error('Failed to get transfers from movements: HANDLED EXCEPTION: {}'.format(
                traceback.format_exc()
            ))
        return transfs_scraped

    def get_transfs_parsed_in_transfs_menu(
            self,
            s: MySession,
            active_transfs_accs: List[DBTransferAccountConfig]) -> Dict[int, List[TransferParsed]]:
        #   Gets transfers from Transfers menu at Bank:
        self.logger.info('Parse transfs in tranfs menu')
        # {db_account_id: transfers_parsed}
        transfs_parsed = {}  # type: Dict[int, List[TransferParsed]]

        try:
            # TODO: add concurrent scraping
            for acc_w_transfs_active in active_transfs_accs:
                fin_ent_account_id = acc_w_transfs_active.FinancialEntityAccountId
                acc_short_no = fin_ent_account_id[14:24]
                date_from = self.basic_get_date_from_for_transfs(acc_w_transfs_active)
                self.logger.info('{}: get transfers from transfers menu: from_date={}'.format(
                    fin_ent_account_id,
                    date_from.strftime(project_settings.SCRAPER_DATE_FMT)
                ))
                dates = date_funcs.get_date_range(date_from, self.date_to)
                acc_transfs_parsed = []  # type: List[TransferParsed]
                for single_date in dates:
                    single_date_str = single_date.strftime(project_settings.SCRAPER_DATE_FMT)
                    # Need to open for each account
                    resp_transf_filter_form, account_select_options = \
                        self.open_tranfs_filter_form_and_get_acc_select_opts(s)
                    self.logger.info('{}: {}: got account_select_options: {}'.format(
                        fin_ent_account_id,
                        single_date_str,
                        account_select_options
                    ))
                    if acc_short_no not in account_select_options:
                        self.logger.warning(
                            '{}: get transfers from transfers menu: '
                            'not found select option for account_short_number={}. Skip'.format(
                                fin_ent_account_id,
                                acc_short_no,
                            ))
                        continue

                    acc_position = account_select_options[acc_short_no]
                    ok, resp_acc_transfers = self.open_acc_transfers(s, acc_position, single_date, single_date, resp_transf_filter_form)
                    if not ok:
                        self.basic_log_wrong_layout(
                            resp_acc_transfers,
                            '{}: could not open account transfers: '
                            'account_position={}. Abort'.format(
                                fin_ent_account_id,
                                acc_position,
                            )
                        )
                        break  # TODO: VB: continue?

                    self.logger.info('{}: {}: parse transfs'.format(fin_ent_account_id, single_date_str))
                    ok, s, last_url, acc_transfs_parsed_one_day = self.get_acc_transfs_parsed(
                        s,
                        fin_ent_account_id,
                        single_date_str,
                        resp_acc_transfers
                    )
                    if not ok:
                        # already reported
                        break  # TODO: VB: continue?

                    acc_transfs_parsed = acc_transfs_parsed + acc_transfs_parsed_one_day

                transfs_parsed[acc_w_transfs_active.AccountId] = acc_transfs_parsed

                self.logger.info('{}: parsed transfs count={}'.format(
                    fin_ent_account_id,
                    len(acc_transfs_parsed)
                ))

            # TODO possible service unavailable and its cause, check if
            self.logger.info('Parsed transfs in tranfs menu: accounts count={}'.format(
                len(transfs_parsed)
            ))
        except Exception as _e:
            self.logger.error('Failed to get transfers from transfers menu: HANDLED EXCEPTION: {}'.format(
                traceback.format_exc()
            ))
        return transfs_parsed

    def download_transfers(self, s: MySession) -> Tuple[bool, Dict[int, List[TransferScraped]]]:

        # Download transfers from transfers menu, and convert some movements in DB to transfers.
        # Insert transfers of two origins in DB.
        accs_w_tranfs_active = self.db_connector.get_active_transfers_accounts()  # type: List[DBTransferAccountConfig]

        transfs_scraped_in_transfs_menu = {}  # type: Dict[int, List[TransferScraped]]
        transfs_scraped_in_db = {}  # type: Dict[int, List[TransferScraped]]
        try:
            if not accs_w_tranfs_active:
                return True, {}

            transfs_parsed_in_transfs_menu = self.get_transfs_parsed_in_transfs_menu(s, accs_w_tranfs_active)
            transfs_scraped_in_transfs_menu = self.get_transfs_scraped_from_transfs_parsed_in_transfs_menu(
                transfs_parsed_in_transfs_menu
            )

            transfs_scraped_in_db = self.get_transfs_scraped_in_db(accs_w_tranfs_active)

            if project_settings.IS_UPDATE_DB:
                for acc_id, transfs_scraped in transfs_scraped_in_transfs_menu.items():
                    self.db_connector.save_transfers_transactional(acc_id, transfs_scraped)

                for acc_id, transfs_scraped in transfs_scraped_in_db.items():
                    self.db_connector.save_transfers_transactional(acc_id, transfs_scraped)

                transfers_linker = TransfersLinker(
                    db_customer_id=self.db_customer_id,
                    fin_entity_name=self.fin_entity_name,
                    db_financial_entity_access_id=self.db_financial_entity_access_id
                )
                succeed = transfers_linker.link_transfers_to_movements()

        except Exception as _e:
            self.logger.error('Failed to download transfers for entity {}: HANDLED EXCEPTION {}'.format(
                self.db_financial_entity_id,
                traceback.format_exc()
            ))
            # self.logger.accesos_log_error("-> download_transfers: Error descargando transferencias {}".format(excep))
            return False, transfs_scraped_in_transfs_menu

        return True, transfs_scraped_in_transfs_menu

    def main(self) -> MainResult:
        s, resp, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(resp.url, resp.text, reason)

        self.download_transfers(s)
        self.basic_log_time_spent('GET TRANSFERS')

        return self.basic_result_success()
