import re
import random
import subprocess
import urllib
import warnings
from collections import OrderedDict

import httpx
import trio
from bs4 import BeautifulSoup
import custom_libs.date_funcs
#from project import settings

warnings.filterwarnings("ignore", module='bs4')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
}

auth = {
    'user': '20005541A',
    'pass': '369258'
}

DEFAULT_PROXIES = {
    # public IP 185.74.81.115
    # {
        'http://': 'http://:@192.168.195.114:8115',
        'https://': 'http://:@192.168.195.114:8115',
    }
#
#     # public IP 185.74.81.116
#     {
#         'http://': 'http://:@192.168.195.114:8116',
#         'https://': 'http://:@192.168.195.114:8116',
#     },
#
#     # public IP 185.74.81.117
#     {
#         'http://': 'http://:@192.168.195.114:8117',
#         'https://': 'http://:@192.168.195.114:8117',
#     },
#
#     # public IP 185.74.81.118
#     # use port 8120 instead of 8118 port (which often blocked by websites)
#     {
#         'http://': 'http://:@192.168.195.114:8120',
#         'https://': 'http://:@192.168.195.114:8120',
#     },
#
#     # public IP 185.74.81.119
#     {
#         'http': 'http://:@192.168.195.114:8119',
#         'https': 'http://:@192.168.195.114:8119',
#     },
#
#     # {'http': 'http://proxys:4MLDPBEz@91.126.60.95:6677',
#     #  'https': 'https://proxys:4MLDPBEz@91.126.60.95:6677'}
#
#     # NEW IP POOL
#
#     # public IP 185.74.80.115
#     {
#         'http://': 'http://:@192.168.195.114:7115',
#         'https://': 'http://:@192.168.195.114:7115',
#     },
#
#     # public IP 185.74.80.116
#     {
#         'http://': 'http://:@192.168.195.114:7116',
#         'https://': 'http://:@192.168.195.114:7116',
#     },
#
#     # public IP 185.74.80.117
#     {
#         'http://': 'http://:@192.168.195.114:7117',
#         'https://': 'http://:@192.168.195.114:7117',
#     },
#
# ]


def encrypt(params):
    x = subprocess.run(
        'node encode.js {} {} {}'.format(params[0], params[1], params[2]), capture_output=True)
    return x.stdout.decode().strip()


def get_cookie(*params):
    x = subprocess.run(
        'node f5_encrypted.js {} {} {}'.format(params[0], params[1], params[2]), capture_output=True)
    return x.stdout.decode().strip()


