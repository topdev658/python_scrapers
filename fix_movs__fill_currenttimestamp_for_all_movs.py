"""This module fills CurrentCreateTimeStamp for all movs
where CreateTimeStamp is not null"""

import datetime

from custom_libs.db.db_funcs import _execute_query as process_query


def fill_initialid_for_all():
    q_upd = """
    MERGE INTO dbo._TesoraliaStatements Tgt
    USING (
        SELECT TOP 50000
            Id, CreateTimeStamp
        FROM dbo._TesoraliaStatements
        WHERE
            CurrentCreateTimeStamp IS NULL 
            and CreateTimeStamp is NOT NULL
    ) Src
    ON  Tgt.Id = Src.Id
    WHEN MATCHED THEN UPDATE SET Tgt.CurrentCreateTimeStamp = Src.CreateTimeStamp;"""
    q_sel = """SELECT COUNT(Id) FROM _TesoraliaStatements WHERE CurrentCreateTimeStamp IS NULL 
               and CreateTimeStamp is NOT NULL"""
    need_to_upd = True
    i = 0
    while need_to_upd:
        print(i)
        res = process_query(q_upd)
        if not (i % 5):
            res_to_upd = process_query(q_sel)
            to_upd = res_to_upd[0]['']
            print('to update:', to_upd)
            if res_to_upd:
                need_to_upd = to_upd > 0
        i += 1

    print('All movements: DONE')


if __name__ == '__main__':
    print('***** START *****')
    start = datetime.datetime.now()
    fill_initialid_for_all()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
