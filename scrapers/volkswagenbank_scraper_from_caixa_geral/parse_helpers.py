import re
import urllib.parse
from typing import List, Optional
from urllib.parse import ParseResult

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

# Number of allowed temp_balance errors
TEMP_BALANCE_MAX_ERRORS = 3


def get_selected_account_id(resp_text: str) -> str:
    """Parses
    <select id="GCUENTA" name="GCUENTA" class='autoSub'   >
        <option value="" >Seleccione una cuenta</option>
            <option value="14800100100000920100025438" data-tipo="01" selected="selected">
                ES19 1480 0010 9201 0002 5438 - CONCESIONARIOS
            </option>
            <option value="14804200100000900400042579" data-tipo="42">
                ES61 1480 0010 9004 0004 2579 - POLIZA BB
            </option>
     </select>
    """
    selected_id = extract.re_first_or_blank(
        r"""(?si)<select id="GCUENTA" name="GCUENTA"[^>]*>.*?"""
        r"""<option value="(\d+)"\s+data-tipo="\d+"\s+selected="selected">""",
        resp_text
    )
    return selected_id


def get_accounts_parsed(resp_text: str, logger: ScrapeLogger) -> List[AccountParsed]:
    accounts_debit_table = extract.re_first_or_blank(r'(?si)<h4[^>]*>Cuentas a la vista\s*</h4>.*?</table>', resp_text)
    accounts_credit_table = extract.re_first_or_blank('(?si)<h4[^>]*>Cuentas de crédito</h4>.*?</table>', resp_text)

    accounts_htmls = [(acc_html, ACCOUNT_TYPE_DEBIT)
                      for acc_html in re.findall('(?si)<tr[^>]*class="[^"]*parentOculto".*?'
                                                 '<tr[^>]*class="detalle_oculto.*?</tr>', accounts_debit_table)]
    accounts_htmls.extend([(acc_html, ACCOUNT_TYPE_CREDIT)
                           for acc_html in re.findall('(?si)<tr[^>]*class="[^"]*parentOculto".*?'
                                                      '<tr[^>]*class="detalle_oculto.*?</tr>', accounts_credit_table)
                           if 'FIN.EXPORT' not in acc_html and 'FIN.IMPORT' not in acc_html])

    accounts_parsed = []  # type: List[AccountParsed]

    for account_html, account_type in accounts_htmls:

        """
        <tr id="tablaPG002_filaTabla_0" class="collapsed parentOculto" data-toggle="collapse" 
        data-target="#tablaPG002_detalle_cuenta_0">

            <td data-title="Créditos" id="tablaPG002_filaTabla_0_0"  class=' icon-flecha_der' >ES34 1480 0010 9904 
            0018 2207
            </td>

            <td data-title="Alias" id="tablaPG002_filaTabla_0_1"  >LINEA DE TESORERIA
            </td>

            <td data-title="Saldo" id="tablaPG002_filaTabla_0_2"  class=' text-right rojo text-bold' >-176.728,40 &euro;
                        </td>

            <td data-title="Saldo Disponible" id="tablaPG002_filaTabla_0_3"  class=' text-right text-bold td_w15' 
            >3.271,60 &euro;
                        </td>
            </tr>
            <tr class="detalle_oculto">
               <td colspan="4">
                  <div id="tablaPG002_detalle_cuenta_0" class="collapse childOculto">
                     <dl>
                        <dt>Saldo Retenido</dt><dd>0,00 &euro;</dd>
                        <dt>Limite del crédito</dt><dd>180.000,00 &euro;</dd>
                        <dt>Tipo de interés vigente</dt><dd>2,88</dd>
                     </dl>
                        <ul class="list-group-submenu">
                               <li class="td-drop-menu-2"><a  
                               href="/BEWeb/1480/1480/oper5838_d_mcd.action?OPERACION=oper5838_d_mcd&IDIOMA=01&OPERAC
                               =1361&LLAMADA=Z141B1S0W5F0X0W7H0Z2&CLIENTE=1480007820&CAJA=1480&CAMINO=1480&GCUENTA
                               =14804600100000990400182207" class="c-link">Movimientos</a></li>
                        </ul>
                  </div>
               </td>
        """

        # 'ES7401300012690150189984'
        account_iban = re.sub(
            r'\s+',
            '',
            extract.re_first_or_blank(r"(?si)icon-flecha_der'\s+>(.*?)<", account_html)
        )

        # to be compat with Caixa Geral format  # todo convert to 1480-0010-98-0400123575 format
        # 'ES7401300012690150189984'
        fin_ent_acc_id = "{}-{}-{}-{}".format(
            account_iban[4:8],
            account_iban[8:12],
            account_iban[12:14],
            account_iban[14:],
        )

        balance_w_currency = (
                extract.re_first_or_blank('(?si)<td data-title="Saldo".*?>(.*?)<', account_html)
                or extract.re_first_or_blank('(?si)<td data-title="Saldo natural".*?>(.*?)<', account_html)
        ).strip()

        currency = ('EUR' if '€' in balance_w_currency else
                    'USD' if '$' in balance_w_currency else None)

        if not currency:
            logger.error("WRONG LAYOUT. Can't get currency. Skip {}. Account HTML:\n{}".format(
                fin_ent_acc_id,
                account_html
            ))
            continue

        balance = convert.to_float(balance_w_currency)

        # '/BEWeb/1480/1480/oper5838_d_mcd.action?OPERACION=oper5838_d_mcd&IDIOMA=01&OPERAC=1361&LLAMADA
        # =Z141B1S0W5F0X0W7H0Z2&CLIENTE=1480007820&CAJA=1480&CAMINO=1480&GCUENTA=14800100100000920100025438'
        mov_req_url = extract.re_first_or_blank(
            r'(?si)<a[^>]*href="([^"]*)"[^>]*class="c-link"\s*>Movimientos</a>',
            account_html
        )

        if not mov_req_url:
            logger.info('{}: incorrect account. No link to details. Skip'.format(fin_ent_acc_id))
            continue

        parsed = urllib.parse.urlparse(mov_req_url)  # type: ParseResult

        mov_req_url_raw = parsed.path  # '/BEWeb/0130/0130/oper5838_d_mcd.action'

        # {'CTASEL': '', 'LLAMADA': 'D2C523S0C3F0C0F1D021', 'ultimosMvtosCheck': '0', 'CTAFOR': '', 'IDIOMA': '01',
        #  'OPERAC': '9827', 'CAMINO': '0130', 'CAJA': '0130', 'GCUENTA': '01300100120000690150189984',
        #  'CLIENTE': '0130060779'})
        mov_req_params = {
            k: vals[0]
            for k, vals in urllib.parse.parse_qs(parsed.query).items()
        }

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


