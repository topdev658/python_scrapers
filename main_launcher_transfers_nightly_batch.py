"""
DB-based access selection for nightly processing for transfers.
Like shell script to emulate manual -a arg
for main_launcher_transfers.py
"""

import subprocess
from typing import List

from custom_libs.db import db_funcs
from custom_libs.db import queue_simple
from custom_libs.log import log

__version__ = '1.0.1'
__changelog__ = """
1.0.1
fmt
1.0.0
init
"""


def get_accesses_to_process() -> List[int]:
    access_ids = db_funcs.FinEntFuncs.get_all_fin_ent_accesses_to_scrape_for_transfers()
    return access_ids


def main():
    log_prefix = 'main_launcher_transfers_nightly_batch'
    try:
        access_ids = get_accesses_to_process()
        log('{}: got {} accesses to process'.format(log_prefix, len(access_ids)))
        for access_id in access_ids:
            log('{}: process -a {}'.format(
                log_prefix,
                access_id
            ))
            # Synced call, the output will be logged at script level
            # TODO use python call
            subprocess.run("python3 main_launcher_transfers.py -a {}".format(access_id), shell=True)
    finally:
        log('==== {}: queue.wait_finishing and close db connection ===='.format(log_prefix))
        queue_simple.wait_finishing()


if __name__ == '__main__':
    main()
