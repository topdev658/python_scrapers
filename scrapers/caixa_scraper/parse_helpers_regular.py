import html
import re
import traceback
import unittest
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs

from custom_libs import convert
from custom_libs import date_funcs
from custom_libs import extract
from custom_libs.myrequests import Response
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed,
    MovementParsed, CorrespondenceDocParsed
)
from .custom_types import Company

__version__ = '1.8.0'
__changelog__ = """
1.8.0
get_companies_new: upd layout (dev_regular_202206)
1.7.0
get_companies_new: upd layout
1.6.1
renamed vars to pass mypy
1.6.0
build_next_page_w_companies_req_params
1.5.1
removed err report
1.5.0
get_companies_new (-a 4039 since 10/2021)
1.4.0
get_number_of_correspondence_documents: 
  handle case when the website displays 'total 0' docs while there are some docs ('1-7 of 0', -a 27006)
1.3.0
_parse_date_str
1.2.0
get_corespondence_from_list: different parsing if exists tablacorresp or tablaComunicadosNew
added get_corespondence_from_list_tabla_comunicados_new
get_account_iban_for_correspondence_document: different parsing if exists tablacorresp or tablaComunicado
get_number_of_correspondence_documents: different parsing if exists tablacorresp or tablaComunicado
get_docs_next_page_refval_param: different parsing if exists tablacorresp or tablaComunicado
1.1.0
parse_helpers_regular: handle account alias like 'GESTORES RED' (contains 'ES ') 
  to avoid false-positive IBAN detection
"""

MOV_EXTENDED_DESCRIPTION_FIELDS = [
    'Concepto',
    'Concepto específico',
    'Remitente',
    'Otras caracteristicas',
    'Concepto informado por el ordenante',
    'Codigo identificacion del ordenante',
    'Concepto transferencia'
]

FOREIGN_CURRENCIES = {
    'ZLOTY POLACO': 'PLN',
    'DÓLAR USA': 'USD',
    'LIBRA ESTERLINA': 'GBP',
    'EUROS': 'EUR',  # also can be in a foreign currency place (-a 22952)
}


def lower_letters(text: str) -> str:
    return ''.join(re.findall(r'\w', text)).lower()


def get_available_company_titles(resp_text: str) -> List[str]:
    """All available company titles from the home page"""

    # -a 29806, company title is parsed from 'Cambiar usuario':'N16 PLUS'
    # But &NOMBRE='NUMBER 16 PLUS SL'

    # <div id="nombreParticular" style="display: block;" class="profile-name">N16 PLUS</div>
    #
    # <div id="nombreEmpresa" style="display: none;" class="profile-name" title ="">
    # N16 PLUS
    # <div class="small">NUMBER 16 PLUS SL</div>  <-- NOMBRE
    # </div>
    title1 = extract.re_first_or_blank('(?si)<div id="nombreParticular"[^>]*>(.*?)</', resp_text).strip()
    title2 = extract.re_first_or_blank('(?si)<div id="nombreEmpresa"[^>]*>(.*?)<div', resp_text).strip()
    title3 = extract.re_first_or_blank('(?si)<div id="nombreEmpresa"[^>]*>.*?<div class="small">(.*?)</',
                                       resp_text).strip()
    title4 = extract.re_first_or_blank(r'(?si)"&NOMBRE=" \+ "(.*?)"', resp_text)
    # from frame name="Inferior" (after login with forced redirection)
    title5 = extract.re_first_or_blank('top[.]nomUser="(.*?)";', resp_text)
    return [title1, title2, title3, title4, title5]


# Note, use get_available_company_titles for validation, this one for
# further processing
def get_company_title(resp_text: str) -> str:
    common = extract.re_first_or_blank(r'(?si)"&NOMBRE=" \+ "(.*?)"', resp_text)
    # from frame name="Inferior" (after login with forced redirection)
    alternate = extract.re_first_or_blank('top[.]nomUser="(.*?)";', resp_text)
    return common or alternate


def movs_parsed_tuples(movs: List[MovementParsed]) -> List[Tuple[float, float, str, str, str]]:
    """Get only necessary fields to provide correct detection for sublist
    Because same movement_parsed will be with different 'mov_details_req_params
    if extracted from different pages (may happen on hanged loop)"""
    tuples = [(m['amount'], m['temp_balance'], m['operation_date'], m['value_date'], m['description'])
              for m in movs]
    return tuples


def get_subdomain_of_url(url: str) -> str:
    return extract.re_first_or_blank(r'loc\d+', url)


def get_redirection_url(resp_text: str) -> str:
    return extract.re_first_or_blank(r"location.replace\('(.*?)'\);", resp_text)


def get_redirection_login2_req_params(resp_logged_in: Response) -> OrderedDict:
    refval_param_name = extract.re_first_or_blank(
        r'input name="(REFVAL_COMPLEJO_\d+)"',
        resp_logged_in.text
    )
    refval_param_val = extract.re_first_or_blank(
        r'input name="REFVAL_COMPLEJO_\d+" value="(.*?)"',
        resp_logged_in.text
    )
    req_login2_params = OrderedDict([
        (refval_param_name, refval_param_val),
        ('CLICK_ORIG', '')
    ])
    return req_login2_params


def get_main_frame_link_w_websession(resp_text: str) -> str:
    wls = extract.re_first_or_blank(r'title="Inferior"\s+src="(.*?)"', resp_text)
    return wls


def get_companies(logger: ScrapeLogger, resp_text: str) -> List[Company]:
    """
    Parses

    <a href="JavaScript:Inicializar('00300078300','NEGOCIOS DE RESTAURACION DEL SUR S.L.',
    '9725013000783','D0biJ9OLu8gPRuIn04u7yAAAAWsr8KzGD98~OW_UDLc')"
    class="no_subrayado"  title=""
    onClick="this.blur();"><span>NEGOCIOS DE RESTAURACION DEL SUR S.L.</span></a>

    into

    Company(title='NEGOCIOS DE RESTAURACION DEL SUR S.L.',
            request_params=['00300078300', 'NEGOCIOS DE RESTAURACION DEL SUR S.L.',
            '9725013000783', 'D0biJ9OLu8gPRuIn04u7yAAAAWsr8KzGD98~OW_UDLc'])

    Handles punctuation ',()'` in company title

    SEE TESTS BELOW
    """
    companies = []  # type: List[Company]

    companies_raw = re.findall(
        r"""(?si)"JavaScript:Inicializar\((.*?)\)"\s+.*?class[^<]+<span>(.*?)</span>""",
        resp_text
    )
    for params_str, title in companies_raw:
        # ',' allows to handle unexpected quote in params
        # (if there is a quote in organization name)
        params_str += ','
        # FAILED -a 29806
        # ['02036293500', 'N16 PLUS', '9725030362935', 'HBT59xmILmgcFPn3GYguaAAAAXdNPWY5sNlTzclmIb8']
        # OK -a 16556
        # ['00989982901', 'FRANCISCO JAVIER MAURICIO FOCHE', '9725019899829', 'o45BRsBl97WjjkFGwGX3tQAAAXdOPRlP70r5zv_dqmQ']
        params = re.findall(r"'(.*?)',", params_str)

        # Necessary condition to be able to switch to company or will fail
        if len(params) < 4:
            logger.error("Company {}: can't parse req params `{}`. Check the regexp".format(
                title,
                params_str
            ))
        company = Company(
            title=html.unescape(title.strip()),
            request_params=params,
        )
        companies.append(company)
    return companies


