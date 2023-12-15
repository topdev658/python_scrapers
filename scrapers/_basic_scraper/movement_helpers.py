import hashlib
import re
from typing import Callable, List, Set, Tuple, Optional

from custom_libs import date_funcs
from custom_libs import str_funcs
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (
    MOVEMENTS_ORDERING_TYPE_ASC, MovementParsed, MovementSaved, MovementScraped
)

__version__ = '1.9.0'

__changelog__ = """
1.9.0 2023.05.23
fill_originals_from_movements_saved: support Receipt and ReceiptChecksum fields
1.8.0
fill_originals_from_movements_saved: log args
_is_equal_to_keep_timestamp: match also on (OperationalDatePosition and fuzzy_matched descr)
1.7.1
fixed type hints
1.7.0
drop_movements_of_oldest_date
1.6.0
reorder_movements_for_dates
1.5.0
clean_description for checksums
1.4.0
fill_originals_from_movements_saved: support ExportTimeStamp field
1.3.0
is_desc_ordering_by_temp_balance
1.2.0
InitialId support
1.1.0
fill_timestamps_from_movements_saved
_is_equal_to_keep_timestamp
"""


def clean_description(descr: str) -> str:
    """Replaces new lines. Strips"""
    return descr.replace('\n', '  ').strip()


def _get_receipt_content(receipt_text: str) -> str:
    if not receipt_text:
        return ''
    # it remains generic, it only removes conflictive info from the receipt if it applies
    receipt_text = re.sub(r'\nREF. ORDENANTE:.*\n', '\n', receipt_text)
    receipt_text = re.sub(r'\nREF. BANCO EMISOR:.*\n', '\n', receipt_text)
    receipt_text = re.sub(r'\nEUR-\n', '|\n', receipt_text)  # todo check
    receipt_text = re.sub(r'\nBanco de Sabadell.*\n', '\n', receipt_text)

    return receipt_text.replace('\n', '|')


def _get_mov_reference(movement_scraped: MovementScraped,
                       ref_regexp: str) -> str:
    fields = (
        'StatementDescription',
        'StatementExtendedDescription',
        'StatementReceiptDescription',
    )

    mov_reference = ''
    res = re.match(r"(-?\d*)/(.*)/", ref_regexp)
    if res:
        ref_pos = int(res.group(1) or "0")
        ref_regexp_upd = "(?si){}".format(res.group(2))
        for f in fields:
            field_content = getattr(movement_scraped, f, '')
            if f == 'StatementReceiptDescription':
                field_content = _get_receipt_content(field_content)

            if field_content:
                mov_ref = re.findall(ref_regexp_upd, field_content)
                if mov_ref:
                    mov_reference = mov_ref[ref_pos]
                    break

    # handling grouping in multiple pattern regexps: get the first non empty result
    if isinstance(mov_reference, tuple):
        non_empties = list(filter(None, mov_reference))
        if non_empties:
            mov_reference = non_empties[0]

    mov_reference = mov_reference.upper().strip()
    return mov_reference


def get_movement_customer_references(movement_scraped: MovementScraped,
                                     ref1_regexp: str,
                                     ref2_regexp: str) -> Tuple[str, str]:
    mov_reference1 = _get_mov_reference(movement_scraped, ref1_regexp)
    mov_reference2 = re.sub(
        r'[-\s_]',
        '',
        _get_mov_reference(movement_scraped, ref2_regexp)
    )

    return mov_reference1, mov_reference2


def get_movement_fin_entity_references(
        movement_scraped: MovementScraped,
        extractor: str,
        parse_reference_from_receipt_func: Callable[[str], str]) -> Tuple[str, str]:
    if extractor == "Recibos Cobros Domiciliados":
        desc = re.findall('(?si)IMPAGADO RECIBOS DOMICIL. SEPA DEVOLUCION RECIBO|'
                          'REMESA DE RECIBOS|REMESA RECIBOS',
                          movement_scraped.StatementDescription)
        if not desc:
            return '', ''

        reference = parse_reference_from_receipt_func(
            movement_scraped.StatementReceiptDescription
        )
        return '', reference.upper()
    elif extractor == "Otros":
        return '', ''

    return '', ''


def get_details_from_extended_descr(description_extended: str,
                                    details_name: str) -> str:
    if not details_name:
        return ''
    for det in description_extended.split('||'):
        if details_name in det:
            return det.strip()
    return ''


def order_movements_asc(movements: list,
                        current_ordering: str) -> list:
    if current_ordering == MOVEMENTS_ORDERING_TYPE_ASC:
        return movements

    # Copy and reverse
    return movements[::-1]


def _get_hash(hashbase: str) -> str:
    return hashlib.sha256(hashbase.encode()).hexdigest().strip()


