import threading
import time
import traceback
from concurrent import futures
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Set

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import MySession, Response
from custom_libs.transfers_linker import TransfersLinker
from project import fin_entities_ids
from project import settings as project_settings
from project.custom_types import (
    AccountParsed, AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
    ScraperParamsCommon, MainResult
)
from project.custom_types import (
    DBTransferAccountConfig, DBTransferFilter,
    TransferParsed, TransferScraped, MovementScraped,
    DBTransfer, MovementParsed
)
from scrapers.bankinter_scraper import parse_helpers
from scrapers.bankinter_scraper.bankinter_scraper import BankinterScraper
from scrapers.bankinter_scraper.custom_types import Company
from . import parse_helpers_transfers, parse_helpers_receipts
from .custom_types import ReceiptOption, ReceiptReqParams

__version__ = '1.6.0'

__changelog__ = """
1.6.0
process_account, process_account_multicurrency:
    force to parse download link params
1.5.1
upd log msg
1.5.0
download_movement_transfer readded parsing of transfer fields from movement parse_transfer_fields_from_movement
1.4.1
upd log msg
1.4.0
download_movement_transfer deleted parsing of transfer fields from movement parse_transfer_fields_from_movement
1.3.1
call transf_linker with named args
1.3.0
TransfersLinker: upd import path
1.2.1
fixed _transfer_scraped_from_transfer_parsed, transf_str (use TransferParsed for logging)
1.2.0
get_transfers_companies
_extract_resp_html_w_transfers
process_transfers_company
process_transfers_account
transfer_scraped_from_transfer_parsed
_transf_str
filter_transfers_scraped_and_not_inserted
main: added transfers download from transfers navigation besides existing from movements
renamed get_transfer_scraped: transfer_scraped_from_movement_scraped
_open_transfers_company_page (not used for now)
1.1.0
fmt
replaced next with access by index
upd log msgs
parse_helpers_transfers: fmt, better typing, replaced next with access by index
1.0.0
init
"""

PROCESS_TRANSFER_MAX_WORKERS = 1

DOWNLOAD_TRANSFERS_RETRY_AFTER_SECONDS = 5

NAVIGATION_TYPE_TRANSFERENCIAS = 'TRANSFERENCIAS'
NAVIGATION_TYPE_MOVIMIENTOS = 'MOVIMIENTOS'

NATIONAL_TRANSFER_BANK_CODE = '0007'
INTERNATIONAL_TRANSFER_BANK_CODE = '0163'

ABONO_VENCIMIENTO_CONFIRMING_BANK_CODE = '0591'
ANTICIPOS_CONFIRMING_BANK_CODE = '0391'

EMPTY_TRANSFER_FIELD_DEFAULT_VALUE = 'N/A'

MAX_AUTOINCREASING_OFFSET_DAYS = 90
MAX_OFFSET = 90
MAX_ALLOWED_MOVEMENTS_PER_PAGE = 135
MAX_CONCURRENT_WORKERS = 4

NO_ACCOUNTS_MARKER = 'NO TIENE CUENTAS'