def get_companies_new(logger: ScrapeLogger, resp_text: str) -> List[Company]:
    """For some accesses since 10/2021 (-a 4039)"""
    companies = []  # type: List[Company]

    table = extract.re_first_or_blank('(?si)<table.*?</table>', resp_text)
    if 'javascript:peUsuarioDefecto' not in table:
        return []
    # broken layout - no </tr>
    rows = re.findall('(?si)<tr.*?</script>', table)
    for row in rows:
        title = extract.re_first_or_blank('<div id="" class="font--size-100">(.*?)</div>', row).strip()
        if not title:
            logger.error("Can't parse org title. Check the regexp. Skip")
            continue
        params_str = ''
        if 'javascript:doCambioUsuario' in row:
            # Can switch to this contract, it also has 'peUsuarioDefecto' (see below)
            param_list_len = 3
            # Can be with title (16556) or without (27606), title will be dropped then
            #   dev_regular_202206/resp_list_contracts_16556.html
            #     javascript:doCambioUsuario('01579041401', 'MEURI SOCIEDAD LIMITADA.', '9725025790414', 'xCDmLTqicMvEIOYtOqJwywAAAXx0Io1A68AUVxljzwA')" # noqa
            #   dev_regular_202206/resp_list_contracts_27606.html
            #     javascript:doCambioUsuario('01579041401', '9725025790414', 'xCDmLTqicMvEIOYtOqJwywAAAXx0Io1A68AUVxljzwA')"  # noqa
            params_str = extract.re_first_or_blank(
                r'(?si)href="javascript:doCambioUsuario\((.*?)\)"',
                row
            )
        elif 'javascript:peUsuarioDefecto' in row:
            # ALREADY SELECTED (SWITCHED) COMPANY/CONTRACT (default usually) has no 'doCambioUsuario'
            # no need to switch, title already extracted
            param_list_len = 0
        else:
            continue
        params_str = params_str.replace('\\', '')
        # ',' allows to handle unexpected quote in params
        # (if there is a quote in organization name)
        params_str += ','
        # If can switch
        #   ['00989982901', 'FRANCISCO JAVIER MAURICIO FOCHE', '9725019899829', 'o45BRsBl97WjjkFGwGX3tQAAAXdOPRlP70r5zv_dqmQ']  # noqa
        #   ['00989982901', '9725019899829', 'o45BRsBl97WjjkFGwGX3tQAAAXdOPRlP70r5zv_dqmQ']
        # -> always to ['00989982901', '9725019899829', 'o45BRsBl97WjjkFGwGX3tQAAAXdOPRlP70r5zv_dqmQ']
        req_params = [
            p for p in re.findall(r'''['"](.*?)['"],''', params_str)
            if p.strip() != title
        ]
        if len(req_params) != param_list_len:
            logger.error("Can't parse req params `{}`. Check the regexp. Skip".format(
                params_str
            ))
            continue
        company = Company(
            title=html.unescape(title),
            request_params=req_params
        )
        companies.append(company)
    return companies


def get_next_page_with_accs_params_patch(resp_text: str) -> Dict[str, str]:
    """
    Parses
    <script id="evaluaScript_GCT111">

    var f = document.forms[0];
    f.CLAVE_CONTINUACION_CLCOTG.value="020";  // curr page
    f.CLAVE_CONTINUACION_TOOFCU.value="357100000000000 000000198388816 "; // curr page
    f.CLAVE_CONTINUACION_TOGECU.value="00000000000 000000198388816 "; // curr page
    f.CLAVE_CONTINUACION_CLCOTG_SIG.value="040"; // next page
    f.CLAVE_CONTINUACION_TOOFCU_SIG.value="357100000000000 000000626541845 ";  // next page
    f.CLAVE_CON
    </script>

    to dict
    """
    res = {}  # type: Dict[str, str]
    for k in ['CLAVE_CONTINUACION_CLCOTG_SIG', 'CLAVE_CONTINUACION_TOOFCU_SIG', 'CLAVE_CONTINUACION_TOGECU_SIG']:
        #  several places to get vals
        #  (extract.form_param fixes acc pagination for 3rd page: -a 21910, acc ES7321009135072200157114)
        res[k] = extract.re_first_or_blank(
            'f.{}.value="(.*?)"'.format(k),
            resp_text
        ) or extract.form_param(resp_text, k)

    return res


