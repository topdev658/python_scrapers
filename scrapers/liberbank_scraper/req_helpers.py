from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

from deprecated import deprecated

from custom_libs import extract
from custom_libs.myrequests import Response
from project.custom_types import AccountParsed
from . import parse_helpers


def receipt_extra_req_params_from_pre_receipt(resp_text: str) -> Dict[str, str]:
    """Parses
            var contador = 0;
        var documentos = new Array();
        documentos[contador] = new Object();
        documentos[contador].cuenta = '20482178763400008898';
        documentos[contador].fecha = '05-11-2020';
        documentos[contador].desderegistro = '3671752';
        documentos[contador].hastaregistro = '3671752';
        documentos[contador].formatoinicial = '0021';
    """
    req_params = {
        'FECHA': extract.re_first_or_blank(r"documentos\[contador\].fecha = '(.*?)';", resp_text),
        'CUENTA': extract.re_first_or_blank(r"documentos\[contador\].cuenta = '(.*?)';", resp_text),
        'DESDE_REGISTRO': extract.re_first_or_blank(
            r"documentos\[contador\].desderegistro = '(.*?)';",
            resp_text
        ),
        'HASTA_REGISTRO': extract.re_first_or_blank(
            r"documentos\[contador\].hastaregistro = '(.*?)';",
            resp_text
        ),
        'FORMATO_INICIAL': extract.re_first_or_blank(
            r"documentos\[contador\].formatoinicial = '(.*?)';",
            resp_text
        ),
    }
    return req_params


def req_params_movs_debit_account(
        account_parsed: AccountParsed,
        date_from_str: str,
        date_to_str: str,
        caja_param: str,
        camino_param: str,
        resp_accs: Response,
        llamada_param_extern: Optional[str]) -> Tuple[str, Dict[str, str]]:
    """:returns (req_url, req_params)"""

    client_param = extract.re_first_or_blank(
        r'CLIENTE=(\d+)',
        resp_accs.text
    )

    # overwrite on retry
    if llamada_param_extern:
        llamada_param = llamada_param_extern
    else:
        llamada_param = parse_helpers.get_llamada_param(resp_accs.text)

    req_url_raw = extract.re_first_or_blank(
        'document.ClienteEnviaMovimientos.action="(.*?_d_CTAMOV.*?)"',
        resp_accs.text
    )

    operac_param = extract.re_first_or_blank(
        r'not(\d+)_d_CTAMOV.action',
        req_url_raw
    )

    req_url = urljoin(resp_accs.url, req_url_raw)

    iban = account_parsed['account_no']

    req_params_debit = {
        'LLAMADA': llamada_param,
        'CLIENTE': client_param,
        'IDIOMA': '01',
        'CAJA': caja_param,  # 2048
        'OPERAC': operac_param,
        'CTASEL': '',
        'CTAFOR': '',
        'ayuda': operac_param,  # 9692
        'tituloope': 'Consulta de movimientos',
        'CAMINO': camino_param,  # 5485 / W066
        'OPERACION': '',
        'OPERACREAL': operac_param,
        'FECINI': date_from_str.replace('/', ''),  # '01012017',
        'FECFIN': date_to_str.replace('/', ''),  # '02042017'
        'MONEDA': '',
        'FINI': date_from_str.replace('/', '-'),  # '01-03-2017',
        'FFIN': date_to_str.replace('/', '-'),  # '02-04-2017',
        'ULTIMOS': '',
        'CODREANUD': '',
        'GCUENTA': account_parsed['numcta'][4:],  # '0103610000103400000832',
        'DATOS': '',
        'SALDOS': account_parsed['balance_str'],  # '20.582,46'
        # '2048 0361 10 3400000832',
        'CUENTA': '{} {} {} {}'.format(iban[4:8], iban[8:12], iban[12:14], iban[14:]),
        'titulooperatoria': '',
        'select_fecha_desde': date_from_str.replace('/', '-'),  # '01-01-2017,
        'select_fecha_hasta': date_to_str.replace('/', '-'),  # '01-04-2017'
    }

    return req_url, req_params_debit


@deprecated
def req_params_movs_excel(
        resp_acc: Response,
        account_parsed: AccountParsed,
        date_from_str: str,
        date_to_str: str,
        llamada_param: Optional[str]) -> Tuple[str, Dict[str, str]]:
    """:returns (req_url, req_params)"""

    # Patch for form_html from extract.build_req_params_from_form_html
    # It uses unstrict regexp, can't modify to be sure that don't affect other scrapers
    form_name = 'ClienteR'
    form_html = extract.re_first_or_blank(
        r'(?si)<form[^>]*?name\s*=\s*"{}".*?</form>'.format(form_name),
        resp_acc.text
    )

    req_link, req_params_excel = extract.build_req_params_from_form_html_patched(form_html, 'ClienteR')

    # Hardfix for liberbank:
    # it detects no-js and uses W066 suburl than 5485, which uses for webbrowsers
    # but W066 doesn't have movements download endpoint
    req_link = req_link.replace('W066', '5485')
    req_excel_url = urljoin(resp_acc.url, req_link)

    req_params_excel.update({
        'FECINI': date_from_str.replace('/', ''),  # '01012017',
        'FECFIN': date_to_str.replace('/', ''),  # '02042017'
        'GCUENTA': account_parsed['numcta'],  # '0103610000103400000832',
        'CONFECHAS': 'NO'
    })

    # overwrite when necessary on retries
    if llamada_param:
        req_params_excel['LLAMADA'] = llamada_param

    return req_excel_url, req_params_excel