class BankinterTransfersScraper(BankinterScraper):
    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES,
                 scraper_name='BankinterTransfersScraper') -> None:

        super().__init__(scraper_params_common, proxies, scraper_name)
        self.fin_entity_name = fin_entities_ids.get_fin_entity_name_by_id(self.db_financial_entity_id)
        self.accs_w_tranfs_active = self.db_connector.get_active_transfers_accounts()  # type: List[DBTransferAccountConfig]
        self.transfers_filters_navigation_movements = []  # type: List[DBTransferFilter]
        for acc_w_tranfs_active in self.accs_w_tranfs_active:
            transfers_filters = self.db_connector.get_active_transfers_filters(acc_w_tranfs_active.AccountId,
                                                                               NAVIGATION_TYPE_MOVIMIENTOS)
            self.transfers_filters_navigation_movements.extend(transfers_filters)

        self.transfers_filters_navigation_transfers = []  # type: List[DBTransferFilter]
        for acc_w_tranfs_active in self.accs_w_tranfs_active:
            transfers_filters = self.db_connector.get_active_transfers_filters(acc_w_tranfs_active.AccountId,
                                                                               NAVIGATION_TYPE_TRANSFERENCIAS)
            self.transfers_filters_navigation_transfers.extend(transfers_filters)

        self.receipts_lock = threading.Lock()

        # Special set to notify only one time for a set of ambiguous_receipts.
        # Example: -u 198549 -a 6918, acc ES8801287712680500001871, 06/06/19
        #  - all receipts for movements with amount 37,56 D
        #  have description "LIQUIDACION DE AVAL".
        # key is fin_ent_account_id__descr_part
        self.ambiguous_receipts = set()  # type: Set[str]

    def _is_in_ambiguous_receipts(self, ambiguous_receipt_key: str) -> bool:
        with self.receipts_lock:
            return ambiguous_receipt_key in self.ambiguous_receipts

    def _add_to_ambiguous_receipts(self, ambiguous_receipt_key: str) -> None:
        with self.receipts_lock:
            self.ambiguous_receipts.add(ambiguous_receipt_key)

    def _handle_various_receipts_selection(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed) -> Tuple[bool, ReceiptReqParams]:
        """Handles case:
        Some movements return pages with receipt selection if there are
        several movements w/ the same amount during one day
        -u 198549 -a 6921 acc ES9101287712680100000395, 20190605
        :returns  (is_success, ReceiptReqParams)
        """

        mov_receipt_params = movement_parsed['receipt_params']  # type: ReceiptReqParams
        mov_str = self._mov_str(movement_scraped)

        req_various_url = ('https://empresas.bankinter.com/www/es-es/cgi/'
                           'empresas+cuentas+varios_documentos')

        req_various_params = {
            'cuenta': account_scraped.FinancialEntityAccountId,  # 01287712100000395
            'aplicacion': mov_receipt_params.semana,  # 'A04'
            'formulario': mov_receipt_params.envio,  # 'F008'
            'importe': abs(movement_scraped.Amount),  # 1020.00, only abs val
            'fecha_contable': movement_scraped.OperationalDate,  # '20190605'
            'fecha_valor': movement_scraped.ValueDate  # '20190605'

        }

        resp_receipts_selection = s.post(
            req_various_url,
            data=req_various_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        receipts_options = parse_helpers_receipts.get_receipts_options(
            resp_receipts_selection.text
        )

        receipt_option = None  # type: Optional[ReceiptOption]
        for ro in receipts_options:
            # Looking for
            # `AB 2015, S.L.`  in  `OTRAS EN /AB 2015, S.L.`
            # `Renovables Rotonda,`  in  `/Renovables Rotonda, S.L`
            # That means receipt_option.descr_part
            #  is always a part of correct movement_scraped.StatementDescription
            if ro.descr_part in movement_scraped.StatementDescription:
                if receipt_option is None:
                    receipt_option = ro
                    # Do not interrupt the loop to be sure
                    # that this is unique receipt_option with such appropriate
                    # descr_part for the movement
                else:
                    # Handle ambiguous receipts - skip downloading with
                    # one time err notification.
                    # Example: -u 198549 -a 6918, acc ES8801287712680500001871, 06/06/19
                    ambiguous_receipt_key = '{}__{}'.format(
                        account_scraped.FinancialEntityAccountId,
                        ro.descr_part
                    )
                    if self._is_in_ambiguous_receipts(ambiguous_receipt_key):
                        self.logger.info(
                            "{}: {}: previously detected ambiguous receipt. "
                            "Skip without additional err notification".format(
                                account_scraped.FinancialEntityAccountId,
                                mov_str
                            )
                        )
                        return False, mov_receipt_params

                    # First-time ambiguous receipt detected
                    self._add_to_ambiguous_receipts(ambiguous_receipt_key)
                    self.logger.warning(
                        "{}: {}: "
                        "bank-level ambiguity: found several receipt links with the same descr_part `{}` "
                        "at the receipt selection page. "
                        "SKIP receipt downloading.".format(
                            account_scraped.FinancialEntityAccountId,
                            mov_str,
                            ro.descr_part
                        )
                    )
                    return False, mov_receipt_params

        if not receipt_option:
            self.logger.warning(
                "{}: {}: can't find a specific receipt for descr `{}`. Skip. "
                "RESPONSE TEXT:\n{}".format(
                    account_scraped.FinancialEntityAccountId,
                    mov_str,
                    movement_scraped.StatementDescription,
                    extract.text_wo_scripts_and_tags(resp_receipts_selection.text)
                )
            )
            return False, mov_receipt_params

        mov_receipt_params_correct = receipt_option.req_params  # type: ReceiptReqParams
        self.logger.info(
            "{}: {}: got correct mov_receipt_params".format(
                account_scraped.FinancialEntityAccountId,
                mov_str,
            )
        )
        return True, mov_receipt_params_correct

    def _get_transf_scraped_field_value(
            self,
            filters: List[DBTransferFilter],
            transf_parsed: TransferParsed,
            transf_scraped_field_name: str) -> str:
        """Applies filter to transf parsed field to get transf scraped field value"""
        # TODO  COPIED FROM BBVA, move to dedicated func
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

    # NOT USED
    def _open_transfers_company_page(
            self,
            s: MySession,
            company: Company,
            fin_ent_account_id='') -> Tuple[bool, MySession, Response]:
        """:return (is_success, session, resp_company)"""
        resp_company = s.get(company.url,
                             headers=self.req_headers,
                             proxies=self.req_proxies)

        if resp_company.status_code != 200:
            if fin_ent_account_id:
                msg = 'Error opening received transfers company {} while processing account {}'.format(
                    company,
                    fin_ent_account_id
                )
            else:
                msg = 'Error opening received transfers company {}'.format(company)
            self.logger.error(msg)
            return False, s, resp_company

        # switch to received transfers explicitly to avoid pos multiempresa
        req_pos_global_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+pagos+transferencias_recibidas'

        req_pos_global_params = {
            'CUENTA': '',
            'cuenta_seleccionada': '',
            'ind_extracto': '2',
            'cambio_tipo_posicion': 'S'
        }
        resp_pos_global = s.post(
            req_pos_global_url,
            data=req_pos_global_params,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        if resp_pos_global.status_code != 200:
            if fin_ent_account_id:
                msg = 'Error switch to received transfers for {} while processing account {}'.format(
                    company,
                    fin_ent_account_id
                )
            else:
                msg = 'Error switch to received transfers for {}'.format(company)
            self.logger.error(msg)
            return False, s, resp_company

        return True, s, resp_pos_global

    def get_transfers_companies(self, s: MySession, resp_logged_in: Response) -> List[Company]:

        self.logger.info('Get transfers companies')
        url_position_global = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+pagos+transferencias_recibidas'
        if resp_logged_in.url != url_position_global:
            resp_logged_in = s.get(url_position_global, headers=self.req_headers, proxies=self.req_proxies)

        companies = parse_helpers.get_companies_parsed(resp_logged_in.text, resp_logged_in.url)
        return companies

    def process_company(self, s: MySession, company: Company, is_need_new_session: bool) -> bool:
        """
        get accounts and extract transfers from them
        then for each account run 'process account' to get movements
        """

        self.logger.info('Process company: {}'.format(company))

        if is_need_new_session:
            ok, s, resp_company = self._login_and_open_company_page(company)
        else:
            ok, s, resp_company = self._open_company_page(s, company)

        if not ok:
            return False  # already reported

        # Get one-currency accounts
        accounts_parsed = parse_helpers.get_accounts_parsed(resp_company.text)
        accounts_scraped = [self.basic_account_scraped_from_account_parsed(company.title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        # Get multi-currency accounts
        # Each subaccount_parsed_for_specific_currency contains fin_ent_account_id_parent (w/o currency)
        # [{parent_2_subaccounts_parsed_for_each_currency}, {parent_2_subaccounts_parsed_for_each_currency}, ...]
        accounts_multicurrency_parsed = parse_helpers.get_accounts_multicurrency_parsed(
            resp_company.text
        )  # type: List[Dict[str, AccountParsed]]

        # Flat list, just for uploading, not for movements extraction
        subaccounts_multicurrency_scraped = [
            self.basic_account_scraped_from_account_parsed(company.title, subaccounts_parsed)
            for account_parsed_multicurrency in accounts_multicurrency_parsed
            for subaccounts_parsed in account_parsed_multicurrency.values()
        ]  # type: List[AccountScraped]

        account_scraped_all = accounts_scraped + subaccounts_multicurrency_scraped

        is_need_new_session_for_each_account_processing = len(account_scraped_all) > 1

        self.logger.info('Company {} has {} accounts: {}'.format(
            company.title,
            len(account_scraped_all),
            account_scraped_all,
        ))

        if not account_scraped_all and NO_ACCOUNTS_MARKER not in resp_company.text:
            self.basic_log_wrong_layout(
                resp_company,
                '{}: suspicious results: no accounts found'.format(company.title)
            )

        # self.basic_upload_accounts_scraped(account_scraped_all)
        financial_entity_ids_w_transf_active = [
            acc_w_tranfs_active.FinancialEntityAccountId
            for acc_w_tranfs_active in self.accs_w_tranfs_active
        ]

        accounts_scraped = [
            account_scraped
            for account_scraped in accounts_scraped
            if account_scraped.FinancialEntityAccountId in financial_entity_ids_w_transf_active
        ]

        subaccounts_multicurrency_scraped = [
            subaccount_multicurrency_scraped
            for subaccount_multicurrency_scraped in subaccounts_multicurrency_scraped
            if subaccount_multicurrency_scraped.FinancialEntityAccountId in financial_entity_ids_w_transf_active
        ]

        self.basic_log_time_spent('GET ACCOUNTS')

        # Should use individual session for each account to get movements

        # TODO  Copied from BankinterScraper, consider using dedicated method
        # Process one-currency accounts
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_account,
                        s,
                        resp_company,
                        company,
                        account_scraped,
                        is_need_new_session_for_each_account_processing
                    ): account_scraped.FinancialEntityAccountId
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_account(
                    s,
                    resp_company,
                    company,
                    account_scraped,
                    is_need_new_session_for_each_account_processing
                )

        # Process multi-currency accounts
        subaccounts_multicurrency_scraped_dict = self.basic_gen_accounts_scraped_dict(
            subaccounts_multicurrency_scraped
        )

        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_account_multicurrency,
                        s,
                        resp_company,
                        company,
                        account_parsed_multicurrency_dict,
                        subaccounts_multicurrency_scraped_dict,
                        is_need_new_session_for_each_account_processing
                    ): self._get_fin_ent_account_id_parent(account_parsed_multicurrency_dict)
                    for account_parsed_multicurrency_dict in accounts_multicurrency_parsed
                    if account_parsed_multicurrency_dict
                }

                self.logger.log_futures_exc('process_account_multicurrency', futures_dict)
        else:
            for account_parsed_multicurrency_dict in accounts_multicurrency_parsed:
                self.process_account_multicurrency(
                    s,
                    resp_company,
                    company,
                    account_parsed_multicurrency_dict,
                    subaccounts_multicurrency_scraped_dict,
                    is_need_new_session_for_each_account_processing
                )

        return True

    def process_account(self,
                        s: MySession,
                        resp_company: Response,
                        company: Company,
                        account_scraped: AccountScraped,
                        is_need_new_session: bool) -> bool:
        """
        Log in again to process each account in different session
        get movements and upload them (if is_need_new_session = True)
        If one account of company, then is_need_new_session = False
        """
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        try:
            self.logger.info('Process_account: {}'.format(fin_ent_account_id))

            acc_w_transfer_active = [
                acc
                for acc in self.accs_w_tranfs_active
                if acc.FinancialEntityAccountId == account_scraped.FinancialEntityAccountId
            ][0]  # type: DBTransferAccountConfig

            date_from = self.basic_get_date_from_for_transfs(acc_w_transfer_active)  # type: datetime
            date_from_str = date_funcs.convert_dt_to_scraper_date_type1(date_from)

            resp_movs_text, date_from_str = self._extract_resp_html_w_movements(
                s,
                resp_company,
                company,
                fin_ent_account_id,
                is_need_new_session,
                date_from_str,
            )

            if not resp_movs_text:
                self.basic_set_movements_scraping_finished(fin_ent_account_id)
                return False

            all_movements_parsed = parse_helpers.get_movements_parsed_from_html_resp(
                resp_movs_text,
                True
            )

            db_acc_id = acc_w_transfer_active.AccountId

            transfers_movement_parsed_w_filters = self.get_transfers_movements_parsed_w_transfer_filters(
                all_movements_parsed, db_acc_id)

            movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
                transfers_movement_parsed_w_filters,
                date_from_str,
                current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
            )

            self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)

            ok, transfers_scraped = self.basic_download_transfers_common(
                s,
                account_scraped,
                movements_scraped,
                transfers_movement_parsed_w_filters
            )
            if not ok:
                return False  # already reported

            for index, value in enumerate(transfers_scraped):
                if value:
                    transfers_scraped[index] = value._replace(AccountId=db_acc_id)

            if project_settings.IS_UPDATE_DB:
                self.db_connector.save_transfers_transactional(db_acc_id, transfers_scraped)

                transfers_linker = TransfersLinker(
                    fin_entity_name=self.fin_entity_name,
                    db_customer_id=self.db_customer_id,
                    db_financial_entity_access_id=self.db_financial_entity_access_id
                )
                _ok = transfers_linker.link_transfers_to_movements()

            return True
        except Exception as _e:
            self.logger.error(
                '{}: failed process_account for transfers:'
                'HANDLED EXCEPTION: {}'.format(
                    fin_ent_account_id,
                    traceback.format_exc()
                )
            )
            return False

    def transfer_scraped_from_movement_scraped(
            self,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            transfer_filters: List[DBTransferFilter],
            parsed_transfer_fields: Dict[str, str]) -> Optional[TransferScraped]:
        try:

            account_order = self._get_transf_scraped_field_value(
                transfer_filters,
                parsed_transfer_fields,
                'AccountOrder'
            )
            name_order = self._get_transf_scraped_field_value(transfer_filters, parsed_transfer_fields, 'NameOrder')
            concept = self._get_transf_scraped_field_value(transfer_filters, parsed_transfer_fields, 'Concept')
            reference = self._get_transf_scraped_field_value(transfer_filters, parsed_transfer_fields, 'Reference')
            description = self._get_transf_scraped_field_value(transfer_filters, parsed_transfer_fields, 'Description')
            observation = self._get_transf_scraped_field_value(transfer_filters, parsed_transfer_fields, 'Observation')

            transfer_scraped = TransferScraped(
                AccountId=0,
                CustomerId=self.db_customer_id,
                OperationalDate=movement_scraped.OperationalDate,
                ValueDate=movement_scraped.ValueDate,
                # date_funcs.convert_date_to_db_format(transf_parsed['Fecha Valor']),
                Amount=movement_scraped.Amount,
                TempBalance=movement_scraped.TempBalance,
                Currency=account_scraped.Currency,
                AccountOrder=account_order,
                NameOrder=name_order,
                Concept=concept,
                Reference=reference,
                Description=description,
                Observation=observation,
                IdStatement=None,
                FinancialEntityName=self.fin_entity_name,
            )
            return transfer_scraped
        except:
            mov_str = self._mov_str(movement_scraped)
            self.logger.error("{}: {}: can't generate scraped transfer pdf: EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                mov_str,
                traceback.format_exc()
            ))
            return None

    def download_movement_transfer(self,
                                   s: MySession,
                                   account_scraped: AccountScraped,
                                   movement_scraped: MovementScraped,
                                   movement_parsed: MovementParsed,
                                   meta: dict) -> Optional[TransferScraped]:
        """Downloads transfer pdf file and extract filtered transfer information from pdf file if exists
           If there is no pdf file extract filtered transfer information from movement scraped"""
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        transfer_filters = movement_parsed['transfer_filters']  # type: List[DBTransferFilter]

        if not movement_parsed['may_have_receipt']:
            ok, parsed_transfer_fields = parse_helpers_transfers.parse_transfer_fields_from_movement(
                self.logger,
                fin_ent_account_id,
                movement_parsed
            )
            if not ok:
                self.logger.info("{}: no pdf available for movement: {} {} {}".format(
                    fin_ent_account_id,
                    movement_parsed['operation_date'],
                    movement_parsed['amount'],
                    movement_parsed['description']
                ))
                return None  # already reported

            transf_scraped = self.transfer_scraped_from_movement_scraped(
                account_scraped,
                movement_scraped,
                transfer_filters,
                parsed_transfer_fields
            )
            return transf_scraped

        mov_receipt_params = movement_parsed['receipt_params']  # type: ReceiptReqParams
        mov_str = self._mov_str(movement_scraped)

        self.logger.info('{}: download transfer for mov {}'.format(
            fin_ent_account_id,
            mov_str
        ))

        try:
            if mov_receipt_params.cuenta != fin_ent_account_id:
                self.logger.info(
                    "{}: {}: various receipts selection page detected. Processing".format(
                        fin_ent_account_id,
                        mov_str
                    )
                )

                ok, mov_receipt_params = self._handle_various_receipts_selection(
                    s,
                    account_scraped,
                    movement_scraped,
                    movement_parsed
                )

                if not ok:
                    self.logger.error(
                        "{}: {}: can't handle various receipts selection".format(
                            fin_ent_account_id,
                            mov_str,
                        )
                    )
                    parsed_transfer_fields = parse_helpers_transfers.get_empty_receipt_parsed_transfer_fields(
                        'Recibos ambiguos'
                    )
                    transf_scraped = self.transfer_scraped_from_movement_scraped(
                        account_scraped,
                        movement_scraped,
                        transfer_filters,
                        parsed_transfer_fields
                    )
                    return transf_scraped

            req_pdf_url = self._get_download_pdf_url(mov_receipt_params)

            resp_pdf = s.get(
                req_pdf_url,
                headers=self.req_headers,
                proxies=self.req_proxies,
                stream=True
            )

            # Expected PDF, but got HTML
            if b'PDF-' not in resp_pdf.content:
                self.logger.error(
                    "{}: {}: can't download pdf. resp_pdf is not a valid PDF. Skip. "
                    "RESPONSE\n{}".format(
                        account_scraped.FinancialEntityAccountId,
                        mov_str,
                        resp_pdf.text
                    )
                )
                return None

            parsed_transfer_fields = parse_helpers_transfers.parse_transfer_fields_from_pdf(
                self.logger,
                transfer_filters,
                resp_pdf.content
            )
            transf_scraped = self.transfer_scraped_from_movement_scraped(
                account_scraped,
                movement_scraped,
                transfer_filters,
                parsed_transfer_fields
            )
            return transf_scraped

        except Exception as _e:
            self.logger.error("{}: {}: can't download pdf: EXCEPTION\n{}".format(
                fin_ent_account_id,
                mov_str,
                traceback.format_exc()
            ))
            return None

    def _mov_str(self, movement_scraped: MovementScraped):
        return "{} ({}/{})".format(movement_scraped.KeyValue[:6],
                                   movement_scraped.Amount,
                                   movement_scraped.OperationalDate)

    def _get_download_pdf_url(self, req_params: ReceiptReqParams) -> str:
        # 'https://empresas.bankinter.com/www/es-es/cgi/empresas+cuentas+vis_pdf
        # ?semana=50&persona=null
        # &envio=1548091&cuenta=01287712500001871&fecha=20181213&fecha_valor=20181213
        # &num_pag=006&ind_csf=1&ind_anyo=A'
        url = (
            'https://empresas.bankinter.com/'
            'www/es-es/cgi/empresas+cuentas+vis_pdf?'
            'semana={semana}&persona=null&envio={envio}&cuenta={cuenta}&fecha={fecha}'
            '&fecha_valor={fecha_valor}&num_pag=006&ind_csf=1&ind_anyo=A'.format(
                **req_params._asdict()
            )
        )

        return url

    def process_account_multicurrency(
            self,
            s: MySession,
            resp_company: Response,
            company: Company,
            account_parsed_multicurrency_dict: Dict[str, AccountParsed],
            subaccounts_multicurrency_scraped_dict: Dict[str, AccountScraped],
            is_need_new_session: bool) -> bool:

        if not account_parsed_multicurrency_dict:
            return True

        # Get fin_ent_account_id_parent from any parsed subaccount
        fin_ent_account_id_parent = self._get_fin_ent_account_id_parent(account_parsed_multicurrency_dict)
        self.logger.info('Process multi-currency account: {}'.format(fin_ent_account_id_parent))

        # Skip multi-currency account only if all sub-accounts marked as 'inactive'
        is_active = any(self.basic_check_account_is_active(acc['financial_entity_account_id'])
                        for acc in account_parsed_multicurrency_dict.values())
        if not is_active:
            return True
        self.logger.info('Active sub-accounts detected: process all of {}'.format(
            account_parsed_multicurrency_dict
        ))

        # Get date_from as the earliest (minimal) date_from of subaccounts
        # (because the scraper extracts movements of all subaccounts by one request).
        date_from_minimal = self.date_to  # will redefine in the loop below
        include_link_data_dict = {}
        for acc_parsed in account_parsed_multicurrency_dict.values():
            date_from_str = self.basic_get_date_from(
                acc_parsed['financial_entity_account_id'],
                max_autoincreasing_offset=MAX_AUTOINCREASING_OFFSET_DAYS
            )
            date_from = date_funcs.get_date_from_str(date_from_str)
            date_from_minimal = min(date_from, date_from_minimal)

            # Get multicurrency subaccount scraped information to parse download link params
            subaccount_scraped_multicurrency = subaccounts_multicurrency_scraped_dict[
                acc_parsed['financial_entity_account_id']]
            include_link_data_dict[subaccount_scraped_multicurrency.Currency] = True

        # PROBLEM:
        # If multi-currency account has a subacount with very old movements and there are
        # no new movements at that subaccount, then it may cause of balance integrity error
        # for another subaccount with many new movements because there is a limit: only 30 pages
        # with movements are allowed - that's why it may be impossible to extract
        # new movements (ASC ordering) if we try to scrape with very old date_from
        # Example:
        # DB customer 198504: fin_entity_access 6223: 01280073550025525EUR: BALANCE INTEGRITY ERROR
        # SOLUTION:
        # allow minimal_date_from >= date_to - 2 * RESCRAPE_OFFSET
        # It will work because there are scraping attempts each night.
        max_offset_days = 2 * project_settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV
        date_from_minimal = max(date_from_minimal, self.date_to - timedelta(days=max_offset_days))
        date_from_str_minimal = date_funcs.convert_dt_to_scraper_date_type1(date_from_minimal)

        resp_text, date_from_str = self._extract_resp_html_w_movements(
            s,
            resp_company,
            company,
            fin_ent_account_id_parent,
            is_need_new_session,
            date_from_str_minimal
        )

        if not resp_text:
            self.basic_set_movements_scraping_finished(fin_ent_account_id_parent)
            return False

        # dict with currency code as key and list of movements as val
        movements_parsed_multicurrency = parse_helpers.get_movements_parsed_from_html_resp_multicurrency(
            resp_text,
            fin_ent_account_id_parent,
            self.logger,
            include_link_data_dict,
        )  # type: Dict[str, List[MovementParsed]]

        for currency, movements_parsed in movements_parsed_multicurrency.items():

            movements_scraped, movements_parsed_filtered = self.basic_movements_scraped_from_movements_parsed(
                movements_parsed,
                date_from_str,
                current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
            )

            subaccount_scraped = subaccounts_multicurrency_scraped_dict[
                account_parsed_multicurrency_dict[currency]['financial_entity_account_id']
            ]  # type: AccountScraped

            self.basic_log_process_account(subaccount_scraped.FinancialEntityAccountId,
                                           date_from_str, movements_scraped)

            acc_w_transfer_active = [
                acc
                for acc in self.accs_w_tranfs_active
                if acc.FinancialEntityAccountId == subaccount_scraped.FinancialEntityAccountId
            ][0]  # type: DBTransferAccountConfig

            db_acc_id = acc_w_transfer_active.AccountId

            transfers_movement_parsed_w_filters = self.get_transfers_movements_parsed_w_transfer_filters(
                movements_parsed,
                db_acc_id
            )

            ok, transfers_scraped = self.basic_download_transfers_common(
                s,
                subaccount_scraped,
                movements_scraped,
                transfers_movement_parsed_w_filters
            )

            if not ok:
                return False  # already reported

            for index, value in enumerate(transfers_scraped):
                transfers_scraped[index] = transfers_scraped[index]._replace(AccountId=db_acc_id)

            if project_settings.IS_UPDATE_DB:
                self.db_connector.save_transfers_transactional(db_acc_id, transfers_scraped)

        return True

    def get_transfers_movements_parsed_w_transfer_filters(
            self,
            all_movements_parsed: List[MovementParsed],
            db_acc_id: int) -> List[MovementParsed]:
        """Filters movements parsed and returns movements considered
        transfers and its corresponding transfer filters
        """
        transfers_movements_parsed = []  # type: List[MovementParsed]

        acc_transfers_filters = self.db_connector.get_active_transfers_filters(
            db_acc_id,
            NAVIGATION_TYPE_MOVIMIENTOS
        )  # type: List[DBTransferFilter]

        for movement in all_movements_parsed:
            # Consider only  movements with amount > 0.
            if movement['amount'] < 0:
                continue

            # Get configured transfer filters for each movement transfer and add to movement
            transfer_filters = [f for f in acc_transfers_filters if movement['description'].startswith(f.BankCode)]
            # Add movement to returned transfers_movements_parsed
            if len(transfer_filters) <= 0:
                continue
            movement['transfer_filters'] = transfer_filters
            transfers_movements_parsed.append(movement)

        return transfers_movements_parsed

    def process_transfers_company(self, s: MySession, company: Company, is_need_new_session: bool) -> bool:
        """
        get accounts and extract transfers from them
        then for each account run 'process account' to get movements
        """

        self.logger.info('Process transfer company: {}'.format(company))

        if is_need_new_session:
            ok, s, resp_company = self._login_and_open_company_page(company)
        else:
            ok, s, resp_company = self._open_company_page(s, company)

        if not ok:
            return False  # already reported

        # Get one-currency accounts
        accounts_parsed = parse_helpers.get_transfers_accounts_parsed(resp_company.text)
        accounts_scraped = [self.basic_account_scraped_from_account_parsed(company.title, acc_parsed)
                            for acc_parsed in accounts_parsed]

        account_scraped_all = accounts_scraped

        is_need_new_session_for_each_account_processing = len(account_scraped_all) > 1

        self.logger.info('Company {} has {} accounts: {}'.format(
            company.title,
            len(account_scraped_all),
            account_scraped_all,
        ))

        if not account_scraped_all and NO_ACCOUNTS_MARKER not in resp_company.text:
            self.basic_log_wrong_layout(
                resp_company,
                '{}: suspicious results: no accounts found'.format(company.title)
            )

        # self.basic_upload_accounts_scraped(account_scraped_all)
        financial_entity_ids_w_transf_active = [
            acc_w_tranfs_active.FinancialEntityAccountId
            for acc_w_tranfs_active in self.accs_w_tranfs_active
        ]

        accounts_scraped = [
            account_scraped
            for account_scraped in accounts_scraped
            if account_scraped.FinancialEntityAccountId in financial_entity_ids_w_transf_active
        ]

        self.basic_log_time_spent('GET TRANSFERS ACCOUNTS')

        # Should use individual session for each account to get movements

        # TODO  Copied from BankinterScraper, consider using dedicated method
        # Process one-currency accounts
        if project_settings.IS_CONCURRENT_SCRAPING:
            with futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:

                futures_dict = {
                    executor.submit(
                        self.process_transfers_account,
                        s,
                        resp_company,
                        company,
                        account_scraped,
                        is_need_new_session_for_each_account_processing
                    ): account_scraped.FinancialEntityAccountId
                    for account_scraped in accounts_scraped
                }

                self.logger.log_futures_exc('process_account', futures_dict)
        else:
            for account_scraped in accounts_scraped:
                self.process_transfers_account(
                    s,
                    resp_company,
                    company,
                    account_scraped,
                    is_need_new_session_for_each_account_processing
                )

        return True

    def _extract_resp_html_w_transfers(
            self,
            s: MySession,
            resp_company: Response,
            company: Company,
            fin_ent_account_id: str,
            is_need_new_session: bool,
            single_date_str='') -> Tuple[Optional[str], str]:
        """:returns: (joined html texts of pages with movements, date_from_str)"""

        if is_need_new_session:
            ok, s, resp_company = self._login_and_open_company_page(company, fin_ent_account_id)
            if not ok:
                return None, ''

        if not single_date_str:
            single_date_str = self.basic_get_date_from(
                fin_ent_account_id,
                max_autoincreasing_offset=MAX_AUTOINCREASING_OFFSET_DAYS,
                max_offset=MAX_OFFSET
            )

        self.basic_log_process_account(fin_ent_account_id, single_date_str, None, single_date_str)

        day_from, month_from, year_from = single_date_str.split('/')
        day_to, month_to, year_to = single_date_str.split('/')

        req_params = {
            'pantalla': '1',
            'importe_desde': '',
            'importe_hasta': '',
            'cuenta_seleccionada': fin_ent_account_id,
            'busq': '0',
            'dia_desde': day_from,
            'mes_desde': month_from,
            'anio_desde': year_from,
            'dia_hasta': day_to,
            'mes_hasta': month_to,
            'anio_hasta': year_to,
            'banco': '',
            'control_banco': '',
            'cuenta_beneficiaria_empresa': '',
            'dirswift': '',
            'importe_mayor': '',
            'importe_menor': '',
            'importe_igual': '',
            'num_contrato': ''
        }

        req_url = 'https://empresas.bankinter.com/www/es-es/cgi/empresas+pagos+transferencias_recibidas_euros'

        has_next_movements = True
        resp_text = ""

        page_ix = 0
        while has_next_movements:
            time.sleep(0.1)
            page_ix += 1

            self.logger.info('{}: open page {} with movements'.format(
                fin_ent_account_id,
                page_ix
            ))

            resp_movs_i = Response()  # suppress linter warnings
            for _ in range(3):
                resp_movs_i = s.post(
                    req_url,
                    data=req_params,
                    headers=self.req_headers,
                    proxies=self.req_proxies,
                    timeout=30,
                )

                if resp_movs_i.status_code == 200:
                    break
            else:
                msg = "{}: dates from {} to {} : error: can't get html with movements\nResponse:\n{}".format(
                    fin_ent_account_id,
                    single_date_str,
                    self.date_to_str,
                    resp_movs_i.text
                )
                self.logger.error(msg)
                self.basic_set_movements_scraping_finished(fin_ent_account_id)
                # DAF: if fails once we return None :-> So we are prefering None
                # than an incomplete list of movements
                return None, single_date_str

            resp_text += "\r\n" + resp_movs_i.text

            has_next_movements = '<button type="submit">Siguiente</button>' in resp_movs_i.text
            if has_next_movements:
                # req_params['tramoCons'] = "Todos los tramos"
                form_sg_val = extract.re_last_or_blank(
                    '(?si)<input name="form-sg" type="hidden" value="([^"]*)"',
                    resp_movs_i.text
                )
                if form_sg_val:
                    req_params['form-sg'] = form_sg_val
                req_params['ROW'] = "NEXT"

        return resp_text, single_date_str


    def process_transfers_account(self,
                                  s: MySession,
                                  resp_company: Response,
                                  company: Company,
                                  account_scraped: AccountScraped,
                                  is_need_new_session: bool) -> bool:
        """
        Log in again to process each account in different session
        get movements and upload them (if is_need_new_session = True)
        If one account of company, then is_need_new_session = False
        """
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        if not self.basic_check_account_is_active(fin_ent_account_id):
            return True

        try:
            self.logger.info('Process_account: {}'.format(fin_ent_account_id))

            acc_w_transfer_active = [
                acc
                for acc in self.accs_w_tranfs_active
                if acc.FinancialEntityAccountId == account_scraped.FinancialEntityAccountId
            ][0]  # type: DBTransferAccountConfig

            date_from = self.basic_get_date_from_for_transfs(acc_w_transfer_active)  # type: datetime
            date_from_str = date_funcs.convert_dt_to_scraper_date_type1(date_from)

            dates = date_funcs.get_date_range(date_from, self.date_to)
            acc_transfs_parsed = []  # type: List[TransferParsed]
            for single_date in dates:
                single_date_str = single_date.strftime(project_settings.SCRAPER_DATE_FMT)

                resp_movs_text, single_date_str = self._extract_resp_html_w_transfers(
                    s,
                    resp_company,
                    company,
                    fin_ent_account_id,
                    is_need_new_session,
                    single_date_str,
                )

                if not resp_movs_text:
                    self.basic_set_movements_scraping_finished(fin_ent_account_id)
                    return False

                transfers_parsed = parse_helpers_transfers.get_transfers_parsed_from_html_resp(
                    fin_ent_account_id,
                    resp_movs_text,
                    self.logger
                )

                acc_transfs_parsed.extend(transfers_parsed)

            db_acc_id = acc_w_transfer_active.AccountId
            transfer_filters = [filter for filter in self.transfers_filters_navigation_transfers
                                if filter.AccountId == db_acc_id]

            transfers_scraped_w_none_elements = []  # type Optional[TransferScraped]
            for transfer_parsed in acc_transfs_parsed:
                transfer_scraped = self.transfer_scraped_from_transfer_parsed(
                    db_acc_id,
                    account_scraped,
                    transfer_parsed,
                    transfer_filters,
                )
                transfers_scraped_w_none_elements.append(transfer_scraped)

            transfers_scraped = [t for t in transfers_scraped_w_none_elements if t]

            self.basic_log_process_account_transfers(fin_ent_account_id, date_from_str, transfers_scraped)

            if project_settings.IS_UPDATE_DB:
                # TODO Make configurable at DB linking transfers to movements
                transfers_scraped_to_instert = self.filter_transfers_scraped_and_not_inserted(db_acc_id,
                                                                                              date_from_str,
                                                                                              transfers_scraped)
                self.db_connector.save_transfers_transactional(db_acc_id, transfers_scraped_to_instert)

            return True
        except Exception as _e:
            self.logger.error(
                '{}: failed process_account for transfers:'
                'HANDLED EXCEPTION: {}'.format(
                    fin_ent_account_id,
                    traceback.format_exc()
                )
            )
            return False

    def filter_transfers_scraped_and_not_inserted(
            self,
            db_acc_id: int,
            date_from_str: str,
            transfers_scraped: List[TransferScraped]) -> List[TransferScraped]:
        '''Filters already inserted transfers to avoid reinsertion.'''
        date_to_str = date_funcs.convert_dt_to_scraper_date_type1(self.date_to)
        db_transfers = self.db_connector.get_transfers_w_operational_date_in_range(
            db_acc_id,
            date_from_str,
            date_to_str,
        )  # type: List[DBTransfer]

        transfers_scraped_to_instert = []  # type: List[TransferScraped]

        for transfer in transfers_scraped:
            already_inserted_transfers = [db_transfer for db_transfer in db_transfers if
                                          transfer.NameOrder == db_transfer.NameOrder and \
                                          transfer.Reference == db_transfer.Reference and \
                                          date_funcs.get_date_from_str(
                                              transfer.OperationalDate) == db_transfer.OperationalDate and \
                                          float(transfer.Amount) == db_transfer.Amount and \
                                          transfer.Reference == db_transfer.Reference and \
                                          transfer.NameOrder == db_transfer.NameOrder and \
                                          transfer.AccountOrder == db_transfer.AccountOrder and \
                                          transfer.Concept == db_transfer.Concept and \
                                          transfer.Description == db_transfer.Description
                                          ]
            if not already_inserted_transfers:
                transfers_scraped_to_instert.append(transfer)
        return transfers_scraped_to_instert

    def transfer_scraped_from_transfer_parsed(
            self,
            db_acc_id: int,
            account_scraped: AccountScraped,
            transfer_parsed: TransferParsed,
            transfer_filters: List[DBTransferFilter]) -> Optional[TransferScraped]:
        try:

            account_order = self._get_transf_scraped_field_value(
                transfer_filters,
                transfer_parsed,
                'AccountOrder'
            )
            name_order = self._get_transf_scraped_field_value(transfer_filters, transfer_parsed, 'NameOrder')
            concept = self._get_transf_scraped_field_value(transfer_filters, transfer_parsed, 'Concept')
            reference = self._get_transf_scraped_field_value(transfer_filters, transfer_parsed, 'Reference')
            description = self._get_transf_scraped_field_value(transfer_filters, transfer_parsed, 'Description')
            observation = self._get_transf_scraped_field_value(transfer_filters, transfer_parsed, 'Observation')

            transfer_scraped = TransferScraped(
                AccountId=db_acc_id,
                CustomerId=self.db_customer_id,
                OperationalDate=transfer_parsed['operation_date'],
                ValueDate=transfer_parsed['value_date'],
                # date_funcs.convert_date_to_db_format(transf_parsed['Fecha Valor']),
                Amount=transfer_parsed['amount'],
                TempBalance=None,
                Currency=account_scraped.Currency,
                AccountOrder=account_order,
                NameOrder=name_order,
                Concept=concept,
                Reference=reference,
                Description=description,
                Observation=observation,
                IdStatement=None,
                FinancialEntityName=self.fin_entity_name,
            )
            return transfer_scraped
        except Exception as _e:
            transf_str = self._transf_str(transfer_parsed)
            self.logger.error("{}: {}: can't generate scraped transfer pdf: EXCEPTION\n{}".format(
                account_scraped.FinancialEntityAccountId,
                transf_str,
                traceback.format_exc()
            ))
            return None

    def _transf_str(self, transfer_scraped: TransferParsed):
        return "({}/{})".format(transfer_scraped['amount'],
                                transfer_scraped['operation_date'])

    def main(self) -> MainResult:
        session, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )
        if self.transfers_filters_navigation_movements:
            companies = self.get_companies(session, resp_logged_in)
            self.logger.info('Got companies (contracts): {}'.format(companies))

            # need to open each company from unique session to avoid collisions
            is_need_new_session_for_each_company_processing = len(companies) > 1

            # can process companies (get accounts_scraped) using one session
            if project_settings.IS_CONCURRENT_SCRAPING and companies:
                with futures.ThreadPoolExecutor(MAX_CONCURRENT_WORKERS) as executor:
                    futures_dict = {
                        executor.submit(self.process_company,
                                        session, company,
                                        is_need_new_session_for_each_company_processing): company.title
                        for company in companies
                    }
                    self.logger.log_futures_exc('process_company', futures_dict)
            else:
                for company in companies:
                    self.process_company(session, company, is_need_new_session_for_each_company_processing)

        if self.transfers_filters_navigation_transfers:
            transfers_companies = self.get_transfers_companies(session, resp_logged_in)
            self.logger.info('Got transfers companies (contracts): {}'.format(transfers_companies))

            # need to open each company from unique session to avoid collisions
            is_need_new_session_for_each_company_processing = len(transfers_companies) > 1

            # can process companies (get accounts_scraped) using one session
            if project_settings.IS_CONCURRENT_SCRAPING and transfers_companies:
                with futures.ThreadPoolExecutor(MAX_CONCURRENT_WORKERS) as executor:
                    futures_dict = {
                        executor.submit(self.process_transfers_company,
                                        session, company,
                                        is_need_new_session_for_each_company_processing): company.title
                        for company in transfers_companies
                    }
                    self.logger.log_futures_exc('process_company', futures_dict)
            else:
                for company in transfers_companies:
                    self.process_transfers_company(session, company, is_need_new_session_for_each_company_processing)

        self.basic_log_time_spent('GET TRANSFERS')
        return self.basic_result_success()
