import json
import random
import warnings
import httpx
import trio
from bs4 import BeautifulSoup
from fingerprints import *
from generate_solution import generate_solution
from headers import Headers
from parse_script import parse_script

warnings.filterwarnings("ignore", module='bs4')

enable_logs = True

proxy_str = 'http://o2renV5yRmwxC9p_c_ES_s_{}:RNW78Fm5@residential.pingproxies.com:10754'
proxy_str = proxy_str.format(random.randint(1000, 10000))
proxies = {
    "http://": proxy_str,
    "https://": proxy_str,
}

# You can find possible values for web_gl.vendor & web_gl.renderer in resources/gpu.json
# Possible canvas & web_gl.preset are found in README.md

# Linux example
# fingerprint = Fingerprint(
#     is_linux=True,
#     navigator=Navigator(
#         user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
#         brands_header='"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
#         hardware_concurrency=24,
#         device_memory=8,
#         languages_navigator=['en-US', 'en'],
#         languages_header='en-US,en;q=0.9',
#     ),
#     screen=Screen(3840, 2160),
#     canvas='linux_001',
#     web_gl=WebGl(
#         vendor='Google Inc. (NVIDIA Corporation)',
#         renderer='ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5.0)',
#         preset='linux_nvidia_001',
#     ),
# )

# Windows example
fingerprint = Fingerprint(
    is_linux=False,
    navigator=Navigator(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        brands_header='"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        hardware_concurrency=8,
        device_memory=8,
        languages_navigator=['en-US', 'en'],
        languages_header='en-US,en;q=0.9',
    ),
    screen=Screen(2560, 1440),
    canvas='windows_002',
    web_gl=WebGl(
        vendor='Google Inc. (NVIDIA)',
        renderer='ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)',
        preset='windows_nvidia_001',
    ),
)


async def main():
    async with httpx.AsyncClient(
        follow_redirects=True,
        base_url='https://univia.unicajabanco.es',
        proxies=proxies,
    ) as client:
        headers_helper = Headers(
            user_agent=fingerprint.navigator.user_agent,
            languages=fingerprint.navigator.languages_header,
            brands=fingerprint.navigator.brands_header,
            platform=fingerprint.platform_header,
        )

        # GET /login
        enable_logs and print('GET /login')
        client.headers.clear()
        client.headers.update(headers_helper.document_get(referer=None))
        response = await client.get('/login')
        html = response.content.decode(encoding='utf-8')

        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        script_src = soup.head.select('script')[-1]['src']
        enable_logs and print('Parsed script_src:', script_src)
        enable_logs and print()

        # GET /script_src
        enable_logs and print('GET', script_src)

        client.headers.clear()
        client.headers.update(headers_helper.script_get(referer='https://univia.unicajabanco.es/login'))
        response = await client.get(script_src)
        js = response.content.decode(encoding='utf-8')

        # Parse JS
        parse_result = parse_script(js)
        enable_logs and print('Parsed script, global vars:', parse_result.global_variables, ', aih:', parse_result.aih)
        enable_logs and print()

        # Get /favicon.ico
        enable_logs and print('GET /favicon.ico')
        client.headers.clear()
        client.headers.update(headers_helper.image_get(referer='https://univia.unicajabanco.es/login'))
        await client.get('/favicon.ico')

        enable_logs and print('Cookies after GET /favicon.ico', client.cookies)
        enable_logs and print()

        # Generate solution.interrogation
        enable_logs and print('Generating interrogation')
        interrogation = generate_solution(
            script_src='https://univia.unicajabanco.es' + script_src,
            aih=parse_result.aih,
            history_len=1,
            global_variables=parse_result.global_variables,
            html=html,
            script_code=parse_result.fp_script,
            fingerprint=fingerprint,
            cwd='./solution_001',
        )

        # Create POST payload
        post_payload = {
            'solution': {
                'interrogation': interrogation,
                'version': 'beta',
            },
            'old_token': None,
            'error': None,
            'performance': {
                'interrogation': random.randint(750, 950)
            }
        }

        # POST /script_src?d=host
        post_url = script_src + '?d=' + 'univia.unicajabanco.es'
        enable_logs and print('POST', post_url)
        enable_logs and print('POST payload', post_payload)

        client.headers.clear()
        client.headers.update(headers_helper.xhr_post(
            referer='https://univia.unicajabanco.es/login',
            accept='application/json; charset=utf-8',
            origin='https://univia.unicajabanco.es',
        ))
        response = await client.post(post_url, json=post_payload)
        content = response.content.decode('utf-8')
        enable_logs and print('Status code:', response.status_code)
        enable_logs and print('Content:', content)

        if response.status_code == httpx.codes.OK:
            response_json = response.json()

            cookie = response_json['token']
            renew_in_sec = response_json['renewInSec']

            enable_logs and print('Parsed token:', cookie)
            enable_logs and print('Parsed renewInSec:', renew_in_sec)
        else:
            response.raise_for_status()

        client.cookies.update({'reese84': cookie})
        enable_logs and print()

        # GET /login
        enable_logs and print('GET /login')
        client.headers.clear()
        client.headers.update(headers_helper.document_get(referer='https://univia.unicajabanco.es/login'))
        response = await client.get('/login')
        html = response.content.decode(encoding='utf-8')
        enable_logs and print('Status code:', response.status_code)
        enable_logs and print('HTML:', html)


if __name__ == "__main__":
    trio.run(main)