import datetime
import json
import logging
import os
import re
import subprocess
import traceback
from typing import Tuple

from bottle import request, run, get, post, HTTPResponse

from custom_libs.db import db_funcs
from custom_libs.log import log, log_err
from project import settings

__version__ = '6.5.0'

__changelog__ = """
6.5.0
'process/' now accepts 'access' POST param
6.4.0
get_user__call_from_web_service
log_err
6.3.0
unlimited stack
get_user_wo_queue
6.2.1
-X faulthandler
6.2.0
get ok method
6.1.0
131072 = 128K
6.0.0
new project structure
5.2.0
stack size up to 65536
5.1.0
ulimit -s 24576 in MAIN_LAUNCHER_CMD_STR (3x to default stack to avoid segfault error)
5.0.0
remove unused index route
4.0.2
log results of subprocess calls 
4.0.1
removed commented code
4.0.0
init logging here
3.0.0
celery disabled due to critical bug related to subprocess calls in the scrapers
OS-level external main_launcher call to avoid celery bugs and to allow hot code replacement
2.5.0
use IS_API_SERVER_PRODUCTON_MODE
2.4.0
8080 port
2.3.0
with 5/30 rule
2.2.0
msg: Pass specific uid for the processing
2.1.0
msg: Start new scraping for uid
2.0.0
clean params uid (digits only) and from (date format) to avoid xss and unexpected errors
checkups before start scraping
check customer_id:
  is existing user
  is scraping already in progress
check date_from:
  is correct date format
1.0.1
log POST params
"""

VALID_TOKEN = 'super-secret-token'
MAIN_LAUNCHER_CMD_STR = 'ulimit -s unlimited && python3 -X faulthandler main_launcher.py'


def check(user, passw) -> bool:
    return user == 'raul' and passw == 'kUtfs7634'


def is_valid_token(token: str) -> bool:
    return token == VALID_TOKEN


def clean_only_digits(uid: str) -> str:
    return re.sub('[^0-9]', '', uid)


def clean_date_from(date_from: str) -> Tuple[str, bool]:
    date_from_cleaned = re.sub('[^0-9/]', '', date_from)

    if date_from:
        is_correct_date_format = bool(re.findall(r'\d{2}/\d{2}/\d{4}', date_from_cleaned))
    else:
        is_correct_date_format = True  # always True if date_from is not passed

    return date_from_cleaned, is_correct_date_format


def build_cmd(customer_id: str, access_id: str, date_from: str) -> str:
    cmd = MAIN_LAUNCHER_CMD_STR + ' -u {}'.format(customer_id)

    if access_id:
        cmd += ' -a {}'.format(access_id)

    if date_from:
        cmd += ' -f {}'.format(date_from)
    return cmd


@get('/ok')
@get('/ok/')
def ok():
    return {'status': 200}