def get_accounts_parsed(logger: ScrapeLogger, resp_text: str, page_ix: int) -> List[AccountParsed]:
    # from dev_regular/5_resp_tesoreria.html

    # Necessary to extract movements
    # TablaBean01_RefVal1 = new Array("p6DpzbyOCGynoOnNvI4IbAAAAWep6Y00YJn1r8ShJUA", "", "")
    accounts_parsed = []  # type: List[AccountParsed]

    numero_cuenta_params = [
        v.strip('"')
        for v in extract.re_first_or_blank(r'(?si)TablaBean01_RefVal1\s*=\s*new\s+Array\((.*?)\)',
                                           resp_text).split(',')
    ]
    accounts_htmls = re.findall(r'(?si)<tr id="data_\d+".*?</tr>', resp_text)
    # Increase with each iteration
    # but if got blank refval_simple_numero_cuenta_param
    # then increase more
    numero_cuenta_ix = 0
    for i, acc_html in enumerate(accounts_htmls):
        cells = re.findall('(?si)<td.*?</td>', acc_html)

        # = AccountNo =

        # ES6321005858740200009275
        # use ES\d+ to avoid ES2321005376447200000795DÓLARUSA:+154.642,19

        # Tesoreria view
        # for USD: from '<td scope="row"  class="ltxt " ><a id="" href="JavaScript:enviar(2, \\'103\\')"
        # title=""><span>ES23 2100 5376 4472 0000 0795</span></a><as_is><BR></as_is>DÓLAR
        # USA<as_is>:&nbsp;</as_is>+154.642,19</th>
        # <td class="" ></td>'
        account_no = extract.re_first_or_blank(
            r'ES[\d\s]+',
            cells[0]
        ).replace(' ', '')
        # Handle account alias like 'GESTORES RED' (contains 'ES ')
        #  to avoid false-positive IBAN detection
        if account_no == 'ES':
            account_no = ''

        # Only Cuentas view
        # Handle case when thee is no IBAN in the list, will retrieve it from movement view
        # id="colNumCuenta" only for 'cuentas' view
        # <td scope="row"  class="ltxt "  id="colNumCuenta" > .....
        # <span class="font--weight-bold">CUENTA IMAGIC</span> ... 0005 7936</span></a></th>
        account_alias = (extract.remove_tags(cells[0]).split('\n')[0]  # drop balance
                         if not account_no and 'id="colNumCuenta"' in cells[0]
                         else '')

        if not (account_no or account_alias):
            logger.error("acc ix {}: can't get account_no or account_alias. Skip. RESPONSE PART\n{}".format(
                i,
                acc_html
            ))
            numero_cuenta_ix += 1
            continue

        # Handle case when list contains blank vals
        # due to end of subtype of accounts
        # -u 149727 -a 6033 company VIA CELERE DESARROLLOS INMOBILIARIOS: before ES73 2100 9135 0722 0015 7114
        # -u 242841 -a 12802
        # -a 6025, -a 7214 foreign currency USD
        # -a 7214 - acc alias, no iban
        while True:
            if numero_cuenta_ix >= len(numero_cuenta_params):
                logger.error("{}: can't get numero_quenta_param: ix={} >= len of {}. "
                             "Skip account".format(account_no, numero_cuenta_ix, numero_cuenta_params))
                return accounts_parsed

            numero_quenta_param = numero_cuenta_params[numero_cuenta_ix]
            if numero_quenta_param:
                break
            numero_cuenta_ix += 1

        # = Currency =

        currency = ''
        if not extract.re_first_or_blank(r'Cuentas nacionales\s*</h1>', resp_text):
            # Tesoreria view
            # Explicit place for foreign currency - near account title,
            for currency_name, currency_code in FOREIGN_CURRENCIES.items():
                if currency_name in cells[0]:
                    currency = currency_code
                    break
            else:
                currency = 'EUR'  # for Tesoreria view if there is no sign then EUR
            # Check for unknown foreign currency
            if '<as_is>' in cells[0]:
                if (currency == 'EUR') and ('EUROS' not in cells[0]):
                    logger.error("{}: expected foreign currency, but got EUR. Skip. RESPONSE PART\n{}".format(
                        account_no,
                        cells[0]
                    ))
                    numero_cuenta_ix += 1
                    continue
        else:
            # Cuentas view

            # After the first balance value (in case of foreign currency):
            # € as html code or 3-char currency
            currency_raw = extract.remove_tags(
                extract.re_first_or_blank(r'id="colExtractoAQM"[^>]*>[-.,0-9\s]+(&#8364;|[A-Z]+)', cells[0])
            )
            currency = 'EUR' if currency_raw == '€' else currency_raw

        if len(currency) != 3:
            logger.error("{}: can't parse currency. Skip. RESPONSE PART\n{}".format(
                account_no,
                cells[0]
            ))
            numero_cuenta_ix += 1
            continue

        # = Balance =

        try:
            # Tesoreria view
            if len(cells) == 8:
                balance = convert.to_float(extract.remove_tags(cells[4]))
                # Foreign currency amount, -a 23501, 22952
                balance_as_is_str = extract.re_first_or_blank(r'</as_is>([-+.,0-9\s]+)</th>', cells[0])
                if balance_as_is_str:
                    balance = convert.to_float(balance_as_is_str)
            # Cuentas view
            elif len(cells) == 3:
                # id="colExtractoAQM" >46.022,98 &#8364;</td>
                # <td class="rtxt "  id="colExtractoAQM" >-15,09 USD (-12,97 &#8364;)</td>
                balance = convert.to_float(
                    extract.re_first_or_blank(r'id="colExtractoAQM"[^>]*>([-.,0-9]+)', cells[0])
                )
            else:
                logger.error("{}: can't get balance. Skip. RESPONSE PART\n{}".format(
                    account_no,
                    acc_html
                ))
                numero_cuenta_ix += 1
                continue
        except Exception as _e:
            logger.error("{}: can't parse. HANDLED EXCEPTION:\n{}\n. Skip. RESPONSE PART\n{}".format(
                traceback.format_exc(),
                account_no,
                acc_html
            ))
            numero_cuenta_ix += 1
            continue

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        # <td class="rtxt  medida20" id="EUR1"><span>+32.080,43</span></td>

        account_parsed = {
            'account_no': account_no,
            'account_alias': account_alias,  # if can't get account_no
            # IMPORTANT: we use balance_available for credit accs (equal to balance if debit acc)
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'refval_simple_numero_cuenta_param': numero_quenta_param,  # only for recent movs
            # For accounts from page_ix > 0 account_page_ix will be 0 ALWAYS (top in the dropdown)
            # but for accounts from first page its ix in dropdown will be as at the page
            # It used to filter by dates
            'account_page_ix': i if page_ix == 0 else 0,
            'is_private_view': False,  # scraped from Empresas
        }
        accounts_parsed.append(account_parsed)
        numero_cuenta_ix += 1

    return accounts_parsed


def build_next_page_w_companies_req_params(resp_text: str) -> Tuple[str, dict]:
    """New and ol compat"""
    req_link, req_params = extract.build_req_params_from_form_html_patched(
        resp_text,
        form_re=r'(?si)<div id="lo_contenido">.*?</form>',
        is_ordered=True
    )
    if not req_params:
        return '', {}

    req_params['PN'] = 'LGU'
    req_params['PE'] = '1'  # was str(page_ix)

    # Var if_branch for:
    # function paginar(val){
    # f=document.forms["formPaginacion"]
    # f.PN.value="LGU"
    # f.PE.value="1"
    # f.PAS.value=""
    # f.LGU2PAS_CABECERA.value=""
    # if (val == 0){
    # f.CLAVE_CONTINUACION_AREACLO.value="000"
    # f.CLAVE_CONTINUACION_USUCLO.value="00000000000"
    # f.CLAVE_CONTINUACION_COMCLO.value="0000000000000"
    # f.PRIMERA_CONSULTA.value="1"
    # }else if (val == 1){
    # f.CLAVE_CONTINUACION_AREACLO.value="96"
    # f.CLAVE_CONTINUACION_USUCLO.value="1940274201"
    # f.CLAVE_CONTINUACION_COMCLO.value="9725029402742"
    # f.PRIMERA_CONSULTA.value="0"
    # }
    # f.submit();
    # }
    # javascript:paginar(1);

    # 0 or 1
    if_branch_val = 1  # 1 - next page, 0 - prev page

    # old - already in req_params, new - need to get from JS
    for param in ['CLAVE_CONTINUACION_AREACLO', 'CLAVE_CONTINUACION_USUCLO',
                  'CLAVE_CONTINUACION_COMCLO', 'PRIMERA_CONSULTA']:
        if not req_params.get(param):
            # Like r'(?si)val == {}.*?CLAVE_CONTINUACION_AREACLO.value="(\d+)"'
            req_params[param] = extract.re_first_or_blank(
                r'(?si)val == {}.*?{}.value="(\d+)"'.format(if_branch_val, param),
                resp_text
            )

    return req_link, req_params


def get_numero_cuenta_for_req_filter_by_dates(resp_text: str, acc_page_ix: int) -> str:
    numero_cuenta_params = [
        v.strip('"')
        for v in extract.re_first_or_blank(r'(?si)ArrayBean01_RefVal1\s*=\s*new\s+Array\((.*?)\)',
                                           resp_text).split(',')
    ]
    return numero_cuenta_params[acc_page_ix]


