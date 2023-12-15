"""The server provides 2-way interaction for the scrapers and the frontend
that allows to get the real-time 2FA tokens

Scraper posts a question
Service returns query_id to the scraper
Front selects pending queries
Front posts an answer by the query_id
Scraper gets the answer by the query_id

RESP JSON format:
    {
      'data' : type: List or Dict,  --  any valuable data
      'status':  type: boolean      --  call target is reached or not
      'meta': {
        'code': type: int,    --  soft code, usually similar to http code
        'system_msg': string  --  some system message in human readable format
      }
    }

API:

POST /q                             --  insert a new query
GET  /q/<query_id>                  --  get the query
GET  /q/<customer_id>/<status_name> --  select queries by args
PUT  /q/<query_id>                  --  update the query: status, answer
DELETE  /q/<query_id>               --  delete the query

Look at the tests for correct requests.

It's ready to use without other parts of the project, so
it might be deployed AT ANY SERVER
"""

import argparse
import sys
import functools
import hashlib
import json
import logging
import os
import re
from collections import OrderedDict
from enum import Enum
from threading import Lock
from typing import Union, Dict, List, Optional

from bottle import (HTTPResponse, response, request, run, route, get,
                    post, delete, put, template, hook)


__version__ = '1.1.0'

__changelog__ = """
1.1.0
relative path for templates (abs is deprecated)
1.0.0
"""


def _encrypt(hashbase: str) -> str:
    return hashlib.sha256(hashbase.encode()).hexdigest().strip()


VALID_TOKEN = _encrypt('scraper-2fa-super-secret-token-2346wdqf')

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8181
DEFAULT_SERVER = 'wsgiref'

TEMPLATES_FOLDER = 'templates'


# == DATA TYPES ==

class QueryStatus(Enum):
    new = 'new'
    wait_answer = 'wait_answer'
    answered = 'answered'

    @staticmethod
    def by_name(status_name) -> 'QueryStatus':
        return getattr(QueryStatus, status_name)


class TokenQuery:
    __slots__ = ['query_id', 'customer_id', 'question', 'answer', 'status']

    @staticmethod
    def gen_query_id(customer_id: str, question: str) -> str:
        hashbase = '{}{}'.format(customer_id, question)
        return _encrypt(hashbase)

    def __init__(self, customer_id: str, question: str):
        self.query_id = self.gen_query_id(customer_id, question)
        self.customer_id = str(customer_id)
        self.status = QueryStatus.new  # init with 'new' status
        self.question = question
        self.answer = ''

    def to_dict(self):
        return OrderedDict([
            ('query_id', self.query_id),
            ('customer_id', self.customer_id),
            ('status', self.status.name),
            ('question', self.question),
            ('answer', self.answer)
        ])


# == STORAGE ==

class Storage:
    def __init__(self):
        # {query_id: TokenQuery}
        self._store = dict()  # type: Dict[str, TokenQuery]
        self._lock = Lock()

    def insert_query(self, query: TokenQuery) -> bool:
        """:returns true if inserted, false if not inserted if already exists"""
        q_id = query.query_id
        with self._lock:
            if q_id in self._store:
                return False
            self._store[q_id] = query
        return True

    def select_queries(self, customer_id: str, status: QueryStatus) -> List[TokenQuery]:
        with self._lock:
            return [q for q in self._store.values()
                    if q.status == status and q.customer_id == customer_id]

    def get_query(self, query_id: str) -> Optional[TokenQuery]:
        with self._lock:
            return self._store.get(query_id)

    def upd_query(self, query: TokenQuery) -> bool:
        q_id = query.query_id
        with self._lock:
            if q_id not in self._store:
                return False
            self._store[query.query_id] = query
        return True

    def delete_query(self, query_id: str) -> bool:
        """
        :returns true if deleted, false if there is no query_id in the storage
        """
        with self._lock:
            if query_id not in self._store:
                return False
        del self._store[query_id]
        return True


storage = Storage()


# == WRAPPERS and CHECKS ==

def is_valid_token(token: str):
    return token == VALID_TOKEN


def clean_customer_id(uid: str):
    return re.sub('[^0-9]', '', uid)


def check_auth(func):
    @functools.wraps(func)
    def wrapper(*a, **ka):
        req_env = request.headers.environ
        ip = req_env.get(
            'REMOTE_ADDR',
            req_env.get('HTTP_X_FORWARDED_FOR')
        )
        auth_token = request.headers.get('X-AUTH', '')
        if not auth_token:
            return resp_err(401, 'Permission denied')

        if not is_valid_token(auth_token):
            return resp_err(401, 'Permission denied')

        return func(*a, **ka)

    return wrapper


@hook('after_request')
def enable_cors():
    # https://stackoverflow.com/questions/43831255/
    _allow_origin = '*'
    _allow_methods = 'PUT, GET, POST, DELETE, OPTIONS'
    _allow_headers = ('Authorization, Origin, Accept, Content-Type, '
                      'X-Requested-With, X-CSRF-Token, X-AUTH')

    response.headers['Access-Control-Allow-Origin'] = _allow_origin
    response.headers['Access-Control-Allow-Methods'] = _allow_methods
    response.headers['Access-Control-Allow-Headers'] = _allow_headers


