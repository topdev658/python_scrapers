import datetime
from datetime import datetime as dt
from collections import OrderedDict
from typing import List, Sequence, Union, Optional, Tuple

from custom_libs import extract
from custom_libs import date_funcs
from custom_libs.db.db_connector_for_scraper import DBConnector
from custom_libs.scrape_logger import ScrapeLogger
from project import result_codes
from project import settings as project_settings
from project.custom_types import AccountScraped, MovementSaved, MovementScraped, ResultCode

__version__ = '3.3.0'

__changelog__ = """
3.3.0 2023.10.03
check_balance_integrity: 
    update account movements without scraped pivot movement (because max offset limit) when balance integrity is ok
    avoid wrong updates from manual launches (-f/-o) or when the last movement saved is recent
3.2.0 2023.07.19
check_balance_integrity: added log when return ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS
3.1.0 2023.07.13
check_balance_integrity: Check balance integrity when there is no movement saved for de scraping period and there is one last movement saved.
3.0.0
removed obsolete is_try_autofix_on_integrity_error
udd log msgs
more result_codes for date limit
also see commit FEW_MOVEMENTS_REACHED_DATE_LIMIT
2.2.0
use result_codes
2.1.0
try_autofix_balance_integrity_error: detect 'probably inactive' accounts
upd log msgs
2.0.0
date_from_str, date_to_str in err reports
1.3.1
better type hints&checks
1.3.0
check_balance_integrity: handle new case if the OpDatePos of the 1st mov_scraped > 1
1.2.4
check_balance_integrity: don't push warning to sentry if the balance is still correct
1.2.3
fixed typo
1.2.2
don't push html msgs to sentry (because they duplicate txt msgs)
1.2.1
type hints
1.2.0
try_autofix_balance_integrity_error: do not delete broken movements if is_update_db == false
more type hints
1.1.0
send movs in err email as html table
1.0.1
check_movements_scraped_consistency: upd log msg
"""


def _format_list(movements: Union[Sequence[MovementSaved], Sequence[MovementScraped]]) -> str:
    return '\n\n'.join(str(mov) for mov in movements) + '\n'


def _as_html_table(movements: Union[Sequence[MovementSaved], Sequence[MovementScraped]]) -> str:
    """Only for List[MovementSaved] and List[MovementScraped]"""
    fields_to_export = OrderedDict([
        ('OperationalDate', 'OpDate'),
        ('ValueDate', 'ValDate'),
        ('StatementDescription', 'Descr'),
        ('Amount', 'Amount'),
        ('TempBalance', 'TempBal'),
        ('OperationalDatePosition', 'DatePos'),
        ('KeyValue', 'Key'),
    ])
    h = '<table cellspacing="0">'
    # title
    h += '<tr>'
    for f in fields_to_export.values():
        h += '<th>{}</th>'.format(f)
    h += '</tr>'
    # rows
    for mov in movements:
        h += '<tr>'
        for f_name, f_name_short in fields_to_export.items():
            val = ''
            try:
                val = getattr(mov, f_name)
                if f_name == 'KeyValue':
                    val = val[:6]
            except:
                pass
            h += '<td>{}</td>'.format(val)
        h += '</tr>'
    h += '</table>'
    return h


def is_equal_movements(movement_saved: MovementSaved,
                       movement_scraped: MovementScraped) -> bool:
    # Handle transitional period
    # Check all parameters explicitly
    if (not movement_saved.KeyValue) or (movement_saved.KeyValue == 'null'):
        if (movement_scraped.OperationalDate != movement_saved.OperationalDate
                and movement_scraped.ValueDate == movement_saved.ValueDate
                and movement_scraped.OperationalDatePosition == movement_saved.OperationalDatePosition
                and movement_scraped.Amount == movement_saved.Amount
                and movement_scraped.TempBalance == movement_saved.TempBalance):
            return False
        else:
            return True

    # Check balance integrity by KeyValue
    if movement_saved.KeyValue != movement_scraped.KeyValue:
        return False

    return True


