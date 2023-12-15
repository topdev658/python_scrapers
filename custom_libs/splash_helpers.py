import base64
from typing import List, Dict, Tuple
from project.custom_types import Cookie
import re

__version__ = '1.0.0'
__changelog__ = """
1.0.0
init
"""

def get_cookies_from_har(har_json: dict) -> List[Cookie]:
    # See eurobic_scraper/dev_new/resp_home_har.json
    # Cookie can override the cookie with the same name
    # from the previous response, thus,
    # need to check for uniqueness by name
    cookies_dict = {}  # type: Dict[str, Cookie]
    # 'entries' are responses in order of appearance
    for entry in har_json['log']['entries']:
        #  {
        #       "name": "visid_incap_2023984",
        #       "value": "Cdgi5lLQSuu0DaqFjFjrY4y9n2EAAAAAQUIPAAAAAABs4vL0PWil5/MC43q4jD2d",
        #       "path": "/",
        #       "domain": ".eurobic.pt",
        #       "expires": "2022-11-24T17:17:09Z",
        #       "httpOnly": true,
        #       "secure": true
        #  }
        cookies = entry['response']['cookies']
        for cookie in cookies:
            cookies_dict[cookie['name']] = Cookie(
                name=cookie['name'],
                value=cookie['value'],
                domain=cookie['domain'],
                path=cookie['path']
            )

    return list(cookies_dict.values())


def get_response_text_from_har(har_json: dict, resp_url_re: str) -> Tuple[bool, str]:
    resp_text = ''
    found = False
    # Save the resp of the last matched url
    for entry in har_json['log']['entries']:
        url = entry['response']['url']
        if re.match(resp_url_re, url):
            resp_b64 = entry['response']['content'].get('text', '')
            if resp_b64:
                resp_text = str(base64.b64decode(resp_b64))
            found = True
    if not found:
        return False, ''
    return True, resp_text