def get_spec_checksum_for_movement_saved(mov_saved: MovementSaved) -> str:
    hashbase = '{}{}{}{}{}'.format(
        mov_saved.OperationalDate,
        mov_saved.ValueDate,
        mov_saved.Amount,
        mov_saved.TempBalance,
        # back comp for movements saved with new lines in descr
        clean_description(mov_saved.StatementDescription)
    )

    checksum = _get_hash(hashbase)
    return checksum


def get_spec_checksums_uniq_for_movements_saved(movements_saved: List[MovementSaved]) -> Set[str]:
    """
    Returns set of special checksums for movements_saved.

    Important difference that these checksums will be calculated
    another way than KeyValue because will be used for movements_parsed
    before calculation of OperationalDatePosition.

    Second important point: if there are 2 movements which have
    the same checksums, then the checksum will be removed from the set,
    that means only checksums of explicitly unique movements by given arguments
    will be put into the set.
    """

    checksums = set()  # type: Set[str]
    # checksums of duplicated (or even more times repeated) movements
    checksums_dupl = set()  # type: Set[str]
    for mov in movements_saved:
        checksum = get_spec_checksum_for_movement_saved(mov)
        if checksum in checksums:
            checksums_dupl.add(checksum)
        checksums.add(checksum)
    checksums_uniq = checksums.difference(checksums_dupl)
    return checksums_uniq


def get_spec_checksum_for_movement_parsed(mov_parsed: MovementParsed) -> str:
    """IMPORTANT
    mov_parsed must have common fields:
    - operation_date
    - value_date
    - amount
    - temp_balance
    - description
    It's necessary to provide generic calculation.
    Otherwise, use custom implementation (but calculate it the same way)
    """
    hashbase = '{}{}{}{}{}'.format(
        date_funcs.convert_date_to_db_format(mov_parsed['operation_date']),
        date_funcs.convert_date_to_db_format(mov_parsed['value_date']),
        mov_parsed['amount'],
        mov_parsed['temp_balance'],
        clean_description(mov_parsed['description'])
    )
    checksum = _get_hash(hashbase)
    return checksum


def _is_equal_to_keep_timestamp(
        mov_scraped: MovementScraped,
        mov_saved: MovementSaved) -> bool:
    """Uses fuzzy_equal for StatementDescription"""
    descr_saved = mov_saved.StatementDescription.lower()
    descr_scraped = mov_scraped.StatementDescription.lower()
    is_equal = (
            mov_saved.OperationalDate == mov_scraped.OperationalDate
            and mov_saved.ValueDate == mov_scraped.ValueDate
            and mov_saved.Amount == mov_scraped.Amount
            and (
                    descr_saved == descr_scraped
                    or
                    (
                            mov_saved.OperationalDatePosition == mov_scraped.OperationalDatePosition
                            and str_funcs.fuzzy_matching(descr_saved, descr_scraped) >= 0.9
                    )
            )
    )
    return is_equal


def fill_originals_from_movements_saved(
        logger: ScrapeLogger,
        fin_ent_account_id: str,
        movements_scraped: List[MovementScraped],
        movements_saved: List[MovementSaved]) -> Tuple[List[MovementScraped],
                                                       List[MovementSaved]]:
    """Fills CreateTimeStamp for each of movements_scraped
    from movement_saved if 'equal enough' movement detected

    :returns (new movements_scraped with filled CreateTimeStamp,
              unmatched movements_saved)
    """
    movements_scraped_copy = movements_scraped.copy()
    movements_saved_copy = movements_saved.copy()
    for i, mov_scraped in enumerate(movements_scraped_copy):
        # No way for optimization by op_date_saved > op_date_scraped
        # because there are messed movs in fin entities
        for j, mov_saved in enumerate(movements_saved_copy):
            if _is_equal_to_keep_timestamp(mov_scraped, mov_saved):
                movements_scraped_copy[i] = mov_scraped._replace(
                    CreateTimeStamp=mov_saved.CreateTimeStamp,
                    InitialId=mov_saved.InitialId,
                    ExportTimeStamp=mov_saved.ExportTimeStamp,
                    Receipt=mov_saved.Receipt,
                    ReceiptChecksum=mov_saved.ReceiptChecksum
                )
                # Log when matched not equal movements
                if (mov_saved.OperationalDatePosition != mov_scraped.OperationalDatePosition
                        or mov_saved.StatementDescription != mov_scraped.StatementDescription):
                    logger.info('{}: FOUND SIMILAR mov saved {} @ {}/{} ({}) for scraped {} @ {}/{} ({})'.format(
                        fin_ent_account_id,
                        mov_saved.Amount,
                        mov_saved.OperationalDate,
                        mov_saved.OperationalDatePosition,
                        mov_saved.StatementDescription,
                        mov_scraped.Amount,
                        mov_scraped.OperationalDate,
                        mov_scraped.OperationalDatePosition,
                        mov_scraped.StatementDescription
                    ))
                # Avoid double matching, no mutations (tested)
                movements_saved_copy.pop(j)
                break
        else:
            if movements_saved_copy:
                logger.info('{}: NO MATCHED MOVEMENT: {}'.format(
                    fin_ent_account_id,
                    mov_scraped
                ))
                ...
    return movements_scraped_copy, movements_saved_copy


