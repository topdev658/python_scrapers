"""
ALL get/select/should/check functions from should return values.
ALL add/update/set/delete functions should return None as they don't provide real DB results.
"""

import datetime
from typing import List, Optional, Tuple, Callable

from deprecated import deprecated

from custom_libs import date_funcs
from custom_libs.db import db_funcs
from custom_libs.log import log
from project import result_codes
from project.custom_types import (
    AccountSavedWithTempBalance, AccountScraped, CheckScraped, DBAccount,
    DBFinancialEntityAccessThirdLoginPass, CorrespondenceDocScraped, DocumentTextInfo,
    MovementSaved, MovementScraped, CheckCollectionScraped, DBOrganization,
    LeasingContractScraped, LeasingFeeScraped, CorrespondenceDocChecked,
    DBTransferAccountConfig, DBTransferFilter, TransferScraped, DBMovementConsideredTransfer,
    DBTransfer, MovementTPV, DBFinancialEntityAccessForN43, AccountToDownloadCorrespondence,
    POSTradePoint, POSCollection, ResultCode
)

__version__ = '8.33.0'

# TODO HANDLE HERE PROJECT_SETTINGS.IS_UPDATE_DB

__changelog__ = """
8.33.0 2023.07.31
get_deactivate_2fa: calls new db_funcs method to get deactivate2FA field from access
8.32.0 2023.06.26
get_movement_data_from_keyvalue: refactored fin_ent_account_id_suffix to fin_ent_account_id
8.31.0 2023.06.13
get_accounts_to_skip_download_correspondence: calls new db_funcs method to get accounts to skip correspondence
8.30.0 2023.06.13
correspondence_doc_upload: added self.financial_entity_access_id into the call to add_correspondence_doc method
8.29.0 2023.05.23
_mov_saved_by_dt_format: support Receipt and ReceiptChecksum fields
should_download_receipt_doc: modified type of return value to bool
get_account_id: calls new db_funcs method to get account_id
8.28.0 2023.05.09
upd deprecation marks
8.27.0 2023.04.27
should_download_receipt_doc: calls new db_funcs method to check if the movement already has a linked PDF
set_receipt_info: deleted has_related_entry_in_doc_table references because is deprecated
deleted deprecated methods
8.26.0
get_movement_data_from_keyvalue: added param (customer_id)
8.25.0
get_financial_entity_access_date_to_offset
8.24.0
get_accounts_saved: optional arg db_organization
8.23.0
set_receipt_info_for_mov:
  renamed from set_receipt_info 
  now doesn't accept receipt_description param 
    (bcs StatementReceiptDescription, field is removed)
removed old hist
8.22.0
set_receipt_info: has_related_entry_in_doc_table param
8.21.0
get_movement_data_from_keyvalue: renamed param (fin_ent_account_id_suffix)
8.20.0
get_mt940_last_successful_result_date_of_access
get_mt940_last_date_and_account_status
8.19.0
balances_upload: added fin_entity_id param
8.18.0
movements_upload: now accepts result_code
8.17.0
update_related_account_info
8.16.0
use source_channel
8.15.0
update_acc_set_mov_scrap_fin: use result_codes
check_and_mark_possible_inactive -> check_and_mark_possible_inactive_and_upd_attempt_ts
8.14.0
update_pos_access_ts
8.13.0
update_acc_set_mov_scrap_fin: now accepts 'success' flag for LastSuccessDownload field
movements_upload: upd for LastSuccessDownload
8.12.0
get_trade_points
update_trade_point
save_pos_collections_wo_movs
save_pos_movements
link_to_general_movement
8.11.0
restored should_download_correspondence (for transitional period)
8.10.0
should_download_correspondence_and_generic
get_accounts_to_download_correspondence
removed old changelog
8.9.0
get_fin_ent_access_for_n43
8.8.1
upd deprecation marks
8.8.0
get_account_custom_offset
8.7.0
save_movements_tpv
get_last_saved_movement_tpv
8.6.1
get_transfers_w_operational_date_in_range: fixed typing
8.6.0
get_transfers_w_operational_date_in_range
8.5.1
upd type hints
8.5.0
get_n43_last_date_and_account_status
8.4.0
correspondence_doc_upload: file_extension
8.3.0
get_movs_considered_transfers
8.2.0
get_active_transfers_accounts
get_active_transfers_filters
save_transfers_transactional
add_log_to_accesos_log
8.1.0
access-level should_download_correspondence
8.0.0
renamed CorrespondenceDocParsed, CorrespondenceDocScraped and appropriate methods
"""


