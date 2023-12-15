import datetime
import hashlib
import json
import os
import threading
import traceback
from collections import OrderedDict
from concurrent import futures
from datetime import timedelta
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from deprecated import deprecated

from custom_libs import list_funcs
from custom_libs import date_funcs
from custom_libs import pdf_funcs
from custom_libs import zip_arch_funcs
from custom_libs.account_no_legal_format_per_country_detector import is_legal_format_for_country
from custom_libs.db.db_connector_for_scraper import DBConnector
from custom_libs.db.db_logger import DBLogger
from custom_libs.myrequests import MySession, Response
from custom_libs.scrape_logger import ScrapeLogger
from project import custom_types
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    ACCOUNT_TYPE_DEBIT, AccountParsed, AccountSavedWithTempBalance, AccountScraped, CheckCollectionParsed,
    CheckCollectionScraped, CheckParsed, CheckScraped, DBAccount, DBFinancialEntityAccess,
    LeasingContractScraped, LeasingFeeParsed, LeasingFeeScraped, MovementParsed, MovementSaved, MovementScraped,
    ScraperParamsCommon, MainResult, DBOrganization,
    CorrespondenceDocParsed, CorrespondenceDocScraped, CorrespondenceDocChecked, DocumentTextInfo,
    DBTransferAccountConfig, TransferScraped, AccountToDownloadCorrespondence, POSTradePoint,
    POSCollection, ResultCode, MT940FileDownloaded, PDF_UNKNOWN_ACCOUNT_NO, BLOCKED_USER_TYPE_COMMON,
    EXPIRED_USER_TYPE_COMMON, PASSWORD_CHANGE_TYPE_COMMON, DOCUMENT_TYPE_RECEIPT, DOBLE_AUTH_TYPE_WITH_DEACTIVATION
)
from scrapers._basic_scraper import integrity_helpers
from scrapers._basic_scraper import movement_helpers
from users_allow_future_movements import USERS_ALLOW_FUTURE_MOVS

__version__ = '26.39.0'
__changelog__ = """
26.39.0 2023.11.16
basic_check_receipt_doc_to_add: clarified log when its not possible to link PDF to statement
26.38.0 2023.08.24
basic_save_or_update_leasing_contract: save all leasing fees even paid ones
26.37.0 2023.08.24
basic_save_receipt_pdf_as_correspondence: deleted unnecessary method call to _get_cached_org_id
26.36.0 2023.07.31
basic_result_not_logged_in_due_reason: added 2FA with deactivation error control
26.35.0 2023.07.28
basic_fee_scraped_from_fee_parsed: added check for None value in DelayInterest 
26.34.0 2023.07.28
basic_upload_movements_scraped: Don't check balance integrity just insert movements for specific 
accounts (FORCE_UPDATE_MOVEMENTS_ACCOUNTS environment variable):
26.33.0 2023.07.26
basic_is_in_update_over_err_last_movement_saved_not_in_scraped_movements_accounts: fixed default return value to False
26.32.0 2023.07.26
basic_upload_movements_scraped: added environment variable FORCE_UPDATE_MOVEMENTS_ACCOUNTS to update accounts in ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS 
added _get_accounts_to_update_over_err_last_movement_saved_not_in_scraped_movements:
added basic_is_in_update_over_err_last_movement_saved_not_in_scraped_movements_accounts:
26.31.0 2023.07.19
basic_upload_movements_scraped: avoid try_autofix_balance_integrity_error when ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS
26.30.0 2023.07.13
basic_upload_movements_scraped: pass last_saved_movement to check_balance_integrity method
26.29.0 2023.06.23
basic_should_download_receipts: fixed log info
basic_save_receipt_pdf_as_correspondence: deleted deprecated parameter into basic_check_receipt_doc_to_add method call
basic_check_receipt_doc_to_add: 
    deleted deprecated product_to_fin_ent_fn, use account_scraped.FinancialEntityAccountId instead
    fixed log info    
26.28.0 2023.06.13
_init_: created self variable _accounts_to_skip_download_corr
basic_should_download_correspondence_for_account__acc_cond:
    modified correspondence download check logic to download all correspondence except accounts to skip
    deleted unnecessary return
__should_save_corr_scraped: modified correspondence check logic to save all correspondence except accounts to skip
basic_should_download_correspondence__acc_cond: 
    fill self variable _accounts_to_skip_download_corr with accounts to skip correspondence
26.27.0 2023.06.07
basic_save_receipt_pdf_as_correspondence: used DOCUMENT_TYPE_RECEIPT instead of hardcoded 'RECEIPT'
26.26.0 2023.05.23
basic_movements_scraped_from_movements_parsed: added 'Receipt' and 'ReceiptChecksum' fields to movement_scraped creation
basic_download_receipts_common: added 'Receipt' and 'ReceiptChecksum' fields to movs_w_receipt_info creation
basic_save_receipt_pdf_as_correspondence: 
    call to new method basic_check_receipt_doc_to_add instead of basic_check_correspondence_doc_to_add
basic_check_receipt_doc_to_add: new method to separately check receipt insert and get StatementId to link PDF
basic_check_correspondence_doc_to_add: refactored method due to migration of receipt check into a new method
26.25.0 2023.05.16
basic_result_not_logged_in_due_reason: added blocked user error control
26.24.0 2023.05.09
basic_save_receipt_pdf_as_correspondence: 
    moved update Receipt and ReceiptChecksum fields to add_correspondence_doc method
basic_get_correspondence_doc_movement_id: 
    added 'StatementDescription' to 'document_info_pos' tuple to check PDF link to movement
26.23.0 2023.04.27
basic_download_receipts_common: added control to avoid downloading PDFs of movements that already have a PDF linked 
basic_save_receipt_pdf_and_update_db: deleted deprecated method
26.22.0
basic_result_not_logged_in_due_reason: 
    used BLOCKED_USER_TYPE_COMMON and EXPIRED_USER_TYPE_COMMON instead of hard-codes 'blocked' and 'expired' 
26.21.0
basic_result_not_logged_in_due_reason: added expired user error control
26.20.0
basic_result_not_logged_in_due_reason: added blocked user error control
26.19.0
basic_fee_scraped_from_fee_parsed: added DelayedInterest, InvoiceNumber to fee_scraped
26.18.0
basic_check_correspondence_doc_to_add: added param (customer_id) to get right movement_id
26.17.0
basic_should_download_correspondence_for_account__acc_cond: returns 'Empty account' when PDF_UNKNOWN_ACCOUNT_NO
26.16.0
_init_: set date_to_str with self.basic_get_date_to()
26.15.0
basic_get_mt940_dates_and_account_status: date_to_offset param
26.14.0
use renamed list_funcs
26.13.0
basic_get_mt940_dates_and_account_status: returns is_account_level_results
26.12.1
upd log msg
26.12.0
call fill_originals_from_movements_saved with more args for logging
26.11.3
upd log msg
26.11.2
basic_get_mt940_dates_for_access: date_from: use min(date_to, <calc>) to avoid date_from > date_to
26.11.1
basic_check_account_is_active: upd log msg
26.11.0
basic_get_n43_dates_for_access
26.10.0
basic_set_movements_scraping_finished_for_contract_accounts
26.9.0
basic_save_receipt_pdf_as_correspondence: now calls db_connector.set_receipt_info in the end
basic_save_receipt_pdf_and_update_db: 
  deprecated (no usages anymore)
  call set_receipt_info w/o pdf_parsed_text (bcs StatementReceiptDescription field is removed)
26.8.0
basic_save_receipt_pdf_as_correspondence: return explicit 'ok' flag
26.7.0
_is_generic_account: added type hints
basic_should_download_correspondence_for_account__acc_cond:
    use fin_ent_account_id[-9:] as acc_suffix to cover all known cases with short account_id 
    use acc_suffix for all checks (fixes mypy detection)
26.6.0
basic_get_mt940_dates_and_account_status, basic_get_mt940_dates_for_access: date_from = last_success_date + 1day
26.5.0
basic_get_mt940_dates_and_account_status, basic_get_mt940_dates_for_access: date_to = max(date_from, today - 1day)
26.4.0
basic_save_receipt_pdf_and_update_db: param 'has_related_entry_in_doc_table'
26.3.0
basic_save_receipt_pdf_and_update_db: now with params: 'only_update_db', 'pdf_parsed_text'
basic_save_receipt_pdf_as_correspondence: return also pdf checksum for further usage 
26.2.0
upd basic_save_receipt_pdf_as_correspondence:
  optional args, checksum
  fixed: call correspondence_doc_upload with corr_scraped_upd
26.1.0
basic_get_mt940_dates_and_account_status
26.0.0
MT940 support:
  basic_scrape_for_mt940
  self.mt940_files_downloaded
  basic_get_mt940_dates_for_access
  _save_mt940
  _get_number_of_mt940_files_downloaded
25.1.0
basic_upload_accounts_scraped: balances_upload: added fin_entity_id param
25.0.0
basic_upload_movements_scraped:
  more result codes for few movements
  don't use obsolete settings: 
    IS_TRY_AUTOFIX_BALANCE_INTEGRITY_ERROR
    IS_OVERWRITE_MOVEMENTS_ON_RESCRAPING
    IS_UPLOAD_MOVEMENTS_ON_BALANCE_INTEGRITY_ERROR
also see commit FEW_MOVEMENTS_REACHED_DATE_LIMIT
24.9.0
basic_get_date_from: respect max_offset if date_from_param provided
24.8.0
basic_update_related_account_info
24.7.0
basic_get_movements_parsed_w_extra_details: optional callback fn to process mov (seq and par)
24.6.0
SOURCE_CHANNEL
24.5.0
basic_set_movements_scraping_finished: use result_codes
use check_and_mark_possible_inactive_and_upd_attempt_ts
24.4.0
basic_movements_scraped_from_movements_parsed:
  new opt params is_reached_pagination_limit, fin_ent_account_id
  to call movement_helpers.drop_movements_of_oldest_date when necessary
24.3.0
basic_result_credentials_error: now accepts last_resp
24.2.0
basic_update_pos_trade_point: also db_connector.update_pos_access_ts
24.1.0
basic_set_movements_scraping_finished: now accepts 'success' flag for LastSuccessDownload field
basic_upload_movements_scraped: upd for LastSuccessDownload support
24.0.0
POS support:
basic_save_excel_with_movs_pos
basic_get_pos_trade_points
basic_update_pos_trade_point
basic_save_pos_collections
23.19.0 
stubs return True, [] (was False, []) - now suitable for main()
  download_correspondence
  download_checks
  download_receipts
  download_leasing
23.18.0
basic_save_receipt_pdf_as_correspondence: only_update_db option
23.17.0
basic_save_receipt_pdf_as_correspondence
23.16.0
static correspondence_folder_path, correspondence_file_path 
  (to use from outer tools)
23.15.0
basic_upload_movements_scraped: mandatory date_from_str param
23.14.0
basic_upload_movements_scraped: optional date_from_str param
23.13.0
use project_settings.IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS
23.12.0
basic_scrape_for_n43:
  set is_temp_folder_for_n43_files = True
  on manual launching if an access is not for nightly N43 download 
upd log msgs
23.11.0
WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED
23.10.0
basic_should_download_correspondence_for_account
use contains.any_el_endswith
_is_generic_account
23.9.0
use __should_save_corr_scraped to respect scrapeCorrespondence, 
 scrapeGenericCorrespondence, scrapeAccountCorrespondence flags
removed old changelog
23.8.0
future movements for specific customers
23.7.0
basic_get_n43_dates_and_account_status: optional param max_offset
23.6.0
basic_get_n43_dates_and_account_status:
  avoid too old date_from due to 'scraping gaps'
  (when the account was processed, then not, then processed again because of db conf), 
  now date_from always >= date_from_if_new 
23.5.1
fixed log msgs
23.5.0
basic_scrape_for_n43: get and set self.is_temp_folder_for_n43_files
_save_n43: use conditional folder path
23.4.0
basic_scrape_for_n43: get and use self.last_successful_n43_download_dt
23.3.0
basic_movements_scraped_from_movements_parsed: optional reorder_movements_for_dates
23.2.0
basic_get_n43_dates_and_account_status: upd logic (consider non-existent account as inactive)
23.1.0
no db updating from basic_save_n43s_and_update_db_for_access 
renamed basic_save_n43s_and_update_db_for_access -> basic_save_n43s
basic_scrape_for_n43: more log msgs
23.0.1
upd log msg
23.0.0
fin_entity_name
db_logger
basic_scrape_for_n43
n43_contents, n43_texts
"""

basic_lock = threading.Lock()


