import re
import subprocess

import httpx
import trio
from bs4 import BeautifulSoup
from pprint import pp

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
}


credentionals = {
    'user': '22695262N',
    'pass': 'LAB9852'
}


def encrypt(params):
    x = subprocess.run(
        'node encode.js {} {} {}'.format(params[0], params[1], params[2]), capture_output=True)
    return x.stdout.decode().strip()


async def get_soup(content):
    return BeautifulSoup(content, 'lxml')


async def main():
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, base_url='https://conet.caixaontinyent.es') as client:
        params = {
            'IDIOMA': '01'
        }
        r = await client.get('/BEWeb/2045/N045/inicio_identificacion.action', params=params)
        soup = await get_soup(r.content)
        fpost, purl = [x['action']
                       for x in soup.select('#frmNormal, #frmSello')]
        data = {
            "CAMINO": "N045",
            "CAJA": 2045,
            "IDIOMA": "01",
        }
        r = await client.post(purl, data=data)
        goal = re.findall('\"(.+?)\"', r.text)
        req_params = "{}|{}".format(goal[0], credentionals['pass']).split('|')
        pin = encrypt(req_params)

        data = {
            "CAMINO": "N045",
            "CAJA": 2045,
            "OPERACION": "0001",
            "SELLO": goal[1],
            "IDIOMA": "01",
            "PIN": pin,
            "IDEN": "CL",
            "BROKER": "SI",
            "PAN": credentionals['user'],
            "NIF": credentionals['user'],
        }
        r = await client.post(fpost, data=data)
        soup = await get_soup(r.content)
        nurl = soup.select_one('#contenedor')['src']

        r = await client.get(nurl)
        soup = await get_soup(r.content)
        goal = soup.select_one('#Cliente_0')
        nurl = goal['action']

        data = {
            x['name']: x['value']
            for x in goal.select('input')
        }
        pp(data, indent=4)
        r = await client.post(nurl, data=data)
        soup = await get_soup(r.content)
        nurl = soup.select_one('#contenedor')['src']

        r = await client.get(nurl)
        with open(f'{credentionals["user"]}.html', 'w', encoding='utf-8-sig') as f:
            f.write(r.text)
            print('Saved TO:', f.name)


if __name__ == "__main__":
    trio.run(main)