def get_refval_params_during_pagination(resp_text: str) -> dict:
    # it looks like these values will overwrite initial vals
    refval_params = {
        'REFVAL_SIMPLE_NUMERO_CUENTA': extract.re_first_or_blank(
            r'document.forms\[0\].REFVAL_SIMPLE_NUMERO_CUENTA.value\s*=\s*"(.*?)"',
            resp_text
        ),
        'REFVAL_SIMPLE_CUENTA': extract.re_first_or_blank(
            r'document.forms\[0\].REFVAL_SIMPLE_CUENTA.value\s*=\s*"(.*?)"',
            resp_text
        )
    }
    return refval_params


def get_clave_continuacion_oper_param(resp_text: str) -> str:
    param = extract.re_first_or_blank(
        # '0F20183580016603       31376312018350'
        r"""href="javaScript:paginacionExtractoAsincronaPlus\('(.*?)'""",
        resp_text
    )
    return param


def get_movs_detail_req_params(resp_text: str) -> dict:
    """Extracts params from resp_recent_movs"""

    # REFVAL_SIMPLE_NUMERO_CUENTA	yi_VLQOpvPPKL9UtA6m88wAAAWeatq0UUL7G1~9uEK4
    # REFVAL_SIMPLE_CUENTA	yi_VLQRERuLKL9UtBERG4gAAAWeatq0UBd~w4RX270k
    # FLAG_PE	undefined
    # POSICION_TR_ABIERTO	5
    # OPCION_OPERACION	LISTACLOP
    # CLICK_ORIG	FLX_GCT_100
    # FLAG_KEEP_THE_CHANGE	N
    # FLUJO_T	GCT,100,188:GCT,11,:GFI,7,''

    params = {
        'REFVAL_SIMPLE_NUMERO_CUENTA': extract.re_first_or_blank(
            r'<input type="hidden" name="REFVAL_SIMPLE_NUMERO_CUENTA" value="(.*?)">',
            resp_text
        ),
        'REFVAL_SIMPLE_CUENTA': extract.re_first_or_blank(
            r'<input type="hidden"\s+name="REFVAL_SIMPLE_CUENTA"\s+value="(.*?)">',
            resp_text
        ),
        'FLAG_PE': 'undefined',
        'POSICION_TR_ABIERTO': '5',  # ?? 0 at the page
        'OPCION_OPERACION': 'LISTACLOP',
        'CLICK_ORIG': 'FLX_GCT_100',
        'FLAG_KEEP_THE_CHANGE': 'N',
        # 'FLUJO_T': extract.re_first_or_blank('FLUJO.value\s*=\s*"(.*?)"', resp_text),  # wrong
        # GCT,100,188:GCT,11,:GFI,7,''
        'FLUJO_T': extract.re_first_or_blank('<input type="hidden" name="FLUJO_T" value="(.*?)">', resp_text),
    }

    return params


def get_movements_parsed(logger: ScrapeLogger,
                         fin_ent_account_id: str,
                         resp_text: str,
                         movement_details_additional_params: dict) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]
    if 'Sin operaciones a extractar' in resp_text:
        return movements_parsed_desc

    # eur accounts columns
    # Concepto 	  	Fecha 	Fecha valor 	Más datos 	Importe 	Saldo 	Opciones
    # usd (but maybe not only usd) accounts have another columns
    # Concepto 	  	Fecha 	Fecha valor 	Más datos 	Oficina 	Importe 	Saldo

    # ['Concepto', 'Fecha', 'Fecha valor', 'Más datos', 'Importe', 'Saldo', 'Opciones']
    # omit empty columns - no such columns in movement
    colums = [
        h for h in
        [extract.remove_tags(el) for el in
         re.findall(r'<th\s+scope.*?>(.*?)</th>',
                    extract.re_first_or_blank(r'(?si)TablaBean02.*?<thead>(.*?)</thead>', resp_text))]
        if h != ''
    ]
    amount_ix = colums.index('Importe')
    temp_balance_ix = colums.index('Saldo')
    mas_datos_ix = colums.index('Más datos')

    movs_htmls = re.findall('(?si)<tr[^>]+id="TablaBean.*?</tr>', resp_text)
    for mov_html in movs_htmls:
        # ['', '24/12/2018', '24/12/2018', 'B14080915000', '- 464,10', '+ 30.059,91', '']
        cells = [extract.remove_tags(v) for v in re.findall('(?si)<td.*?</td>', mov_html)]
        # not a movement?
        if len(cells) != 7:
            continue
        operation_date = cells[1]
        value_date = cells[2]
        remitente_param = cells[3]  # Remitente=B14080915000

        # handle `INGRESO POR VALIDAR
        # $(document).ready(function() {
        # initMailboxTooltip("EnlaceTooltipAyuda1");
        # }); (CAJA MMC PICA)` - remove 'help tooltip'from the descr
        descr = re.sub(r"(?si)\$\(document\).*", '',
                       extract.remove_tags(extract.re_first_or_blank('(?si)<th.*?</th>', mov_html))).strip()
        descr_mas_datos = extract.remove_tags(cells[mas_datos_ix])
        descr_w_mas_datos = ("{} ({})".format(descr, descr_mas_datos)
                             if descr_mas_datos else descr)  # descr if no/empty mas_datos

        try:
            temp_balance = convert.to_float(cells[temp_balance_ix])

            # handle case 198549: fin_entity_access 6923: ES1021005858760200007027
            # <td class="rtxt " ><span>&nbsp;</span></td>
            # <td class="ltxt "  colspan="2"  id="FECHA7"><span>29/01/2019</span></td>
            # <td class="ltxt "  colspan="2"  id="DATA_VALOR7" style="display:none;"><span>29/01/2019</span></td>
            # <td class="tamanyomaximocolumna ltxt " ><span>26</span></td>
            # <td class="rtxt " ><span>Pendiente</span></td>  <------- calc from temp_bal if possible
            # <td class="rtxt " ><span>+&nbsp;60.009,18</span></td>
            # <td class="ltxt "  id="columna_link" ><span>&nbsp;</span></td>
            try:
                amount = convert.to_float(cells[amount_ix])  # type: Optional[float]
            except ValueError:
                # This is a pending movement.
                # The amount will be calculated in calculate_pending_amounts()
                # after all movements from all pages are parsed
                amount = None

            # PN=GCT
            # &PE=103
            # &NUMERO_MOVIMIENTO=0016607
            # &FECHA_CONTABLE=2018358
            # &INDICADOR_COMUNICADOS=N
            # &CLOPWW=046
            # &SUBCLO=00000&IMPORTE_COM=000000000046410
            # &SIGNO_IMPORTE_COM=-
            # &MONEDA_COM=EUR
            # &SALDO_ACTUAL=000000003005991
            # &SIGNO_SALDO_ACTUAL=+
            # &FECHA_VALOR=24122018
            # &INDICA_SALDO=NNSN&TIPO_BUSQUEDA=05
            # &FECHA_COM=24122018
            # &TIPO_COMUNICADO=00000&DESC_COMUNICADO=INFRICO+S.L.&REMITENTE=B14080915000
            # &NUMERO_RECIBO=021634900263006&OPCION_OPERACION=LISTACLOP
            # &CLICK_ORIG=FLX_GCT_100
            # &CLAVE_ANTERIOR=++000000000000000000000000000+0000000
            # &CLAVE_CONTINUACION_SUM=  000000000000000000000000000 0000000
            # &CLAVE_CONTINUACION_DETALLE_3496=  000000000000000000000000000 0000000
            # &CLAVE_DETALLE_3496=D_3496_0
            # &NUMERO_SUBMOVIMIENTO=&TIPO_CUENTAS=VIG
            # &APLICACION_ORIGEN=CIA' as dict
            mov_details_req_params = {
                k: v[0]
                for k, v in parse_qs(extract.re_first_or_blank(r"javascript:sendIFrame\('(.*?)'", mov_html)).items()
            }
            mov_details_req_params.update(movement_details_additional_params)
            mov_details_req_params['REMITENTE'] = remitente_param
        except Exception as _e:
            logger.error("{}: can't parse movement: HANDLED EXCEPTION\n{}\n---\nmov html:\n{}\n"
                         "Skip the movement".format(fin_ent_account_id,
                                                    traceback.format_exc(),
                                                    mov_html))
            continue

        movement_parsed = {
            'operation_date': operation_date,  # '24/12/2018'
            'value_date': value_date,
            'description': descr_w_mas_datos,
            'amount': amount,
            'temp_balance': temp_balance,
            'mov_details_req_params': mov_details_req_params,
            # can be any unique, to process parallel
            'id': '{}--({}/{})--{}'.format(operation_date, amount, temp_balance, uuid.uuid4())
        }
        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc


def calculate_pending_amounts(logger: ScrapeLogger,
                              fin_ent_account_id: str,
                              movs_parsed_desc: List[MovementParsed]) -> List[MovementParsed]:
    movs_parsed_calc_amounts_asc = []  # type: List[MovementParsed]
    temp_balance_prev = None
    # from the oldest to newest
    for mov in reversed(movs_parsed_desc):
        amount = mov['amount']
        if amount is None and temp_balance_prev is None:
            # can't calculate amount for the very first movement in the list
            # (it is the oldest movement of the account)
            logger.warning("{}: can't calculate amount. No previous movements. Mov: {}".format(
                fin_ent_account_id, mov
            ))
            temp_balance_prev = mov['temp_balance']
            continue

        if amount is None:
            mov['amount'] = round(mov['temp_balance'] - temp_balance_prev, 2)
            logger.info('{}: calculated amount={} for mov {}'.format(
                fin_ent_account_id, mov['amount'], mov
            ))

        movs_parsed_calc_amounts_asc.append(mov)
        temp_balance_prev = mov['temp_balance']

    # the code expects descending ordering
    return list(reversed(movs_parsed_calc_amounts_asc))


def get_description_extended(logger: ScrapeLogger,
                             fin_ent_account_id: str,
                             resp_text: str,
                             movement_parsed: MovementParsed) -> str:
    """Extracts the description_extended from mov details resp with the rules described below.
    Fields:
    a. Concepto
    b. Concepto específico
    c. Remitente
    d. Referencia 2
    e. Otras caracteristicas
    f. Concepto informado por el ordenante
    g. Codigo identificacion del ordenante
    h. Concepto transferencia
    i. [NEW since 2019-06-02] Oficina
    The fields must be concatenated to be inserted in ExtendedDescription as you are doing in BBVA. They must be
    concatenated in the order above.
    If a field does not appear in the Detail of the movement,
     it must also be included in the ExtendedDescription as
    "|| ||", so that the ExtendedDescription format will always be the same, whether the fields appear or not.
    """

    description_extended = movement_parsed['description']

    trs = re.findall('(?si)<tr.*?</tr>', resp_text)
    fields_vals = {}  # type: Dict[str, str]
    for tr in trs:
        # handle tr with th only - or it'll bring expecting exception
        if '<td' not in tr:
            continue
        try:
            # '<tr id="" name="" class=" no_border border_bottom" style="">
            # <th scope="row"  class="" ><span></span></th>
            # <td class="bold rtxt " >Otras características</td>
            # <td class="tamanyomaximocolumna ltxt " ><span>866356-000876-00002000001</span></td>
            # </tr>'
            tds = [extract.remove_tags(v) for v in re.findall('(?si)<td.*?</td>', tr)]
            fields_vals[tds[0]] = tds[1]
        except Exception as _e:
            logger.error(
                "{}: can't parse extended description: HANDLED EXCEPTION\n{}\n"
                "---\ntr html:\n{}\nUse short (default) description as description_extended".format(
                    fin_ent_account_id,
                    traceback.format_exc(),
                    tr
                ))
            return description_extended

    for title in MOV_EXTENDED_DESCRIPTION_FIELDS:
        val = fields_vals.get(title, '')
        msg = '{}: {}'.format(title, val).strip() if val else ''
        description_extended += ' || {}'.format(msg).rstrip()

    # Get 'oficina' field and add to description_extended
    # it can be
    # 'Oficina'
    # 'Oficina Caixabank origen'
    # 'Oficina origen'
    # '... Oficina ... '
    for k, v in fields_vals.items():
        if 'oficina' in k.lower():
            msg = 'Oficina: {}'.format(extract.remove_extra_spaces(v)).strip()
            description_extended += ' || {}'.format(msg)
            break
    else:
        description_extended += ' ||'  # no office info found

    return description_extended


def req_switch_comp_params(company: Company) -> OrderedDict:
    req_params = OrderedDict([
        ('PN', 'LGU'),
        ('PE', '9'),  # check 9
        ('ORIGEN_LGU', 'E'),
        # jBt9SJarsQCMG31IlquxAAAAAWerh2aGT8X33M1gEtA  // 3rd par
        ('refCanviUsuclo', company.request_params[2]),
        ('CLAVE_CONTINUACION_AREACLO', '000'),
        ('CLAVE_CONTINUACION_USUCLO', '00000000000'),
        ('CLAVE_CONTINUACION_COMCLO', '0000000000000'),
        ('CC1', '000'),
        ('CC2', '00000000000'),
        ('CC3', '0000000000000'),
        #  9725010894983 // 2nd par
        ('CONTRATO_CLO', company.request_params[1]),
        # SOLAR+CASA+ARRIBA+DE+LOS+LLANOS+SL // 1st par
        # ('USUARI_DEFECTE_MID', company.request_params[1]),
        # 00089498301 // 0-idx par
        ('CANVI_USUCLO', company.request_params[0]),
        ('PRIMERA_CONSULTA', '1'),
        ('CLICK_ORIG', ''),
    ])
    return req_params


