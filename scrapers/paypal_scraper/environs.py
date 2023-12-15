"""
Access-specific cookies to emulate
scraping from the 'confirmed' environment (web browser).
Usually, these cookies require SMS confirmation and cannot be obtained
without extra customer-provided efforts.

Add once here the necessary cookies for every access after the SMS confirmation.
"""

from typing import Dict, NamedTuple

__version__ = '2.1.0'
__changelog__ = """
2.1.0
Env as struct to pass mypy
removed ENV_DEFAULT (no further usage)
2.0.0
Env as dict
more confirmed
merge 2fa and captcha cookies
1.0.0
Env as struct
"""

Env = NamedTuple('Env', [
    ('user_agent', str),
    ('cookies', Dict[str, str])
])


def updated(base: dict, upd_with: dict) -> dict:
    base.update(upd_with)
    return base


# {access_id_int: Env(user_agent=user_agent_str, cookies={cookie_name: cookie_val})}
ENVS = {
    31902: Env(
        user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0',
        cookies={
            # 2FA
            'd_id': '0b369c1aa3b5494d9ad305232bb463831645178224535',
            'KHcl0EuY7AKSMgfvHl7J5E7hPtK': 'iMFktAEWqZ2O9mJKfU2sQqymfthSwhzlMAiWS0FqwrMqReqHs08_AZSdnT4IbqR0qh-4ID89tmaDYLB7',
            'rmuc': 'OljotwRN1EQjpXFBWrJjaUf364_ZWZp5ep-u-xyK9Jq0kh9JKfSh53rKVqsvMrUEIVth1Nbb1ptadLxbssTzYJh3zhDF9LxeNKh4aogj47j2DxzJ3cZ7LyY1MdSBPsPtyifzdnrHpCztLwF3jz1OvMLSAM4A1VasMAxjke_HHtgeDwzZYppvTjRieX0yIi39qV8qSfDY3PylbVL8PFmkOm6l_VcEUCqMAtkRlss_QGHcLtgV',
            # CAPTCHA
            'X-PP-ADS':	'AToBqHAPYhZ2U9pgQH8BcSLNs1fBEFI',
            'x-pp-s': 'eyJ0IjoiMTY0NTE3OTA4ODkzNSIsImwiOiIxIiwibSI6IjAifQ',
            'SEGM': 'bRdV1vB0ebq9RKdAb3xSHowCi6QnnlCiDOLNk8i1mAuLl1vTbzHQwWajSsMe8mvoWiJtY1GnpzN4Y-sixGy7BQ',
            'TfXMWj95u2_Zf1Kmv_GCUOjlGG8': 'roWkxhk-W9H4eztQth3DEsQ7x_PhNVdO2IGAae6n2XZ3jJj8KSi8zczrlf-DJRhdM1LTs0h8tfVcYs6zDpKeXmvqdNx6fhBpjnIFd3SpN8xYVksoGm8B_RiIv9hPpdOMBzPo3jhC-ap_y5RhRaOGW89U07kNpuo5W3G6z-cFviGekgl8ckvmJRTozAp4suGA2Y7oWG',
            'AV894Kt2TSumQQrJwe-8mzmyREO': '',
            'DPz73K5mY4nlBaZpzRkjI3ZzAY3QMmrP': '',
        }
    ),

    32814: Env(
        user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
        cookies={
            # 2FA
            'd_id': 'e914945d622e4b08bf7187946d8903661639478886295',
            'KHcl0EuY7AKSMgfvHl7J5E7hPtK': '6kExjSOpe_EWmGyFBb388OeoK7VHsBh579gFhLLyp1OynSEmXlfhW2B5qwOimRJPTQIXXAlT-wJU9yaA',
            'rmuc': 'St2DWclLgvV06xn3QghOM79twI7vFm2h66cYuo-RYJ2PLVo4nW5BuH0-1Sj8HEPfkZVXTzNPFGSrrYITSEBTU37aGHG4OodBA-uBCdbtlAO9BbRC8TSr1-SPFH6HhoYjw3Mf_wBOMVdbcloVbn5f6EitK3LfpPqDtgZBy2lJjWMitWIvZUIKcm1ssjTPaphrUAygTr7o-NXk8eAyxp48KPWxZxIrLya79W-UoyP6VoiRdjUkcLFwSY1bESO',
            # CAPTCHA
            'x-cdn': '0110',
            'X-PP-ADS':	'AToBCTm5YfrcF8KSRR1ya2d64WiSUNo',
            'x-pp-s': 'eyJ0IjoiMTYzNTAwNDUwMTI2OSIsImwiOiIwIiwibSI6IjAifQ',
            'SEGM': 'bRdV1vB0ebq9RKdAb3xSHowCi6QnnlCiDOLNk8i1mAuLl1vTbzHQwWajSsMe8mvoWiJtY1GnpzN4Y-sixGy7BQ',
            'TfXMWj95u2_Zf1Kmv_GCUOjlGG8': 'ihuy6C5oXtE5JhbfRiYJkrOkq74MkRz1H9HU-aylJ7jkBVl_TNxE_xPnsAZ7u7dD7OO2tJFSeEIG8u6bVFADwrLQcWWM_1Af1HtvzbLCivA4icu6uFNo_OmWlobqWtIrTehhcLhPjAa5Ihko2evYKUMuPxCoGMmtQCKUDjMCjj9EWmEyVpzst0p-fqdliv-rmjvA3AgGwa5NlPku',
            'AV894Kt2TSumQQrJwe-8mzmyREO': '',
            'DPz73K5mY4nlBaZpzRkjI3ZzAY3QMmrP': '',
        }
    ),

    32815: Env(
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        cookies={
            # 2FA
            'd_id': 'e1a2219165a8402cb54060f873ee53661640772133212',
            'KHcl0EuY7AKSMgfvHl7J5E7hPtK': 'fv31QVOTgvtHs03vIxUGsll-xV0yja9uT3o0gUV5wT9iEiqNo0OkOaJj5pLYrnso_m9ozobLD6WWD6B6',
            'rmuc': 'S4DETqnBsPg1fNxUdq7ndP_vZ9X71ioyJYXt7Tc8mLcAzpGNVLbLC3oR1mzm6s_bQmIMarxlZg2XWK1gGpjU-JCSBoVBdwCpB82urlpH8e_fI2cAb34BRg_-8VS6sOYZOPoYqnsd_ZpqAUo82iIJcbtjsMKQWdTO-uWG1_tk_JXTOQ5yErwtfxD_T2p-WVlgmXe2CXObWU7rFq1Va3_x8w1IsZNnX2_dNrpUsm',
            # CAPTCHA
            'x-cdn': '0133',
            'X-PP-ADS':	'AToBLDPMYbu1LuC.5dxge7HtjKYlP.E',
            'x-pp-s': 'eyJ0IjoiMTY0MDc3MjQ2MzYzOCIsImwiOiIxIiwibSI6IjAifQ',
            'SEGM': 'bRdV1vB0ebq9RKdAb3xSHowCi6QnnlCiDOLNk8i1mAuLl1vTbzHQwWajSsMe8mvoWiJtY1GnpzN4Y-sixGy7BQ',
            'TfXMWj95u2_Zf1Kmv_GCUOjlGG8': 'EBOJ2tsTyKxYHeqZ1kLiuXoEnuEhMu1ClCpT7zIUA4wpPv7V55jGKYLUZGHG3x9oddNwEMJ9_712iBjCbThP1VHk9k0oevdu1ZhnS8i4Img4EZzMXpl8QE5O9XveoDWJTom2pdOkYqNOpndRk0JIbm2mpoojk8dHRQJAUYZb-pclhs32mWecJIql5qO',
            'AV894Kt2TSumQQrJwe-8mzmyREO': '',
            'DPz73K5mY4nlBaZpzRkjI3ZzAY3QMmrP': '',
        }
    )

}  # type: Dict[int, Env]
