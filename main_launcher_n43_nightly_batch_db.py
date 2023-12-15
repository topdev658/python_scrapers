"""
DB-based access selection for nightly N43 processing.
Like shell script to emulate manual -a arg
for main_launcher_n43.py
"""

import subprocess
import uuid
from datetime import datetime
from typing import List, Optional

from custom_libs import date_funcs
from custom_libs.db import db_funcs
from custom_libs.db import queue_simple
from custom_libs.db.db_logger import DBLogger
from custom_libs.log import log
from project import settings as project_settings
from project.custom_types import DBCustomerForN43, DBFinancialEntityAccessForN43

__version__ = '5.0.0'
__changelog__ = """
5.0.0 2023.11.08
Fixed n43 logs for nightly. Added -n argument to indicate all n43 accesses.
4.0.0
feed all accesses at once to scrape concurrently
3.0.0
skip already scraped accesses basing on LastSuccessDownload 
2.0.0
DBLogger
launcher_id
1.0.1
fixed access arg
upd log msgs
1.0.0
init
"""


def get_users_to_process() -> List[DBCustomerForN43]:
    users = db_funcs.UserFuncs.get_all_users_for_n43()
    return users


def get_accesses_to_process(user: DBCustomerForN43) -> List[DBFinancialEntityAccessForN43]:
    accesses = db_funcs.FinEntFuncs.get_fin_ent_accesses_to_scrape_for_n43(user.Id)
    return accesses


def main():
    launcher_id = str(uuid.uuid4())
    db_logger = DBLogger(
        logger_name=project_settings.DB_LOGGER_NAME_N43,
        launcher_id=launcher_id,
    )
    db_logger.accesos_log_info(
        message='N43 Orchestration Initiated',
        status='STARTED'
    )
    log_prefix = 'main_launcher_n43_nightly_batch'
    today = date_funcs.today()
    try:
        access_ids = []  # type: List[int]
        users = get_users_to_process()
        log('{}: got {} users to process'.format(log_prefix, len(users)))
        for user in users:
            user_access_ids = []  # type: List[int]
            accesses = get_accesses_to_process(user)
            log('{}: {}: got {} accesses to process'.format(log_prefix, user, len(accesses)))
            for access in accesses:
                access_id = access.Id
                last_successful_dt = access.LastSuccessDownload  # type: Optional[datetime]
                if last_successful_dt and last_successful_dt >= today:
                    log("{}: -a {}: already successfully downloaded N43 docs earlier today. Skip".format(
                        log_prefix,
                        access_id
                    ))
                    continue
                user_access_ids.append(access_id)

            if user_access_ids:
                log('{}: will process -l {} -u {} -a {} -n'.format(
                    log_prefix,
                    launcher_id,
                    user.Id,
                    ','.join([str(a) for a in user_access_ids]),
                ))
                access_ids.extend(user_access_ids)

        if access_ids:
            # Synced call, the output will be logged at script level
            subprocess.run(
                "python3 main_launcher_n43.py -l {} -a {} -n".format(
                    launcher_id,
                    ','.join([str(a) for a in access_ids]),
                ),
                shell=True
            )
    finally:
        db_logger.accesos_log_info(
            message='N43 Orchestration Completed',
            status='COMPLETED'
        )
        log('==== main_launcher_n43_nightly_batch: queue.wait_finishing and close db connection ====')
        queue_simple.wait_finishing()


if __name__ == '__main__':
    main()
