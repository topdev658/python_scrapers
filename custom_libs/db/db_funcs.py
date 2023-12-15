"""
ALL get/select/should/check functions should return values.
ALL add/update/set/delete functions should return None as they don't provide real DB results.
"""

import datetime
import random
import re
import time
import uuid
from typing import Any, List, Optional, Tuple, Sequence, Callable, NewType, Union

import pyodbc
from deprecated import deprecated

from custom_libs import date_funcs
from custom_libs import extract
from custom_libs import str_funcs
from custom_libs.db import queue_simple
from custom_libs.log import log, log_err
from custom_libs.scrape_logger import ScrapeLogger
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    AccountSavedWithTempBalance, AccountScraped, CheckScraped, DBAccount, DBCustomer,
    DBCustomerToUpdateState, DBFinancialEntityAccess, DBFinancialEntityAccessThirdLoginPass,
    DBFinancialEntityAccessToUpdateState, DBFinancialEntityAccessWithCodesToUpdateState,
    DBOrganization, CorrespondenceDocScraped, DocumentTextInfo, MovementScraped, CheckCollectionScraped,
    LeasingContractScraped, LeasingFeeScraped, CorrespondenceDocChecked,
    DBTransferFilter, TransferScraped, DBTransferAccountConfig, DBMovementConsideredTransfer,
    DBCustomerForN43, DBFinancialEntityAccessForN43, DBTransfer, DBMovementByTransfer,
    GroupOfTransfersNotLinkedMultipleMovs, MovementTPV, AccountToDownloadCorrespondence,
    POSTradePoint, POSCollection, ResultCode, PDF_UNKNOWN_ACCOUNT_NO
)

__version__ = '26.30.0'

__changelog__ = """

26.30.0 2023.10.04
delete_leasing_contract_and_fees: added to delete leasing contract and its fees from 
db before inserting just scraped contract and fees
get_movement_initial_id_from_leasing_fee_data: allow to assign initial_id to leasing fee even if it is already assigned
due to deletion of old leasing fees has been added befor inserting already scraped.
26.29.0 2023.08.18
AccessFuncs: added get_all_receipts_customer_financial_entity_accesses_ids to get 
all customer_financial_entity_access_id with receipts download configure
26.28.0 2023.08.02
add_or_update_leasing_contract: managed null CurrentInterest in LeasingContracts
add_or_update_leasing_fee: fixed PendingRepayment in LeasingFees
26.27.0 2023.07.31 
get_deactivate_2fa: new method to get deactivate2FA field from access
26.26.0 2023.07.28
add_or_update_leasing_contract: added parameters to update {InitialInterestParams}, {UpdateContractAccountParams}
add_or_update_leasing_fee: fixed InsuranceAmount, PendingRepayment
26.25.0 2023.06.26
get_movement_data_from_keyvalue:
    refactored fin_ent_account_id_suffix to fin_ent_account_id
    query moved into a SP (lportal.dbo.SP_PY_GetMovementInitialIdFromKeyvalue)
26.24.0 2023.06.13
get_accounts_to_skip_download_correspondence: new method to get accounts to skip correspondence download
add_accounts_and_organiz_or_update: set default value scrapeAccountCorrespondence on account insertion
26.23.0 2023.06.13
add_correspondence_doc: added AccessId on the pdfs insertion 
26.22.0 2023.06.01
add_correspondence_doc: added AccountId on the correspondence pdf insertion
26.21.0 2023.05.30
should_download_receipt_doc: modified type of return value to bool
get_account_id: new method to get account_id by SP_PY_GetAccountId
MOVEMENT_SELECT_FIELDS: added fields 'Receipt' and 'ReceiptChecksum'
add_new_movements: added fields 'Receipt' and 'ReceiptChecksum' on insertion of new movements
add_correspondence_doc: modified check into insertion, when PDF is linked to movement
26.20.0 2023.05.26
add_accounts_and_organiz_or_update, update_acc_set_mov_scrap_fin: removed insertion to table
    _TesoraliaAccountsHistoricalBalances because table is not used
26.19.0 2023.05.09
add_correspondence_doc: upd Receipt and ReceiptChecksum fields if StatementId is linked to doc
get_movement_initial_ids_from_document_info: 
    refactored query to avoid linking correspondence PDFs to movs that already have PDF linked
upd deprecation marks
26.18.0 2023.04.27
add_correspondence_doc: insert NULL OrganizationId at _TesoraliaDocuments if parameter is None,
escaped quote for DocumentType
26.17.0 2023.04.27
should_download_receipt_doc: new method to check if the movement already has a linked PDF into DB
check_add_correspondence_doc: query moved into a SP (lportal.dbo.SP_PY_CheckSavedPDFChecksum)
deleted deprecated methods
26.16.0
add_or_update_leasing_fee: fixed NULL values for State and InvoiceNumber
26.15.0
add_or_update_leasing_contract: added UpdateTimeStamp and ResidualValue management
add_leasing_fee: added InvoiceNumber
new add_or_update_leasing_fee
save_or_update_leasing_contract_transactional: 
    call to add_or_update_leasing_fee instead of (delete_leasing_fee + add_leasing_fee)
26.14.0
get_movement_data_from_keyvalue: upd query 
    customer_id added to get right account information
26.13.0
check_add_correspondence_doc: changed 'UNKNOWN' string to PDF_UNKNOWN_ACCOUNT_NO
26.12.0
get_financial_entity_access_date_to_offset at AccessFuncs
26.11.0
get_accounts_to_download_correspondence: check also Active and Freeze
26.10.0
check Freeze is null:
    check_account_is_active
    get_accounts_temp_balances
    set_accounts_scraping_in_progress
    update_accounts_scraping_attempt_timestamp
    rollback_ts_and_balances
    set_accounts_possible_inactive_and_upd_attempt_ts
    add_accounts_and_organiz_or_update
    get_active_transfers_accounts
26.9.0
get_fin_ent_accesses_to_scrape with more logging
get_fin_ent_accesses_all_customers_scraping with more logging
26.8.0
get_accounts: optional arg db_organization
get_organization: added 1st step strict comparizon by name (were only fuzzy comparizons) 
26.7.0
set_receipt_info: don't save StatementReceiptDescription
deleted deprecated func set_receipt_description
26.6.0
check_add_correspondence_doc, add_correspondence_doc: 
    filter also by CustomerId allowing duplicates for different customers
26.5.0
add_correspondence_doc: check in transaction for existing docs before insertion
26.4.0
check_add_correspondence_doc:
 upd product_id_for_query
 query: more checks to find already inserted doc  
26.3.0
set_receipt_info: Document field support (has_related_entry_in_doc_table param)
26.2.0
get_movement_data_from_keyvalue: allow fin_ent_account_id_suffix instead of fin_ent_account_id
get_movement_initial_ids_from_document_info: allow duplicates from receipts and mailbox
26.1.0
get_all_user_ids_for_mt940
get_fin_ent_access_ids_to_scrape_for_mt940
get_mt940_last_date_and_account_status
26.0.0
MT940Funcs
25.10.0
add_accounts_and_organiz_or_update: added fin_entity_id param
25.9.0
update_acc_set_mov_scrap_fin: WRN_.. result also updates LastSuccessDownload 
25.8.0
add_transfer: replace quote with blank for Description, for AccountOrder, Concept, Reference y Observation
25.7.0
update_related_account_info
25.6.0
add_accounts_and_organiz_or_update: use source_channel
25.5.0
update_acc_set_mov_scrap_fin: use result_codes
set_accounts_possible_inactive -> set_accounts_possible_inactive_and_upd_attempt_ts
25.4.0
_TesoraliaPOSFinancialCollections.RegisterDate: was UTC now local
_TesoraliaPOSFinancialCollectionsStatements.fechaRegistro: was UTC now local
_TesoraliaPOSFinancialCollectionsAccess.UpdateTimeStamp: was UTC now local
_TesoraliaPOSFinancialIdComercio.FechaDescarga: was UTC now local
25.3.0
update_pos_access_ts
25.2.0
POSTradePoint
  DownloadTimeStamp (added in the type) is FechaDescarga
  LastDownloadedOperationalDate is FechaUltimaDescargaCorrecta (added in DB)
25.1.0
update_acc_set_mov_scrap_fin: LastSuccessDownload field support 
25.0.0
POSFuncs
24.12.0
get_organization: use unescaped organization_title
24.11.1
get_one_movement_before_date: convert date to db format (avoid corner cases)
24.11.0
add_log_to_accesos_log: removed temp 'Server' field for PRE 
24.10.0
restored should_download_correspondence (for transitional period)
24.9.0
should_download_correspondence_and_generic
get_accounts_to_download_correspondence
24.8.3
add_new_movements_tpv: escape quotes
24.8.2
get_fin_ent_accesses_to_scrape_for_n43: TempFolder convert from 0/1 to bool
24.8.1
get_fin_ent_accesses_to_scrape_for_n43: set TempFolder=True if the field is not provided by DB SP
24.8.0
get_fin_ent_accesses_to_scrape_for_n43: TempFolder field support
get_fin_ent_access_for_n43
24.7.0
get_fin_ent_accesses_to_scrape: LastSuccessDownload field support
24.6.0 
get_fin_ent_accesses_to_scrape_for_n43: explict fields for DBFinancialEntityAccessForN43 creation 
 to allow more fields to be returned from SP   
24.5.0
get_n43_last_successful_result_date_of_access: now uses accesos_Log table
DBLoggerFuncs class as a namespace 
upd deprecation marks
removed old changelog msgs
24.4.1
add_log_to_accesos_log: escape quotes in exc_str
_db_execute_query_loop: interrupt attempts on syntax errs
24.4.0
add_log_to_accesos_log: optional customer, optional status
24.3.0
_str_or_null_for_db
add_log_to_accesos_log: more params
24.2.0
add_transfer: escape quotes in Description
24.1.0
AccountFuncs: get_account_custom_offset
24.0.0
MovementTPVFuncs
23.2.1
get_transfers_w_operational_date_in_range: fixed typing
23.2.0
get_transfers_w_operational_date_in_range
get_transfers_w_statement_id_null: extracted get_db_transfer_from_db_row
23.1.1
get_movements_by_transfer_by_value_date, get_movements_by_transfer_by_operational_date:
    added check to avoid link a transfer to an already used IdStatement 
23.1.0
set_transfer_statement_id: used exec stmt to call SP instead sql stmt 
get_transfers_not_linked_due_to_multiple_statements_by_value_date: used exec stmt to call SP instead sql stmt
add_transfer:
    added temp balance
    added query to error log
delete_duplicated_transfers_by_value_date
delete_duplicated_transfers_by_operational_date
get_movements_by_transfer_by_value_date
get_movements_by_transfer_by_operational_date
get_db_transfer_from_db_row: temp_balance
correct checks for optional transfer.TempBalance
23.0.1
set_transfer_statement_id: sql stmt instead of SP due to absent SP at PROD
23.0.0
all sql statements (queries) from TransfersLinker
correct get_db_transfer_from_db_row
22.6.1
get_n43_last_date_and_account_status: upd type hints, convert to expected types
22.6.0
get_all_fin_ent_accesses_to_scrape_for_transfers
21.5.0
N43Funcs.get_n43_last_date_and_account_status
21.4.0
db funcs for N43 nightly processing: 
  get_all_users_for_n43, get_fin_ent_accesses_to_scrape_for_n43 
21.3.0
get_accounts_temp_balances: get Active field to use in _rollback_accounts
21.2.0
add_correspondence_doc: file_extension
21.1.0
get_active_transfers_accounts:
  use custom query with LastScrapedTransfersTimeStampWithOffset field
add_transfer:
  FinancialEntityName param (was FinancialEntityId) 
get_movs_considered_transfers:
  moved here, upd query: filter by AccountId 
  (earlier SP 'GetStatements_BBVA_0391_0591' has been used with only cusomer-level filter)
21.0.0
get_active_transfers_accounts
get_active_transfers_filters
add_transfer
update_last_scraped_transfers_time_stamp
save_transfers_transactional
add_log_to_accesos_log
20.1.1
should_download_correspondence: upd query (more correct)
20.1.0
access-level should_download_correspondence
20.0.1
upd log msg
20.0.0
DocumentFuncs: renamed CorrespondenceDocParsed, CorrespondenceDocScraped and appropriate methods
19.0.1
get_user__call_from_web_service: use updated _execute_query
19.0.0
N43Funcs
18.6.0
correspondence: currency field support
18.5.0
check_account_is_active;
get_accounts_temp_balances
  rollback_ts_and_balances
  add_accounts_and_organiz_or_update: update_inactive_accounts params
18.4.0
get_organization: use fuzzy_equal
18.3.0
check_add_document: product_id_for_query len restrictions for converting
18.2.0
removed get_movement_initial_id_from_document_info (could give false positive matches), 
  use get_movement_initial_ids_from_document_info instead
add_document: use strict data struct for fields, use datetime
18.1.0
check_add_document: empty ProductId support
18.0.0
ExportTimeStamp field support
_db_execute_query_loop: ErrMsg instead of Exception to prevent hanging queue
add_new_movements: guarantee post-add actions (even after an exception, then re-raise it) to avoid unreleased MovementInsertMutex
deleted old changelog
"""

MOVEMENT_SELECT_FIELDS = ("Id, Amount, TempBalance, OperationalDate, ValueDate, StatementDescription, "
                          "OperationalDatePosition, KeyValue, CreateTimeStamp, InitialId, ExportTimeStamp, Receipt, "
                          "ReceiptChecksum")

# https://stackoverflow.com/questions/3783238/python-database-connection-close#3783305
# https://groups.google.com/forum/#!topic/pyodbc/Mg6rFPb4gw8
# pyodbc.pooling = False

ErrMsg = NewType('ErrMsg', str)


# Use this instead of global 'conn' from server_for_scraping (due to it is multithreaded)
def new_conn() -> pyodbc.Connection:
    return pyodbc.connect(project_settings.DB_CONN_STR)


# Suitable only for serial db requests
# (if project.settings.DB_QUEUE_CONCURRENT_WORKERS == 1)
# Helps to avoid segfaults raised in libodbc when
# the app creates 2 (or more) connections from same thread
# (it happens from futures with ThreadPoolExecutor)
# Global connection
conn = new_conn()


def _split_list(l: List[Any], n: int) -> List[List[Any]]:
    """Split list to lists by number of items per batch"""
    ll = []  # type: List[List[Any]]
    while True:
        if len(l) > n:
            ll.append(l[:n])
            l = l[n:]
        else:
            ll.append(l)
            break
    return ll


def _str_or_null_for_db(val: Union[None, str, int, float]) -> str:
    val_escaped = extract.escape_quote_for_db(val) if isinstance(val, str) else val
    return 'NULL' if val is None else "'{}'".format(val_escaped)


# Just returns module-global connection since 9.8.0 (to use from futures)
def get_conn() -> pyodbc.Connection:
    return conn


def _db_execute_query_loop(cursor: pyodbc.Cursor, q: str) -> Tuple[pyodbc.Cursor, Optional[ErrMsg]]:
    """
    Raise exception only if
        Incorrect syntax
    else retry
    """
    global conn

    def random_sleep(k: int):
        time.sleep(k * random.random())

    def query_part(query: str, letters_cnt: int):
        return re.sub(r'\s+', ' ', query[:letters_cnt]).strip()

    i = 0
    while True:
        try:
            cursor.execute(q)
            # cursor.commit()
            break
        # Can't re-raise exc here to prevent
        # hanging queue => return critical ErrMsg to
        # raise after the queue returned the err.
        except Exception as exc:
            i += 1
            exc_str = str(exc)
            if i > 50:
                err_msg = ('_db_execute_query_loop: TOO MANY ATTEMPTS #{} to handle EXCEPTION: '
                           '{}:\n. QUERY:\n{}'.format(i, exc, q[:100]))
                return cursor, ErrMsg(err_msg)

            # 40001 deadlock error
            # 42000 access error (?); also syntax error, convertation err (handled above)
            # 08S01 communication link failure
            # HY000 connection is busy
            # [07005] [Microsoft][ODBC Driver 13 for SQL Server]Prepared statement is not a cursor-specification
            if '[07005]' in exc_str:
                # try create new cursor
                log('_db_execute_query_loop: HANDLED EXCEPTION: {}. '
                    'RETRY with new cursor #{}. QUERY: {}...'.format(exc, i, query_part(q, 30)))
                del cursor
                random_sleep(i)
                cursor = conn.cursor()
                continue
            elif '[40001]' in exc_str:
                log('_db_execute_query_loop: HANDLED EXCEPTION: {}. '
                    'RETRY on deadlock #{}. QUERY: {}...'.format(exc, i, q[:100]))
                random_sleep(i)
                continue
            elif '[42000]' in exc_str and '[SQL Server]Sintaxis incorrecta' not in exc_str:
                log('_db_execute_query_loop: HANDLED EXCEPTION: {}. '
                    'RETRY on conn error #{}. QUERY: {}...'.format(exc, i, q[:100]))
                del cursor
                cursor = conn.cursor()
                random_sleep(i)
                continue
            elif '[08S01]' in exc_str:
                log('_db_execute_query_loop: HANDLED EXCEPTION: {}. '
                    'RETRY on communication link failure #{}. QUERY: {}...'.format(exc, i, q[:100]))
                del cursor
                del conn
                conn = new_conn()  # renew global conn
                cursor = conn.cursor()
                random_sleep(i)
                continue
            elif '[HY0' in exc_str or 'HY000' in exc_str:
                log('_db_execute_query_loop: HANDLED EXCEPTION: {}. '
                    'RETRY on busy connection #{}. QUERY: {}...'.format(exc, i, query_part(q, 30)))
                random_sleep(i)
                continue
            else:
                # [SQL Server]Sintaxis incorrecta'
                # [SQL Server]Error al convertir'
                # [SQL Server]El nombre de columna
                # ...
                err_msg = '_db_execute_query_loop: EXCEPTION: {}:\n. QUERY:\n{}'.format(exc, q)
                return cursor, ErrMsg(err_msg)

    return cursor, None


def _fetch_data(cursor: pyodbc.Cursor, return_fields: Sequence) -> List[dict]:
    """
    Check pyodbc.ProgrammingError as exc (appear if cursor.fetchall() of query w/o results)
        text 'Previous SQL was not a query' means the exception is not error, just it was not SELECT query ->
            return empty res
    or raise if unknown error (will be logged in caller)
    """
    result = []  # type: List[dict]
    i = 0
    while True:
        try:
            if return_fields:
                result = [
                    {c[0]: v
                     for (c, v) in zip(row.cursor_description, row)
                     if c[0] in return_fields}
                    for row in cursor.fetchall()
                ]
            else:
                result = [{c[0]: v for (c, v) in zip(row.cursor_description, row)}
                          for row in cursor.fetchall()]
            break
        except Exception as exc:
            i += 1
            exc_str = str(exc)
            if i > 50:
                msg = '_fetch_data: TOO MANY ATTEMPTS #{} to handle EXCEPTION: {}'.format(i, exc)
                log_err(msg)
                raise Exception(msg)

            if '[40001]' in exc_str or '[HY0' in exc_str or 'HY000' in exc_str:
                log('_fetch_data: HANDLED EXCEPTION: {}. RETRY #{} on deadlock/busy connection'.format(exc_str, i))
                time.sleep(random.random())
                continue
            if 'No results.  Previous SQL was not a query' in exc_str:
                break
            raise exc
    return result


def _execute_query(q: str, return_fields: Sequence = (), connection=None) -> Tuple[List[dict], Optional[ErrMsg]]:
    """query caller
     formerly `process_query` functions
     that was used without celery"""
    if not connection:
        connection = get_conn()

    with connection as conn:
        cursor, err_msg = _db_execute_query_loop(conn.cursor(), q)
        if err_msg:
            return [], err_msg
        result = _fetch_data(cursor, return_fields)
        # del cursor
    return result, None


def _process_query_queue_simple(q: str, return_fields: Sequence = ()) -> List[dict]:
    query_id = queue_simple.add(_execute_query, q, return_fields)
    while True:
        if not queue_simple.ready(query_id):
            time.sleep(0.05)
            continue
        result, err_msg = queue_simple.get(query_id)
        if err_msg:
            # CRITICAL error, can't continue if got
            # DB error here
            raise Exception(err_msg)
        return result


def process_query(q: str, return_fields: Sequence = ()) -> List[dict]:
    """Replaced common `process_query`
    Now with queue support"""
    return _process_query_queue_simple(q, return_fields)


