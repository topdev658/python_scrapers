"""This module recalculates and updates KeyValue for a specific movement"""

import hashlib
import sys
import traceback
from typing import Tuple

from custom_libs import date_funcs
from custom_libs.db import db_connector_for_scraper
from custom_libs.db import queue_simple
from custom_libs.db.db_funcs import _execute_query as process_query

db_connector = db_connector_for_scraper.DBConnector('', '')  # for mov_saved


def calc_kv(mov_dict: dict) -> str:
    assert mov_dict['OperationalDatePosition'] > 0

    mov_saved = db_connector._mov_saved_by_dt_format(
        mov_dict,
        date_funcs.convert_dt_to_scraper_date_type3
    )

    hashbase = '{}{}{}{}{}'.format(
        mov_saved.OperationalDate,
        mov_saved.ValueDate,
        round(mov_saved.Amount, 2),
        round(mov_saved.TempBalance, 2),
        mov_saved.OperationalDatePosition
    )
    print('hashbase={}'.format(hashbase))
    key_value = hashlib.sha256(hashbase.encode()).hexdigest().strip()
    print('kv={}'.format(key_value))
    assert key_value != ''
    return key_value


def process_mov(mov_dict) -> bool:
    key_value = calc_kv(mov_dict)

    q_mov_data_to_update = """
    UPDATE dbo._TesoraliaStatements
    SET
      KeyValue = '{}'
    WHERE Id = {};
    """.format(key_value, mov_dict['Id'])

    process_query(q_mov_data_to_update)
    return True


def get_mov(mov_id: int) -> dict:
    q_movs_wo_keyvalue = """SELECT * FROM dbo._TesoraliaStatements WHERE Id={};""".format(
        mov_id
    )
    movs_dicts, _err_msg = process_query(q_movs_wo_keyvalue)
    assert len(movs_dicts) == 1
    return movs_dicts[0]


def main(mov_id: int):
    mov = get_mov(mov_id)
    assert mov['Id'] == mov_id
    process_mov(mov)


if __name__ == '__main__':
    try:
        args = sys.argv
        if len(args) < 2:
            print('Specify movement ID: python movements_fixer__upd_keyvalue.py 12345')
            sys.exit(1)

        mov_id_arg = int(sys.argv[1])

        print('***** START *****')
        main(mov_id_arg)
        print('**** DONE *****')

    except Exception as exc:
        traceback.print_exc()
        sys.exit(1)
    finally:
        queue_simple.wait_finishing()
