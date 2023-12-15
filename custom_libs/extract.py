import html
import re
import urllib.parse
from collections import OrderedDict
from typing import Any, Dict, Tuple, Optional

from custom_libs import convert

__version__ = '1.27.0'

__changelog__ = """
1.27.0
unescape_html_from_json: more cases
1.26.0
unescape_html_from_json
1.25.0
replace_quote_with_blank_for_db 
1.24.0
unescape non-ASCII hyphen
1.23.0
custom splitquery
1.22.2
added todo
1.21.1
build_req_params_from_form_html_patched: handle spaces around '='
1.21.0
build_req_params_from_form_html_patched: handle names with '@#' (cajamar)
1.20.0
eval_xls_formula_safely: more cases
1.19.1
upd type hints
1.19.0
get_link_contains_text
1.18.0
form_param
re_last_or_blank
1.17.0
build_req_params_from_form_html_patched: form_re param
1.16.0
remove_extra_spaces
1.15.0
req_params_as_ord_dict: supports full url or only req params
1.14.0
req_params_as_ord_dict (dev helper)
1.13.0
text_wo_scripts_and_tags: remove escaped r
all regexps: raw strings
by_index_or_blank, by_index_or_none: renamed param
1.12.0
text_wo_scripts_and_tags: + w/o styles
1.11.0
text_wo_scripts_and_tags
1.10.3
build_req_params_from_form_html_patched: fields_tuples_with_values: added \s* around =
1.10.2
type hints upd
exc msg upd
1.10.1
build_req_params_from_form_html_patched: support single quotes for action
1.10.0
build_req_params_from_form_html_patched
1.9.0
by_index_or_none
1.8.0
eval_xls_formula_safely more cases
1.7.0
build_req_params_from_form_html 
    add symbols :._ in name params 
    is_ordered option
1.6.1
get_link_by_text return blank if not found
1.6.0
get_link_by_text generic approach to handle all cases
1.5.0
get_link_by_text new case
1.4.3
raise Exc class
1.4.2
raise (exc.__str__() + ': ' + formula_cleaned_correct)
1.4.1
eval_xls_formula_safely: fix case +000/100
1.4.0
eval_xls_formula_safely handle unhandleble includings: more cases
1.3.0
eval_xls_formula_safely handle unhandleble includings
1.2.0
eval_xls_formula_safely
1.1.0
build_req_params_from_form_html \s* in form name, action
"""


def unescape(text: str) -> str:
    return html.unescape(text).replace('\xa0', ' ').replace('\xad', '-')


def unescape_html_from_json(text: str) -> str:
    """
    >>> unescape_html_from_json(r'Com TRF créd SEPA+ net\\/app\\\\x3e=100.000')
    'Com TRF créd SEPA+ net/app>=100.000'

    # Cajamar
    >>> unescape_html_from_json(r'z_gjY2d0wPC_02IiI\\x2DEHXA9A')
    'z_gjY2d0wPC_02IiI-EHXA9A'
    """
    for s in [r'\\\\', r'\\']:
        hexcodes = re.findall(r'(?i)%sx([0-9a-f]{2})' % s, text)
        for hexcode in hexcodes:
            code_str = bytes.fromhex(hexcode).decode('utf-8')
            text = re.sub(r'(?i)%sx%s' % (s, hexcode), code_str, text)
        text = re.sub(s, '', text)
    return unescape(text)


def escape_quote_for_db(text: str) -> str:
    return text.replace("'", "''")


def replace_quote_with_blank_for_db(text: str) -> str:
    return text.replace("'", " ")


def rex_first_or_blank(rex, text: str) -> str:
    """
    :param rex: regular_expression_compiled
    :param text: text to search in
    """

    results = rex.findall(text)
    if results:
        try:
            return html.unescape(results[0])
        except:
            return results[0]
    return ''


def re_first_or_blank(re_exp: str, text: str) -> str:
    """
    :param re_exp: regular expression string
    :param text: text to search in
    """

    results = re.findall(re_exp, text)
    if results:
        try:
            return html.unescape(results[0])
        except:
            return results[0]
    return ''


def re_last_or_blank(re_exp: str, text: str) -> str:
    """
    :param re_exp: regular expression string
    :param text: text to search in
    """

    results = re.findall(re_exp, text)
    if results:
        try:
            return html.unescape(results[-1])
        except:
            return results[-1]
    return ''