class UserFuncs:
    @staticmethod
    def get_all_users_scraping_not_in_progress() -> List[DBCustomer]:

        # q = ('EXEC dbo.CustomerByIdAndScrapingInProgress @CustomerId=Null, '
        #      '@ScrapingInProgress=False')
        q = """
        -- get_all_users_scraping_not_in_progress
        
        EXEC dbo.ActiveCustomersForNightlyBatch
        """
        result = process_query(q)
        users = []
        for row_dict in result:
            users.append(DBCustomer(**row_dict))
        return users

    @staticmethod
    def get_all_users_for_n43() -> List[DBCustomerForN43]:
        q = """
        -- get_all_users_for_n43
        
        ActiveCustomersForNightlyBatch_N43
        """
        result = process_query(q)
        users = []  # type: List[DBCustomerForN43]
        for row_dict in result:
            users.append(DBCustomerForN43(**row_dict))
        return users

    @staticmethod
    def get_all_user_ids_for_mt940() -> List[int]:
        q = """
        -- get_all_user_ids_for_mt940
        
        ActiveCustomersForNightlyBatch_MT940
        """
        results = process_query(q)
        user_ids = [u['Id'] for u in results]  # type: List[int]
        return user_ids

    @staticmethod
    def get_user_scraping_not_in_progress(customer_id: int) -> Optional[DBCustomer]:

        q = """
        -- get_user_scraping_not_in_progress for customer {customer_id}
        
        EXEC dbo.CustomerByIdAndScrapingInProgress @CustomerId={customer_id}, @ScrapingInProgress=False
        """.format(customer_id=customer_id)
        # params = ('Id', 'Name')
        result = process_query(q)
        if result:
            return DBCustomer(**result[0])
        return None  # to pass mypy checkups silently

    @staticmethod
    def get_user(customer_id: int) -> Optional[DBCustomer]:

        q = """
        -- get_user for customer {customer_id}
        
        EXEC dbo.Customer @CustomerId = {customer_id}
        """.format(customer_id=customer_id)
        # params = ('Id', 'Name')
        result = process_query(q)
        if result:
            return DBCustomer(**result[0])
        return None

    @staticmethod
    def get_user__call_from_web_service(customer_id: int) -> Optional[DBCustomer]:
        """Should be used to call from sever_for_scraping ONLY
        It doesn't use queue
        and it creates new connection for each query
        (due to gunicorn multithreading)
        """
        connection = new_conn()
        q = """
        -- get_user__call_from_web_service for customer {customer_id}
        
        EXEC dbo.Customer @CustomerId = {customer_id}
        """.format(customer_id=customer_id)
        # params = ('Id', 'Name')
        result, err = _execute_query(q, (), connection)
        if err:
            log_err(err, is_sentry=True)
        connection.close()
        del connection
        if result:
            return DBCustomer(**result[0])
        return None

    @staticmethod
    def get_user_for_status_reset(customer_id: int) -> Optional[DBCustomerToUpdateState]:
        q = """
        -- get_user_for_status_reset for customer {Id}
        
        SELECT 
            LiferayId as Id,
            ScrapingInProgress,
            LastScrapingStartedTimeStamp as ScrapingStartedTimeStamp,
            LastScrapingFinishedTimeStamp as ScrapingFinishedTimeStamp
        FROM 
            dbo._TesoraliaCustomers
        WHERE
            LiferayId = {Id}
        """.format(Id=customer_id)

        result = process_query(q)
        if result:
            return DBCustomerToUpdateState(**result[0])
        return None

    @staticmethod
    def get_users_by_timing_for_status_reset(time_threshold: str) -> List[DBCustomerToUpdateState]:
        q = """
        -- get_users_by_timing_for_status_reset for threshold {time_threshold}
        
        SELECT 
            LiferayId as Id,
            ScrapingInProgress,
            LastScrapingStartedTimeStamp as ScrapingStartedTimeStamp,
            LastScrapingFinishedTimeStamp as ScrapingFinishedTimeStamp
        FROM 
            dbo._TesoraliaCustomers
        WHERE
            ScrapingInProgress = 1
            AND LastScrapingStartedTimeStamp < '{time_threshold}'
        """.format(time_threshold=time_threshold)

        result = process_query(q)
        if result:
            return [DBCustomerToUpdateState(**row) for row in result]
        return []

    @staticmethod
    def update_user_scraping_state(user_to_update: DBCustomerToUpdateState):
        """
        Use stored procedures to save history

        :param user_to_update.ScrapingFinishedTimeStamp = now_for_db OR None
        """

        user_to_update_dict = user_to_update._asdict()
        # add quotes if exists
        if user_to_update.ScrapingFinishedTimeStamp:
            user_to_update_dict['ScrapingFinishedTimeStampForDB'] = "'{}'".format(
                user_to_update.ScrapingFinishedTimeStamp)
        else:
            user_to_update_dict['ScrapingFinishedTimeStampForDB'] = "Null"

        q = """
            -- update_user_scraping_state for customer {Id}
        
            DECLARE @Customers as CustomersUpdate;
            INSERT INTO @Customers (
                Id,
                ScrapingInProgress,
                ScrapingStartedTimeStamp,
                ScrapingFinishedTimeStamp
            )
            SELECT
                {Id},
                {ScrapingInProgress},
                '{ScrapingStartedTimeStamp}',
                {ScrapingFinishedTimeStampForDB};

            EXEC dbo.CustomerScrapingStateUpdate @CUS = @Customers;
            """.format(**user_to_update_dict)
        result = process_query(q)

        return True


class FinEntFuncs:
    @staticmethod
    def get_fin_ent_accesses_to_scrape(
            logger: ScrapeLogger,
            db_customer_id: int) -> List[DBFinancialEntityAccess]:
        """
        IF COMMENTED below, the scraping state of fin entity is not used as filter because
        it is checked at customer level (customer filtered by state)
        and if fin ent hanged (and still scraping_in_progress=True), this approach will allow
        to rescrape fin_entity
        IF NOT COMMENTED - check the scraping state in any case at this level too
        """

        assert type(db_customer_id) == int

        q = """
        -- get_fin_ent_accesses_to_scrape for customer {db_customer_id}
        
        EXEC dbo.CustomerFinancialEntityAccessWithCodeByCustomerId @CustomerId = {db_customer_id}
        """.format(db_customer_id=db_customer_id)

        result = process_query(q)
        accesses = []
        for row_dict in result:
            access = DBFinancialEntityAccess(**row_dict)
            if access.FinancialEntityId in project_settings.FINANCIAL_ENTITIES_TO_SCRAPE:
                # scraping in progress -> skip
                # todo IMPORTANT - comment next line to rescrape finEntAcc with hanged scrapings
                if access.ScrapingInProgress:
                    logger.info(
                        "get_fin_ent_accesses_to_scrape: access {}: "
                        "scraping in progress since {}. Skip".format(
                            access.Id,
                            access.LastScrapingStartedTimeStamp,
                    ))
                    continue
                # last successful scraping less than 30 mins ago -> skip
                if access.LastResponseTesoraliaCode == result_codes.SUCCESS.code:
                    if not date_funcs.is_enough_time_interval(
                            access.LastScrapingFinishedTimeStamp,
                            project_settings.NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT):
                        logger.info(
                            "get_fin_ent_accesses_to_scrape: access {}: "
                            "delay after previous successful result at {}. Skip".format(
                                access.Id,
                                access.LastScrapingFinishedTimeStamp,
                            )
                        )
                        continue
                # last unsuccessful scraping (or empty code) less than 5 mins ago -> skip
                if access.LastResponseTesoraliaCode != result_codes.SUCCESS.code:
                    if not date_funcs.is_enough_time_interval(
                            access.LastScrapingFinishedTimeStamp,
                            project_settings.NECESSARY_INTERVAL_BTW_FAILED_SCRAP_OF_FIN_ENT):
                        logger.info(
                            "get_fin_ent_accesses_to_scrape: access {}: "
                            "delay after previous failed result at {}. Skip".format(
                                access.Id,
                                access.LastScrapingFinishedTimeStamp,
                            )
                        )
                        continue

                accesses.append(access)
        return accesses

    @staticmethod
    def get_fin_ent_accesses_to_scrape_for_n43(db_customer_id: int) -> List[DBFinancialEntityAccessForN43]:
        assert type(db_customer_id) == int
        q = """
        -- get_fin_ent_accesses_to_scrape_for_n43 for customer {db_customer_id}
        
        CustomerFinancialEntityAccessWithCodeByCustomerId_N43 @CustomerId = {db_customer_id}
        """.format(db_customer_id=db_customer_id)

        result = process_query(q)
        accesses = []  # type: List[DBFinancialEntityAccessForN43]
        for row_dict in result:
            access = DBFinancialEntityAccessForN43(
                Id=row_dict['Id'],
                AccessFirstLoginValue=row_dict['AccessFirstLoginValue'],
                AccessPasswordLoginValue=row_dict['AccessPasswordLoginValue'],
                AccessSecondLoginValue=row_dict['AccessSecondLoginValue'],
                CustomerId=row_dict['CustomerId'],
                FinancialEntityAccessFirstLoginLabel=row_dict['FinancialEntityAccessFirstLoginLabel'],
                FinancialEntityAccessId=row_dict['FinancialEntityAccessId'],
                FinancialEntityAccessName=row_dict['FinancialEntityAccessName'],
                FinancialEntityAccessPasswordLoginLabel=row_dict['FinancialEntityAccessPasswordLoginLabel'],
                FinancialEntityAccessSecondLoginLabel=row_dict['FinancialEntityAccessSecondLoginLabel'],
                FinancialEntityAccessUrl=row_dict['FinancialEntityAccessUrl'],
                FinancialEntityId=row_dict['FinancialEntityAccessUrl'],
                LastSuccessDownload=row_dict['LastSuccessDownload'],
                # If the field is not provided (backward compat), use TempFolder by default
                #   also converts 0 or 1 to bool
                TempFolder=bool(row_dict.get('TempFolder', True))
            )
            accesses.append(access)
        return accesses

    @staticmethod
    def get_fin_ent_access_ids_to_scrape_for_mt940(db_customer_id: int) -> List[int]:
        assert type(db_customer_id) == int
        q = """
        -- get_fin_ent_access_ids_to_scrape_for_mt940 for customer {db_customer_id}
        
        CustomerFinancialEntityAccessWithCodeByCustomerId_MT940 @CustomerId = {db_customer_id}
        """.format(db_customer_id=db_customer_id)
        results = process_query(q)
        access_ids = [a['Id'] for a in results]  # type: List[int]
        return access_ids

    @staticmethod
    def get_fin_ent_access_for_n43(db_customer_id: int, db_access_id: int) -> Optional[DBFinancialEntityAccessForN43]:
        """:returns DBFinancialEntityAccessForN43
            or None if the access is not supposed to be scraped for N43.
            None will be handled by calling code
        """
        accesses = [
            a for a in FinEntFuncs.get_fin_ent_accesses_to_scrape_for_n43(db_customer_id)
            if a.Id == db_access_id
        ]
        if accesses:
            return accesses[0]
        return None

    @staticmethod
    def get_all_fin_ent_accesses_to_scrape_for_transfers() -> List[int]:
        q = """
        -- get_all_fin_ent_accesses_to_scrape_for_transfers
        
        CustomerFinancialEntityAccessWithTransfersPython
        """

        result = process_query(q)
        access_ids = [row['CustomerFinancialEntityAccessId'] for row in result]  # type: List[int]
        return access_ids

    @staticmethod
    def get_all_fin_ent_accesses_to_scrape_for_tpv() -> List[int]:
        q = """
        -- get_all_fin_ent_accesses_to_scrape_for_tpv
        
        CustomerFinancialEntityAccessFromRedSysTPV
        """

        result = process_query(q)
        access_ids = [row['CustomerFinancialEntityAccess'] for row in result]  # type: List[int]
        return access_ids

    @staticmethod
    def get_fin_ent_accesses_all(db_customer_id: int) -> List[DBFinancialEntityAccess]:
        """
        The scraping state of fin entity is not used
        """

        assert type(db_customer_id) == int

        q = """
        -- get_fin_ent_accesses_all for customer {db_customer_id}
        
        EXEC dbo.CustomerFinancialEntityAccessPlusInactiveWithCodeByCustomerId 
        @CustomerId = {db_customer_id}
        """.format(db_customer_id=db_customer_id)

        result = process_query(q)
        accesses = []
        for row_dict in result:
            access = DBFinancialEntityAccess(**row_dict)
            if access.FinancialEntityId in project_settings.FINANCIAL_ENTITIES_TO_SCRAPE:
                accesses.append(access)
        return accesses

    @staticmethod
    def get_equal_access_ids_scraping_in_progress(fin_ent_access: DBFinancialEntityAccess) -> List[int]:
        """Finds other accesses with the same credentials where ScrapingInProgress==1 right now"""
        q = """
        -- get_equal_access_ids_scraping_in_progress for {Id} 
         
        SELECT accCli.accesosClienteId as accessId   
        FROM accesos_AccClientes as accCli
        INNER JOIN _TesoraliaCustomerFinancialEntityAccess as accEnt ON accCli.accesosClienteId = accEnt.LiferayId
        WHERE
            accCli.accessFirstLoginValue = '{AccessFirstLoginValue}' AND
            accCli.accessSecondLoginValue = '{AccessSecondLoginValue}' AND
            accCli.accessPasswordLoginValue = '{AccessPasswordLoginValue}' AND
            accCli.accesoId = {FinancialEntityAccessId} AND
            accEnt.ScrapingInProgress = 1
        """.format(
            Id=fin_ent_access.Id,
            AccessFirstLoginValue=fin_ent_access.AccessFirstLoginValue,
            AccessSecondLoginValue=fin_ent_access.AccessSecondLoginValue,
            AccessPasswordLoginValue=fin_ent_access.AccessPasswordLoginValue,
            FinancialEntityAccessId=fin_ent_access.FinancialEntityAccessId
        )
        result = process_query(q)
        access_ids = [row_dict['accessId'] for row_dict in result if row_dict['accessId'] != fin_ent_access.Id]
        return access_ids

    @staticmethod
    def get_fin_ent_accesses_all_customers_scraping(
            logger: ScrapeLogger,
            db_customer_id: int) -> List[DBFinancialEntityAccess]:
        """
        Filter accesses from get_financial_entity_accesses additionally
        by NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT_ALL_CUSTOMERS_SCRAPING
        to allow rescrape failed accesses several times per night
        and avoid rescrape successfully several times per night
        """

        now_time_hour = date_funcs.now_time_hour()

        accesses = FinEntFuncs.get_fin_ent_accesses_to_scrape(logger, db_customer_id)
        logger.info('got total {} accesses: {}'.format(len(accesses), [a.Id for a in accesses]))
        accesses_filtered = []  # type: List[DBFinancialEntityAccess]
        accesses_skipped = []  # type: List[DBFinancialEntityAccess]

        # green time tunnel? return all accesses to scrape without filtering by
        # NECESSARY_INTERVAL_BTW_SUCCESSFUL_SCRAP_OF_FIN_ENT_ALL_CUSTOMERS_SCRAPING
        if (project_settings.GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING[0]
                < now_time_hour
                < project_settings.GREEN_TIME_SCRAPING_TUNNEL_HRS_ALL_CUSTOMERS_SCRAPING[1]):
            logger.info('"green" time tunnel: scrape all accesses of the customer')
            return accesses

        for access in accesses:
            if access.LastResponseTesoraliaCode == result_codes.SUCCESS.code:
                if not date_funcs.is_enough_time_interval(
                        access.LastScrapingFinishedTimeStamp,
                        project_settings.NECES_INTER_BTW_SUCCESS_SCRAP_OF_FIN_ENT_ALL_CUST_SCRAP):
                    accesses_skipped.append(access)
                    continue

            accesses_filtered.append(access)
        if accesses_skipped:
            logger.warning(
                'out of "green" time tunnel: '
                'delay after previous "all customers" scraping process ({} hrs). '
                'Skip accesses: ids {}, details {}'.format(
                    project_settings.NECES_INTER_BTW_SUCCESS_SCRAP_OF_FIN_ENT_ALL_CUST_SCRAP / 3600,
                    [a.Id for a in accesses_skipped],
                    accesses_skipped
                )
            )
        return accesses_filtered

    @staticmethod
    def get_financial_entity_access(fin_ent_access_id: int) -> Optional[DBFinancialEntityAccess]:

        assert type(fin_ent_access_id) == int
        q = """
        -- get_financial_entity_access {fin_ent_access_id}
        
        EXEC dbo.CustomerFinancialEntityAccessWithCode 
        @CustomerFinancialEntityAccesId = {fin_ent_access_id}
        """.format(fin_ent_access_id=fin_ent_access_id)
        result = process_query(q)
        if result:
            return DBFinancialEntityAccess(**result[0])
        return None  # to pass mypy checkups silently

    @staticmethod
    def get_financial_entity_access_third_login_pass(
            fin_ent_access_id: int) -> Optional[DBFinancialEntityAccessThirdLoginPass]:
        q = """
        -- get_financial_entity_access_third_login_pass for access {fin_ent_access_id} 
        
        SELECT accessThirdLoginValue
               , accessPasswordThirdLoginValue 
        FROM accesos_AccClientes 
        WHERE accesosClienteId={fin_ent_access_id}
        """.format(fin_ent_access_id=fin_ent_access_id)
        result = process_query(q)
        if result:
            return DBFinancialEntityAccessThirdLoginPass(
                AccessThirdLoginValue=result[0]['accessThirdLoginValue'],
                AccessPasswordThirdLoginValue=result[0]['accessPasswordThirdLoginValue']
            )
        return None

    @staticmethod
    def get_financial_entity_reference_extractor(fin_ent_access_id: int) -> str:
        q = """
        -- get_financial_entity_reference_extractor for access {fin_ent_access_id}
        
        SELECT 'Recibos Cobros Domiciliados' AS [ref_type]
        FROM accesos_AccClientes 
        WHERE accesosClienteId={fin_ent_access_id}
        """.format(fin_ent_access_id=fin_ent_access_id)
        result = process_query(q)
        if result:
            return result[0]['ref_type']
        return ''

    @staticmethod
    def get_organization(db_customer_id: int,
                         organization_title: str) -> Optional[DBOrganization]:
        org_title_unescaped = extract.unescape(organization_title)
        q = """
        -- get_organizations to find {Name}
        
        SELECT Id, Name, NameOriginal
        FROM _TesoraliaOrganizations 
        WHERE 
            CustomerId = {CustomerId};
        """.format(
            CustomerId=db_customer_id,
            Name=extract.escape_quote_for_db(org_title_unescaped)
        )
        org_dicts = process_query(q)
        # Use 'fuzzy_equal' because often there are
        # organizations with different punctuation from different
        # menus (example: Santander 'Nuevo' for -a 22917 (EXEA) correspondence)
        for kind, stricter in [('equal', True), ('fuzzy', True), ('fuzzy', False)]:
            found = []  # type: List[dict]  # with org_dict
            for org_dict in org_dicts:
                if kind == 'equal' and org_dict['NameOriginal'] == org_title_unescaped:
                    found.append(org_dict)
                elif kind == 'fuzzy' and str_funcs.fuzzy_equal(org_dict['NameOriginal'], org_title_unescaped,
                                                               stricter=stricter):
                    found.append(org_dict)
                # Only one result means that we found correct organization,
                # 0 or >1 not allowed
                if len(found) == 1:
                    return DBOrganization(
                        Id=found[0]['Id'],
                        Name=found[0]['Name'],
                        NameOriginal=found[0]['NameOriginal']
                    )
        return None

    @staticmethod
    def set_fin_ent_access_inactive(user_id: int,
                                    fin_ent_access_id: int) -> None:
        """
        call it if not logged in due wrong username or password
        """
        assert type(user_id) == int
        assert type(fin_ent_access_id) == int
        q = """
        -- set_fin_ent_access_inactive for access {financial_entity_access_id}
        
        EXEC dbo.CustomerFinancialEntityAccessSetInactive @CustomerId = {user_id},
        @FinancialEntityAccessId = {financial_entity_access_id}
        """.format(user_id=user_id,
                   financial_entity_access_id=fin_ent_access_id)
        result = process_query(q)
        return

    @staticmethod
    def update_fin_ent_access_scrap_state(
            fin_ent_access_to_update: DBFinancialEntityAccessToUpdateState):
        """Use stored procedures to save history"""

        fin_entity_access_to_update_dict = fin_ent_access_to_update._asdict()
        # add quotes if exists
        if fin_ent_access_to_update.ScrapingFinishedTimeStamp:
            fin_entity_access_to_update_dict['ScrapingFinishedTimeStampForDB'] = "'{}'".format(
                fin_ent_access_to_update.ScrapingFinishedTimeStamp)
        else:
            fin_entity_access_to_update_dict['ScrapingFinishedTimeStampForDB'] = "Null"

        q = """
            -- update_fin_ent_access_scrap_state for access {Id}
        
            DECLARE @FinEntUpdate as CustomerFinancialEntityAccessUpdate;
            INSERT INTO @FinEntUpdate (
                Id,
                ScrapingInProgress,
                ScrapingStartedTimeStamp,
                ScrapingFinishedTimeStamp
            )
            SELECT
                {Id},
                {ScrapingInProgress},
                '{ScrapingStartedTimeStamp}',
                {ScrapingFinishedTimeStampForDB};

            EXEC dbo.CustomerFinancialEntityAccessScrapingStateUpdate @CUS = @FinEntUpdate;
            """.format(**fin_entity_access_to_update_dict)
        process_query(q)

        return True

    @staticmethod
    def update_fin_ent_access_scrap_state_with_codes(
            fin_ent_access_with_codes_to_update: DBFinancialEntityAccessWithCodesToUpdateState):
        """New function with response codes
        use stored procedures to save history
        """

        fin_entity_access_to_update_with_codes_dict = fin_ent_access_with_codes_to_update._asdict()

        # add quotes if exists
        if fin_ent_access_with_codes_to_update.ScrapingFinishedTimeStamp:
            fin_entity_access_to_update_with_codes_dict['ScrapingFinishedTimeStampForDB'] = "'{}'".format(
                fin_ent_access_with_codes_to_update.ScrapingFinishedTimeStamp)
        else:
            fin_entity_access_to_update_with_codes_dict['ScrapingFinishedTimeStampForDB'] = "Null"

        q = """
            -- update_fin_ent_access_scrap_state_with_codes for access {Id}
        
            DECLARE @FinEntUpdate as CustomerFinancialEntityAccessUpdate;
            INSERT INTO @FinEntUpdate (
                Id,
                ScrapingInProgress,
                ScrapingStartedTimeStamp,
                ScrapingFinishedTimeStamp,
                HttpStatusResponseCode,
                HttpStatusResponseDescription,
                ResponseTesoraliaCode,
                ResponseTesoraliaDescription
            )
            SELECT
                {Id},
                {ScrapingInProgress},
                '{ScrapingStartedTimeStamp}',
                {ScrapingFinishedTimeStampForDB},
                {HttpStatusResponseCode},
                '{HttpStatusResponseDescription}',
                {ResponseTesoraliaCode},
                '{ResponseTesoraliaDescription}';

            EXEC dbo.CustomerFinancialEntityAccessScrapingStateUpdate @CUS = @FinEntUpdate;
            """.format(**fin_entity_access_to_update_with_codes_dict)
        process_query(q)

        return True


