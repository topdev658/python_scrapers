import datetime
from typing import List, Tuple

from custom_libs import date_funcs
from custom_libs import scrape_logger
from custom_libs.db import db_funcs
from project import result_codes
from project import settings as project_settings
from project.custom_types import (
    DBCustomerToUpdateState, DBFinancialEntityAccessWithCodesToUpdateState,
    DBAccount, DBFinancialEntityAccess
)

__version__ = '3.6.0'

__changelog__ = """
3.6.0
use account-level result_codes
3.5.0
call update_acc_set_mov_scrap_fin with 'success' flag
3.4.2
reset_by_timing: log level waring if detected 
3.4.1
fixed type hint
fmt
3.4.0
reset_forced: logger.warning instead of logger.error
3.3.0
StateResetByTiming logger name for corresponding process
3.2.2
msg fixed
3.2.1
fixed to: accounts_accesses.append((account, fin_ent_access))
3.2.0
msgs reformatted
login url info added for accesses and accounts for faster debugging
3.1.0
fin_ent_access err msg send only public info
3.0.0
reset_error_message instead of logger.error each time
2.1.0
changed ordering of state reset: 
- movements;
- balances;
- finEntAccess;
- customer.
2.0.3
fixed log msg (only account info, deleted redundant)
2.0.2
main default pass
2.0.1
renamed:
    UserFuncs.get_users_by_timing_for_status_reset
    LIMIT_PER_CUSTOMER_SCRAPING
2.0.0
reset_by_timing
"""

HTTP_STAT_RESP_CODE = 999
HTTP_STAT_RESP_CODE_DESCR = 'Not_implemented'


def reset_forced(db_customer_id, logger: scrape_logger.ScrapeLogger = None):
    """
    Clean up all states

    Set all scraping states to 0 for specific customer,
    notify if 1 found,
    doesn't matter how long the scraping goes
    """

    # to send one message for all
    reset_message = ''

    if not logger:
        logger = scrape_logger.ScrapeLogger('StateReset',
                                            db_customer_id, None)

    user = db_funcs.UserFuncs.get_user_for_status_reset(db_customer_id)
    if not user:
        logger.info("No user found with id={}. Skip".format(db_customer_id))
        return

    fin_ent_accesses = db_funcs.FinEntFuncs.get_fin_ent_accesses_all(user.Id)
    accounts_accesses = []  # type: List[Tuple[DBAccount, DBFinancialEntityAccess]]

    for fin_ent_access in fin_ent_accesses:
        accounts = db_funcs.AccountFuncs.get_accounts(fin_ent_access.Id)  # type: List[DBAccount]
        # Add explicit access details here to use login url later
        for account in accounts:
            accounts_accesses.append((account, fin_ent_access))

    # reset account state
    for account, access in accounts_accesses:
        if (not account.MovementsScrapingInProgress) and (not account.BalancesScrapingInProgress):
            continue

        hanged_at = 'Movements' if account.MovementsScrapingInProgress else 'Balances'

        reset_message += (
            '\n\nAccount {} from {}: {} '
            'scraping in progress found. Reset'.format(
                account,
                access.FinancialEntityAccessUrl,
                hanged_at
            ))

        db_funcs.AccountFuncs.update_acc_set_mov_scrap_fin(
            account.FinancialEntityAccountId,
            db_customer_id,
            result_codes.WRN_STATE_RESET
        )

    # reset finEntAccess scraping state
    for fin_ent_access in fin_ent_accesses:
        if fin_ent_access.ScrapingInProgress == 1:
            reset_message += (
                '\n\nFin_ent_access (Id={}, CustomerId={},  FinancialEntityId={}, LoginURL={}) '
                'scraping in progress found. Reset'.format(
                    fin_ent_access.Id,
                    fin_ent_access.CustomerId,
                    fin_ent_access.FinancialEntityId,
                    fin_ent_access.FinancialEntityAccessUrl,
                ))

            result_code = result_codes.ERR_COMMON_SCRAPING_ERROR

            fin_ent_acc_to_upd_state_with_codes = DBFinancialEntityAccessWithCodesToUpdateState(
                Id=fin_ent_access.Id,
                ScrapingInProgress=0,
                ScrapingStartedTimeStamp=date_funcs.convert_dt_to_db_ts_str(
                    fin_ent_access.LastScrapingStartedTimeStamp),
                ScrapingFinishedTimeStamp=date_funcs.now_for_db(),
                HttpStatusResponseCode=HTTP_STAT_RESP_CODE,
                HttpStatusResponseDescription=HTTP_STAT_RESP_CODE_DESCR,
                ResponseTesoraliaCode=result_code.code,
                ResponseTesoraliaDescription=result_code.description
            )

            db_funcs.FinEntFuncs.update_fin_ent_access_scrap_state_with_codes(
                fin_ent_acc_to_upd_state_with_codes)

    # reset user scraping state
    if user.ScrapingInProgress == 1:
        reset_message += (
            '\n\nCustomer (Id={}) scraping in progress found. Reset'.format(user.Id))
        # update user scraping finished
        db_funcs.UserFuncs.update_user_scraping_state(
            DBCustomerToUpdateState(
                Id=user.Id,
                ScrapingInProgress=0,
                # user.ScrapingStartedTimeStamp is datetime ts value
                ScrapingStartedTimeStamp=date_funcs.convert_dt_to_db_ts_str(
                    user.ScrapingStartedTimeStamp),
                ScrapingFinishedTimeStamp=date_funcs.now_for_db()))

    if reset_message:
        logger.warning(reset_message)


def reset_by_timing():
    """
    Clean up all states by timing:
    find user reached scraping time limit and reset states

    NOTE:
        The whole execution takes more than 1 minute if hanged
        scraping processes found,
        so don't call from cron to avoid multiple unfinished executions;
        use external python caller instead with delay between calls
    """
    time_limit = project_settings.LIMIT_PER_CUSTOMER_SCRAPING
    # filter by this time
    time_threshold = date_funcs.convert_dt_to_db_ts_str(
        date_funcs.now() - datetime.timedelta(seconds=time_limit))

    users = db_funcs.UserFuncs.get_users_by_timing_for_status_reset(time_threshold)
    for user in users:
        logger = scrape_logger.ScrapeLogger('StateResetByTiming',
                                            user.Id, None)
        logger.warning('FOUND USER REACHED THE SCRAPING TIME LIMIT. '
                       'Calling reset_forced to clean up')
        reset_forced(user.Id, logger)


if __name__ == '__main__':
    pass
    reset_forced(226770)
    print('DONE')
    # reset_by_timing()
