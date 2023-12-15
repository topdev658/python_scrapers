"""
PROD TEST:
$ IS_PROD=true SRV_URL=http://52.207.27.88:8181 python -m unittest *.py

LOCAL TEST:
$ python -m unittest *.py
"""

import os
import threading
import time
import unittest
from urllib.parse import urljoin

import requests

try:
    from . import server_for_2fa
except SystemError:
    import server_for_2fa

IS_PROD = bool(os.getenv('IS_PROD', False))

# launch with SRV_URL=http://52.207.27.88:8181
SRV_URL = os.getenv(
    'SRV_URL',
    'http://{}:{}'.format(server_for_2fa.DEFAULT_HOST,
                          server_for_2fa.DEFAULT_PORT)
)


class Server2FATestCase(unittest.TestCase):
    server_url = SRV_URL
    customer_id = '123456789'
    question = 'PostFinance. Cuestión: 12 345 6789'
    q_id = ''  # will set in setUpClass

    @classmethod
    def setUpClass(cls) -> None:
        print('test: server URL={}'.format(cls.server_url))
        cls.q_id = server_for_2fa.TokenQuery.gen_query_id(
            cls.customer_id,
            cls.question
        )
        if not IS_PROD:
            print('test: local launch: start the server')
            # daemon to be auto-terminated in the end of the test
            thread = threading.Thread(target=server_for_2fa.main, daemon=True)
            thread.start()
            time.sleep(1)

    @classmethod
    def tearDownClass(cls) -> None:
        time.sleep(1)

    # REQUESTS

    def _insert(self) -> requests.Response:
        query = {
            'customer_id': self.customer_id,
            'question': self.question
        }
        resp = requests.post(
            urljoin(self.server_url, '/api/v1/q'),
            json=query,
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    def _select(self) -> requests.Response:
        resp = requests.get(
            urljoin(self.server_url, '/api/v1/q/{}/new'.format(self.customer_id)),
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    def _select_for_wrong_customer(self) -> requests.Response:
        resp = requests.get(
            urljoin(self.server_url, '/api/v1/q/{}/new'.format(0)),
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    def _get(self) -> requests.Response:
        resp = requests.get(
            urljoin(self.server_url, '/api/v1/q/{}'.format(self.q_id)),
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    def _update(self) -> requests.Response:
        query = {
            'query_id': self.q_id,
            'customer_id': self.customer_id,
            'question': self.question,
            'status': server_for_2fa.QueryStatus.wait_answer.name
        }
        resp = requests.put(
            urljoin(self.server_url, '/api/v1/q'),
            json=query,
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    def _delete(self) -> requests.Response:
        resp = requests.delete(
            urljoin(self.server_url, '/api/v1/q/{}'.format(self.q_id)),
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        return resp

    # TEST DESCRIPTIONS

    def _test_insert_query(self):
        resp = self._insert()
        resp_json = resp.json()
        self.assertNotEqual(resp_json['data'].get('query_id', ''), '')

    def _test_get_query(self):
        resp = self._get()
        resp_json = resp.json()
        self.assertNotEqual(resp_json['data'].get('query_id', ''), '')

    def _test_select_queries(self):
        resp = self._select()
        resp_json = resp.json()
        self.assertTrue(len(resp_json['data'].get('queries', [])) > 0)

    def _test_select_queries_for_wrong_customer(self):
        resp = self._select_for_wrong_customer()
        resp_json = resp.json()
        self.assertTrue(len(resp_json['data'].get('queries', [])) == 0)

    def _test_update_query(self):
        resp = self._update()
        resp_json = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_json['data'].get('status', ''), 'wait_answer')

    def _test_delete_query(self):
        resp = self._delete()

        resp_json = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_json['status'], True)

        # can't delete already deleted
        resp2 = self._delete()
        resp2_json = resp2.json()
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2_json['status'], False)

    # TESTS

    def test_server_started(self):
        resp = requests.get(
            urljoin(self.server_url, 'ok'),
        )
        self.assertEqual(resp.status_code, 200)

    def test_wrong_auth(self):
        query = {
            'customer_id': 12345,
            'question': 'xxx'
        }
        resp = requests.post(
            urljoin(self.server_url, '/api/v1/q'),
            json=query
        )

        self.assertEqual(resp.status_code, 401)

    def test_wrong_insert_query(self):
        query = {
            'customer_id': '',
            'question': ''
        }
        resp = requests.post(
            urljoin(self.server_url, '/api/v1/q'),
            json=query,
            headers={'X-AUTH': server_for_2fa.VALID_TOKEN}
        )
        self.assertTrue(resp.status_code, 501)

    def test_svc(self):
        funcs = [
            self._test_insert_query,
            self._test_select_queries,
            self._test_select_queries_for_wrong_customer,
            self._test_get_query,
            self._test_update_query,
            self._test_delete_query,
        ]

        for func in funcs:
            with self.subTest(func.__name__):
                func()


if __name__ == '__main__':
    unittest.main()