class AccountFuncs:

    @staticmethod
    def set_movements_insert_mutex_if_not_locked_yet(
            fin_ent_account_id: str,
            db_customer_id: int,
            movements_insert_mutex: str) -> None:
        """Sets mutex only if the account has no active mutex"""

        q = """
            -- set_movements_insert_mutex {MovementsInsertMutex} for account {FinancialEntityAccountId} 
            UPDATE
                dbo._TesoraliaAccounts
            SET
                MovementsInsertMutex = '{MovementsInsertMutex}',
                MutexLockedTimeStamp = getutcdate()
            WHERE
                FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
                CustomerId = {CustomerId} AND
                -- locks ONLY FREE (not locked) accounts
                MovementsInsertMutex IS NULL;
            """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            MovementsInsertMutex=movements_insert_mutex
        )
        process_query(q)
        return

    @staticmethod
    def get_movements_insert_mutex(
            fin_ent_account_id: str,
            db_customer_id: int) -> Optional[str]:
        """
        Checks that the account has an active mutex in the DB
        :returns mutex val or None
        """

        q = """
        -- get_movements_insert_mutex for account {FinancialEntityAccountId}
        SELECT MovementsInsertMutex 
        FROM dbo._TesoraliaAccounts
        WHERE 
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
            CustomerId = {CustomerId}
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
        )
        result = process_query(q)
        if result:
            return result[0]['MovementsInsertMutex']
        # not found
        return None

    @staticmethod
    def release_movements_insert_mutex(
            fin_ent_account_id: str,
            db_customer_id: int,
            movements_insert_mutex: str) -> None:
        """Important: can release only exact movements_insert_mutex"""

        q = """
        -- release_movements_insert_mutex {MovementsInsertMutex} for account {FinancialEntityAccountId}

        UPDATE
            dbo._TesoraliaAccounts
        SET
            MovementsInsertMutex = NULL,
            MutexLockedTimeStamp = NULL
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
            CustomerId = {CustomerId} AND
            MovementsInsertMutex = '{MovementsInsertMutex}';
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            MovementsInsertMutex=movements_insert_mutex
        )

        process_query(q)
        return

    @staticmethod
    def check_and_release_movements_insert_mutex(
            fin_ent_account_id: str,
            db_customer_id: int,
            movs_insert_mutex: str):
        """Actions after movements has been inserted
        Must release the mutex any way (if possible),
        that's why there are extra try/except
        """

        # Should be the same, additional check
        movs_insert_mutex_in_db = AccountFuncs.get_movements_insert_mutex(
            fin_ent_account_id,
            db_customer_id,
        )

        err_msg = None  # type: Optional[str]
        if movs_insert_mutex_in_db != movs_insert_mutex:
            # Was locked by another mutex during the insertion, but it wouldn't happen at all.
            err_msg = (
                "can't release movements_insert_mutex {}, got another active UNEXPECTED MUTEX {}. "
                "It's a VERY CRITICAL ERROR that causes further BALANCE INTEGRITY ERROR. "
                "Check the code!!!".format(
                    movs_insert_mutex,
                    movs_insert_mutex_in_db
                )
            )
            return err_msg

        AccountFuncs.release_movements_insert_mutex(
            fin_ent_account_id,
            db_customer_id,
            movs_insert_mutex
        )

        return err_msg

    @staticmethod
    def get_accounts(fin_ent_access_id: int, db_organization: Optional[DBOrganization] = None) -> List[DBAccount]:
        org_filter = ' AND OrganizationId = {}'.format(db_organization.Id) if db_organization else ''
        org_title_for_comment = 'and org {}'.format(db_organization.Id) if db_organization else ''
        q = """
        -- get_accounts of access {CustomerFinancialEntityAccessId} {org_title_for_comment}

        SELECT 
            Id,
            Balance,
            FinancialEntityAccountId,
            UpdateTimeStamp,
            BalancesScrapingInProgress,
            MovementsScrapingInProgress,
            LastBalancesScrapingStartedTimeStamp,
            LastBalancesScrapingFinishedTimeStamp,
            LastMovementsScrapingStartedTimeStamp,
            LastMovementsScrapingFinishedTimeStamp,
            CustomerFinancialEntityAccessId,
            PossibleInactive
        FROM 
            dbo._TesoraliaAccounts
        WHERE
            CustomerFinancialEntityAccessId={CustomerFinancialEntityAccessId}
            {org_filter}
        """.format(
            CustomerFinancialEntityAccessId=fin_ent_access_id,
            org_title_for_comment=org_title_for_comment,
            org_filter=org_filter,
        )

        result = process_query(q)
        accounts = []  # type: List[DBAccount]
        if result:
            accounts = [DBAccount(**row_dict) for row_dict in result]
        return accounts

    @staticmethod
    def get_accounts_temp_balances(
            fin_ent_access_id: int,
            update_inactive_accounts: bool) -> List[AccountSavedWithTempBalance]:
        """Returns data
        Id,FinancialEntityAccountId,Balance,TempBalance
        1266,1062178065,87443.73000000000000000000,87443.73000000000000000000
        to use in BasicScraper._rollback_accounts()
        """

        # join accounts with the their last movements
        q = """
        -- get_accounts_temp_balances for access {CustomerFinancialEntityAccessId}
        WITH Accounts AS (
          -- temp table with all accounts of the access
          SELECT Id, FinancialEntityAccountId, Balance, Active
          FROM _TesoraliaAccounts
          WHERE 
            CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId}
            {filter_by_update_inactive}
        )

        SELECT Accounts.Id,
               Accounts.FinancialEntityAccountId,
               Accounts.Balance,
               _TesoraliaStatements.TempBalance,
               Accounts.Active
        FROM _TesoraliaStatements
        INNER JOIN Accounts ON _TesoraliaStatements.AccountId = Accounts.Id
        WHERE _TesoraliaStatements.Id in (
          -- last movement for each account of the access
          -- we use max(id) to detect the last movement
          SELECT max(_TesoraliaStatements.Id)
          FROM _TesoraliaStatements
          INNER JOIN Accounts ON _TesoraliaStatements.AccountId = Accounts.Id
          WHERE _TesoraliaStatements.AccountId in (SELECT Id FROM Accounts)
          GROUP BY Accounts.Id
        )
        """.format(
            CustomerFinancialEntityAccessId=fin_ent_access_id,
            filter_by_update_inactive='' if update_inactive_accounts else 'AND Active = 1 AND Freeze IS NULL',
        )
        result = process_query(q)

        accounts = []  # type: List[AccountSavedWithTempBalance]
        if result:
            accounts = [AccountSavedWithTempBalance(**row_dict) for row_dict in result]
        return accounts

    @staticmethod
    def check_account_is_active(db_customer_id: int, fin_ent_account_id: str) -> bool:
        """Some account are shared between different fin entities of the customer,
        that's why we filter by  db_customer_id
        """
        q = """
        -- get_account_is_active for {FinancialEntityAccountId}
        SELECT 
            Active,
            Freeze
        FROM
            dbo._TesoraliaAccounts
        WHERE 
            CustomerId = {CustomerId} AND
            FinancialEntityAccountId = '{FinancialEntityAccountId}'
        """.format(
            CustomerId=db_customer_id,
            FinancialEntityAccountId=fin_ent_account_id
        )
        res = process_query(q)
        if res:
            return bool(res[0]['Active']) and (res[0]['Freeze'] is None)
        # For new or absent accounts it's True
        return True

    @staticmethod
    def get_account_custom_offset(db_customer_id: int, fin_ent_account_id: str) -> Optional[int]:
        """Get optional custom offset of the account"""
        q = """
        -- get_account_custom_offset for {FinancialEntityAccountId}
        SELECT 
            CustomOffsetDays
        FROM
            dbo._TesoraliaAccounts
        WHERE 
            CustomerId = {CustomerId} AND
            FinancialEntityAccountId = '{FinancialEntityAccountId}'
        """.format(
            CustomerId=db_customer_id,
            FinancialEntityAccountId=fin_ent_account_id
        )
        res = process_query(q)
        if res:
            return res[0]['CustomOffsetDays']
        return None

    @staticmethod
    def set_accounts_scraping_in_progress(customer_financial_entity_access_id: int) -> None:

        now_for_db = date_funcs.now_for_db()

        q = """
        -- set_accounts_scraping_in_progress for access {CustomerFinancialEntityAccessId}

        UPDATE
          dbo._TesoraliaAccounts
        SET
          BalancesScrapingInProgress = 1,
          LastBalancesScrapingStartedTimeStamp = '{NowTimeStamp}'
        WHERE
          CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId}
          AND Active = 1 
          AND Freeze IS NULL
        """.format(
            CustomerFinancialEntityAccessId=customer_financial_entity_access_id,
            NowTimeStamp=now_for_db
        )

        process_query(q)
        return

    @staticmethod
    def update_accounts_scraping_attempt_timestamp(customer_financial_entity_access_id: int) -> None:

        now_for_db = date_funcs.now_for_db()

        q = """
        -- update_accounts_scraping_attempt_timestamp for access {CustomerFinancialEntityAccessId}

        UPDATE
          dbo._TesoraliaAccounts
        SET
          LastScrapingAttemptStartedTimeStamp = '{NowTimeStamp}'
        WHERE
          CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId}
          AND Active = 1
          AND Freeze IS NULL
        """.format(
            CustomerFinancialEntityAccessId=customer_financial_entity_access_id,
            NowTimeStamp=now_for_db
        )

        process_query(q)
        return

    @staticmethod
    def update_related_account_info(
            customer_financial_entity_access_id: int,
            fin_ent_account_id: str,
            related_account_info: str) -> None:

        q = """
            -- update_related_account_info for {FinancialEntityAccountId}
    
            UPDATE
              dbo._TesoraliaAccounts
            SET
              RelatedAccount = '{RelatedAccount}'
            WHERE
              CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId}
              AND FinancialEntityAccountId = '{FinancialEntityAccountId}'
            """.format(
            CustomerFinancialEntityAccessId=customer_financial_entity_access_id,
            FinancialEntityAccountId=fin_ent_account_id,
            RelatedAccount=related_account_info
        )

        process_query(q)
        return

    @staticmethod
    def rollback_ts_and_balances(fin_ent_access_id: int, accounts: List[DBAccount],
                                 update_inactive_accounts: bool) -> None:
        """Rollback accounts balances and timestamps using corresponding fields values"""

        dt_fmt = date_funcs.convert_dt_to_db_ts_str  # just a shorter alias
        q = '-- rollback_ts_and_balances for access {}'.format(fin_ent_access_id)
        for account in accounts:
            q += """
            UPDATE
              _TesoraliaAccounts
            SET
              Balance = {Balance},
              UpdateTimeStamp = '{UpdateTimeStamp}',
              BalancesScrapingInProgress = {BalancesScrapingInProgress},
              MovementsScrapingInProgress = {MovementsScrapingInProgress},
              LastBalancesScrapingStartedTimeStamp = '{LastBalancesScrapingStartedTimeStamp}',
              LastBalancesScrapingFinishedTimeStamp = '{LastBalancesScrapingFinishedTimeStamp}',
              LastMovementsScrapingStartedTimeStamp = '{LastMovementsScrapingStartedTimeStamp}',
              LastMovementsScrapingFinishedTimeStamp = '{LastMovementsScrapingFinishedTimeStamp}'
            WHERE
              CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId}
              {filter_by_update_inactive}
              AND Id = {Id};
            """.format(
                CustomerFinancialEntityAccessId=fin_ent_access_id,
                Id=account.Id,
                LastMovementsScrapingFinishedTimeStamp=dt_fmt(account.LastMovementsScrapingFinishedTimeStamp),
                LastMovementsScrapingStartedTimeStamp=dt_fmt(account.LastMovementsScrapingStartedTimeStamp),
                LastBalancesScrapingFinishedTimeStamp=dt_fmt(account.LastBalancesScrapingFinishedTimeStamp),
                LastBalancesScrapingStartedTimeStamp=dt_fmt(account.LastBalancesScrapingStartedTimeStamp),
                MovementsScrapingInProgress=int(account.MovementsScrapingInProgress),
                BalancesScrapingInProgress=int(account.BalancesScrapingInProgress),
                UpdateTimeStamp=dt_fmt(account.UpdateTimeStamp),
                Balance=float(account.Balance),
                filter_by_update_inactive='' if update_inactive_accounts else 'AND Active = 1 AND Freeze IS NULL',
            )
        if q:
            process_query(q)

        return

    @staticmethod
    def set_accounts_possible_inactive_and_upd_attempt_ts(fin_ent_accounts_ids: List[str],
                                                          db_customer_id: int, value: bool) -> None:

        """Since 2021-11-01: Updates only active accounts,
        also sets LastScrapingAttemptFinishedTimeStamp for active but 'possible inactive' accounts
        """

        if not fin_ent_accounts_ids:
            return

        now_for_db = date_funcs.now_for_db()

        where_query = str(tuple(fin_ent_accounts_ids))

        # remove trailing comma from "('20384222546000042687',)" (if one element only)
        if len(fin_ent_accounts_ids) == 1:
            where_query = where_query.replace(',', '')

        flag = int(value)

        q = """
        -- set_accounts_possible_inactive {flag} for accounts {where_query}

        UPDATE
          dbo._TesoraliaAccounts
        SET
          PossibleInactive = {flag},
          LastScrapingAttemptFinishedTimeStamp = '{NowTimeStamp}'
        WHERE
          FinancialEntityAccountId IN {where_query}
          AND Active = 1
          AND Freeze IS NULL
          AND CustomerId = {CustomerId}
        """.format(
            where_query=where_query,
            CustomerId=db_customer_id,
            flag=flag,
            NowTimeStamp=now_for_db
        )
        process_query(q)
        return

    @staticmethod
    def add_accounts_and_organiz_or_update(
            accounts: List[AccountScraped],
            customer_financial_entity_access_id: int,
            update_inactive_accounts: bool,
            source_channel: str,
            fin_entity_id: int) -> None:
        """
        Add if not exist or update if exists
        """

        now_for_db = date_funcs.now_for_db()

        for i, acc_batch in enumerate(_split_list(accounts, project_settings.ACCOUNTS_TO_UPLOAD_BATCH_SIZE)):

            q = """
            -- add_accounts_and_organiz_or_update #{} for access {}

            DECLARE @OrganizationId BIGINT;
            DECLARE @AccountId BIGINT; 
            """.format(i, customer_financial_entity_access_id)

            for account in acc_batch:
                q_params = account._asdict()
                q_params['OrganizationName'] = extract.escape_quote_for_db(q_params['OrganizationName'])
                q_params['SourceChannel'] = source_channel
                q_params['entidadId'] = fin_entity_id

                # TODO can get AccountID once
                q += """
                -- create organization if not exists or update scrape time
                IF NOT EXISTS 
                    (SELECT Id
                     FROM dbo._TesoraliaOrganizations  
                     WITH (NOLOCK)
                     WHERE
                        NameOriginal = '{OrganizationName}' AND
                        CustomerId = {CustomerId})
                BEGIN
                    INSERT INTO dbo._TesoraliaOrganizations (
                        Name,
                        NameOriginal,
                        ScrapeTime,
                        CustomerId,
                        CustomerFinancialEntityAccessId,
                        CreateTimeStamp,
                        LastUpdateTimeStamp,
                        DefaultOrganization,
                        Active
                    ) VALUES (
                        '{OrganizationName}',
                        '{OrganizationName}',
                        '{BalancesScrapingStartedTimeStamp}',
                        {CustomerId},
                        {CustomerFinancialEntityAccessId},
                        '{NowTimeStamp}',
                        '{NowTimeStamp}',
                        {IsDefaultOrganization},
                        {IsActiveOrganization}
                    )
                END
                ELSE
                BEGIN
                    UPDATE
                        dbo._TesoraliaOrganizations
                    SET
                        ScrapeTime = '{BalancesScrapingStartedTimeStamp}'
                    WHERE
                        NameOriginal = '{OrganizationName}' AND
                        CustomerId = {CustomerId}
                END;

                -- get organization id by name, customer, financial entity
                SELECT
                    @OrganizationId = Id
                FROM dbo._TesoraliaOrganizations
                WITH (NOLOCK)
                WHERE
                    NameOriginal = '{OrganizationName}' AND
                    CustomerId = {CustomerId};

                -- create or update account
                IF NOT EXISTS 
                    (SELECT Id
                     FROM dbo._TesoraliaAccounts
                     WITH (NOLOCK)
                     WHERE 
                        FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
                        CustomerId = {CustomerId})
                    BEGIN
                        INSERT INTO dbo._TesoraliaAccounts (
                            FinancialEntityAccountId,
                            AccountNo,
                            AccountNoFormat,
                            AccountNoCountry,
                            Type,
                            Currency,
                            Balance,
                            OrganizationId,
                            CustomerId,
                            BalancesScrapingInProgress,
                            MovementsScrapingInProgress,
                            LastBalancesScrapingStartedTimeStamp,
                            LastBalancesScrapingFinishedTimeStamp,
                            LastMovementsScrapingStartedTimeStamp,
                            CreditLimit,
                            CreditAvailable,
                            CreateTimeStamp,
                            Active,
                            CustomerFinancialEntityAccessId,
                            SourceChannel,
                            entidadId,
                            scrapeAccountCorrespondence
                        ) VALUES (
                            '{FinancialEntityAccountId}',
                            '{AccountNo}',
                            '{AccountNoFormat}',
                            '{AccountNoCountry}',
                            {Type},
                            '{Currency}',
                            {Balance},
                            @OrganizationId,
                            {CustomerId},
                            {BalancesScrapingInProgress},
                            {MovementsScrapingInProgress},
                            '{BalancesScrapingStartedTimeStamp}',
                            '{BalancesScrapingFinishedTimeStamp}',
                            '{MovementsScrapingStartedTimeStamp}',
                            0,
                            0,
                            '{NowTimeStamp}',
                            1,
                            {CustomerFinancialEntityAccessId},
                            '{SourceChannel}',
                            {entidadId},
                            0
                        )
                    END
                    ELSE
                    BEGIN
                        UPDATE
                            dbo._TesoraliaAccounts
                        SET
                            Balance = {Balance},
                            BalancesScrapingInProgress =  {BalancesScrapingInProgress},
                            MovementsScrapingInProgress = {MovementsScrapingInProgress},
                            LastBalancesScrapingStartedTimeStamp = '{BalancesScrapingStartedTimeStamp}',
                            LastBalancesScrapingFinishedTimeStamp = '{BalancesScrapingFinishedTimeStamp}',
                            LastMovementsScrapingStartedTimeStamp = '{MovementsScrapingStartedTimeStamp}',
                            CustomerFinancialEntityAccessId = {CustomerFinancialEntityAccessId},
                            UpdateTimeStamp = '{NowTimeStamp}'
                        WHERE
                            FinancialEntityAccountId = '{FinancialEntityAccountId}'
                            {filter_by_update_inactive}
                            AND CustomerId = {CustomerId};
                END;""".format(
                    NowTimeStamp=now_for_db,
                    CustomerFinancialEntityAccessId=customer_financial_entity_access_id,
                    filter_by_update_inactive='' if update_inactive_accounts else 'AND Active = 1 AND Freeze IS NULL',
                    **q_params
                )
            if q:
                result = process_query(q)
        return

    @staticmethod
    def update_acc_set_mov_scrap_fin(fin_ent_account_id: str,
                                     db_customer_id: int,
                                     result_code: ResultCode) -> None:
        """
        Update_account - movements scraping finished
        set
            MovementsScrapingInProgress = 0,
            BalancesScrapingInProgress = 0,
            LastMovementsScrapingFinishedTimeStamp = ts
        add
            historical record

        UPD: removed with(nolock) to fix unupdated accs
        """

        now_for_db = date_funcs.now_for_db()
        q = """
        -- update_acc_set_mov_scrap_fin for account {FinancialEntityAccountId}

        DECLARE @AccountId BIGINT;
        DECLARE @Balance DECIMAL(38,20);
        DECLARE @BalancesScrapingStartedTimeStamp DATETIME;
        DECLARE @BalancesScrapingFinishedTimeStamp DATETIME;
        DECLARE @MovementsScrapingStartedTimeStamp DATETIME;

        UPDATE dbo._TesoraliaAccounts
        SET MovementsScrapingInProgress = 0,
            BalancesScrapingInProgress = 0, 
            LastMovementsScrapingFinishedTimeStamp = '{NowTimeStamp}',
            LastResponseTesoraliaDescription = '{LastResponseTesoraliaDescription}',
            LastScrapingAttemptFinishedTimeStamp = '{NowTimeStamp}'
            {LastSuccessStmt}
        WHERE 
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
            CustomerId = {CustomerId};
        """.format(
            NowTimeStamp=now_for_db,
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            LastResponseTesoraliaDescription=result_code.description,
            # SUCCESS.code == 0. Also,  WRN_...code == 0,
            # thus warnings are acceptable to upd LastSuccessDownload
            LastSuccessStmt=
                ", LastSuccessDownload='{}'".format(now_for_db)
                if result_code.code == result_codes.SUCCESS.code
                else '',
        )
        process_query(q)
        return

    @staticmethod
    def get_last_movements_scraping_finished_ts(
            fin_ent_account_id: str,
            db_customer_id: int) -> dict:
        """
        Get max ValueDate and OperationalDate of all movements of the Account

        :return:
            {'MaxValueDate': datetime.datetime(1900, 1, 1, 0, 0);
            'MaxOperationalDate': datetime.datetime(1900, 1, 1, 0, 0)}
        """
        # think about: don't optimize this query que to many calcs on every insert
        q = """
        -- get_last_movements_scraping_finished_ts for account {FinancialEntityAccountId}

        DECLARE @AccountId BIGINT;

        -- get account id
        SELECT 
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE 
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
            CustomerId = {CustomerId};

        SELECT
            max(OperationalDate) as MaxOperationalDate,
            max(ValueDate) as MaxValueDate
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE 
            AccountId = @AccountId;
        """.format(FinancialEntityAccountId=fin_ent_account_id,
                   CustomerId=db_customer_id)

        result = process_query(q)
        if not result:
            return {}  # to use .get method
        return result[0]

    @staticmethod
    def upd_possible_inactive_set_scraping_state_to_false(db_customer_id: int) -> None:
        """
        Use this func in the end of the scraping for user (customer).
        The aim of its to set all PossibleInactive accounts to 'scraping not in progress',
        because really unavailable in the web sites, but still existing in the DB accounts were
        marked as 'scraping in progress'.
        NOTE: this func doesn't set 'last...finished' timestamps because they are not really scraped.
        We use customer level (not fin ent access level) due to same accounts can be presented in
        different accesses, so, to avoid collisions, we don't update the states at fin ent access levels
        """
        q = """
        -- upd_possible_inactive_set_scraping_state_to_false for customer {CustomerId}

        UPDATE dbo._TesoraliaAccounts
        SET MovementsScrapingInProgress = 0,
            BalancesScrapingInProgress = 0
        WHERE 
            CustomerId = {CustomerId}
            AND PossibleInactive = 1;
        """.format(CustomerId=db_customer_id)
        process_query(q)
        return

    @staticmethod
    def check_should_download_receipts(fin_ent_account_id: str, db_customer_id: int) -> bool:
        q = """
        -- check_should_download_receipts for account {FinancialEntityAccountId}

        SELECT Id FROM dbo._TesoraliaAccounts
        WHERE
          FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
          CustomerId = {CustomerId} AND 
          scrapereceipts=1
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id
        )

        result = process_query(q)
        if not result:
            return False

        return True

class AccessFuncs:
    @staticmethod
    def get_financial_entity_access_date_to_offset(fin_ent_access_id: int) -> Optional[int]:
        """Get optional date to offset of the access"""
        q = """
        -- get_access_date_to_offset for {FinancialEntityAccessId}
        SELECT 
            dateToOffset
        FROM
            dbo.accesos_AccClientes
        WHERE 
            accesosClienteId = {FinancialEntityAccessId}
        """.format(
            FinancialEntityAccessId=fin_ent_access_id
        )
        res = process_query(q)
        if res:
            return res[0]['dateToOffset']
        return None

    @staticmethod
    def get_deactivate_2fa(fin_ent_access_id: int) -> bool:
        """Returns deactivate2FA field from access
         :param fin_ent_access_id: CustomerFinancialEntityAccessId
         :returns bool
         """

        q = """
            -- get_deactivate_2fa for access {CustomerFinancialEntityAccessId}
            EXEC dbo.SP_PY_GetDeactivate2FAFromAccess
                @CustomerFinancialEntityAccessId='{CustomerFinancialEntityAccessId}';
                """.format(
            CustomerFinancialEntityAccessId=fin_ent_access_id
        )
        result = process_query(q)
        # the sql query always returns result
        return bool(result[0]['deactivate2FA'])


    @staticmethod
    def get_all_receipts_customer_financial_entity_accesses_ids() -> List[int]:
        """Get all customer_financial_entity_access_id with receipts download configured"""
        q = """
        -- get_all_receipts_accesses 
            SELECT CustomerFinancialEntityAccessId
            FROM [lportal].[dbo].[V_Accesos_activos_para_descargar_PDFs]
        """
        res = process_query(q)
        if res:
            return [int(a['CustomerFinancialEntityAccessId']) for a in res]
        return []


class MovementFuncs:
    @staticmethod
    def _movements_scraped_new(movements_scraped: List[MovementScraped],
                               fin_ent_account_id: str,
                               db_customer_id: int) -> List[MovementScraped]:
        """:returns new movements after last saved movement of given account"""

        last_movement_saved_keyvalue = ''
        last_movement_saved = MovementFuncs.get_last_movement_of_account(fin_ent_account_id, db_customer_id)
        if last_movement_saved:
            last_movement_saved_keyvalue = last_movement_saved['KeyValue'].strip()
        if not last_movement_saved_keyvalue:
            # No prev movement_saved - all movements_scraped are new
            return movements_scraped

        movements_scraped_new = []  # type: List[MovementScraped]
        found_new_movs_point = False
        for mov in movements_scraped:
            # Add all movements after found_new_movs_point detection
            if found_new_movs_point:
                movements_scraped_new.append(mov)
                continue
            # New point not found yet
            if mov.KeyValue == last_movement_saved_keyvalue:
                found_new_movs_point = True
        # No intersection with previously scraped movements (mostly due to manual time frame) -
        # that means all scraped are new
        if not found_new_movs_point:
            movements_scraped_new = movements_scraped
        return movements_scraped_new

    @staticmethod
    def fill_empty_initial_id_from_id(db_customer_id: int,
                                      fin_ent_account_id: str,
                                      since_date: str) -> None:
        """Fills InitialId for the very new movements"""
        q = """
            -- upd InitialId from Id for {FinancialEntityAccountId}

            DECLARE @AccountId BIGINT;
            SELECT @AccountId = Id
            FROM dbo._TesoraliaAccounts
            WHERE
                FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
                CustomerId = {CustomerId};
            
            MERGE INTO dbo._TesoraliaStatements Tgt
            USING (
                SELECT
                    Id, InitialId
                FROM dbo._TesoraliaStatements
                WHERE
                    AccountId = @AccountId AND
                    InitialId IS NULL AND
                    OperationalDate >= '{since_date}'
                ) Src
            ON
                Tgt.Id = Src.Id
            
            WHEN MATCHED THEN
                UPDATE SET Tgt.InitialId = Src.Id;
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            since_date=since_date
        )
        process_query(q)
        return

    @staticmethod
    def add_new_movements(movements_scraped: List[MovementScraped],
                          fin_ent_account_id: str,
                          db_customer_id: int) -> Optional[str]:
        """
        Accepts all provided movements_scraped of the account and then
        uploads (inserts) only new movements (detects them automatically)
        using _TesoraliaAccounts.MovementsInsertMutex.
        The function provides batch uploading without IF EXISTS check for each movement.

        important:
            fails on lists more than 100 movements (use MOVEMENTS_TO_UPLOAD_BATCH_SIZE to split to batches),
            can insert not all movements even with passing correct query
            solution implemented: split in several queries

        :returns Optional[err_msg]. Err_msg means movements_insert_mutex failure, should be logged in scraper
        """

        # Speed optimization if most accounts HAVE NO new movements,
        # but speed degradation if most accounts HAVE new movements (due to additional DB query)
        # movements_scraped_new_pre = MovementFuncs._movements_scraped_new(
        #     movements_scraped,
        #     fin_ent_account_id,
        #     db_customer_id
        # )
        #
        # if not movements_scraped_new_pre:
        #     log('Account {} has no new movements. Skip the insertion.'.format(
        #         fin_ent_account_id,
        #     ))
        #     return None

        movs_insert_mutex = str(uuid.uuid4())
        AccountFuncs.set_movements_insert_mutex_if_not_locked_yet(
            fin_ent_account_id,
            db_customer_id,
            movs_insert_mutex
        )

        # The step to avoid races between threads or processes
        movs_insert_mutex_in_db = AccountFuncs.get_movements_insert_mutex(
            fin_ent_account_id,
            db_customer_id,
        )
        if movs_insert_mutex_in_db == movs_insert_mutex:
            log('Account {} has been successfully locked by mutex {} for movements insertion.'.format(
                fin_ent_account_id,
                movs_insert_mutex
            ))
        else:
            log('Account {} already locked by another mutex {}. Skip movements insertion'.format(
                fin_ent_account_id,
                movs_insert_mutex_in_db
            ))
            return None

        # Can't use movements_scraped_new_pre - may cause data races (inconsistent movements)
        movements_scraped_new = MovementFuncs._movements_scraped_new(
            movements_scraped,
            fin_ent_account_id,
            db_customer_id
        )

        now_for_db = date_funcs.now_for_db()

        err_msg = None  # type: Optional[str]
        # Extra try to provide after_added_movements,
        # then re-raise
        try:
            # Split movements to batches by MOVEMENTS_TO_UPLOAD_BATCH_SIZE
            for i, mov_batch in enumerate(_split_list(movements_scraped_new,
                                                      project_settings.MOVEMENTS_TO_UPLOAD_BATCH_SIZE)):
                # Edge case - skip empty list
                if not mov_batch:
                    continue

                # Filter each time by mutex to avoid cases
                # when someone manually resets the mutex during the insertion
                q = """
                -- add_new_movements #{ix} for account {FinancialEntityAccountId}
                
                DECLARE @AccountId BIGINT;
                SELECT @AccountId = Id 
                FROM dbo._TesoraliaAccounts
                WHERE 
                    FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
                    CustomerId = {CustomerId} AND
                    MovementsInsertMutex = '{MovementsInsertMutex}';
                
                INSERT INTO dbo._TesoraliaStatements (
                    OperationalDate,
                    OperationalDatePosition,
                    ValueDate,
                    StatementDescription,
                    StatementExtendedDescription,
                    Amount,
                    TempBalance,
                    AccountId,
                    KeyValue,
                    Bankoffice,
                    Payer,
                    CreateTimeStamp,
                    CurrentCreateTimeStamp,
                    InitialId,
                    ExportTimeStamp,
                    Receipt,
                    ReceiptChecksum
                ) VALUES
                """.format(
                    FinancialEntityAccountId=fin_ent_account_id,
                    CustomerId=db_customer_id,
                    ix=i,
                    MovementsInsertMutex=movs_insert_mutex
                )

                for movement in mov_batch:  # type: MovementScraped
                    q_params = movement._asdict()
                    assert datetime.datetime.strptime(q_params['OperationalDate'], project_settings.DB_DATE_FMT)
                    assert datetime.datetime.strptime(q_params['ValueDate'], project_settings.DB_DATE_FMT)
                    if q_params['CreateTimeStamp']:
                        assert datetime.datetime.strptime(q_params['CreateTimeStamp'],
                                                          project_settings.DB_TIMESTAMP_FMT)

                    q_params['StatementDescription'] = extract.escape_quote_for_db(q_params['StatementDescription'])
                    q_params['StatementExtendedDescription'] = extract.escape_quote_for_db(
                        q_params['StatementExtendedDescription']
                    )
                    q_params['FinancialEntityAccountId'] = fin_ent_account_id
                    q_params['CustomerId'] = db_customer_id
                    q_params['Bankoffice'] = extract.escape_quote_for_db(q_params['Bankoffice'])
                    q_params['Payer'] = extract.escape_quote_for_db(q_params['Payer'])
                    # Keep if passed or create a new CreateTimeStamp if None.
                    # It is useful for exporting functionality for
                    # a feature when we 'transfer'
                    # the CreateTimeStamp for the renewed movement from
                    # the previously inserted to allow export only
                    # really new movements.
                    # (The detection 'is renewed or a new movement' is a kind of
                    # a heuristic and may give false-positive new timestamps for movements
                    # but it's ok at this stage).
                    # Suitable only for balance_integrity error fixes.
                    q_params['CreateTimeStamp'] = q_params['CreateTimeStamp'] or now_for_db
                    # CurrentCreateTimeStamp always contains the real timestamp
                    # where exact movement was inserted
                    q_params['CurrentCreateTimeStamp'] = now_for_db
                    initial_id_for_db = q_params['InitialId'] or 'NULL'  # null for the 1st insertion
                    export_timestamp_for_db = ("'{}'".format(q_params['ExportTimeStamp'])
                                               if q_params['ExportTimeStamp']
                                               else 'NULL')  # null for the 1st insertion
                    receipt_for_db = 1 if q_params['Receipt'] == True else 'NULL'
                    receipt_checksum_for_db = ("'{}'".format(q_params['ReceiptChecksum'])
                                               if q_params['ReceiptChecksum']
                                               else 'NULL')

                    q += """
                    (
                        '{OperationalDate}',
                        '{OperationalDatePosition}',
                        '{ValueDate}',
                        '{StatementDescription}',
                        '{StatementExtendedDescription}',
                        {Amount},
                        {TempBalance},
                        @AccountId,
                        '{KeyValue}',
                        '{Bankoffice}',
                        '{Payer}',
                        '{CreateTimeStamp}',
                        '{CurrentCreateTimeStamp}',
                        {initial_id_for_db},
                        {export_timestamp_for_db},
                        {receipt_for_db},
                        {receipt_checksum_for_db}
                    ),
                    """.format(
                        **q_params,
                        initial_id_for_db=initial_id_for_db,
                        export_timestamp_for_db=export_timestamp_for_db,
                        receipt_for_db=receipt_for_db,
                        receipt_checksum_for_db=receipt_checksum_for_db
                    )

                q = re.sub(r',\s+$', '', q)  # remove last comma

                # Insert the batch
                process_query(q)
            # end for i, mov_batch

            if movements_scraped_new:
                MovementFuncs.fill_empty_initial_id_from_id(
                    db_customer_id,
                    fin_ent_account_id,
                    movements_scraped_new[0].OperationalDate  # the oldest mov
                )
        except Exception as e:
            if err_msg:
                # Not a common format, but logged in any case,
                # this might be err_msg from AccountFuncs.check_and_release_movements_insert_mutex
                log_err('-u {} -a {}: {}'.format(
                    db_customer_id,
                    fin_ent_account_id,
                    err_msg))
            # Raise up
            raise e
        finally:
            err_msg = AccountFuncs.check_and_release_movements_insert_mutex(
                fin_ent_account_id,
                db_customer_id,
                movs_insert_mutex
            )

        return err_msg

    @staticmethod
    @deprecated(reason='switched to add_new_movements')
    def add_movements_if_not_exist(movements_scraped: List[MovementScraped],
                                   fin_ent_account_id: str,
                                   db_customer_id: int) -> None:
        """
        Add if not exists or skip adding

        important:
            fails on lists more than 100 movements (use MOVEMENTS_TO_UPLOAD_BATCH_SIZE to split to batches),
            can insert not all movements even with passing correct query
            solution implemented: split in several queries
        """

        now_for_db = date_funcs.now_for_db()

        # Split movements to batches by MOVEMENTS_TO_UPLOAD_BATCH_SIZE
        for i, mov_batch in enumerate(_split_list(movements_scraped,
                                                  project_settings.MOVEMENTS_TO_UPLOAD_BATCH_SIZE)):

            q = """
            -- add_movements_if_not_exist #{ix} for account {FinancialEntityAccountId} 
                
            DECLARE @AccountId BIGINT;
            SELECT @AccountId = Id 
            FROM dbo._TesoraliaAccounts
            WITH (NOLOCK)
            WHERE 
                FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
                CustomerId = {CustomerId};
            """.format(
                FinancialEntityAccountId=fin_ent_account_id,
                CustomerId=db_customer_id,
                ix=i
            )

            for movement in mov_batch:  # type: MovementScraped

                q_params = movement._asdict()

                assert q_params['KeyValue']
                assert datetime.datetime.strptime(q_params['OperationalDate'], project_settings.DB_DATE_FMT)
                assert datetime.datetime.strptime(q_params['ValueDate'], project_settings.DB_DATE_FMT)

                q_params['StatementDescription'] = extract.escape_quote_for_db(q_params['StatementDescription'])
                q_params['StatementExtendedDescription'] = extract.escape_quote_for_db(
                    q_params['StatementExtendedDescription']
                )
                q_params['FinancialEntityAccountId'] = fin_ent_account_id
                q_params['CustomerId'] = db_customer_id
                q_params['Bankoffice'] = extract.escape_quote_for_db(q_params['Bankoffice'])
                q_params['Payer'] = extract.escape_quote_for_db(q_params['Payer'])

                q += """
                IF NOT EXISTS (SELECT * FROM dbo._TesoraliaStatements WITH (NOLOCK)
                    WHERE
                        KeyValue = '{KeyValue}' AND
                        AccountId = @AccountId)
                BEGIN
                    INSERT INTO dbo._TesoraliaStatements (
                        OperationalDate,
                        OperationalDatePosition,
                        ValueDate,
                        StatementDescription,
                        StatementExtendedDescription,
                        Amount,
                        TempBalance,
                        AccountId,
                        KeyValue,
                        Bankoffice,
                        Payer,
                        CreateTimeStamp)
                    VALUES (
                        '{OperationalDate}',
                        '{OperationalDatePosition}',
                        '{ValueDate}',
                        '{StatementDescription}',
                        '{StatementExtendedDescription}',
                        {Amount},
                        {TempBalance},
                        @AccountId,
                        '{KeyValue}',
                        '{Bankoffice}',
                        '{Payer}',
                        '{CreateTimeStamp}')
                END;""".format(CreateTimeStamp=now_for_db, **q_params)

            # q += 'COMMIT TRANSACTION;'

            if q:
                result = process_query(q)
        return

    @staticmethod
    def delete_movs_since_date(fin_ent_account_id: str,
                               db_customer_id: int,
                               date_from_str: str) -> None:

        operational_date_from = date_funcs.convert_date_to_db_format(date_from_str)

        q = """
        -- delete_movs_since_date {OperationalDate} for account {FinancialEntityAccountId}
        DECLARE @AccountId BIGINT;
        SELECT @AccountId = Id 
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE 
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
            CustomerId = {CustomerId};
        DELETE FROM dbo._TesoraliaStatements
        WHERE
            [OperationalDate] >= '{OperationalDate}' AND
            [AccountId] = @AccountId;
        """.format(
            OperationalDate=operational_date_from,
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id
        )

        result = process_query(q)
        return

    @staticmethod
    def delete_movs_after_id(fin_ent_account_id: str,
                             db_customer_id: int,
                             movement_id: int) -> None:

        """Use this when autofix movements"""

        q = """
        -- delete_movs_after_id {Id} for account {FinancialEntityAccountId}
        
        DECLARE @AccountId BIGINT;
        SELECT @AccountId = Id 
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE 
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
            CustomerId = {CustomerId};
        DELETE FROM dbo._TesoraliaStatements
        WHERE
            Id > {Id} 
            AND AccountId = @AccountId;
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            Id=movement_id
        )

        result = process_query(q)
        return


    @staticmethod
    def get_last_movement_of_account(fin_ent_account_id: str,
                                     db_customer_id: int) -> Optional[dict]:

        q = """
        -- get_last_movement_of_account for account {FinancialEntityAccountId} 

        DECLARE @AccountId BIGINT;

        -- get account id
        SELECT
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
            CustomerId = {CustomerId};

        SELECT TOP 1 {movement_select_fields}
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE AccountId = @AccountId
        ORDER BY Id DESC;  
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            movement_select_fields=MOVEMENT_SELECT_FIELDS,
        )

        result = process_query(q)
        if not result:
            return None
        return result[0]

    @staticmethod
    def get_first_movement_of_account(fin_ent_account_id: str,
                                      db_customer_id: int) -> Optional[dict]:

        q = """
        -- get_first_movement_of_account for account {FinancialEntityAccountId}
        
        DECLARE @AccountId BIGINT;

        -- get account id
        SELECT
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}'
            AND CustomerId = {CustomerId};

        SELECT TOP 1 {movement_select_fields}
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE AccountId = @AccountId
        ORDER BY OperationalDate ASC, Id ASC;  
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            movement_select_fields=MOVEMENT_SELECT_FIELDS,
        )

        result = process_query(q)
        if not result:
            return None
        return result[0]

    @staticmethod
    def get_one_movement_before_date(fin_ent_account_id: str,
                                     db_customer_id: int,
                                     date_str) -> Optional[dict]:
        """
        Use this function to get one movement before the date_str.
        It's useful for increasing_offset.
        :param date_str: usual fmt 30/01/2019
        """
        q = """
        -- get_one_movement_before_date {OperationalDate} for account {FinancialEntityAccountId}
        
        DECLARE @AccountId BIGINT;

        -- get account id
        SELECT
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}'
            AND CustomerId = {CustomerId};

        SELECT TOP 1 {movement_select_fields}
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE AccountId = @AccountId
            AND OperationalDate < '{OperationalDate}'
        ORDER BY Id DESC;  
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            OperationalDate=date_funcs.convert_date_to_db_format(date_str),
            movement_select_fields=MOVEMENT_SELECT_FIELDS,
        )

        result = process_query(q)
        if not result:
            return None
        return result[0]

    @staticmethod
    def get_movements_since_date(fin_ent_account_id: str,
                                 db_customer_id: int,
                                 date_from_str: str) -> List[dict]:
        """
        Use this function to compare movements scraped last time and now
        Returns movements in ascending ordering by Id
        """

        date_from_str_for_db = date_funcs.convert_date_to_db_format(date_from_str)

        q = """
        -- get_movements_since_date for account {FinancialEntityAccountId}
        
        DECLARE @AccountId BIGINT;

        -- get account id
        SELECT
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
            CustomerId = {CustomerId};

        SELECT {movement_select_fields}
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE
            AccountId = @AccountId
            AND OperationalDate >= '{DateFrom}'
        ORDER BY Id ASC;
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            DateFrom=date_from_str_for_db,
            movement_select_fields=MOVEMENT_SELECT_FIELDS,
        )

        result = process_query(q)
        if not result:
            return []
        return result

    @staticmethod
    def get_movements_after_first_movement_of_date(fin_ent_account_id: str,
                                                   db_customer_id: int,
                                                   date_from_str: str) -> List[dict]:
        """
        Use this functions to compare movements scraped last time and now
        Returns movements in ascending ordering by Id
        """

        date_from_str_for_db = date_funcs.convert_date_to_db_format(date_from_str)

        q = """
        -- get_movements_after_first_movement_of_date for account {FinancialEntityAccountId}
        
        DECLARE @AccountId BIGINT;
        DECLARE @MovIdFirstOfDate BIGINT;
        
        
        -- get account id
        SELECT
            @AccountId = Id
        FROM dbo._TesoraliaAccounts
        WITH (NOLOCK)
        WHERE
            FinancialEntityAccountId = '{FinancialEntityAccountId}' 
            AND CustomerId = {CustomerId};
        
        -- get Id of the first movement of the date
        -- suitable to handle cases with meshed dates
        -- to extract all movs after the specific one
        -- ES0300810165510002217427 (12.10.2018-15.10.2018)
        SELECT TOP 1
              @MovIdFirstOfDate = Id
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE
            AccountId = @AccountId
            AND OperationalDate >= '{DateFrom}'
        ORDER BY Id ASC;
        
        
        SELECT {movement_select_fields}
        FROM dbo._TesoraliaStatements
        WITH (NOLOCK)
        WHERE
            AccountId = @AccountId
            AND Id >=  @MovIdFirstOfDate
        ORDER BY Id ASC;
        """.format(
            FinancialEntityAccountId=fin_ent_account_id,
            CustomerId=db_customer_id,
            DateFrom=date_from_str_for_db,
            movement_select_fields=MOVEMENT_SELECT_FIELDS,
        )

        result = process_query(q)
        if not result:
            return []
        return result

    @staticmethod
    def get_movement_data_from_keyvalue(mov_keyvalue: str,
                                        fin_ent_account_id: str,
                                        customer_id: int) -> Optional[dict]:
        """
        :param mov_keyvalue:
        :param fin_ent_account_id: use full FinancialEntityAccountId.
            Also, see check_add_correspondence_doc (these funcs in one pipeline)
        :param customer_id:
            Added param to avoid obtaining the information of an account belonging to another client,
            since it may be duplicated in several customers
        :return: optional mov partial dict
        """
        if not mov_keyvalue or not fin_ent_account_id or not customer_id:
            return None

        q = """
        -- get_movement_initial_id_from_keyvalue for account: {FinancialEntityAccountId} keyvalue: {KeyValue}
        EXEC [dbo].[SP_PY_GetMovementInitialIdFromKeyvalue]
                @CustomerId='{CustomerId}',
                @FinancialEntityAccountId='{FinancialEntityAccountId}',
                @KeyValue='{KeyValue}';
        """.format(FinancialEntityAccountId=fin_ent_account_id,
                   CustomerId=customer_id,
                   KeyValue=mov_keyvalue)

        result = process_query(q)
        if result:
            return result[0]
        return None

    @staticmethod
    def get_customer_reference_patterns(db_customer_id: int) -> Tuple[str, str]:

        q = """
        -- get_customer_reference_patterns for customer {db_customer_id}
        
        SELECT EV.[data_]	
        FROM [dbo].[ExpandoColumn] EC
        INNER JOIN [dbo].[ExpandoValue] EV
        ON EC.[columnId] = EV.[columnId]
        WHERE EC.[name] LIKE '_Referencia___patron' AND EV.[classPK]='{db_customer_id}'
        ORDER BY EC.[name]
        """.format(db_customer_id=db_customer_id)

        result = process_query(q)
        if result:
            return result[0]['data_'], result[1]['data_']
        return "", ""

    @staticmethod
    def get_customer_show_bankoffice_payer(db_customer_id: int) -> Tuple[bool, bool]:
        """Verifies whether bankoffice and payer
        should be extracted from the extended description

        :returns (show_bankoffice, show_payer)
        """

        q = """
        -- get_customer_show_bankoffice_payer for {db_customer_id}

        SELECT EV.[data_]	
        FROM [dbo].[ExpandoColumn] EC
        INNER JOIN [dbo].[ExpandoValue] EV
        ON EC.[columnId] = EV.[columnId]
        WHERE EC.[name] IN ('_Mostrar_oficina','_Mostrar_Pagador') 
        AND EV.[classPK]='{db_customer_id}'
        ORDER BY EC.[name]
        """.format(db_customer_id=db_customer_id)

        result = process_query(q)
        if result:
            return result[0]['data_'].lower() == 'true', result[1]['data_'].lower() == 'true'
        else:
            return False, False

    @staticmethod
    @deprecated(reason='Receipt and ReceiptChecksum updated on add_correspondence_doc method')
    def set_receipt_info(
            account_fin_ent_id: str,
            db_customer_id: int,
            mov_keyvalue: str,
            receipt_checksum: str) -> None:
        receipt_checksum_str = "'{}'".format(receipt_checksum) if receipt_checksum else 'NULL'

        q = """
            -- set_receipt_info for movement {mov_keyvalue}

            DECLARE @AccountId BIGINT;

            -- get account id
            SELECT 
              @AccountId = Id
            FROM 
              dbo._TesoraliaAccounts
            WITH (NOLOCK)
            WHERE
              FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
              CustomerId = {CustomerId};

            -- update related movements
            UPDATE 
              dbo._TesoraliaStatements
            SET
              Receipt = 1,
              ReceiptChecksum = {receipt_checksum_str}
            WHERE 
              AccountId=@AccountId AND
              KeyValue = '{mov_keyvalue}';
        """.format(
            FinancialEntityAccountId=account_fin_ent_id,
            CustomerId=db_customer_id,
            receipt_checksum_str=receipt_checksum_str,
            mov_keyvalue=mov_keyvalue
        )

        process_query(q)
        return

    @staticmethod
    def set_movement_references(account_fin_ent_id: str, db_customer_id: int,
                                mov_keyvalue: str, mov_reference1: str, mov_reference2: str) -> None:

        q = """
            -- set_movement_references for movement {mov_keyvalue}
            
            DECLARE @AccountId BIGINT;
    
            -- get account id
            SELECT 
              @AccountId = Id
            FROM 
              dbo._TesoraliaAccounts
            WITH (NOLOCK)
            WHERE
              FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
              CustomerId = {CustomerId};
    
            -- update related movements
            UPDATE 
              dbo._TesoraliaStatements
            SET 
              StatementReference1 = '{mov_reference1}',
              StatementReference2 = '{mov_reference2}'
            WHERE 
              AccountId=@AccountId AND
              KeyValue = '{mov_keyvalue}';
        """.format(
            FinancialEntityAccountId=account_fin_ent_id,
            CustomerId=db_customer_id,
            mov_reference1=mov_reference1,
            mov_reference2=mov_reference2,
            mov_keyvalue=mov_keyvalue
        )

        process_query(q)
        return

    @staticmethod
    def update_extended_descriptions_if_necessary(movements_scraped: List[MovementScraped],
                                                  fin_ent_account_id: str,
                                                  db_customer_id: int) -> None:
        """Updates StatementExtendedDescription
        and also Bankoffice and Payer which are extracted from extended description
        if len(descr_new) > len(descr_old)
        """

        for i, mov_batch in enumerate(_split_list(movements_scraped,
                                                  project_settings.MOVEMENTS_TO_UPLOAD_BATCH_SIZE)):
            # Edge case - skip empty list
            if not mov_batch:
                continue

            q = """
            -- update_extended_descriptions_if_necessary #{ix} for account {FinancialEntityAccountId}
            DECLARE @AccountId BIGINT;
            SELECT @AccountId = Id
            FROM dbo._TesoraliaAccounts
            WITH (NOLOCK)
            WHERE
                FinancialEntityAccountId = '{FinancialEntityAccountId}' AND
                CustomerId = {CustomerId};
            """.format(
                FinancialEntityAccountId=fin_ent_account_id,
                CustomerId=db_customer_id,
                ix=i,
            )

            q += """
                UPDATE e
                SET
                    StatementExtendedDescription = t.StatementExtendedDescription,
                    Bankoffice = t.Bankoffice,
                    Payer = t.Payer
                FROM dbo._TesoraliaStatements e
                JOIN (
                    VALUES
            """

            for movement in mov_batch:  # type: MovementScraped
                q += """
                ('{StatementExtendedDescription}',
                 '{Bankoffice}',
                 '{Payer}',
                 @AccountId,
                 '{KeyValue}',
                 {stmt_len}
                )
                """.format(
                    StatementExtendedDescription=extract.escape_quote_for_db(
                        movement.StatementExtendedDescription
                    ),
                    Bankoffice=extract.escape_quote_for_db(movement.Bankoffice),
                    Payer=extract.escape_quote_for_db(movement.Payer),
                    KeyValue=movement.KeyValue,
                    stmt_len=len(movement.StatementExtendedDescription)
                )
                q += ""","""

            q = q[:-1]
            q += """
            ) t (
                StatementExtendedDescription,
                Bankoffice,
                Payer,
                AccountId,
                KeyValue,
                lenDescription
            )
            ON t.AccountId = e.AccountId
                AND t.KeyValue = e.KeyValue
                AND len(e.StatementExtendedDescription) < lenDescription;
            """
            if q:
                result = process_query(q)

        return

    @staticmethod
    def update_descriptions_if_necessary(movements_scraped: List[MovementScraped],
                                         fin_ent_account_id: str,
                                         db_customer_id: int) -> None:
        """Sets new description if len(new) > len(saved)"""

        for i, mov_batch in enumerate(_split_list(movements_scraped,
                                                  project_settings.MOVEMENTS_TO_UPLOAD_BATCH_SIZE)):
            if len(mov_batch):
                q = """
                -- update_descriptions_if_necessary #{ix} for account {FinancialEntityAccountId} 
                
                DECLARE @AccountId BIGINT;
                SELECT @AccountId = Id 
                FROM dbo._TesoraliaAccounts
                WITH (NOLOCK)
                WHERE 
                    FinancialEntityAccountId = '{FinancialEntityAccountId}' AND 
                    CustomerId = {CustomerId};
                """.format(
                    FinancialEntityAccountId=fin_ent_account_id,
                    CustomerId=db_customer_id,
                    ix=i,
                )

                for movement in mov_batch:  # type: MovementScraped
                    q += """
                    UPDATE dbo._TesoraliaStatements SET StatementDescription = '{}'
                    WHERE 
                        AccountId=@AccountId AND
                        KeyValue = '{}' AND 
                        len(StatementDescription) < {};
                    """.format(
                        extract.escape_quote_for_db(movement.StatementDescription),
                        movement.KeyValue,
                        len(movement.StatementDescription)
                    )

                result = process_query(q)  # for debugging, expect []
        return


class DocumentFuncs:
    """Collection of functions for PDF downloading:
    - correspondence
    - checks
    - leasing
    - ...
    """

    @staticmethod
    def check_add_correspondence_doc(
            corr_scraped: CorrespondenceDocScraped,
            db_customer_id: int,
            product_to_fin_ent_fn: Optional[Callable[[str], str]] = None) -> CorrespondenceDocChecked:
        """If no need to add, returns
         CorrespondenceDocChecked(IsToAdd=False, AccountId=None, AccountNo=None)
         :param product_to_fin_ent_fn: a function converts product_id to appropriate value
                    for matching `FinancialEntityAccountId LIKE '%{product_to_fin_ent_fn(product_id)}'`.
                    If not provided then default product_id[4:] will be used
         """

        assert corr_scraped.Checksum

        product_id = corr_scraped.ProductId
        if not product_id:
            # empty not allowed (it leads to any account matching),
            # thus 'Sin cuenta asociada' will not match with any FinancialEntityAccountId aka ProductId
            product_id = PDF_UNKNOWN_ACCOUNT_NO

        # Create appropriate value for further select stmt
        product_id_for_query = (
            product_id if product_id == PDF_UNKNOWN_ACCOUNT_NO  # was empty
            else product_to_fin_ent_fn(product_id) if product_to_fin_ent_fn  # custom
            # for many scrapers (historically from Bankia) + len restriction
            else product_id[-9:]
        )

        q = """
        -- check_add_correspondence_doc for '{corr_descr}..'@{corr_date} with checksum {Checksum}
        EXEC [dbo].[SP_PY_CheckSavedPDFChecksum]
                @CustomerId='{CustomerId}',
                @FinancialEntityAccountId='{FinancialEntityAccountId}',
                @Checksum='{Checksum}';
        """.format(
            corr_descr=corr_scraped.Description.replace('\n', ' ')[:8],
            corr_date=corr_scraped.DocumentDate.strftime('%d/%m/%Y'),
            Checksum=corr_scraped.Checksum,
            FinancialEntityAccountId=product_id_for_query,
            CustomerId=db_customer_id,
        )

        result = process_query(q)
        # the sql query always returns result
        res = result[0]
        doc_checked = CorrespondenceDocChecked(
            IsToAdd=bool(res['IsToAdd']),
            AccountId=res['AccountId'],
            AccountNo=res['AccountNo'],
        )
        return doc_checked

    @staticmethod
    def should_download_receipt_doc(
            mov_keyvalue: str,
            db_customer_id: int,
            fin_ent_account_id: str) -> bool:
        """Check if the movement already has a linked PDF,
        in that case returns 'False' to avoid download and save the receipt into DB
         :param mov_keyvalue
         :param db_customer_id:
            Added param to avoid obtaining the information of an account belonging to another client,
            since it may be duplicated in several customers
         :param fin_ent_account_id: FinancialEntityAccountId
         :returns bool
         """

        q = """
            -- check_download_receipt_doc for movement with keyvalue {KeyValue}
            EXEC dbo.SP_PY_CheckLinkedPDFToMovement
                @CustomerId='{CustomerId}',
                @FinancialEntityAccountId='{FinancialEntityAccountId}',
                @KeyValue='{KeyValue}';
                """.format(
            CustomerId=db_customer_id,
            FinancialEntityAccountId=fin_ent_account_id,
            KeyValue=mov_keyvalue,
        )
        result = process_query(q)
        # the sql query always returns result
        res = result[0]
        return bool(res['IsToAdd'])

    @staticmethod
    def get_account_id(
            db_customer_id: int,
            financial_entity_account_id: str) -> int:
        """Get AccountId from accountNo and CustomerId
         :param db_customer_id:
            Added param to avoid obtaining the information of an account belonging to another client,
            since it may be duplicated in several customers
         :param financial_entity_account_id: FinancialEntityAccountId
         :returns account_id
         """

        q = """
            -- get_account_id for account {FinancialEntityAccountId}
            EXEC dbo.SP_PY_GetAccountId
                @CustomerId='{CustomerId}',
                @FinancialEntityAccountId='{FinancialEntityAccountId}';
                """.format(
            CustomerId=db_customer_id,
            FinancialEntityAccountId=financial_entity_account_id
        )
        result = process_query(q)
        # the sql query always returns result
        return result[0]['AccountId']

    @staticmethod
    def add_correspondence_doc(corr_scraped: CorrespondenceDocScraped,
                               db_customer_id: int,
                               file_extension: str,
                               db_financial_entity_access_id: int) -> None:
        """
        Insert new document in table
        """
        assert file_extension in ['PDF', 'ZIP']

        q_params = corr_scraped._asdict()

        assert corr_scraped.Checksum
        q_params['DocumentDate'] = datetime.datetime.strftime(
            corr_scraped.DocumentDate,
            project_settings.DB_DATE_FMT
        )
        q_params['Description'] = extract.escape_quote_for_db(corr_scraped.Description)
        q_params['DocumentText'] = extract.escape_quote_for_db(corr_scraped.DocumentText)
        q_params['DocumentType'] = extract.escape_quote_for_db(corr_scraped.DocumentType)

        if not corr_scraped.AccountId:
            q_params['AccountId'] = 'null'

        if not corr_scraped.StatementId:
            q_params['StatementId'] = 'null'

        if corr_scraped.Amount is None:
            q_params['Amount'] = 'null'

        # Wrap into extra quotes to use in queries w/o them (raw null support)
        q_params['Currency'] = (
            'null' if corr_scraped.Currency is None
            else "'{}'".format(corr_scraped.Currency)
        )

        q_params['FileType'] = file_extension
        q_params['AccessId'] = db_financial_entity_access_id

        if not corr_scraped.OrganizationId:
            q_params['OrganizationId'] = 'null'

        if corr_scraped.AccountId and corr_scraped.StatementId:
            q = """
            -- add_document {Checksum}
                
            IF NOT EXISTS (
                SELECT TOP 1 Id FROM dbo._TesoraliaDocuments
                WHERE
                    AccountId = {AccountId}
                    AND StatementId = {StatementId}    
            )
                
                INSERT INTO dbo._TesoraliaDocuments (
                    CustomerId,
                    OrganizationId,
                    FinancialEntityId,
                    ProductId,
                    ProductType,
                    DocumentDate,
                    Description,                            
                    DocumentType,
                    DocumentText,
                    Checksum,
                    AccountId,
                    StatementId,
                    Amount,
                    Currency,
                    CreateTimeStamp,
                    FileType,
                    AccessId
                )                            
                VALUES (
                    '{CustomerId}',
                    {OrganizationId},
                    '{FinancialEntityId}',
                    '{ProductId}',
                    '{ProductType}',
                    '{DocumentDate}',
                    '{Description}',
                    '{DocumentType}',
                    '{DocumentText}',
                    '{Checksum}',
                    {AccountId},
                    {StatementId},
                    {Amount},
                    {Currency},
                    getutcdate(),
                    '{FileType}',
                    {AccessId}       
                )""".format(**q_params)

            # Update Receipt and ReceiptChecksum fields (in case we have a StatementId)
            # to link the PDF to the movement, either receipt or correspondence doc
            q += """
                UPDATE
                    dbo._TesoraliaStatements
                SET
                  Receipt = 1,
                  ReceiptChecksum = '{Checksum}'
                WHERE
                  InitialId='{StatementId}'
                """.format(**q_params)

        else:
            q = """
            -- add_document {Checksum}
            
            IF NOT EXISTS (
                SELECT TOP 1 Id FROM dbo._TesoraliaDocuments
                WHERE CustomerId = {CustomerId}
                    AND ProductId = '{ProductId}'
                    AND DocumentDate = '{DocumentDate}'
                    AND Checksum = '{Checksum}'
            )
            
                INSERT INTO dbo._TesoraliaDocuments (
                    CustomerId,
                    OrganizationId,
                    FinancialEntityId,
                    ProductId,
                    ProductType,
                    DocumentDate,
                    Description,                            
                    DocumentType,
                    DocumentText,
                    Checksum,
                    AccountId,
                    StatementId,
                    Amount,
                    Currency,
                    CreateTimeStamp,
                    FileType,
                    AccessId
                )                            
                VALUES (
                    '{CustomerId}',
                    {OrganizationId},
                    '{FinancialEntityId}',
                    '{ProductId}',
                    '{ProductType}',
                    '{DocumentDate}',
                    '{Description}',
                    '{DocumentType}',
                    '{DocumentText}',
                    '{Checksum}',
                    {AccountId},
                    {StatementId},
                    {Amount},
                    {Currency},
                    getutcdate(),
                    '{FileType}',
                    {AccessId}
            )""".format(**q_params)

        result = process_query(q)  # result val for debugging purposes, expecting []
        return

    @staticmethod
    def should_download_correspondence(db_customer_id: int, fin_ent_access_id: int) -> bool:
        """
        INITIAL correspondence download logic implmenentation

        LOGIC:
        -----
        IF customer-level flag=1 and there is at least 1 account for the access where scrapereceipts=1
        THEN True
        ELSE False
        """

        # Old version: doesn't respect scrapereceipts
        # q = """
        # -- should_download_correspondence for customer {db_customer_id}
        # SELECT EV.[data_]
        # FROM [dbo].[ExpandoColumn] EC
        # INNER JOIN [dbo].[ExpandoValue] EV
        # ON EC.[columnId] = EV.[columnId]
        # WHERE EC.[name] LIKE '_Descarga_de_correspondencia' AND EV.[classPK]='{db_customer_id}'
        # ORDER BY EC.[name]
        # """.format(db_customer_id=db_customer_id)

        q = """
        -- should_download_correspondence for access {access_id}
        SELECT EV.data_
        FROM ExpandoColumn EC
            INNER JOIN ExpandoValue EV ON EC.columnId = EV.columnId
            INNER JOIN _TesoraliaAccounts TA ON EV.classPK = TA.CustomerId
        WHERE EC.name LIKE '_Descarga_de_correspondencia'
            AND TA.CustomerId={db_customer_id}
            AND TA.scrapereceipts=1
            AND TA.CustomerFinancialEntityAccessId={access_id}
        GROUP BY EV.data_;
        """.format(
            db_customer_id=db_customer_id,
            access_id=fin_ent_access_id
        )

        result = process_query(q)
        if not result:
            return False
        if result[0]['data_'] == 'false':
            return False
        return True

    @staticmethod
    def should_download_correspondence_and_generic(db_fin_ent_access_id: int) -> Tuple[bool, bool]:
        """
        Gets access-level flags:
            scrapeCorrespondence - allows correspondence downloading or not
            scrapeGenericCorrespondence - allows to download no-account-related correspondence
                                          (only if  scrapeCorrespondence also is true)
        :return (scrapeCorrespondenceBool, scrapeGenericCorrespondenceBool)
        """

        q = """
        -- should_download_correspondence_and_generic for access {db_fin_ent_access_id}
        SELECT scrapeCorrespondence, scrapeGenericCorrespondence
        FROM lportal.dbo.accesos_AccClientes
        WHERE accesosClienteId={db_fin_ent_access_id}
        """.format(
            db_fin_ent_access_id=db_fin_ent_access_id
        )

        result = process_query(q)[0]
        scrape_correspondence = result['scrapeCorrespondence'] is True
        scrape_generic_correspondence = result['scrapeGenericCorrespondence'] is True
        return scrape_correspondence, scrape_generic_correspondence

    @staticmethod
    def get_accounts_to_download_correspondence(db_fin_ent_access_id: int) -> List[AccountToDownloadCorrespondence]:
        """
        :return list of accounts where scrapeAccountCorrespondence=1
        """

        q = """
        -- get_accounts_ids_to_download_correspondence for access {db_fin_ent_access_id}
        SELECT Id, FinancialEntityAccountId
        FROM dbo._TesoraliaAccounts
        WHERE
            CustomerFinancialEntityAccessId={db_fin_ent_access_id}
            AND scrapeAccountCorrespondence=1
            AND Active=1
            AND Freeze IS NULL
        """.format(
            db_fin_ent_access_id=db_fin_ent_access_id
        )

        results = process_query(q)
        accs = [
            AccountToDownloadCorrespondence(
                Id=row['Id'],
                FinancialEntityAccountId=row['FinancialEntityAccountId']
            )
            for row in results
        ]
        return accs

    @staticmethod
    def get_accounts_to_skip_download_correspondence(db_fin_ent_access_id: int) -> List[AccountToDownloadCorrespondence]:
        """
        :return list of accounts where scrapeAccountCorrespondence=0
        """

        q = """
        -- get_accounts_ids_to_skip_download_correspondence for access {db_fin_ent_access_id}
        EXEC dbo.SP_PY_GetAccountsToSkipCorrespondenceDownload
                @CustomerFinancialEntityAccessId={db_fin_ent_access_id}
        """.format(
            db_fin_ent_access_id=db_fin_ent_access_id
        )

        results = process_query(q)
        accs = [
            AccountToDownloadCorrespondence(
                Id=row['Id'],
                FinancialEntityAccountId=row['FinancialEntityAccountId']
            )
            for row in results
        ]
        return accs

    @staticmethod
    def get_movement_initial_ids_from_document_info(
            db_account_id: int,
            document_info: DocumentTextInfo) -> List[int]:
        """
        Returns all matched movements (possible situation).
        Used for more wide search (see Laboral Kutxa)
        """
        if not document_info.Amount:
            return []

        q = """
        -- get_movement_id_from_document_info where account {AccountId}, amount {Amount} 
        SELECT [InitialId], [OperationalDatePosition]
        FROM 
            [dbo].[_TesoraliaStatements]
        WHERE 
            AccountId={AccountId}
            AND OperationalDate='{OperationalDate}'        
            AND Amount={Amount}
            AND ReceiptChecksum IS NULL
            AND StatementDescription = '{StatementDescription}'
        """.format(
            AccountId=db_account_id,
            OperationalDate=document_info.OperationalDate,
            Amount=document_info.Amount,
            StatementDescription=extract.escape_quote_for_db(document_info.StatementDescription)
        )

        if document_info.ValueDate:
            q += """
                AND ValueDate='{ValueDate}'
            """.format(ValueDate=document_info.ValueDate)

        q += """
        ORDER BY [InitialId] DESC
        """

        result = process_query(q)
        return [r['InitialId'] for r in result]

    @staticmethod
    def check_if_exists_correspondence_doc_movement_initial_id(mov_id: int) -> bool:

        q = """
        -- check_if_exists_document_movement_initial_id {StatementId} 
        SELECT TOP 1 [InitialId]
        FROM 
            [dbo].[_TesoraliaDocuments]
        WHERE 
            StatementId={StatementId}            
        """.format(StatementId=mov_id)

        result = process_query(q)
        if result:
            return True
        return False

    @staticmethod
    def should_download_checks(db_customer_id: int) -> bool:

        q = """
        -- should_download_checks for customer {customer}
        SELECT EV.[data_]   
        FROM [dbo].[ExpandoColumn] EC
        INNER JOIN [dbo].[ExpandoValue] EV
        ON EC.[columnId] = EV.[columnId]
        WHERE EC.[name] LIKE '_Descarga_de_cheques' AND EV.[classPK]='{customer}'
        ORDER BY EC.[name]
        """.format(customer=db_customer_id)

        result = process_query(q)
        if not result:
            return False
        if result[0]['data_'] == 'false':
            return False
        return True

    # DAF: solo lo usa bbva
    @staticmethod
    def check_add_checks(keyvalue_lst: List[str], db_customer_id: int) -> List[str]:
        if not keyvalue_lst:
            return []

        keyvalues_str = ", ".join("'{0}'".format(k) for k in keyvalue_lst)

        q = """
        -- check_add_checks for customer {customer} check keyvalues: {keyvalues}
        SELECT keyvalue
        FROM [dbo].[_TesoraliaChecks]
        WHERE customerId={customer} 
        AND keyvalue in ({keyvalues})
        AND statementId IS NOT NULL        
        """.format(customer=db_customer_id,
                   keyvalues=keyvalues_str)

        result = process_query(q)
        if result:
            return [r['keyvalue'] for r in result]
        return []

    @staticmethod
    def add_check(check_scraped: CheckScraped, collection_id: Optional[int]) -> None:
        """
        Insert a new check in table
        """
        q_params = check_scraped._asdict()

        assert q_params['KeyValue']
        q_params['ExpirationDate'] = date_funcs.convert_date_to_db_format(q_params['ExpirationDate'])
        q_params['CaptureDate'] = date_funcs.convert_date_to_db_format(q_params['CaptureDate'])

        # if not q_params['AccountId']:
        #   print(q_params)

        if not q_params['StatementId']:
            q_params['StatementId'] = 'null'
            q_params['AccountId'] = 'null'
            q_params['AccountNo'] = ''

        if collection_id:
            q_params['CollectionId'] = collection_id
        else:
            q_params['CollectionId'] = 'null'

        q = """
        -- add_check {CheckNumber} {KeyValue}

        INSERT INTO dbo._TesoraliaChecks(
            CheckNumber,
            CaptureDate,
            ExpirationDate,
            PaidAmount,
            NominalAmount,
            ChargeAccount,
            ChargeCIF,
            DocCode,
            Stamped,
            State,
            KeyValue,
            Receipt,
            CustomerId,
            FinancialEntityId,
            AccountId,
            AccountNo,
            StatementId,
            CollectionId            
        )                            
        VALUES (
            '{CheckNumber}',
            '{CaptureDate}',
            '{ExpirationDate}',
            '{PaidAmount}',
            '{NominalAmount}',
            '{ChargeAccount}',
            '{ChargeCIF}',
            '{DocCode}',
            '{Stamped}',
            '{State}',
            '{KeyValue}',
            '{Receipt}',
            '{CustomerId}',
            '{FinancialEntityId}',
            {AccountId},
            '{AccountNo}',
            {StatementId},
            {CollectionId}
        )""".format(**q_params)

        process_query(q)  # result val for debugging purposes, expecting []
        return

    @staticmethod
    def get_movement_initial_id_from_check_collection_data(check_collection_scraped: CheckCollectionScraped,
                                                           db_customer_id: int, desc_keywords: str) -> Optional[dict]:
        # DAF: it seems the CollectionDate = OperationalDate of the movement...
        q_params = check_collection_scraped._asdict()

        q_params['CollectionDate'] = datetime.datetime.strftime(
            datetime.datetime.strptime(q_params['CollectionDate'], '%d/%m/%Y'),
            project_settings.DB_DATE_FMT)

        q = """
        -- get_movement_initial_id_from_check_collection_data amount {Amount}
        SELECT TS.InitialId, TS.[AccountId], TA.[AccountNo]
        FROM
        [dbo].[_TesoraliaStatements] TS
        LEFT JOIN [dbo].[_TesoraliaAccounts] TA ON TS.AccountId=TA.Id
        WHERE
        TS.[Amount] = {Amount}
        AND TA.[CustomerId] = '{CustomerId}'
        AND TS.[StatementDescription] LIKE '{Keywords}'
        AND TS.InitialId NOT IN (SELECT StatementId FROM [dbo].[_TesoraliaCheckCollections] WHERE StatementId IS NOT NULL)
        ORDER BY TS.OperationalDate DESC, TS.OperationalDatePosition ASC
        """.format(CustomerId=db_customer_id,
                   Keywords=desc_keywords,
                   Amount=q_params['Amount'])

        result = process_query(q)
        if result:
            return result[0]
        return None

    @staticmethod
    def check_add_check_collections(keyvalue_lst: List[str], db_customer_id: int) -> List[str]:
        if not keyvalue_lst:
            return []

        keyvalues_str = ", ".join("'{0}'".format(k) for k in keyvalue_lst)

        q = """
        -- check_add_check_collections for customer {CustomerId} check keyvalues: {keyvalues}
        SELECT KeyValue
        FROM [dbo].[_TesoraliaCheckCollections]
        WHERE CustomerId={CustomerId} 
        AND KeyValue in ({keyvalues})
        AND StatementId IS NOT NULL        
        """.format(CustomerId=db_customer_id,
                   keyvalues=keyvalues_str)

        result = process_query(q)
        if result:
            return [r['KeyValue'] for r in result]
        return []

    @staticmethod
    def add_check_collection(check_collection_scraped: CheckCollectionScraped) -> Optional[int]:
        """
        Insert a new check collection in table
        :returns Optional[SCOPE_IDENTITY()]
        """
        q_params = check_collection_scraped._asdict()

        assert q_params['KeyValue']
        q_params['CollectionDate'] = date_funcs.convert_date_to_db_format(q_params['CollectionDate'])

        if not q_params['StatementId']:
            q_params['StatementId'] = 'null'
            q_params['AccountId'] = 'null'
            q_params['AccountNo'] = ''

        q = """
        -- add_check_collection {CollectionReference} {KeyValue}

        INSERT INTO dbo._TesoraliaCheckCollections(
            CustomerId,
            FinancialEntityId,
            AccountId,
            AccountNo,
            StatementId,
            OfficeDC,
            CheckType,
            CollectionReference,
            Amount,
            CollectionDate,
            State,
            CheckQuantity,
            KeyValue
        )                            
        VALUES (
            '{CustomerId}',
            '{FinancialEntityId}',
            {AccountId},
            '{AccountNo}',
            {StatementId},
            '{OfficeDC}',
            '{CheckType}',
            '{CollectionReference}',
            {Amount},
            '{CollectionDate}',
            '{State}',
            '{CheckQuantity}',
            '{KeyValue}'
        )
        """.format(**q_params)

        process_query(q)

        q = """                                      
        SELECT TOP 1 Id
        FROM [dbo].[_TesoraliaCheckCollections] WITH (NOLOCK)
        WHERE CustomerId={CustomerId} 
        AND KeyValue = '{KeyValue}'               
        """.format(**q_params)

        result = process_query(q)
        if result:
            return result[0]['Id']
        return None

    @staticmethod
    def delete_check_collection(keyvalue: str, db_customer_id: int) -> None:
        if not keyvalue:
            return

        q = """
         -- delete_check_collection for customer {CustomerId} and keyvalue: {KeyValue}
         DELETE FROM [dbo].[_TesoraliaCheckCollections]
         WHERE CustomerId={CustomerId} 
         AND KeyValue = '{KeyValue}'
         """.format(CustomerId=db_customer_id,
                    KeyValue=keyvalue)

        process_query(q)  # always []
        return

    @staticmethod
    def should_download_leasing(db_customer_id: int) -> bool:

        q = """
        -- should_download_leasing for customer {customer}
        SELECT EV.[data_]   
        FROM [dbo].[ExpandoColumn] EC
        INNER JOIN [dbo].[ExpandoValue] EV
        ON EC.[columnId] = EV.[columnId]
        WHERE EC.[name] LIKE '_Descarga_de_leasing' AND EV.[classPK]='{customer}'
        ORDER BY EC.[name]
        """.format(customer=db_customer_id)

        result = process_query(q)
        if not result:
            return False
        if result[0]['data_'] == 'false':
            return False
        return True

    @staticmethod
    def get_saved_leasing_contracts_keyvalues(keyvalue_lst: List[str], db_customer_id: int) -> List[str]:
        if not keyvalue_lst:
            return []

        keyvalues_str = ", ".join("'{0}'".format(k) for k in keyvalue_lst)

        q = """
        -- get_saved_leasing_contracts_keyvalues for customer {CustomerId} contract keyvalues: {keyvalues}
        SELECT KeyValue
        FROM [dbo].[_TesoraliaLeasingContracts]
        WHERE CustomerId={CustomerId} 
        AND KeyValue IN ({keyvalues})
        """.format(CustomerId=db_customer_id,
                   keyvalues=keyvalues_str)

        result = process_query(q)
        if result:
            return [r['KeyValue'] for r in result]
        return []

    @staticmethod
    def get_incomplete_leasing_contracts_keyvalues(keyvalue_lst: List[str], db_customer_id: int) -> List[str]:
        if not keyvalue_lst:
            return []

        keyvalues_str = ", ".join("'{0}'".format(k) for k in keyvalue_lst)

        q = """
        -- get_incomplete_leasing_contracts_keyvalues for customer {CustomerId} contract keyvalues: {keyvalues}
        SELECT DISTINCT LC.[KeyValue]
        FROM [lportal].[dbo].[_TesoraliaLeasingContracts] LC
        INNER JOIN [lportal].[dbo].[_TesoraliaLeasingFees] LF
        ON LC.[Id] = LF.[ContractId]
        WHERE LF.[State]<>'LIQUIDADO'
        AND LC.[CustomerId] = {CustomerId}
        AND LC.[KeyValue] IN ({keyvalues})
        """.format(CustomerId=db_customer_id,
                   keyvalues=keyvalues_str)

        result = process_query(q)
        if result:
            return [r['KeyValue'] for r in result]
        return []

    @staticmethod
    def get_paid_fees_keyvalues_for_leasing_contract(
            leasing_contract: LeasingContractScraped,
            db_customer_id: int) -> List[str]:

        q = """
        -- get_paid_fees_keyvalues_for_leasing_contract for customer {CustomerId} contract: {Contract}
        SELECT LF.[KeyValue]
        FROM [dbo].[_TesoraliaLeasingContracts] LC
        INNER JOIN [dbo].[_TesoraliaLeasingFees] LF
        ON LC.[Id] = LF.[ContractId]
        WHERE LF.[State]='LIQUIDADO'
        AND LC.[CustomerId] = {CustomerId}
        AND LC.[KeyValue] = '{KeyValue}'
        """.format(CustomerId=db_customer_id,
                   Contract=leasing_contract.ContractReference,
                   KeyValue=leasing_contract.KeyValue)

        result = process_query(q)
        if result:
            return [r['KeyValue'] for r in result]
        return []

    @staticmethod
    def add_or_update_leasing_contract(leasing_contract_scraped: LeasingContractScraped) -> Optional[int]:
        """
        Insert or update a leasing contract in table
        :returns Optional[Id]
        """
        now_for_db = date_funcs.now_for_db()
        q_params = leasing_contract_scraped._asdict()

        assert q_params['KeyValue']
        q_params['ContractDate'] = date_funcs.convert_date_to_db_format(q_params['ContractDate'])
        q_params['ExpirationDate'] = date_funcs.convert_date_to_db_format(q_params['ExpirationDate'])

        update_contract_account_params = ''
        if not q_params['AccountId']:
            q_params['AccountId'] = 'null'
        else:
            update_contract_account_params = ', AccountId={} '.format(q_params['AccountId'])

        if not q_params['AccountNo']:
            q_params['AccountNo'] = 'null'
        else:
            update_contract_account_params = update_contract_account_params + ', AccountNo = \'{}\' '.format(q_params['AccountNo'])

        if not q_params['ResidualValue']:
            q_params['ResidualValue'] = 'null'

        update_contract_initial_interest_param = ''
        if not q_params['InitialInterest']:
            q_params['InitialInterest'] = 'null'
        else:
            update_contract_initial_interest_param = ',InitialInterest = {}'.format(q_params['InitialInterest'])

        update_contract_current_interest_param = ''
        if not q_params['CurrentInterest']:
            q_params['CurrentInterest'] = 'null'
        else:
            update_contract_current_interest_param = ',CurrentInterest = {}'.format(q_params['CurrentInterest'])

        q = """
        -- add_or_update_leasing_contract {ContractReference} {KeyValue}
        IF NOT EXISTS 
            (SELECT TOP 1 Id
            FROM [dbo].[_TesoraliaLeasingContracts] WITH (NOLOCK)
            WHERE CustomerId={CustomerId} 
            AND KeyValue = '{KeyValue}'
            ) 
        BEGIN
        -- add leasing contract {ContractReference} {KeyValue}
            INSERT INTO dbo._TesoraliaLeasingContracts(
                CustomerId,
                FinancialEntityId,
                AccountId,
                AccountNo,
                Office,
                ContractReference,
                ContractDate,
                ExpirationDate,
                FeesQuantity,
                Amount,
                Taxes,
                ResidualValue,
                InitialInterest,
                CurrentInterest,
                PendingRepayment,
                CreateTimeStamp,
                KeyValue,
                UpdateTimeStamp
            )                            
            VALUES (
                '{CustomerId}',
                '{FinancialEntityId}',
                {AccountId},
                '{AccountNo}',
                '{Office}',
                '{ContractReference}',
                '{ContractDate}',
                '{ExpirationDate}',
                '{FeesQuantity}',
                {Amount},
                {Taxes},
                {ResidualValue},
                {InitialInterest},
                {CurrentInterest},
                {PendingRepayment},
                '{NowTimeStamp}',
                '{KeyValue}',
                '{NowTimeStamp}'
            )
        END
        ELSE
        BEGIN
        -- update leasing contract {ContractReference} {KeyValue}
            UPDATE
                dbo._TesoraliaLeasingContracts
            SET
                ResidualValue = {ResidualValue},
                PendingRepayment = {PendingRepayment},
                UpdateTimeStamp = '{NowTimeStamp}'
                {CurrentInterestParams}
                {InitialInterestParams}
                {UpdateContractAccountParams}
            WHERE
                CustomerId={CustomerId} 
                AND KeyValue = '{KeyValue}'
        END                
        """.format(NowTimeStamp=now_for_db,
                   InitialInterestParams=update_contract_initial_interest_param,
                   CurrentInterestParams=update_contract_current_interest_param,
                   UpdateContractAccountParams=update_contract_account_params,
                   **q_params)

        process_query(q)

        q = """                                      
        SELECT TOP 1 Id
        FROM [dbo].[_TesoraliaLeasingContracts] WITH (NOLOCK)
        WHERE CustomerId={CustomerId} 
        AND KeyValue = '{KeyValue}'               
        """.format(**q_params)

        result = process_query(q)
        if result:
            return result[0]['Id']
        return None

    @staticmethod
    def get_leasing_fees_with_movement_id_keyvalues(
            leasing_contract: LeasingContractScraped,
            db_customer_id: int) -> List[str]:

        q = """
        -- get_leasing_fees_with_movement_id_keyvalues for customer {CustomerId} contract keyvalue: {KeyValue}
        SELECT DISTINCT LF.[KeyValue]
        FROM [lportal].[dbo].[_TesoraliaLeasingContracts] LC
        INNER JOIN [lportal].[dbo].[_TesoraliaLeasingFees] LF
        ON LC.[Id] = LF.[ContractId]
        WHERE LF.[StatementId] IS  NOT NULL
        AND LC.[CustomerId] = {CustomerId}
        AND LC.[KeyValue] = '{KeyValue}'
        """.format(CustomerId=db_customer_id,
                   KeyValue=leasing_contract.KeyValue)

        result = process_query(q)
        if result:
            return [r['KeyValue'] for r in result]
        return []

    @staticmethod
    def get_movement_initial_id_from_leasing_fee_data(leasing_fee_scraped: LeasingFeeScraped,
                                                      db_customer_id: int,
                                                      desc_keywords: str) -> Optional[dict]:

        operational_date = date_funcs.convert_date_to_db_format(leasing_fee_scraped.OperationalDate)

        q = """
        -- get_movement_initial_id_from_leasing_fee_data: customer_id:{CustomerId} fee_amount:{FeeAmount} date:{OperationalDate}
        SELECT TS.InitialId, TS.[AccountId], TA.[AccountNo]
        FROM
        [dbo].[_TesoraliaStatements] TS
        LEFT JOIN [dbo].[_TesoraliaAccounts] TA ON TS.AccountId=TA.Id
        WHERE
        --TS.OperationalDate = '{OperationalDate}'
        TS.OperationalDate BETWEEN DATEADD(day, -3, '{OperationalDate}') AND DATEADD(day, 3, '{OperationalDate}')  
        AND TA.[CustomerId] = '{CustomerId}'
        AND TS.[Amount] = {FeeAmount}
        AND TS.[StatementDescription] LIKE '{Keywords}'
        --AND TS.InitialId NOT IN (SELECT StatementId FROM [dbo].[_TesoraliaLeasingFees] WHERE StatementId IS NOT NULL)
        ORDER BY TS.OperationalDate DESC, TS.OperationalDatePosition ASC
        """.format(CustomerId=db_customer_id,
                   Keywords=desc_keywords,
                   FeeAmount="-{}".format(leasing_fee_scraped.FeeAmount),
                   OperationalDate=operational_date)

        result = process_query(q)
        if result:
            return result[0]
        return None

    @staticmethod
    def add_leasing_fee(leasing_fee_scraped: LeasingFeeScraped, contract_id: Optional[int]) -> None:
        """
        Insert a new leasing fee in table
        """

        now_for_db = date_funcs.now_for_db()
        q_params = leasing_fee_scraped._asdict()

        assert q_params['KeyValue']

        q_params['OperationalDate'] = date_funcs.convert_date_to_db_format(q_params['OperationalDate'])

        if not q_params['StatementId']:
            q_params['StatementId'] = 'null'

        if not q_params['ContractId']:
            q_params['ContractId'] = 'null'

        if contract_id:
            q_params['ContractId'] = contract_id
        else:
            q_params['ContractId'] = 'null'

        # print(q_params)  # for tests

        q = """
        -- add_leasing_fee {FeeReference} {KeyValue}

        INSERT INTO dbo._TesoraliaLeasingFees(
            FeeReference,
            FeeNumber,
            OperationalDate,
            Currency,
            Amount,
            TaxesAmount,
            InsuranceAmount,
            FeeAmount,
            FinRepayment,
            FinPerformance,
            PendingRepayment,
            State,
            KeyValue,
            CreateTimeStamp,
            StatementId,
            ContractId,
            InvoiceNumber
        )                            
        VALUES (
            '{FeeReference}',
            '{FeeNumber}',
            '{OperationalDate}',
            '{Currency}',
            '{Amount}',
            '{TaxesAmount}',
            '{InsuranceAmount}',
            '{FeeAmount}',
            '{FinRepayment}',
            '{FinPerformance}',
            '{PendingRepayment}',
            '{State}',
            '{KeyValue}',
            '{NowTimeStamp}',
            {StatementId},
            {ContractId},
            '{InvoiceNumber}'
        )""".format(NowTimeStamp=now_for_db,
                    **q_params)

        process_query(q)  # result val for debugging purposes, expecting []
        return

    @staticmethod
    def delete_leasing_fee(keyvalue: str) -> None:
        if not keyvalue:
            return

        q = """
         -- delete_leasing_fee. keyvalue: {KeyValue}
         DELETE FROM [dbo].[_TesoraliaLeasingFees]
         WHERE KeyValue = '{KeyValue}'
         """.format(KeyValue=keyvalue)

        process_query(q)  # always []
        return

    @staticmethod
    def delete_leasing_contract_and_fees(
            leasing_contract: LeasingContractScraped,) -> None:
        if not leasing_contract:
            return
        contract_reference = leasing_contract.ContractReference
        customer_id = leasing_contract.CustomerId
        financial_entity_id = leasing_contract.FinancialEntityId
        q = """
         -- delete_leasing_contract_and_fees. contract_reference: {ContractReference}, customer_id: {CustomerId}, financial_entity_id = {FinancialEntityId}
         
        DECLARE @ContractId BIGINT;
        SELECT
            @ContractId = Id
        FROM [dbo].[_TesoraliaLeasingContracts]
        WITH (NOLOCK)
        WHERE
             ContractReference = '{ContractReference}'
             AND
             CustomerId = {CustomerId}
             AND
             FinancialEntityId = {FinancialEntityId};
         
        DELETE 
        FROM [dbo].[_TesoraliaLeasingFees]
        WHERE ContractId = @ContractId    
        
        DELETE
        FROM [dbo].[_TesoraliaLeasingContracts]
        WHERE Id = @ContractId
         """.format(
            ContractReference=contract_reference,
            CustomerId=customer_id,
            FinancialEntityId=financial_entity_id)

        process_query(q)  # always []
        return


    @staticmethod
    def add_or_update_leasing_fee(leasing_fee_scraped: LeasingFeeScraped, contract_id: Optional[int]) -> Optional[int]:
        """
        Insert or update a leasing fee in table
        :returns Optional[Id]
        """
        now_for_db = date_funcs.now_for_db()
        q_params = leasing_fee_scraped._asdict()

        assert q_params['KeyValue']

        if contract_id:
            q_params['ContractId'] = contract_id
        else:
            q_params['ContractId'] = 'null'

        q_params['OperationalDate'] = date_funcs.convert_date_to_db_format(q_params['OperationalDate'])

        if not q_params['State']:
            q_params['State'] = 'NULL'
        else:
            q_params['State'] = "'{}'".format(q_params['State'])

        if not ('InsuranceAmount' in q_params):
            q_params['InsuranceAmount'] = 'null'

        if q_params['InsuranceAmount'] == None:
            q_params['InsuranceAmount'] = 'null'

        if not q_params['StatementId']:
            q_params['StatementId'] = 'null'

        if not q_params['InvoiceNumber']:
            q_params['InvoiceNumber'] = 'NULL'
        else:
            q_params['InvoiceNumber'] = "'{}'".format(q_params['InvoiceNumber'])

        if not q_params['DelayInterest']:
            q_params['DelayInterest'] = 'null'

        if not ('PendingRepayment' in q_params):
            q_params['PendingRepayment'] = 'null'

        if q_params['PendingRepayment'] == None:
            q_params['PendingRepayment'] = 'null'

        q = """
        -- add_or_update_leasing_fee {FeeReference} {KeyValue}
        IF NOT EXISTS 
            (SELECT TOP 1 Id
            FROM [dbo].[_TesoraliaLeasingFees] WITH (NOLOCK)
            WHERE ContractId={ContractId} 
            AND KeyValue = '{KeyValue}'
            ) 
        BEGIN
        -- add leasing fee {FeeReference} {KeyValue}
            INSERT INTO dbo._TesoraliaLeasingFees(
                FeeReference,
                FeeNumber,
                OperationalDate,
                Currency,
                Amount,
                TaxesAmount,
                InsuranceAmount,
                FeeAmount,
                FinRepayment,
                FinPerformance,
                PendingRepayment,
                State,
                KeyValue,
                CreateTimeStamp,
                StatementId,
                ContractId,
                InvoiceNumber,
                UpdateTimeStamp
            )                            
            VALUES (
                '{FeeReference}',
                '{FeeNumber}',
                '{OperationalDate}',
                '{Currency}',
                '{Amount}',
                '{TaxesAmount}',
                {InsuranceAmount},
                '{FeeAmount}',
                '{FinRepayment}',
                '{FinPerformance}',
                {PendingRepayment},
                {State},
                '{KeyValue}',
                '{NowTimeStamp}',
                {StatementId},
                {ContractId},
                {InvoiceNumber},
                '{NowTimeStamp}'
            )
        END
        ELSE
        BEGIN
        -- update leasing fee {FeeReference} {KeyValue}
            UPDATE
                dbo._TesoraliaLeasingFees
            SET
                State = {State},
                StatementId = {StatementId},
                InvoiceNumber = {InvoiceNumber},
                UpdateTimeStamp = '{NowTimeStamp}'
            WHERE
                ContractId={ContractId} 
                AND KeyValue = '{KeyValue}'
        END                
        """.format(NowTimeStamp=now_for_db,
                   **q_params)

        process_query(q)

        # q = """
        # SELECT TOP 1 Id
        # FROM [dbo].[_TesoraliaLeasingFees] WITH (NOLOCK)
        # WHERE ContractId = {ContractId}
        # AND KeyValue = '{KeyValue}'
        # """.format(**q_params)
        #
        # result = process_query(q)
        # if result:
        #     return result[0]['Id']
        return None


