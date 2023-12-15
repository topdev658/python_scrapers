import re
import urllib.parse
from typing import List

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from .custom_types import ContractSwitchParams


def get_selected_account_id(resp_text: str) -> str:
    """Parses
    <select class="combo" name="GCUENTA" id="GCUENTA">
        <option value="Sel" >Seleccione una cuenta</option>
        <option value="01300108000000910100064657" selected="selected">
            0130 0800 91 0100064657 - C/C FINANCIERA - EUR
        </option>
        <option value="01300408000000980400007615">
            0130 0800 98 0400007615 - CTO.GAR.PER.EMP - EUR
        </option>
    </select>
    """
    selected_id = extract.re_first_or_blank(
        r"""(?si)<select[^>]*name="GCUENTA" id="GCUENTA"[^>]*>.*?<option value="(\d+)"\s+selected="selected">""",
        resp_text
    )
    return selected_id


def get_company_title(resp_text: str) -> str:
    return extract.re_first_or_blank(
        r'(?si)<div class="wa_perso">.*?<span class="bar_perso">.*?</span>\s*<span>(.*?)<',
        resp_text
    )


def get_contracts_params(resp_text: str, base_url: str, logger: ScrapeLogger) -> List[ContractSwitchParams]:
    if 'Seleccione el contrato con el que desea operar' not in resp_text:
        return []

    contracts_switch_params = []  # type: List[ContractSwitchParams]
    forms_ids = re.findall(r'form id="(Cliente\d+)"', resp_text)
    for form_id in forms_ids:
        action_url, req_params = extract.build_req_params_from_form_html_patched(
            resp_text,
            form_id=form_id
        )
        if not (action_url and req_params):
            logger.error(
                "WRONG LAYOUT. Can't parse contract params for form_id={}. "
                "RESPONSE:\n{}\n".format(
                    form_id,
                    resp_text
                )
            )
            continue

        req_url = urllib.parse.urljoin(base_url, action_url)
        contract_switch_params = ContractSwitchParams(
            url=req_url,
            req_params=req_params,
            title=req_params.get('FIT_CTT_NOMBRE_CONTRATO', '').strip()
        )
        contracts_switch_params.append(contract_switch_params)

    return contracts_switch_params


