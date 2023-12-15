import html
import re
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

EXTENDED_DESCRIPTION_DETAILS = [
    'Oficina',
    'Número documento',
    'Identificación del acreedor',
    'Nombre ordenante',
    'Referencia del ordenante',
    'BIC Acreedor',
    'Nombre del deudor',
    'Estado',
    'Fecha de Liquidación',
    'Fecha de Cargo',
    'Cuenta de cargo',
    'Fecha de Devolución',
    'Motivo devolución'
]


def get_selected_account_id(resp_text: str) -> str:
    """Parses
    <select name="GCUENTA" id="GCUENTA" class="flotaIzq">
        <option value="01250100200000382000999846" selected>
            0125-0020-38-2000999846 J MANUEL HERRERO
        </option>
        <option value="01250100200000392001028499">
            0125-0020-39-2001028499 J.M.HERRERO-PERS
        </option>
    </select>
    """
    selected_id = extract.re_first_or_blank(
        r"""(?si)<select name="GCUENTA" id="GCUENTA"[^>]*>.*?<option value="(\d+)" selected>""",
        resp_text
    )
    return selected_id


def get_accounts_parsed(resp_text: str) -> Tuple[bool, List[AccountParsed]]:
    accounts_parsed = []  # type: List[AccountParsed]

    accs_table = extract.re_first_or_blank('(?si)<table[^>]+id="tblResul1".*</table>', resp_text)
    rows = re.findall('(?si)<tr.*?</tr>', accs_table)
    for row in rows:
        cells = re.findall('(?si)<td.*?>(.*?)</td>', row)
        if len(cells) != 3:
            continue

        # 01250100290000492000776565
        fin_ent_acc_id = extract.re_first_or_blank(r'id="DET\d{3}(\d{26})', cells[0])

        # Website now provides ES49-0125-****-**-******6565
        # Let's get the prefix to validate is it current account or not
        account_no_prefix = extract.re_first_or_blank(r'ES[\d-]+', cells[0]).replace('-', '')
        if not account_no_prefix:
            # not a cuenta
            continue
        # 01250029492000776565
        account_no_base = ''.join(
            extract.re_first_or_blank(r'id="DET\d{3}(\d{4})\d{2}(\d{4})\d{4}(\d{12})', cells[0])
        )
        # ES4901250029492000776565, calc explicitly
        account_no = iban_builder.build_iban('ES', account_no_base)

        balance = convert.to_float(cells[2])
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'account_no': account_no,
            'financial_entity_account_id': fin_ent_acc_id,
            'currency': 'EUR',
            'balance': balance,
            'account_type': account_type,
        }
        accounts_parsed.append(account_parsed)

    if not accounts_parsed:
        return False, accounts_parsed

    return True, accounts_parsed


def get_codreanud_param(resp_text: str) -> Tuple[bool, str]:
    c = extract.re_first_or_blank('var codreanuda="(.*?)";', resp_text)
    return bool(c), c


def get_req_params_for_mov_details(resp_text: str, req_movs_params: dict) -> dict:
    params = {
        'GCUENTA': req_movs_params['GCUENTA'],
        'MES': extract.re_first_or_blank(r"var MHoy='(\d+)';", resp_text),  # '10',
        'ANIO': extract.re_first_or_blank(r"var AHoy='(\d+)';", resp_text),  # '2019',
        'OPCION': '1',
        'FECHINI': req_movs_params['FECINI'],  # '01092019',
        'FECHFIN': req_movs_params['FECFIN'],  # '30092019',
        'LLAMADA': req_movs_params['LLAMADA'],
        'CLIENTE': req_movs_params['CLIENTE'],
        'IDIOMA': '01',
        'CAJA': extract.form_param(resp_text, 'CAJA'),
        'OPERAC': extract.form_param(resp_text, 'OPERAC'),
        'CTASEL': '',
        'CTAFOR': '',
        'FECINI': req_movs_params['FECINI'],
        'FECFIN': req_movs_params['FECFIN'],
        'CODREANUD': req_movs_params['CODREANUD'],
        'TIPOSCTAS': '',
        'AUXCODREANUDA': '',
        'TOPEAUXCODREANUDA': '',
        'CONCEPTO2': '',
        'DEDONDE': extract.form_param(resp_text, 'DEDONDE'),  # '5838',
        'ULTDIA': '',
        'SECUENCIA': '',  # 009665 MOV ID
        'FECHMOVI': '',  # 02092019  MOV OP DATE
        'FECHADESDECOMBO': req_movs_params.get('FECHADESDECOMBO', ''),  # 01102019 ?
        'SALDOCTASIG': extract.form_param(resp_text, 'SALDOCTASIG'),
    }
    return params