def check_movements_scraped_consistency(logger: ScrapeLogger,
                                        account_scraped: AccountScraped,
                                        movements_scraped: List[MovementScraped]) -> bool:
    """
    This checker checks the movements_scraped consistency.
    It calculates TempBalance for the next movement (of the list of the movements)
    basing on its Amount and the TempBalance of the previous movement.
    Calculated and scraped balances should be the same.
    If not, the checker sends BALANCE INTEGRITY ERROR notification and returns False

    :param logger: the instance of the logger, usually self.logger of the caller
    :param account_scraped: currently scraped account info
    :param movements_scraped: ascending ordering (the last is the most recent)
    :return: is_consistent_movements: bool (True - no errors, False - BALANCE INTEGRITY ERROR)
    """
    temp_balance_calculated = None
    for movement_scraped in movements_scraped:
        # init temp_balance_calculated
        if temp_balance_calculated is None:
            temp_balance_calculated = movement_scraped.TempBalance
            continue

        temp_balance_calculated = temp_balance_calculated + movement_scraped.Amount
        if round(temp_balance_calculated, 2) != round(movement_scraped.TempBalance, 2):
            msg_pattern = ('{}: BALANCE INTEGRITY ERROR: INCONSISTENT movements scraped:\n'
                           'Calculated temp_balance {} != scraped {}\nfor {}\n\n'
                           'Movements SCRAPED: {}')
            logger.error(msg_pattern.format(
                account_scraped.FinancialEntityAccountId,
                round(temp_balance_calculated, 2),
                movement_scraped.TempBalance,
                movement_scraped,
                _format_list(movements_scraped)
            ), is_send_email=False)

            logger.error(msg_pattern.format(
                account_scraped.FinancialEntityAccountId,
                round(temp_balance_calculated, 2),
                movement_scraped.TempBalance,
                movement_scraped,
                _as_html_table(movements_scraped)
            ), is_print=False, is_sentry=False, is_html=True)

            return False

    return True


def check_temp_balance_of_last_movement_scraped(logger: ScrapeLogger,
                                                account_scraped: AccountScraped,
                                                movements_scraped: List[MovementScraped]) -> bool:
    """
    The checker compares account_scraped.Balance and last_movement_scraped.Tempbalance
    It expects that account_scraped.Balance == last_movement_scraped.TempBalance
    or it means that there is BALANCE INTEGRITY ERROR

    If there are no movements_scraped, the checker returns True (there is another checker
    for this case)

    :param logger: the instance of the logger, usually self.logger of the caller
    :param account_scraped: currently scraped account
    :param movements_scraped: currently scraped movements in asc ordering (the last is the most recent)
    :return: is_correct_temp_balance_of_last_movement_scraped: bool
            (True - correct, no error; False - BALANCE INTEGRITY ERROR)
    """

    if movements_scraped and (account_scraped.Balance != movements_scraped[-1].TempBalance):
        msg_pattern = ('{}: BALANCE INTEGRITY ERROR: DIFFERENT account.Balance and '
                       'last_movement_scraped.TempBalance\n'
                       'Should upload (due to the settings): {}\n'
                       'ACCOUNT:\n{}\n'
                       'LAST MOVEMENT_SCRAPED:\n{}\n')
        logger.error(msg_pattern.format(
            account_scraped.FinancialEntityAccountId,
            project_settings.IS_UPLOAD_MOVEMENTS_ON_BALANCE_INTEGRITY_ERROR,
            account_scraped,
            movements_scraped[-1]
        ))

        return False

    return True


