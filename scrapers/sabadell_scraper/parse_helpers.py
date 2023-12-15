import hashlib
import re
import uuid
from typing import Dict, List, Tuple

import xlrd

from custom_libs import convert
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed, \
    CheckParsed, CheckCollectionParsed
from .custom_types import AccountFromDropdown

__version__ = '1.2.0'
__changelog__ = """
1.2.0
_get_account_from_dropdown: reproduce js: balance = 0 if balance_str == ''
1.1.0
use extended AccountFromDropdown
_get_account_from_dropdown
convert_accs_from_dropdown_to_parsed
"""

MOV_EXTENDED_DESCRIPTION_FIELDS = [
    'Oficina origen:',
    'Referencia 1',
    'Referencia 2',
    'Concepto propio :',
    'Concepto común :',
    'Información complementaria'
]


def get_companies_params(resp_text: str) -> List[dict]:
    companies_params = [
        ({'contrato': i, 'userContract': v})
        for i, v in enumerate(re.findall(r'contratos\[i]="(\d+)"', resp_text))
    ]
    return companies_params


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]

    accounts_htmls = re.findall(r'(?si)<div\sid="_CC\d+".*?</table>\s*</div>', resp_text)
    for acc_html in accounts_htmls:
        account_no = extract.re_first_or_blank(r'ES\d{2}.*', acc_html).replace(' ', '').strip()
        balance = convert.to_float(extract.re_first_or_blank(r'<span class="a11[\w]*">\s*([-\+0-9.,]+)', acc_html))
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        balance_w_curr = extract.re_first_or_blank(r'(?si)<span class="a11[\w]*">(.*?)</span', acc_html)
        currency_str = re.split(r'\s+', balance_w_curr.strip())[1]
        # -a 28402 many currencies
        currency = convert.to_currency_code(currency_str)

        organization_title = extract.re_first_or_blank(r'(?si)<td class="a11[\w]*">(.*?)</td', acc_html).strip()

        account_parsed = {
            'account_no': account_no,
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'organization_title': organization_title,
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _get_account_from_dropdown(account_html: str, idx: int) -> AccountFromDropdown:
    """Parses (see dev/10_resp_saldos_y_movs_w_dropdown.html)
    var aliasStr = escape("MEURI");

    var balanceStr = '1282,31';
    if (balanceStr == '') balanceStr = '0';
    iAccounts[0]=new Array('000001143416',
        '5095',
        'DV00001',
        "MEURI SOCIEDAD LIMITADA.",
        '0081',
        '27',
        aliasStr,
        'BSAB ESBB',
        '00815095270001143416',
        '47',
        'ES',
        "CUENTA RELACIÓN",
        balanceStr,
        'EUR',
        "MEURI");
    :param account_html:
    :param idx:
    :return:
    """

    # iAccounts[0]=new Array('000002514463','0085','DV00001',"CP JOSE LUIS ARRESE N 38",'0081','63',aliasStr,
    # 'BSAB ESBB','00810085630002514463','62','ES','CUENTA RELACIÓN');
    # -> ES76 0081 7305 1000 0132 3742 OMESIT, S.L.
    # iAccounts[0]=new Array('000001323742','7305','DV00037',"OMESIT, S.L.",'0081','10',aliasStr,'BSAB ESBB',
    # '00817305100001323742','76','ES','CUENTA EXPANSION NEGOCIOS PLUS'); <-- ',' between "...."
    # OR from (see double quotes and commas)
    # '000002533764','0085','DV00001',"AURORA ENERGY HOLDING, S.L.U.",
    # '0081','69',aliasStr,'BSAB ESBB','00810085690002533764','35','ES',
    # "CUENTA RELACIÓN",balanceStr,'EUR',""'

    arr_str = extract.re_first_or_blank(r'(?si)new Array\((.*?)\);', account_html)
    # Delete account title to avoid wrong parsing due quotes and colons, back comp
    account_html_wo_double_quoted_data = re.sub('".*?"', '', arr_str)
    account_data_list_clean = re.findall("'(.*?)'", account_html_wo_double_quoted_data)
    a = account_data_list_clean
    # Split initial list by commas and clean of quotes, only for account_type
    # ['000002533764',
    # '0085',
    # 'DV00001',
    # 'AURORA ENERGY HOLDING', <-- broken title example
    # ' S.L.U.',
    # '0081',
    # '69',
    # 'aliasStr',
    # 'BSAB ESBB',
    # '00810085690002533764',
    # '35',
    # 'ES',
    # 'CUENTA RELACIÓN', <-- target
    # 'balanceStr',
    # 'EUR',
    # '']
    account_data_list_raw = [re.sub("""^['"]|["']$""", '', x) for x in re.findall('[^,]+', arr_str)]
    balance_str = extract.re_first_or_blank(r"var balanceStr\s*=\s*'(.*?)';", account_html)
    # -a 32501, some accs have balanceStr=''
    # reproduce js: if (balanceStr == '') balanceStr = '0'
    balance = convert.to_float(balance_str) if balance_str else 0
    account_from_dropdown = AccountFromDropdown(
        org_title=account_data_list_raw[3],
        account_no=a[8] + a[7] + a[6],  # 'ES3500810085690002533764'
        idx=idx,
        # 'CUENTA RELACIÓN'
        # 'CUENTA EXPANSIÓN NEGOCIOS'
        # 'CUENTA EXPANSION NEGOCIOS PLUS'
        # 'CUENTA EN DIVISA GESTIONADA'
        # 'CUENTA CORRIENTE'
        account_type_raw=account_data_list_raw[-4],
        currency=account_data_list_raw[-2],
        balance=balance,
    )
    return account_from_dropdown


def get_accounts_from_dropdown(resp_text: str) -> List[AccountFromDropdown]:
    resp_text_clean = re.sub(r'[\t\n]', '', resp_text)
    accounts_htmls = re.findall(r'(?si)var balanceStr.*?iAccounts\[\d+]=new Array\(.*?\);', resp_text_clean)
    accounts_from_dropdown = []  # type: List[AccountFromDropdown]
    for idx, account_html in enumerate(accounts_htmls):
        account_from_dropdown = _get_account_from_dropdown(account_html, idx)
        accounts_from_dropdown.append(account_from_dropdown)

    return accounts_from_dropdown


def convert_accs_from_dropdown_to_parsed(accounts_from_dropdown: List[AccountFromDropdown]) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    for account_from_dropdown in accounts_from_dropdown:
        if 'CUENTA' not in account_from_dropdown.account_type_raw:
            continue
        account_parsed = {
            'account_no': account_from_dropdown.account_no,
            'balance': account_from_dropdown.balance,
            'account_type': ACCOUNT_TYPE_CREDIT if account_from_dropdown.balance < 0 else ACCOUNT_TYPE_DEBIT,
            'currency': account_from_dropdown.currency,
            'organization_title': account_from_dropdown.org_title,
        }
        accounts_parsed.append(account_parsed)
    return accounts_parsed


def parse_movements_from_resp_excel(resp_excel_bytes: bytes) -> Tuple[List[MovementParsed], bool]:
    movements_parsed = []  # type: List[MovementParsed]
    is_too_many_movements = False

    # no movements - no excel, just html
    try:
        book = xlrd.open_workbook(file_contents=resp_excel_bytes)
    except xlrd.XLRDError:
        return movements_parsed, is_too_many_movements

    sheet = book.sheet_by_index(0)

    for row_num in range(6, sheet.nrows):
        movement = {}
        cells = sheet.row_values(row_num)

        movement['operation_date'] = cells[0]

        # handle case if there are over 3000 movements and
        # got excel with additional warning message like
        # Su petición supera el límite máximo de 3.000 movimientos.
        # En el fichero Excel se han incluido los últimos 3.000 movimientos de las fechas solicitadas.
        # Si necesita movimientos anteriores realice una nueva petición de extracto seleccionando las fechas
        # requeridas.
        if not re.match(r'\d+/\d+/\d+', movement['operation_date']):
            is_too_many_movements = True
            continue

        movement['value_date'] = cells[2]
        movement['description'] = re.sub(r'\s+', ' ', cells[1].strip())  # remove redundant spaces
        movement['amount'] = cells[3]
        movement['temp_balance'] = cells[4]

        movements_parsed.append(movement)

    return movements_parsed, is_too_many_movements


def parse_movements_from_html(resp_text: str) -> Tuple[List[MovementParsed], bool, bool]:
    is_too_many_movements = False

    mov_htmls = re.findall('(?si)<tr class="fila.*?</tr>', resp_text)
    if mov_htmls:
        mov_htmls.pop(0)

    movements_parsed = []
    for mov_html in mov_htmls:
        fields = re.findall('(?si)<td.*?>(.*?)</td>', mov_html)
        operation_date = fields[0].strip().replace('-', '/')
        amount = convert.to_float(extract.remove_tags(fields[3]))
        temp_balance = convert.to_float(extract.remove_tags(fields[4]))

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': fields[1].strip().replace('-', '/'),
            'description': ' '.join(extract.remove_tags(fields[2]).split()),
            'amount': amount,
            'temp_balance': temp_balance,
            'mov_details_req_params': "",
            'may_have_receipt': False,
            'receipt_params': "",
            'id': '{}--({}/{})--{}'.format(operation_date, amount, temp_balance, uuid.uuid4())
        }

        detail_params = re.findall(
            r'(?si)window.open\("/txempbs/CUExtractOperationsQueryNew.movementDetail.bs\?(.*?)","new"',
            fields[5]
        )
        if detail_params:
            movement_parsed['mov_details_req_params'] = detail_params[0]

        receipt_params_str = extract.re_first_or_blank(r'(?si)cdoc=window.open\("[^?]*\?(.*?)","new"', fields[5])
        if receipt_params_str:
            movement_parsed['may_have_receipt'] = True
            receipt_params = extract.req_params_as_ord_dict(receipt_params_str)
            receipt_params['concept'] = ''  # was escape(document.myForm.c_2.value)
            movement_parsed['receipt_params'] = receipt_params

        if not re.match(r'\d+/\d+/\d+', movement_parsed['operation_date']):
            is_too_many_movements = True
            continue

        movements_parsed.append(movement_parsed)

    has_more_movs = "javascript:paginate('next')" in resp_text

    return movements_parsed, is_too_many_movements, not has_more_movs