def by_index_or_blank(arr: list, idx: int) -> Any:
    try:
        return arr[idx]
    except IndexError:
        return ''


def by_index_or_none(arr: list, idx: int) -> Any:
    try:
        return arr[idx]
    except IndexError:
        return None


def get_link_by_text(html_str: str, current_url: str, link_text: str) -> str:
    """
    :return: href of link with given text or blank if not found
    """

    link_href = by_index_or_blank(
        [unescape(l[1])
         for l in re.findall(r"""(?si)(<a.*?href\s*=\s*["'](.*?)["'].*?</a>)""", html_str)
         if remove_tags(l[0]) == link_text],
        0
    )

    if not link_href:
        return ''
    link_url = urllib.parse.urljoin(current_url, link_href)
    return link_url


def get_link_contains_text(html_str: str, current_url: str, link_text: str) -> str:
    """
    Not so strict as get_link_by_text
    :return: href of link contains given text or blank if not found

    """

    link_href = by_index_or_blank(
        [unescape(l[1])
         for l in re.findall(r"""(?si)(<a.*?href\s*=\s*["'](.*?)["'].*?</a>)""", html_str)
         if link_text in remove_tags(l[0])],  # less strict
        0
    )

    if not link_href:
        return ''
    link_url = urllib.parse.urljoin(current_url, link_href)
    return link_url


def remove_tags(html_text: str) -> str:
    if not html_text:
        return html_text
    wo_comments = re.sub('(?si)<!--.*?-->', '', html_text).strip()
    wo_tags = re.sub('(?si)<.*?>', '', wo_comments).strip()
    return unescape(wo_tags).strip()


def build_req_params_from_form_html(html_str: str,
                                    form_name: str = '',
                                    form_id: str = '',
                                    is_ordered=False) -> Tuple[str, Dict[str, str]]:
    """
    <input type="hidden" name="PRF_CODE" value="[ST]9PNQ0KDOiR4dR3TLwWRopA==">
    """

    form_html = ''
    if form_name:

        form_html = re_first_or_blank(
            r'(?si)<form.*?name\s*=\s*"{}".*?</form>'.format(form_name),
            html_str
        )

    else:
        form_html = re_first_or_blank(
            r'(?si)<form.*?id\s*=\s*"{}".*?</form>'.format(form_id),
            html_str
        )

    action_url = re_first_or_blank(r'(?si)action\s*=\s*"(.*?)"', form_html)

    # [(name, value), ...]
    fields_tuples_with_values = re.findall(
        """(?si)<input.*?name=["']?([a-zA-Z0-9:._]*)['"]?[^>]*value=["'](.*?)['"]""",
        form_html
    )

    fields_tuples_wo_values = re.findall(
        r"""(?si)<input.*?name=["']?([a-zA-Z0-9:._]*)['"]?\s*()[/]?>""",
        form_html
    )

    fields_tuples = []  # type: list
    fields_tuples += fields_tuples_with_values
    fields_tuples += fields_tuples_wo_values

    if not is_ordered:
        # for 100% compatibility
        req_params = {name: value for name, value in fields_tuples}
    else:
        req_params = OrderedDict([(name, value) for name, value in fields_tuples])

    return action_url, req_params


# Extracts form_html correctly when the necessary form places after
# any previous form on the page
# Saved as additional func to avoid probable bugs for already
# implemented fin entities
def build_req_params_from_form_html_patched(html_str: str,
                                            form_name: str = '',
                                            form_id: str = '',
                                            is_ordered=False,
                                            form_re='') -> Tuple[str, Dict[str, str]]:
    """
    <input type="hidden" name="PRF_CODE" value="[ST]9PNQ0KDOiR4dR3TLwWRopA==">
    """

    form_html = ''
    if form_re:
        form_html = re_first_or_blank(
            form_re,
            html_str
        )
    else:
        if form_name:

            form_html = re_first_or_blank(
                r'(?si)<form[^>]*name\s*=\s*"{}".*?</form>'.format(form_name),
                html_str
            )

        else:
            form_html = re_first_or_blank(
                r'(?si)<form[^>]*id\s*=\s*"{}".*?</form>'.format(form_id),
                html_str
            )

    action_url = re_first_or_blank(r"""(?si)action\s*=\s*["'](.*?)["']""", form_html)

    # [(name, value), ...]
    fields_tuples_with_values = re.findall(
        r"""(?si)<input.*?name\s*=\s*["']?([@#a-zA-Z0-9:._]*)['"]?[^>]*value\s*=\s*["'](.*?)['"]""",
        form_html
    )

    fields_tuples_wo_values = re.findall(
        r"""(?si)<input.*?name\s*=\s*["']?([a-zA-Z0-9:._]*)['"]?\s*()[/]?>""",
        form_html
    )

    fields_tuples = []  # type: list
    fields_tuples += fields_tuples_with_values
    fields_tuples += fields_tuples_wo_values

    if not is_ordered:
        # for 100% compatibility
        req_params = {name: value for name, value in fields_tuples}
    else:
        req_params = OrderedDict([(name, value) for name, value in fields_tuples])

    return action_url, req_params