def do_try(func):
    @functools.wraps(func)
    def wrapper(*a, **ka):
        try:
            return func(*a, **ka)
        except Exception as e:
            return resp_err(500, str(e))

    return wrapper


# == RESPONSE FORMATS ==


def resp_ok(status: bool, data: Union[dict, list], msg: str) -> HTTPResponse:
    """
    resp JSON data format:
    {
      # TokenQuery.to_dict() or {'queries': [TokenQuery.to_dict()]}
      'data' : type: dict,
      # call target is reached or not
      'status':  type: boolean
      'meta': {
        # soft code, usually similar to http code
        'code': type: int,
        # some system message in human readable format
        'system_msg': string
      }
    }
    """
    return HTTPResponse(
        headers={
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': "*"
        },
        status=200,  # http code
        body=json.dumps({
            'data': data,
            'status': status,  # call target reached or not
            'meta': {
                'code': 200,
                'system_msg': msg
            }
        })
    )


def resp_err(code: int, err_msg: str) -> HTTPResponse:
    return HTTPResponse(
        headers={
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': "*"
        },
        status=code,
        body=json.dumps({
            'data': {},
            'status': False,
            'meta': {
                'code': code,
                'system_msg': err_msg
            }
        })
    )


# == HANDLERS ==


@route('/', method='OPTIONS')
@route('/api/v1/<path:re:.*>', method='OPTIONS')
def options_handler(path=None):
    return


@get('/ok')
def ok():
    return resp_ok(True, {}, 'ok')


@post('/api/v1/q')
@check_auth
@do_try
def insert_query():
    req_json = request.json
    question = req_json.get('question')
    customer_id = req_json.get('customer_id')
    if not (question and customer_id):
        return resp_err(501, 'No question/customer_id provided')

    query = TokenQuery(customer_id, question)
    result = storage.insert_query(query)
    msg = ('inserted' if result
           else 'not inserted: existing query with id={}'.format(query.query_id))
    return resp_ok(result, query.to_dict(), msg)


@get('/api/v1/q/<customer_id>/<status_name>')
@do_try
def select_queries(customer_id='', status_name=''):
    customer_id = clean_customer_id(customer_id)
    if not (customer_id and status_name):
        return resp_err(501, 'No customer_id/status provided')
    queries = storage.select_queries(customer_id, QueryStatus.by_name(status_name))
    return resp_ok(True, {'queries': [q.to_dict() for q in queries]}, 'selected')


@get('/api/v1/q/<query_id>')
@do_try
def get_query(query_id=''):
    if not query_id:
        return resp_err(501, 'No query_id provided')

    q = storage.get_query(query_id)
    if not q:
        return resp_ok(False, {}, 'no query with id={}'.format(query_id))
    return resp_ok(True, q.to_dict(), 'got')


@put('/api/v1/q')
@do_try
def upd_query():
    req_json = request.json
    query_id = req_json.get('query_id')

    if not query_id:
        return resp_err(501, 'No query_id provided')

    q = storage.get_query(query_id)
    if not q:
        # no query found
        return resp_ok(False, {}, 'not updated: no query with id={}'.format(query_id))

    # update provided fields
    q.query_id = req_json.get('query_id', q.question)
    q.question = req_json.get('question', q.question)
    q.answer = req_json.get('answer', q.answer)
    status_name = req_json.get('status', q.status.name)
    q.status = QueryStatus.by_name(status_name)

    storage.upd_query(q)
    q_upd = storage.get_query(query_id)

    result = (
            q.question == q_upd.question and
            q.answer == q_upd.answer and
            q.status == q_upd.status
    )

    return resp_ok(result, q_upd.to_dict(), 'updated')


@delete('/api/v1/q/<query_id>')
@check_auth
def delete_query(query_id: str):
    result = storage.delete_query(query_id)
    msg = 'deleted' if result else 'not deleted: no query with id={}'.format(query_id)
    return resp_ok(result, {}, msg)


@get('/<customer_id>')
def home(customer_id: str):
    response.body = template(os.path.join(TEMPLATES_FOLDER, 'home.html'),
                             customer_id=clean_customer_id(customer_id))
    return response


# == CMD ==

# defaults are suitable for tests
def main(host: str = DEFAULT_HOST,
         port: int = DEFAULT_PORT,
         server: str = DEFAULT_SERVER):
    # One worker to provide consistent storage,
    # no need to have more workers
    run(
        host=host,
        port=port,
        timeout=30,
        server=server,
        debug=True,
        # certfile='2fa.crt',
        # keyfile='2fa.key'
    )


def parse_cmdline_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        type=str
    )

    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
    )

    parser.add_argument(
        '--server',
        type=str,
        help='Server type: wsgiref(default) or gunicorn',
        default=DEFAULT_SERVER
    )

    args = parser.parse_args()
    return parser, args


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,  # for both info and errs, not used now
        format='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    cli_parser, cli_args = parse_cmdline_args()
    # Drop all args to fix gunicorn launch (it tries to parse cli too)
    sys.argv = sys.argv[:1]
    main(cli_args.host, cli_args.port, cli_args.server)