def req_recent_movs_params(account_parsed: AccountParsed) -> OrderedDict:
    # from enviar() js func
    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '16'),
        ('NCTREL', '003'),
        ('CLAVE_CONTINUACION_CLCOTG', '000'),
        ('CLAVE_CONTINUACION_TOOFCU', '000000000000000 000000000000000'),
        ('CLAVE_CONTINUACION_TOGECU', '00000000000 000000000000000'),
        ('CLAVE_CONTINUACION_CLCOTG_SIG', '000'),
        ('CLAVE_CONTINUACION_TOOFCU_SIG', '000000000000000 000000000000000'),
        ('CLAVE_CONTINUACION_TOGECU_SIG', '00000000000 000000000000000'),
        ('SUMA_OFICINA_P', '0.0'),
        ('SUMA_TOTAL_P', '0.0'),  # total '436926.0'
        ('SUMA_OFICINA_E', '0.0'),
        ('SUMA_TOTAL_E', account_parsed['balance']),  # acc bal
        ('REFVAL_SIMPLE_NUMERO_CUENTA', account_parsed['refval_simple_numero_cuenta_param']),
        ('ORIGEN_INVOCACION', 'GCT11'),
        ('FLAG_PE', 'P'),
        ('TORNA_PN_CCT', 'GCT'),
        ('TORNA_PE_CCT', '11'),
        ('ALIAS_CUENTA', ''),
        ('FLAG_MONEDA', '0'),  # may be different, if not EUR?
        ('NumFilasTabla', '1'),
        ('FLAG_KEEP_THE_CHANGE', 'N'),
        ('MONEDA', ''),
        ('MOSTRAR_TRASPASO_RAPIDO', 'N'),
        ('CLICK_ORIG', 'EOC_GCT_11'),
    ])
    return req_params


def get_account_no_from_movs_page(resp_text: str) -> str:
    """To use in validator"""
    account_no = extract.re_first_or_blank(
        '(?s)<span class="tit_subt ">([^<]+)</span>',
        resp_text
    ).replace(' ', '')
    return account_no


def req_movs_filter_by_dates_params(date_from: str, date_to: str,
                                    refval_numero_cuenta_for_req_filter_by_dates: str) -> OrderedDict:
    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '102'),
        ('OPERACION_NUEVO_EXTRACTO', 'MOVIMIENTOS_POR_FECHA'),
        ('CLICK_ORIG', 'FLX_GCT_100'),
        ('FLAG_PE', 'E'),
        ('FLUJO', "GCT,100,180:GFI,7,'"),  # fixed value, but may be changed
        ('CLAVE_CONTINUACION_SUM', '  000000000000000000000000000 0000000'),
        ('FECHA_INICIAL', ''),
        ('ORDEN_MOVIMIENTOS', 'R'),
        ('FECHA_INICIO_OPERACIONES', date_funcs.convert_to_ymd(date_from)),  # '20180101'
        ('FECHA_FIN_OPERACIONES', date_funcs.convert_to_ymd(date_to)),  # '20181230'
        ('FILTRO_ABIERTO', 'S'),
        ('ID_TABLA', 'TablaBean02'),
        ('TIPO_CUENTAS', 'VIG'),
        # 'lZkCMwQriBOVmQIzBCuIEwAAAWgARULCerw5JiVuqfE'
        ('REFVAL_SIMPLE_NUMERO_CUENTA', refval_numero_cuenta_for_req_filter_by_dates),
        ('ALIAS_CUENTA', ''),
        ('FLAG_KEEP_THE_CHANGE', 'N'),
        ('MONEDA', '1004'),
        ('INDICADOR_CANCELADA', ''),
        ('CLAU_CONTINUACIO_MOV', '40' * 50),  # ?, too long string
        ('FLAG_CAMBIO_CUENTA_EXTRACTO', 'S'),
    ])
    return req_params


def req_movs_next_page_params(refval_params: dict,
                              clave_continuation_oper_param: str,
                              loop_ix: int,
                              date_from_str: str,
                              date_to_str: str,
                              max_movs_per_page: int) -> OrderedDict:
    req_params = OrderedDict([
        ('PN', 'GCT'),
        ('PE', '102'),
        ('OPERACION_NUEVO_EXTRACTO', 'MOVIMIENTOS_POR_FECHA'),
        ('CLICK_ORIG', 'PAG_GCT_102'),
        ('TOTAL_MOVIMIENTOS', max_movs_per_page * (loop_ix + 1)),  # the changing doesn't make effect
        ('ID_TABLA', 'TablaBean02PaginacionPlus'),
        ('TIPO_CUENTAS', 'VIG'),
        ('REFVAL_SIMPLE_NUMERO_CUENTA', refval_params['REFVAL_SIMPLE_NUMERO_CUENTA']),
        ('FLAG_KEEP_THE_CHANGE', 'N'),
        # should be 000000006133395 (last mov temp bal * 100)
        # can extract from document.forms[0].SALDO_ACTUAL.value="000000006133395";
        # during the pagination
        # ('SALDO_ACTUAL', '000000029570555'),
        ('SALDO_ACTUAL', '000000000000000'),
        ('SALDO_RETENIDO', '000000000000000'),
        ('SIGNO_SALDO_ACTUAL', ' '),
        # ('SIGNO_SALDO_ACTUAL', '-'),  # for credit acc
        ('SIGNO_SALDO_RETENIDO', ' '),
        ('CLAVE_CONTINUACION_OPER', clave_continuation_oper_param),
        ('FLAG_PE', 'E'),
        ('FLUJO', "GCT,100,180:GFI,7,''"),
        ('CLAVE_CONTINUACION_SUM', '  000000000000000000000000000 0000000'),
        ('FECHA_INICIAL', ''),
        ('ORDEN_MOVIMIENTOS', 'R'),
        ('FECHA_INICIO_OPERACIONES', date_funcs.convert_to_ymd(date_from_str)),  # 20180101
        ('FECHA_FIN_OPERACIONES', date_funcs.convert_to_ymd(date_to_str)),  # 20181230
        ('FILTRO_ABIERTO', 'S'),
        ('FLAG_VISUALIZAR_LINK_ESPECIAL', 'N'),
        ('MONEDA', ''),
        # '0F20183580016603       31376312018350'
        ('CLAU_CONTINUACIO_MOV', clave_continuation_oper_param),
    ])
    return req_params


# fixme: NO THIS FUNCTION PROVIDED IN ORIGINAL CODE
#  VB: copied from sabadell_scraper/parse_helpers.py
def parse_reference_from_receipt(receipt_description: str) -> str:
    ref_fichero = extract.re_first_or_blank(r'(?si)\w\d{29}', receipt_description)  # B86900263000201811281142035178
    if ref_fichero:
        return ref_fichero

    # FECHA 21-12-18
    date_str = extract.re_first_or_blank(r'(?si)FECHA (\d\d-\d\d-\d\d)', receipt_description)
    # CONTENIA 652 ADEUDOS
    numrec_str = extract.re_first_or_blank(r'(?si)CONTENIA (\d+) ADEUDOS', receipt_description)
    # N.I.F.......: B86900263
    nif_str = extract.re_first_or_blank(r'(?si)N.I.F.......: (\w\d+)', receipt_description)

    # fact_str = re.findall('(?si)N.FACTURA...: ([^\s]+)', receipt_description) #N.FACTURA...: 2I266J9A1000

    if not (date_str and numrec_str and nif_str):
        return ''
    return "{}|{}|{}|".format(date_str, numrec_str, nif_str)