async def main():
    #req_proxies=settings.DEFAULT_PROXIES_FOR_HTTPX
    async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            base_url='https://banking.eurocajarural.es',
            proxies=DEFAULT_PROXIES
    ) as client:

        client.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'en,es-ES;q=0.8,es;q=0.5,en-US;q=0.3',
			'Connection': 'keep-alive',
			'Host': 'banking.eurocajarural.es',
			'Referer': 'https://eurocajarural.es/',
			'Sec-Fetch-Dest': 'document',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-Site': 'same-site',
			'Sec-Fetch-User': '?1',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        })
        resp_0 = await client.get('https://banking.eurocajarural.es/3081/3081/#/beext/identificacion')
        soup = BeautifulSoup(resp_0.content, 'lxml')
        script_url = soup.select('script')[1]['src']

        resp_1 = await client.get(script_url)
        bobcmn = re.search('bobcmn\".*?\"(.*?)\"', resp_0.text).group(1)
        con = re.search('\"(0.*?)\"', resp_0.text).group(1)
        src = soup.select('script')[-1]['src']
        #       secret = re.search('delete Number.*?\"(.*?)\"', r.text, re.M).group(1)
        secret = re.search(r'(?s)delete Number.*?\"(.*?)\"', resp_1.text, re.M).group(1)
        cookie = get_cookie(bobcmn, con, secret)
        client.cookies.update({
            'TSc7f0f12a075': cookie
        })
        # client.headers.update({
        #     'Cache-Control': 'no-cache',
        #     'Pragma': 'no-cache',
        # })

        resp_2 = await client.get('https://banking.eurocajarural.es/3081/3081/')

        client.headers.update({'Referer': 'https://banking.eurocajarural.es/3081/3081/'})

        # resp3 = await client.get('https://banking.eurocajarural.es/3081/3081/assets/i18n/es.json')
        # resp4 = await client.get('https://banking.eurocajarural.es/3081/I081/estado/estado.json')

        # timestamp = custom_libs.date_funcs.now_str('%d/%m/%Y-%H:%M:%S,%f').strip()[:-3]
        # timestampFin = custom_libs.date_funcs.now_str('%d/%m/%Y-%H:%M:%S,%f').strip()[:-3]
        # lggro_value = '{"version":"8.0.3","mensaje":"INICIO /beext/identificacion","timestamp":"06/10/2023-11:34:34,925","timestampFin":"06/10/2023-11:34:35,203","nivel":"WARN","ruta":"/","estadisticas":true,"errorName":"","errorMensaje":""}'
        #
        # resp5 = await client.post(
        #    'https://banking.eurocajarural.es/BEWeb/3081/3081/lggAngpag.action',
        #    data={'LGGR0': 'eyJ2ZXJzaW9uIjoiOC4wLjMiLCJtZW5zYWplIjoiSU5JQ0lPIC9iZWV4dC9pZGVudGlmaWNhY2lvbiIsInRpbWVzdGFtcCI6IjA2LzEwLzIwMjMtMDk6MTU6MDcsMDg0IiwidGltZXN0YW1wRmluIjoiMDYvMTAvMjAyMy0wOToxNTowNyw2NjkiLCJuaXZlbCI6IldBUk4iLCJydXRhIjoiLyIsImVzdGFkaXN0aWNhcyI6dHJ1ZSwiZXJyb3JOYW1lIjoiIiwiZXJyb3JNZW5zYWplIjoiIn0'})

        # client.cookies.update({
        #     'TSc7f0f12a077': '087b6cfa27ab2800abac0c084ba69f8b1289bff9a0f67e73bcd84371c98adff895106867497f455dce6dd8cee4d2e99a08d46cbb421720003ace608a6e6bede670850f98b129ba8c35a7058ffa0b3902fa757b13c2d8b22f'
        # })


        resp6= await client.get('https://banking.eurocajarural.es/TSPD/?type=22')
        resp7 = await client.get('https://banking.eurocajarural.es/BEWeb/3081/3081/delete_sesion_cookies.do')


        aleatorioidensello_param = str(int(random.uniform(1000000000, 9999999999)))

        req_inicio_sello_params = {
            'CAJA': '3081',
            'CAMINO': '3081',
            'IDIOMA': '01',
            'ALEATORIOIDENSELLO': aleatorioidensello_param,
        }
        resp_inicio_sello = await client.post(
            'https://banking.eurocajarural.es/BEWeb/3081/3081/inicio_identificacion_sello.action',
            data=req_inicio_sello_params
        )

        resp_inicio_sello_json = resp_inicio_sello.json()

        sello_param = resp_inicio_sello_json['sello']
        clave = resp_inicio_sello_json['claveCalcula']

        req_params = clave.split('|')

        req_params.append(auth['pass'])
        encrypted = encrypt(req_params)
        req_login_params = OrderedDict([
             ('SELLO', sello_param),
             ('OPERACION', '0002'),
             ('BROKER', 'NO2'),
             ('PINV3', 'si'),
             ('PIN', encrypted),  # '83ecc45223b7984677518da8fd059e2c'
             ('PAN', '9999993081'),
             ('PANENT', auth['user'])
         ])

        resp_logged_in = await client.post(
             "https://banking.eurocajarural.es/BEWeb/3081/3081/identificacion.action?CAJA=3081&CAMINO=3081&IDIOMA=01",
             data=req_login_params,
         )




        resp5 = await client.get('estado.json' )


        # resp_0 = await client.get('https://eurocajarural.es')

        # _resp_init = s.get(
        #     'https://eurocajarural.es/',
        #     headers=self.req_headers,
        #     proxies=self.req_proxies
        # )

        # _resp_login_page = await client.get('https://banking.eurocajarural.es/3081/3081/#/beext/identificacion')
        #
        # aleatorioidensello_param = str(int(random.uniform(1000000000, 9999999999)))
        #
        # req_inicio_cello_params = {
        #     'CAJA': '3081',
        #     'CAMINO': '3081',
        #     'IDIOMA': '01',
        #     'ALEATORIOIDENSELLO': aleatorioidensello_param,
        # }
        # resp_inicio_cello = await client.post(
        #     'https://banking.eurocajarural.es/BEWeb/3081/3081/inicio_identificacion_sello.action',
        #     data=req_inicio_cello_params
        # )
        #
        #
        # resp_inicio_cello_json = resp_inicio_cello.json()
        #
        # sello_param = resp_inicio_cello_json['sello']
        #
        # clave = resp_inicio_cello_json['claveCalcula']
        # req_params = clave.split('|')
        # sello = sello_param
        # req_params.append(auth['pass'])
        # encrypted = encrypt(req_params)
        #
        # req_login_params = OrderedDict([
        #     ('SELLO', sello_param),
        #     ('OPERACION', '0002'),
        #     ('BROKER', 'NO2'),
        #     ('PINV3', 'si'),
        #     ('PIN', encrypted),  # '83ecc45223b7984677518da8fd059e2c'
        #     ('PAN', '9999993081'),
        #     ('PANENT', auth['pass'])
        # ])
        #
        # resp_logged_in = await client.post(
        #     "https://banking.eurocajarural.es/BEWeb/3081/3081/identificacion.action?CAJA=3081&CAMINO=3081&IDIOMA=01",
        #     data=req_login_params,
        # )
        #
        #

        params = {
            'DEDONDE': 'GENE',
            'IDIOMA': '02'
        }
        r = await client.get('/BEWeb/3025/6025/CABEm_0_fusionRestyling.action', params=params)

        ref = str(r.url)
        _random = r.url.params.get('RANDOM')
        new_url = re.search('urlSello2 = \"(.+)\"', r.text).group(1)
        post_url = re.search('action=\"(.+?)\"', r.text).group(1)

        r = await client.get(new_url)
        soup = BeautifulSoup(r.text, 'lxml')
        req_params = soup.select_one('clave').text.split('|')
        sello = soup.select_one('sello').text
        req_params.append(auth['pass'])
        pin = encrypt(req_params)
        data = {
            "PAN": auth["user"],
            "PIN": pin,
            "OPERACION": "0002",
            "IDIOMA": "02",
            "CAJA": "3025",
            "SELLO": sello,
            "IDEN": "",
            "PINV2": "si",
            "NUMV": pin,
            "INILOGIN": "S",
            "PUESTO": [
                "",
                ""
            ],
            "OPERADOR": [
                "",
                ""
            ],
            "EASYCODE": [
                "",
                ""
            ],
            "BROKER": "SI",
            "OPGENERICA": [
                "",
                ""
            ],
            "GENERICA": "S",
            "DEDONDE": [
                "GENE",
                "GENE"
            ],
            "ACCSS": "FUSION",
            "REFDESDE": [
                "",
                ""
            ],
            "RANDOM": _random,
            "PERR_AUX": ""
        }
        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            'Referer': ref
        })

        r = await client.post(post_url, data=data)
        soup = BeautifulSoup(r.content, 'lxml')
        bobcmn = re.search('bobcmn\".*?\"(.*?)\"', r.text).group(1)
        con = re.search('\"(0.*?)\"', r.text).group(1)
        src = soup.select('script')[-1]['src']
        data = r.request.content.decode()

        r = await client.get(src)
