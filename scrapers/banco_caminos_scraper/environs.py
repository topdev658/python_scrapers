"""
Access-specific environments to emulate
scraping from the 'confirmed' web browser.
Usually, it requires SMS confirmation and cannot be obtained
without extra customer-provided efforts.

Add once here the necessary environments for every access after the SMS confirmation.
"""

from typing import Dict, NamedTuple


UA_DEFAULT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'

Env = NamedTuple('Env', [
    ('user_agent', str),
    ('device_id', str)  # from LocalStorage->deviceId
])

# {access_id_int: env}
ENVS = {
    32701: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='df909e46-9f10-4ede-9d3e-52f7d090cc41'
    ),
    30621: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='0dad520e-100b-4aea-9db5-712a050eadc3'
    ),
    20813: Env(
        user_agent='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        device_id='df909e46-9f10-4ede-9d3e-52f7d090cc41'
    ),
}  # type: Dict[int, Env]

# No device_id - can't log in
ENV_DEFAULT = Env(
    user_agent=UA_DEFAULT,
    device_id=''
)