@post('/process/')
@post('/process')
def process():
    """
    # Accepts POST params:
    # 'token' str (validation token)
    # 'from' str (from date)
    # 'uid' [int] (user/customer id)
    # 'access' [int] (access id)
    #
    # scrapingServerResponse  - http response result
    # JSON data format:
    #  {
    #       'data' : type: List or Dict,     // any valuable data
    #       'status':  type: boolean        // call target is reached or not
    #       'meta': {
    #                'code': type: int,      // soft code, usually similar to http code
    #                'system_msg': string  // some system message in human readable format
    #               }
    #   }
    """
    try:

        ip = request.headers.environ.get('REMOTE_ADDR', request.headers.environ.get('HTTP_X_FORWARDED_FOR'))

        date_from = request.POST.get('from', '')  # date fmt dd/mm/yyyy or blank (None?)
        customer_id_raw = request.POST.get('uid', '')
        token = request.POST.get('token', '')
        access_id_raw = request.POST.get('access', '')

        if not is_valid_token(token):
            log('{} - POST /process  401: {}'.format(ip, request.POST.dict))
            return HTTPResponse(
                headers={'Content-Type': 'application/json'},
                status=401,
                body=json.dumps({
                    'data': {},
                    'status': False,
                    'meta': {
                        'code': 401,
                        'system_msg': 'Permission denied'
                    }
                })
            )

        if not customer_id_raw:
            log('{} - POST /process  501: {}'.format(ip, request.POST.dict))
            return HTTPResponse(
                headers={'Content-Type': 'application/json'},
                status=501,
                body=json.dumps({
                    'data': {},
                    'status': False,
                    'meta': {
                        'code': 501,
                        'system_msg': "Pass specific uid for the processing"
                    }
                })
            )

        customer_id_cleaned = clean_only_digits(customer_id_raw)
        access_id_cleaned = clean_only_digits(access_id_raw)
        # use get_user_from_web_service to avoid db errors
        db_customer_or_none = db_funcs.UserFuncs.get_user__call_from_web_service(customer_id_cleaned)
        log(db_customer_or_none)

        if not db_customer_or_none:
            log('{} - POST /process  501: post_params {} :customer {} NOT FOUND'.format(
                ip, request.POST.dict, customer_id_cleaned, date_from
            ))

            return HTTPResponse(
                headers={'Content-Type': 'application/json'},
                status=501,
                body=json.dumps({
                    'data': {},
                    'status': False,
                    'meta': {
                        'code': 501,
                        'system_msg': "The customer with uid {} was not found".format(customer_id_cleaned)
                    }
                })
            )

        if db_customer_or_none.ScrapingInProgress:
            log('{} - POST /process  200: post_params {} :customer {}: '
                'scraping already in progress. will not start new scraping'.format(
                ip, request.POST.dict, customer_id_cleaned, date_from
            ))

            return {
                'data': {},
                'status': False,  # note status=False
                'meta': {
                    'code': 200,
                    'system_msg': 'The scraping for uid {} already is in progress. '
                                  'Will not start new scraping'.format(customer_id_cleaned)
                }
            }

        date_from_cleaned, is_correct_date_format = clean_date_from(date_from)

        if not is_correct_date_format:
            log('{} - POST /process  501: post_params {} :customer {}: date_from {}: '
                'wrong date format'.format(
                ip, request.POST.dict, customer_id_cleaned, date_from_cleaned
            ))

            return HTTPResponse(
                headers={'Content-Type': 'application/json'},
                status=501,
                body=json.dumps({
                    'data': {},
                    'status': False,
                    'meta': {
                        'code': 501,
                        'system_msg': "Wrong date format: {}. Should be dd/mm/yyyy".format(date_from_cleaned)
                    }
                })
            )

        cmd = build_cmd(
            customer_id_cleaned,
            access_id_cleaned,
            date_from_cleaned
        )

        if settings.IS_API_SERVER_PRODUCTON_MODE:
            # async run
            result = subprocess.Popen(cmd, shell=True)
            log(result)
        else:
            # synced run
            result = subprocess.run(cmd, shell=True)
            log(result)

        log('{} - POST /process  200: post_params {} :customer {}: date_from {}'.format(
            ip, request.POST.dict, customer_id_cleaned, date_from
        ))
        return {
            'data': {},
            'status': True,
            'meta': {
                'code': 200,
                'system_msg': 'Start new scraping for uid {} with 5/30 rule'.format(customer_id_cleaned)
            }
        }

    except:
        err_msg = traceback.format_exc()
        log_err('{}\n{}'.format(datetime.datetime.now(), err_msg))

        return HTTPResponse(
            headers={'Content-Type': 'application/json'},
            status=500,
            body=json.dumps({
                'data': {},
                'status': False,
                'meta': {
                    'code': 500,
                    'system_msg': 'Internal server error. Contact to administrator'
                }
            })
        )


def init_server(host):
    if settings.IS_API_SERVER_PRODUCTON_MODE:
        run(host=host, port=8080, server='gunicorn', workers=4, timeout=15)
    else:
        run(host=host, port=8080, timeout=15)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.abspath(os.path.join(
            settings.PROJECT_ROOT_PATH,
            'logs',
            'server__{}.log'.format(datetime.datetime.utcnow().strftime(settings.LOG_FILENAME_DATETIME_FMT))
        )),
        format='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    init_server(settings.LOCAL_IP)