def get_movements_parsed(resp_text: str, fin_ent_account_id: str,
                         logger: ScrapeLogger) -> List[MovementParsed]:
    # verify that switched to correct account
    correct_account_selected = extract.re_first_or_blank(
        r'value="\d+{}"[^>]*?selected"'.format(fin_ent_account_id[-10:]),
        resp_text
    )
    if not correct_account_selected:
        selected_acc = extract.re_first_or_blank(
            r'value="(\d+)"[^>]*?selected"'.format(fin_ent_account_id[-10:]),
            resp_text
        )
        logger.error(
            "{}: can't extract movements, switched to wrong account {}".format(
                fin_ent_account_id,
                selected_acc[-10:]
            )
        )
        return []

    mov_htmls = re.findall(r'(?si)<tr\s+id="tablaMvtos.*?</tr>', resp_text)

    movements_parsed_desc = []  # type: List[MovementParsed]

    # Sometimes the bank returns wrong temp_balance at the web page
    # Example: -u 189178 -a 7474,
    # acc 1480-0010-96-0100002835, 26/06/2019, 3 movs since mov w/ amount -24551,57
    # Use temp_balance_calc and temp_balance_errors to handle such cases
    temp_balance_errors = 0
    temp_balance_calc = None  # type: Optional[float]

    for mov_html in mov_htmls:
        operation_date = extract.re_first_or_blank(
            '(?si)data-title="Fecha".*?>(.*?)<', mov_html
        ).strip().replace('-', '/')  # 06/03/2017

        value_date = extract.re_first_or_blank(
            '(?si)data-title="Fecha valor".*?>(.*?)<', mov_html
        ).strip().replace('-', '/')  # 06/03/2017

        if not (operation_date and value_date):
            logger.warning(
                "{}: parse movements: can't extract dates of movement. Check the layout:\n{}".format(
                    fin_ent_account_id,
                    mov_html
                )
            )
            continue

        descr = extract.remove_tags(
            extract.re_first_or_blank(
                '(?si)data-title="Descripción".*?>(.*?)<',
                mov_html
            ).strip().replace('-', '/')
        )

        amount = convert.to_float(
            extract.re_first_or_blank(
                '(?si)data-title="Importe".*?>(.*?)<',
                mov_html
            ).strip()
        )

        temp_balance = convert.to_float(
            extract.re_first_or_blank(
                '(?si)data-title="Saldo".*?>(.*?)<',
                mov_html
            ).strip()
        )

        if temp_balance_calc is None:
            temp_balance_calc = temp_balance  # initial set

        if temp_balance != temp_balance_calc:
            logger.warning("{}: {}: received temp_balance {} != temp_balance_calc {}. Use calculated".format(
                fin_ent_account_id,
                "mov op_date={} amount={}".format(operation_date, amount),
                temp_balance,
                temp_balance_calc
            ))
            temp_balance_errors += 1
            temp_balance = temp_balance_calc

        if temp_balance_errors > TEMP_BALANCE_MAX_ERRORS:
            logger.error(
                "{}: too many temp_balance errors (received != calculated). "
                "Check warning msgs in log files and the web. "
                "Last failed movement: {}. "
                "Abort movements parsing now".format(
                    fin_ent_account_id,
                    "mov op_date={} amount={}".format(operation_date, amount),
                )
            )
            return []

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(movement_parsed)

        # to check for the next mov
        # (which really is a previous movement due to descending ordering)
        temp_balance_calc = round(temp_balance - amount, 2)

    # caixa geral ordering
    movements_parsed_asc = list(reversed(movements_parsed_desc))

    return movements_parsed_asc