class TransfersFuncs:

    @staticmethod
    def get_active_transfers_accounts(fin_ent_access_id: int) -> List[DBTransferAccountConfig]:
        q = """
        -- get_active_transfers_accounts for access {fin_ent_access_id}
        
        SELECT INST.AccountId, 
               ACC.FinancialEntityAccountId , 
               ACC.CustomerFinancialEntityAccessId, 
               INST.LastScrapedTransfersTimeStamp - INST.OffsetDays as LastScrapedTransfersTimeStampWithOffset
        FROM 
               [lportal].[dbo].[_TesoraliaInstrumentsConfig] AS INST INNER JOIN [lportal].[dbo]._TesoraliaAccounts AS ACC
               ON INST.AccountId = ACC.Id
        WHERE
               INST.ScrapeTransfers = 1
               AND ACC.CustomerFinancialEntityAccessId = {fin_ent_access_id}
               AND ACC.Active = 1
               AND ACC.Freeze IS NULL
        """.format(fin_ent_access_id=fin_ent_access_id)
        # params = ('Id')
        result = process_query(q)
        return [DBTransferAccountConfig(**row) for row in result]

    @staticmethod
    def get_active_transfers_filters(
            db_account_id: int,
            navigation_type: str) -> List[DBTransferFilter]:
        q = """
        -- get_transfers_filters for account id={db_account_id}

        EXEC [tesoralia].[ONLINE].[GetActiveTransfersFilters] @AccountId={db_account_id}, @NavigationType={navigation_type}
        """.format(db_account_id=db_account_id,
                   navigation_type=navigation_type)
        # params = ('Id')
        result = process_query(q)
        transfer_filters = [DBTransferFilter(**row) for row in result]
        return transfer_filters

    @staticmethod
    def add_transfer(cursor, transfer_scraped: TransferScraped) -> None:
        """
        Insert a new transfer in table
        """

        q_params = transfer_scraped._asdict()
        if not transfer_scraped.IdStatement:
            # i.e.: transfers from transfers menu without IdStatement
            q_params['IdStatement'] = 'NULL'
            q_params['UpdateIdStatementDate'] = 'NULL'
        else:
            q_params['IdStatement'] = "'" + transfer_scraped.IdStatement + "'"
            q_params['UpdateIdStatementDate'] = 'GETDATE()'

        q_params['AccountOrder'] = extract.replace_quote_with_blank_for_db(transfer_scraped.AccountOrder)
        q_params['NameOrder'] = extract.replace_quote_with_blank_for_db(transfer_scraped.NameOrder)
        q_params['Concept'] = extract.replace_quote_with_blank_for_db(transfer_scraped.Concept)
        q_params['Reference'] = extract.replace_quote_with_blank_for_db(transfer_scraped.Reference)
        q_params['Description'] = extract.replace_quote_with_blank_for_db(transfer_scraped.Description)
        q_params['Observation'] = extract.replace_quote_with_blank_for_db(transfer_scraped.Observation)

        if transfer_scraped.TempBalance is None:
            q_params['TempBalance'] = 'NULL'

        # description is a reserved word in sql so use [Description]
        q = """
           -- add_transfer for account {AccountId} {Amount}@{OperationalDate}

           INSERT INTO lportal.dbo._TesoraliaTransferStatement(
               AccountId,
               CustomerId,
               OperationalDate,
               ValueDate,
               Amount,
               Currency,
               AccountOrder,
               NameOrder,
               Concept,
               Reference,
               [Description], 
               Obrservation,
               Entity,
               IdStatement,
               FechaRegistro,
               UpdateIdStatementDate,
               TempBalance     
           )                            
           VALUES (
               '{AccountId}',
               '{CustomerId}',
               CAST ('{OperationalDate}' AS DATETIME),
               CAST ('{ValueDate}' AS DATETIME),
               '{Amount}',
               '{Currency}',
               '{AccountOrder}',
               '{NameOrder}',
               '{Concept}',
               '{Reference}',
               '{Description}',
               '{Observation}',
               '{FinancialEntityName}',
               {IdStatement},
               GETDATE(),
               {UpdateIdStatementDate},
               {TempBalance}
           )""".format(**q_params)

        try:
            cursor.execute(q)
            # process_query(q)  # result val for debugging purposes, expecting []

        except Exception as e:
            log_err('[db_funcs.py] -> [add_transfer] -> {}: {}'.format(e, q))
            raise Exception(e)
        return

    @staticmethod
    def update_last_scraped_transfers_time_stamp(cursor, account_id: int) -> None:
        """
        Updates LastScrapedTransfersTimeStamp for an account id at TesoraliaInstrumentsConfig
        """
        try:
            q = """
               -- update LastScrapedTransfersTimeStamp for an account id at TesoraliaInstrumentsConfig 
               
                UPDATE
                    dbo._TesoraliaInstrumentsConfig
                SET
                    LastScrapedTransfersTimeStamp = GETDATE()
                WHERE
                    AccountId={AccountId}                   
                """.format(AccountId=account_id)
            cursor.execute(q)
        except Exception as e:
            log_err('[db_funcs.py] -> [update_last_scraped_transfers_time_stamp] -> {}'.format(e))
            raise Exception(e)
        return

    @staticmethod
    def get_movs_considered_transfers(
            db_account_id: int,
            fin_ent_account_id: str,
            date_from: datetime.datetime) -> List[DBMovementConsideredTransfer]:
        """Select movs_w_bank_codes_in_extended_description"""

        q = """
        -- get_movs_considered_transfers for {FinancialEntityAccountId} (id {AccountId})
        SELECT
            OperationalDate,
            ValueDate,
            Amount,
            AccountId,
            StatementExtendedDescription,
            InitialId
        FROM _TesoraliaStatements
        WHERE
            AccountId = {AccountId}
            AND OperationalDate >= '{OperationalDate}'
            AND (StatementExtendedDescription LIKE N'%Código: 0391%'
                 OR StatementExtendedDescription LIKE N'%Código: 0591%')
            AND (
              CONVERT(VARCHAR,InitialId) NOT IN
                (
                  SELECT IdStatement FROM _TesoraliaTransferStatement
                  WHERE IdStatement IS NOT NULL
                )
            )
        ORDER BY _TesoraliaStatements.Id;
        """.format(
            AccountId=db_account_id,
            FinancialEntityAccountId=fin_ent_account_id,
            OperationalDate=date_from.strftime(project_settings.DB_DATE_FMT)
        )
        result = process_query(q)
        return [DBMovementConsideredTransfer(**row) for row in result]

    @staticmethod
    def delete_duplicated_transfers_by_value_date(customer_id: int, fin_entity_name: str) -> bool:
        """Deletes duplicates from DB
        :param customer_id: db_customer_id
        :param fin_entity_title: name like 'BBVA' etc.
        """
        # AVIA customer requirement specifies that ValueDate must be used for linking movements and transfers as
        # OperatinalDate from the bank for transfers and movements can mismatch
        q = '''
            -- delete duplicated transfers for customer {customer_id}, entity {entity}
            [tesoralia].[ONLINE].[SP_DeleteDuplicatedTransfer_By_ValueDate] 
                @ParamCustomerId={customer_id}, 
                @ParamEntity='{entity}';
        '''.format(
            customer_id=customer_id,
            entity=fin_entity_name
        )
        _result = process_query(q)
        return True

    @staticmethod
    def delete_duplicated_transfers_by_operational_date(customer_id: int, fin_entity_name: str) -> bool:
        """Deletes duplicates from DB
        :param customer_id: db_customer_id
        :param fin_entity_title: name like 'BANKINTER' etc.
        """
        q = '''
            -- delete duplicated transfers for customer {customer_id}, entity {entity}
            [tesoralia].[ONLINE].[SP_DeleteDuplicatedTransfer_By_OperationalDate] 
                @ParamCustomerId={customer_id}, 
                @ParamEntity='{entity}';
        '''.format(
            customer_id=customer_id,
            entity=fin_entity_name
        )
        _result = process_query(q)
        return True

    @staticmethod
    def set_transfer_statement_id(transfer_id: int, statement_id_str: str, not_linked_reason: str) -> bool:

        q = """
            -- set IdStatement and NotLinkedReason for transfer {TransferId}
            
            EXEC [tesoralia].[ONLINE].[SetTransferIdStatement]
                @TransferId={TransferId},
                @IdStatement='{IdStatement}',
                @NotLinkedReason='{NotLinkedReason}'
        """.format(
            TransferId=transfer_id,
            IdStatement=statement_id_str,
            NotLinkedReason=not_linked_reason
        )
        _result = process_query(q)
        return True

    @staticmethod
    def get_movements_by_transfer_by_value_date(transfer: DBTransfer) -> List[DBMovementByTransfer]:
        q = '''
            -- get movement ids for transfer where account={acc_id}, date={value_date}, amount={amount}
            SELECT InitialId, StatementDescription, StatementExtendedDescription
            FROM lportal.dbo._TesoraliaStatements
            WHERE
                AccountId = {acc_id}
                AND	ValueDate = '{value_date}'
                AND Amount = {amount}
                AND CAST(InitialId AS VARCHAR) NOT IN (SELECT IdStatement FROM [lportal].[dbo].[_TesoraliaTransferStatement]
                    WHERE   OperationalDate > GETDATE() - 30
                            AND IdStatement IS NOT NULL)
        '''.format(acc_id=transfer.AccountId,
                   value_date=transfer.ValueDate.strftime(project_settings.DB_DATE_FMT),
                   amount=transfer.Amount)

        if transfer.TempBalance is not None:
            q = q + '''
                AND TempBalance = {temp_balance} '''.format(temp_balance=transfer.TempBalance)

        result = process_query(q)
        movs_by_transfer = [
            DBMovementByTransfer(
                InitialId=row['InitialId'],
                StatementDescription=row['StatementDescription'],
                StatementExtendedDescription=row['StatementExtendedDescription'],
            ) for row in result
        ]
        return movs_by_transfer

    @staticmethod
    def get_movements_by_transfer_by_operational_date(transfer: DBTransfer) -> List[DBMovementByTransfer]:
        q = '''
            -- get movement ids for transfer where account={acc_id}, date={operational_date}, amount={amount}
            SELECT InitialId, StatementDescription, StatementExtendedDescription
            FROM lportal.dbo._TesoraliaStatements
            WHERE
                AccountId = {acc_id}
                AND	OperationalDate = '{operational_date}'
                AND Amount = {amount}
                AND CAST(InitialId AS VARCHAR) NOT IN (SELECT IdStatement FROM [lportal].[dbo].[_TesoraliaTransferStatement]
                    WHERE   OperationalDate > GETDATE() - 30
                            AND IdStatement IS NOT NULL)
        '''.format(acc_id=transfer.AccountId,
                   operational_date=transfer.OperationalDate.strftime(project_settings.DB_DATE_FMT),
                   amount=transfer.Amount)

        if transfer.TempBalance is not None:
            q = q + '''
                AND TempBalance = {temp_balance} '''.format(temp_balance=transfer.TempBalance)

        result = process_query(q)
        movs_by_transfer = [
            DBMovementByTransfer(
                InitialId=row['InitialId'],
                StatementDescription=row['StatementDescription'],
                StatementExtendedDescription=row['StatementExtendedDescription'],
            ) for row in result
        ]
        return movs_by_transfer

    @staticmethod
    def get_db_transfer_from_db_row(db_row: dict) -> DBTransfer:
        """Extracts transfer from row
        Reference, Description, Obrsevation, IdStatement, FechaRegistro,
        UpdateIdStatementDate, NotLinkedReason, TempBalance can be null
        """
        dt_min = datetime.datetime.min
        transf_id = db_row['Id']  # type: int
        account_id = db_row['AccountId']  # type: int
        customer_id = db_row['CustomerId']  # type: int
        operational_date = db_row['OperationalDate']  # type: datetime.datetime
        value_date = db_row['ValueDate']  # type: datetime.datetime
        amount = round(float(db_row['Amount']), 2)  # type: float  # from Decimal
        temp_balance = (round(float(db_row['TempBalance']), 2)
                        if db_row['TempBalance'] else None)  # type: Optional[float] # from opt Decimal
        currency = db_row['Currency']  # type: str
        account_order = db_row['AccountOrder']  # type: str
        name_order = db_row['NameOrder']  # type: str
        concept = db_row['Concept']  # type: str
        entity = db_row['Entity']  # type: str
        reference = db_row['Reference'] or ''  # type: str
        description = db_row['Description'] or ''  # type: str
        obrservation = db_row['Obrservation'] or ''  # type: str
        id_statement = db_row['IdStatement'] or ''  # type: str
        fecha_registro = db_row['FechaRegistro'] or dt_min  # type: datetime.datetime
        update_id_statement_date = db_row['UpdateIdStatementDate'] or dt_min  # type: datetime.datetime
        not_linked_reason = db_row['NotLinkedReason'] or ''  # type: str

        db_transfer = DBTransfer(
            Id=transf_id,
            AccountId=account_id,
            CustomerId=customer_id,
            OperationalDate=operational_date,
            ValueDate=value_date,
            Amount=amount,
            TempBalance=temp_balance,
            Currency=currency,
            AccountOrder=account_order,
            NameOrder=name_order,
            Concept=concept,
            Reference=reference,
            Description=description,
            Obrservation=obrservation,
            Entity=entity,
            IdStatement=id_statement,
            FechaRegistro=fecha_registro,
            UpdateIdStatementDate=update_id_statement_date,
            NotLinkedReason=not_linked_reason,
        )
        return db_transfer

    @staticmethod
    def get_transfers_w_statement_id_null(customer_id: int, fin_entity_name: str) -> List[DBTransfer]:
        q = """
            -- get transfers with IdStatement is NULL/No vinculable/Multiple vinculation for customer {customer_id}, entity {entity}
        
            EXEC [tesoralia].[ONLINE].[GetTransfersIdStatementNull] 
                @CustomerId={customer_id}, 
                @Entity={entity}
        """.format(customer_id=customer_id,
                   entity=fin_entity_name)
        result = process_query(q)
        db_transfers = [TransfersFuncs.get_db_transfer_from_db_row(row) for row in result]
        return db_transfers

    @staticmethod
    def get_transfers_w_operational_date_in_range(
            account_id: int,
            from_operational_date_str: str,
            to_operational_date_str: str) -> List[DBTransfer]:
        q = """
            -- get transfers with for account {account_id}, {from_operational_date} >= operational date <= {to_operational_date}

            EXEC [tesoralia].[ONLINE].[GetTransfersOperationalDateInRange] 
                @AccountId={account_id},
                @FromOperationalDate='{from_operational_date}', 
                @ToOperationalDate='{to_operational_date}';
        """.format(account_id=account_id,
                   from_operational_date=from_operational_date_str,
                   to_operational_date=to_operational_date_str,
                   )
        result = process_query(q)
        db_transfers = [TransfersFuncs.get_db_transfer_from_db_row(row) for row in result]
        return db_transfers

    @staticmethod
    def get_mov_ids_not_linked_due_to_multiple_transfers(
            account_id: int,
            amount: float,
            operational_date_str: str = None,
            value_date_str: str = None) -> List[int]:
        """Get movements not linked to transfer due to multiple possible transfers"""

        # AVIA customer requirement specifies that ValueDate must be used for linking movements and transfers as
        # OperatinalDate from the bank can mismatch for transfers and movements
        operational_date_param = "\'{}\'".format(operational_date_str) if operational_date_str else 'NULL'
        value_date_param = "\'{}\'".format(value_date_str) if value_date_str else 'NULL'

        q = """ 
            -- get movements not linked due to multiple transfers for account_id={account_id}
            
            EXEC [tesoralia].[ONLINE].[GetStatementsNotLinkedDueToMultipleTransfers]
                @AccountId={account_id},
                @OperationalDate={operational_date_param}, 
                @ValueDate={value_date_param},
                @Amount={amount}; 
        """.format(
            account_id=account_id,
            operational_date_param=operational_date_param,
            value_date_param=value_date_param,
            amount=amount
        )

        result = process_query(q)
        return [row['InitialId'] for row in result]

    @staticmethod
    def get_transf_ids_not_linked_due_to_multiple_statements(
            account_id: int,
            amount: float,
            operational_date_str: str = None,
            value_date_str: str = None) -> List[int]:
        """Get transfers ids not linked to transfer due to multiple
        possible statements for an account, amount and date
        """

        # AVIA customer requirement specifies that ValueDate must be used for linking movements and transfers as
        # OperatinalDate from the bank for transfers and movements can mismatch
        # 30/12/2020
        operational_date_param = "\'{}\'".format(operational_date_str) if operational_date_str else 'NULL'
        value_date_param = "\'{}\'".format(value_date_str) if value_date_str else 'NULL'

        q = """
            -- get ids of transfers not linked due to multiple statements
            
            EXEC [tesoralia].[ONLINE].[GetTransfersIdsNotLinkedDueToMultipleStatements]
                @AccountId={account_id}, 
                @OperationalDate={operational_date_param},
                @ValueDate={value_date_param},
                @Amount={amount}
        """.format(
            account_id=account_id,
            operational_date_param=operational_date_param,
            value_date_param=value_date_param,
            amount=amount
        )
        result = process_query(q)
        transf_ids = [row['Id'] for row in result]
        return transf_ids

    @staticmethod
    def get_transfers_not_linked_due_to_multiple_statements_by_value_date() -> List[
        GroupOfTransfersNotLinkedMultipleMovs]:
        """Get transfers not linked to statements due to multiple possible statements"""

        # AVIA customer requirement specifies that
        # ValueDate must be used for linking movements and transfers as
        # OperatinalDate from the bank for transfers and movements can mismatch

        # EXTENDED: EXEC [tesoralia].[ONLINE].[GetTransfersNotLinkedDueToMultipleStatements_By_ValueDate]
        q = '''
            -- get transfers not linked due to multiple statements
            SELECT
                COUNT(*) AS FILAS, 
                TS.AccountId, 
                TA.FinancialEntityAccountId, 
                CONVERT(VARCHAR, TS.ValueDate, 103) AS ValueDate, 
                TS.Amount
            FROM
                [lportal].[dbo].[_TesoraliaTransferStatement] TS
            INNER JOIN [lportal].[dbo].[_TesoraliaAccounts] TA on TS.AccountId = TA.Id
            WHERE
                    TS.IdStatement = 'Multiple vinculacion'
            GROUP BY
                TS.AccountId, TA.FinancialEntityAccountId, TS.ValueDate, TS.Amount
            HAVING COUNT(*) > 1;
        '''
        # ValueDate is a str like '31/12/2019'
        result = process_query(q)
        transf_groups = [GroupOfTransfersNotLinkedMultipleMovs(
            FILAS=row['FILAS'],
            AccountId=row['AccountId'],
            FinancialEntityAccountId=row['FinancialEntityAccountId'],
            ValueDate=row['ValueDate'],
            Amount=round(float(row['Amount']), 2)
        ) for row in result]
        return transf_groups