def get_description_extended(resp_text: str,
                             movement_parsed: MovementParsed) -> str:
    """Extracts the description_extended from mov details resp with the rules described below.
    Fields:
    a. 'Concepto'
    b. 'Oficina origen:',
    c. 'Referencia 1',
    d. 'Referencia 2',
    e. 'Concepto propio',
    f. 'Concepto común',
    g. 'Información complementaria'
    The fields must be concatenated to be inserted in ExtendedDescription as you are doing in BBVA. They must be
    concatenated in the order above.
    If a field does not appear in the Detail of the movement,
     it must also be included in the ExtendedDescription as
    "|| ||", so that the ExtendedDescription format will always be the same, whether the fields appear or not.
    """

    description_extended = movement_parsed['description']
    if not resp_text:
        return description_extended

    fields_vals = {}  # type: Dict[str, str]
    trs = re.findall('(?si)<tr.*?</tr>', resp_text)
    for tr in trs:
        # handle tr with th only - or it'll bring expecting exception
        if '<td' not in tr:
            continue

        # '<tr>
        # <td class=a12 width="35%"><b>Referencia 1</b>&nbsp;</td>
        # <td class=a12>
        # <td class=a12 width="65%">0229_2901  029012899790000 01 P EUR  02320129012899790000DEUT05731</td>
        # </tr>
        # <tr>'
        tds = [extract.remove_tags(v) for v in re.findall('(?si)<td.*?</td>', tr)]
        try:
            fields_vals[tds[0]] = tds[1]
        except:
            pass

    extra_info_block = re.findall('(?si)Información complementaria(.*)Cerrar</a>', resp_text)[0]

    # 'Información complementaria'
    #
    # FROM
    # </td>
    # </tr>
    # <tr><td height=15 colspan=3></td></tr>
    # <tr>
    # <td class=a12 colspan=3 width="100%">BENEFICIARIO DE LA TRANSFERENCIA :      INTURCOSA</td></tr>
    # </tr>
    # <tr>
    # <td class=a12 colspan=3 width="100%"></td>
    # <tr>
    # <td class=a12 colspan=3 width="100%">BANCO   :  0081         OFICINA :     5181   CUENTA     :
    # 0001017703</td>
    # </tr>
    # <tr>
    # <td class=a12 colspan=3 width="100%"> IMPORTE :        1.226,50                    COMISIONES :           0,
    # 00 OBSERVACIONES : RESTO PROFORMA 6200318779</td>
    # </tr>
    # <tr><td height=15 colspan=3></td></tr>
    #
    # TO
    # (max 3 spaces)
    # 'BENEFICIARIO DE LA TRANSFERENCIA: INTURCOSA   BANCO: 0081   OFICINA: 5181   CUENTA: 000101770
    # IMPORTE: 1.226,50   COMISIONES: 0,00 OBSERVACIONES: RESTO PROFORMA 6200318779'
    fields_vals['Información complementaria'] = '   '.join(
        [re.sub(r'\s{3}\s*', '   ', re.sub(r':\s+', ': ', re.sub(r'\s+:', ':', extract.remove_tags(v))))
         for v in re.findall('(?si)<td.*?</td>', extra_info_block)
         if extract.remove_tags(v)]
    ).strip()

    for title in MOV_EXTENDED_DESCRIPTION_FIELDS:
        val = fields_vals.get(title, '')
        msg = '{}: {}'.format(title.replace(':', '').strip(), val).strip() if val else ''
        description_extended += ' || {}'.format(msg).rstrip()

    return description_extended


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


