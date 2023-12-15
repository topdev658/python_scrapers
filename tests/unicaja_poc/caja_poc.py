import re
import subprocess
import warnings

import httpx
import trio
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", module='bs4')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
}

auth = {
    'user': 'test',
    'pass': 'aaa'
}


def encrypt(params):
    x = subprocess.run(
        'node encode.js {} {} {}'.format(params[0], params[1], params[2]), capture_output=True)
    return x.stdout.decode().strip()


def get_cookie(*params):
    return '3:mobXsFNKoWwr4lIl9nfMqQ==:cry269vwS1QdXjPUV666+1+phz1XcovXiZLrqutkvnBkWf8cpIzemORDB/840iS8jjQby12z+tzY9GAhW/nWMuPVQ5+Wm5ki8jelOtRwWv5/bhB6t7kjvKXkNofr/oFWNIWlX8zlViQof1r6WI5BwmzgAlSSr0UG0Ln3jB3MujEjQfyBE90Qj4qUIGAee0vMaonjoI3e71K3UoAnlUQzOnK0EgKpOt5UPDw6BtRh+9r8CrC/0OLs4cZvnwOL9JToS1DrD2UD92wl9p94K0wqggonINHnD7sYr1c3o+m/Nm1Gv6qTlTF8fi3usRkd0fNgGVNZwikFemGTdqGU4ZgZO2NZRyAFvcUeOugWCMq22b4zwLUC3zQUNPQaUSNtOFUtvidi1r1SfFuc9Ik4z3OE/LHB/l9+YuYoPB01N8a5N5TRW752ya460BPYZ05iu1oidCGQwZMebOX6soInUrjb3w==:1JqfHtC+1WdBAGc7JeOJCpLpqdvzoINnv/8zYkLiEh8='
    # x = subprocess.run(
    #     'node unicaja.js {} {} {}'.format(params[0], params[1], params[2]), capture_output=True)
    return x.stdout.decode().strip()


async def main():
    async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            base_url='https://univia.unicajabanco.es',

    ) as client:

        resp_0 = await client.get('/login')

        soup = BeautifulSoup(resp_0.content, 'lxml')
        src = soup.head.select('script')[-1]['src']
        resp_1 = await client.get(src)
        resp_2 = await client.get('/favicon.ico')

        req_login_params = {
            'error': None,
            'old_token': None,
            'performance': {'interrogation': 442},
            'solution': {
                'interrogation': {
                    'cr': 394634885,
                    'og': 1,
                    'p': "KStDEYFG8AlzgKVXPyxhxt/ucAHuTnMri5Rz6qzhOKEHq438UV3xN3oRi74R/rAJ/vnDwsxF/co0RyHZ+qCnipz/9hKuC"
                         "zazzsbwcHEk7z3cPNVoDJH6PDoEhCKcvOiApuEHXMMPvo29Uu4MN/7nVdOpJAXyF6Oi1xBi5uA2dPqHNsIkV19iMWQPC"
                         "KAQMGMLoznDzU3LeUb+Bq1fPaYuwZzxPhNkCS1tHdwta2S+/DdLNdlvDBH4divRHz1NJfsUtSVXWJjf6ZLq2XGNoCMrCZ"
                         "lgPcyq2SBj2BltIa/ytfiT/d5gC5t9fP9DCq1fNezYpiFHlEpK+A19gyBdPyP3zoH46N29xuK7HtWga6/j+fvCqw322FQ"
                         "jtisFHqqH6P0VtahVXVra5VAqEyACeCzoAVgx8p3mgPk9AYN6dDmqbm/UJ919DwA3u7wFCiocPn4EL3mAS4aSNdO63iyH"
                         "NXzqXI+0Y1txSux2nMh6PDlpraHLcEn+xtn2uztFh2YeN6w…KyQYF8uHVl5+EeMAk9BY42LbaMQj9dPaKP57YcilTcbVl"
                         "h2jOQ9br9jEd45B92CL772ATtuzPgICGf7NIhTdi4u74FCHUab2VY4ySKnwcaspejEf9CO7WwUQbibE3xXizvHl7k6rs"
                         "ydbqPN9ujDN5xvfoPAefX+CzM5TLYzlDJaZnu3vwPZH72WI4rOZviRq2i3d3l5aivd7UFuhbuxxmgI2AUUz2DbfUXPCHG"
                         "lJVJr4CoWTuHYPjwWMtkfI42F2hk2Zci/Xkknf8OY735yQu8IYrpFeUgEU+nZKY68nUNO0Ho3NRkdqAQ0n1VZ3eKYHZMg"
                         "M7AeVTqkWQJefhr2t0teY5umaQo29qp5OS2KHoX+8TgmBLtvinOWKJDY7WTc+4X2tCLrU4sxTHd9ST+10qpa8u3Wb+tSZ"
                         "fsYTM2r/MavZEqCNExd74HTScX5ybXZKXImE6fvBc9lSbDejVwGIonLkL21umh3Z6noHhypzdWsBzqgpEh62vbm7caLm0"
                         "U",
                    'sr': 1367610210,
                    'st': 1694676615
                },
                'version': 'beta'
            }
        }
        post_url = 'https://univia.unicajabanco.es/nq-vent-man-macd-and-and-macbeth-gayne-i-not-of-?d=univia.unicajabanco.es'
        cookie = get_cookie(None)
        client.cookies.update({
            'reese84': cookie
        })
        resp_3 = await client.post(post_url, data=req_login_params)



if __name__ == "__main__":
    trio.run(main)
