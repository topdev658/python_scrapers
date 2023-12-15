import re
import subprocess
import warnings

import httpx
import trio
from bs4 import BeautifulSoup
#from project import settings

warnings.filterwarnings("ignore", module='bs4')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
}

auth = {
    'user': 'B60917051001',
    'pass': '212022'
}


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
            base_url='https://be.caja-ingenieros.es',
            #proxies=req_proxies
    ) as client:
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