def check_balance_integrity(logger: ScrapeLogger,
                            account_scraped: AccountScraped,
                            movements_scraped: List[MovementScraped],
                            movements_saved: List[MovementSaved],
                            date_from_str: str,
                            date_to_str: str,
                            min_allowed_date_from: datetime,
                            last_movement_saved: MovementSaved) -> Tuple[bool, ResultCode]:
    """
    This checker provides 3 checkups:

    1. If there are no movements_scraped, but there are movements_saved (movements in the DB)
    of the date (the date is the date_from for the current scraping process),
    that means that there is a probability of balance integrity error,
    because the scraper had to extract at least movements of the date that already in the DB.

    In this case the checker sends warning if the account.Balance == last_movement_saved.TempBalance or
    it send BALANCE INTEGRITY ERROR if account.Balance already != last_movement_saved.TempBalance.

    2. The checker compares each of the movements_saved to each of the corresponding movement
    of the movements_scraped by index (first of the movements_saved should be == first of the movements_scraped)
    and all of them should be the same by result of `is_equal_movements` function.

    There are several cases:
        2.1 Scraped less movements than already saved (error on access by index)
        2.2 There is movement_saved != corresponding movement_scraped

    3. Check balance integrity when there is no movement saved for de scraping period and there is one last movement saved.

    In both cases the checker returns False.
    If is_try_autofix_on_integrity_error != True, the checker sends BALANCE INGERITY ERROR notification immediately,
    or it expects that the caller will call the `try_autofix_balance_integrity_error` function,
    and the message will be sent from `try_autofix_balance_integrity_error` basing on its results.

    :param logger: the instance of the logger, usually self.logger of the caller
    :param account_scraped: currently scraped account
    :param movements_scraped: currently scraped movements in asc ordering (the last is the most recent)
    :param movements_saved: movements from the DB started since date_from (same date for the movements_scraped)
    :param date_from_str: for err reports
    :param date_to_str: for err reports
    :param min_allowed_date_from: to detect ...FEW_MOVEMENTS_REACHED_DATE_LIMIT
    :param last_movement_saved: last movement from DB

    :return is_balance_correct: bool (True - correct balance, False - BALANCE INTEGRITY ERROR)
    """

    fin_ent_account_id = account_scraped.FinancialEntityAccountId
    date_from = date_funcs.get_date_from_str(date_from_str)
    offset_limit_dt = datetime.datetime.now() - datetime.timedelta(days=70)
    logger.info('{}: check balance integrity: start'.format(fin_ent_account_id))

    # No previously scraped movements - no balance integrity error
    if not movements_saved:
        # Check balance integrity when there is no movement saved for the scraping period and there is one last movement saved.
        if movements_scraped and last_movement_saved:
            last_movement_saved_dt = date_funcs.get_date_from_str(last_movement_saved.OperationalDate, '%Y%m%d')
            movement_scraped_equal_to_last_movement_saved = [movement_scraped for movement_scraped in movements_scraped if is_equal_movements(last_movement_saved, movement_scraped)]
            if not movement_scraped_equal_to_last_movement_saved:
                # Avoid wrong updates from manual launches (-f/-o) or when the last movement saved is recent
                if date_from < offset_limit_dt and last_movement_saved_dt < offset_limit_dt:
                    # Update account movements without scraped pivot movement (because max offset limit) when balance integrity is ok
                    # Sometimes the result of the sum is not correct since many decimals appear, rounded to 2 decimals to compare correctly
                    if round(last_movement_saved.TempBalance + movements_scraped[0].Amount,2) == movements_scraped[0].TempBalance:
                        logger.info('{}: check balance integrity: Last movement saved not in scraped movements '
                                    'but same balance. Insert scraped movements'.format(fin_ent_account_id))
                        return True, result_codes.SUCCESS
                    else:
                        logger.error('{}: check balance integrity: Last movement saved not in scraped movements '
                                     'and wrong balance integrity '
                                     '{}'.format(fin_ent_account_id, last_movement_saved))
                        return False, result_codes.ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS
                else:
                    logger.error('{}: check balance integrity: Last movement saved not in scraped movements '
                                     ' and recent date_from or last movement saved '
                                     '{}'.format(fin_ent_account_id, last_movement_saved))
                    return False, result_codes.ERR_LAST_MOVEMENT_SAVED_NOT_IN_SCRAPED_MOVEMENTS

        logger.info('{}: check balance integrity: No previous movements. '
                    'PASSED'.format(fin_ent_account_id))
        return True, result_codes.SUCCESS

    movement_saved_last = movements_saved[-1]

    # Check for OperationalDatePosition in all movements_saved
    for movement_saved in movements_saved:
        if not movement_saved.OperationalDatePosition:
            return False, result_codes.ERR_BALANCE_BAD_DB_DATA

    # If there are no movements_scraped - this is possible balance integrity error in the future,
    # but now just send warning notification if scraped account balance == last mov tempbalance
    if not movements_scraped:
        if movement_saved_last.TempBalance == account_scraped.Balance:
            if date_from <= min_allowed_date_from:
                result_code = result_codes.WRN_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT
                msg_part = 'Reached HISTORICAL MOVEMENTS LIMIT (DATE LIMIT).'
            else:
                result_code = result_codes.WRN_FEW_MOVEMENTS
                msg_part = 'If -f used, check it (could miss some movements before), consider using -o param.'
            logger.warning(
                '{}: dates from {} to {}: no movements scraped, but expected to scrape again at least '
                'last saved movement.\n'
                'Balance is still correct.\n'
                'ACCOUNT:\n{}\n\n'
                '{}\n\n'
                'LAST SAVED MOVEMENT:\n{}\n\n'
                'CURRENTLY SCRAPED:\n{}\n'.format(
                    fin_ent_account_id,
                    date_from_str,
                    date_to_str,
                    account_scraped,
                    msg_part,
                    movement_saved_last,
                    _format_list(movements_scraped)
                ),
                is_sentry=True
            )
            return True, result_code
        else:
            result_code = (result_codes.ERR_BALANCE_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT
                           if date_from <= min_allowed_date_from
                           else result_codes.ERR_BALANCE_FEW_MOVEMENTS)
            # Will try to fix try_autofix_balance_integrity_error
            return False, result_code

    # BASIC CHECKUP
    # Compare same positions one to one
    # The date of 1st of movements_saved is equal of the date of 1st of movs_scraped
    # by design (the logic is in basic_scraper.basic_upload_movements_scraped
    ix = -1
    must_check_oper_date_position = True
    oper_date_position_first_scraped = movements_scraped[0].OperationalDatePosition
    for movement_saved in movements_saved:
        # Skip movements_saved for incremental scraping if oper_date_position_first_scraped > 1
        if must_check_oper_date_position and (
                movement_saved.OperationalDatePosition < oper_date_position_first_scraped):
            continue
        # Already aligned movements, then shouldn't do it to avoid false-positive
        # balance integrity errors -> set False
        must_check_oper_date_position = False
        ix += 1  # start from 0
        movement_scraped = extract.by_index_or_none(movements_scraped, ix)
        if not movement_scraped:
            return False, result_codes.ERR_BALANCE_FEW_MOVEMENTS

        if not is_equal_movements(movement_saved, movement_scraped):
            # Back comp, generally tells: 'found different movements'
            # Earlier it was possible to save on this case
            return False, result_codes.ERR_BALANCE_SAVED_UNFIXED

    if ix == -1:
        return False, result_codes.ERR_BALANCE_NO_PIVOT_MOVEMENT

    logger.info('{}: check balance integrity: PASSED'.format(fin_ent_account_id))

    return True, result_codes.SUCCESS


