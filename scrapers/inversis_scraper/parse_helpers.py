import re
from typing import List

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import AccountParsed, MovementParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT
from .custom_types import AccountFromDropdown


def get_id_tds_param(resp_text: str) -> str:
    id_tds = extract.re_first_or_blank(
        'var _id_tds = "(.*?)"',
        resp_text
    )
    return id_tds


def get_fin_ent_acc_ids_from_dropdown(resp_text: str) -> List[str]:
    """No balance available here. Get it later
    :returns [fin_ent_account_ids]
    Parses:
    var aCuentas = [
        ["","","A","S"],
        ["0029493443","CUENTA EFECTIVO - 0232-0105-00-0029493443 - VIA CELERE DESARROLLOS INMOBIL",
        "A",
        "N",
        "EUR"]
        ];
    """
    accounts_html = extract.re_first_or_blank(r'(?si)var aCuentas\s*=\s*\[(.*?)];', resp_text)
    fin_ent_account_ids = re.findall(r'\["(\d+)"', accounts_html)  # ['0029493443', ...]
    return fin_ent_account_ids


def get_account_from_dropdown(resp_json: dict) -> AccountFromDropdown:
    """
    See dev/resp_acc_from_dropdown.json
    Parses
    {
      "BODY": {
        "RESPUESTA_BACKOFFICE": {
          "DESCRIPCION_RESPUESTA": "PROCESO FINALIZADO CORRECTAMENTE",
          "CODIGO_RESPUESTA": "0"
        },
        "DATOSSALIDA": {
          "PETICION_CUENTA": {
            "CONJUNTODATOSCUENTA": {
              "DATOSCUENTA": {
                "CODIGO_INSTITUCION": "5000",
                "DIGITO_CONTROL": "00",
                "NUMERO_CUENTA_PADRE": "",
                "INSTITUCION_COLECTIVA": "5358217",
                "DESCRIPCION_ESTADO_CUENTA": "ACTIVADA",
                "NUMERO_CUENTA": "0029493443",
                "INDICADOR_CUENTA_GESTIONADA": "",
                "ESTADO_CUENTA": "A",
                "DESCRIPCION_LARGA": "VIA CELERE DESARROLLOS INMOBIL",
                "ENTIDAD_CUENTA": "0232",
                "NUMERO_CUENTA_EXTERNA": "0029493443",
                "DECIMALES_DIVISA_INSTITUCION": "2",
                "SUCURSAL_CUENTA": "0105",
                "DIVISA_CUENTA": "EUR",
                "DIVISA_INSTITUCION": "EUR",
                "TIPO_CUENTA": "AG"
              },
              "DATOSPRODUCTO": {
                "DESCRIPCION_TIPO_PRODUCTO": "CUENTA EFECTIVO",
                "TIPO_ENTIDAD": "CE",
                "CODIGO_PRODUCTO": "0232-0105-00-0029493443",
                "TIPO_PRODUCTO": "CC000",
                "ALIAS": ""
              }
            }
          }
        }
      }
    }

    """
    data = resp_json['BODY']['DATOSSALIDA']['PETICION_CUENTA']['CONJUNTODATOSCUENTA']
    acc_from_dropdown = AccountFromDropdown(
        fin_ent_account_id=data['DATOSCUENTA']['NUMERO_CUENTA'],
        currency=data['DATOSCUENTA']['DIVISA_CUENTA'],
        codigo_insitucion_param=data['DATOSCUENTA']['CODIGO_INSTITUCION'],
        divisa_institucion_param=data['DATOSCUENTA']['DIVISA_INSTITUCION'],
        institucion_collectiva_param=data['DATOSCUENTA']['INSTITUCION_COLECTIVA'],
        product_code=data['DATOSPRODUCTO']['CODIGO_PRODUCTO'],  # '0232-0105-00-0029493443'
        tipo_cuenta_param=data['DATOSCUENTA']['TIPO_CUENTA']
    )
    return acc_from_dropdown


def get_account_parsed(
        resp_text: str,
        account_from_dropdown: AccountFromDropdown) -> AccountParsed:
    """
    Parses resp_movs to get balance information
    """
    balance_str = extract.remove_tags(extract.re_first_or_blank(
        '(?si)Saldo Final.*?<td[^>]*>(.*?)</td>',
        resp_text
    ))
    balance = convert.to_float(balance_str)
    account_no = iban_builder.build_iban('ES', account_from_dropdown.product_code)
    account_parsed = {
        'account_no': account_no,
        'financial_entity_account_id': account_from_dropdown.fin_ent_account_id,
        'currency': account_from_dropdown.currency,
        'balance': balance,
        'account_type': ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT,
    }

    return account_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movs_parsed_asc = []  # type: List[MovementParsed]
    rows = re.findall('(?si)<tr.*?</tr>', resp_text)
    for row in rows:
        cells = [extract.text_wo_scripts_and_tags(c) for c in re.findall(r'(?si)<td.*?</td\s*>', row)]
        if len(cells) != 7:
            continue

        operation_date = cells[0]  # '09/10/2020'
        value_date = cells[1]  # '09/10/2020'
        descr = cells[3]
        amount = convert.to_float(cells[5])
        temp_balance = convert.to_float(cells[6])
        mov_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
        }
        movs_parsed_asc.append(mov_parsed)

    return movs_parsed_asc
