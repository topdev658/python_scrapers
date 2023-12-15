import requests
import logging


__version__ = '1.2.0'

__changelog__ = """
1.2.0
get_current_ip: raise initial (not wrapped) exc if can't get IP 
1.1.0
_get_proxies_to_use to handle list of proxies
"""


def log(text):
    print(text)
    logging.info(text)


def _get_proxies_to_use(proxies):
    if not proxies:
        return
    if type(proxies) == list:
        return proxies[0]
    elif type(proxies) == dict:
        return proxies
    raise Exception('Incorrect proxy format')


def check_ip(proxies=None):
    log('Check IP address')
    proxies_to_use = _get_proxies_to_use(proxies)
    try:
        if proxies:
            log(requests.get('http://ip-api.com/json', proxies=proxies_to_use, timeout=5).json())
        else:
            log(requests.get('http://ip-api.com/json', timeout=5).json())
        log('\n')
    except Exception as e:
        log('check_ip: handled exception: {}'.format(e))


def get_current_ip(proxies=None) -> str:
    log('Get current IP address')
    proxies_to_use = _get_proxies_to_use(proxies)
    try:
        ip = requests.get('http://api.ipify.org', proxies=proxies_to_use, timeout=10).text
    except:
        ip = requests.get('http://ip-api.com/json', proxies=proxies_to_use, timeout=10).json()['query']
    return ip