class N43Funcs:

    @staticmethod
    @deprecated(reason='must use get_n43_last_date_and_account_status')
    def get_n43_last_date_of_account(fin_ent_account_id: str) -> Optional[datetime.datetime]:
        # SELECT cuenta,saldodivisa,fechaultimomovimiento,importeultimomovimiento,
        # cuentaficos,FechaCierreUltExtracto
        # FROM [informes].[dbo].[VISTA_INFORME_POSICION_DIARIA_ANALISIS_EURO];

        q = """ 
        -- get_n43_last_mov_date_for_account for {cuenta}
        
        SELECT FechaCierreUltExtracto
        FROM [informes].[dbo].[VISTA_INFORME_POSICION_DIARIA_ANALISIS_EURO]
        WHERE cuenta = '{cuenta}';
        """.format(
            cuenta=fin_ent_account_id
        )

        results = process_query(q)
        if results:
            return results[0]['FechaCierreUltExtracto']

        return None

    @staticmethod
    def get_n43_last_date_and_account_status(
            db_customer_id: int,
            fin_ent_account_id: str) -> Optional[Tuple[Optional[datetime.datetime], bool]]:
        """:return: (LastN43StatementDateOpt, IsAccountActiveOpt)"""
        q = """ 
        -- get_n43_last_date_and_account_status for {fin_ent_account_id}
        
        GetLastStatementDateFromAccount_N43 @CustomerId={CustomerId}, @AccountNo='{fin_ent_account_id}';
        """.format(
            CustomerId=db_customer_id,
            fin_ent_account_id=fin_ent_account_id
        )

        # None
        # None, 0
        # datetime, 1
        results = process_query(q)
        if results:
            return results[0]['LastStatementDate'], bool(results[0]['ActiveAccount'])

        return None

    @staticmethod
    @deprecated('accesos_Log is used')
    def add_n43_successful_results_for_access(
            customer_financial_entity_access_id: int,
            started_at: datetime.datetime,
            num_files: int) -> bool:
        q = """
        -- add_successful_historical_n43_results_for_access {accesosClienteId}
        
        INSERT INTO dbo.accesos_HistDescargas_N43_online (
            accesosClienteId,
            timeStamp,
            numFiles
            )
        VALUES (
            {accesosClienteId},
            '{timeStamp}',
            {numFiles}
            );""".format(
            accesosClienteId=customer_financial_entity_access_id,
            # Similar to DB_TIMESTAMP_FMT but w/o millis
            # for better correlation with file names:
            #   TES-<< entidadName >>-<< accesosClienteId >>
            #   -<<Execution date YYYYMMDD>>-<<Execution started time HHMMSS>>
            #   -Incremental counter for this execution
            # e.g.
            # TES-SANTANDER-22938-20201025-160653-1.N43
            # where
            # 20201025 - date
            # 160653 - time
            # in DB:
            # 2020-10-25 16:06:53.000
            timeStamp=started_at.strftime('%Y%m%d %H:%M:%S'),
            numFiles=num_files
        )

        process_query(q)

        return True

    @staticmethod
    def get_n43_last_successful_result_date_of_access(
            customer_financial_entity_access_id: int) -> Optional[datetime.datetime]:
        """Returns the date of the latest successful results for n43 downloading
        (access-level results).
        It's then used to skip some accesses if already there are successful today results
        """

        q = """
        -- get_access_n43_last_successful_result_date {Access}
        
        SELECT TOP 1 Date FROM dbo.accesos_Log
        WHERE Access={Access}
            AND Status='SUCCESS'
            AND Logger='{Logger}'
        ORDER BY Id DESC;
        """.format(
            Access=customer_financial_entity_access_id,
            Logger=project_settings.DB_LOGGER_NAME_N43
        )

        results = process_query(q)
        if results:
            return results[0]['Date']

        return None