class BasicScraper:
    scraper_name = 'BasicScraperShouldBeRenamed'
    fin_entity_name = 'UnknownShouldBeRenamed'  # can be used for logging

    # can be redefined in receipt scrapers
    CONCURRENT_PDF_SCRAPING_EXECUTORS = 1

    # forward offset to use from some scrapers for some customers
    FUTURE_MOVEMENTS_OFFSET = 4

    SOURCE_CHANNEL = 'ONLINE'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:

        db_customer = scraper_params_common.db_customer  # type: custom_types.DBCustomer
        self.db_customer_name = db_customer.Name
        # for now (28/03/2019), it expects and handles '0' and '1' options
        self.__should_scrape_extended_descriptions_user_level = bool(int(
            db_customer.ExtendedDescriptionFlag
        ))

        access = scraper_params_common.db_financial_entity_access  # type: DBFinancialEntityAccess

        self.username = access.AccessFirstLoginValue  # type: str
        self.username_second = access.AccessSecondLoginValue  # type: str
        self.userpass = access.AccessPasswordLoginValue  # type: str
        self.access_type = access.FinancialEntityAccessName  # type: str
        self.db_customer_id = access.CustomerId  # type: int
        self.db_financial_entity_access_id = access.Id  # type: int

        self.logger = ScrapeLogger(self.scraper_name,
                                   self.db_customer_id,
                                   self.db_financial_entity_access_id)
        # for DB logging
        self.launcher_id = scraper_params_common.launcher_id  # type: str

        self.req_headers = {'User-Agent': project_settings.DEFAULT_USER_AGENT}
        self.req_proxies = proxies

        self.started_datetime_for_db = date_funcs.now_for_db()
        # to use _get_date_from for each account
        self.date_from_param_str = scraper_params_common.date_from_str  # type: Optional[str]
        self.date_from_param = (
            datetime.datetime.strptime(self.date_from_param_str, project_settings.SCRAPER_DATE_FMT)
            if self.date_from_param_str
            else None
        )  # type: Optional[datetime.datetime]

        self.date_to_param_str = scraper_params_common.date_to_str  # type: Optional[str]
        self.date_to_str = scraper_params_common.date_to_str or date_funcs.today_str()  # type: str
        self.date_to_str = self.basic_get_date_to()  # type: str
        self.date_to = datetime.datetime.strptime(self.date_to_str,
                                                  project_settings.SCRAPER_DATE_FMT)
        # To use in basic_get_date_from_for_correspondence,
        # allows to avoid be affected by changed date_to for future movs
        self.date_to_no_future_movs = self.date_to

        self.started = datetime.datetime.now()
        # keep the list of fin_ent_ids to use in 'possible inactive' detector
        self.accounts_fin_ent_ids = []  # type: List[str]

        # DAF: include FinancialEntityId as self.db_financial_entity_id
        self.db_financial_entity_id = access.FinancialEntityId

        self.should_show_bankoffice, self.should_show_payer = self.db_connector.get_customer_show_bankoffice_payer()
        # used in rare cases to distinguish receipts (mostly nightly) and regular scrapers
        # for now used in __process_movement_wrapper (for BBVA)
        # TODO: set real val here by launcher, not in specific scraper
        #  OR use SCRAPE_ALL_EXT_DESCR_IF_HOUR_LESS (new opt)
        self.is_receipts_scraper = False

        # VB: 2020-03-24: HARDFIX for AVIA
        # if self.db_customer_id == 239949:
        #     project_settings.IS_TRY_AUTOFIX_BALANCE_INTEGRITY_ERROR = False

        # By default it's True until check_account_is_active()
        # is implemented for all scrapers.
        # For those which use `check_account_is_active`, it should be False
        self.update_inactive_accounts = True

        # The list of accounts to process (by FinancialEntityAccountId)
        # restricted from from CLI (env) on startup.
        # It's an extra restriction and doesn't intersect with db-based logic
        # like 'inactive accounts' etc.
        # If empty, then all must be processed.
        # The handler must be implemented in a specific scraper.
        # See doc for _get_accounts_only_to_process().
        # Shape: [fin_ent_acc_id1, fin_ent_acc_id1] or empty
        self.__process_only_accounts = self._get_accounts_only_to_process()

        # Environment variable to update movements if last DB movement is
        # older than MAX_OFFSET BUT balance is correct for new movements
        self.__update_over_err_last_movement_saved_not_in_scraped_movements_accounts = self._get_accounts_to_update_over_err_last_movement_saved_not_in_scraped_movements()

        self.db_logger = self.__init_db_logger()

        # Use more appropriate: n43_contents or n43_texts
        self.n43_contents = []  # type: List[bytes]
        self.n43_texts = []  # type: List[str]
        # Used also for file filtering
        self.last_successful_n43_download_dt = None  # type: Optional[datetime.datetime]
        self.is_temp_folder_for_n43_files = False

        self.mt940_files_downloaded = []  # type: List[MT940FileDownloaded]

        # User-level future movements scraping.
        # To reassign self.date_to and self.date_to_str,
        # use set_date_to_for_future_movs from the target scraper
        self.__allow_future_movs_for_customer = self.db_customer_id in USERS_ALLOW_FUTURE_MOVS  # type: bool
        # Helpers for self.__allow_future_movs_for_customer
        self.__is_passed_date_to_param = bool(scraper_params_common.date_to_str)
        # Set to True only when set_date_to_for_future_movs
        # is called for the customer with permissions
        self.__allow_future_movs_for_access = False

        # For conditional correspondence downloading
        # access-level no-account-related "generic" correspondence flag
        self._should_download_corr_generic = False
        # {db_account_id: fin_ent_account_id} where account-level flags is True
        self._accounts_to_download_corr = dict()  # type: Dict[int, str]
        self._accounts_to_skip_download_corr = dict()  # type: Dict[int, str]

        # dict {org_title: db_org_id}
        # as cached data when it's necessary
        self.__org_titles_to_ids = dict()  # type: Dict[str, int]

        # explicit set of failed fin_ent_account_id
        # only after set_movs_sctaping_finnished? or basic_upload_movements_scraped
        self.success_fin_ent_account_ids = set()  # type: Set[str]

        # To use in integrity checkers (only for case REACHED_.._LIMIT)
        self._min_allowed_date_from = None  # type: Optional[datetime.datetime]

    @property
    def db_connector(self) -> DBConnector:
        """Creates new db connector each time to avoid possible side effects"""
        return DBConnector(self.db_customer_id,
                           self.db_financial_entity_access_id)

    def __init_db_logger(self) -> DBLogger:
        db_logger = DBLogger(
            logger_name=project_settings.DB_LOGGER_NAME,
            db_customer_id=self.db_customer_id,
            db_financial_entity_access_id=self.db_financial_entity_access_id,
            fin_entity_name=self.fin_entity_name,
            launcher_id=self.launcher_id,
        )
        return db_logger

    def __set_min_allowed_date_from(self, min_allowed_date_from: datetime.datetime):
        with basic_lock:
            if self._min_allowed_date_from is None:
                self._min_allowed_date_from = min_allowed_date_from
        return

    def set_db_logger(self, logger_name: str) -> None:
        """Sets a new self.db_logger (with other params)"""
        db_logger = DBLogger(
            logger_name=logger_name,
            db_customer_id=self.db_customer_id,
            db_financial_entity_access_id=self.db_financial_entity_access_id,
            fin_entity_name=self.fin_entity_name,
            launcher_id=self.launcher_id,
        )
        self.db_logger = db_logger

    def set_date_to_for_future_movs(self) -> None:
        """Reassigns date_to for customers who required future movements.
        Call it only from specific scrapers supporting future movements
        """
        if not self.__allow_future_movs_for_customer:
            self.logger.info('Future movements are not allowed for the customer')
            return

        self.__allow_future_movs_for_access = True

        if self.__is_passed_date_to_param:
            self.logger.info('Future movements are allowed, but the scraped called with explicit date_to param, '
                             'will not reassign date_to')
            return

        self.date_to += datetime.timedelta(days=self.FUTURE_MOVEMENTS_OFFSET)
        self.date_to_str = self.date_to.strftime(project_settings.SCRAPER_DATE_FMT)
        self.logger.info('Reassigned date_to={} to scrape future movements'.format(self.date_to_str))
        return

    def _accounts_fin_ent_ids_append(self, account_scraped: AccountScraped) -> None:
        with basic_lock:
            self.accounts_fin_ent_ids.append(account_scraped.FinancialEntityAccountId)

    def _req(self, s: MySession, method: str, *args, **kwargs) -> Response:
        logger_info = kwargs.pop('logger_info') if 'logger_info' in kwargs else ''
        err_signs = kwargs.pop('err_signs') if 'err_signs' in kwargs else []

        if method == 'GET':
            resp = s.get(*args, **kwargs)
        elif method == 'POST':
            resp = s.post(*args, **kwargs)
        else:
            raise Exception('Unrecognized HTTP request method')

        url = args[0]
        for err_sign in err_signs:
            if err_sign in resp.text:
                self.logger.warning('{}\n\n{}\n{}'.format(logger_info, url, resp.text))

        return resp

    def basic_new_session(self) -> MySession:
        return MySession(self.logger)

    def basic_req_headers_updated(self, headers_additional: Dict[str, str]):
        """Returns self.req_headers, updated by headers_additional

        Example:
            resp = s.get(url, headers=self.basic_req_headers_updated({'Referer': resp_logged_in.url}))
        """

        req_headers = self.req_headers.copy()
        req_headers.update(headers_additional)
        return req_headers

    def basic_req_get(self, s: MySession, *args, **kwargs) -> Response:
        """requests.Session GET with logging on error signs (if passed).
        :param s: requests.Session
        :param args: requests.Request positional args
        :param kwargs: requests.Request named args
        AND
            logger_info: str - for logging on err resps
            err_signs: List[str] - signs to detect and log err resps
        :return: requests.Response
        """
        return self._req(s, 'GET', *args, **kwargs)

    def basic_get_resp_json(
            self,
            resp: Response,
            err_msg: str = "Can't get resp_json",
            is_ordered=False) -> Tuple[bool, Union[dict, OrderedDict]]:
        """Safely get resp.json or log the err
        :return (is_success, resp_json_dict)
        """
        try:
            if not is_ordered:
                data = resp.json()
            else:
                data = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp.text)
            return True, data
        except Exception as e:
            self.logger.error(
                "{}\nHANDLED EXCEPTION: {}\nSTATUS CODE: {}\nHEADERS: {}\nRESPONSE TEXT:\n{}".format(
                    err_msg,
                    e,
                    resp.status_code,
                    resp.headers,
                    resp.text
                )
            )
        return False, {}

    def basic_req_post(self, s: MySession, *args, **kwargs) -> Response:
        """requests.Session POST with logging on error signs (if passed)
        :param s: requests.Session
        :param args: requests.Request positional args
        :param kwargs: requests.Request named args
        AND Optional but
            logger_info: str - for logging on err resps
            err_signs: List[str] - signs to detect and log err resps
        :return: requests.Response
        """
        return self._req(s, 'POST', *args, **kwargs)

    def basic_mov_parsed_str(self, movement_parsed: MovementParsed) -> str:
        return 'mov {} (amount={} bal={})'.format(
            movement_parsed['operation_date'],
            movement_parsed['amount'],
            movement_parsed['temp_balance']
        )

    def _get_accounts_only_to_process(self) -> List[str]:
        """To fill self.__process_only_accounts
        Gets the list from env var ACCOUNTS
        Example: ACCOUNTS='ES...,ES...' python main_launcher.py ...
        """
        accounts_only_str = os.getenv('ACCOUNTS', '').strip()
        fin_ent_accounts_ids = []  # type: List[str]
        if accounts_only_str:
            fin_ent_accounts_ids = [a.strip() for a in accounts_only_str.split(',')]
            self.logger.info('Got a restricted list of accounts to process: {}'.format(
                fin_ent_accounts_ids
            ))
        return fin_ent_accounts_ids

    def basic_is_in_process_only_accounts(self, fin_ent_account_id: str) -> bool:
        """Checks __process_only_accounts"""
        if not self.__process_only_accounts:
            return True
        if fin_ent_account_id in self.__process_only_accounts:
            self.logger.info("{}: in 'process_only_accounts' list. "
                             "Should process it".format(fin_ent_account_id))
            return True
        self.logger.info("{}: not in 'process_only_accounts' list. "
                         "Should skip it".format(fin_ent_account_id))
        return False

    def _get_accounts_to_update_over_err_last_movement_saved_not_in_scraped_movements(self) -> List[str]:
        """To fill self.__update_over_err_last_movement_saved_not_in_scraped_movements_accounts
        Gets the list from env var FORCE_UPDATE_MOVEMENTS_ACCOUNTS
        Example: FORCE_UPDATE_MOVEMENTS_ACCOUNTS=<fin_ent_account_id_1>,<fin_ent_account_id_2>.' python main_launcher.py -a access_id_1,acces_id_2
        """
        """To fill self.__update_over_err_last_movement_saved_not_in_scraped_movements_accounts
        Gets FORCE_UPDATE_MOVEMENTS_ACCOUNTS
        Example: FORCE_UPDATE_MOVEMENTS_ACCOUNTS='ES...,ES...' python main_launcher.py ...
        """

        accounts_only_str = os.getenv('FORCE_UPDATE_MOVEMENTS_ACCOUNTS', '').strip()
        fin_ent_accounts_ids = []  # type: List[str]
        if accounts_only_str:
            fin_ent_accounts_ids = [a.strip() for a in accounts_only_str.split(',')]
            self.logger.info('Got a environment configuration FORCE_UPDATE_MOVEMENTS_ACCOUNTS: {}'.format(
                fin_ent_accounts_ids
            ))
        return fin_ent_accounts_ids

    def basic_is_in_update_over_err_last_movement_saved_not_in_scraped_movements_accounts(self, fin_ent_account_id: str) -> bool:
        """Checks __update_over_err_last_movement_saved_not_in_scraped_movements_accounts"""
        if not self.__update_over_err_last_movement_saved_not_in_scraped_movements_accounts:
            return False
        if fin_ent_account_id in self.__update_over_err_last_movement_saved_not_in_scraped_movements_accounts:
            self.logger.info("{}: in 'update_over_err_last_movement_saved_not_in_scraped_movements_accounts' list. "
                             "Should update its movements".format(fin_ent_account_id))
            return True
        self.logger.info("{}: not in 'update_over_err_last_movement_saved_not_in_scraped_movements_accounts' list. "
                         "Should skip updating its movementes".format(fin_ent_account_id))
        return False


    def __get_movements_saved_asc(
            self,
            fin_ent_account_id: str,
            date_from_str: str) -> List[MovementSaved]:
        """ASC means order from older to younger movement
        (dates and IDs are ascending)
        """

        movements_saved = self.db_connector.get_movements_since_date(
            fin_ent_account_id,
            date_from_str
        )
        return movements_saved

    def basic_get_movements_saved_desc_and_checksums(
            self,
            fin_ent_account_id: str,
            date_from_str) -> Tuple[List[MovementSaved], List[str]]:
        """All movements_saved since date_from_str and their spec_checksums

        :returns (movs_saved_desc, checksums_spec_saved_desc)
        """

        movs_saved_desc = list(reversed(self.__get_movements_saved_asc(
            fin_ent_account_id,
            date_from_str
        )))  # type: List[MovementSaved]

        checksums_spec_saved_desc = [
            movement_helpers.get_spec_checksum_for_movement_saved(m)
            for m in movs_saved_desc
        ]  # type: List[str]

        return movs_saved_desc, checksums_spec_saved_desc

    def basic_get_oper_date_position_start(
            self,
            fin_ent_account_id: str,
            movements_parsed_desc: List[MovementParsed],
            movements_saved_desc: List[MovementSaved],
            checksums_saved_desc: List[str],
            minimal_intersection_size: int) -> Tuple[bool, int]:
        """
        ALLOWS TO DO AN INCREMENTAL SCRAPING (scrape as few movements as possible)

        Finds the intersection of saved and just extracted movements.
        Returns the operational_date_position_start to be used as the
        OperationalDatePosition for the oldest of the movements_parsed.

        Returns (True, result) only if there are no amgigious movements.

        Common usage:
        -------------
            movs_saved_desc, checksums_saved_desc = \
                self.basic_get_movements_saved_desc_and_checksums(
                    fin_ent_account_id,
                    date_from_str
                )
            movs_parsed_desc = []
            while paginate:
                movs_parsed_desc_i = ...
                movs_parsed_desc.append(movs_parsed_i)
                is_found, oper_date_position_start = \
                    self.basic_get_oper_date_position_start(
                    fin_ent_account_id,
                    movs_parsed_desc,
                    movs_saved_desc,
                    checksums_saved_desc,
                    MIN_INTERSECTION_SIZE
                )
                if is_found:
                    # No need to log, already informed
                    # Stop the pagination
                    break

            movements_scraped, _ = \
                self.basic_movements_scraped_from_movements_parsed(
                    movements_parsed_desc,
                    date_from_str,
                    # THIS IS THE POINT
                    operational_date_position_start=oper_date_position_start
                )

        returns: (is_found, oper_date_position_start)
        """
        if len(checksums_saved_desc) < minimal_intersection_size + 1:
            return False, 1

        checksums_parsed_desc = [
            self.basic_get_spec_checksum_for_movement_parsed(m)
            for m in movements_parsed_desc
        ]
        if not checksums_parsed_desc:
            return False, 1

        checksum_parsed_oldest = checksums_parsed_desc[-1]
        if checksum_parsed_oldest not in checksums_saved_desc:
            return False, 1

        index_parsed_oldest = checksums_saved_desc.index(checksum_parsed_oldest)
        # Need at least minimal_intersection_size of intersection (1 page usually)
        if index_parsed_oldest < minimal_intersection_size:
            return False, 1

        # Detect different movements inside the intersection
        # We want all equal for at least minimal_intersection_size
        for i in range(minimal_intersection_size):
            if checksums_parsed_desc[-1 - i] != checksums_saved_desc[index_parsed_oldest - i]:
                return False, 1

        mov_saved_since = movements_saved_desc[index_parsed_oldest]
        oper_date_position_start = mov_saved_since.OperationalDatePosition
        self.logger.info(
            '{}: found an intersection with already saved movements: '
            'since date {} and oper_date_position = {}. '
            'No need for further extraction/pagination'.format(
                fin_ent_account_id,
                mov_saved_since.OperationalDate,
                oper_date_position_start,
            )
        )

        return True, oper_date_position_start

    def __autoincrease_offset_if_need(
            self,
            fin_ent_account_id: str,
            date_from_str: str,
            max_autoinctreasing_offset: int) -> str:
        """Get date from the top movement _before_ the date_from_str.

        Reason:
        It is necessary sometimes to scrape movements with different dates
        to be able to fix balance integrity errors
        (because this err appears mostly in the last scraped and saved date).

        It is useful for accounts having big intervals between movs
        (> rescraping_offset) to be able to fix possible balance
        integrity errors.

        :returns date_from_before_str: fmt 30/01/2019
        """

        movements_saved = self.__get_movements_saved_asc(
            fin_ent_account_id,
            date_from_str
        )  # type: List[MovementSaved]

        dates_saved = []  # type: List[str]
        # len(movements_saved) > 0 due to prev checks for acc_last_movs_scrap_finished_date_dt
        for m in movements_saved:
            if m.OperationalDate not in dates_saved:
                dates_saved.append(m.OperationalDate)

        # Good news - there are movements_saved from different days for date_from_str
        if len(dates_saved) > 1:
            return date_from_str

        # Increase offset
        movement_before = self.db_connector.get_one_movement_before_date(
            fin_ent_account_id,
            date_from_str
        )

        if not movement_before:
            return date_from_str

        date_from_before_str = movement_before.OperationalDate

        # Check if date_from_before_str is too old,
        # then just return initial date_from_str
        if (date_funcs.now() - date_funcs.get_date_from_str(date_from_before_str)).days > max_autoinctreasing_offset:
            return date_from_str

        return date_from_before_str

    def basic_get_date_from(
            self,
            fin_ent_account_id: str,
            rescraping_offset: int = None,
            max_offset: int = project_settings.MAX_OFFSET,
            max_autoincreasing_offset: int = project_settings.MAX_AUTOINCREASING_OFFSET) -> str:
        """
        LOGIC
        -----
            IF date_from_param
            THEN start_scrap_from = date_from_param
            ELSE
                IF last_scraped_mov_date
                THEN date_from = last_scraped_mov_date_with_offset_for_rescraping
                ELSE date_from = today_with_offset_for_initial_scraping

            ALSO THEN (if the corresponding arg is provided):
                limit date_from (decrease offset) using max_offset_of_today
                extend date_from (increase offset) using max_autoincreasing_offset

        :param fin_ent_account_id: FinancialEntityAccountId
        :param rescraping_offset: offset in days if there are movs for the account in the DB
        :param max_offset: max offset in days from TODAY (day of scraping)
        :param max_autoincreasing_offset: need to increase offset to have movements_saved
                                          at least from 2 days.
                                          max offset is the offset from TODAY (day of scraping)
                                          due to fin entity restrictions.
                                          If None then project_setting.MAX_AUTOINCREASING_OFFSET is used.
                                          If 0 then option is disabled
                                          Recommended val is 90.

        :returns date str in '30/01/2017' format
        """
        # To use redefined value

        min_allowed_date = date_funcs.offset_dt(max_offset)
        # memo for integrity checkers
        self.__set_min_allowed_date_from(min_allowed_date)

        if not rescraping_offset:
            rescraping_offset = project_settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV

        # Get and use account-level rescraping offset if it's provided
        rescraping_offset_account_level = self.db_connector.get_account_custom_offset(fin_ent_account_id)
        if rescraping_offset_account_level:
            self.logger.info('{}: set account-level custom rescraping offset={} day(s)'.format(
                fin_ent_account_id,
                rescraping_offset_account_level
            ))
            rescraping_offset = rescraping_offset_account_level

        # Handle possible case with incorrect incoming params
        if not fin_ent_account_id:
            # '30/11/2016' format
            return self.date_from_param_str or date_funcs.scrape_dates_before_initially_str()

        # If date_from - start from it respecting max_offset
        if self.date_from_param:
            if min_allowed_date > self.date_from_param:
                self.logger.info("{}: date_from_param={}, but set min allowed date_from={}".format(
                    fin_ent_account_id,
                    self.date_from_param,
                    min_allowed_date.strftime(project_settings.SCRAPER_DATE_FMT)
                ))
            return max(min_allowed_date, self.date_from_param).strftime(project_settings.SCRAPER_DATE_FMT)

        # Get last movements date from DB if exists
        acc_last_movs_scrap_finished_date_dt = (
                self.db_connector.get_last_movements_scraping_finished_date_dt(fin_ent_account_id)
                or None
        )  # type: Optional[datetime.datetime]

        # Initial scraping for the access
        if not acc_last_movs_scrap_finished_date_dt:
            return date_funcs.scrape_dates_before_initially_str()

        # Calculate offset
        date_from_str = date_funcs.scrape_dates_before_on_rescraping_str(
            acc_last_movs_scrap_finished_date_dt,
            rescraping_offset
        )  # type: str

        # Calc limited offset
        date_from_str_limited = date_funcs.limit_date_max_offset(
            date_from_str,
            max_offset
        )

        if date_from_str_limited != date_from_str:
            self.logger.info("{}: got limited date_from={}".format(
                fin_ent_account_id,
                date_from_str_limited
            ))
            date_from_str = date_from_str_limited

        # Don't increase the offset even if necessary
        if max_autoincreasing_offset <= 0:
            return date_from_str

        # Handle autoincreasing_offset
        date_from_before_str = self.__autoincrease_offset_if_need(
            fin_ent_account_id,
            date_from_str,
            max_autoincreasing_offset
        )
        if date_from_before_str != date_from_str:
            self.logger.info("{}: auto-increased date_from={} instead of {}".format(
                fin_ent_account_id,
                date_from_before_str,
                date_from_str
            ))

        return date_from_before_str

    def basic_get_date_to(self) -> str:
        """
        LOGIC
        -----
            IF date_to_param_str
            THEN
                limit date_to (decrease offset) using db_fin_ent_access_date_to_offset
            ELSE
                date_to = today_with_offset_for_initial_scraping

        :returns date str in '30/01/2017' format
        """
        # To use redefined value
        db_financial_entity_access_date_to_offset = self.db_connector.get_financial_entity_access_date_to_offset(
            self.db_financial_entity_access_id
        )

        max_allowed_date_str = date_funcs.limit_date_to_max_offset(
            date_funcs.today_str(),
            db_financial_entity_access_date_to_offset)

        self.logger.info("{}: Max allowed date_to={}, db_fin_ent_access_date_to_offset={}".format(
            self.db_financial_entity_access_id,
            max_allowed_date_str,
            db_financial_entity_access_date_to_offset
        ))

        max_allowed_date = date_funcs.get_date_from_str(max_allowed_date_str)

        if self.date_to_param_str:
            date_to_param = date_funcs.get_date_from_str(self.date_to_param_str)
            if max_allowed_date < date_to_param:
                self.logger.info(
                    "{}: date_to_param={}, but set max allowed date_to={}".format(
                        self.db_financial_entity_access_id,
                        self.date_to_param_str,
                        max_allowed_date_str
                ))
            return min(max_allowed_date, date_to_param).strftime(project_settings.SCRAPER_DATE_FMT)

        self.logger.info("{}: Set max allowed date_to={}".format(
            self.db_financial_entity_access_id,
            max_allowed_date_str
        ))
        return max_allowed_date_str

    def basic_get_date_from_dt(
            self,
            fin_ent_account_id: str,
            rescraping_offset: int = None,
            max_offset: int = project_settings.MAX_OFFSET,
            max_autoincreasing_offset: int = project_settings.MAX_AUTOINCREASING_OFFSET
    ) -> Tuple[datetime.datetime, str]:
        """:returns (date_from, date_from_str)"""
        date_from_str = self.basic_get_date_from(
            fin_ent_account_id,
            rescraping_offset,
            max_offset,
            max_autoincreasing_offset
        )
        return datetime.datetime.strptime(date_from_str, project_settings.SCRAPER_DATE_FMT), date_from_str

    def basic_get_date_from_for_correspondence(
            self,
            offset: int = None,
            max_offset: int = 45) -> Tuple[datetime.datetime, str]:
        """
        :param offset: int days, if None then default will be used
        :param max_offset: int days, max allowed offset (useful if date_from_param_str provided),
                           useful for concrete fin entities
        :returns (date_from, date_from_str) in SCRAPER_DATE_FMT (30/01/2020)
        LOGIC:
            date_from = IF date_from_param provided, then use it
                        ELSE date_to - offset
            ALSO THEN:
            limit date_from to date_from_by_max_allowed_offset
        """
        if offset is None:
            offset = project_settings.SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV

        # Using self.date_to_no_future_movs to handle case when changed date_to for future movements
        date_from = self.date_to_no_future_movs - datetime.timedelta(days=offset)

        if self.date_from_param_str:
            date_from = datetime.datetime.strptime(
                self.date_from_param_str,
                project_settings.SCRAPER_DATE_FMT
            )
        # maybe from today?
        date_from__by_max_offset = self.date_to_no_future_movs - datetime.timedelta(days=max_offset)
        date_from__respect_max_offset = max(date_from__by_max_offset, date_from)

        return date_from__respect_max_offset, date_from__respect_max_offset.strftime(project_settings.SCRAPER_DATE_FMT)

    def basic_get_date_from_for_transfs(
            self,
            acc_w_transfs_active: DBTransferAccountConfig) -> datetime.datetime:
        """
        JFM: if self.date_from_param_str is not provided,
        we process transfers from DOWNLOAD_TRANSFERS_DAYS_BEFORE_DATE_TO days before from "date_to"
        """
        if self.date_from_param_str:
            date_from = datetime.datetime.strptime(self.date_from_param_str, project_settings.SCRAPER_DATE_FMT)
        else:
            if acc_w_transfs_active.LastScrapedTransfersTimeStampWithOffset:
                date_from = acc_w_transfs_active.LastScrapedTransfersTimeStampWithOffset
            else:
                date_from = self.date_to - datetime.timedelta(days=project_settings.DOWNLOAD_TRANSFERS_OFFSET_DAYS)
        return date_from

    def get_active_transfers_accounts(self) -> List[DBTransferAccountConfig]:
        """
        Get all accounts with transfers instrument active
        """
        all_accounts_of_fin_ent_access_w_transfers_active = \
            self.db_connector.get_active_transfers_accounts()  # type:List[DBTransferAccountConfig]
        return all_accounts_of_fin_ent_access_w_transfers_active

    def basic_gen_accounts_scraped_dict(
            self,
            accounts_scraped: List[AccountScraped]) -> Dict[str, AccountScraped]:
        """Generates dict from list with FinancialEntityAccountId as key.
        Useful in process_account if we pass account_parsed as main arg
        """
        accounts_scraped_dict = {account_scraped.FinancialEntityAccountId: account_scraped
                                 for account_scraped in accounts_scraped}  # type: Dict[str, AccountScraped]
        return accounts_scraped_dict

    def __operation_date_dt(self, movement_parsed: MovementParsed) -> datetime.datetime:
        operational_date = date_funcs.convert_date_to_db_format(movement_parsed['operation_date'])  # 20170130
        return datetime.datetime.strptime(operational_date, project_settings.DB_DATE_FMT)

    def basic_movements_scraped_from_movements_parsed(
            self,
            movements_parsed: List[MovementParsed],
            date_from_str: str,
            current_ordering=custom_types.MOVEMENTS_ORDERING_TYPE_DESC,
            bankoffice_details_name='',
            payer_details_name='',
            operational_date_position_start=1,
            reorder_movements_for_dates: List[str] = None,
            is_reached_pagination_limit=False,
            fin_ent_account_id='') -> Tuple[List[MovementScraped], List[MovementParsed]]:

        """Creates movements_scraped with OperationalDatePosition and KeyValue.
        Use it than basic_movement_scraped_from_movement_parsed because need to calculate
        OperationalDatePosition using the list of the movements

        :param movements_parsed: ...
        :param date_from_str: 30/01/2017 format. It is necessary to filter movements by date_from
            to avoid too early movements if they were scraped due to unexpected reason.
            Need it to calculate OperationalDatePosition properly for all movements
            (or for some movements from too early dates would calculate improperly,
            because usually extracts couple instead of full list of too early dates)
        :param current_ordering: ordering of the movements_parsed
        :param bankoffice_details_name: bankoffice param title in extended description
        :param payer_details_name: payer param title in extended description
        :param operational_date_position_start: the position of the 1st movement
        :param reorder_movements_for_dates: optional list of dates with inverted ordering (!),
                                            date_str in the format of dates mov_parsed['operation_date']
        :param is_reached_pagination_limit:
                    if True, then should drop the movements on the oldest date,
                    because hey will have wrong OperationalDatePosition.
                    It's ok to drop the oldest movs w/o changing date_from, because
                    basic_upload_movements_scraped don't use it for balance err checks (ony for reports),
                    example: -a 18620 (> 100 pages w/ movs for 3 days)
        :param fin_ent_account_id: optional for better logging
        :returns List[MovementScraped] ordered ASC
        """
        if not movements_parsed:
            return [], []

        if reorder_movements_for_dates:
            movements_parsed = movement_helpers.reorder_movements_for_dates(
                movements_parsed,
                reorder_movements_for_dates
            )

        acc_logging_param = '' if not fin_ent_account_id else '{}: '.format(fin_ent_account_id)

        movements_scraped_ordered_asc = []  # type: List[MovementScraped]
        date_from_dt = datetime.datetime.strptime(date_from_str, project_settings.SCRAPER_DATE_FMT)
        # Allow future movements only if self.set_date_to_for_future_movs() has been called
        # for the customer with permissions (flag __allow_future_movs_for_access).
        # In other cases don't allow future movs at all
        # (generally to prevent frequent balance integrity error fixes)
        max_date_to_dt = self.date_to if self.__allow_future_movs_for_access else date_funcs.today()
        date_to_dt_by_scraper = datetime.datetime.strptime(self.date_to_str, project_settings.SCRAPER_DATE_FMT)
        date_to_dt = min(date_to_dt_by_scraper, max_date_to_dt)
        if date_to_dt != date_to_dt_by_scraper:
            self.logger.info(
                "{}Changed date_to={} instead of {} for movements_scraped to remove future movements".format(
                    acc_logging_param,
                    date_to_dt,
                    date_to_dt_by_scraper
                )
            )

        movements_parsed_ordered_asc = movement_helpers.order_movements_asc(
            movements_parsed,
            current_ordering
        )

        operational_date_position = operational_date_position_start
        prev_operational_date = date_funcs.convert_date_to_db_format(
            movements_parsed_ordered_asc[0]['operation_date']
        )  # 20170130
        # The list with movs, which are exactly corresponding to movements_scraped list
        # useful for receipts downloading because we don't keep (and shouldn't)
        # necessary information in MovementScraped structure
        movements_parsed_filtered = []  # type: List[MovementParsed]
        is_reached_date_from = False
        movements_parsed_ordered_asc_len = len(movements_parsed_ordered_asc)
        for ix, movement_parsed in enumerate(movements_parsed_ordered_asc):

            amount = movement_parsed['amount']
            temp_balance = movement_parsed['temp_balance']
            operational_date = date_funcs.convert_date_to_db_format(movement_parsed['operation_date'])  # 20170130
            operational_date_obj = datetime.datetime.strptime(operational_date, project_settings.DB_DATE_FMT)

            # Filter too young (future) movements
            # Handle tricky Sabadell cases: future movements between previous dates
            # Examples:
            # -u 92282 -a 2707: ES3900815181030001047607: 05/12/2019-09/12/2019
            # -u 226770 -a 11117 (many from 09/12/2019 between 05/12 and 06/12)
            # -a 16808 acc ES1701825437660208509436
            # VB: since 2020-04-14
            # Skip the rest (break) if got a date of this one > date_to_dt
            # to reduce the number of balance integrity error fixes
            if self.__operation_date_dt(movement_parsed) > date_to_dt:
                break

            # Filter too old movements
            # only if not yet is_reached_date_from
            # to handle case with meshed movements
            # e.g. ES0300810165510002217427 (12.10.2018-15.10.2018)
            # we have movs of 12.10 after movs of 12.10
            # and then again movs of 15.10
            if not is_reached_date_from and (operational_date_obj < date_from_dt):
                continue

            is_reached_date_from = True

            value_date = date_funcs.convert_date_to_db_format(movement_parsed['value_date'])
            description = movement_parsed['description']
            description_extended = movement_parsed.get('description_extended', description)

            # Reset the counter for a new date
            if operational_date != prev_operational_date:
                operational_date_position = 1

            assert operational_date_position

            hashbase = '{}{}{}{}{}'.format(
                operational_date,
                value_date,
                amount,
                temp_balance,
                operational_date_position
            )
            key_value = hashlib.sha256(hashbase.encode()).hexdigest().strip()
            bankoffice = ''
            payer = ''
            if description_extended:
                if self.should_show_bankoffice:
                    bankoffice = movement_helpers.get_details_from_extended_descr(
                        description_extended,
                        bankoffice_details_name
                    )
                if self.should_show_payer:
                    payer = movement_helpers.get_details_from_extended_descr(
                        description_extended,
                        payer_details_name
                    )

            movement_scraped = MovementScraped(
                Amount=amount,
                TempBalance=temp_balance,
                OperationalDate=operational_date,
                ValueDate=value_date,
                # For better integration with generated N43s
                StatementDescription=movement_helpers.clean_description(description),
                StatementExtendedDescription=movement_helpers.clean_description(description_extended),
                OperationalDatePosition=operational_date_position,
                KeyValue=key_value,
                StatementReceiptDescription='',
                StatementReference1='',
                StatementReference2='',
                Bankoffice=bankoffice,
                Payer=payer,
                # Might be updated by fill_originals_from_movements_saved
                CreateTimeStamp=None,
                InitialId=None,
                ExportTimeStamp=None,
                Receipt=None,
                ReceiptChecksum=None
            )

            movements_scraped_ordered_asc.append(movement_scraped)
            movements_parsed_filtered.append(movement_parsed)
            prev_operational_date = operational_date
            operational_date_position += 1

        movements_scraped_ordered_asc_wo_old = movements_scraped_ordered_asc
        if is_reached_pagination_limit:
            movements_scraped_ordered_asc_wo_old, dropped_date = movement_helpers.drop_movements_of_oldest_date(
                movements_scraped_ordered_asc
            )
            if dropped_date:
                self.logger.info(
                    "{}Dropped movements of the oldest date {} due to reached pagination limit. "
                    "It's necessary to keep valid OperationalDatePosition vals".format(
                        acc_logging_param,
                        dropped_date
                    )
                )

        return movements_scraped_ordered_asc_wo_old, movements_parsed_filtered

    def __process_movement_wrapper(self,
                                   s: MySession,
                                   movement_parsed: MovementParsed,
                                   fin_ent_account_id: str,
                                   should_get_extra_for_already_saved: bool,
                                   movements_saved_spec_checksums: Set[str],
                                   meta: Optional[dict] = None,
                                   callback: Optional[Callable] = None) -> Optional[MovementParsed]:
        """Handles should_rescrape_already_saved.

        Compares movements by spec_checkums
        """
        mov_str = self.basic_mov_parsed_str(movement_parsed)

        if should_get_extra_for_already_saved:
            if callback:
                return callback(s, movement_parsed, fin_ent_account_id, meta)
            return self.process_movement(s, movement_parsed, fin_ent_account_id, meta)

        mov_parsed_spec_checksum = self.basic_get_spec_checksum_for_movement_parsed(movement_parsed)
        if mov_parsed_spec_checksum in movements_saved_spec_checksums:
            if not self.is_receipts_scraper:
                self.logger.info("{}: {} already saved, "
                                 "no need to get extra details".format(fin_ent_account_id, mov_str))
                return movement_parsed
            else:
                # Need to download receipts for movements
                # scraped by non-receipt scraper
                self.logger.info(
                    "{}: {} already saved, "
                    "but it's a receipt scraper: "
                    "get extra details".format(fin_ent_account_id, mov_str)
                )
        if callback:
            return callback(s, movement_parsed, fin_ent_account_id, meta)
        return self.process_movement(s, movement_parsed, fin_ent_account_id, meta)

    def basic_get_movements_parsed_w_extra_details(
            self,
            s: MySession,
            movements_parsed: List[MovementParsed],
            account_scraped: AccountScraped,
            date_from_str: str,
            n_mov_details_workers=8,
            should_get_extra_for_already_saved=False,
            meta: dict = None,
            callback: Callable[[MySession, MovementParsed, str, Optional[dict]], Optional[MovementParsed]] = None
    ) -> List[MovementParsed]:
        """Default implementation to get extra details
        for movements if additional HTTP requests are required.
        Calls self.process_movement in concurrent mode with max_workers=n_mov_details_workers

        Usual extra details:
        - extended description + any more

        Mandatory:
        - movement_parsed must have 'id' key
        - self.process_movement must be implemented in the concrete scraper

        The ordering will be obtained from movements_parsed
        Important: if process_movement returns None, then all movements after this None
                   will be dropped (used by BBVA) to keep consistency,
                   thus, only movements_parsed_asc
                   are suitable for the scrapers that can return None

        :param s: session
        :param movements_parsed
        :param account_scraped
        :param date_from_str: date in 30/01/2019 fmt
        :param should_get_extra_for_already_saved: the flag that allows skip re-scraping
               for already saved movements.
               If skip, extended descriptions will not be updated.
               The func uses basic_get_spec_checksums_for_movements_saved
               and then basic_get_spec_checksum_for_movement_parsed to detect already saved ones.
               NOTE: __processs_movement_wrapper then allows
               to re-scrape ext descr in any case if self.is_receipts_scraper = True
               (it is necessary to update movs if ext descr appears not immediately - known BBVA case).
        :param n_mov_details_workers: max workers for concurrent movements processing
        :param meta: any dict that will be passed to self.process_movement()
        :param callback: optional function instead of self.process_movement()
        :returns movements_parsed_extra_details on success OR
                 movements_parsed on failure
        """
        if not self.basic_should_scrape_extended_descriptions():
            return movements_parsed

        lock = threading.Lock()

        movs_parsed_w_extra_details_dict = {}  # type: Dict[str, Optional[MovementParsed]]
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        movements_saved_spec_checksums = set()  # type: Set[str]
        if not should_get_extra_for_already_saved:
            movements_saved_spec_checksums = self.basic_get_spec_checksums_for_movements_saved(
                fin_ent_account_id,
                date_from_str
            )

        if not project_settings.IS_CONCURRENT_SCRAPING or n_mov_details_workers <= 1:
            for mov_parsed in movements_parsed:
                movs_parsed_w_extra_details_dict[mov_parsed['id']] = self.__process_movement_wrapper(
                    s,
                    mov_parsed,
                    fin_ent_account_id,
                    should_get_extra_for_already_saved,
                    movements_saved_spec_checksums,
                    meta,
                    callback
                )
        else:
            if movements_parsed:  # avoid unnecessary initialization if no movs
                with futures.ThreadPoolExecutor(max_workers=n_mov_details_workers) as executor:
                    futures_dict = {
                        executor.submit(self.__process_movement_wrapper,
                                        s,
                                        mov_parsed,
                                        fin_ent_account_id,
                                        should_get_extra_for_already_saved,
                                        movements_saved_spec_checksums,
                                        meta,
                                        callback): mov_parsed['id']
                        for mov_parsed in movements_parsed
                    }

                    # Extract result from the futures
                    for future in futures.as_completed(futures_dict):
                        mov_parsed_id = futures_dict[future]
                        try:
                            mov_parsed_w_extra_details = future.result()
                            with lock:
                                movs_parsed_w_extra_details_dict[mov_parsed_id] = mov_parsed_w_extra_details
                        except:
                            self.logger.error(
                                '{function_title} failed: {mov_parsed_id}: '
                                '!!! EXCEPTION !!! {exc}'.format(
                                    function_title='process_movement',
                                    mov_parsed_id=mov_parsed_id,
                                    exc=traceback.format_exc()
                                )
                            )
                            self.logger.error(
                                '{}: failed to scrape extra details for movs '
                                '(extended descriptions). '
                                'Use w/o extra details'.format(fin_ent_account_id))
                            return movements_parsed

        # Get ordered results
        movements_parsed_w_extra_details = [
            movs_parsed_w_extra_details_dict[mov['id']]
            for mov in movements_parsed
        ]  # type: List[Optional[MovementParsed]]

        # Drop all after the first None
        movements_parsed_w_extra_details_nonones = []  # type: List[MovementParsed]
        for mov in movements_parsed_w_extra_details:
            if mov is None:
                break
            movements_parsed_w_extra_details_nonones.append(mov)

        self.logger.info('{}: got {} movements_parsed_w_extra_details'.format(
            fin_ent_account_id,
            len(movements_parsed_w_extra_details_nonones),
        ))

        return movements_parsed_w_extra_details_nonones

    def basic_account_scraped_from_account_parsed(
            self,
            organization_title: str,
            account_parsed: AccountParsed,
            country_code='ESP',
            account_no_format=custom_types.ACCOUNT_NO_TYPE_IBAN,
            is_default_organization: bool = False) -> AccountScraped:
        """Creates account_scraped. Get data from account_parsed dict or use defaults"""

        now_for_db = date_funcs.now_for_db()
        account_no = account_parsed['account_no']
        account_scraped = AccountScraped(
            # default is 'account_no'
            FinancialEntityAccountId=account_parsed.get('financial_entity_account_id',
                                                        account_no),
            # critical (since 2017-04-23)
            AccountNo=(account_no
                       if is_legal_format_for_country(country_code, account_no_format)
                       else None),
            AccountNoFormat=account_no_format,
            AccountNoCountry=country_code,
            Type=account_parsed.get('account_type', ACCOUNT_TYPE_DEBIT),
            Currency=account_parsed.get('currency', 'EUR'),
            Balance=account_parsed['balance'],
            OrganizationName=organization_title,
            CustomerId=self.db_customer_id,
            BalancesScrapingInProgress=0,
            BalancesScrapingStartedTimeStamp=self.started_datetime_for_db,
            BalancesScrapingFinishedTimeStamp=now_for_db,
            MovementsScrapingInProgress=1,
            MovementsScrapingStartedTimeStamp=now_for_db,
            IsDefaultOrganization=int(is_default_organization),
            IsActiveOrganization=1
        )

        self._accounts_fin_ent_ids_append(account_scraped)
        return account_scraped

    def basic_check_is_account_inactive_by_text_signs(
            self,
            text: str,
            fin_ent_account_id: str,
            inactive_text_signs: List[str]) -> bool:
        """Deletes fin_ent_account_id from self.accounts_fin_ent_ids.
        After this action the account will be marked as inactive during check in the end of the scraping
        due to it will be detected as un-extracted (and un-scraped)
        :return:
            True - inactive
            False - active
        """
        if (fin_ent_account_id in self.accounts_fin_ent_ids) \
                and any(sign in text for sign in inactive_text_signs):
            self.accounts_fin_ent_ids.remove(fin_ent_account_id)
            return True
        return False

    def basic_result_credentials_error(self, last_resp: Response = None) -> MainResult:
        """With side effect!
        Set fin entity inactive first.
        Usage from scraper:
            return self.basic_result_credentials_error()
        """
        if last_resp:
            self.logger.log_credentials_error(last_resp_url=last_resp.url, last_resp_text=last_resp.text)
        else:
            self.logger.log_credentials_error()
        if project_settings.IS_UPDATE_DB:
            self.db_connector.set_financial_entity_access_inactive()
        return result_codes.ERR_WRONG_CREDENTIALS, None

    def basic_result_not_logged_in_due_unknown_reason(self, current_url: str,
                                                      page_source: str) -> MainResult:
        """Usage from scraper:
            return self.basic_result_not_logged_in_due_unknown_reason(url, page_source)
        """
        self.logger.log_non_credentials_error(current_url, page_source)
        return result_codes.ERR_NOT_LOGGED_IN_UNKNOWN_REASON, None

    def basic_result_not_logged_in_due_reason(self, current_url: str,
                                              page_source: str, reason: str = '') -> MainResult:
        """Supports optional reason. If the reason not provided,
        it does the same actions as basic_result_not_logged_in_due_unknown_reason()

        Usage from scraper:
            return self.basic_result_not_logged_in_due_reason(url, page_source, reason)
            OR
            return self.basic_result_not_logged_in_due_reason(url, page_source)
        """
        if not reason:
            self.logger.log_non_credentials_error(current_url, page_source)
            return result_codes.ERR_NOT_LOGGED_IN_UNKNOWN_REASON, None

        self.logger.log_non_credentials_error_w_reason(current_url, page_source, reason)
        if DOBLE_AUTH_TYPE_WITH_DEACTIVATION == reason:
            if project_settings.IS_UPDATE_DB:
                self.db_connector.set_financial_entity_access_inactive()
            return result_codes.ERR_NOT_LOGGED_IN_DETECTED_REASON_DOUBLE_AUTH_WITH_DEACTIVATION, None
        elif any(m in reason.lower() for m in ['2fa', 'sms auth', 'double auth']):
            return result_codes.ERR_NOT_LOGGED_IN_DETECTED_REASON_DOUBLE_AUTH, None
        elif BLOCKED_USER_TYPE_COMMON == reason:
            return result_codes.ERR_BLOCKED_USER, None
        elif EXPIRED_USER_TYPE_COMMON == reason:
            return result_codes.ERR_NOT_LOGGED_IN_DETECTED_REASON_EXPIRED_USER, None
        elif PASSWORD_CHANGE_TYPE_COMMON == reason:
            return result_codes.ERR_NOT_LOGGED_IN_DETECTED_REASON_PASSWORD_CHANGE, None

        return result_codes.ERR_NOT_LOGGED_IN_DETECTED_REASON, None

    def basic_result_success(self):
        """With side effect!
        You should call check_and_mark_maybe_disabled first.
        Usage from scraper:
            return self.basic_success_result()
        """
        if project_settings.IS_UPDATE_DB:
            self.logger.info(
                'Update PossibleInactive for fin ent access id {}: scraped accounts {}'.format(
                    self.db_financial_entity_access_id,
                    self.accounts_fin_ent_ids
                )
            )
            self.db_connector.check_and_mark_possible_inactive_and_upd_attempt_ts(self.accounts_fin_ent_ids)
        return result_codes.SUCCESS, None

    def basic_result_common_scraping_error(self):
        return result_codes.ERR_COMMON_SCRAPING_ERROR, None

    def basic_upload_accounts_scraped(
            self,
            accounts_scraped: List[AccountScraped]):
        """Thread safe, can be used from futures"""
        try:
            if project_settings.IS_UPDATE_DB:
                self.db_connector.balances_upload(
                    accounts_scraped,
                    self.update_inactive_accounts,
                    source_channel=self.SOURCE_CHANNEL,
                    fin_entity_id=self.db_financial_entity_id,
                )
        except:
            self.logger.error(traceback.format_exc())

    def basic_update_related_account_info(
            self,
            account_scraped: AccountScraped,
            related_account_info: str) -> bool:
        self.logger.info('{}: update related account info: set "{}"'.format(
            account_scraped.FinancialEntityAccountId,
            related_account_info
        ))
        if project_settings.IS_UPDATE_DB:
            self.db_connector.update_related_account_info(
                account_scraped.FinancialEntityAccountId,
                related_account_info
            )
        return True

    def __check_and_update_acc_bal_from_mov(self,
                                            account_scraped: AccountScraped,
                                            movements_scraped_ordered_asc: List[MovementScraped]):
        """Handle case when wrong account balance from accounts overview page"""

        self.logger.info(
            '{}: check and update account balance basing on scraped movements: start'.format(
                account_scraped.FinancialEntityAccountId,
            )
        )

        if not movements_scraped_ordered_asc:
            self.logger.info(
                '{}: check and update account balance basing on scraped movements: no movements. Skip check'.format(
                    account_scraped.FinancialEntityAccountId,
                )
            )
            return

        # Get TempBalance of last movement
        account_balance_real = movements_scraped_ordered_asc[-1].TempBalance
        account_balance = account_scraped.Balance

        if account_balance != account_balance_real:
            # Change the account balance!
            account_parsed = {
                'account_no': account_scraped.AccountNo,
                'financial_entity_account_id': account_scraped.FinancialEntityAccountId,
                'account_type': account_scraped.Type,
                'balance': account_balance_real,
                'currency': account_scraped.Currency
            }

            # Re-create account_scraped because it's strict structure, can't modify it
            account_scraped = self.basic_account_scraped_from_account_parsed(
                account_scraped.OrganizationName,
                account_parsed,
                country_code=account_scraped.AccountNoCountry,
                account_no_format=account_scraped.AccountNoFormat,
                is_default_organization=account_scraped.IsDefaultOrganization
            )
            self.basic_upload_accounts_scraped([account_scraped])

            self.logger.info(
                '{}: balance has been updated by balance from last movement: {}'.format(
                    account_scraped.FinancialEntityAccountId, account_balance_real
                )
            )
        else:
            self.logger.info(
                '{}: check and update account balance basing on scraped movements: balance is correct'.format(
                    account_scraped.FinancialEntityAccountId,
                )
            )

    def basic_upload_movements_scraped(self,
                                       account_scraped: AccountScraped,
                                       movements_scraped_ordered_asc: List[MovementScraped],
                                       date_from_str: str) -> bool:
        """Generic method with balance integrity checkers

        Thread safely, can be used from futures.

        NOTE: expects exactly movements_scraped_ordered_asc
        (generated from basic_movements_scraped_from_movements_parsed)
        :param account_scraped
        :param movements_scraped_ordered_asc
        :param date_from_str: added 08/2021 for better err reports
        """
        fin_ent_account_id = account_scraped.FinancialEntityAccountId

        is_movements_scraped_consistent = integrity_helpers.check_movements_scraped_consistency(
            self.logger,
            account_scraped,
            movements_scraped_ordered_asc
        )

        if not is_movements_scraped_consistent:
            self.basic_set_movements_scraping_finished(
                fin_ent_account_id,
                result_codes.ERR_BALANCE_INCONSISTENT_MOVEMENTS
            )
            return False

        # DISABLED because bankinter and ruralvia-based scrapers
        # often have different balance and it should be updated from
        # last movement_scraped...
        # is_correct_temp_balance_of_last_movement_scraped = \
        #     integrity_helpers.check_temp_balance_of_last_movement_scraped(
        #         self.logger,
        #         account_scraped,
        #         movements_scraped_ordered_asc
        #     )
        #
        # if not is_correct_temp_balance_of_last_movement_scraped:
        #     self.basic_set_movements_scraping_finished(fin_ent_account_id)
        #     return False

        # Get the last movement saved
        last_movement_saved = self.db_connector.get_last_movement_of_account(
            fin_ent_account_id
        )
        # Get already saved movements in the DB. Type is MovementScraped
        # Declaration to suppress mypy warnings
        movements_saved = []  # type: List[MovementSaved]
        if movements_scraped_ordered_asc:
            # Since date of the first mov of movements scraped
            movements_saved = self.db_connector.get_movements_since_date(
                fin_ent_account_id,
                movements_scraped_ordered_asc[0].OperationalDate  # of first mov
            )
        else:
            # Get the last movement
            if last_movement_saved:
                movements_saved = [last_movement_saved]

        # Don't try check and upload movements with OperationalDate earlier than movement_saved_first
        # These (too early) movements_scraped may be extracted
        # due to SCRAPE_MOVEMENTS_WITH_DATES_OFFSET_BEFORE_LAST_SCRAPED_MOV
        # Example (pseudocode)
        # movements_saved_first = (OpDate='20180101', Key=123)
        #    - first date if the scraping started since 2018-01-15
        # movements_scraped([OpDate='20171231', Key=999],[OpDate='20180101', Key=123])
        #    - due to re-scrape offset
        # There is no real balance integrity error but one-to-one comparing will fail
        # That's why need to filter movements_scraped OpDate >= first OpDate
        movement_saved_first = self.db_connector.get_first_movement_of_account(fin_ent_account_id)
        if not movement_saved_first:
            movements_scraped_filtered_by_first_saved_op_date = movements_scraped_ordered_asc

        else:
            mov_saved_first_oper_date_dt = date_funcs.convert_db_fmt_date_str_to_dt(
                movement_saved_first.OperationalDate
            )

            movements_scraped_filtered_by_first_saved_op_date = [
                movement_scraped
                for movement_scraped in movements_scraped_ordered_asc
                if (date_funcs.convert_db_fmt_date_str_to_dt(movement_scraped.OperationalDate)
                    >= mov_saved_first_oper_date_dt)
            ]

        assert self._min_allowed_date_from  # avoid None (must be set from basic_get_date_from)
        is_balance_correct, result_code = integrity_helpers.check_balance_integrity(
            self.logger,
            account_scraped,
            movements_scraped_filtered_by_first_saved_op_date,
            movements_saved,
            date_from_str=date_from_str,
            date_to_str=self.date_to_str,
            min_allowed_date_from=self._min_allowed_date_from,
            last_movement_saved=last_movement_saved,
        )

        if result_code == result_codes.ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS:
            # JFM: Don't check balance integrity just insert movements for specific
            # accounts (FORCE_UPDATE_MOVEMENTS_ACCOUNTS environment variable):
            # Comment 2023-07-25 BR https://tesoralia.visualstudio.com/tesoralia.soporte/_workitems/edit/6318
            if self.basic_is_in_update_over_err_last_movement_saved_not_in_scraped_movements_accounts(fin_ent_account_id):
                # if date_funcs.get_date_from_str(last_movement_saved.OperationalDate, date_funcs.DB_DATE_FMT) < self._min_allowed_date_from:
                #     self.logger.warning('{}: Balance from last DB movement is correct:'.format(fin_ent_account_id, last_movement_saved))
                result_code = result_codes.SUCCESS
                is_balance_correct = True

        if not is_balance_correct and not result_code == result_codes.ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS:
            movements_scraped_filtered_by_first_saved_op_date, _ = \
                movement_helpers.fill_originals_from_movements_saved(
                    self.logger,
                    fin_ent_account_id,
                    movements_scraped_filtered_by_first_saved_op_date,
                    movements_saved,
                )
            is_balance_correct, result_code = integrity_helpers.try_autofix_balance_integrity_error(
                self.logger,
                self.db_connector,
                is_balance_correct,
                account_scraped,
                movements_scraped_filtered_by_first_saved_op_date,
                movements_saved,
                date_from_str=date_from_str,
                date_to_str=self.date_to_str,
                min_allowed_date_from=self._min_allowed_date_from,
            )

        # Stop if inconsistent balance and we don't want upload if inconsistent balance
        if not is_balance_correct:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_code)
            return False

        if not movements_scraped_filtered_by_first_saved_op_date:
            self.basic_set_movements_scraping_finished(fin_ent_account_id, result_code)
            return True

        # Update balance from last movement temp_balance only if no balance integrity error detected
        if is_balance_correct:
            self.__check_and_update_acc_bal_from_mov(
                account_scraped,
                movements_scraped_filtered_by_first_saved_op_date
            )

        # '20171030'
        date_from_str_db_format = movements_scraped_filtered_by_first_saved_op_date[0].OperationalDate

        try:
            if project_settings.IS_UPDATE_DB:
                err_msg = self.db_connector.movements_upload(
                    fin_ent_account_id,
                    movements_scraped_filtered_by_first_saved_op_date,
                    result_code
                )
                if err_msg:
                    self.logger.error('{}: {}'.format(fin_ent_account_id, err_msg))
            else:
                self.logger.info("Don't save movements due to settings")
            # Returns true even if err_msg from self.db_connector.movements_upload
            #  to process download_receipts on weak errors
            return True
        except:
            self.logger.error(traceback.format_exc())
            return False

    def basic_set_movements_scraping_finished(
            self,
            fin_ent_account_id: str,
            result_code: ResultCode = result_codes.ERR_COMMON_SCRAPING_ERROR) -> None:
        """Marks account as MovementsScrapingInProgress=False
        :param fin_ent_account_id: fin_ent_account_id
        :param result_code: default is ERR_COMMON_SCRAPING_ERROR
                for backward compat with this method called from scrapers (not from basic_...),
                because the scrapers usually calls this method on failures
        """
        self.logger.info("{}: set movement scraping: finished with code: {}".format(
            fin_ent_account_id,
            result_code.description
        ))
        if project_settings.IS_UPDATE_DB:
            self.db_connector.update_acc_set_mov_scrap_fin(fin_ent_account_id, result_code)

    def basic_set_movements_scraping_finished_for_contract_accounts(
            self,
            org_title: str,
            result_code: ResultCode) -> bool:
        """Finds in DB all accounts belonging to the contract by org_title,
        sets movements_scraping_finished for each account with result code.
        Usually called on contact-level errors to fill result_codes for accounts
        """
        self.logger.info("{}: update states for belonging accounts".format(org_title))
        db_organization = self.basic_get_organization(org_title)
        if not db_organization:
            self.logger.warning("{}: can't find saved db_organization. Skip")
            return False
        accounts_saved = self.db_connector.get_accounts_saved(db_organization)
        self.logger.info('{}: found {} accounts_saved: {}'.format(
            org_title,
            len(accounts_saved),
            [a.FinancialEntityAccountId for a in accounts_saved]
        ))
        for acc in accounts_saved:
            self.basic_set_movements_scraping_finished(
                acc.FinancialEntityAccountId,
                result_code=result_code
            )
        return True

    def basic_log_time_spent(self, metric: str) -> None:
        """Logs time spent from init till the moment"""
        finished = datetime.datetime.now()
        spent_balances = (finished - self.started).seconds
        self.logger.info('===== {}: DONE in {} sec. ====='.format(metric, spent_balances))

    def basic_log_process_account(self,
                                  account_no: str,
                                  date_from_str: str,
                                  movements_scraped: List[MovementScraped] = None,
                                  date_to_str: str = None) -> None:
        """Call it with or without movements.
        Call it in the beginning of the func and/or in the end
        """
        date_to_str = date_to_str or self.date_to_str

        if movements_scraped is not None:
            self.logger.info(
                'Process_account: {}: dates from {} to {}: {} movements: {}'.format(
                    account_no,
                    date_from_str,
                    date_to_str,
                    len(movements_scraped),
                    movements_scraped
                )
            )
        else:
            self.logger.info(
                'Process_account: {}: dates from {} to {}'.format(
                    account_no,
                    date_from_str,
                    date_to_str
                )
            )
        return

    def basic_log_process_account_transfers(self,
                                            account_no: str,
                                            date_from_str: str,
                                            transfers_scraped: List[TransferScraped] = None,
                                            date_to_str: str = None) -> None:
        """Call it with or without transfers .
        Call it in the beginning of the func and/or in the end
        """
        date_to_str = date_to_str or self.date_to_str

        if transfers_scraped is not None:
            self.logger.info(
                'Process_account for transfers: {}: dates from {} to {}: {} transfers: {}'.format(
                    account_no,
                    date_from_str,
                    date_to_str,
                    len(transfers_scraped),
                    transfers_scraped
                )
            )
        else:
            self.logger.info(
                'Process_account for transfers: {}: dates from {} to {}'.format(
                    account_no,
                    date_from_str,
                    date_to_str
                )
            )
        return

    def basic_log_wrong_layout(self, resp: Response, reason_info: str) -> bool:
        """Call it if a response with unwanted/wrong layout has been detected

        :param resp: the response where wrong layout has been detected
        :param reason_info: text message with the reason
                            and an additional info, mostly the further action.
        Examples:
        ---------

            # Simple case - check the resp for some text marker
            if 'CSRFtoken' not in resp_pre_login.text:
                self.basic_log_wrong_layout(resp_pre_login, "Can't parse csrf_token_param. Abort")
                return s, resp_pre_login, False

            # More complex parsing process:
            # check the 'ok' flag from the parsing function (this one should be provided in this case)
            ok, movements_parsed = parse_helpers.get_movements_parsed(resp_movs.text)
            if not ok:
                self.basic_log_wrong_layout(
                    resp_movs,
                    "{}: can't get movements_parsed. Skip process_account".format(fin_ent_account_id)
                )
                return False

            # Useful information about the further action of the scraper
            for ...:
                ok, movements_parsed_i = parse_helpers.get_movements_parsed(resp_movs_i.text)
                if not ok:
                    self.basic_log_wrong_layout(
                        resp_movs_i,
                        "{}: can't get movements_parsed_i at page #{}. Break the loop".format(
                            fin_ent_account_id,
                            i
                        )
                    )
                    break
        """
        self.logger.error('WRONG LAYOUT. {}. RESPONSE:\n{}\n{}'.format(
            reason_info,
            resp.url,
            resp.text
        ))
        return True

    def basic_should_scrape_extended_descriptions(self) -> bool:
        """Allows to scrape extended descriptions"""
        return self.__should_scrape_extended_descriptions_user_level

    def basic_check_account_is_active(self, fin_ent_account_id: str) -> bool:
        is_active = self.db_connector.check_account_is_active(fin_ent_account_id)
        action_msg = "Should process it" if is_active else "Should skip it"
        self.logger.info('{}: is active and not frozen: {}. {}'.format(fin_ent_account_id, is_active, action_msg))
        return is_active

    def basic_should_download_receipts(self, account_scraped: AccountScraped) -> bool:
        """Allows to download receipts only for specific accounts in
        specific time
        :returns True if allowed.
        """
        hour = date_funcs.now_time_hour()
        if (hour < project_settings.DOWNLOAD_RECEIPTS_IF_HOUR_LESS and
                self.db_connector.should_download_receipts(account_scraped.FinancialEntityAccountId)):
            self.logger.info("{}: should download receipts".format(account_scraped.FinancialEntityAccountId))
            return True
        self.logger.info("{}: should NOT download receipts".format(account_scraped.FinancialEntityAccountId))
        return False

    def basic_update_movements_extended_descriptions_if_necessary(
            self,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped]) -> bool:

        """Updates extended descriptions only if
        len(descriptionNew) > len(descriptionOld)
        that means we got extended description with more details.

        It covers cases for BBVANetCash when sometimes it is possible to
        get later the extended description with more details.

        Also, it respects project_settings UPDATE_MOVEMENTS_EXTENDED_DESCRIPTIONS_IF_HOUR_LESS
        """

        hour = date_funcs.now_time_hour()

        if (hour < project_settings.UPDATE_MOVEMENTS_EXTENDED_DESCRIPTIONS_IF_HOUR_LESS
                and project_settings.IS_UPDATE_DB):
            try:
                self.db_connector.update_movements_extended_descriptions_if_necessary(
                    account_scraped.FinancialEntityAccountId,
                    movements_scraped
                )
                return True
            except:
                self.logger.error(traceback.format_exc())
        return False

    def basic_update_movements_descriptions_if_necessary(
            self,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped]) -> bool:

        """Updates descriptions only if
        len(descriptionNew) > len(descriptionOld)
        that means we got description with more details.

        It covers cases for RBS when there are no all
        'narrative #' vals for future/today movements for the moment,
        but then they appear
        """

        if project_settings.IS_UPDATE_DB:
            try:
                self.db_connector.update_movements_descriptions_if_necessary(
                    account_scraped.FinancialEntityAccountId,
                    movements_scraped
                )
                return True
            except:
                self.logger.error(traceback.format_exc())
        return False

    def basic_download_receipts_common(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed],
            meta: dict = None) -> Tuple[bool, List[MovementScraped]]:
        """The most common implementation for self.download_receipts
        Use it if no need to implement custom behavior

        It calls self.download_movement_receipt concurrently for each movement
        and then updates StatementExtendedDescription (also for each movement)

        Code example:
        -------------
        def download_receipts(self, args):
            return self.basic_download_receipts_common(args)

        :param s: ...
        :param account_scraped: ...
        :param movements_scraped: ...
        :param movements_parsed: ...
        :param meta: a dictionary of any additional params

        :returns (is_success, list_of_mov_scraped_w_receipts_info)
        """
        if not meta:
            meta = {}

        if not self.basic_should_download_receipts(account_scraped):
            return False, movements_scraped

        self.logger.info("Download receipts for {}".format(account_scraped))

        receipt_descriptions = [''] * len(movements_parsed)
        if (project_settings.IS_CONCURRENT_SCRAPING
                and self.CONCURRENT_PDF_SCRAPING_EXECUTORS > 1):
            with futures.ThreadPoolExecutor(max_workers=self.CONCURRENT_PDF_SCRAPING_EXECUTORS) as executor:
                futures_dict = {}
                for i in range(len(movements_parsed)):
                    should_download_receipt = self.db_connector.should_download_receipt_doc(
                        movements_scraped[i].KeyValue,
                        account_scraped.FinancialEntityAccountId
                    )
                    if should_download_receipt:
                        # ALL EXCEPTIONS SHOULD BE HANDLED IN self.download_movement_receipt,
                        # NOT ALLOWED TO RAISE UNHANDLED EXCEPTION
                        future = executor.submit(self.download_movement_receipt,
                                                 s, account_scraped,
                                                 movements_scraped[i],
                                                 movements_parsed[i],
                                                 meta)
                        futures_dict[future] = i
                    else:
                        self.logger.info('{}: don\'t download receipt for mov: date {}, pos #{}, amount {}. '
                                         'The movement already has a linked PDF. Skip'.format(
                            account_scraped.FinancialEntityAccountId,
                            movements_scraped[i].OperationalDate,
                            movements_scraped[i].OperationalDatePosition,
                            movements_scraped[i].Amount,
                        ))
                        continue

                lock = threading.Lock()
                for future in futures.as_completed(futures_dict):
                    ix = futures_dict[future]
                    if future.result():
                        with lock:
                            receipt_descriptions[ix] = future.result()
        else:
            for i, movement_parsed in enumerate(movements_parsed):
                should_download_receipt = self.db_connector.should_download_receipt_doc(
                    movements_scraped[i].KeyValue,
                    account_scraped.FinancialEntityAccountId
                )
                if should_download_receipt:
                    receipt_descriptions[i] = self.download_movement_receipt(
                        s,
                        account_scraped,
                        movements_scraped[i],
                        movement_parsed,
                        meta
                    )
                else:
                    self.logger.info('{}: don\'t download receipt for mov: date {}, pos #{}, amount {}. '
                                     'The movement already has a linked PDF. Skip'.format(
                        account_scraped.FinancialEntityAccountId,
                        movements_scraped[i].OperationalDate,
                        movements_scraped[i].OperationalDatePosition,
                        movements_scraped[i].Amount,
                    ))
                    continue
        movs_w_receipt_info = [
            MovementScraped(
                Amount=m.Amount,
                TempBalance=m.TempBalance,
                OperationalDate=m.OperationalDate,
                ValueDate=m.ValueDate,
                StatementDescription=m.StatementDescription,
                StatementExtendedDescription=m.StatementExtendedDescription,
                OperationalDatePosition=m.OperationalDatePosition,
                KeyValue=m.KeyValue,
                StatementReceiptDescription=receipt_descriptions[i],  # set
                StatementReference1='',
                StatementReference2='',
                CreateTimeStamp=m.CreateTimeStamp,
                Bankoffice=m.Bankoffice,
                Payer=m.Payer,
                InitialId=m.InitialId,
                ExportTimeStamp=m.ExportTimeStamp,
                Receipt=m.Receipt,
                ReceiptChecksum=m.ReceiptChecksum
            )
            for (i, m) in enumerate(movements_scraped)
        ]
        return True, movs_w_receipt_info

    def basic_download_transfers_common(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            movements_parsed: List[MovementParsed],
            meta: dict = None) -> Tuple[bool, List[TransferScraped]]:
        """The most common implementation for self.download_transfer
        Use it if no need to implement custom behavior

        It calls self.download_movement_transfer concurrently for each movement
        and then updates StatementExtendedDescription (also for each movement)

        Code example:
        -------------
        def download_transfers(self, args):
            return self.basic_download_transfers_common(args)

        :param s: ...
        :param account_scraped: ...
        :param movements_scraped: ...
        :param movements_parsed: ...
        :param meta: a dictionary of any additional params

        :returns (is_success, list_of_mov_scraped_w_receipts_info)
        """
        if not meta:
            meta = {}

        # if not self.basic_should_download_transfers(account_scraped):
        #     return False, movements_scraped

        self.logger.info("Download transfers for {}".format(account_scraped))

        transfers_scraped_w_none_elements = [None] * len(movements_parsed)  # type: List[Optional[TransferScraped]]
        if (project_settings.IS_CONCURRENT_SCRAPING
                and self.CONCURRENT_PDF_SCRAPING_EXECUTORS > 1):
            with futures.ThreadPoolExecutor(max_workers=self.CONCURRENT_PDF_SCRAPING_EXECUTORS) as executor:
                futures_dict = {}
                for i in range(len(movements_parsed)):
                    # ALL EXCEPTIONS SHOULD BE HANDLED IN self.download_movement_receipt,
                    # NOT ALLOWED TO RAISE UNHANDLED EXCEPTION
                    future = executor.submit(self.download_movement_transfer,
                                             s, account_scraped,
                                             movements_scraped[i],
                                             movements_parsed[i],
                                             meta)
                    futures_dict[future] = i

                lock = threading.Lock()
                for future in futures.as_completed(futures_dict):
                    ix = futures_dict[future]
                    if future.result():
                        with lock:
                            transfers_scraped_w_none_elements[ix] = future.result()
        else:
            for i, movement_parsed in enumerate(movements_parsed):
                transfers_scraped_w_none_elements[i] = self.download_movement_transfer(
                    s,
                    account_scraped,
                    movements_scraped[i],
                    movement_parsed,
                    meta
                )
        transfers_scraped = [t for t in transfers_scraped_w_none_elements if t]
        # TransferScraped = NamedTuple(
        #     'TransferScraped', [
        #         ('AccountId', int),
        #         ('CustomerId', int),
        #         ('OperationalDate', str),  # db fmt
        #         ('ValueDate', str),  # db fmt
        #         ('Amount', float),
        #         ('TempBalance', Optional[float]),
        #         ('Currency', str),
        #         ('AccountOrder', str),
        #         ('NameOrder', str),
        #         ('Concept', str),
        #         ('Reference', str),
        #         ('Description', str),
        #         ('Observation', str),
        #         ('FinancialEntityName', str),
        #         ('IdStatement', Optional[str]),  # str to set 'not linked' ('No vinculable') then by TransfersLinker

        return True, transfers_scraped

    def basic_get_organization(self, organization_title: str) -> Optional[DBOrganization]:
        return self.db_connector.get_organization(organization_title)

    @staticmethod
    def correspondence_folder_path(product_id: str) -> str:
        """To call from removal tool"""
        folder_path = os.path.join(
            project_settings.DOWNLOAD_CORRESPONDENCE_DOCUMENTS_TO_FOLDER,
            product_id
        )
        return folder_path

    @staticmethod
    def correspondence_file_path(folder_path: str, file_id: str, file_extension: str):
        """To call from removal tool"""
        file_path = os.path.join(folder_path, 'doc-{}.{}'.format(file_id, file_extension))
        return file_path

    def _create_correspondence_folder(self, corr_scraped: CorrespondenceDocScraped) -> str:
        folder_path = self.correspondence_folder_path(corr_scraped.ProductId)
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                self.logger.warning(
                    "Can't create folder {}: probable reason: several attempts to create the folder "
                    "from different threads at the same time. Skip".format(folder_path)
                )
        return folder_path

    def basic_should_download_correspondence_for_account(self, fin_ent_account_id: Optional[str]) -> bool:
        if project_settings.IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS:
            return self.basic_should_download_correspondence_for_account__acc_cond(fin_ent_account_id)
        return True

    def basic_should_download_correspondence_for_account__acc_cond(
            self,
            fin_ent_account_id: Optional[str]) -> bool:
        """Check account-level correspondence downloading flag before download correspondence
        Possible cases:
            account with scrapeAccountCorrespondence = 1 -> True
            should download generic and scrapeAccountCorrespondence = 0 -> False
            should download generic and scrapeAccountCorrespondence != 0 -> True
            should NOT download generic and scrapeAccountCorrespondence != 1 -> False
        :param fin_ent_account_id: FinancialEntityAccountId
        :returns True if allowed
        """
        # fin_ent_account_id[-9:] covers all known cases when fin_ent_account_id[-9:] == account_no[-9:]
        if fin_ent_account_id is None or fin_ent_account_id == PDF_UNKNOWN_ACCOUNT_NO:
            acc_suffix = 'Empty account'
        else:
            acc_suffix = fin_ent_account_id[-9:]

        # Check if account has correspondence download activated
        is_in_list_to_download = list_funcs.any_el_endswith(self._accounts_to_download_corr.values(), acc_suffix)
        if is_in_list_to_download:
            # Account with scrapeAccountCorrespondence = 1
            self.logger.info('...{}: should download account correspondence'.format(acc_suffix))
            return True

        if self._should_download_corr_generic:
            # Check if account has correspondence download deactivated
            is_in_list_to_skip = list_funcs.any_el_endswith(self._accounts_to_skip_download_corr.values(),acc_suffix)
            if is_in_list_to_skip:
                # Account with scrapeAccountCorrespondence = 0
                self.logger.info('...{}: should NOT download account correspondence'.format(acc_suffix))
                return False
            else:
                # Account with scrapeAccountCorrespondence != 0 and scrapeAccountCorrespondence != 1
                self.logger.info('...{}: should download generic correspondence'.format(acc_suffix))
                return True
        else:
            self.logger.info('...{}: should NOT download generic correspondence'.format(acc_suffix))
            return False

    def __should_save_corr_scraped(self, corr_scraped: CorrespondenceDocScraped) -> bool:
        """Checks all details for conditional correspondence downloading after download correspondence
        (DB flags scrapeCorrespondence, scrapeGenericCorrespondence, scrapeAccountCorrespondence)

        Suitable for the scrapers where basic_should_download_correspondence_for_account is not used yet,
        also it uses DB AccountId instead an account suffix search on prev step
        :param corr_scraped: CorrespondenceDocScraped (create it by the specific scraper)
        :returns True if allowed
        """
        if not project_settings.IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS:
            return True

        corr_str = "Corr '{}...' ({}) @ {} of {}".format(
            corr_scraped.Description[:10],
            corr_scraped.Amount,
            corr_scraped.DocumentDate.strftime(project_settings.SCRAPER_DATE_FMT),
            corr_scraped.ProductId
        )

        db_account_id = corr_scraped.AccountId
        if db_account_id in self._accounts_to_download_corr.keys():
            # Account with scrapeAccountCorrespondence = 1
            self.logger.info('{}: should save account correspondence'.format(corr_str))
            return True

        if self._should_download_corr_generic:
            if db_account_id in self._accounts_to_skip_download_corr.keys():
                # Account with scrapeAccountCorrespondence = 0
                self.logger.info('{}: should NOT save account correspondence'.format(corr_str))
                return False
            else:
                # Account with scrapeAccountCorrespondence != 0 and scrapeAccountCorrespondence != 1
                self.logger.info('{}: should save generic correspondence'.format(corr_str))
                return True
        else:
            self.logger.info('{}: should NOT save generic correspondence'.format(corr_str))
            return False

    def basic_save_correspondence_doc_pdf_and_update_db(
            self,
            corr_scraped: CorrespondenceDocScraped,
            pdf_file_content: bytes,
            file_extension: str = 'pdf',
            force_save_for_any_account=False) -> bool:
        """Basic method to save the document and update the DB flag that uses Checksum as file id
        :param corr_scraped:
        :param pdf_file_content:
        :param file_extension:
            for multi-file correspondence it will be "zip"
            Example: -a 23006: FUNDACION LANTEGI BATUAK:
            CorrespondenceDocParsed(account_no='ES7021003810820200030647', operation_date=01/01/2021,
            amount=2639.6, descr='Liquidación cuenta de crédito')
        :param force_save_for_any_account:
            if True, then skips __should_save_corr_scraped() checker
            (that checks account and access DB flags)
            and saves anyway.
            Useful for save_receipts_pdf_as_correspondence
        """
        # important to use KeyValue bcs it's unique field (at least for the account)

        if not force_save_for_any_account:
            if not self.__should_save_corr_scraped(corr_scraped):
                return True

        file_id = corr_scraped.Checksum
        folder_path = self._create_correspondence_folder(corr_scraped)
        file_path = self.correspondence_file_path(
            folder_path=folder_path,
            file_id=file_id,
            file_extension=file_extension
        )

        # if os.path.isfile(file_path):
        #     self.logger.info("Document file {} already saved ...".format(os.path.abspath(file_path)))
        #     return False

        self.logger.info("Save document to {}".format(os.path.abspath(file_path)))
        try:
            with open(file_path, 'wb') as f:
                f.write(pdf_file_content)
        except Exception as exc:
            self.logger.error(
                "{}: {}: can't save correspondence PDF: {} {}".format(
                    corr_scraped.ProductId,
                    corr_scraped.Description,
                    file_id,
                    exc
                )
            )
            return False
        if project_settings.IS_UPDATE_DB:
            self.db_connector.correspondence_doc_upload(corr_scraped, 'PDF')
        return True

    def basic_save_correspondence_doc_zip_and_update_db(
            self,
            corr_scraped: CorrespondenceDocScraped,
            pdf_contents: List[bytes],
            force_save=False) -> bool:
        """Basic method to save the document and update the DB flag that uses Checksum as file id
        :param corr_scraped:
        :param pdf_contents: a list of contents of several PDFs (multi-file correspondence)
            Example: -a 23006: FUNDACION LANTEGI BATUAK:
            CorrespondenceDocParsed(account_no='ES7021003810820200030647', operation_date=01/01/2021,
            amount=2639.6, descr='Liquidación cuenta de crédito')
        :param force_save:
            if True, then skips __should_save_corr_scraped() checker
            (that checks account and access DB flags)
            and saves anyway.
            Useful for save_receipts_pdf_as_correspondence
        """

        if not force_save:
            if not self.__should_save_corr_scraped(corr_scraped):
                return True

        # Handle args
        if not pdf_contents:
            self.logger.error('{}: no PDF content(s). Skip'.format(corr_scraped))
            return False

        if len(pdf_contents) < 2:
            return self.basic_save_correspondence_doc_pdf_and_update_db(
                corr_scraped,
                pdf_contents[0]
            )
        file_id = corr_scraped.Checksum
        folder_path = self._create_correspondence_folder(corr_scraped)

        # [(archived_file_name, archived_content)]
        fnames_contents = []  # type: List[Tuple[str, bytes]]
        for file_ix, content in enumerate(pdf_contents):
            # file names: doc-xyz.1.pdf, doc-xyz.2.pdf
            file_name = 'doc-{}.{}.pdf'.format(file_id, file_ix + 1)
            fnames_contents.append((file_name, content))

        # file_path = os.path.join(folder_path, 'doc-{}.zip'.format(file_id))
        file_path = self.correspondence_file_path(
            folder_path=folder_path,
            file_id=file_id,
            file_extension='zip'
        )

        self.logger.info("Save correspondence zipped PDFs to {}".format(os.path.abspath(file_path)))
        try:
            zip_arch_funcs.save_zip_arch(file_path, fnames_contents)
        except Exception as exc:
            self.logger.error(
                "{}: {}: can't save correspondence zipped PDFs: {} {}".format(
                    corr_scraped.ProductId,
                    corr_scraped.Description,
                    file_id,
                    exc
                )
            )
            return False
        if project_settings.IS_UPDATE_DB:
            self.db_connector.correspondence_doc_upload(corr_scraped, 'ZIP')
        return True

    def _get_cached_org_id(self, org_title: str) -> Tuple[bool, int]:
        if org_title not in self.__org_titles_to_ids:
            organization = self.basic_get_organization(org_title)
            if not organization:
                return False, -1
            with basic_lock:
                self.__org_titles_to_ids[org_title] = organization.Id

        with basic_lock:
            org_id = self.__org_titles_to_ids[org_title]
        return True, org_id

    def basic_save_receipt_pdf_as_correspondence(
            self,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            pdf_content: bytes,
            pdf_parsed_text: Optional[str] = None,
            pdf_data_format='',
            account_to_fin_ent_fn: Optional[Callable[[str], str]] = None,
            only_update_db=False,
            checksum: Optional[str] = None) -> Tuple[bool, str, str]:
        """Converts any PDF (usually receipt) to a correspondence doc and saves.
        - saves as doc-<checksum>.pdf
        - updates doc table
        - sets receipt info in the mov table: ReceiptChecksum, Document=1
        Must be called explicitly from the scraper where we need this option.
        For now, supports exactly 'pdf' file type.
        (Meanwhile, is is known that Caixa sometimes returns multi-file
        documents from correspondence mailbox which are saving as 'zip' archives.
        This option is not supported for this method because receipts, probably,
        always one-file-pdfs even from Caixa.
        But it can be implemented later is needed)
        :param pdf_parsed_text: can be None, in this case it will be parsed inside this method
        :param account_to_fin_ent_fn: similar to product_to_fin_ent of basic_check_correspondence_doc_to_add
            to use in LIKE '%fin_ent_account_id', thus it is allowed to use suffix of the FinancialEntityAccountId
        :param only_update_db:
            if True, then it doesn't save correspondence PDF file - only adds Db entry,
            it's odd, but for some scrapers it's required to save receipts to "receipts" folder
            and update correspondence metadata in DB. This is the case (see SabadellReceiptsScraper)
        :param checksum: explicit checksum to be used. If not provided, then will be calc in this method
        :return (ok, pdf_parsed_text, checksum)
        """

        def date_str_to_date(date_str: str) -> datetime.datetime:
            return datetime.datetime.strptime(
                date_funcs.convert_date_to_db_format(date_str),
                project_settings.DB_DATE_FMT
            )

        self.logger.info('{}: save receipt as correspondence ({}) for mov: date {}, pos #{}, amount {}'.format(
            account_scraped.FinancialEntityAccountId,
            "only DB, no files" if only_update_db else "DB and files",
            movement_scraped.OperationalDate,
            movement_scraped.OperationalDatePosition,
            movement_scraped.Amount,
        ))

        oper_date = date_str_to_date(movement_scraped.OperationalDate)
        val_date = date_str_to_date(movement_scraped.ValueDate)

        if pdf_parsed_text is None:
            pdf_parsed_text = pdf_funcs.get_text(pdf_content, pdf_data_format)

        if checksum is None:
            checksum = pdf_funcs.calc_checksum(bytes(pdf_parsed_text, 'utf-8'))

        corr_parsed = CorrespondenceDocParsed(
            type=DOCUMENT_TYPE_RECEIPT,  # !
            account_no=account_scraped.AccountNo,
            operation_date=oper_date,
            value_date=val_date,
            amount=movement_scraped.Amount,
            currency=account_scraped.Currency,
            descr=movement_scraped.StatementDescription,
            extra={},
        )
        corr_scraped = CorrespondenceDocScraped(
            CustomerId=self.db_customer_id,
            OrganizationId=None,
            FinancialEntityId=self.db_financial_entity_id,
            ProductId=corr_parsed.account_no,
            ProductType='',
            DocumentDate=corr_parsed.operation_date,
            Description=corr_parsed.descr,
            DocumentType=corr_parsed.type,
            DocumentText=pdf_parsed_text,
            # Checksum from parsed text to avoid be affected by PDF meta info
            Checksum=checksum,
            AccountId=None,  # Account DB Id, will be in corr_scraped_upd
            StatementId=None,  # will be in corr_scraped_upd
            Amount=corr_parsed.amount,
            Currency=corr_parsed.currency,
        )

        corr_scraped_upd, should_save = self.basic_check_receipt_doc_to_add(
            corr_scraped,
            account_scraped,
            movement_keyvalue=movement_scraped.KeyValue
        )
        if should_save:
            if only_update_db:
                if project_settings.IS_UPDATE_DB:
                    self.db_connector.correspondence_doc_upload(corr_scraped_upd, 'PDF')
            else:
                self.basic_save_correspondence_doc_pdf_and_update_db(
                    corr_scraped_upd,
                    pdf_content,
                    force_save_for_any_account=True
                )
        return True, pdf_parsed_text, checksum

    def basic_set_movement_scraped_references(
            self,
            account_scraped: AccountScraped,
            movements_scraped: List[MovementScraped],
            parse_reference_from_receipt_func: Callable[[str], str]) -> bool:

        """Sets StatementReference1 and StatementReference2
        fields of the movement_scraped with info extracted
        from the available movement description fields

        Tries for each movement:
        - get_movement_customer_references
        - get_movement_fin_entity_references
        - set_movement_references in DB (if at least one of the mov_references != '')

        :param account_scraped: ...
        :param movements_scraped: ...
        :param parse_reference_from_receipt_func: the parser func for fin_entity_reference
        """

        ref1_regexp, ref2_regexp = self.db_connector.get_customer_reference_patterns()
        fin_ent_extractor = self.db_connector.get_financial_entity_reference_extractor()

        for movement in movements_scraped:
            ref1, ref2 = movement_helpers.get_movement_customer_references(
                movement,
                ref1_regexp,
                ref2_regexp
            )
            if not (ref1 or ref2):
                ref1, ref2 = movement_helpers.get_movement_fin_entity_references(
                    movement,
                    fin_ent_extractor,
                    parse_reference_from_receipt_func
                )

            if project_settings.IS_UPDATE_DB:
                self.db_connector.set_movement_references(
                    account_scraped.FinancialEntityAccountId,
                    movement.KeyValue,
                    ref1,
                    ref2
                )

        return True

    def basic_should_download_correspondence_for_access(self) -> bool:
        """Checks customer-level correspondence downloading flag
        + access-level logic (at least one account should have scrapereceipts=1).
        It doesn't check time-specific parameters like basic_should_download_correpondence()
        and only used to set 'save_checksum' flag for receipt downloading
        to prevent PDF duplicates from correspondence area
        (see Bankia, Caixa, Liberbank).
        :returns True if allowed.
        """
        if project_settings.IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS:
            return self.basic_should_download_correspondence_for_access__acc_cond()

        if self.db_connector.should_download_correspondence(self.db_financial_entity_access_id):
            self.logger.info("Should download correspondence (checked access-level settings)")
            return True
        self.logger.info("Should NOT download correspondence (checked access-level settings)")
        return False

    def basic_should_download_correspondence_for_access__acc_cond(self) -> bool:
        """Checks customer-level correspondence downloading flag
        + access-level logic (at least one account should have scrapereceipts=1).
        It doesn't check time-specific parameters like basic_should_download_correpondence()
        and only used to set 'save_checksum' flag for receipt downloading
        to prevent PDF duplicates from correspondence area
        (see Bankia, Caixa, Liberbank).
        :returns True if allowed.
        """
        should_dwnld_corr, _ = self.db_connector.should_download_correspondence_and_generic(
            self.db_financial_entity_access_id
        )
        if should_dwnld_corr:
            self.logger.info("Should download correspondence (checked access-level settings)")
            return True
        self.logger.info("Should NOT download correspondence (checked access-level settings)")
        return False

    def basic_should_download_correspondence(self) -> bool:
        """Allows to download correspondence documents only for specific customers
        at specific time.
        :returns True if allowed.

        USAGE:
        def download_correspondence(self) -> Tuple[bool, List[CorrespondenceDocScraped]]:
            ...
            if not self.basic_should_download_correspondence():
                return False, []
        """
        if project_settings.IS_ACCOUNT_LEVEL_CORRESPONDENCE_CONDITIONS:
            return self.basic_should_download_correspondence__acc_cond()

        hour = date_funcs.now_time_hour()
        if (hour < project_settings.DOWNLOAD_CORRESPONDENCE_DOCUMENTS_IF_HOUR_LESS and
                self.db_connector.should_download_correspondence(self.db_financial_entity_access_id)):
            self.logger.info("Should download correspondence (checked access-level & time settings)")
            return True
        self.logger.info("Should NOT download correspondence (checked access-level & time settings)")
        return False

    def basic_should_download_correspondence__acc_cond(self) -> bool:
        """Allows to download correspondence documents only for specific customers
        at specific time.
        :returns True if allowed.

        Also, sets (!):
            - self.__should_download_corr_generic
            - self.__accounts_ids_to_download_corr

        USAGE:
        def download_correspondence(self) -> Tuple[bool, List[CorrespondenceDocScraped]]:
            ...
            if not self.basic_should_download_correspondence():
                return False, []
        """
        hour = date_funcs.now_time_hour()
        should_dwnld_corr, should_dwnld_corr_generic = \
            self.db_connector.should_download_correspondence_and_generic(self.db_financial_entity_access_id)
        if hour >= project_settings.DOWNLOAD_CORRESPONDENCE_DOCUMENTS_IF_HOUR_LESS or not should_dwnld_corr:
            self.logger.info("Should NOT download correspondence (checked access-level & time settings)")
            return False

        self.logger.info("Should download correspondence (checked access-level & time settings)")

        # List of accounts where field scrapeAccountCorrespondence = 1
        accounts_to_download_corr = self.db_connector.get_accounts_to_download_correspondence(
            self.db_financial_entity_access_id
        )  # type: List[AccountToDownloadCorrespondence]

        # List of accounts where field scrapeAccountCorrespondence = 0
        accounts_to_skip_download_corr = self.db_connector.get_accounts_to_skip_download_correspondence(
            self.db_financial_entity_access_id
        )  # type: List[AccountToDownloadCorrespondence]

        self.logger.info('Got should_download_corr_generic={}, accounts_to_download_corr={}'.format(
            should_dwnld_corr_generic,
            accounts_to_download_corr
        ))
        self._should_download_corr_generic = should_dwnld_corr_generic
        self._accounts_to_download_corr = {
            acc.Id: acc.FinancialEntityAccountId
            for acc in accounts_to_download_corr
        }
        self._accounts_to_skip_download_corr = {
            acc.Id: acc.FinancialEntityAccountId
            for acc in accounts_to_skip_download_corr
        }

        return True

    def basic_get_correspondence_doc_movement_id(
            self,
            db_account_id: int,
            corr_parsed: CorrespondenceDocParsed,
            corr_document_text_info: Optional[DocumentTextInfo] = None) -> Optional[int]:
        """
        To use from correspondence scraper.
        Searches for the movement id by abs(corr.amount) == abs(mov.amount)
        Returns the corresponding movement id if there is only 1 matching movement for the date
        """
        # Use given data
        document_info_pos = corr_document_text_info  # 'positive' amount - as is
        # Or build from CorrespondenceDocParsed
        if not document_info_pos:
            document_info_pos = DocumentTextInfo(
                OperationalDate=corr_parsed.operation_date.strftime(project_settings.DB_DATE_FMT),
                ValueDate=(corr_parsed.value_date.strftime(project_settings.DB_DATE_FMT)
                           if corr_parsed.value_date is not None
                           else ''),
                Amount=corr_parsed.amount,
                StatementDescription=corr_parsed.descr
            )
        movement_ids_pos = self.db_connector.get_movement_initial_ids_from_document_info(
            db_account_id,
            document_info_pos
        )
        if len(movement_ids_pos) == 1:
            return movement_ids_pos[0]

        if corr_parsed.amount is None:
            return None

        # Try to find equal mov with the same neg(amount) because
        # correspondence's amount (mostly) always positive
        # and there is no reliable way to detect its sign
        document_info_neg = DocumentTextInfo(
            OperationalDate=corr_parsed.operation_date.strftime(project_settings.DB_DATE_FMT),
            ValueDate=(corr_parsed.value_date.strftime(project_settings.DB_DATE_FMT)
                       if corr_parsed.value_date is not None
                       else ''),
            Amount=-corr_parsed.amount,  # !
            StatementDescription=corr_parsed.descr
        )
        movement_ids_neg = self.db_connector.get_movement_initial_ids_from_document_info(
            db_account_id,
            document_info_neg
        )
        if len(movement_ids_neg) == 1:
            return movement_ids_neg[0]

        return None

    def basic_check_correspondence_doc_to_add(
            self,
            corr_parsed: CorrespondenceDocParsed,
            corr_scraped: CorrespondenceDocScraped,
            corr_document_text_info: Optional[DocumentTextInfo] = None,
            product_to_fin_ent_fn: Optional[Callable[[str], str]] = None) -> Tuple[CorrespondenceDocScraped, bool]:
        """
        :param corr_parsed: CorrespondenceDocParsed
        :param corr_scraped: CorrespondenceDocScraped (create it by the specific scraper)
        :param product_to_fin_ent_fn: a function to convert product_id to appropriate value
            for matching `FinancialEntityAccountId LIKE '%{product_to_fin_ent_fn(product_id)}'`.
            If not provided then default product_id[4:] will be used
        :param corr_document_text_info: if provided, then it will be used to get movement id,
            otherwise it will be built automatically from corr
            (it contains basically the same data, but from PDF text instead of HTML list)
        :return: (CorrespondenceDocScrapedUpdated, should_save)
            If should_save == True,
            then when need, use self.basic_save_document_pdf_and_update_db(document_upd, doc_pdf_content)
        """
        corr_checked = self.db_connector.check_add_correspondence_doc(
            corr_scraped,
            product_to_fin_ent_fn
        )  # type: CorrespondenceDocChecked
        if not corr_checked.IsToAdd:
            self.logger.info("Correspondence doc {} already saved in DB. Skip insertion".format(corr_scraped.Checksum))
            return corr_scraped, False

        corr_scraped_upd = corr_scraped

        # replace document with a new document object
        if corr_checked.AccountNo and corr_checked.AccountId:
            # Try to get movement_id to link correspondence PDF looking for movements
            # that do not have a linked PDF and have the same metadata
            movement_id = self.basic_get_correspondence_doc_movement_id(
                corr_checked.AccountId,
                corr_parsed,
                corr_document_text_info
            )

            corr_scraped_upd = CorrespondenceDocScraped(
                CustomerId=corr_scraped.CustomerId,
                OrganizationId=corr_scraped.OrganizationId,
                FinancialEntityId=corr_scraped.FinancialEntityId,
                ProductId=corr_checked.AccountNo,  # upd
                ProductType=corr_scraped.ProductType,
                DocumentDate=corr_scraped.DocumentDate,
                Description=corr_scraped.Description,
                DocumentType=corr_scraped.DocumentType,
                DocumentText=corr_scraped.DocumentText,
                Checksum=corr_scraped.Checksum,
                AccountId=corr_checked.AccountId,  # upd
                StatementId=movement_id,  # upd
                Amount=corr_scraped.Amount,
                Currency=corr_scraped.Currency,
            )
        return corr_scraped_upd, True

    def basic_check_receipt_doc_to_add(
            self,
            corr_scraped: CorrespondenceDocScraped,
            account_scraped: AccountScraped,
            movement_keyvalue='') -> Tuple[CorrespondenceDocScraped, bool]:
        """
        Validate and update corr_scraped with StatementId and AccountId to link receipt to movement
        :param corr_scraped: CorrespondenceDocScraped (create it by the specific scraper)
        :param account_scraped: account scraped data
        :param movement_keyvalue: movement_scraped.KeyValue
        :param product_to_fin_ent_fn: a function to convert product_id to appropriate value
            for matching `FinancialEntityAccountId LIKE '%{product_to_fin_ent_fn(product_id)}'`.
            If not provided then default product_id[4:] will be used
        :return: (CorrespondenceDocScrapedUpdated, should_save)
            If should_save == True,
            then when need, use self.basic_save_document_pdf_and_update_db(document_upd, doc_pdf_content)
        """
        receipt_account_id = self.db_connector.get_account_id(account_scraped.FinancialEntityAccountId)  # type: int
        if not receipt_account_id:
            self.logger.error("Can't get right receipt account id for account {}. Skip insertion".format(account_scraped.AccountNo))
            return corr_scraped, False

        if movement_keyvalue:
            # Strict and short way to get movement id by its KeyValue to link PDF
            movement_data_opt = self.db_connector.get_movement_data_from_keyvalue(
                movement_keyvalue,
                account_scraped.FinancialEntityAccountId,
                self.db_customer_id,
            )
            movement_id = int(movement_data_opt['InitialId']) if movement_data_opt else None

            if movement_id:
                corr_scraped_upd = CorrespondenceDocScraped(
                    CustomerId=corr_scraped.CustomerId,
                    OrganizationId=corr_scraped.OrganizationId,
                    FinancialEntityId=corr_scraped.FinancialEntityId,
                    ProductId=account_scraped.AccountNo,  # upd
                    ProductType=corr_scraped.ProductType,
                    DocumentDate=corr_scraped.DocumentDate,
                    Description=corr_scraped.Description,
                    DocumentType=corr_scraped.DocumentType,
                    DocumentText=corr_scraped.DocumentText,
                    Checksum=corr_scraped.Checksum,
                    AccountId=receipt_account_id,  # upd
                    StatementId=movement_id,  # upd
                    Amount=corr_scraped.Amount,
                    Currency=corr_scraped.Currency,
                )
                return corr_scraped_upd, True
            else:
                self.logger.error("{}: Can't get statement id to link receipt doc downloaded for mov: "
                                  "date {}, amount {}, description {}. It's possible that the movement "
                                  "does not exist in DB. Skip insertion"
                                  .format(account_scraped.FinancialEntityAccountId, corr_scraped.DocumentDate,
                                          corr_scraped.Amount, corr_scraped.Description))
                return corr_scraped, False
        else:
            self.logger.error("{}: Can't get movement_keyvalue to obtain statement id for mov:"
                              "date {}, amount {}, description {}. Skip insertion"
                              .format(account_scraped.FinancialEntityAccountId, corr_scraped.DocumentDate, corr_scraped.Amount,
                                      corr_scraped.Description))
            return corr_scraped, False

    def basic_get_spec_checksums_for_movements_saved(
            self,
            fin_ent_account_id: str,
            date_from_str: str) -> Set[str]:
        """Returns a set of special checksums for movements_saved.

        Important difference that these checksums will be calculated
        another way than KeyValue because will be used for movements_parsed
        before calculation of OperationalDatePosition.

        Second important point: if there are 2 movements which have
        the same checksums, then the checksum will be removed from the set,
        that means only checksums of explicitly unique movements by given arguments
        will be put into the set.
        """

        # Special usage for optimized extra details extraction
        movements_saved = self.__get_movements_saved_asc(
            fin_ent_account_id,
            date_from_str
        )  # type: List[MovementSaved]

        checksums = movement_helpers.get_spec_checksums_uniq_for_movements_saved(
            movements_saved
        )
        return checksums

    def basic_get_spec_checksum_for_movement_parsed(self, mov_parsed: MovementParsed):
        """IMPORTANT
        mov_parsed must have common fields:
        - operation_date
        - value_date
        - amount
        - temp_balance
        - description
        It's necessary to provide generic calculation.
        Otherwise, use custom implementation, but calculate it
        using the corresponding fields and the same approach
        """
        checksum = movement_helpers.get_spec_checksum_for_movement_parsed(mov_parsed)
        return checksum

    def basic_check_scraped_from_check_parsed(
            self,
            check_parsed: CheckParsed,
            check_collection_scraped: CheckCollectionScraped) -> CheckScraped:

        check_scraped = CheckScraped(
            CheckNumber=check_parsed['check_number'],
            CaptureDate=check_parsed['capture_date'],
            ExpirationDate=check_parsed['expiration_date'],
            PaidAmount=check_parsed['amount'],
            NominalAmount=check_parsed['amount'],
            ChargeAccount=check_parsed['charge_account'],
            ChargeCIF=check_parsed['charge_cif'],
            DocCode=check_parsed['doc_code'],
            Stamped=check_parsed['stamped'],
            State=check_parsed['state'],
            KeyValue=check_parsed['keyvalue'],
            Receipt=bool(check_parsed['image_content']),
            CustomerId=self.db_customer_id,
            FinancialEntityId=self.db_financial_entity_id,
            AccountId=check_collection_scraped.AccountId,
            AccountNo=check_collection_scraped.AccountNo,
            StatementId=check_collection_scraped.StatementId,
            CollectionId=None
        )
        return check_scraped

    def basic_should_download_checks(self) -> bool:
        """Allows to download checks only for specific clients
        at specific time
        :returns True if allowed.
        """
        hour = date_funcs.now_time_hour()
        if (hour < project_settings.DOWNLOAD_CHECKS_IF_HOUR_LESS and
                self.db_connector.should_download_checks()):
            self.logger.info("should download checks")
            return True
        self.logger.info("should NOT download checks")
        return False

    def basic_save_check_collection(self,
                                    check_collection_scraped: CheckCollectionScraped,
                                    checks_parsed: List[CheckParsed]) -> Tuple[bool, str]:
        checks_scraped = [
            self.basic_check_scraped_from_check_parsed(
                check_parsed,
                check_collection_scraped
            )
            for check_parsed in checks_parsed
        ]

        return self.db_connector.save_check_collection_transactional(check_collection_scraped, checks_scraped)

    def basic_get_check_collections_to_process(
            self,
            collections_parsed: List[CheckCollectionParsed]) -> List[CheckCollectionParsed]:

        all_keyvalues = [
            collection_parsed['keyvalue']
            for collection_parsed in collections_parsed
            if collection_parsed['has_details']
        ]
        saved_keyvalues = self.db_connector.check_add_check_collections(all_keyvalues)

        collections_to_process = [
            collection_parsed
            for collection_parsed in collections_parsed
            if (collection_parsed['keyvalue'] not in saved_keyvalues) and collection_parsed['has_details']
        ]

        self.logger.info('Got {} collections to process'.format(len(collections_to_process)))

        return collections_to_process

    def basic_should_download_leasing(self) -> bool:
        """Allows to download leasing only for specific clients
        at specific time
        :returns True if allowed.
        """
        hour = date_funcs.now_time_hour()
        if (hour < project_settings.DOWNLOAD_LEASING_IF_HOUR_LESS and
                self.db_connector.should_download_leasing()):
            self.logger.info("should download leasing")
            return True
        self.logger.info("should NOT download leasing")
        return False

    def basic_save_or_update_leasing_contract(
            self,
            leasing_contract_scraped: LeasingContractScraped,
            fees_scraped: List[LeasingFeeScraped]) -> Tuple[bool, str]:

        return self.db_connector.save_or_update_leasing_contract_transactional(
            leasing_contract_scraped,
            fees_scraped
        )

    def basic_fee_scraped_from_fee_parsed(self, leasing_fee_parsed: LeasingFeeParsed) -> LeasingFeeScraped:

        leasing_fee_scraped = LeasingFeeScraped(
            FeeReference=leasing_fee_parsed['fee_reference'],
            FeeNumber=leasing_fee_parsed['fee_number'],
            OperationalDate=leasing_fee_parsed['operational_date'],
            Currency=leasing_fee_parsed['currency'],
            Amount=leasing_fee_parsed['amount'],
            TaxesAmount=leasing_fee_parsed['taxes_amount'],
            InsuranceAmount=leasing_fee_parsed['insurance_amount'],
            FeeAmount=leasing_fee_parsed['fee_amount'],
            FinRepayment=leasing_fee_parsed['financial_repayment'],
            FinPerformance=leasing_fee_parsed['financial_performance'],
            PendingRepayment=leasing_fee_parsed['pending_repayment'],
            State=leasing_fee_parsed['state'],
            KeyValue=leasing_fee_parsed['keyvalue'],
            StatementId=leasing_fee_parsed['statement_id'],
            ContractId=None,
            InvoiceNumber= None if 'invoice_number' not in leasing_fee_parsed else leasing_fee_parsed['invoice_number'],
            DelayInterest= None if 'delay_interest' not in leasing_fee_parsed else leasing_fee_parsed['delay_interest'],
        )
        return leasing_fee_scraped

    @deprecated(reason='must use basic_get_n43_dates_and_account_status')
    def basic_get_n43_date_from_for_account(
            self,
            fin_ent_account_id: str,
            date_to: datetime.datetime) -> datetime.datetime:
        """Gets date basing of DB data (+1 day to prev)
        or by custom offset from today for new accounts
        """
        last_n43_date = self.db_connector.get_n43_last_date_of_account(fin_ent_account_id)
        date_from = (
            last_n43_date + datetime.timedelta(days=1) if last_n43_date
            else date_funcs.today() - datetime.timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS)
        )

        return min(date_from, date_to)  # avoid future date_from

    def _clean_account_no_for_n43(self, account_no: str) -> Tuple[bool, str]:
        """
        00497313592810000247          >>  00497313592810000247 -- If 20 digit then that's fine
        0049 7313 59 2810000247       >>  00497313592810000247
        ES4101822346110201515797      >>  01822346110201515797
        ES41 0182 2346 11 0201515797  >>  01822346110201515797
        -- else we have to decide
        """
        acc_no_wo_spaces = account_no.replace(' ', '')
        if len(acc_no_wo_spaces) < 20:
            return False, ''
        return True, acc_no_wo_spaces[-20:]

    def basic_get_mt940_dates_for_access(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """date_from: uses mt940_last_successful_result_date_of_access or initial offset"""
        date_from_initial = self.date_to - datetime.timedelta(
            days=project_settings.DOWNLOAD_MT940_OFFSET_DAYS_INITIAL
        )
        last_access_success_date = self.db_connector.get_mt940_last_successful_result_date_of_access()
        date_to = date_funcs.today() - datetime.timedelta(days=1)
        date_from = (min(date_to, last_access_success_date + datetime.timedelta(days=1))
                     if last_access_success_date
                     else date_from_initial)
        return date_from, date_to

    def basic_get_mt940_dates_and_account_status(
            self,
            account_no: str,
            date_to_offset=1) -> Tuple[datetime.datetime, datetime.datetime, bool, bool]:
        """
        :param account_no: account_no
        :param date_to_offset: date_to = today - date_to_offset
        :returns (date_from, date_to, is_active, is_account_level_results)"""
        prefix = '{}: MT940 downloading'.format(account_no)
        date_to = date_funcs.today() - datetime.timedelta(days=date_to_offset)
        date_from_if_new = date_to - datetime.timedelta(
            days=project_settings.DOWNLOAD_MT940_OFFSET_DAYS_INITIAL
        )

        last_mt940_date_and_account_status = self.db_connector.get_mt940_last_date_and_account_status(
            account_no
        )
        # "If no record is returned. Don’t do anything."
        # BUT also
        # "If no record is returned. This means that the account is new account, so you have to scrape it"
        if last_mt940_date_and_account_status is None:
            is_active_account = project_settings.MT940_IS_ACTIVE_ACCOUNT_IF_NONEXISTENT_IN_DB
            self.logger.info('{}: non-existent account for MT940: is_active={} (due to settings)'.format(
                prefix,
                is_active_account,
            ))
            # Hit DB only if active
            date_from, date_to = (
                self.basic_get_mt940_dates_for_access()
                if is_active_account
                # can be any for inactive account
                else (date_to, date_to)
            )
            return date_from, date_to, is_active_account, False

        last_mt940_mov_date, is_active_account = last_mt940_date_and_account_status

        if not is_active_account:
            self.logger.info('{}: existing account: is_active={}'.format(
                prefix,
                is_active_account,
            ))
            # Any dates
            return date_to, date_to, False, True

        # Active

        date_from = (last_mt940_mov_date + datetime.timedelta(days=1)
                     if last_mt940_mov_date
                     else date_from_if_new)

        # Avoid too old date_from due to 'scraping gaps'
        # (when the account was processed, then not, then processed again because of settings)
        date_from = max(date_from, date_from_if_new)

        # Avoid date_to < date_from
        date_to = max(date_from, date_to)

        self.logger.info('{}: existing account: is_active={}, dates from {} to {}{}'.format(
            prefix,
            is_active_account,
            date_from.date(),
            date_to.date(),
            '' if last_mt940_mov_date else ' (no last_mt940_mov_date)'
        ))

        return date_from, date_to, is_active_account, True

    def basic_get_n43_dates_for_access(self, offset_days=1) -> Tuple[datetime.datetime, datetime.datetime]:
        """During incremental scraping, we need only 1 day: yesterday or today
        :param offset_days is offset 0 or 1 of today, takes effect for both: date_from and date_to
        """
        # Logic for offset = 1
        # 11.06 (Fri) - date_from = ..., date_to = 10.06, success
        # 12.06 (Sat) - date_from = 11.06, date_to = 11.06, success
        # 13.06 (Sun) - failure
        # 14.06 (Mon) - date_from = 12.06, date_to = 13.06
        assert offset_days in [0, 1]
        date_to = date_funcs.today() - timedelta(days=offset_days)
        date_from = (
            # explicit operations to display logic
            self.last_successful_n43_download_dt - timedelta(days=offset_days) + timedelta(days=1)
            if self.last_successful_n43_download_dt
            else date_funcs.today() - datetime.timedelta(days=project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )
        date_from = min(date_to, date_from)

        return date_from, date_to

    def basic_get_n43_dates_and_account_status(
            self,
            account_no: str,
            org_title='',
            max_offset: int = None) -> Tuple[datetime.datetime, datetime.datetime, bool]:
        """Gets dates basing on DB data (+1 day to prev)
        or by custom offset from today for new accounts + account_status.
        + Log messages
        :param account_no: any suitable account_no to get n43 dates, it should be >= 20 digits
        :param org_title: optional org_title for logging; if not provided,
                          then only fin_ent_account_id will be used
        :param max_offset: some fin_entities has max_offset < DOWNLOAD_N43_OFFSET_DAYS_INITIAL
                           (Bankinter)
        :returns: (n43_date_from, n43_date_to, is_active_account)
        """
        if max_offset is None:
            max_offset = project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL

        prefix = ('{}: {}: N43 downloading'.format(org_title, account_no) if org_title
                  else '{}: N43 downloading'.format(account_no))
        date_to = date_funcs.today() - datetime.timedelta(days=1)
        date_from_if_new = date_funcs.today() - datetime.timedelta(
            days=min(max_offset, project_settings.DOWNLOAD_N43_OFFSET_DAYS_INITIAL)
        )
        ok, account_no_to_get_dates = self._clean_account_no_for_n43(account_no)
        if not ok:
            self.logger.error("{}: error while cleaning account_no to get dates, "
                              "consider as is_active=False".format(prefix))
            return date_to, date_to, False

        last_n43_date_and_account_status = self.db_connector.get_n43_last_date_and_account_status(
            account_no_to_get_dates
        )
        # "If no record is returned. Don’t do anything."
        if last_n43_date_and_account_status is None:
            is_active_account = False
            self.logger.info('{}: non-existent account for N43: is_active={}'.format(
                prefix,
                is_active_account,
            ))
            # Any dates
            return date_to, date_to, is_active_account

        last_n43_mov_date, is_active_account = last_n43_date_and_account_status

        if not is_active_account:
            self.logger.info('{}: existing account: is_active={}'.format(
                prefix,
                is_active_account,
            ))
            return date_to, date_to, False

        # Active

        # Avoid future date_from,
        # last_n43_mov_date (== LastStatementDate from N43) can be None if account is new or was inactive
        date_from = (min(last_n43_mov_date + datetime.timedelta(days=1), date_to) if last_n43_mov_date
                     else date_from_if_new)

        # Avoid too old date_from due to 'scraping gaps'
        # (when the account was processed, then not, then processed again because of settings)
        date_from = max(date_from, date_from_if_new)

        self.logger.info('{}: existing account: is_active={}, dates from {} to {}{}'.format(
            prefix,
            is_active_account,
            date_from.date(),
            date_to.date(),
            '' if last_n43_mov_date else ' (no last_n43_mov_date)'
        ))

        return date_from, date_to, is_active_account

    def _save_n43(
            self,
            fin_ent_name: str,
            ix: int,
            n43_content: bytes) -> bool:
        """Saves N43 file"""

        # TES-SANTANDER-7476-20201020-083546-21.N43
        # TES-<< entidadName >>-<< accesosClienteId >>-<<Execution date YYYYMMDD>>
        # -<<Execution started time HHMMSS>>-Incremental counter for this execution
        file_name = 'TES-{}-{}-{}-{}-{}.N43'.format(
            fin_ent_name,
            self.db_financial_entity_access_id,
            self.started.strftime('%Y%m%d'),
            self.started.strftime('%H%M%S'),
            ix
        )

        folder_path = (project_settings.DOWNLOAD_N43_TO_FOLDER_TEMP if self.is_temp_folder_for_n43_files
                       else project_settings.DOWNLOAD_N43_TO_FOLDER_FINAL)

        with basic_lock:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        file_path = os.path.join(folder_path, file_name)
        self.logger.info("Save N43 to {}".format(os.path.abspath(file_path)))

        try:
            with open(file_path, 'wb') as f:
                f.write(n43_content)
        except Exception as exc:
            self.logger.error(
                "Can't save N43 with ix {}: {}".format(ix, exc)
            )
            return False
        return True

    def basic_save_n43s(
            self,
            fin_ent_name: str,
            n43_contents: List[bytes]) -> bool:
        """Access-level func
        :param fin_ent_name: financial enity name for file naming, i.e. 'SANTANDER'
        :param n43_contents: list of all downloaded to memory N43s
        """
        num_files = len(n43_contents)
        ok = True
        for i, n43_content in enumerate(n43_contents):
            ok = self._save_n43(fin_ent_name, i, n43_content)
            if not ok:
                break

        if not ok:
            self.logger.error("An error occurred while saving N43 files. Abort")
            return False

        # NO NEED anymore, see basic_scrape_for_n43
        # Update DB
        # if project_settings.IS_UPDATE_DB:
        #     self.db_connector.add_n43_successful_results_for_access(
        #         started_at=self.started,
        #         num_files=num_files
        #     )

        return True

    def _save_mt940(self, mt940_file_downloaded: MT940FileDownloaded) -> bool:
        """Saves MT940 file"""

        folder_path = os.path.join(
            project_settings.DOWNLOAD_MT940_TO_FOLDER,
            str(self.db_financial_entity_access_id)
        )

        with basic_lock:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        file_path = os.path.join(folder_path, mt940_file_downloaded.file_name)
        self.logger.info("Save MT940 to {}".format(os.path.abspath(file_path)))

        try:
            with open(file_path, 'wb') as f:
                f.write(mt940_file_downloaded.file_content)
        except Exception as exc:
            self.logger.error(
                "Can't save MT940 file {}: {}".format(mt940_file_downloaded.file_name, exc)
            )
            return False
        return True

    def basic_save_mt940s(self, mt940_files_downloaded: List[MT940FileDownloaded]):
        ok = True
        for mt940_file_downloaded in mt940_files_downloaded:
            ok = self._save_mt940(mt940_file_downloaded)
            if not ok:
                break

        if not ok:
            self.logger.error("An error occurred while saving MT940 files. Abort")
            return False

        return True

    # STUBS

    def download_movement_receipt(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> str:
        """Stub that should be implemented in each receipts scraper
        Should download receipt for the movement, save it
        and CAN provide additional actions

        ALL EXCEPTIONS SHOULD BE HANDLED IN self.download_movement_receipt,
        NOT ALLOWED TO RAISE UNHANDLED EXCEPTION

        :returns the text of the receipts of the movement"""
        self.logger.warning("download_movement_receipt: NOT IMPLEMENTED")
        return ''

    def download_movement_transfer(
            self,
            s: MySession,
            account_scraped: AccountScraped,
            movement_scraped: MovementScraped,
            movement_parsed: MovementParsed,
            meta: dict) -> Optional[TransferScraped]:
        """Stub that should be implemented in each transfer scraper
        Should download transfer for the movement, save it
        and CAN provide additional actions

        ALL EXCEPTIONS SHOULD BE HANDLED IN self.download_movement_transfer,
        NOT ALLOWED TO RAISE UNHANDLED EXCEPTION

        :returns the text of the transfer of the movement"""
        self.logger.warning("download_movement_transfer: NOT IMPLEMENTED")
        return None

    def download_correspondence(self, *args, **kwargs) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Download correspondence docs from mailbox.

        Stub to call from standard scrapers to provide
        compatibility with companies correspondence documents downloading scrapers

        Real signature can be different at scraper level

        Should be implemented ONLY in DocumentsScraper
        but should call from each self.process_company()

        Code example:
        -------------
        def process_company(...):
            ...
            # from each scraper
            self.download_correspondence(s, ...)
            return True

        :returns (is_success, list_of_doc_scraped)
        """
        return True, []

    def download_checks(self, *args, **kwargs) -> Tuple[bool, List[CorrespondenceDocScraped]]:
        """Check scraping from each access and customer.

        Stub to call from standard scrapers to provide
        compatibility with customer access check downloading scrapers

        Real signature can be different at scraper level

        Should be implemented ONLY in ReceiptsScraper
        but should call from main()

        Code example:
        -------------
        def main(...):
            ...
            # from each scraper
            self.download_checks(s, ...)
            return True

        :returns (is_success, list_of_checks_scraped)
        """
        return True, []

    def download_receipts(self, *args, **kwargs) -> Tuple[bool, List[MovementScraped]]:
        """Stub to call from standard scrapers to provide
        compatibility with movements receipts downloading scrapers

        Real signature can be different at scraper level

        Should be implemented ONLY in ReceiptsScraper
        but should call from each self.process_account()

        Code example:
        -------------
        def process_account(...):
            ...
            # from each scraper
            self.download_receipts(s, account_scraped, movements_scraped, movements_parsed_corresponding)
            return True

        :returns list_of_mov_scraped_w_receipts_info
        """
        return True, []

    def download_leasing(self, *args, **kwargs) -> Tuple[bool, List[LeasingContractScraped]]:
        """Leasing Scraping from each access and customer.

        Stub to call from standard scrapers to provide
        compatibility with customer access check downloading scrapers

        Real signature can be different at scraper level

        Should be implemented ONLY in LeasingScraper
        but should call from main()

        Code example:
        -------------
        def main(...):
            ...
            # from each scraper
            self.download_leasing(s, ...)
            return True

        :returns (is_success, list_of_leasing_contracts_scraped)
        """
        return True, []

    # PROTO

    def process_movement(self,
                         s: MySession,
                         movement_parsed: MovementParsed,
                         fin_ent_account_id: str,
                         meta: Optional[dict]) -> Optional[MovementParsed]:
        """Must be implemented in the concrete scraper that uses it.
        Will be called by self.basic_get_movements_parsed_w_extra_details()

        If the movement has no extra details, must explicitly return
        movement_parsed

        If the scraper should drop this movement, return None
        (useful for BBVA: if it can't get at least one extra details
        due to 500 err, then it must return only movements where it obtained
        these details before the err occured).
        Then Nones will be dropped from the final list

        :returns optional movement_parsed_w_extra_details (extended descr + any more)
        """
        raise NotImplementedError

    def login(self) -> Union[Tuple[MySession, Response, bool, bool],
                             Tuple[MySession, Response, bool, bool, str],
                             Tuple[MySession, Response, bool, bool, str, str],
                             Tuple[MySession, Response, bool, bool, bool, str],]:
        """
        :return: (session, response, is_logged_in, is_credentials_error) OR
                 (session, response, is_logged_in, is_credentials_error, reason) OR
                 (session, response, is_logged_in, is_credentials_error, extra_val, reason) OR
                 (session, response, is_logged, is_credentials_error, is_redirected, reason)

        Note: real return signature may have additional values, but first 4 are always included
        """
        raise NotImplementedError

    def main(self) -> MainResult:
        """
        The main method for each concrete scraper
        :return (result code, optional msg str)
        """
        raise NotImplementedError

    # ENTRY POINT

    def _rollback_accounts(
            self,
            accounts_before_scraping: List[DBAccount]) -> Tuple[List[DBAccount],
                                                                List[AccountSavedWithTempBalance],
                                                                List[DBAccount]]:
        """Rollbacks accounts if 'rollback' conditions are satisfied:

        Detects accounts where balance != temp_balance of the last movement.
        That means the scraping process was not finished successfully
        (because the current implementation
        sets account.balance = temp_balance
        during the movements uploading),
        so, difference of balance and temp_balance means that the
        movements were not uploaded and we can rollback account's
        timestamps and balance to the state that was before the scraping job

        Additional checkup to allow the rollback:
        acc_before_scraping.Balance should be == last_mov_current_scraping.TempBalance,
        this means that we didn't upload movements partially
        (or any other unexpected way)
        and can return to previous balance without collision

        Again, it will rollback only if
        acc_before_scraping.Balance == last_mov_in_the_db.TempBalance
        to avoid collisions.

        :returns tuple(accs_to_rollback, accs_wrong_balances, accs_cant_rollback)
        """

        self.logger.info("For each account: align balance "
                         "and the last movement's temp_balance")

        accs_with_temp_balances = (
            self.db_connector.get_accounts_with_temp_balances(self.update_inactive_accounts)
        )  # type: List[AccountSavedWithTempBalance]

        # set corresponding accounts_before_scraping and accs_with_temp_balances
        accs_joined = {
            acc_prev.Id: (acc_prev, acc_w_temp_bal)
            for acc_prev in accounts_before_scraping
            for acc_w_temp_bal in accs_with_temp_balances
            if acc_prev.Id == acc_w_temp_bal.Id
        }  # type: Dict[str, Tuple[DBAccount, AccountSavedWithTempBalance]]

        accs_cant_rollback = []  # type: List[DBAccount]
        accs_wrong_balances = []  # type:List[AccountSavedWithTempBalance]
        accs_to_rollback = []  # type: List[DBAccount]

        # We can restore balance only if
        # temp_balance == acc_berofe_scraping.balance.
        # If they don't equal that means execution flow error
        # and may bring a collision -> should report it
        for acc_id, (acc_prev, acc_w_temp_bal) in accs_joined.items():
            if acc_w_temp_bal.Balance != acc_w_temp_bal.TempBalance:
                if acc_prev.Balance == acc_w_temp_bal.TempBalance:
                    accs_wrong_balances.append(acc_w_temp_bal)
                    accs_to_rollback.append(acc_prev)
                else:
                    # Can't rollback, handle 'Active' flag
                    if acc_w_temp_bal.Active:
                        accs_wrong_balances.append(acc_w_temp_bal)
                        accs_cant_rollback.append(acc_prev)
                    else:
                        self.logger.info(
                            "GOT AN ACCOUNT WITH WRONG BALANCE, BUT IT'S INACTIVE - "
                            "WILL NOT ROLLBACK.\n"
                            "ACCOUNT after this scraping job: {}\n"
                            "ACCOUNT before this scraping job: {}".format(
                                acc_w_temp_bal,
                                acc_prev
                            )
                        )

        if accs_to_rollback and project_settings.IS_UPDATE_DB:
            self.db_connector.accounts_rollback_ts_and_balances(accs_to_rollback,
                                                                self.update_inactive_accounts)

        return accs_to_rollback, accs_wrong_balances, accs_cant_rollback

    def scrape(self) -> MainResult:
        """Entry point for all scraping jobs.
        Not allowed to redefine it in children.
        This should be called by the main_launcher to provide postprocessing:
        - align account balance with the last mov temp balance
        """

        if project_settings.IS_UPDATE_DB:
            self.db_connector.update_accounts_scraping_attempt_timestamp()

        # remember the accounts state before scraping job
        accounts_before = self.db_connector.get_accounts_saved()  # type: List[DBAccount]

        # moved from main_launcher
        if project_settings.IS_UPDATE_DB:
            self.db_connector.set_accounts_scraping_in_progress()
        try:
            result = self.main()
            return result
        except Exception as e:
            raise e  # just allow it to bubble up
        finally:
            # main aim of this method
            (accs_to_rollback,
             accs_wrong_balances,
             accs_cant_rollback) = self._rollback_accounts(accounts_before)

            if accs_cant_rollback:
                self.logger.error(
                    "CAN'T ROLLBACK ACCOUNTS: EXECUTION FLOW COLLISION "
                    "(expected acc_before_scraping_balance == last_mov_temp_balance). "
                    "CHECK THE ACCOUNTS MANUALLY.\n\n"
                    "WRONG BALANCES DETECTED after this scraping job:\n{}\n\n"
                    "THE ACCOUNTS before this scraping job:\n{}".format(
                        '\n'.join('{}. {}'.format(i + 1, a) for i, a in enumerate(accs_wrong_balances)),
                        '\n'.join('{}. {}'.format(i + 1, a) for i, a in enumerate(accs_cant_rollback))
                    )
                )
                for acc in accs_cant_rollback:
                    self.basic_set_movements_scraping_finished(acc.FinancialEntityAccountId,
                                                               result_codes.ERR_BALANCE_UNALIGNED)
            if not accs_to_rollback:
                self.logger.info('No accounts to rollback')
            else:
                self.logger.warning("Rolled back accounts with wrong balances {} to {}".format(
                    accs_wrong_balances, accs_to_rollback))

    def _get_number_of_n43_files_downloaded(self) -> int:
        """Returns number of n43 files"""
        return len(self.n43_contents) or len(self.n43_texts)

    def _get_number_of_mt940_files_downloaded(self) -> int:
        """Returns number of downloaded mt940 files"""
        return len(self.mt940_files_downloaded)

    def basic_scrape_for_n43(self) -> MainResult:
        """
        Usage in N43 scrapers (must override default scrape() method):
        def scrape(self) -> MainResult:
            return self.basic_scrape_for_n43()
        """
        self.logger.info("== Scrape N43 (using basic_scrape_for_n43) ==")

        fin_ent_access_for_n43 = self.db_connector.get_fin_ent_access_for_n43()
        if fin_ent_access_for_n43 is not None:
            # Supposed to be processed for N43 by nightly scraper
            self.is_temp_folder_for_n43_files = bool(fin_ent_access_for_n43.TempFolder)
            self.last_successful_n43_download_dt = fin_ent_access_for_n43.LastSuccessDownload
        else:
            # Only manual launching supposed
            self.logger.info("The access is not set for nightly N43 downloading. "
                             "Using fallback func to get last_successful_n43_download, "
                             "set is_temp_folder_for_n43_files=True")
            self.is_temp_folder_for_n43_files = True
            self.last_successful_n43_download_dt = self.db_connector.get_n43_last_successful_result_date_of_access()

        self.logger.info('GOT last_successful_n43_download={}, is_temp_folder_for_n43_files={}'.format(
            self.last_successful_n43_download_dt,
            self.is_temp_folder_for_n43_files
        ))

        if self.last_successful_n43_download_dt and self.last_successful_n43_download_dt >= date_funcs.today():
            # Will not update db log - desired behavior
            self.logger.info("Already successfully downloaded N43 docs earlier today. Abort")
            return self.basic_result_success()

        self.set_db_logger(logger_name=project_settings.DB_LOGGER_NAME_N43)
        is_success = False
        exception_str = None  # type: Optional[str]
        try:
            result = self.main()  # type: MainResult
            result_code, _ = result
            if result_code in [result_codes.SUCCESS, result_codes.WRN_N43_DOWNLOAD_IS_NOT_ACTIVATED]:
                is_success = True  # to use in 'finally' block
            return result
        except Exception as e:
            exception_str = str(e)  # to use in 'finally' block
            raise e  # just allow it to bubble up
        finally:
            n_files_downloaded = self._get_number_of_n43_files_downloaded()
            self.logger.info('Save number of downloaded files: {}'.format(n_files_downloaded))
            if is_success:
                self.db_logger.accesos_log_info(
                    'N43 Access Successfully Downloaded: {} file(s)'.format(n_files_downloaded),
                    status='SUCCESS'
                )
            else:
                self.db_logger.accesos_log_error(
                    'N43 Access Failure: only {} file(s)'.format(n_files_downloaded),
                    exception_str=exception_str,
                    status='FAILURE'
                )

    def basic_scrape_for_mt940(self) -> MainResult:
        """
        Usage in MT940 scrapers (must override default scrape() method):
        def scrape(self) -> MainResult:
            return self.basic_scrape_for_mt940()
        """
        self.logger.info("== Scrape MT940 (using basic_scrape_for_mt940) ==")

        self.set_db_logger(logger_name=project_settings.DB_LOGGER_NAME_MT940)
        is_success = False
        exception_str = None  # type: Optional[str]
        try:
            result = self.main()  # type: MainResult
            result_code, _ = result
            if result_code in [result_codes.SUCCESS]:
                is_success = True  # to use in 'finally' block
            return result
        except Exception as e:
            exception_str = str(e)  # to use in 'finally' block
            raise e  # just allow it to bubble up
        finally:
            n_files_downloaded = self._get_number_of_mt940_files_downloaded()
            self.logger.info('Saved number of downloaded files: {}'.format(n_files_downloaded))
            if is_success:
                self.db_logger.accesos_log_info(
                    'MT940 Access Successfully Downloaded: {} file(s)'.format(n_files_downloaded),
                    status='SUCCESS'
                )
            else:
                self.db_logger.accesos_log_error(
                    'MT940 Access Failure: only {} file(s)'.format(n_files_downloaded),
                    exception_str=exception_str,
                    status='FAILURE'
                )

    def basic_save_excel_with_movs_pos(
            self,
            trade_point_id: int,
            filter_date: datetime.date,
            downloaded_at: datetime.datetime,
            file_content: bytes,
            file_extension='xls') -> bool:
        filename = '{}_{}.xls'.format(
            trade_point_id,
            downloaded_at.strftime('%Y%m%d_%H%M%S')
        )
        folder_path = os.path.join(project_settings.DOWNLOAD_POS_TO_FOLDER, filter_date.strftime('%Y%m%d'))
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                self.logger.warning(
                    "Can't create folder {}: probable reason: several attempts to create the folder "
                    "from different threads at the same time. Skip".format(folder_path)
                )
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)
        self.logger.info('{}: saved Excel file with POS collections to {}'.format(trade_point_id, filepath))
        return True

    def basic_get_pos_trade_points(self) -> List[POSTradePoint]:
        trade_points = self.db_connector.get_trade_points()
        self.logger.info('Got {} trade points: {}'.format(
            len(trade_points),
            [t.CommercialId for t in trade_points]
        ))
        return trade_points

    def basic_update_pos_trade_point(self, trade_point: POSTradePoint) -> bool:
        self.logger.info('Update trade point to: {}'.format(trade_point))
        if project_settings.IS_UPDATE_DB:
            self.db_connector.update_trade_point(trade_point)
            self.db_connector.update_pos_access_ts()
        return True

    def basic_save_pos_collections(self, pos_collections: List[POSCollection]) -> bool:
        if project_settings.IS_UPDATE_DB:
            self.db_connector.save_pos_collections_wo_movs(pos_collections)
            for pos_collection in pos_collections:
                self.db_connector.save_pos_movements(pos_collection)
                ok, reason = self.db_connector.link_to_general_movement(pos_collection)
                if not ok:
                    self.logger.warning("{}. Skip".format(reason))

        return True

    # Implement in children

    # def process_company(self, *args, **kwargs):
    #     """Real signature can be different at scraper level"""
    #     raise NotImplementedError
    #
    # def process_account(self, *args, **kwargs):
    #     """Real signature can de different at scraper level"""
    #     raise NotImplementedError
