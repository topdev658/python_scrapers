"""
Access-specific environments to emulate
scraping from the 'confirmed' web browser.
Usually, it requires SMS confirmation and cannot be obtained
without extra customer-provided efforts.

Add once here the necessary environments for every access after the SMS confirmation.
"""

from typing import Dict

from scrapers.banco_caminos_scraper.environs import Env

# {access_id_int: env}
ENVS = {
    26906: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='a4b067b8-18c0-4794-a3cf-0fdebf088315'
    ),
    4901: Env(
        user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
        device_id='048cac22-7149-4042-91b3-1f25157f0428'
    ),
    10508: Env(
        user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
        device_id='048cac22-7149-4042-91b3-1f25157f0428'
    ),
    33501: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='a4b067b8-18c0-4794-a3cf-0fdebf088315'
    ),
    35436: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='9cec6c25-44b3-4a57-a8a7-338645fbfb72'
    ),
    20121: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='548982a5-a5ba-4319-aa03-5229ee7c9747'
    ),
    35305: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='9cec6c25-44b3-4a57-a8a7-338645fbfb72'
    ),
    40980: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='9cec6c25-44b3-4a57-a8a7-338645fbfb72'
    ),


}  # type: Dict[int, Env]