class MT940Funcs:

    @staticmethod
    def get_mt940_last_successful_result_date_of_access(
            customer_financial_entity_access_id: int) -> Optional[datetime.datetime]:
        """Returns the date of the latest successful results for mt940 downloading"""

        q = """
        -- get_mt940_last_successful_result_date_of_access {Access}
        
        SELECT TOP 1 Date FROM dbo.accesos_Log
        WHERE Access={Access}
            AND Status='SUCCESS'
            AND Logger='{Logger}'
        ORDER BY Id DESC;
        """.format(
            Access=customer_financial_entity_access_id,
            Logger=project_settings.DB_LOGGER_NAME_MT940
        )

        results = process_query(q)
        if results:
            return results[0]['Date']

        return None

    @staticmethod
    def get_mt940_last_date_and_account_status(
            db_customer_id: int,
            account_no: str) -> Optional[Tuple[Optional[datetime.datetime], bool]]:
        """
        :param db_customer_id:
        :param account_no: IBAN
        :return: opt(LastMT940StatementDateOpt, IsAccountActive)"""
        q = """ 
        -- get_mt940_last_date_and_account_status for {account_no}
        
        GetLastStatementDateFromAccount_MT940 @CustomerId={CustomerId}, @AccountNo='{account_no}';
        """.format(
            CustomerId=db_customer_id,
            account_no=account_no,
        )

        # None
        # None, 0
        # datetime, 1
        results = process_query(q)
        if results:
            return results[0]['LastStatementDate'], bool(results[0]['ActiveAccount'])

        return None