def try_autofix_balance_integrity_error(
        logger: ScrapeLogger,
        db_connector: DBConnector,
        is_balance_correct: bool,
        account_scraped: AccountScraped,
        movements_scraped: List[MovementScraped],
        movements_saved: List[MovementSaved],
        date_from_str: str,
        date_to_str: str,
        min_allowed_date_from: dt) -> Tuple[bool, ResultCode]:
    """
    Call it only when balance integrity error detected
    and project_settings.IS_OVERWRITE_MOVEMENTS_TO_FIX_BALANCE_INTEGRITY_ERROR == True

    Sends different notifications when:
        - not fixed
        - fixed since last scraped date
        - fixed since not last scraped date
        - detected 'probably inactive' account

    IMPORTANT: All movements in the DB should have OperationalDatePosition

    Also, it is necessary only for an attempt to for non-incremental movements
    because incremental ones (OperationalDatePosition > 1) already with correct balance.

    :param movements_scraped: scraped just now movements in ascending ordering
    :param movements_saved: movements from the DB of same dates in ascending ordering
    :param date_from_str: for err reports
    :param date_to_str: for err reports
    :param min_allowed_date_from: to detect ...FEW_MOVEMENTS_REACHED_DATE_LIMIT
    :return: True - fixed balance integrity error; False - not fixed
    """
    # Additional checkup
    if not (movements_scraped or movements_saved):
        return is_balance_correct, result_codes.SUCCESS

    fin_ent_account_id = account_scraped.FinancialEntityAccountId
    date_from = date_funcs.get_date_from_str(date_from_str)

    # Special case:
    # No scraped movements at all with changed account_balance
    # the date of 1st movement_saved is very old.
    # Suggestion: we got a closed account if balance = 0

    # If got the err when date_from > min_allowed_date_from,
    # it generally tells about missed movements
    # between min_allowed_date_from and date_from (due to -f param)

    if (not movements_scraped
            and (dt.strptime(movements_saved[0].OperationalDate, project_settings.DB_DATE_FMT)
                 < date_from)):
        if date_from <= min_allowed_date_from:
            result_code = result_codes.ERR_BALANCE_FEW_MOVEMENTS_HISTORICAL_DATE_LIMIT
            msg_part = 'Reached HISTORICAL MOVEMENTS LIMIT (DATE LIMIT).'
        else:
            result_code = result_codes.ERR_BALANCE_FEW_MOVEMENTS
            msg_part = 'If -f used, check it (could miss some movements before), consider using -o param.'
        msg_part2 = 'Account is PROBABLY INACTIVE' if account_scraped.Balance == 0 else ''

        msg_pattern = ("{}: dates from {} to {}: BALANCE INTEGRITY ERROR:\n"
                       "no scraped movements and the last saved movement is too old\n"
                       "Current account balance = {}\n"
                       "{}\n{}\n"
                       "SAVED:\n{}\nSCRAPED:\n{}")
        logger.error(msg_pattern.format(
            account_scraped.FinancialEntityAccountId,
            date_from_str,
            date_to_str,
            account_scraped.Balance,
            msg_part,
            msg_part2,
            movements_saved,
            movements_scraped
        ), is_sentry=True)

        return False, result_code

    last_correct_movement = None  # type: Optional[MovementSaved]
    first_broken_mov_saved = None  # type: Optional[MovementSaved]
    first_broken_mov_scraped = None  # type: Optional[MovementScraped]
    first_broken_ix = None  # type: Optional[int]

    for ix, movement_saved in enumerate(movements_saved):
        movement_scraped = extract.by_index_or_none(movements_scraped, ix)

        if not movement_scraped:
            msg_pattern = ("{}: dates from {} to {}: BALANCE INTEGRITY ERROR:\n"
                           "CAN'T FIX movements automatically: "
                           "scraped less movements than already saved: "
                           "no movement_scraped with index {}.\n"
                           "Current account balance = {}\n"
                           "SAVED:\n{}\nSCRAPED:\n{}")
            logger.error(msg_pattern.format(
                account_scraped.FinancialEntityAccountId,
                date_from_str,
                date_to_str,
                ix,
                account_scraped.Balance,
                _format_list(movements_saved),
                _format_list(movements_scraped)
            ), is_send_email=False)

            logger.error(msg_pattern.format(
                account_scraped.FinancialEntityAccountId,
                date_from_str,
                date_to_str,
                ix,
                account_scraped.Balance,
                _as_html_table(movements_saved),
                _as_html_table(movements_scraped)
            ), is_print=False, is_sentry=False, is_html=True)

            return False, result_codes.ERR_BALANCE_FEW_MOVEMENTS

        if not is_equal_movements(movement_saved, movement_scraped):
            first_broken_mov_saved = movement_saved
            first_broken_mov_scraped = movement_scraped
            first_broken_ix = ix
            break

        last_correct_movement = movement_saved

    # Handle broken point
    if last_correct_movement is None:
        msg_pattern = ("{}: dates from {} to {}: BALANCE INTEGRITY ERROR:\n"
                       "CAN'T FIX movements automatically: "
                       "no matching movements to start fix from.\n"
                       "SAVED:\n{}\n"
                       "SCRAPED:\n{}")
        logger.error(msg_pattern.format(
            account_scraped.FinancialEntityAccountId,
            date_from_str,
            date_to_str,
            _format_list(movements_saved),
            _format_list(movements_scraped)
        ), is_send_email=False)

        logger.error(msg_pattern.format(
            account_scraped.FinancialEntityAccountId,
            date_from_str,
            date_to_str,
            _as_html_table(movements_saved),
            _as_html_table(movements_scraped)
        ), is_print=False, is_sentry=False, is_html=True)

        return False, result_codes.ERR_BALANCE_NO_PIVOT_MOVEMENT

    # delete all movements after last correct
    if project_settings.IS_UPDATE_DB:
        # The fixing action
        db_connector.delete_movements_after_id(fin_ent_account_id, last_correct_movement.Id)

    # send different notifications if fixed movements since the last scraped date or earlier
    assert first_broken_mov_saved is not None  # for linter
    if first_broken_mov_saved.OperationalDate == movements_saved[-1].OperationalDate:
        msg_title = "{}: dates from {} to {}: BALANCE INTEGRITY ERROR: FIXED automatically\n".format(
            fin_ent_account_id,
            date_from_str,
            date_to_str,
        )
    else:
        msg_title = (
            "{}: dates from {} to {}: BALANCE INTEGRITY ERROR: FIXED automatically "
            "(WAS BROKEN IN PREVIOUS DATES)\n".format(
                fin_ent_account_id,
                date_from_str,
                date_to_str,
            )
        )

    logger.warning(
        "{}"
        'BROKEN MOV_SAVED:\n{}\n'
        'BROKEN MOV_SCRAPED:\n{}\n'
        'BROKEN MOV INDEX IN THE LIST: {}\n'
        "SAVED:\n{}\n"
        "SCRAPED:\n{}".format(
            msg_title,
            first_broken_mov_saved,
            first_broken_mov_scraped,
            first_broken_ix,
            _format_list(movements_saved),
            _format_list(movements_scraped)
        )
    )

    return True, result_codes.SUCCESS