def eval_xls_formula_safely(formula_str: str) -> float:
    """
    >>> eval_xls_formula_safely('+7239,45')
    7239.45

    >>> eval_xls_formula_safely('=+723945/100')
    7239.45

    >>> eval_xls_formula_safely('=-1123538/100')
    -11235.38

    >>> eval_xls_formula_safely('=-047/100')
    -0.47

    >>> eval_xls_formula_safely('=00000047/100')
    0.47

    >>> eval_xls_formula_safely('=+000/100')
    0.0

    >>> eval_xls_formula_safely('=00000000/100')
    0.0

    >>> eval_xls_formula_safely('=485419,2*100/100')
    485419.2

    >>> eval_xls_formula_safely('=-485419,25*100/100')
    -485419.25
    """

    if not formula_str.startswith('='):
        return convert.to_float(formula_str)
    # '=-1123538/100 EUR' -> '-1123538/100
    formula_str = formula_str.replace(',', '.')
    formula_cleaned = re.sub('[^+-/*0-9.]', '', formula_str)

    # handle case '-047/100' -> '-47/100'
    unhandleable_includings = re.findall(r'[+-]0+[1-9.]|^0+\d', formula_cleaned)

    formula_cleaned_correct = formula_cleaned
    for incl in unhandleable_includings:
        replace_incl_with = incl.replace('0', '') or '0'
        formula_cleaned_correct = formula_cleaned_correct.replace(incl, replace_incl_with)

    try:
        res = eval(formula_cleaned_correct)
    except Exception as exc:
        raise Exception('{}: {}'.format(exc, formula_cleaned_correct))
    return res


def text_wo_scripts_and_tags(resp_text: str) -> str:
    return re.sub(
        r'[ \t]+', ' ',
        re.sub(
            r'\n\n\s*', r'\n\n',
            re.sub(r'\r', '',
                   remove_tags(
                       re.sub(
                           '(?si)<script.*?</script>', '',
                           re.sub(
                               '(?si)<style.*?</style>', '',
                               re.sub('<!--.*?-->', '', resp_text)
                           )
                       )
                   )
            )
        )
    )


# Copied deprecated from urllib.parse
def splitquery(url: str) -> Tuple[str, Optional[str]]:
    """splitquery('/path?query') --> '/path', 'query'."""
    path, delim, query = url.rpartition('?')
    if delim:
        return path, query
    return url, None


def req_params_as_ord_dict(url_or_req_params: str) -> OrderedDict:
    """Parses full url or only encoded req parameters to ordered dict"""
    split_tpl = splitquery(url_or_req_params)
    # handle full url with params or req params only
    req_params = split_tpl[1] if split_tpl[1] is not None else split_tpl[0]
    return OrderedDict(urllib.parse.parse_qsl(req_params, True))


def remove_extra_spaces(text: str) -> str:
    """Replaces 1+ space to 1 space"""
    return re.sub(r'\s+', ' ', text).strip()


def form_param(form_html: str, param_name='', param_id='') -> str:
    """Extracts form param from HTLM by its name or id"""
    by = 'name' if param_name else 'id'

    val = re_first_or_blank(
        r"""(?si)<input[^>]+{}=["']{}['"][^>]+value\s*=\s*["'](.*?)['"]""".format(
            by,
            param_name or param_id),
        form_html
    )
    return val