def is_desc_ordering_by_temp_balance(movs_parsed: List[MovementParsed]) -> Optional[bool]:
    """Allows to detect ordering of today and future movements
    (it may be different to prev days)
    :returns is_desc_optional

    >>> mm_asc = [{'temp_balance': 2.0, 'amount': -1.0},\
        {'temp_balance': 3.0, 'amount': 1.0}, \
        {'temp_balance': 4.0, 'amount': 1.0}]
    >>> is_desc_ordering_by_temp_balance(mm_asc)
    False

    >>> mm_desc = [{'temp_balance': 3.0, 'amount': 1.0},\
        {'temp_balance': 2.0, 'amount': -2.0},\
        {'temp_balance': 4.0, 'amount': 1.0}]
    >>> is_desc_ordering_by_temp_balance(mm_desc)
    True
    """
    mov_prev = None
    for mov in movs_parsed:
        is_asc = False
        is_desc = False

        if mov['temp_balance'] is None:
            continue
        if mov_prev is None:
            mov_prev = mov
            continue

        # Desc
        if round(mov_prev['temp_balance'], 2) == round(mov['temp_balance'] + mov_prev['amount'], 2):
            is_desc = True
        # Asc
        if round(mov['temp_balance'], 2) == round(mov_prev['temp_balance'] + mov['amount'], 2):
            is_asc = True

        if not (is_asc or is_desc):
            return None  # Can't detect

        if is_desc and is_asc:  # Unclear situation, repeat an attempt
            mov_prev = mov
            continue
        else:
            return is_desc  # OK. Detected

    return None  # Can't detect


def reorder_movements_for_dates(
        movements_parsed: List[MovementParsed],
        reorder_for_dates: List[str]) -> List[MovementParsed]:
    """
    :param movements_parsed: initial list of movements_parsed
    :param reorder_for_dates: dates in format how it saved for the specific
    :return: movements reordered

    >>> movs_parsed = [\
        {'operation_date': '01/02/2020', 'amount': 1.0},\
        {'operation_date': '02/02/2020', 'amount': 10.0},\
        {'operation_date': '02/02/2020', 'amount': 1.0},\
        {'operation_date': '03/02/2020', 'amount': 1.0},\
        {'operation_date': '03/02/2020', 'amount': 2.0},\
        {'operation_date': '04/02/2020', 'amount': 10.0},\
        {'operation_date': '04/02/2020', 'amount': 1.0},\
    ]
    >>> movs_reordered = reorder_movements_for_dates(movs_parsed, ['02/02/2020', '04/02/2020'])
    >>> expect = [\
        {'operation_date': '01/02/2020', 'amount': 1.0},\
        {'operation_date': '02/02/2020', 'amount': 1.0},\
        {'operation_date': '02/02/2020', 'amount': 10.0},\
        {'operation_date': '03/02/2020', 'amount': 1.0},\
        {'operation_date': '03/02/2020', 'amount': 2.0},\
        {'operation_date': '04/02/2020', 'amount': 1.0},\
        {'operation_date': '04/02/2020', 'amount': 10.0},\
    ]
    >>> movs_reordered == expect
    True
    """

    def process_movs_by_date():
        """Closure, no need to accept args - captures existing vars
        Reorders movs_by_date if it's needed and adds to movements_parsed_reordered
        """
        if prev_mov_date in reorder_for_dates:
            movs_by_date.reverse()
        movements_parsed_reordered.extend(movs_by_date)

    movements_parsed_reordered = []  # type: List[MovementParsed]
    prev_mov_date = ''
    movs_by_date = []  # type: List[MovementParsed]
    for mov in movements_parsed:
        mov_date = mov['operation_date']
        if mov_date != prev_mov_date:
            # New date? -> Save movs of prev date
            process_movs_by_date()
            movs_by_date = []
        movs_by_date.append(mov)
        prev_mov_date = mov_date
    # After last mov need to process movs_by_date again
    process_movs_by_date()

    return movements_parsed_reordered


def drop_movements_of_oldest_date(
        movements_scraped_asc: List[MovementScraped]) -> Tuple[List[MovementScraped], Optional[str]]:
    """:return (movements_scraped_wo_old_date, dropped_date)"""
    if not movements_scraped_asc:
        return [], None
    mov_oldest_date_str = movements_scraped_asc[0].OperationalDate
    movements_scraped_wo_old_date = [
        m for m in movements_scraped_asc if m.OperationalDate != mov_oldest_date_str
    ]
    return movements_scraped_wo_old_date, mov_oldest_date_str
