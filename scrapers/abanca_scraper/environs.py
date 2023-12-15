"""
GoAbanca (don't mess with Abanca) access-specific confirmed environments
to emulate scraping from those envs (cookies, user agent).
Usually, these environments require SMS confirmation and cannot be obtained
without extra customer-provided efforts.

Add once here the necessary data for every access after the SMS confirmation.
"""

from typing import Dict, NamedTuple

Env = NamedTuple('Env', [
    ('headers', Dict[str, str]),
    ('cookies', Dict[str, str])
])

# {access_id_int: Env(headers={header_name: header_val}, cookies={cookie_name: cookie_val})}
ENVS = {
    28167: Env(
        headers={
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
        },
        cookies={
            'TS01463095': '01301e525bb726af8d8b8ebf940685a599ddf990c3d46ecfcd9160a286470403f8fc62a1971c8b63ac9d8eb222d01e73aa4fca8fd3',
        }
    ),
    26914: Env(
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        },
        cookies={
            'TS01463095': '01301e525ba4f032f14960de1891f237968f36f596f25a28a73e43421edb48f5bb52659858e45acef195046471e893faa54bcc67ca',
        }
    ),
    30929: Env(
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
        },
        cookies={
            'TS01463095': '01301e525be870a39d4d31857d99cb55a624ac7835de794cd4a694a71f6dd5c4d25786c81dc3be75a47af3a6dee3bb2a805063735d',
        }
    ),
    3824: Env(
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
        },
        cookies={
            'TS01463095': '01301e525be870a39d4d31857d99cb55a624ac7835de794cd4a694a71f6dd5c4d25786c81dc3be75a47af3a6dee3bb2a805063735d',
        }
    ),
    28208: Env(
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        },
        cookies={
            'TS01463095': '01301e525baeb5e215b49982e6473e6950047bd3f629b75592d68f383f90c871582028a62c9c1272a8795d43a0bb565b681eb4eff5',
        }
    ),
}  # type: Dict[int, Env]


ENV_DEFAULT = Env(
    headers={
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
    },
    cookies={
        'TS01463095': '01301e525bb726af8d8b8ebf940685a599ddf990c3d46ecfcd9160a286470403f8fc62a1971c8b63ac9d8eb222d01e73aa4fca8fd3',
    }
)
