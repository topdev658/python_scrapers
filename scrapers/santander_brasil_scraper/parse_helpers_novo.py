from custom_libs import convert
from custom_libs import extract
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
    AccountParsed,
)


def get_view_state_param(resp_text: str) -> str:
    return extract.re_first_or_blank(
        '(?si)name="javax.faces.ViewState"[^>]+value="(.*?)"',
        resp_text
    )


def get_cuenta_page_form_geral_id_param(resp_text: str) -> str:
    return extract.re_first_or_blank(r"Conta\s+Corrente.*?id:'formGeral:(.*?)'", resp_text)


def get_recent_movs_form_geral_id_param(resp_text: str) -> str:
    return extract.re_first_or_blank(r'>Extratos<.*?<a[^>]+name="formGeral:(.*?)">Consultar', resp_text)


def get_ticket_param(resp_text: str) -> str:
    return extract.re_first_or_blank("'Ticket','(.*?)'", resp_text)


def get_account_parsed(resp_text: str, fin_ent_acc_id: str) -> AccountParsed:
    acc_bal_str = extract.re_first_or_blank(
        '(?s)Saldo Disponível[^R$]*?R[$](.*?)</span>',
        resp_text
    )
    if not acc_bal_str:
        return {}

    account_balance = convert.to_float(acc_bal_str)

    credit_limit = 0.0
    credit_limit_str = extract.re_first_or_blank(
        '(?s)Limite[^R$]*?R[$](.*?)</span>',
        resp_text
    ).strip()
    if credit_limit_str:
        credit_limit = convert.to_float(credit_limit_str)

    account_parsed = {
        'account_no': fin_ent_acc_id,
        'account_type': ACCOUNT_TYPE_CREDIT if credit_limit else ACCOUNT_TYPE_DEBIT,
        'currency': 'BRL',  # Brasilian real
        'balance': account_balance,
    }
    return account_parsed
