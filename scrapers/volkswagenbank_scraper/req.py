"""
The reason of creating this module is that
requests package fails on open volksagenbank (ssl error)
because it uses urllib3 under the hood.
But urllib from standard library is working well

The interface is similar to regular requests.session interface
(to the parts that used in the project)
"""

import html
import json
import unittest
import urllib.parse
import urllib.request
from typing import Dict


def _cookies_header(cookies: Dict):
    cookies_header = ';'.join('{}={}'.format(name, val) for name, val in cookies.items())
    return cookies_header


def urlopen(url, **kw):
    """
    Basic method

    >>> cookies = {'n1': 'v1', 'n2': 'v2'}
    >>> proxies = [{'http': 'http://:@192.168.195.114:8116', 'https': 'http://:@192.168.195.114:8116'}]
    >>> headers = {}

    >>> resp1 = urlopen('http://httpbin.org/cookies', headers=headers, proxies=proxies, cookies=cookies, method='GET')
    >>> resp1.json() ==  {'cookies': {'n2': 'v2', 'n1': 'v1'}}
    True

    >>> resp2 = urlopen('http://httpbin.org/ip', headers=headers, proxies=proxies, cookies=cookies, method='GET')
    >>> resp2.json()
    {'origin': '217.113.248.116'}
    """

    # https://stackoverflow.com/questions/22967084/urllib-request-urlretrieve-with-proxy
    # https://stackoverflow.com/questions/28880629/python-3-urllib-request-send-cookie-fetch-results
    # https://docs.python.org/3.5/library/urllib.request.html?highlight=urllib

    proxies = kw.get('proxies', [{}])
    headers = kw.get('headers', {})
    cookies = kw.get('cookies', {})
    method = kw.get('method', 'GET')
    data = urllib.parse.urlencode(kw.get('data', {})).encode('utf-8')

    proxy_dict = proxies[0]
    proxy_handler = urllib.request.ProxyHandler(proxy_dict)
    opener = urllib.request.build_opener(proxy_handler)

    headers['Cookie'] = _cookies_header(cookies)

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp = opener.open(request)

    return VWResp(resp)


class VWResp:
    def __init__(self, opener_resp):
        self.response = opener_resp
        self.content = self.response.read()

    @property
    def text(self):
        try:
            return html.unescape(self.content.decode('utf-8'))
        except:
            return html.unescape(self.content.decode('iso-8859-1'))

    def json(self):
        return json.loads(self.text)

    @property
    def url(self):
        return self.response.url


class VWSession:
    """Keep cookies between requests"""

    def __init__(self):
        self.cookies = {}
        return

    def _update_cookies(self, resp: VWResp):
        """
        Simple cookie updater
        It collects all cookies for any path as for '/'
        """
        resp_headers = resp.response.info()
        for header, value in resp_headers.items():
            if header == 'Set-Cookie':
                c_name, c_val = value.split(';')[0].split('=')
                self.cookies[c_name] = c_val

    def open(self, url, method, **kw):
        kw['cookies'] = self.cookies
        kw['method'] = method
        vwresp = urlopen(url, **kw)  # type: VWResp
        self._update_cookies(vwresp)
        return vwresp

    def get(self, url, **kw):
        """get with cookies"""
        return self.open(url, 'GET', **kw)

    def post(self, url, **kw):
        """post with cookies"""
        return self.open(url, 'POST', **kw)


class TestVWSession(unittest.TestCase):
    def test_proxy(self):
        proxies = [{'http': 'http://:@192.168.195.114:8116', 'https': 'http://:@192.168.195.114:8116'}]
        s = VWSession()
        resp = s.get(
            'http://httpbin.org/ip',
            proxies=proxies
        )
        self.assertEqual(resp.json(), {'origin': '217.113.248.116'})

    def test_no_proxy(self):
        s = VWSession()
        resp = s.get(
            'http://httpbin.org/ip'
        )
        self.assertEqual(resp.json(), {'origin': '78.153.142.88'})

    def test_cookies(self):
        s = VWSession()
        resp = s.get(
            'https://oficinaempresas.bankia.es/es/login.html'
        )
        self.assertNotEqual(s.cookies, {})


if __name__ == '__main__':
    unittest.main()
