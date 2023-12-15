import re
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed


def get_accounts_parsed(resp_text: str) -> List[AccountParsed]:
    """Parses
    <td width="10px"></td>
    <td align="center" width="200px">
        <script>
            formatearCuenta('ES36 3001 0053 0553 1075 0924');
        </script>
    </td>
    <td align="right" width="80px">
        <script>
            formateaImporte('38621.38');
        </script>
    </td>
    <td width="10px"></td>
    <td>
         AGUAS DE MORALEJA U.T.E.
    </td>
    <td class="center" width="20px">
    """
    accounts_parsed = []  # type: List[AccountParsed]
    accs_details = re.findall(
        r"""(?si)formatearCuenta\('(.*?)'\).*?formateaImporte\('(.*?)'\).*<td>(.*?)</td>""",
        resp_text
    )  # type: List[Tuple[str, str, str]]

    for account_no_raw, balance_str, company_title_raw in accs_details:
        balance = float(balance_str)

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        account_parsed = {
            'account_no': account_no_raw.replace(' ', ''),
            'financial_entity_account_id': account_no_raw,  # ES36 3001 0053 0553 1075 0924
            'organization_title': company_title_raw.strip(),
            'balance': balance,
            'currency': 'EUR',
            'account_type': account_type,
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_req_movs_combo_param(resp_text: str, fin_ent_account_id: str) -> str:
    """Parses
    <?xml version="1.0" encoding="ISO-8859-15"?>
    <ajax-response><response><item><name>ES36 3001 0053 0553 1075 0924 | CUENTA
    CORRIENTE</name><value>30010053055310750924</value></item></response></ajax-response>
    """
    return extract.re_first_or_blank(
        '<name>({}.*)</name>'.format(fin_ent_account_id),
        resp_text
    )


def _get_amount_from_cell(cell: str):
    return convert.to_float(extract.re_first_or_blank(r"formateaImporte\('(.*?)'\)", cell))


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    """Parses
    <tr class="TextoNormal" style="display:none;">
    <input type="hidden" name="masDatos" value="false" id="masDatos">
    <td class="tdmargen">&nbsp;  </td>
    <input type="hidden" name="conceptoDetallado" value="01855604" id="conceptoDetallado">
    <td>0000215</td>
    <td>22/07/2019</td>
    <td>22/07/2019</td>
    <td>EMBARGOS OAR<br/></td>
    <td class="right">
                <script>formateaImporte('-9,28');</script>
    </td>
    <td class="right">
                <script>formateaImporte('24.754,19');</script>
    </td>
    <input type="hidden" name="referenciaCorreo" value="" id="referenciaCorreo">
    <td class="center">

    </td>
    <td class="tdmargen">&nbsp;  </td>
    </tr>
    """
    movements_parsed_desc = []  # type: List[MovementParsed]
    table = extract.re_first_or_blank('<(?si)table[^>]+"tabla_listado".*?</table>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', table)
    for tr in trs:
        cells = re.findall('(?si)<td[^>]*>(.*?)</td>', tr)
        if len(cells) != 11:
            continue

        operation_date = cells[2]  # 22/07/2019

        if 'Fecha Operación' in operation_date:
            continue  # skip table title

        value_date = cells[3]
        descr = extract.remove_tags(cells[4])
        amount = _get_amount_from_cell(cells[5])
        temp_balance = _get_amount_from_cell(cells[6])

        mov_parsed = {
            'value_date': value_date,
            'operation_date': operation_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(mov_parsed)

    return movements_parsed_desc
