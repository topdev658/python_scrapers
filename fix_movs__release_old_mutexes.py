"""Releases hanging 'movement insert mutexes'
(may occur due to manual scraping interruption)
To change default args, use:
 $ MUTEX_OFFSET='00:10:00' python3 fix_movs__release_old_mutexes.py
"""
import os

from custom_libs.db.db_funcs import process_query
from custom_libs.db import queue_simple

MUTEX_OFFSET = os.getenv('MUTEX_OFFSET', '01:00:00')


def process():
    q = """
    UPDATE _TesoraliaAccounts
    SET MovementsInsertMutex=NULL,
        MutexLockedTimeStamp=NULL
    WHERE MutexLockedTimeStamp < (getutcdate() - '{}');
    """.format(MUTEX_OFFSET)

    process_query(q)


if __name__ == '__main__':
    print('*** START with MUTEX_OFFSET={} ***'.format(MUTEX_OFFSET))
    try:
        process()
    finally:
        queue_simple.wait_finishing()
        print('*** DONE ***')
