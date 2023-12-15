import re
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from .custom_types import Contract

LABORAL_KUTXA_ID = '3035'
ACCOUNT_TO_PROCESS_NAME_CONTENT_MARKERS = ['crédito de pago aplazado', 'cuenta', 'libreta']


def fin_ent_account_id_from_account_no(account_no: str) -> str:
    """
    Used by newweb scraper
    Proivides old-web-compat format (see -a 24431)

    >>> fin_ent_account_id_from_account_no('ES6030350238612380020003')
    '238.0.02000.3'
    """
    fin_ent_acc_id = '{}.{}.{}.{}'.format(
        account_no[-10:-7],
        account_no[-7:-6],
        account_no[-6:-1],
        account_no[-1:]
    )
    return fin_ent_acc_id


def get_companies_tuples(resp_text: str) -> List[Tuple[str, str]]:
    # [('B31210487', 'B31210487 ARFILA S.L.'),
    # ('A31404221', 'A31404221 AS-MOVIL S.A.U.'),
    # ('B31682214', 'B31682214 ESTUDIO DE PROMOCIONES Y EDIFICACIONES T')]
    return re.findall("<OPTION VALUE='(.*?)'>(.*?)<", resp_text)


def get_cuentas_prestamos_params(resp_text: str) -> List[str]:
    """
    Extract cuentas and prestamos (can't detect cuentas only at this level
    Will detect during further processing at get_account_parsed to process cuentas only

    <SELECT class='campo'  id='lcuenta' onClick='return true' name='lcuenta' size='5 '>
    <OPTION value='0200001612@01@020.0.00161.2'>020.0.00161.2 (Cuenta Tesoreria)</OPTION>
    <OPTION value='0200070759@01@020.0.07075.9'>020.0.07075.9 (Cuenta Tesoreria)</OPTION>
    <OPTION value='4524600171@12@452.46.0017.1'>452.46.0017.1 (Pr&eacute;stamo)</OPTION></SELECT>
    -> [(req_param, text), ...]

    <select class="campo" id="lcuenta" onclick="return true" name="lcuenta" size="5">
    <option value="3450040242@01@345.0.04024.2">345.0.04024.2 (Supercuenta)</option>
    <option value="1182666@09@1182666">1182666 (Anticipos de Crédito)</option>
    <option value="2016014877@10@2016014877">2016014877 (Aval)</option></select>
    USD ACC
    <OPTION value='6910023058@26@691.002305.8'>691.002305.8 (Cuenta Ordinaria En Divisas)</OPTION>
    """

    account_signature = r'\d{10}@\d{2}@\d{3}[.]\d{1,2}[.]?\d{4,5}[.]\d'
    accounts_params = [
        acc_param for acc_param in re.findall("(?i)<OPTION value='(.*?)'>", resp_text)
        if re.findall(account_signature, acc_param)
    ]

    return accounts_params


