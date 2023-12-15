"""This module finds KeyValue collision for movements to prepare DB
to use UNIQUE index (KeyValue, AccountId)
Launch it ONCE, fix and then add the index
"""

import datetime

from tqdm import tqdm

from custom_libs.db.db_funcs import _execute_query as process_query


def find_key_value_collisions():
    q_movs = """SELECT Id, AccountId, KeyValue FROM dbo._TesoraliaStatements"""
    movs_dicts = process_query(q_movs)

    movs_processed = {}
    for mov in tqdm(movs_dicts):
        key = "{}:{}".format(mov['AccountId'], mov['KeyValue'].strip())
        if key not in movs_processed.keys():
            movs_processed[key] = mov['Id']
        else:
            print('COLLISION: {}={} ({})'.format(movs_processed[key], mov['Id'], key))

    print('All movements: DONE')


if __name__ == '__main__':
    print('***** START *****')
    start = datetime.datetime.now()
    find_key_value_collisions()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