class MovementTPVFuncs:

    @staticmethod
    def get_date_from_for_tpv(company_no: str) -> Optional[datetime.datetime]:
        q = """
        -- get_date_from_for_tpv for company {company_no}
        
        SELECT TOP 1 Fecha FROM dbo._TesoraliaTPV
        WHERE NoComercio={company_no}
        ORDER BY Id DESC;""".format(
            company_no=company_no
        )
        results = process_query(q)
        if results:
            return results[0]['Fecha']

        return None

    @staticmethod
    def get_last_movement_tpv(financial_entity_access_id: int, company_no: str) -> Optional[MovementTPV]:
        q = """
        -- get_last_movement_tpv for company {company_no}
        
        SELECT TOP 1 * FROM dbo._TesoraliaTPV
        WHERE NoComercio='{company_no}'
              AND AccessId={access_id}  
        ORDER BY Id DESC;""".format(
            company_no=company_no,
            access_id=financial_entity_access_id
        )
        results = process_query(q)
        if not results:
            return None

        res = results[0]
        # Convert to MovementTPV here to compare with incoming movements
        mov_tpv = MovementTPV(
            NoComercio=res['NoComercio'],
            Fecha=res['Fecha'],
            NumeroTerminal=res['NumeroTerminal'],
            TipoOperacion=res['TipoOperacion'],
            NumeroPedido=res['NumeroPedido'],
            ResultadoOperacion=res['ResultadoOperacion'],
            Importe=res['Importe'],  # str
            ImporteNeto=res['ImporteNeto'],  # str
            CierreSesion=res['CierreSesion'],
            TipoPago=res['TipoPago'],
            NumeroTarjeta=res['NumeroTarjeta'],
            Titular=res['Titular'],
        )
        return mov_tpv

    @staticmethod
    def _movements_new(
            movements_tpv: List[MovementTPV],
            mov_tpv_last_saved: Optional[MovementTPV]) -> List[MovementTPV]:
        """Returns new movements after mov_tpv_last_saved"""
        if mov_tpv_last_saved is None:
            return movements_tpv

        movements_tpv_new = []  # type: List[MovementTPV]
        found_new_movs_point = False
        for mov in movements_tpv:
            # Add all movements after found_new_movs_point detection
            if found_new_movs_point:
                movements_tpv_new.append(mov)
                continue
            # New point not found yet
            if mov == mov_tpv_last_saved:
                found_new_movs_point = True
        # No intersection with previously scraped movements (mostly due to manual time frame) -
        # that means all scraped are new
        if not found_new_movs_point:
            movements_tpv_new = movements_tpv
        return movements_tpv_new

    @staticmethod
    def add_new_movements_tpv(
            financial_entity_access_id: int,
            company_no: str,
            movements_tpv_asc: List[MovementTPV]) -> None:
        """
        Adds only new movements_tpv_asc. Drops previously saved movements
        NOTE: update_user_scraping_state() is used by main_launcher to
        provide user-level defence against double insertion from
        simultaneously launched different instances of main_launcher_tpv.

        :param financial_entity_access_id:
        :param company_no: company number
        :param movements_tpv_asc: ASC ordering!
        """
        mov_tpv_last_saved = MovementTPVFuncs.get_last_movement_tpv(financial_entity_access_id, company_no)
        movements_tpv_new = MovementTPVFuncs._movements_new(movements_tpv_asc, mov_tpv_last_saved)
        if not movements_tpv_new:
            return None

        batches = _split_list(movements_tpv_new, project_settings.MOVEMENTS_TO_UPLOAD_BATCH_SIZE)
        for movement_tpv_batch in batches:
            q = """
            -- add_new_movements_tpv for company_no {company_no}
            INSERT INTO _TesoraliaTPV (
                Fecha, -- datetime    not null,
                NumeroTerminal, --  int         not null,
                TipoOperacion, -- varchar(50) not null,
                NumeroPedido, -- varchar(50) not null,
                ResultadoOperacion, -- varchar(50) not null,
                Importe, --  varchar(50) not null,
                ImporteNeto, -- varchar(50),
                CierreSesion, --  nvarchar(50),
                TipoPago, --  nvarchar(50),
                NumeroTarjeta, --  nvarchar(50),
                Titular, --  nvarchar(max),
                FechaExport, -- datetime
                FechaRegistro, -- datetime    not null,
                AccessId, -- int         not null,
                NoComercio -- varchar(50) not null
            ) VALUES
            """.format(
                company_no=company_no
            )
            now = date_funcs.now_for_db()
            for mov_tpv in movement_tpv_batch:
                q_params = mov_tpv._asdict()
                q_params['Fecha'] = datetime.datetime.strftime(
                    mov_tpv.Fecha,
                    project_settings.DB_TIMESTAMP_FMT
                )[:-3]
                # Handle optional vals
                # Note: ImporteNeto is str (i.e. 'EUR')!
                for param_name in ['ImporteNeto', 'CierreSesion', 'TipoPago', 'NumeroTarjeta', 'Titular']:
                    val = q_params[param_name]
                    val_wrapped = 'NULL' if val is None else "'{}'".format(extract.escape_quote_for_db(val))
                    q_params['{}Wrapped'.format(param_name)] = val_wrapped

                q += """
                    (
                        '{Fecha}', 
                        {NumeroTerminal},
                        '{TipoOperacion}',
                        '{NumeroPedido}',
                        '{ResultadoOperacion}',
                        '{Importe}',
                        {ImporteNetoWrapped},
                        {CierreSesionWrapped},
                        {TipoPagoWrapped},
                        {NumeroTarjetaWrapped},
                        {TitularWrapped},
                        NULL,  -- FechaExport
                        '{FechaRegistro}',
                        {access_id},
                        '{NoComercio}'
                    ),
                """.format(
                    **q_params,
                    access_id=financial_entity_access_id,
                    FechaRegistro=now
                )
            q = re.sub(r'(?s),\s+$', '', q)
            # insert batch
            process_query(q)
        # end for .. in movements_tpv_asc

        return None


