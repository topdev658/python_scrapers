"""This module fills InitialId for all movs"""

import datetime

from custom_libs.db.db_funcs import _execute_query as process_query
from custom_libs.db import queue_simple


def fill_initialid_for_all():
    q_upd = """
    MERGE INTO dbo._TesoraliaStatements Tgt
    USING (
        SELECT TOP 50000
            Id, InitialId
        FROM dbo._TesoraliaStatements
        WHERE
            InitialId IS NULL
    ) Src
    ON  Tgt.Id = Src.Id
    WHEN MATCHED THEN UPDATE SET Tgt.InitialId = Src.Id;"""
    q_sel = """SELECT COUNT(Id) FROM _TesoraliaStatements WHERE InitialId IS NULL"""
    need_to_upd = True
    i = 0
    while need_to_upd:
        res = process_query(q_upd)
        if not (i % 5):
            res_to_upd = process_query(q_sel)[0]
            to_upd = res_to_upd[0]['']
            print('To update initialId:', to_upd)
            if res_to_upd:
                need_to_upd = to_upd > 0
        i += 1

    print('All movements filled initialId: DONE')


if __name__ == '__main__':
    print('***** START *****')
    start = datetime.datetime.now()
    fill_initialid_for_all()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
    queue_simple.wait_finishing()