def parse_check_collections_from_html(resp_text: str) -> List[CheckCollectionParsed]:
    collection_htmls = re.findall('(?si)<tr class="fila.">.?<td class=a11 align="center">.*?</tr>', resp_text)
    collections_parsed = []  # type: List[CheckCollectionParsed]

    for collection_html in collection_htmls:
        fields = re.findall('(?si)<td.*?>(.*?)</td>', collection_html)
        fls = [extract.remove_tags(field) for field in fields]
        fls[6] = re.findall(r'(?si)<a href=\'javascript:detalle\("(.*)"\)', collection_html)[0]

        hashbase = 'SABADELL{}{}{}{}'.format(
            fls[4],  # cod.remesa
            fls[1],  # nº.docs
            fls[0],  # fecha
            fls[2],  # importe, meter mas
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        has_details = True
        amount = convert.to_float(fls[2])
        state = fls[3].upper()
        """
        if fls[3].upper() in ['ABONADO', 'PROCESADO']:
            state = 'ABONADO'
        elif fls[3].upper() in ['TRANSMITIDO', 'TRANSMITIDO BANCO', 'TRANSMÈS BANC']:
            state = 'TRANSMITIDO'
        elif fls[3].upper() in ['DEVUELTO']:
            state = 'DEVUELTO'
            amount = "-{}".format(amount)
        """

        collections_parsed.append({
            'details_selected_index': fls[6],
            'check_collection': fls[4],
            'collection_date': fls[0],
            'amount': amount,
            'doc_quantity': fls[1],
            'state': state,
            'delivered': bool(fls[5].lower() == "sí"),
            'keyvalue': keyvalue,
            'has_details': has_details,
        })

    return collections_parsed


def parse_checks_from_html(resp_text: str, check_collection: CheckCollectionParsed) -> List[CheckParsed]:
    check_htmls = re.findall('(?si)<tr class="fila.">.?<td class=a11 align="center">.*?</tr>', resp_text)
    checks_parsed = []

    for check_html in check_htmls:
        fields = re.findall('(?si)<td.*?>(.*?)</td>', check_html)
        fls = [extract.remove_tags(field) for field in fields]

        charge_account = '{}{}{}{}'.format(fls[0], fls[1], fls[2], fls[3])
        hashbase = 'SABADELL{}{}{}{}'.format(
            fls[5],
            check_collection['collection_date'],
            charge_account,
            fls[6]
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        amount = convert.to_float(fls[6])
        state = fls[8].upper()
        """
        if fls[8].upper() in ['ABONADO', 'PROCESADO']:
            state = 'ABONADO'
        elif fls[8].upper() in ['TRANSMITIDO', 'TRANSMITIDO BANCO', 'TRANSMÈS BANC']:
            state = 'TRANSMITIDO'
        elif fls[8].upper() in ['DEVOLVIDO', 'DEVUELTO']:
            state = 'DEVUELTO'
            amount = "-{}".format(amount)
        """

        checks_parsed.append({
            'details_link': '',
            'capture_date': check_collection['collection_date'],  # DAF: fls[7] is "Fecha Vencimiento" but is empty
            'check_number': fls[5],
            'charge_account': charge_account,
            'amount': amount,
            'expiration_date': check_collection['collection_date'],  # DAF: fls[7] is "Fecha Vencimiento" but is empty
            'doc_code': fls[4],
            'stamped': False,
            'state': state,
            'has_details': False,
            'keyvalue': keyvalue,
            'charge_cif': '',
            'image_link': None,
            'image_content': None
        })

    return checks_parsed