def get_account_parsed(resp_text: str) -> Tuple[AccountParsed, bool]:
    """
    Gets account from page with acc iban, one per page
    """
    # handle case
    # 345.0.04043.7<span style='color:green;'>
    # &nbsp;&nbsp;&nbsp;Cuenta anterior en IparKutxa: 3084-0063-43-6300012089</span>
    # -> '345.0.04043.7'
    financial_entity_account_id = extract.re_first_or_blank(
        '[0-9.]+',
        extract.remove_tags(
            extract.re_first_or_blank(
                r'(?si)Cuenta:</th>\s*<td.*?>(.*?)</td',
                resp_text
            )
        )
    )

    if 'CUENTA INEXISTENTE' in resp_text:
        return {'financial_entity_account_id': financial_entity_account_id}, False

    product_name = extract.re_first_or_blank(
        r'(?si)Producto:</th>\s*<td.*?>(.*?)</td',
        resp_text
    )

    # skip further parsing
    if not any(m in product_name.lower() for m in ACCOUNT_TO_PROCESS_NAME_CONTENT_MARKERS):
        return {'financial_entity_account_id': financial_entity_account_id}, False

    balance = convert.to_float(
        extract.remove_tags(
            extract.re_first_or_blank(
                r'(?si)Saldo actual:</th>\s*<td.*?>(.*?)</td',
                resp_text
            )
        )
    )
    currency = 'USD' if 'en divisas' in product_name.lower() else 'EUR'
    if 'crédito' in product_name.lower() or balance < 0:
        account_type = ACCOUNT_TYPE_CREDIT
    else:
        account_type = ACCOUNT_TYPE_DEBIT

    # <a style="color: #940058; text-decoration:none;"
    # href="javascript:ImprimirJustificante('Consulta de Detalle de Cuenta','020.0.00161.2',
    # '','01/01/1970','ES05','020','57','0200001612', '01')"> &nbsp;&nbsp;- Todos los titulares de la cuenta</a>
    # <br/><br/>
    # <a style="color: #940058; text-decoration:none;"
    # href="javascript:ImprimirJustificante('Consulta de Detalle de Cuenta','020.0.00161.2',
    # 'ALTUNA Y URIA S.A.','01/01/1970','ES05','020','57','0200001612','')">
    # &nbsp;&nbsp;- S&oacute;lo yo c&oacute;mo titular de la cuenta</a>

    company = extract.re_first_or_blank(
        r"'Consulta de Detalle de Cuenta','\d+[^']*','(\w+[^']*)'",
        resp_text
    )

    company_alt = extract.re_first_or_blank(
        r"(?si)<TD class='txtazul' ALIGN='LEFT'>&nbsp;(.*?)</TD>\s*"
        r"<TD>&nbsp;</TD><TD nowrap class='txtazul' ALIGN='LEFT'>&nbsp;01 TITULAR</TD></TR>",
        resp_text
    )

    # '0200001612'
    account_no_raw = financial_entity_account_id.replace('.', '')

    # <tr>
    #     <td nowrap="nowrap" class="txtazul" align="center"> ES05 </td>
    #     <td><img src="/ImgArista/pto_transp.gif" width="3" height="18" alt=""/></td>
    #     <td class="txtazul" align="center">&nbsp;3035&nbsp;</td>
    #     <td><img src="/ImgArista/pto_transp.gif" width="3" height="18" alt=""/></td>
    #     <td nowrap="nowrap" class="txtazul" align="center"> 0020 </td>
    #     <td><img src="/ImgArista/pto_transp.gif" width="3" height="18" alt=""/></td>
    #     <td class="txtazul" align="center"> 57 </td>
    #     <td><img src="/ImgArista/pto_transp.gif" width="3" height="18" alt=""/></td>
    #     <td class="txtazul" align="left">&nbsp;0200001612</td>
    # </tr>

    account_iban_tuple = extract.re_first_or_blank(
        r'(?si)<td[^>]*>([^<]*)</td>\s*<td><img[^>]*></td>\s*<td[^>]*>'
        r'([^<]*)</td>\s*<td><img[^>]*></td>\s*<td[^>]*>([^<]*)</td>\s*'
        r'<td><img[^>]*></td>\s*<td[^>]*>([^<]*)</td>\s*<td><img[^>]*></td>\s*'
        r'<td class="txtazul" align="left">[^<]*({account_no_raw})</td>'.format(
            account_no_raw=account_no_raw), resp_text)
    account_no = ''.join(extract.remove_tags(token).strip() for token in account_iban_tuple)

    account_parsed = {
        'financial_entity_account_id': financial_entity_account_id,
        'account_no': account_no,
        'organization_title': company or company_alt,
        'balance': balance,
        'account_type': account_type,
        'currency': currency,
    }

    return account_parsed, True