#       secret = re.search('delete Number.*?\"(.*?)\"', r.text, re.M).group(1)
        secret = re.search(r'(?s)delete Number.*?\"(.*?)\"', r.text, re.M).group(1)
        cookie = get_cookie(bobcmn, con, secret)
        client.cookies.update({
            'TSd4417f47075': cookie
        })

        r = await client.post(post_url, files={'_pd': data})
        soup = BeautifulSoup(r.text, 'lxml')
        nurl = soup.select_one('form')['action']
        data = {
            x['name']: x['value']
            for x in soup.select_one('form').select('input')
        }

        r = await client.post(nurl, data=data)
        soup = BeautifulSoup(r.text, 'lxml')
        purl = soup.select_one('#supframeBE')['src']
        r = await client.get(purl)
        nurl = re.search(r"([^\"]*not7327_d_0GNRL.*?)\\",
                         r.text, re.M).group(1)
        data = {
            "CAJA": "3025",
            "CAMINO": "6025",
            "CLIENTE": '3025218363',
            "DEDONDE": "PSGL",
            "IDIOMA": "02",
            "LLAMADA": data['LLAMADA'],
            "OPERAC": "1004",
            "OPERACION": "PSGL",
            "OPERACREAL": "7327",
            "TIPE": "2"
        }
        r = await client.post(nurl, data=data)
        with open('r.html', 'w', encoding='utf-8-sig') as f:
            f.write(r.text)


if __name__ == "__main__":
    trio.run(main)
