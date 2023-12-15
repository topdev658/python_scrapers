import re
from custom_libs import extract
from typing import List


def get_urls_of_login_js_scripts(resp_text: str) -> List[str]:
    """Parses init page.
    Searches for
    ["https://www1.bac-assets.com/homepage/spa-assets/bundles/592d8802.js",
    "https://www1.bac-assets.com/homepage/spa-assets/bundles/4d86e198.js"]"""
    urls = re.findall('"(https://www1.bac-assets.com/homepage/spa-assets/bundles.[^.]+[.]js)"', resp_text)
    # cc.go is a js script too, but with 'broken' extension
    urls.append('https://secure.bankofamerica.com/login/sign-in/entry/cc.go')
    return urls


def get_vals_from_js_texts(js_texts: List[str]) -> dict:
    sid = ''
    tid = ''
    cf_flags_param = ''
    t_param = ''
    for js_text in js_texts:

        # expect from https://www1.bac-assets.com/homepage/spa-assets/bundles/4d86e198.js
        # for "sid":"933928f25519a10e","tid":"5678"
        if not sid:
            sid_tid = extract.re_first_or_blank(
                r"""(?si)_cc.push\(\['ci',\s*\{\s*sid:\s*'(.*?)',\s*tid:\s*'(\d+)'""",
                js_text
            )
            if sid_tid:
                sid = sid_tid[0]
                tid = sid_tid[1]
                continue

        # expect from https://www1.bac-assets.com/homepage/spa-assets/bundles/592d8802.js
        # for "cf_flags":155687923
        if not cf_flags_param:
            cf_flags_param = extract.re_first_or_blank(r'flagsToCollect:(\d+)', js_text)
            if cf_flags_param:
                continue

        # expect from https://secure.bankofamerica.com/login/sign-in/entry/cc.go for
        # "_t":"NDY4MDg1MjMtMTk4Zi00MTkxLTkyZDctYmEzM2FiZDE2MTFkOjE1NTEwMzgxOTg3OTM"
        if not t_param:
            t_param = extract.re_first_or_blank(r'Fb={run:function\(a\){B=a;K="(.*?)"', js_text)

    js_vals = {
        'sid': sid,
        'tid': tid,
        'cf_flags': cf_flags_param,
        't': t_param
    }

    return js_vals
