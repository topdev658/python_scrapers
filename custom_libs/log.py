"""
Use logging.basicConfig from caller
"""

import logging
import os
import datetime
from typing import Optional

from raven import Client

from project import settings

__version__ = '2.3.0'

__changelog__ = """
2.3.0
added prepare_fixer_logging:
2.2.0
log_err default is_sentry=True
2.1.0
log_err default is_sentry=False
2.0.0
Senrty integration
"""

sentry_client = Client(settings.SENTRY_API_TOKEN)


def log(text, is_sentry=False):
    print(text)
    logging.info(text)
    if is_sentry:
        sentry_client.captureMessage(text, level='info')


def log_err(text, is_sentry=True):
    print(text)
    logging.error(text)
    if is_sentry:
        sentry_client.captureMessage(text)


def prepare_fixer_logging(fixer_name: str, log_sug_dir: Optional[str] = ''):
    logdir = os.path.abspath(os.path.join(
        settings.PROJECT_ROOT_PATH,
        'logs',
        log_sug_dir))

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(
            logdir,
            '{}__{}.log'.format(
                fixer_name,
                datetime.datetime.utcnow().strftime(settings.LOG_FILENAME_DATETIME_FMT)
            )
        ),
        format='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
