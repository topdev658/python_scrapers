"""A wrapper for requests with a customized MySession"""

import random
import time
from http import client
from logging import Logger
from typing import List, Optional, Tuple, Union

import requests

from custom_libs.scrape_logger import ScrapeLogger

# must be > 100 to cover some cases, used by requests
# fixes
# requests.exceptions.ConnectionError: ('Connection aborted.', HTTPException('got more than 100 headers',))
client._MAXHEADERS = 1000

__version__ = '4.4.0'

__changelog__ = """
4.4.0
tweak global http client config (MAXHEADERS)
4.3.1
longer TIMEOUT_DEFAULT=30
4.3.0
handle logger==None in constructor, now can use MySession() instead of myrequests.session()
re-assigned Session, Response, Request for better IDE integration
optim imports
4.2.5
inc TIMEOUT_DEFAULT
4.2.4
fixed type hints
4.2.3
unused import for proper type hints
4.2.2
fixed type hints
4.2.1
bugfix: if 'resp is None' instead of 'if not resp' because failed resp is False, but only None should be processed
4.2.0
additional handler: success_on_cookies_even_if_exception
4.1.1
reformatted
4.1.0
resp_codes_bad_for_proxies as property
4.0.0
retry_on_codes optional parameter
3.2.0
cache current_proxies_dict to keep the state
3.1.0
improved logging
3.0.0
iterates over randomly shuffled list of proxies with several tries per proxy
2.0.0
err msg if no more proxy approach
1.3.0
failed proxies log changed to info and error
1.2.0
err_msg -> warn_msg
1.1.0
add ReadTimeout to handling exc
1.0.2
init msg if debug only
1.0.1
from requests import Session, Request, Response  # for typing from scrapers
"""

# to re-import from scrapers
Session = requests.Session  # todo remove after refactoring
Response = requests.Response
Request = requests.Request

MAX_RETRIES_PER_PROXY = 3
RESP_CODES_BAD_FOR_PROXIES = [500, 502, 503, 504, 403, None]
REQ_EXCEPTIONS_TO_BLOCK_PROXY = (requests.exceptions.ConnectionError,
                                 requests.exceptions.ConnectTimeout,
                                 requests.exceptions.ReadTimeout)
# to avoid hanging with default presets of requests
TIMEOUT_DEFAULT = 30

DEBUG = False


