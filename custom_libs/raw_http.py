"""raw_http provides tiny wrappers over sockets to make
 raw requests and get raw responses when necessary"""

import re
import socket
import ssl
from typing import Dict, List, Tuple, Union

import socks

__version__ = '2.1.2'

__changelog__ = """
2.1.2
fixed type hints
2.1.1
test proxies upd
2.1.0
use first el from given list of proxies
2.0.0
proxy support
"""

TIMEOUT = 10

TEST_PROXIES = [{
    'http': 'http://:@192.168.195.114:8115',
    'https': 'https://:@192.168.195.114:8115'
}]


def _parse_http_proxy_for_socket(proxies: Union[List[Dict[str, str]], Dict[str, str]],
                                 protocol: str) -> Tuple[str, str, str, int]:
    """
    :param protocol: "'http' or 'https'"
    """

    if type(proxies) == list:
        proxies_to_use = proxies[0]  # todo think how to implement rotation
    elif type(proxies) == dict:
        proxies_to_use = proxies
    else:
        raise Exception('Incorrect proxy format')

    http_proxy = proxies_to_use[protocol]
    proxy_username, proxy_password, proxy_host, proxy_port = \
        re.findall('http[s]?://(.*?):(.*?)@(.*?):(.*)', http_proxy)[0]
    return proxy_username, proxy_password, proxy_host, int(proxy_port)


def open_https(host: str, req_raw: str, port=443,
               proxies: Union[List[Dict[str, str]], Dict[str, str]] = None) -> str:
    """
    :param host: 'textberry.ru' or '91.224.22.44'
    :param port: 443
    :param req_raw:  correct headers + body
    :param proxies: requests-like proxies dict, e.g.:
        {'http': 'http://proxys:4MLDPBEz@91.126.60.95:6677',
        'https': 'https://proxys:4MLDPBEz@91.126.60.95:6677'}
    :return:
    """
    ip = socket.gethostbyname(host)

    s = socks.socksocket()
    if proxies:
        proxy_username, proxy_password, proxy_host, proxy_port = _parse_http_proxy_for_socket(proxies, 'https')
        s.set_proxy(socks.PROXY_TYPE_HTTP, proxy_host, proxy_port, username=proxy_username, password=proxy_password)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(TIMEOUT)
    sls = ssl.wrap_socket(s)
    sls.connect((ip, port))
    sls.send(req_raw.encode())

    body = b''
    while True:
        chunk = sls.recv()
        if not chunk:
            break
        # print(chunk)
        body += chunk
    html = body.decode(errors='ignore')
    s.close()
    return html


def open_http(host: str, req_body: str, port=80,
              proxies: Union[List[Dict[str, str]], Dict[str, str]] = None) -> str:
    req_ip = socket.gethostbyname(host)

    s = socks.socksocket()
    if proxies:
        proxy_username, proxy_password, proxy_host, proxy_port = _parse_http_proxy_for_socket(proxies, 'http')
        s.set_proxy(socks.PROXY_TYPE_HTTP, proxy_host, proxy_port, username=proxy_username, password=proxy_password)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(TIMEOUT)
    s.connect((req_ip, port))
    s.send(req_body.encode())

    body = b''
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        # print(chunk)
        body += chunk
    html = body.decode(errors='ignore')
    s.close()
    return html


def main():
    print('IP-API')
    req = """GET /json HTTP/1.0
    Host:ip-api.com

    """

    html = open_http('ip-api.com', req, proxies=TEST_PROXIES)
    print(html + '\n\n')

    # print('TEXTBERRY')
    # req = """GET / HTTP/1.0
    # Host:textberry.ru
    #
    # """
    # html = open_https('textberry.ru', req, proxies=TEST_PROXIES)
    # print(html + '\n\n')

    print('BANCOPOPULAR')
    req = """POST /ACBL/acl/login HTTP/1.1
Host: bm.bancopopular.es
Accept: application/json, text/plain, */*
Authorization: 9DJXLGxQqGfMpUnw4FgOih/JdzTubmZj3JKwNxQbT70+QF1/xoVtjP0ctiny56BndU3PXc/9/S4ppiY6B0FkSujjPkk33EyO
/jMETmhk71xWXaSbGfOlGH6yUNRxW5T8v1hbkjFSbiUNe8+kTkpWrop+FjHBNar4yW8BiPCiyKgGqZ+5DTkVv91AGoVu/bbE9aHOntXu
+WpvUJ8FU2skb9ogV+6wQrI7zaC+gxuvJH4=.SPWkvxzmOKEP0zLlKU4U4VH0egkUL52
/kGVb88hOqPeKwJsyHz9bjYM2a5eoSnkD37lU7gpBYWJVMvuvkVCmI3YizCWywSSVnsN3d7BRMcmoDJ7iT1cJbQbovEXEMA4X9ofkG4n8s9MvnsNI1PxXHV37uCoeo66DPo8JsQWC5nrP4eIQJk2dOn/oTLUgYMc+npTJy10s2EjB0SDeKHXEoyNaZpdWUO22yXujF1dJgTknP8Lm+TaH7emXgY4yPq4fEkOcVzSVW0TaHPgjUMStvlfa7nXNOr61w9CqD6FZ00d93L8S2Nuests+EZNwgnddmPURqkQdJVI8jFDhPEDE3Q==
cod_plataforma: 20
TKN-CRC: 
9508432759360be4b7477066b2b066473a2f33a2afcb810fb542a2f51271b77f557523a106a920ab7472e14f6fb41ce3a7d130fe0211a1407e8c3c1df910702b
Accept-Encoding: gzip, deflate
Accept-Language: es
Content-Type: application/json;charset=UTF-8
Origin: file://
Content-Length: 62
Connection: close
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 10_1_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) 
Mobile/14B100

{"usuario":"CARLOSRO","idPassword":"190614","plataforma":"20"}

    """
    html = open_https('bm.bancopopular.es', req)  # 178.60.206.42 or 195.55.131.42
    print(html + '\n\n')


if __name__ == '__main__':
    main()