def get_contracts_newweb(resp_json: dict) -> List[Contract]:
    """See 040_resp_usuario_with_contracts.json"""
    contracts = []  # type: List[Contract]
    # 1st contract will be used as is (no need to switch)
    current_contract = Contract(
        org_title=resp_json['usuario']['razonSocial'],
        cif=resp_json['usuario']['nif'],
        id=''
    )
    contracts.append(current_contract)
    admin_dict = resp_json['usuario'].get('administrador', {})
    for admin_dict_i in admin_dict.get('administrados', []):
        contract = Contract(
            org_title=admin_dict_i['nombre'],
            cif=admin_dict_i['cif'],
            id=admin_dict_i['id']
        )
        contracts.append(contract)
    return contracts


def get_accounts_parsed_newweb(resp_json: dict) -> Tuple[bool, List[AccountParsed]]:
    """Parses dev_newweb/resp_accs.json
    :returns (is_success, accounts)
    """
    accounts_parsed = []  # type: List[AccountParsed]
    ok = resp_json.get('resultado') == 0
    for acc_dict in resp_json.get('cuentas', []):
        if acc_dict.get("categoriaId", '') != "1":
            continue  # not a current account

        account_no = acc_dict['numero']  # 'ES4330350045270450086742'
        balance = acc_dict['saldo']['cantidad']
        currency = acc_dict['saldo']['moneda']  # 'EUR'
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        position_id_param = acc_dict['id']  # '1', '5'
        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id_from_account_no(account_no),
            'account_no': account_no,
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'position_id_param': position_id_param
        }
        accounts_parsed.append(account_parsed)
    return ok, accounts_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    mov_table_html = extract.re_first_or_blank(
        """(?si)<form name="frm">\s*<table[^>]+>.*</table>""",
        resp_text
    )
    return []


def get_movements_parsed_from_excel(resp_excel_text: str,
                                    fin_ent_account_id: str,
                                    is_foreign_currency: bool,
                                    logger: ScrapeLogger) -> List[MovementParsed]:
    """
    :param resp_excel_text: look at the ./dev/Excel_AS_TABLE_CHECK_TXT.xls
    :param fin_ent_account_id
    :param logger: scrape logger
    """

    # there are 2 tables, select second
    if not is_foreign_currency:
        # EUR
        mov_table_html = extract.re_first_or_blank(
            "(?si)<TABLE><TR><TD align='center'.*</TABLE>",
            resp_excel_text
        )
        temp_balance_initial_str = extract.re_first_or_blank(
            '(?i)<TD>Saldo anterior:</TD><TD>(.*?)</TD>',
            resp_excel_text
        )
    else:
        # USD
        mov_table_html = extract.re_first_or_blank(
            "(?si)<table[^>]+><tr><td colspan='6'><img src='.*</table>",
            resp_excel_text
        )
        temp_balance_initial_str = extract.re_first_or_blank(
            '(?i)<TD><b>Saldo anterior:</b></TD><TD>(.*?)</TD>',
            resp_excel_text
        )

    # init balance
    if not temp_balance_initial_str:
        logger.error("{}: can't parse temp_balance_initial. Skip movements parsing. RESPONSE:\n{}".format(
            fin_ent_account_id,
            resp_excel_text
        ))
        return []

    temp_balance_initial = convert.to_float(
        temp_balance_initial_str
    )

    temp_balance_prev = temp_balance_initial

    table_rows = re.findall('(?i)<TR.*?</TR>', mov_table_html)
    movements_parsed = []
    if not is_foreign_currency:
        mov_rows = table_rows[1:]  # drop table header
    else:
        mov_rows = table_rows[2:]  # drop table header

    for row in mov_rows:
        try:
            movement = {}  # type: MovementParsed
            cells = [extract.remove_tags(cell_html) for cell_html in re.findall('(?i)<TD.*?/TD>', row)]
            # cells = [
            #     extract.re_first_or_blank('(?i)<TD.*?>(.*?)</TD>', cell_html).strip()
            #     for cell_html in cell_htmls
            # ]  # type: List[str]

            movement['operation_date'] = cells[0].replace('-', '/').strip('.')
            movement['value_date'] = cells[3].replace('-', '/').strip('.')
            movement['description'] = cells[2].strip()
            # =+723945/100 -> 7239.45
            movement['amount'] = extract.eval_xls_formula_safely(cells[4])

            # possible case: no temp_balance - get it using temp_balance_prev
            temp_balance_or_blank = ''
            # USD mov has no temp balance
            if len(cells) >= 7:
                temp_balance_or_blank = cells[6]
            if temp_balance_or_blank:
                movement['temp_balance'] = round(
                    extract.eval_xls_formula_safely(temp_balance_or_blank),
                    2
                )
            else:
                movement['temp_balance'] = round(temp_balance_prev + movement['amount'], 2)
            temp_balance_prev = movement['temp_balance']

            movements_parsed.append(movement)
        except Exception as e:
            pass

    # Return currently scraped movements without modifications
    # If temp_balance_initial != 0
    if temp_balance_initial:
        return movements_parsed

    # Probable case: wrong zero-value saldo initial in the excel response (Saldo anterior:	0,00+ EUR instead of != 0)
    # Solution: re-calculate temp balances from the last movement
    temp_bal_next_correct = None
    temp_bal_fixed_logger_msg = ''
    for i in range(len(movements_parsed) - 1, -1, -1):
        if temp_bal_next_correct is None:
            temp_bal_next_correct = movements_parsed[i]['temp_balance']
            continue

        temp_balance = round(temp_bal_next_correct - movements_parsed[i + 1]['amount'], 2)
        if movements_parsed[i]['temp_balance'] != temp_balance:
            temp_bal_fixed_logger_msg += 'fixed wrong temp_balance for mov idx {}: {} to {}'.format(
                i,
                movements_parsed[i],
                temp_balance
            )
        movements_parsed[i]['temp_balance'] = temp_balance
        temp_bal_next_correct = temp_balance

    if temp_bal_fixed_logger_msg:
        logger.info(
            '{}: the response with movements contains wrong saldo initial. '
            'Fixed automatically: {}\nRESPONSE:\n{}'.format(
                fin_ent_account_id,
                temp_bal_fixed_logger_msg,
                resp_excel_text,
            )
        )
        ...

    # movements_parsed with re-calculated balances
    return movements_parsed