class DBConnector:
    """
    the DBConnector suppose that
    if account updated - balance already scraped and updated here,
        so it can set BalancesScrapingInProgress to False
    if movements received - it can set MovementsScrapingInProgress to False
        in the end of method
    """

    def __init__(self, customer_id, financial_entity_access_id):
        self.customer_id = customer_id  # type: int
        self.financial_entity_access_id = financial_entity_access_id  # type: int

    def get_third_login_password(self) -> DBFinancialEntityAccessThirdLoginPass:
        third_log_pass = db_funcs.FinEntFuncs.get_financial_entity_access_third_login_pass(
            self.financial_entity_access_id
        )
        if not third_log_pass:
            raise Exception("Expected, but didn't get third_log_pass")

        return third_log_pass

    def update_accounts_scraping_attempt_timestamp(self) -> None:
        """Scraping attempt represents each scraping attempt,
        doesn't matter successful or now
        NOTE: if an access shares the account with another access,
            then only those accounts wil be updated
            which are linked right now to the current access
        """
        db_funcs.AccountFuncs.update_accounts_scraping_attempt_timestamp(
            self.financial_entity_access_id
        )

    def set_accounts_scraping_in_progress(self) -> None:
        """The timestamps affected by this funcstion may be rolled back
        on failed scraping attempt (if acc balance != last mov temp balance)"""
        db_funcs.AccountFuncs.set_accounts_scraping_in_progress(self.financial_entity_access_id)

    def get_accounts_saved(self, db_organization: Optional[DBOrganization] = None) -> List[DBAccount]:
        """Get all accounts of CustomerFinancialEntityAccessId
        Will be used for the 'rollback the balance' functionality.
        :param db_organization:
            if provided, then only accounts of this organization will be returned,
            (for now it's used to set custom statuses when failed on switching to a contract)
        """
        all_accounts_of_fin_ent_access = db_funcs.AccountFuncs.get_accounts(
            self.financial_entity_access_id,
            db_organization
        )  # type:List[DBAccount]
        return all_accounts_of_fin_ent_access

    def get_accounts_with_temp_balances(
            self,
            update_inactive_accounts: bool) -> List[AccountSavedWithTempBalance]:
        """Get accounts with temp_balances
        where temp_balance is the balance of the last movement
        """
        accounts_with_temp_balances = db_funcs.AccountFuncs.get_accounts_temp_balances(
            self.financial_entity_access_id,
            update_inactive_accounts
        )  # type:List[AccountSavedWithTempBalance]
        return accounts_with_temp_balances

    def check_account_is_active(self, fin_ent_account_id: str) -> bool:
        is_active = db_funcs.AccountFuncs.check_account_is_active(
            self.customer_id,
            fin_ent_account_id
        )
        return is_active

    def get_account_custom_offset(self, fin_ent_account_id: str) -> Optional[int]:
        custom_offset = db_funcs.AccountFuncs.get_account_custom_offset(
            self.customer_id,
            fin_ent_account_id
        )
        return custom_offset

    def balances_upload(
            self,
            accounts: List[AccountScraped],
            update_inactive_accounts: bool,
            source_channel: str,
            fin_entity_id: int) -> None:
        """accounts from one financial entity (default by design)"""

        db_funcs.AccountFuncs.add_accounts_and_organiz_or_update(
            accounts,
            self.financial_entity_access_id,
            update_inactive_accounts,
            source_channel=source_channel,
            fin_entity_id=fin_entity_id,
        )

    def accounts_rollback_ts_and_balances(
            self,
            accounts: List[DBAccount],
            update_inactive_accounts: bool) -> None:
        """Set necessary fields from provided accounts"""
        db_funcs.AccountFuncs.rollback_ts_and_balances(
            self.financial_entity_access_id,
            accounts,
            update_inactive_accounts
        )

    def update_related_account_info(
            self,
            fin_ent_account_id: str,
            related_account_info: str) -> None:
        db_funcs.AccountFuncs.update_related_account_info(
            self.financial_entity_access_id,
            fin_ent_account_id,
            related_account_info
        )

    def movements_upload(
            self,
            fin_ent_account_id: str,
            movements_scraped: List[MovementScraped],
            result_code: ResultCode) -> Optional[str]:
        """Upload movements and mark account as scrap finished

        :param fin_ent_account_id: use explicit parameter to handle case if there are no movements
        :param movements_scraped: scraped movements
        :param result_code: result code provided by BasicScraper (usually from integrity_helpers)
        :returns Optional[err_msg] from MovementFuncs.add_new_movements
        """
        log('DBConnector: movements_upload {}'.format(
            movements_scraped))

        err_msg = None
        try:
            if movements_scraped:
                err_msg = db_funcs.MovementFuncs.add_new_movements(
                    movements_scraped,
                    fin_ent_account_id,
                    self.customer_id
                )
            if err_msg:
                result_code = result_codes.ERR_CANT_INSERT_MOVEMENTS_DB_ERR
        finally:
            self.update_acc_set_mov_scrap_fin(fin_ent_account_id, result_code)
        return err_msg


    def update_acc_set_mov_scrap_fin(self, fin_ent_account_id: str, result_code: ResultCode) -> None:
        """only marks account as scrap finished"""
        db_funcs.AccountFuncs.update_acc_set_mov_scrap_fin(
            fin_ent_account_id,
            self.customer_id,
            result_code
        )

    def set_financial_entity_access_inactive(self) -> None:
        db_funcs.FinEntFuncs.set_fin_ent_access_inactive(
            self.customer_id,
            self.financial_entity_access_id
        )

    def get_last_movements_scraping_finished_date_str(
            self,
            fin_ent_account_id: str) -> Optional[str]:
        """
        return min(max(MaxValueDate), max(MaxOperationalDate)) of movements of the account
        """
        last_movements_datetime_dt_dict = db_funcs.AccountFuncs.get_last_movements_scraping_finished_ts(
            fin_ent_account_id,
            self.customer_id
        )

        if not last_movements_datetime_dt_dict.get('MaxOperationalDate'):
            return None

        return date_funcs.convert_db_timestamp_dt_to_scraper_date_str(
            last_movements_datetime_dt_dict['MaxOperationalDate']
        )

    def get_last_movements_scraping_finished_date_dt(
            self,
            fin_ent_account_id: str) -> Optional[datetime.datetime]:
        """
        return min(max(MaxValueDate), max(MaxOperationalDate)) of movements of the account
        """
        last_movements_datetime_dt_dict = db_funcs.AccountFuncs.get_last_movements_scraping_finished_ts(
            fin_ent_account_id,
            self.customer_id
        )

        if not last_movements_datetime_dt_dict.get('MaxOperationalDate'):
            return None

        return last_movements_datetime_dt_dict['MaxOperationalDate']

    def _mov_saved_by_dt_format(
            self,
            mov_dict: dict,
            datetime_convert_func: Callable[[datetime.datetime, ], str]) -> MovementSaved:
        export_timestamp_raw = mov_dict['ExportTimeStamp']
        export_timestamp = (date_funcs.convert_dt_to_db_ts_str(export_timestamp_raw)
                            if export_timestamp_raw else None)
        movement_saved = MovementSaved(
            Id=mov_dict['Id'],
            Amount=float(mov_dict['Amount']),  # from Decimal
            TempBalance=float(mov_dict['TempBalance']),  # from Decimal
            OperationalDate=datetime_convert_func(mov_dict['OperationalDate']),
            ValueDate=datetime_convert_func(mov_dict['ValueDate']),
            StatementDescription=mov_dict['StatementDescription'],
            OperationalDatePosition=mov_dict['OperationalDatePosition'],
            KeyValue=(mov_dict['KeyValue'] or '').strip(),
            CreateTimeStamp=date_funcs.convert_dt_to_db_ts_str(mov_dict['CreateTimeStamp']),
            ExportTimeStamp=export_timestamp,
            # Read the val from this DB's field or fill from Id if there were no renewed movs
            # (if there is no value in InitialId then this movement wasn't re-inserted yet)
            InitialId=mov_dict['InitialId'] or mov_dict['Id'],
            # Read the values from these DB fields
            # If there is no value then movement has not linked PDF
            Receipt=mov_dict['Receipt'],
            ReceiptChecksum=mov_dict['ReceiptChecksum']
        )

        return movement_saved

    def get_movements_since_date(self,
                                 fin_ent_account_id: str,
                                 date_from_str: str) -> List[MovementSaved]:
        """Use this function compare how many movements scraped last time and now"""

        movements_dicts = db_funcs.MovementFuncs.get_movements_after_first_movement_of_date(
            fin_ent_account_id,
            self.customer_id,
            date_from_str
        )

        if not movements_dicts:
            return []

        movements_saved = [
            self._mov_saved_by_dt_format(
                mov_dict,
                date_funcs.convert_dt_to_scraper_date_type3  # date fmt 20170130
            )
            for mov_dict in movements_dicts
        ]

        return movements_saved

    def get_one_movement_before_date(
            self,
            fin_ent_account_id: str,
            date_str: str) -> Optional[MovementSaved]:
        """Use this function to detect one date before
        :param fin_ent_account_id
        :param date_str: fmt 30/01/2019
        """

        mov_dict = db_funcs.MovementFuncs.get_one_movement_before_date(
            fin_ent_account_id,
            self.customer_id,
            date_str
        )

        if not mov_dict:
            return None

        movement_saved = self._mov_saved_by_dt_format(
            mov_dict,
            date_funcs.convert_dt_to_scraper_date_type1  # to fmt 30/01/2017
        )

        return movement_saved

    def get_last_movement_of_account(self, fin_ent_account_id: str) -> Optional[MovementSaved]:

        mov_dict = db_funcs.MovementFuncs.get_last_movement_of_account(
            fin_ent_account_id,
            self.customer_id
        )

        if not mov_dict:
            return None

        movement_saved = self._mov_saved_by_dt_format(
            mov_dict,
            date_funcs.convert_dt_to_scraper_date_type3  # date fmt 20170130
        )

        return movement_saved

    def get_first_movement_of_account(self, fin_ent_account_id: str) -> Optional[MovementSaved]:

        mov_dict = db_funcs.MovementFuncs.get_first_movement_of_account(
            fin_ent_account_id,
            self.customer_id
        )

        if not mov_dict:
            return None

        movement_saved = self._mov_saved_by_dt_format(
            mov_dict,
            date_funcs.convert_dt_to_scraper_date_type3  # date fmt 20170130
        )

        return movement_saved

    def delete_movements_since_date(self,
                                    fin_ent_account_id,
                                    date_from_str) -> None:

        # Synced call to be sure that movements were deleted before next step
        db_funcs.MovementFuncs.delete_movs_since_date(
            fin_ent_account_id,
            self.customer_id,
            date_from_str
        )

    def delete_movements_after_id(self,
                                  fin_ent_account_id,
                                  movement_id: int) -> None:

        # Synced call to be sure that movements were deleted before next step
        db_funcs.MovementFuncs.delete_movs_after_id(
            fin_ent_account_id,
            self.customer_id,
            movement_id
        )

    def check_and_mark_possible_inactive_and_upd_attempt_ts(self, accounts_fin_ent_ids: List[str]) -> None:
        all_accounts_of_fin_ent_access = db_funcs.AccountFuncs.get_accounts(
            self.financial_entity_access_id
        )  # type:List[DBAccount]

        scraped_fin_ent_accs_ids = []  # type: List[str]
        unscraped_fin_ent_accs_ids = []  # type: List[str]
        for acc in all_accounts_of_fin_ent_access:
            if acc.FinancialEntityAccountId in accounts_fin_ent_ids:
                scraped_fin_ent_accs_ids.append(acc.FinancialEntityAccountId)
            else:
                unscraped_fin_ent_accs_ids.append(acc.FinancialEntityAccountId)

        db_funcs.AccountFuncs.set_accounts_possible_inactive_and_upd_attempt_ts(
            scraped_fin_ent_accs_ids,
            self.customer_id,
            False
        )

        db_funcs.AccountFuncs.set_accounts_possible_inactive_and_upd_attempt_ts(
            unscraped_fin_ent_accs_ids,
            self.customer_id,
            True
        )

        return

    def should_download_receipts(self, account_fin_ent_id: str) -> bool:
        return db_funcs.AccountFuncs.check_should_download_receipts(account_fin_ent_id, self.customer_id)

    @deprecated(reason='Receipt and ReceiptChecksum updated on add_correspondence_doc method')
    def set_receipt_info_for_mov(
            self,
            account_fin_ent_id: str,
            mov_keyvalue: str,
            receipt_checksum: str) -> None:
        """Set Receipt=1 anf ReceiptChecksum (if provided)
        for the movement with mov_keyvalue
        """
        db_funcs.MovementFuncs.set_receipt_info(
            account_fin_ent_id,
            self.customer_id,
            mov_keyvalue,
            receipt_checksum
        )

    def set_movement_references(self, account_fin_ent_id: str, mov_keyvalue: str,
                                mov_reference1: str, mov_reference2: str) -> None:
        """Set StatementReference1 and StatementReference1 for the movement with mov_keyvalue"""
        if not (mov_reference1 or mov_reference2):
            return

        db_funcs.MovementFuncs.set_movement_references(
            account_fin_ent_id,
            self.customer_id,
            mov_keyvalue,
            mov_reference1,
            mov_reference2
        )

    def update_movements_extended_descriptions_if_necessary(
            self,
            fin_ent_account_id: str,
            movements_scraped: List[MovementScraped]) -> None:
        """Updates extended descriptions when necessary.

        'if necessary' means that the StatementExtendedDescription will be
        updated only with longer new StatementExtendedDescription (len(new) > len(old))

        It covers cases for BBVANetCash when sometimes it is possible to
        get later the extended description with more details.
        """

        if movements_scraped:
            db_funcs.MovementFuncs.update_extended_descriptions_if_necessary(
                movements_scraped,
                fin_ent_account_id,
                self.customer_id,
            )

    def update_movements_descriptions_if_necessary(
            self,
            fin_ent_account_id: str,
            movements_scraped: List[MovementScraped]) -> None:
        """Updates descriptions when necessary.

        'if necessary' means that the StatementDescription will be
        updated only with longer new StatementDescription (len(new) > len(old))

        It covers cases for RBS when there are no all
        'narrative #' vals for future/today movements for the moment,
        but then they appear
        """

        if movements_scraped:
            db_funcs.MovementFuncs.update_descriptions_if_necessary(
                movements_scraped,
                fin_ent_account_id,
                self.customer_id,
            )

    def get_financial_entity_reference_extractor(self) -> str:
        """Get a key to get a regexp associated with the financial entity to extract movement reference values"""
        return db_funcs.FinEntFuncs.get_financial_entity_reference_extractor(self.financial_entity_access_id)

    def get_customer_show_bankoffice_payer(self) -> Tuple[bool, bool]:
        """Validate if the bankoffice or payer should be shown

        :returns (show_bankoffice, show_payer)
        """
        return db_funcs.MovementFuncs.get_customer_show_bankoffice_payer(self.customer_id)

    def get_customer_reference_patterns(self) -> Tuple[str, str]:
        """Get regexps associated with the customer to extract movement reference values"""
        return db_funcs.MovementFuncs.get_customer_reference_patterns(self.customer_id)

    def get_organization(self, organization_title: str) -> Optional[DBOrganization]:
        """Get organization from organizaction title in fin_ent"""
        return db_funcs.FinEntFuncs.get_organization(self.customer_id, organization_title)

    def should_download_correspondence(self, fin_ent_access_id: int) -> bool:
        """Initial corresondence download logic implementation"""
        return db_funcs.DocumentFuncs.should_download_correspondence(self.customer_id, fin_ent_access_id)

    def should_download_correspondence_and_generic(self, db_fin_ent_access_id: int) -> Tuple[bool, bool]:
        """:return (scrapeCorrespondenceBool, scrapeGenericCorrespondenceBool)"""
        return db_funcs.DocumentFuncs.should_download_correspondence_and_generic(db_fin_ent_access_id)

    def get_accounts_to_download_correspondence(
            self,
            db_fin_ent_access_id: int) -> List[AccountToDownloadCorrespondence]:
        """:return [db_account_id]"""
        return db_funcs.DocumentFuncs.get_accounts_to_download_correspondence(db_fin_ent_access_id)

    def get_accounts_to_skip_download_correspondence(
            self,
            db_fin_ent_access_id: int) -> List[AccountToDownloadCorrespondence]:
        """:return [db_account_id]"""
        return db_funcs.DocumentFuncs.get_accounts_to_skip_download_correspondence(db_fin_ent_access_id)

    def check_add_correspondence_doc(
            self,
            corr_scraped: CorrespondenceDocScraped,
            product_to_fin_ent_fn: Optional[Callable[[str], str]] = None) -> CorrespondenceDocChecked:
        """Get [account , accountNo] for the document if its ok for add or [null, null] if not

        :param product_to_fin_ent_fn: a function to convert product_id to appropriate value
            for matching `FinancialEntityAccountId LIKE '%{product_to_fin_ent_fn(product_id)}'`.
            If not provided then default product_id[4:] will be used
        """
        return db_funcs.DocumentFuncs.check_add_correspondence_doc(
            corr_scraped,
            self.customer_id,
            product_to_fin_ent_fn
        )

    def should_download_receipt_doc(
            self,
            mov_keyvalue: str,
            fin_ent_account_id: str) -> bool:
        """Check if the movement already has a linked PDF
        :param mov_keyvalue
        :param fin_ent_account_id: FinancialEntityAccountId
        :returns 'True' if it has NOT linked PDF or 'False' if it has.
        """
        return db_funcs.DocumentFuncs.should_download_receipt_doc(
            mov_keyvalue,
            self.customer_id,
            fin_ent_account_id
        )

    def get_account_id(
            self,
            financial_entity_account_id: str) -> CorrespondenceDocChecked:
        """Get AccountId from FinancialEntityAccountId and CustomerId
        :param financial_entity_account_id: FinancialEntityAccountId
        :returns account_id
        """
        return db_funcs.DocumentFuncs.get_account_id(
            self.customer_id,
            financial_entity_account_id
        )

    def correspondence_doc_upload(self, corr_scraped: CorrespondenceDocScraped, file_extension: str) -> None:
        """Document upload without more checks
        :param corr_scraped: CorrespondenceDocScraped
        :param file_extension: 'PDF' or 'ZIP'
        """
        if corr_scraped:
            db_funcs.DocumentFuncs.add_correspondence_doc(
                corr_scraped,
                self.customer_id,
                file_extension,
                self.financial_entity_access_id
            )

    def get_movement_initial_ids_from_document_info(
            self,
            db_account_id: int,
            document_text_info: DocumentTextInfo) -> List[int]:
        """Get all matched movement_id from movements table
           for a document from the document text info.
           To use from more intellectual _get_document_movement_id rather than
           get_movement_initial_id_from_document_info
        """
        return db_funcs.DocumentFuncs.get_movement_initial_ids_from_document_info(db_account_id, document_text_info)

    def check_if_exists_correspondence_doc_movement_initial_id(self, mov_id: int) -> bool:
        """Check if this mov initial id is already assigned to a company document"""
        return db_funcs.DocumentFuncs.check_if_exists_correspondence_doc_movement_initial_id(mov_id)

    def should_download_checks(self) -> bool:
        return db_funcs.DocumentFuncs.should_download_checks(self.customer_id)

    def check_add_checks(self, keyvalue_lst: List[str]) -> List[str]:
        """From scraped checks keyvalue list, return the keyvalue list of those already saved"""
        return db_funcs.DocumentFuncs.check_add_checks(keyvalue_lst, self.customer_id)

    def add_check(self, check_scraped: CheckScraped, collection_id: int) -> None:
        """Add the check_scraped without more checkings"""
        log('DBConnector: (1)add_check {}'.format(check_scraped))
        if check_scraped:
            db_funcs.DocumentFuncs.add_check(check_scraped, collection_id)

    # TODO return more specific type
    def get_movement_initial_id_from_check_collection_data(
            self,
            check_collection_scraped: CheckCollectionScraped,
            desc_keywords: str) -> Optional[dict]:
        """Get movement initial id for the check"""
        return db_funcs.DocumentFuncs.get_movement_initial_id_from_check_collection_data(
            check_collection_scraped,
            self.customer_id,
            desc_keywords
        )

    def check_add_check_collections(self, keyvalue_lst: List[str]) -> List[str]:
        """From scraped check collections keyvalue list, return the keyvalue list of those already saved"""
        return db_funcs.DocumentFuncs.check_add_check_collections(keyvalue_lst, self.customer_id)

    def add_check_collection(self, check_collection_scraped: CheckCollectionScraped) -> Optional[int]:
        """Add the check_collection_scraped without more checkings
        :returns Optional[SCOPE_IDENTITY()]
        """
        log('DBConnector: (1)add_check_collection {}'.format(check_collection_scraped))
        if check_collection_scraped:
            return db_funcs.DocumentFuncs.add_check_collection(check_collection_scraped)
        return None

    def delete_check_collection(self, check_collection_scraped: CheckCollectionScraped) -> None:
        """Delete the check_collection_scraped without more checkings
        On cascade checks of the collections will be deleted also"""
        if check_collection_scraped:
            db_funcs.DocumentFuncs.delete_check_collection(
                check_collection_scraped.KeyValue,
                self.customer_id
            )

    def get_movement_data_from_keyvalue(
            self,
            mov_keyvalue: str,
            fin_ent_account_id: str,
            customer_id: int) -> Optional[dict]:
        """Get the movement data from movements table for a movement key value
        :param mov_keyvalue:
        :param fin_ent_account_id: full fin_ent_account_id
        :param customer_id:
        """
        return db_funcs.MovementFuncs.get_movement_data_from_keyvalue(
            mov_keyvalue,
            fin_ent_account_id,
            customer_id,
        )

    def save_check_collection_transactional(
            self,
            check_collection_scraped: CheckCollectionScraped,
            checks_scraped: List[CheckScraped]) -> Tuple[bool, str]:
        log('DBConnector: (1)save_check_collection_transactional {}'.format(check_collection_scraped))
        if check_collection_scraped and checks_scraped:
            return db_funcs.DBTransactionalOperations.save_check_collection_transactional(
                check_collection_scraped,
                checks_scraped,
                self.customer_id
            )
        return False, ""

    def should_download_leasing(self) -> bool:
        return db_funcs.DocumentFuncs.should_download_leasing(self.customer_id)

    def get_saved_leasing_contracts_keyvalues(self, keyvalue_lst: List[str]) -> List[str]:
        """From scraped leasing contracts keyvalue list, return the keyvalue list of those already saved"""
        return db_funcs.DocumentFuncs.get_saved_leasing_contracts_keyvalues(keyvalue_lst, self.customer_id)

    def get_incomplete_leasing_contracts_keyvalues(self, keyvalue_lst: List[str]) -> List[str]:
        """From scraped leasing contracts keyvalue list, return the keyvalue list of those
        that still have fees to scrap"""
        return db_funcs.DocumentFuncs.get_incomplete_leasing_contracts_keyvalues(keyvalue_lst, self.customer_id)

    def get_paid_fees_keyvalues_for_leasing_contract(self, leasing_contract: LeasingContractScraped) -> List[str]:
        """Get the list of paid fees keyvalues for the leasing contract"""
        return db_funcs.DocumentFuncs.get_paid_fees_keyvalues_for_leasing_contract(leasing_contract, self.customer_id)

    def add_or_update_leasing_contract(self, leasing_contract_scraped: LeasingContractScraped) -> Optional[int]:
        """Add or update the leasing_contract_scraped without more checkings
        :returns Optional[Id]
        """
        log('DBConnector: (1)add_or_update_leasing_contract {}'.format(leasing_contract_scraped))
        if leasing_contract_scraped:
            return db_funcs.DocumentFuncs.add_or_update_leasing_contract(leasing_contract_scraped)
        return None

    def get_leasing_fees_with_movement_id_keyvalues(self, leasing_contract: LeasingContractScraped) -> List[str]:
        """Get the list of fees with movement_id keyvalues for the leasing contract"""
        return db_funcs.DocumentFuncs.get_leasing_fees_with_movement_id_keyvalues(leasing_contract, self.customer_id)

    def get_movement_initial_id_from_leasing_fee_data(
            self,
            leasing_fee_scraped: LeasingFeeScraped,
            desc_keywords: str) -> Optional[dict]:
        """Get movement id for the leasing fee"""
        return db_funcs.DocumentFuncs.get_movement_initial_id_from_leasing_fee_data(
            leasing_fee_scraped,
            self.customer_id,
            desc_keywords
        )

    def add_leasing_fee(self, leasing_fee_scraped: LeasingFeeScraped, contract_id: int) -> None:
        """Add the leasing_fee_scraped without more checkings"""
        log('DBConnector: (1)add_leasing_fee {}'.format(leasing_fee_scraped))
        if leasing_fee_scraped:
            db_funcs.DocumentFuncs.add_leasing_fee(leasing_fee_scraped, contract_id)

    def delete_leasing_fee(self, leasing_fee_scraped: LeasingFeeScraped) -> None:
        """Delete the leasing_fee_scraped without more checkings"""
        if leasing_fee_scraped:
            db_funcs.DocumentFuncs.delete_leasing_fee(leasing_fee_scraped.KeyValue)

    def save_or_update_leasing_contract_transactional(self,
                                                      leasing_contract_scraped: LeasingContractScraped,
                                                      fees_scraped: List[LeasingFeeScraped]) -> Tuple[bool, str]:
        log('DBConnector: (1)save_or_update_leasing_contract_transactional {}'.format(leasing_contract_scraped))
        if leasing_contract_scraped and fees_scraped:
            return db_funcs.DBTransactionalOperations.save_or_update_leasing_contract_transactional(
                leasing_contract_scraped,
                fees_scraped,
                self.customer_id
            )
        return False, ""

    @deprecated(reason='must use get_n43_last_date_and_account_status')
    def get_n43_last_date_of_account(
            self,
            fin_ent_account_id: str) -> Optional[datetime.datetime]:
        return db_funcs.N43Funcs.get_n43_last_date_of_account(fin_ent_account_id)

    def get_n43_last_date_and_account_status(
            self,
            fin_ent_account_id: str) -> Optional[Tuple[Optional[datetime.datetime], bool]]:
        """:return: Optional[LastN43StatementDate, IsAccountActive]"""
        return db_funcs.N43Funcs.get_n43_last_date_and_account_status(self.customer_id, fin_ent_account_id)

    def get_mt940_last_date_and_account_status(
            self,
            account_no: str) -> Optional[Tuple[Optional[datetime.datetime], bool]]:
        """:return: Optional[LastMT940StatementDateOpt, IsAccountActive]"""
        return db_funcs.MT940Funcs.get_mt940_last_date_and_account_status(self.customer_id, account_no)

    @deprecated('accesos_Log must be used')
    def add_n43_successful_results_for_access(
            self,
            started_at: datetime.datetime,
            num_files: int):
        return db_funcs.N43Funcs.add_n43_successful_results_for_access(
            self.financial_entity_access_id,
            started_at,
            num_files,
        )

    def get_n43_last_successful_result_date_of_access(self) -> Optional[datetime.datetime]:
        return db_funcs.N43Funcs.get_n43_last_successful_result_date_of_access(
            self.financial_entity_access_id
        )

    def get_mt940_last_successful_result_date_of_access(self) -> Optional[datetime.datetime]:
        return db_funcs.MT940Funcs.get_mt940_last_successful_result_date_of_access(
            self.financial_entity_access_id
        )

    def get_fin_ent_access_for_n43(self) -> Optional[DBFinancialEntityAccessForN43]:
        return db_funcs.FinEntFuncs.get_fin_ent_access_for_n43(self.customer_id, self.financial_entity_access_id)

    def get_active_transfers_accounts(self) -> List[DBTransferAccountConfig]:
        """
        Get all accounts with transfers instrument active
        """
        all_accounts_of_fin_ent_access_w_transfers_active = db_funcs.TransfersFuncs.get_active_transfers_accounts(
            self.financial_entity_access_id
        )  # type:List[DBTransferAccountConfig]
        return all_accounts_of_fin_ent_access_w_transfers_active

    def get_movs_considered_transfers(
            self,
            db_account_id: int,
            fin_ent_account_id: str,
            date_from: datetime.datetime) -> List[DBMovementConsideredTransfer]:
        movs_cosidered_transfs = db_funcs.TransfersFuncs.get_movs_considered_transfers(
            db_account_id,
            fin_ent_account_id,
            date_from
        )
        return movs_cosidered_transfs

    def get_active_transfers_filters(self,
                                     db_account_id: int,
                                     navigation_type: str) -> List[DBTransferFilter]:
        """
        Get all active transfer filters for given account and navigation_type
        """
        all_active_transfers_filters_of_fin_ent_account_id = db_funcs.TransfersFuncs.get_active_transfers_filters(
            db_account_id,
            navigation_type
        )  # type:List[DBTransferFilter]
        return all_active_transfers_filters_of_fin_ent_account_id

    def save_transfers_transactional(self,
                                     db_account_id: int,
                                     transfers_scraped: List[TransferScraped]) -> Tuple[bool, str]:
        if db_account_id:  # TODO: VB: why checking? can it be 0??
            return db_funcs.DBTransactionalOperations.save_transfers_transactional(
                db_account_id,
                transfers_scraped
            )
        return False, ""

    def get_transfers_w_operational_date_in_range(
            self,
            account_id: int,
            from_operational_date_str: str,
            to_operational_date_str: str) -> List[DBTransfer]:
        """
        Get all transfer with for customer and account with operational date in range
        """
        transfers = db_funcs.TransfersFuncs.get_transfers_w_operational_date_in_range(
            account_id,
            from_operational_date_str,
            to_operational_date_str,
        )  # type:List[DBTransfer]
        return transfers

    def get_last_saved_movement_tpv(self, company_no: str) -> Optional[MovementTPV]:
        return db_funcs.MovementTPVFuncs.get_last_movement_tpv(
            self.financial_entity_access_id,
            company_no
        )

    def save_movements_tpv(self, company_no: str, movements_tpv_asc: List[MovementTPV]) -> None:
        """Saves movements_tpv_asc in DB. Uses add_new_movements_tpv to save only new movements.
        movements_tpv must be ordered ASC (movements_tpv_asc)
        """
        db_funcs.MovementTPVFuncs.add_new_movements_tpv(
            self.financial_entity_access_id,
            company_no,
            movements_tpv_asc
        )

    def get_trade_points(self) -> List[POSTradePoint]:
        return db_funcs.POSFuncs.get_trade_points(self.financial_entity_access_id)

    def update_trade_point(self, trade_point: POSTradePoint) -> None:
        db_funcs.POSFuncs.update_trade_point(trade_point)

    def save_pos_collections_wo_movs(self, pos_collections: List[POSCollection]) -> None:
        db_funcs.POSFuncs.add_new_pos_collections_wo_movs(self.customer_id, pos_collections)

    def save_pos_movements(self, pos_collection: POSCollection) -> None:
        db_funcs.POSFuncs.add_new_pos_movements(self.customer_id, pos_collection)

    def link_to_general_movement(self, pos_collection: POSCollection) -> Tuple[bool, str]:
        """
        :return: (ok, reason)
        """
        return db_funcs.POSFuncs.link_to_general_movement(self.customer_id, pos_collection)

    def update_pos_access_ts(self) -> None:
        db_funcs.POSFuncs.update_pos_access_ts(self.financial_entity_access_id)

    def get_financial_entity_access_date_to_offset(self, fin_ent_access_id: int) -> Optional[int]:
        date_to_offset = db_funcs.AccessFuncs.get_financial_entity_access_date_to_offset(
            fin_ent_access_id
        )
        return date_to_offset

    def get_deactivate_2fa(self, fin_ent_access_id: int) -> bool:
        """Check if the access has 'deactivate2FA'
        :param fin_ent_access_id: access
        :returns 'deactivate2FA' field value"""
        return db_funcs.AccessFuncs.get_deactivate_2fa(fin_ent_access_id)
