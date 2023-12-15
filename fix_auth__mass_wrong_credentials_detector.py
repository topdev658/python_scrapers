"""
Detects suspicious cases and reports
when there are many 'wrong credentials' detections
in a short time period
"""

import argparse
import datetime
import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from custom_libs.db import queue_simple
from custom_libs.db.db_funcs import process_query
from custom_libs.scrape_logger import ScrapeLogger
from project import fin_entities_ids
from project import settings

__version__ = '1.0.1'

__changelog__ = """
1.0.1
msg updated
"""

LOG_SUBDIR = 'fixers'
DEFAULT_OFFSET_HRS = 6
DEFAULT_THRESHOLD_PER_FIN_ENTITY = 3


def get_recent_wrong_credentials(offset_hours: int) -> Dict[int, List[dict]]:
    q = """
    -- get_recent_wrong_credentials
    SELECT
       FA.LiferayId accesosClienteId,
       FA.LastResponseTesoraliaDescription,
       FA.LastScrapingFinishedTimeStamp,
       AC.accesoClienteEntidadId FinancialEntityId
    FROM _TesoraliaCustomerFinancialEntityAccess FA
    INNER JOIN accesos_AccClientes AC on AC.accesosClienteId = FA.LiferayId
    WHERE FA.LastResponseTesoraliaDescription = 'ERR_WRONG_CREDENTIALS' AND
          FA.LastScrapingFinishedTimeStamp >= dateadd(hour, -{}, getutcdate())
    ORDER BY FA.LastScrapingFinishedTimeStamp DESC;
    """.format(offset_hours)
    results = process_query(q)
    errs_by_fin_entity = defaultdict(list)  # type: Dict[int, List[dict]]
    for result in results:
        errs_by_fin_entity[result['FinancialEntityId']].append(result)
    return errs_by_fin_entity


def check_and_report(logger: ScrapeLogger, offset: int, threshold: int, errs_by_fin_entity: Dict[int, List[dict]]):
    for fin_ent_id, err_details in errs_by_fin_entity.items():
        if len(err_details) >= threshold:
            fin_ent_name = fin_entities_ids.get_fin_entity_name_by_id(fin_ent_id)
            logger.error(
                "{}: TOO MANY ({}) 'wrong credentials' detected during the last {} hours: {}. "
                "Pls, check the website manually and restore the accesses if need. "
                "Probably, {} is NOT AVAILABLE.".format(
                    fin_ent_name,
                    len(err_details),
                    offset,
                    [e['accesosClienteId'] for e in err_details],
                    fin_ent_name
                ))


def parse_cmdline_args() -> Tuple[int, int]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--offset',
        '-o',
        help="Offset (hrs) to detect mass 'wrong credentials'",
        type=int,
        default=DEFAULT_OFFSET_HRS
    )

    parser.add_argument(
        '--threshold',
        '-t',
        help="Maximum allowed 'wrong credentials' per fin entity between [now-offset, now]",
        type=int,
        default=DEFAULT_THRESHOLD_PER_FIN_ENTITY
    )

    args = parser.parse_args()
    return args.offset, args.threshold


def prepare_logging():
    logdir = os.path.abspath(
        os.path.join(
            settings.PROJECT_ROOT_PATH,
            'logs',
            LOG_SUBDIR
        )
    )

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(
            logdir,
            'mass_wrong_cred_detector__{}.log'.format(
                datetime.datetime.utcnow().strftime(settings.LOG_FILENAME_DATETIME_FMT)
            )
        ),
        format='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == '__main__':
    try:
        prepare_logging()
        offset, threshold = parse_cmdline_args()
        logger = ScrapeLogger('MassWrongCredentialsDetector', 'all', 'all')
        recent_errs = get_recent_wrong_credentials(offset)
        check_and_report(logger, offset, threshold, recent_errs)
    finally:
        queue_simple.wait_finishing()
        time.sleep(3)