class DBTransactionalOperations:

    @staticmethod
    def save_check_collection_transactional(check_collection_scraped: CheckCollectionScraped,
                                            checks_scraped: List[CheckScraped],
                                            customer_id: int) -> Tuple[bool, str]:
        result = True
        error_msg = ""
        conn = get_conn()
        try:

            """ ************************************************ 
            *************** INIT TRANSACTION ******************* 
            ************************************************ """

            conn.autocommit = False
            # cursor = conn.cursor()

            DocumentFuncs.delete_check_collection(check_collection_scraped.KeyValue, customer_id)

            collection_id = DocumentFuncs.add_check_collection(check_collection_scraped)

            for check_scraped in checks_scraped:
                DocumentFuncs.add_check(check_scraped, collection_id)

            conn.commit()

            """ ************************************************ 
            *************** END TRANSACTION ******************** 
            ************************************************ """
        except Exception as error:
            conn.rollback()
            log_err('[ERROR_TES][db_funcs.py] -> [save_check_collection_transactional] -> {}'.format(error))
            result = False
            error_msg = str(error)

        finally:
            return result, error_msg

    @staticmethod
    def save_or_update_leasing_contract_transactional(leasing_contract: LeasingContractScraped,
                                                      fees_scraped: List[LeasingFeeScraped],
                                                      customer_id: int) -> Tuple[bool, str]:

        result = True
        error_msg = ""
        conn = get_conn()
        try:

            """ ************************************************ 
            *************** INIT TRANSACTION ******************* 
            ************************************************ """

            conn.autocommit = False
            DocumentFuncs.delete_leasing_contract_and_fees(leasing_contract)
            contract_id = DocumentFuncs.add_or_update_leasing_contract(leasing_contract)

            for fee_scraped in fees_scraped:
                # DocumentFuncs.delete_leasing_fee(fee_scraped.KeyValue)
                # DocumentFuncs.add_leasing_fee(fee_scraped, contract_id)
                DocumentFuncs.add_or_update_leasing_fee(fee_scraped, contract_id)

            conn.commit()

            """ ************************************************ 
            *************** END TRANSACTION ******************** 
            ************************************************ """
        except Exception as error:
            conn.rollback()
            log_err('[ERROR_TES][db_funcs.py] -> [save_or_update_leasing_contract_transactional] -> {}'.format(error))
            result = False
            error_msg = str(error)

        finally:
            return result, error_msg

    @staticmethod
    def save_transfers_transactional(
            account_id: int,
            transfers_scraped: List[TransferScraped]) -> Tuple[bool, str]:

        result = True
        error_msg = ""
        conn = get_conn()
        cursor = conn.cursor()
        try:

            """ ************************************************ 
            *************** INIT TRANSACTION ******************* 
            ************************************************ """

            conn.autocommit = False

            for transfer_scraped in transfers_scraped:
                TransfersFuncs.add_transfer(cursor, transfer_scraped)
            TransfersFuncs.update_last_scraped_transfers_time_stamp(cursor, account_id)

            conn.commit()
            """ ************************************************ 
            *************** END TRANSACTION ******************** 
            ************************************************ """
        except Exception as error:
            conn.rollback()
            log_err('[db_funcs.py] -> [save_transfers_transactional] -> {}'.format(error))
            result = False
            error_msg = str(error)

        finally:
            conn.autocommit = True
            return result, error_msg


class DBLoggerFuncs:
    @staticmethod
    def add_log_to_accesos_log(
            launcher_id: str,
            logger_name: str,
            level: str,
            message: str,
            exception_str: Optional[str],
            fin_entity_name: Optional[str],
            customer_id: Optional[int],
            customer_financial_entity_access_id: Optional[int],
            status: str = None) -> None:
        """
        Insert a new log into accesos_Log table
        """
        q_params = {}
        q_params['Thread'] = launcher_id
        q_params['Level'] = level
        q_params['Logger'] = extract.escape_quote_for_db(logger_name)
        q_params['Message'] = extract.escape_quote_for_db(message)
        q_params['ExceptionWrapped'] = _str_or_null_for_db(exception_str)
        q_params['ClientWrapped'] = _str_or_null_for_db(customer_id)
        q_params['StatusWrapped'] = _str_or_null_for_db(status)
        q_params['AccessWrapped'] = _str_or_null_for_db(customer_financial_entity_access_id)
        q_params['EntityWrapped'] = _str_or_null_for_db(fin_entity_name)

        q = """
               -- add_log_to_accesos_log with msg  {Message}
    
                INSERT INTO [lportal].[dbo].[accesos_Log]
                   (Date
                   ,Thread
                   ,Level
                   ,Logger
                   ,Message
                   ,Exception
                   ,Client
                   ,Status
                   ,Access
                   ,Entity)
                VALUES (
                   GETDATE(),
                   '{Thread}',
                   '{Level}',
                   '{Logger}',
                   '{Message}',
                   {ExceptionWrapped},
                   {ClientWrapped},
                   {StatusWrapped},
                   {AccessWrapped},
                   {EntityWrapped}
            )""".format(**q_params)

        process_query(q)
        return


class POSFuncs:

    @staticmethod
    def get_trade_points(customer_financial_entity_access_id: int) -> List[POSTradePoint]:
        q = """
        -- get trade points for access {access}
        SELECT Id, IdComercio, Activo, FechaDescarga, FechaRegistro, accesosClienteId, FechaUltimaDescargaCorrecta
        FROM _TesoraliaPOSFinancialIdComercio
        WHERE Activo=1
        """.format(
            access=customer_financial_entity_access_id
        )
        results = process_query(q)
        trade_points = [
            POSTradePoint(
                Id=t['Id'],
                AccessId=t['accesosClienteId'],
                CommercialId=t['IdComercio'],
                Active=t['Activo'],
                CreateTimeStamp=t['FechaRegistro'],
                DownloadTimeStamp=t['FechaDescarga'],
                LastDownloadedOperationalDate=t['FechaUltimaDescargaCorrecta'].date(),
            )
            for t in results
        ]
        return trade_points

    @staticmethod
    def update_trade_point(trade_point: POSTradePoint) -> bool:
        q = """
        -- update trade point {CommercialId}
        UPDATE _TesoraliaPOSFinancialIdComercio
        SET
            Activo = {Activo},
            FechaDescarga = getdate(),
            FechaUltimaDescargaCorrecta = '{LastDownloadedOperationalDate}'
        WHERE Id={Id}
        """.format(
            Id=trade_point.Id,
            CommercialId=trade_point.CommercialId,
            Activo=int(trade_point.Active),
            LastDownloadedOperationalDate=trade_point.LastDownloadedOperationalDate.strftime(
                project_settings.DB_DATE_FMT
            )
        )
        _res = process_query(q)
        return True

    @staticmethod
    def update_pos_access_ts(financial_entity_access_id: int) -> bool:
        q = """
        -- update pos access ts for {accesosClienteId}
        UPDATE _TesoraliaPOSFinancialCollectionsAccess
        SET
            UpdateTimeStamp = getdate()
        WHERE accesosClienteId={accesosClienteId}
        """.format(
            accesosClienteId=financial_entity_access_id
        )
        _res = process_query(q)
        return True

    @staticmethod
    def add_new_pos_collections_wo_movs(db_customer_id: int, pos_collections: List[POSCollection]) -> bool:
        q = """
        -- add new pos collections {}
        """.format([c.ref for c in pos_collections])

        for pos_collection in pos_collections:
            assert pos_collection.oper_date
            q += """
                IF NOT EXISTS 
                    (SELECT POSFinancialCollectionId
                     FROM dbo._TesoraliaPOSFinancialCollections  
                     WITH (NOLOCK)
                     WHERE
                        POSFinancialCollectionReference = '{POSFinancialCollectionReference}' AND
                        CustomerId = {CustomerId} AND
                        NumLines = {NumLines} AND
                        Base = {Base} AND
                        Commission = {Commission} AND
                        OperationalDate = '{OperationalDate}'
                    )
                BEGIN
                    INSERT INTO dbo._TesoraliaPOSFinancialCollections (
                        POSFinancialCollectionReference,
                        CustomerId,
                        NumLines,
                        Base,
                        Commission,
                        Amount,
                        RegisterDate,
                        OperationalDate,
                        AccountId,
                        StatementId,
                        TotalDCC
                    ) VALUES (
                        '{POSFinancialCollectionReference}',
                        {CustomerId},
                        {NumLines},
                        {Base},
                        {Commission},
                        {Amount},
                        getdate(),
                        '{OperationalDate}',
                        {AccountId},
                        {StatementId},
                        {TotalDCC}
                    )
                END        
            """.format(
                POSFinancialCollectionReference=pos_collection.ref,
                CustomerId=db_customer_id,
                NumLines=len(pos_collection.movements),
                Base=pos_collection.base,
                Commission=pos_collection.commission,
                Amount=pos_collection.amount,
                OperationalDate=pos_collection.oper_date.strftime(project_settings.DB_DATE_FMT),
                AccountId=-1,  # indicates: no binding
                StatementId=-1,  # indicates: no binding
                TotalDCC=0,  # no real data
            )
        _res = process_query(q)
        return True

    @staticmethod
    def add_new_pos_movements(db_customer_id: int, pos_collection: POSCollection) -> bool:
        if not pos_collection.movements:
            return True

        assert pos_collection.oper_date

        q = """
        -- add new pos movements for collection {ReferenceCollection}
        
        DECLARE @POSFinancialCollectionId BIGINT;
        SELECT
            @POSFinancialCollectionId = POSFinancialCollectionId
        FROM dbo._TesoraliaPOSFinancialCollections
        WITH (NOLOCK)
        WHERE
            POSFinancialCollectionReference = '{ReferenceCollection}' AND
            OperationalDate = '{Date}';
        """.format(
            Date=pos_collection.oper_date.strftime(project_settings.DB_DATE_FMT),
            ReferenceCollection=pos_collection.ref,
        )
        for m in pos_collection.movements:
            q += """
                IF NOT EXISTS
                (SELECT POSFinancialCollectionsStatementId
                    FROM dbo._TesoraliaPOSFinancialCollectionsStatements
                    WITH (NOLOCK)
                    WHERE
                        Date = '{Date}' AND
                        Hour = '{Hour}' AND
                        IDComercio = {IDComercio} AND
                        CardNumber = '{CardNumber}' AND
                        Position = {Position} AND
                        Amount = {Amount} AND
                        POSFinancialCollectionId = @POSFinancialCollectionId AND
                        ReferenceCollection = '{ReferenceCollection}'
                )
            BEGIN
            INSERT INTO dbo._TesoraliaPOSFinancialCollectionsStatements (
                Date,
                Hour,
                IDComercio,
                CardNumber,
                StatementType,
                Position,
                Amount,
                POSFinancialCollectionId,
                AbonoDCC,
                PercentajesCommission,
                AmountCommission,
                Currency,
                ReferenceCollection,
                fechaRegistro,
                CustomerId
            ) VALUES (
                '{Date}',
                '{Hour}',
                {IDComercio},
                '{CardNumber}',
                '{StatementType}',
                {Position},
                {Amount},
                @POSFinancialCollectionId,
                {AbonoDCC},
                '{PercentajesCommission}',
                {AmountCommission},
                '{Currency}',
                '{ReferenceCollection}',
                getdate(),
                {CustomerId}
            )
            END
            """.format(
                Date=m.date.strftime(project_settings.DB_DATE_FMT),
                Hour=m.time,
                IDComercio=pos_collection.trade_point_id,
                CardNumber=m.card_number,
                StatementType=m.descr,
                Position=m.date_position,
                Amount=m.amount,
                AbonoDCC=0,  # no real data
                PercentajesCommission=m.commission_percent,
                AmountCommission=m.commission_amount,
                Currency=m.currency,
                ReferenceCollection=m.collection_ref,
                CustomerId=db_customer_id,
            )

        _res = process_query(q)
        return True

    @staticmethod
    def link_to_general_movement(db_customer_id: int, pos_collection: POSCollection) -> Tuple[bool, str]:
        assert pos_collection.oper_date
        q1 = """
            -- link pos collection {CollectionReference} step 1
            
            SELECT InitialId, AccountId
            FROM dbo._TesoraliaStatements s
                INNER JOIN dbo._TesoraliaAccounts a 
                ON s.AccountId = a.Id
            WHERE
                OperationalDate >= '{OperationalDate}' AND
                CustomerId = {CustomerId} AND
                Amount = {Amount} AND
                StatementDescription LIKE '%{CollectionReference}%';
        """.format(
            # Allows to find movement near the dats
            OperationalDate=(pos_collection.oper_date -
                             datetime.timedelta(days=1)).strftime(project_settings.DB_DATE_FMT),
            # pos_collection.base (before commission) to _TesoraliaStatements.Amount!
            Amount=pos_collection.base,
            CustomerId=db_customer_id,
            CollectionReference=pos_collection.ref,
        )
        results1 = process_query(q1)
        if not results1:
            return False, "no movement reference to {}".format(pos_collection.ref)
        if len(results1) > 1:
            return False, "several movements are referencing to POS collection {}: {}".format(
                pos_collection.ref,
                results1
            )
        mov_id, account_id = results1[0]['InitialId'], results1[0]['AccountId']

        q2 = """
            -- link pos collection {CollectionReference} step 2
            
            UPDATE dbo._TesoraliaPOSFinancialCollections
            SET StatementId = {InitialId},
                AccountId = {AccountId}
            WHERE POSFinancialCollectionReference = '{CollectionReference}'
        """.format(
            InitialId=mov_id,
            AccountId=account_id,
            CollectionReference=pos_collection.ref
        )
        _results2 = process_query(q2)
        return True, ''
