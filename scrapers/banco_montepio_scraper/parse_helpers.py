import re
from typing import Dict, List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import MovementParsed, AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT
from .custom_types import ReqAccParams

EXTENDED_DESCRIPTION_DETAILS = [
    'Local',
    'Hora',
    'Referência',
]


def get_val_by_label(resp_text: str, title: str) -> str:
    val = extract.re_first_or_blank(r'(?si){}</td>\s*<td.*?>(.*?)</td>'.format(title), resp_text)
    return val


def get_next_page_ix(resp_text: str) -> str:
    ix_str = extract.re_last_or_blank(r"javascript:gotopage\('(\d+)'\)", resp_text)
    return ix_str


def get_digits_to_codes(resp_text: str) -> Dict[str, str]:
    digits_and_codes = re.findall(r"""value="(\d)" onclick="doclick2\('(\w{4})'\)""", resp_text)
    digits_to_codes = {d: c for (d, c) in digits_and_codes}
    return digits_to_codes


def get_movs_filtered_dest_page(resp_text: str) -> str:
    """Parses document.formDados.destino.value = "ctaOrdemMovimentosResultadoDC57.jsp"; """
    dest = extract.re_first_or_blank(r'document.formDados.destino.value\s*=\s*"([^"]+)";', resp_text)
    return dest


def get_account_parsed_only_fid_iban(resp_text: str) -> dict:
    account_dict = {
        'financial_entity_account_id': get_val_by_label(resp_text, 'Nº Conta:'),  # '041.10.036760-0 CONTA EMPRESAS'
        'account_no': get_val_by_label(resp_text, 'IBAN:').replace('.', '').strip(),  # 'PT50.0036.0041.99100367600.86'
    }
    return account_dict


def get_account_parsed(resp_text: str, account_dict: dict) -> AccountParsed:
    """Extracts balance-related details from the page with filtered movements"""

    balance = convert.to_float(get_val_by_label(resp_text, 'Saldo Contabilístico'))
    currency = get_val_by_label(resp_text, 'Moeda')
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    organization_title = get_val_by_label(resp_text, 'Nome 1º Titular')
    account_parsed = {
        'organization_title': organization_title,
        'financial_entity_account_id': account_dict['financial_entity_account_id'],
        'account_no': account_dict['account_no'],
        'balance': balance,
        'currency': currency,
        'account_type': account_type,
    }
    return account_parsed


def get_numcta_ordem_param(fin_ent_account_id: str) -> str:
    return re.sub(r'\D', '', extract.re_first_or_blank(r'[\d.-]+', fin_ent_account_id))


def get_req_acc_params(fin_ent_account_id: str) -> ReqAccParams:
    # '041.10.036760-0 CONTA EMPRESAS' ->

    # '041.10.036760-0'
    num_cta_ordem_param_raw = extract.re_first_or_blank(r'[\d.-]+', fin_ent_account_id)
    # '041100367600'
    num_cta_ordem_param = get_numcta_ordem_param(fin_ent_account_id)
    # 'CONTA EMPRESAS'
    descproduto_in_param = fin_ent_account_id.replace(num_cta_ordem_param_raw, '').strip()
    # "041100367600|041.10.036760-0 CONTA EMPRESAS||CONTA EMPRESAS"
    seleccao_conta_param = '{}|{}||{}'.format(num_cta_ordem_param, fin_ent_account_id, descproduto_in_param)
    req_acc_params = ReqAccParams(
        numCtaOrdem=num_cta_ordem_param,
        descproduto_IN=descproduto_in_param,
        seleccaoConta=seleccao_conta_param
    )
    return req_acc_params


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movements_parsed_asc = []

    movs_table = extract.re_first_or_blank(
        r'(?si)<table width="100%" border="0" cellspacing="2" cellpadding="0">.*?</table>',
        resp_text
    )
    trs = re.findall('(?si)<tr.*?</tr>', movs_table)
    for tr in trs:
        tds = re.findall('(?si)<td.*?</td>', tr)
        if len(tds) != 5:
            continue

        operation_date = extract.remove_tags(tds[0])  # 2019-08-07

        # skip title
        if operation_date == 'Data Mov.':
            continue

        value_date = extract.remove_tags(tds[1])  # 2019-08-07
        description = extract.remove_tags(tds[2])
        amount = convert.to_float(extract.remove_tags(tds[3]))
        temp_balance = convert.to_float(extract.remove_tags(tds[4]))
        id_ = extract.re_first_or_blank(r"onLnkDetalhe\('(\d+)'\);return false;", tds[2])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description.strip(),
            'amount': amount,
            'temp_balance': temp_balance,
            'id': id_,  # will be used for details param
            'has_extra_details': bool(id_)
        }

        movements_parsed_asc.append(movement_parsed)

    return movements_parsed_asc


def get_description_extended(resp_text: str, mov_parsed: MovementParsed) -> str:
    # Similar to AlphaBank (not the same)
    description_extended = mov_parsed['description']

    for det_title in EXTENDED_DESCRIPTION_DETAILS:
        detail = get_val_by_label(resp_text, det_title).strip()
        msg = '{}: {}'.format(det_title, detail).strip()
        description_extended += ' || {}'.format(msg)

    return description_extended.strip()
