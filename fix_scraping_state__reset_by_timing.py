import datetime
import logging
import os
import time

from custom_libs import state_reset
from custom_libs.db import queue_simple
from project import settings

__version__ = '3.0.1'

__changelog__ = """
3.0.1
upd log msgs
3.0.0
one action with try-finally to use with every-min-crontab-jobs
2.0.0
new project structure
"""

LOG_SUBDIR = 'scraping_state_observer'


def prepare_logging():
    logdir = os.path.abspath(os.path.join(
        settings.PROJECT_ROOT_PATH,
        'logs',
        LOG_SUBDIR))

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(
            logdir,
            'scraping_state_observer__{}.log'.format(
                datetime.datetime.utcnow().strftime(settings.LOG_FILENAME_DATETIME_FMT)
            )
        ),
        format='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == '__main__':
    try:
        prepare_logging()
        logging.info('== Reset by timing: START  ==')
        state_reset.reset_by_timing()
    finally:
        logging.info('Wait for queue')
        queue_simple.wait_finishing()
        # Mostly to allow sentry client send all pending msgs
        time.sleep(3)
        logging.info('== Reset by timing: DONE  ==')
