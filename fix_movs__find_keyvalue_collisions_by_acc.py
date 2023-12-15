"""This module finds KeyValue collision for AccountId"""

import datetime
import sys
from tqdm import tqdm

from custom_libs.db.db_funcs import _execute_query as process_query


def find_key_value_collisions(db_account_id: int):
    q_movs = """SELECT Id, AccountId, KeyValue FROM dbo._TesoraliaStatements
                WHERE AccountId={}""".format(db_account_id)
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
    db_account_id = int(sys.argv[1])
    print("Find collisions for account_id={}".format(db_account_id))
    find_key_value_collisions(db_account_id)
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
