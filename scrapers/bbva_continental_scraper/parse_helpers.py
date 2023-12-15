import re
from typing import List, Tuple

from custom_libs import extract
from project.custom_types import (
    ACCOUNT_NO_TYPE_UNKNOWN, ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    AccountParsed, AccountScraped, MovementParsed,
)


def _to_float(v: str) -> float:
    return float(v.replace(',', ''))


def get_currency_code(currency_raw: str) -> str:
    curr_to_code = {
        'dolares': 'USD',
        'euros': 'EUR',
        'soles': 'PEN',
        'pounds': 'GBP',
    }
    curr = currency_raw.lower()
    if curr not in curr_to_code:
        raise Exception("Can't detect correct currency code from '{}'".format(currency_raw))

    return curr_to_code[curr]


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    companies_htmls_tuples = re.findall(
        r'(?si)<div class="titulo-acordion" id="acordion\d+"(.*?)'
        r'(<div class="contenedor-seccion">|</html>)',
        resp_text
    )

    for company_html in [res[0] for res in companies_htmls_tuples]:
        # '313,877.46' => 313877.46

        organization_title = extract.re_first_or_blank(
            '<span class="descripcion">([^<]+)</span>',
            company_html
        )
        accounts_htmls = [
            res[1] for res in re.findall(
                '(?si)<tr class="(even|odd)">(.*?)</tr>',
                company_html
            )
        ]
        for acc_html in accounts_htmls:
            # <tr class="even">
            #   <td class="ta_c">
            #     <a class="enlace" href="javascript:llamada(
            # 'OperacionCBTFServlet?proceso=posicion_global_prUX&operacion=movimientos_ctas_op_ux&accion=movimientos
            # ', '01$001103770100029767$Saldo-Movimiento','CUENTA CORRIENTE')">
            #       0011-0377-01-00029767
            #     </a>
            #    </td>
            #  <td class="ta_l">CUENTA CORRIENTE</td>
            # <!-- <td class="ta_l">COMSA INSTALACIONES  Y SISTEMAS INDUSTRIA LES SA SUCURSAL EN</td> -->
            #   <td class="ta_r">75,970.47</td>
            #   <td class="ta_r">75,970.47</td>
            #   <td class="ta_c">DOLARES</td>
            # </tr>
            cells = re.findall('(?si)<td.*?>(.*?)</td>', acc_html)
            # filter hidden info that duplicates useful acc info
            if len(cells) < 6:
                continue

            fin_ent_account_id = extract.remove_tags(cells[0])
            if '<a class="enlace"' not in cells[0]:
                # no link to details? not a cuenta
                # e.g. trajetas
                continue
            balance = _to_float(cells[3])  # balance_contable == real
            balance_disponible = _to_float(cells[4])  # available with credit

            # DOLARES -> USD, SOLES -> PEN, EUROS  -> EUR, POUNDS -> GBP
            currency = get_currency_code(cells[5])

            account_type = (ACCOUNT_TYPE_DEBIT
                            if balance == balance_disponible
                            else ACCOUNT_TYPE_CREDIT)

            account_parsed = {
                'organization_title': organization_title,
                'account_no': fin_ent_account_id,
                'financial_entity_account_id': fin_ent_account_id,
                'balance': balance,
                'currency': currency,
                'account_type': account_type,
                'country_code': 'PER',  # Peru
                'account_no_format': ACCOUNT_NO_TYPE_UNKNOWN
            }

            accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_dropdown_ids(resp_text: str,
                     accounts_scraped: List[AccountScraped]) -> List[Tuple[AccountScraped, str]]:
    accs_and_dropdown_ids = []  # type: List[Tuple[AccountScraped, str]]
    dropdown_ids = re.findall(r'<option value="(\d+@\w+\d+)"', resp_text)
    for acc in accounts_scraped:
        fin_ent_acc_id_digits = acc.FinancialEntityAccountId.replace('-', '').strip()
        # find 0011-0377-01-00029759 in 6@PEN00110377960100029759
        for dropdown_id in dropdown_ids:
            if fin_ent_acc_id_digits[-10:] in dropdown_id:
                accs_and_dropdown_ids.append((acc, dropdown_id))
                break

    return accs_and_dropdown_ids


def get_req_mov_excel_idx(resp_text: str) -> int:
    """Parses var UrlVerExcel      = "OperacionCBTFServlet?proceso=tlcl_sym_histmov_pr_multipais&operacion
    =tlcl_sym_hmhistoricomovimientos_op_multipais&accion=verExcel&numOPRequest=" + (parseInt('5') + 1);
    """
    req_excel_url_num_tpl = extract.re_first_or_blank(
        r"UrlVerExcel.*?parseInt\('(\d+)'\)\s+[+]\s+(\d+)",
        resp_text
    )
    if not len(req_excel_url_num_tpl):
        return -1  # err marker

    return int(req_excel_url_num_tpl[0]) + int(req_excel_url_num_tpl[1])


def get_movements_parsed_from_excel_html(resp_text: str,
                                         account_balance: float) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]
    rows = re.findall('<tr.*?>(.*?)</tr>', resp_text)

    temp_balance = account_balance

    # process from the end to use
    # helpers like 'Saldo Final: 06-11-2018' in cells[4]
    # align temp_balance by dates
    for row in reversed(rows):
        cells = re.findall('<td.*?>(.*?)</td>', row)

        # too shot row? - this is not a movement
        if len(cells) < 7:
            continue

        if 'Saldo Final' in cells[4]:
            temp_balance = _to_float(cells[5])
            continue

        operation_date = cells[0].replace('-', '/').strip()
        value_date = cells[1].replace('-', '/').strip()

        # no dates? - this is not a movement
        if not (operation_date and value_date):
            continue

        # cell is not a number? - this is not a movement
        try:
            amount = _to_float(cells[5])
        except:
            continue

        description = re.sub(r'\s+', ' ', cells[4].strip())

        movement = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(movement)
        temp_balance = round(temp_balance - amount, 2)

    return movements_parsed_desc