def get_movs_receipts_req_params(resp_text: str) -> OrderedDict:
    """Extracts receipt params from resp_recent_movs"""

    # parse <a href="javascript:guardarPDFComunicado(\'00611\',\'L\',
    # \'8TYGl0nvSArxNgaXSe9ICgAAAWnMzSVcQ1TzaB_ffGM:COM:200\')"
    # class="no_subrayado"  title=""  onClick="this.blur();"><img class=" "  src="../imatge/icon_PDF.gif"  onclick
    # ="" /></a>
    # '00611', 'L', '8TYGl0nvSArxNgaXSe9ICgAAAWnMzSVcQ1TzaB_ffGM:COM:200'

    params_raw = re.findall(r"(?si)javascript:guardarPDFComunicado\('(.*?)','(.*?)','(.*?)'\)", resp_text)
    if not params_raw:
        return OrderedDict([])

    extracted_params = {
        'FORMATO_COMUNICADO': params_raw[0][1],
        'TIPO_COMUNICADO': params_raw[0][0],
        'REFCLAVECOMUNICADO': params_raw[0][2]
    }

    return _get_receipt_req_params(extracted_params)


def get_movs_receipts_req_params_from_first_comm(resp_text: str) -> OrderedDict:
    """Extracts receipt params from the first communication of the resp_recent_movs"""

    # if it exists, parse href="JavaScript:verComunicadoLista(0,
    # 'PN=GCT&amp;PE=103&amp;CLICK_ORIG=FLX_GCT_100&amp;FORMATO_COMUNICADO=L&amp;OPCION_OPERACION=VISTERCIO&amp;
    # REFCLAVECOMUNICADO=MWHs~mubP2MxYez6a5s_YwAAAWmUlQjTy9zC3cYfWL8:COM:200&amp;REF_CONTRATO_VINCULADO=
    # MWHs~mwpxPUxYez6bCnE9QAAAWmUlQjTEIY9sBcYVpc:COM:200&amp;TIPO_COMUNICADO=00611&amp;FECHA_COM=03042019')

    if not re.search(r'(?si)JavaScript:verComunicadoLista\(0,', resp_text):
        return OrderedDict([])

    first_comm_params = {
        k: v[0]
        for k, v in parse_qs(extract.re_first_or_blank(r"JavaScript:verComunicadoLista\(0,'(.*?)'", resp_text)).items()
    }

    return _get_receipt_req_params(first_comm_params)


def _get_receipt_req_params(extracted_params: dict) -> OrderedDict:
    """Return request params to get receipt"""

    if not extracted_params:
        return OrderedDict([])

    return OrderedDict([
        ('FLUJO', "GCT,100,180:GFI,7,''"),
        ('PN', 'COM'),
        ('PE', '39'),
        ('CLICK_ORIG', '300'),
        ('RESOLUCION', '300'),
        ('FLAG_PDF_INICIAL', 'S'),
        ('FORMATO_COMUNICADO', extracted_params['FORMATO_COMUNICADO']),
        ('TIPO_COMUNICADO', extracted_params['TIPO_COMUNICADO']),
        ('REFCLAVECOMUNICADO', extracted_params['REFCLAVECOMUNICADO']),
        ('OPERACION_NUEVO_EXTRACTO', 'MOVIMIENTOS_POR_FECHA'),
        ('CLAVE_ANTERIOR', '  000000000000000000000000000 0000000'),
        ('HTML_DETALLE_MOVIMIENTO', '')
    ])


def get_corespondence_from_list(resp_correspondence_text: str) -> List[CorrespondenceDocParsed]:
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]

    corr_table = ''
    if 'tablacorresp' in resp_correspondence_text:
        corr_table = extract.re_first_or_blank('(?si)<table[^>]+id="tablacorresp".*?</table>',
                                           resp_correspondence_text)
    if 'detalleComunicadoNew' in resp_correspondence_text:
        return get_corespondence_from_list_tabla_comunicados_new(resp_correspondence_text)

    rows = re.findall('(?si)<tr.*?</tr>', corr_table)
    for row in rows:
        cells = re.findall('(?si)<td.*?</td>', row)
        if len(cells) < 5:
            continue
        # from javascript:detalleComunicado('0','202005280046500009570','',
        # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw');
        js_details = extract.re_first_or_blank("javascript:detalleComunicado[(](.*?)[)]", cells[0]).split(',')
        if 'detalleComunicadoNew' in resp_correspondence_text:
            js_details = extract.re_first_or_blank("javascript:detalleComunicadoNew[(](.*?)[)]", cells[3]).split(',')
        doc_id = js_details[1].replace("'", '')
        # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw'
        refval_complejo_param = js_details[3].replace("'", '')
        amount_str = extract.text_wo_scripts_and_tags(cells[3])  # '937,50' or ''
        currency = convert.to_currency_code(extract.text_wo_scripts_and_tags(cells[4]))
        corr = CorrespondenceDocParsed(
            type=extract.text_wo_scripts_and_tags(cells[1]),  # 'Varios'
            # no info, will get from correspondence's details
            # using get_account_iban_for_correspondence_document
            account_no='',
            # from '26/05/2020'
            operation_date=datetime.strptime(extract.text_wo_scripts_and_tags(cells[2]), '%d/%m/%Y'),
            value_date=None,
            amount=convert.to_float(amount_str) if amount_str else None,
            currency=currency,
            descr=extract.text_wo_scripts_and_tags(cells[0]),  # 'Normativa EMIR Refit'
            extra={
                'amount_str': amount_str,
                'currency': extract.text_wo_scripts_and_tags(cells[4]),  # 'euros' or ''
                'doc_id': doc_id,  # '202005280046500009570'
                # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw'
                'refval_complejo_param': refval_complejo_param,
            }
        )
        corrs_from_list.append(corr)

    return corrs_from_list


def _parse_date_str(date_str: str) -> datetime:
    """
    >>> dt = datetime.strptime('12/08/2021', '%d/%m/%Y')
    >>> _parse_date_str('12 ago 2021') == dt
    true
    >>> _parse_date_str('12 aug 2021') == dt
    true
    """
    try:
        # English date '12 aug 2021'
        dt = datetime.strptime(date_str, '%d %b %Y')
    except ValueError as e:
        # Spanish date '12 ago 2021'
        d_str, m_es_str, y_str = date_str.strip().split()
        m_num_str = date_funcs.month_esp_to_num_str_short(m_es_str.lower())
        date_str = '{}/{}/{}'.format(d_str, m_num_str, y_str)
        dt = datetime.strptime(date_str, '%d/%m/%Y')
    return dt