class MySession(requests.Session):
    """
    Implements basic methods of requests.session with automatically proxy rotation on errors

    On error it marks proxy as blocked (to skip it next time)
    Supports proxies with different types: Union[List[Dict[str, str], Dict[str, str], None]
    Iterates over randomly shuffled list of proxies with several tries per proxy
    Raises a requests' exception if got final exception after all tries

    By default it uses ScrapeLogger to send error notifications

    ADDITIONAL ABILITIES
    resp_codes_bad_for_proxies: can be redefined to use custom list
    """

    def __init__(self, logger: Union[Logger, ScrapeLogger] = None):
        super().__init__()
        self.blocked_proxies = []  # type: List[dict]
        self.logger = logger or ScrapeLogger('MySession', '', '')
        DEBUG and self.logger.info('MySession successfully initialized')
        self.current_proxies_dict = None
        self.resp_codes_bad_for_proxies = RESP_CODES_BAD_FOR_PROXIES  # can be redefined
        self.success_on_cookies_even_if_exception = []  # type: List[str]

    def _is_success_on_cookies_even_if_exception(self) -> bool:
        """Returns True if found target cookie in session
        Known case: SocieteGenerale: it breaks ssl handshake but before returns correct cookie
        """
        cookies = self.cookies.get_dict()
        return any(c in cookies for c in self.success_on_cookies_even_if_exception)

    def _check_is_useful_proxies_dict_and_update_blocked_proxies(self, proxies_dict: dict,
                                                                 custom_proxies: List[dict]):
        """
        return True if proxy in list of self.blocked_proxies
        reset self.blocked_proxies if all proxies from custom_proxies are blocked
        """
        if proxies_dict not in self.blocked_proxies:
            return True

        # are all proxies blocked?
        if len(self.blocked_proxies) == len(custom_proxies):
            self.blocked_proxies = []
            return True

        return False

    def _log_err_msg(self, url, proxies_dict, reason: str = ''):
        self.logger.error(
            'MYREQUESTS: ERROR: URL {} : PROXIES {} : REASON {} '.format(
                url,
                proxies_dict,
                reason
            )
        )

    def _log_failed_request(self, url, proxies_dict, reason):
        self.logger.info('FAILED REQUEST: {} : proxies {} : {}'.format(url, proxies_dict, reason))

    def _mark_proxy_as_blocked(self, proxies_dict):
        self.blocked_proxies.append(proxies_dict)

    def _req_standard_params(self, *args, **kwargs) -> Tuple[Optional[requests.Response],
                                                             Optional[Exception]]:
        """with retries and logging"""

        resp = requests.Response()
        url = args[1]
        proxies = kwargs.get('proxies')
        exception = None

        i = 0
        while i < MAX_RETRIES_PER_PROXY:
            try:
                resp = super().request(*args, **kwargs)
                if resp.status_code not in self.resp_codes_bad_for_proxies:
                    # SUCCESS
                    return resp, None
                else:
                    exception = None
                    self._log_failed_request(url,
                                             proxies,
                                             reason='resp code: {}'.format(resp.status_code))

            except REQ_EXCEPTIONS_TO_BLOCK_PROXY as exc:
                # None as response to rely on cookie in the caller
                exception = exc
                if self._is_success_on_cookies_even_if_exception():
                    # special case to handle None resp, but session on app code
                    return None, exception
                self._log_failed_request(url,
                                         proxies,
                                         reason='exc: {}'.format(exc))

            i += 1
            time.sleep(random.random())

        # FAILED
        return resp, exception

    def custom_request(self, *args, **kwargs):
        """
        supports proxies with different types: type: Union[List[dict], Dict, None]
        iterates over randomly shuffled list of proxies with several tries per proxy
        """

        custom_proxies = kwargs.get('proxies')  # type: Union[dict, List[dict]]

        if not custom_proxies or type(custom_proxies) == dict:
            custom_proxies = [custom_proxies]

        random.shuffle(custom_proxies)

        # put current proxy in the begginng of shuffled list
        if self.current_proxies_dict:
            if self.current_proxies_dict in custom_proxies:
                custom_proxies_copy = custom_proxies.copy()
                custom_proxies_copy.pop(custom_proxies.index(self.current_proxies_dict))
                custom_proxies = [self.current_proxies_dict] + custom_proxies_copy

            else:
                custom_proxies = [self.current_proxies_dict] + custom_proxies

        resp = requests.Response()
        url = args[1]
        exc = None
        err_reason = ''  # will be used only if failed

        for proxies_dict in custom_proxies:
            if not self._check_is_useful_proxies_dict_and_update_blocked_proxies(proxies_dict, custom_proxies):
                continue

            self.current_proxies_dict = proxies_dict

            # set requests' standard proxy
            kwargs['proxies'] = proxies_dict  # type: dict

            resp, exc = self._req_standard_params(*args, **kwargs)
            # special case when we want to get 'None' as resp basing on cookies from session
            if resp is None:
                return None, None
            if resp.status_code not in self.resp_codes_bad_for_proxies:
                # SUCCESS
                return resp, None

            self._mark_proxy_as_blocked(proxies_dict)
            if exc:
                err_reason = 'most recent exc: {}\n\n NO MORE PROXIES'.format(exc)
            else:
                err_reason = 'most recent resp code: {} \n\n {} \n\n NO MORE PROXIES'.format(resp.status_code,
                                                                                             resp.text)

        # FAILED
        self._log_err_msg(url, custom_proxies, reason=err_reason)
        return resp, exc

    def request(self, *args, **kwargs):

        if DEBUG:
            method = args[0]
            url = args[1]
            self.logger.info('{} to {} with proxies {}'.format(method, url, kwargs.get('proxies')))

        # set timeout in any case
        kwargs['timeout'] = kwargs.get('timeout', TIMEOUT_DEFAULT)

        resp, exc = self.custom_request(*args, **kwargs)
        if exc:
            raise exc
        else:
            return resp


def session(logger: Logger = None):
    """The same func to create an instance of MySession similar to requests.session() call.
    It is not necessary to use myrequests.session() (as for 'requests'), just use MySession() constructor
    """
    return MySession(logger)


if __name__ == '__main__':
    DEBUG = True
    s = MySession()
    proxies = [{
        'http': 'http://:@192.168.195.114:8115',
        'https': 'http://:@192.168.195.114:8115'
    },
        {
            'http': 'http://:@192.168.195.114:8116',
            'https': 'http://:@192.168.195.114:8116'
        },
        {
            'http': 'http://:@192.168.195.114:8117',
            'https': 'http://:@192.168.195.114:8117'
        }]

    print(s.get('http://api.ipify.org', proxies=proxies, timeout=3).text)
    s.resp_codes_bad_for_proxies = [500]
    print(s.get('http://api.ipify.org', proxies=proxies, timeout=3).text)
    print(s.get('http://api.ipify.org', proxies=proxies).text)
    print(s.get('http://api.ipify.org', proxies=proxies).text)

    # should get failed responses
    s.get('http://yau.ru', proxies=proxies)

    try:
        session().get('http://yau.ru')
    except Exception as e:
        print("yau.ru: handled exception: {}".format(e))