def get_accounts_parsed(resp_text: str, logger: ScrapeLogger) -> List[AccountParsed]:
    accounts_debit_table = extract.re_first_or_blank('(?si)<h2>Cuentas</h2>.*?</table>', resp_text)
    accounts_credit_table = extract.re_first_or_blank('(?si)<h2>Financiación</h2>.*?</table>', resp_text)

    accounts_htmls = [(acc_html, ACCOUNT_TYPE_DEBIT)
                      for acc_html in re.findall('(?si)<tr[^>]*class="row.*?</tr>', accounts_debit_table)]
    accounts_htmls.extend([(acc_html, ACCOUNT_TYPE_CREDIT)
                           for acc_html in re.findall('(?si)<tr[^>]*class="row.*?</tr>', accounts_credit_table)
                           if 'FIN.EXPORT' not in acc_html and 'FIN.IMPORT' not in acc_html])

    accounts_parsed = []

    for account_html, account_type in accounts_htmls:

        # <tr class="row_branco" id="filaTabla_0">
        # <td class=" "  width="25%" id="columnaTabla_0_0" colspan="">
        # 			<a class="linkLar" id="link_0" title="Ver más información">0130 0012 69 0150189984</a>
        # </td>
        # <td class=" "   id="columnaTabla_1_0" colspan="">
        #                C/C NORMAL
        # </td>
        # <td class=" "   id="columnaTabla_2_0" colspan="">
        #                EUR
        # </td>
        # <td class="importeTabla "   id="columnaTabla_3_0" colspan="">
        #                2.036,23
        # </td>
        # <td class=" "   id="columnaTabla_4_0" colspan="">
        #
        # </td>
        # <td class="td_form" style="display:none">
        #     <form id="frmDetalle00" name="frmDetalle00" target="" action="/BEWeb/0130/0130/oper5838_d_mcd.action"
        # method="post" class="" enctype="application/x-www-form-urlencoded">
        #         <input name="LLAMADA" type="hidden" value="D2C523S0C3F0C0F1D021" />
        #         <input name="CLIENTE" type="hidden" value="0130060779" />
        #             <input name="IDIOMA"  id="IDIOMAfrmDetalle00"  type="hidden" value="01" />
        #         <input name="CAJA"    type="hidden" value="0130" />
        #         <input name="OPERAC"  type="hidden" value="9827" />
        #         <input name="CTASEL"  type="hidden" value="" />
        #         <input name="CTAFOR"  type="hidden" value="" />
        #             <input type="hidden" name="CAMINO" id="frmDetalle00-CAMINO" value="0130"/>
        #             <input type="hidden" name="GCUENTA" id="frmDetalle00-GCUENTA" value="01300100120000690150189984"/>
        #             <input type="hidden" name="ultimosMvtosCheck" id="frmDetalle00-ultimosMvtosCheck" value="0"/>
        #     </form>
        #     </td>
        # </tr>

        # '0130 0012 69 0150189984'
        fin_ent_acc_id = extract.re_first_or_blank(r'(?si)id="columnaTabla_0.*?>\s*<a.*?>(.*?)<', account_html).strip()
        if not fin_ent_acc_id:
            logger.warning('Incorrect cuenta: {}.\n\nNo link to details. Skip'.format(account_html))
            continue
        # 'ES7401300012690150189984'
        account_iban = iban_builder.build_iban('ES', fin_ent_acc_id)
        # 'EUR'
        currency = extract.re_first_or_blank('(?si)id="columnaTabla_2.*?>(.*?)<', account_html).strip()
        # 2036.23
        balance = convert.to_float(extract.re_first_or_blank('(?si)id="columnaTabla_3.*?>(.*?)<',
                                                             account_html).strip())
        # credit accounts balances are inverted
        if account_type == ACCOUNT_TYPE_CREDIT:
            balance = -balance

        # 'C/C NORMAL'
        description = extract.re_first_or_blank('(?si)id="columnaTabla_1.*?>(.*?)<', account_html).strip()
        form_id = extract.re_first_or_blank('<form id="(.*?)"', account_html)

        # ('/BEWeb/0130/0130/oper5838_d_mcd.action',
        # {'CTASEL': '', 'LLAMADA': 'D2C523S0C3F0C0F1D021', 'ultimosMvtosCheck': '0', 'CTAFOR': '', 'IDIOMA': '01',
        #  'OPERAC': '9827', 'CAMINO': '0130', 'CAJA': '0130', 'GCUENTA': '01300100120000690150189984',
        #  'CLIENTE': '0130060779'})
        mov_req_url_raw, mov_req_params = extract.build_req_params_from_form_html(account_html, form_id=form_id)

        account_parsed = {
            'account_no': account_iban,
            'financial_entity_account_id': fin_ent_acc_id,
            'currency': currency,
            'balance': balance,
            'account_type': account_type,
            'mov_req_url_raw': mov_req_url_raw,  # '/BEWeb/0130/0130/oper5838_d_mcd.action'
            'mov_req_params': mov_req_params
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _get_value_date_from_raw(value_date_raw: str, operation_date: str) -> str:
    """
    convert 06/03 to 06/03/2017, get date from operation_date
    """
    value_date_raw_digits = value_date_raw.split('/')

    # year already included
    if len(value_date_raw_digits) == 3:
        return value_date_raw

    operation_date_digits = operation_date.split('/')
    # glue with year from operation date
    value_date = '/'.join([value_date_raw_digits[0], value_date_raw_digits[1], operation_date_digits[-1]])

    return value_date


def get_movements_parsed(resp_text: str, fin_ent_account_id: str,
                         logger: ScrapeLogger) -> List[MovementParsed]:
    mov_htmls = re.findall('(?si)<tr class="row.*?</tr>', resp_text)

    movements_parsed = []  # type: List[MovementParsed]

    for mov_html in mov_htmls:
        operation_date = extract.re_first_or_blank(
            '(?si)id="columnaTabla_0.*?>(.*?)<', mov_html
        ).strip().replace('-', '/')  # 06/03/2017

        value_date_raw = extract.re_first_or_blank(
            '(?si)id="columnaTabla_1.*?>(.*?)<', mov_html
        ).strip().replace('-', '/')  # 06/03

        try:
            value_date = _get_value_date_from_raw(value_date_raw, operation_date)
        except:
            # wrong layout -> this is not a cuenta (current account) -> not necessary to get movements
            logger.info(
                '{}: parse movements: another layout. These are not movements of a cuenta. Skip parsing'.format(
                    fin_ent_account_id
                )
            )
            return []

        descr = extract.remove_tags(
            extract.re_first_or_blank('(?si)id="columnaTabla_2.*?>(.*?)</td', mov_html).strip()
        )

        amount = convert.to_float(
            extract.re_first_or_blank('(?si)id="columnaTabla_3.*?>(.*?)<', mov_html).strip()
        )
        temp_balance = convert.to_float(
            extract.re_first_or_blank('(?si)id="columnaTabla_4.*?>(.*?)<', mov_html).strip()
        )

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
