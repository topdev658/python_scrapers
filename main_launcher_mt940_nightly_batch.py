"""
DB-based access selection for nightly MT940 processing.
Like shell script to emulate manual -a arg
for main_launcher_mt940.py
"""

import subprocess
import uuid
from typing import List

from custom_libs.db import db_funcs
from custom_libs.db import queue_simple
from custom_libs.db.db_logger import DBLogger
from custom_libs.log import log
from project import settings as project_settings

__version__ = '1.0.0'
__changelog__ = """
1.0.0
get_user_ids_to_process, get_access_ids_to_process from db
0.2.0
upd hardcoded accesses 
0.1.0
hardcoded accesses
"""


def get_user_ids_to_process() -> List[int]:
    user_ids = db_funcs.UserFuncs.get_all_user_ids_for_mt940()
    return user_ids


def get_access_ids_to_process(user_id: int) -> List[int]:
    # access_ids = [32603, 33108]
    access_ids = db_funcs.FinEntFuncs.get_fin_ent_access_ids_to_scrape_for_mt940(user_id)
    return access_ids


def main():
    launcher_id = str(uuid.uuid4())
    db_logger = DBLogger(
        logger_name=project_settings.DB_LOGGER_NAME_MT940,
        launcher_id=launcher_id,
    )
    db_logger.accesos_log_info(
        message='MT940 Orchestration Initiated',
        status='STARTED'
    )
    log_prefix = 'main_launcher_mt940_nightly_batch'
    try:
        user_ids = get_user_ids_to_process()
        log('{}: got {} users to process'.format(log_prefix, len(user_ids)))
        for user_id in user_ids:
            access_ids = get_access_ids_to_process(user_id)
            log('{}: user {}: got {} accesses to process'.format(log_prefix, user_id, len(access_ids)))
            for access_id in access_ids:
                log('{}: process -l {} -a {}'.format(
                    log_prefix,
                    launcher_id,
                    access_id,
                ))
                # Synced call, the output will be logged at script level
                subprocess.run(
                    "python3 main_launcher_mt940.py -a {} -l {}".format(access_id, launcher_id),
                    shell=True
                )
    finally:
        db_logger.accesos_log_info(
            message='MT940 Orchestration Completed',
            status='COMPLETED'
        )
        log('==== {}: queue.wait_finishing and close db connection ===='.format(log_prefix))
        queue_simple.wait_finishing()


if __name__ == '__main__':
    main()