def get_movements_parsed(resp_text: str) -> Tuple[bool, List[MovementParsed]]:
    """Parses
    resultados5838[ resultados5838.length ] = new Object();
    resultados5838[ resultados5838.length - 1 ].fechmovi2 = "02/09/2019";  # op date
    resultados5838[ resultados5838.length - 1 ].concepto1 = "COMISION COMERCIO                     ";  # type
    resultados5838[ resultados5838.length - 1 ].concepto2 = "COMISION TPV                          ";  # descr
    resultados5838[ resultados5838.length - 1 ].impomovi = "-1,16";
    resultados5838[ resultados5838.length - 1 ].signomovi = "C";
    resultados5838[ resultados5838.length - 1 ].saldcuen = "25.721,42";
    resultados5838[ resultados5838.length - 1 ].fechmovi = "02092019";
    resultados5838[ resultados5838.length - 1 ].secuencia = "009676";
    resultados5838[ resultados5838.length - 1 ].fecvalmo = "31082019";  # val date
    resultados5838[ resultados5838.length - 1 ].fecvalmo2 = "31/08/2019";
    """
    movemens_parsed_asc = []  # type: List[MovementParsed]
    movs_htmls = re.findall('(?si)new Object.*?fecvalmo2.*?";', resp_text)
    # expect movs_htmls or 'no movements' text marker
    if not (movs_htmls or ('NO HAY DATOS PARA ESA SELECCION' in resp_text)):
        return False, []

    for mov_html in movs_htmls:
        values = re.findall(r'=\s*"(.*)";', mov_html)
        amount = convert.to_float(values[3])
        temp_balance = convert.to_float(values[5])
        descr = '{}: {}'.format(values[1].strip(), values[2].strip())
        operation_date = values[0]
        value_date = values[9]
        movement_parsed = {
            'id': values[7],  # secuencia
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movemens_parsed_asc.append(movement_parsed)
    return True, movemens_parsed_asc


def _get_val_by_label(resp_text: str, title: str) -> str:
    val = extract.re_first_or_blank(r'(?si)<dt>{}[:]?</dt>\s*<dd[^>]*>(.*?)</dd>'.format(title), resp_text)
    return val.strip()


def get_description_extended(resp_mov_text: str,
                             resp_extra_details_text: str,
                             mov_parsed: MovementParsed) -> Tuple[bool, str]:
    # N&uacute;mero documento -> Número documento'
    resp_mov_text = html.unescape(resp_mov_text)
    resp_extra_details_text = html.unescape(resp_extra_details_text)
    ok_oficina = False
    ok_others = True if not resp_extra_details_text else False  # we expect other details for non-empty resp

    # Similar to Montepio (not the same)
    description_extended = mov_parsed['description']

    for det_title in EXTENDED_DESCRIPTION_DETAILS:
        if det_title == 'Oficina':
            detail = _get_val_by_label(resp_mov_text, det_title)
            if detail:
                ok_oficina = True
        else:
            detail = _get_val_by_label(resp_extra_details_text, det_title)
            if detail:
                ok_others = True
        msg = '{}: {}'.format(det_title, detail).strip()
        description_extended += ' || {}'.format(msg)

    return ok_oficina and ok_others, description_extended.strip()
