from datetime import datetime, date
from typing import List, Tuple, Optional

import xlrd
from xlrd.biffh import XLRDError

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import POSCollection, POSMovement

__version__ = '1.1.0'
__changelog__ = """
1.1.0
_parse_commission
get_pos_collections: calc commission_amount using commission_percent, commission_fixed
"""


def validate_excel(resp_excel: bytes) -> bool:
    try:
        _book = xlrd.open_workbook(file_contents=resp_excel)
        return True
    # Not an excel
    except XLRDError as _e:
        return False


def _validate_collection(collection: POSCollection) -> bool:
    ok = (
            collection.validate_number_of_movs()
            and collection.validate_mov_collection_ids()
    )
    return ok


def _parse_commission(val_str: str) -> Tuple[float, float]:
    """
    >>> _parse_commission('-1,80% -  0,39&euro;')
    (1.8, 0.39)
    >>> _parse_commission('-1,80% -  0,39€')
    (1.8, 0.39)
    >>> _parse_commission('0,03%')
    (0.03, 0.0)
    >>> _parse_commission('')
    (0.0, 0.0)
    >>> _parse_commission('-0,07&euro;')
    (0.0, 0.07)

    # extra spaces
    >>> _parse_commission('  -1,80%  -    0,39&euro; ')
    (1.8, 0.39)
    >>> _parse_commission('  0,03%  ')
    (0.03, 0.0)
    >>> _parse_commission('  ')
    (0.0, 0.0)

    :return (commission_percent, commission_amount)
    """
    val_str = val_str.strip()
    if '%' in val_str:
        split = val_str.split('%')
    else:
        # no percent (see test cases)
        split = ['0', val_str]
    percent = abs(round(convert.to_float(split[0]) if '%' in val_str else 0.0, 2))
    amount = abs(round(convert.to_float(split[1]) if len(split) == 2 and split[1] else 0.0, 2))
    return percent, amount


def get_pos_collections(resp_excel: bytes, trade_point_id: int, logger: ScrapeLogger) -> List[POSCollection]:
    collections = []  # type: List[POSCollection]
    book = xlrd.open_workbook(file_contents=resp_excel)
    sheet = book.sheet_by_index(0)

    collection = None  # type: Optional[POSCollection]
    oper_date = None  # type: Optional[date]
    # see dev_tpv/33743493_20210905_143023.xls
    for row_ix in range(4, sheet.nrows):
        cells = sheet.row_values(row_ix)
        cell0 = cells[0]
        if cell0 == 'Fecha':
            # Validate and add prev collection to list of collections
            if collection is not None:
                if not _validate_collection(collection):
                    # already reported
                    continue

                collection.build()
                if collection.ref in [c.ref for c in collections]:
                    logger.warning('trade point {}: collection {}: duplicated collection detected. Skip'.format(
                        trade_point_id,
                        collection.ref
                    ))
                    continue

                collections.append(collection)

            # Create new collection, then will mutate (after all related movements)
            collection = POSCollection(trade_point_id=trade_point_id, logger=logger)
            continue

        # For mypy due to Optional
        assert collection is not None

        # COLLECTION DATA
        # Nº operaciones 13
        # Total importe 2.715,00 EUR
        # Comis. 8,15 EUR
        # Líquido 2.706,85 EUR
        if 'Nº operaciones' in cell0:
            # to check that declared equal to actual
            collection.declared_number_of_movs = int(extract.re_last_or_blank(r'\d+', cell0))
            continue
        if 'Líquido' in cell0:
            collection.amount = round(convert.to_float(cell0), 2)
            continue
        if 'Total importe' in cell0:
            collection.base = round(convert.to_float(cell0), 2)
            continue
        if 'Comis' in cell0:
            collection.commission = round(convert.to_float(cell0), 2)
            continue

        # Blank etc.
        if len(cells) != 9 or not cells[0]:
            continue

        # MOV
        # 0 Fecha           28/06/2021
        # 1 Hora            20:18
        # 2 Nº de tarjeta   5163________1808
        # 3 Importe         1.000,00
        # 4 Comisión.Dto    -0,30%
        # 5 Descripción     VENTA
        # 6 Nº operación    0000001
        # 7 Nº remesa       6031381816 -- collection_ref
        # 8 Divisa original EUR
        mov_date = datetime.strptime(cells[0], '%d/%m/%Y').date()
        mov_time_str = cells[1]
        card_number = cells[2]
        amount = convert.to_float(cells[3])

        # Automatically converts '&euro;' to '€'
        commission_str = extract.re_first_or_blank('.*', cells[4].strip())
        commission_percent, commission_fixed = _parse_commission(commission_str)
        # 0.01 means 'percent'
        commission_amount = round(commission_percent * 0.01 * amount + commission_fixed, 2)

        descr = cells[5]
        date_position = int(cells[6])
        collection_ref = cells[7]
        currency = cells[8]
        mov = POSMovement(
            date=mov_date,
            time=mov_time_str,
            card_number=card_number,
            amount=amount,
            commission_percent=commission_str,  # it is not only percent, but percent and fixed amount
            commission_amount=commission_amount,  # calculated abs value of commission
            descr=descr,
            date_position=date_position,
            collection_ref=collection_ref,
            currency=currency
        )
        assert collection is not None  # for mypy
        collection.add_movement(mov)

    # Last collection
    if collection is not None:
        # Validate and add the last collection
        if _validate_collection(collection):
            collection.build()
            collections.append(collection)

    return collections