def get_corespondence_from_list_tabla_comunicados_new(resp_correspondence_text: str) -> List[CorrespondenceDocParsed]:
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank('(?si)<table[^>]+id="tablaComunicadosNew".*?</table>',
                                           resp_correspondence_text)

    rows = re.findall('(?si)<tr.*?</tr>', corr_table)
    for row in rows:
        cells = re.findall('(?si)<td.*?</td>', row)
        if len(cells) < 5:
            continue
        # from javascript:detalleComunicado('0','202005280046500009570','',
        # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw');
        # from javascript:detalleComunicadoNew('0','YDWCF5r4kT9gNYIXmviRPwAAAXpYB02Oky_vgoTVRe4##YDWCF5ojIZFgNYIXmiMhkQAAAXpYB02OYGoIPSTHD3U','REFPARAMETROSCOMUNICADO=YDWCF5ojIZFgNYIXmiMhkQAAAXpYB02OYGoIPSTHD3U');
        js_details = extract.re_first_or_blank("javascript:detalleComunicadoNew[(](.*?)[)]", cells[3]).split(',')
        doc_id = js_details[1].replace("'", '')
        # # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw'
        # 'REFPARAMETROSCOMUNICADO=YDWCF5ojIZFgNYIXmiMhkQAAAXpYB02OYGoIPSTHD3U'
        # # refval_complejo_param = js_details[3].replace("'", '')
        ref_parametros_comunicado = js_details[2].replace("'", '')
        amount_str = extract.text_wo_scripts_and_tags(cells[5])  # '937,50' or ''
        currency = convert.to_currency_code(extract.text_wo_scripts_and_tags(cells[6]))
        corr = CorrespondenceDocParsed(
            type=extract.text_wo_scripts_and_tags(cells[4]),  # 'Varios'
            # no info, will get from correspondence's details
            # using get_account_iban_for_correspondence_document
            account_no='',
            # from '28 Jun 2021', '13 ago 2021'
            operation_date=_parse_date_str(extract.text_wo_scripts_and_tags(cells[2]).lower()),
            value_date=None,
            amount=convert.to_float(amount_str) if amount_str else None,
            currency=currency,
            descr=extract.text_wo_scripts_and_tags(cells[3]),  # 'Normativa EMIR Refit'
            extra={
                'amount_str': amount_str,
                'currency': extract.text_wo_scripts_and_tags(cells[6]),  # 'euros' or ''
                'doc_id': doc_id,  # '202005280046500009570'
                # 'REFVAL_COMPLEJO_5386=rfMLzpP4qket8wvOk_iqRwAAAXJf7pZYnm1mjFx3Nrw'
                # 'refval_complejo_param': refval_complejo_param,
                'ref_parametros_comunicado': ref_parametros_comunicado,
            }
        )
        corrs_from_list.append(corr)

    return corrs_from_list


def get_account_iban_for_correspondence_document(resp_text: str) -> Tuple[bool, str]:
    """Parses resp_doc"""
    # '00000000000000000000000' is possible (by web page)
    account_iban = ''
    if '<span class="blau' in resp_text:
        account_iban = extract.re_first_or_blank(
            r'<span class="blau\s*">(.*?)</span>',
            resp_text
        ).replace(' ', '')
    if '<span id="fila5122' in resp_text:
        account_iban = extract.re_first_or_blank(
            r'(?si)<span id="fila5122">(.*?)</span>',
            resp_text
        ).replace(' ', '').replace('\n', '')

    # Handle LACAIXACENTRAL.ES7021003810820200030647,  PolizaGControl.ES3921001812350200118082
    if '.' in account_iban:
        account_iban_parts = account_iban.split('.')
        account_iban = account_iban_parts[1]
        # Check only after split
        if not account_iban.startswith('ES'):
            return False, ''
    return True, account_iban


def get_number_of_correspondence_documents(resp_text: str) -> Tuple[bool, int]:
    total = 0
    if 'tablacorresp' in resp_text:
        # Parses 'Está viendo 15 mensajes de 1820
        total_corresp_str = extract.re_first_or_blank(r"Está viendo \d+ mensajes de (\d+)", resp_text)
        if total_corresp_str:
            total = int(total_corresp_str)
    if 'tablaComunicadosNew' in resp_text:
        # Parses 'data-c-select-initial-text="1-15 de 56'
        # -a 27006: UTE ACTUACIONES ELECTRICAS TENERIFE NORTE: total 0 correspondence document(s)
        # data-c-select-initial-text="1-7 de 0" <----- displays total = 0 !!!!!
        # Let's use 7 as total in this case
        res = re.findall(r'data-c-select-initial-text="\d+-(\d+) de (\d+)"', resp_text)
        if res:
            up_to_comunicados, total_comunicados = int(res[0][0]), int(res[0][1])
            total = max(up_to_comunicados, total_comunicados)

    if not total:
        if 'Selección sin comunicados' in resp_text:
            return True, 0  # No correspondence
        return False, 0
    return True, total


def get_docs_next_page_refval_param(resp_text: str) -> str:
    refval_param = ''
    if 'tablacorresp' in resp_text:
        """Parses
        <a class="next_acumulativo_on "
            href="javascript:paginacionComunicados('f3oxTBSeNQZ_ejFMFJ41BgAAAXJ2crLmtB0eae5RMbE','65','15');"
            >Siguientes</a>"""
        refval_param = extract.re_first_or_blank(
            r"""(?si)javascript:paginacionComunicados\('([^']+)'[^>]+\);">Siguientes""",
            resp_text
        )
    if 'tablaComunicadosNew' in resp_text:
        """Parses
        <a id="enlaceSiguiente" class="c-pagination__pageListCumulative__inner__link" href="javascript:paginacionComunicadosNew('GGcJUQsnJeoYZwlRCycl6gAAAXpblhh89VX5S~foA2U','56','15');">
        Ver siguientes
        </a>"""
        refval_param = extract.re_first_or_blank(
            r"""(?si)javascript:paginacionComunicadosNew\('([^']+)'[^>]+\);">\nVer siguientes""",
            resp_text
        )
    return refval_param


def is_multi_pdf_correspondence(resp_text: str) -> bool:
    is_multi_pdf = 'Páginas' in resp_text
    return is_multi_pdf


class TestParseHelpersRegular(unittest.TestCase):
    resp_text = ''

    @classmethod
    def setUpClass(cls) -> None:
        # from  -u 203070 -a 9422
        cls.resp_text = """SOME SOME 
        <a href="JavaScript:Inicializar('01860172100','LOTOVIC S.L. (EXTINGUIDA)',
        '9725028601721','D0biJ9PQviwPRuIn09C~LAAAAWsr8KzGPIoBVm5CM7c')"  
        class="no_subrayado"  title=""  onClick="this.blur();"><span>
        LOTOVIC S.L. (EXTINGUIDA)</span></a> SOME SOME
         <a href="JavaScript:Inicializar('00300078300','NEGOCIOS DE RESTAURACION DEL SUR S.L.',
    '9725013000783','D0biJ9OLu8gPRuIn04u7yAAAAWsr8KzGD98~OW_UDLc')"  
    class="no_subrayado"  title=""  
    onClick="this.blur();"><span>NEGOCIOS DE RESTAURACION DEL SUR S.L.</span></a>
        <a href="JavaScript:Inicializar('01904887300','L\' ARTE DI MANGIARE SL','9725029048873',
        'clWWWhnrVwtyVZZaGetXCwAAAWsrxa6W30Af7batuSo')"  class="no_subrayado"  
        title=""  onClick="this.blur();"><span>L' ARTE DI MANGIARE SL</span></a>
        """

    def test_parse_companies(self):
        companies = get_companies(ScrapeLogger("TEST", 0, 0), self.resp_text)
        self.assertEqual(len(companies), 3)
        for c in companies:
            print(c)
