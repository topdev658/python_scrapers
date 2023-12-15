"""This module fills KeyValue for movements where KeyValue is Null
Launch it ONCE to affect old movements only to start use KayValue to compare movements
2018-07-29: there are 40K+ movs where KeyValue is null of total 800K movs

CHANGELOG:
2019-10-05: FIXED calc_kv (hashbase args)
"""

import datetime
import hashlib

from custom_libs import date_funcs
from custom_libs.db import db_connector_for_scraper
from custom_libs.db import queue_simple
from custom_libs.db.db_funcs import _execute_query as process_query

db_connector = db_connector_for_scraper.DBConnector('', '')  # for mov_saved


def calc_kv(mov_dict):
    # use approach as in main
    # from schema
    #   Id                      bigint identity,
    #   OperationalDate         datetime,
    #   ValueDate               datetime,
    #   StatementDescription    varchar(max),
    #   Amount                  decimal(38, 20),
    #   TempBalance             decimal(38, 20),
    #   AccountId               bigint,
    #   CreateTimeStamp         datetime,
    #   OperationalDatePosition int,
    #   KeyValue                char(256),
    #   ExportTimeStamp         datetime
    try:
        assert int(mov_dict['OperationalDatePosition']) > 0
    except Exception as exc:
        print(exc)
        return 0, True

    mov_saved = db_connector._mov_saved_by_dt_format(mov_dict, date_funcs.convert_dt_to_scraper_date_type3)

    hashbase = '{}{}{}{}{}'.format(
        mov_saved.OperationalDate,
        mov_saved.ValueDate,
        round(mov_saved.Amount, 2),
        round(mov_saved.TempBalance, 2),
        mov_saved.OperationalDatePosition
    )

    key_value = hashlib.sha256(hashbase.encode()).hexdigest().strip()
    print(key_value)
    return key_value, None


def process_mov(mov_dict):
    key_value, err = calc_kv(mov_dict)
    if err:
        return

    mov_id = mov_dict['Id']
    q_mov_data_to_update = """
    UPDATE dbo._TesoraliaStatements
    SET
      KeyValue = '{}'
    WHERE Id = {};
    """.format(key_value, mov_id)

    try:
        process_query(q_mov_data_to_update)
    except Exception as exc:
        print(exc)


def fill_key_value_for_all():
    q_movs_wo_keyvalue = """SELECT * FROM dbo._TesoraliaStatements WHERE KeyValue IS NULL;"""
    movs_dicts = process_query(q_movs_wo_keyvalue)
    for mov in movs_dicts[0]:
        print(mov['Id'])
        process_mov(mov)

    print('All movements: DONE')


if __name__ == '__main__':
    print('***** START *****')
    start = datetime.datetime.now()
    fill_key_value_for_all()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
    queue_simple.wait_finishing()