def get_movements_parsed_newweb(resp_json: dict) -> List[MovementParsed]:
    """
    Parses dev_newweb/resp_movs.json
    Each mov:
    {
      "alias": "CUENTA PROFESIONAL",
      "apunteContable": "0000001",
      "categoriaId": "30",
      "concepto": "PAGO PARCIAL 1725+1764",
      "cuenta": "0450086742",
      "cuentaId": "0",
      "entidad": {
        "iconoUrl": "https://lkweb.laboralkutxa.com/entidades/PRV72400003035-65.png",
        "id": "PRV72400003035"
      },
      "fecha": "2020-12-16T11:00:00Z",
      "importe": {
        "cantidad": -12141.82,
        "moneda": "EUR"
      },
      "orden": 1,
      "referenciaMovimiento": "201216V0168573",
      "saldoPosterior": {
        "cantidad": 17449.18,
        "moneda": "EUR"
      },
      "tipoOperacion": "transferenciaEmitida"
    },
    """
    movs_parsed_desc = []  # type: List[MovementParsed]
    for mov_dict in resp_json['movimientos']:
        # '2020-12-16T11:00:00Z' -> '20201216' (also appropriate datetime format)
        operation_date = mov_dict['fecha'].split('T')[0].replace('-', '')  # '20220504'
        value_date = (mov_dict['fechaValor'].split('T')[0].replace('-', '')
                      if 'fechaValor' in mov_dict
                      else operation_date)
        description = mov_dict['concepto']
        amount = mov_dict['importe']['cantidad']  # -12141.82
        temp_balance = mov_dict['saldoPosterior']['cantidad']
        mov = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
        }
        movs_parsed_desc.append(mov)
    return movs_parsed_desc
