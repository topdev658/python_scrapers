import re
import time
import traceback
from typing import *

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, InvalidElementStateException, WebDriverException  # + reexport
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # for reexport
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from custom_libs import date_funcs
from custom_libs.scrape_logger import ScrapeLogger  # to use here as type hint
from project import settings as project_settings

MAX_TIMEOUT = 10

__version__ = '1.7.0'

__changelog__ = """
1.7.0
selenium_driver_chrome in progress
1.6.0
use first from list of DEFAULT_PROXIES
1.5.1
from selenium.webdriver.common.keys import Keys  # for reexport
from selenium.common.exceptions import TimeoutException, InvalidElementStateException, WebDriverException  # + for reexport
1.5.0
DEFAULT_PROXIES_SELENIUM (!) to obtain capaibility with list of proxies for requests
1.4.0
try to handle exception during initialization
1.3.0
close_driver_if_opened
1.2.0
wait_and_get_elems
more exceptions import for reexport
1.1.0
wait_and_get_elem
"""


def _get_proxy_for_selenium(proxies=project_settings.DEFAULT_PROXIES) -> Tuple[str, str]:
    """
    >>> _get_proxy_for_selenium()
    ('proxys:4MLDPBEz', '91.126.60.95:6677')

    where
    proxies: DEFAULT_PROXIES_SELENIUM = {
        'http': 'http://proxys:4MLDPBEz@91.126.60.95:6677',
        'https': 'https://proxys:4MLDPBEz@91.126.60.95:6677'
    }
    """

    if type(proxies) == list:
        proxies_to_use = proxies[0]  # todo think how to implement rotation
    elif type(proxies) == dict:
        proxies_to_use = proxies
    else:
        raise Exception('Incorrect proxy format')

    http_proxy = proxies_to_use['http']
    proxy_auth, proxy_host_port = re.findall('.*?//(.*?)@(.*)', http_proxy)[0]
    return proxy_auth, proxy_host_port


# keep the function name for further refactoring for Caixa
def selenium_driver(scrape_logger: ScrapeLogger, proxies, w_size_x=800, w_size_y=600) -> \
        webdriver.PhantomJS:
    """
    initialize PhantomJS

    handle exception during initialization like
        selenium.common.exceptions.WebDriverException:
        Message: Service phantomjs unexpectedly exited. Status code was: 1

    Note: most possible reason: out of memory
    """

    proxy_auth, proxy_host_port = _get_proxy_for_selenium(proxies)

    scrape_logger.info('init driver: start: {}'.format(date_funcs.now()))
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = project_settings.DEFAULT_USER_AGENT

    service_args = ['--load-images=false']
    # service_args = []
    if proxies:
        service_args.extend([
            '--proxy={}'.format(proxy_host_port),
            '--proxy-type=http',
            '--proxy-auth={}'.format(proxy_auth)
        ])

    driver = None
    last_exception_traceback = ''
    for _ in range(10):
        try:
            driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
            break
        except:
            last_exception_traceback = traceback.format_exc()
            time.sleep(1)

    if not driver:
        scrape_logger.error(last_exception_traceback)
        # todo: think is it necessary exception or not
        raise Exception("Can't initialize webdriver after several tries. Check logs")

    driver.set_window_size(w_size_x, w_size_y)
    scrape_logger.info('init driver: success: {}'.format(date_funcs.now()))
    return driver


# chrome --headless --disable-gpu --proxy-server=192.168.195.114:8116 \
#  --proxy-type=http --proxy-auth=: --print-to-pdf http://api.ipify.org
# fixme service_args not passed
def selenium_driver_chrome(scrape_logger: ScrapeLogger,
                    proxies, w_size_x=800, w_size_y=600) -> webdriver.Chrome:
    """
    initialize Chrome

    handle exception during initialization like
        selenium.common.exceptions.WebDriverException:
        Message: Service ... unexpectedly exited. Status code was: 1

    Note: most possible reason: out of memory
    """

    proxy_auth, proxy_host_port = _get_proxy_for_selenium(proxies)

    scrape_logger.info('init driver: start headless chrome: {}'.format(date_funcs.now()))

    # chrome

    # no images
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    service_args = []

    # service_args.append('--load-images=false')
    service_args.extend([
        '--headless',
        '--disable-gpu',
    ])

    if proxies:
        service_args.extend([
            '--proxy-server={}'.format(proxy_host_port),
            '--proxy-type=http',
            '--proxy-auth={}'.format(proxy_auth)
        ])

    driver = None
    last_exception_traceback = ''
    for _ in range(10):
        try:
            driver = webdriver.Chrome(executable_path='/home/vladimirb/chromedriver',
                                      chrome_options=chrome_options, service_args=service_args)
            break
        except:
            last_exception_traceback = traceback.format_exc()
            time.sleep(1)

    if not driver:
        scrape_logger.error(last_exception_traceback)
        raise Exception("Can't initialize webdriver after several tries. Check logs")

    driver.set_window_size(w_size_x, w_size_y)
    scrape_logger.info('init driver: headless chrome success: {}'.format(date_funcs.now()))
    return driver



def close_driver_if_opened(driver):
    try:
        driver.close()
    except:
        pass
    try:
        driver.quit()
    except:
        pass


def update_requests_session_cookies(selenium_driver, request_session):
    """
    USAGE: self.s = update_requests_session_cookies(self.d, self.s)
    where self.d - selenium driver
          self.s - requests session
    """
    cookies = selenium_driver.get_cookies()
    for c in cookies:
        request_session.cookies.set(
            c['name'], c['value'], domain=c['domain'],
            # expires=c['expires'],
            path=c['path'], secure=c['secure'],
            rest={'httponly': c.get('httponly', None), 'expiry': c.get('expiry', None)})
    return request_session


def wait_and_get_elem(selenium_driver, css_selector, timeout=MAX_TIMEOUT):
    try:
        elem, err = WebDriverWait(selenium_driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        ), False
    except TimeoutException:
        elem, err = None, True

    return elem, err


def wait_and_get_elems(selenium_driver, css_selector, timeout=MAX_TIMEOUT):
    try:
        elems, err = WebDriverWait(selenium_driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
        ), False
    except TimeoutException:
        elems, err = None, True

    return elems, err
