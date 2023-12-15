import html
import re
import urllib.parse
from typing import List
from urllib.parse import ParseResult

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, MovementParsed, AccountParsed

import json


def get_selected_account_id(resp_text: str) -> str:
    """Parses
    <input class="ftlui-formctl ftlui-formctl-rd ftlui-status-checked rdiobtn-vrtclalgn"
    id="ftlui-selectProd-15-item-0"
    name="GCUENTA" checked="checked" type="radio" value="30250100160000121400005159" />
    """
    selected_id = extract.re_first_or_blank(
        r'name="GCUENTA" checked="checked" type="radio" value="(\d+)"',
        resp_text
    )
    return selected_id


def get_company_title(resp_text: str) -> str:
    company_title = extract.re_first_or_blank(
        'document.Cli.NOMBRECLIENTE.value="(.*?)";',
        resp_text
    ).strip()
    return company_title


def get_accounts_parsed(resp_text: str, logger: ScrapeLogger) -> List[AccountParsed]:
    accounts_htmls = re.findall('(?si)<tr[^>]*id="pgtable7327-CT-item.*?"(.*?)</tr>', resp_text)

    # from caixa geral
    # accounts_credit_table = extract.re_first_or_blank(
    # '(?si)<h4[^>]*>Cuentas de crédito</h4>.*?</table>', html_str)
    #  '<tr[^>]*class="detalle_oculto.*?</tr>', html_str)]
    # accounts_htmls.extend(
    # [(acc_html, ACCOUNT_TYPE_CREDIT)
    # for acc_html in re.findall('(?si)<tr[^>]*class="[^"]*parentOculto".*?'
    # '<tr[^>]*class="detalle_oculto.*?</tr>', accounts_credit_table)
    # if 'FIN.EXPORT' not in acc_html and 'FIN.IMPORT' not in acc_html])

    accounts_parsed = []

    for account_html in accounts_htmls:

        # 'ES7401300012690150189984'
        account_iban = re.sub(r'\s+', '',
                              extract.re_first_or_blank(r'(?si)id="ftlid-\d+">(.*?)</span>', account_html))
        fin_ent_acc_id = account_iban

        # todo use contable or disponible, check on credit accounts
        balance_w_currency = (
            extract.re_first_or_blank('CT-col-scont">(.*?)</td>', account_html)
        ).strip()

        balance_str, currency = balance_w_currency.split(' ')

        if not currency:
            logger.error("Can't get currency. Check the html:\n{}".format(account_html))
            continue

        balance = convert.to_float(balance_str)

        # '/BEWeb/3025/6025/not9765_d_0GNRL.action;jsessionid=4198EDA7C430EE17131089BB95D7E11B.lima
        # ?OPERACION=not9765_d_0GNRL&amp;IDIOMA=01&amp;OPERAC=7327&amp;LLAMADA=F3B651A0F220W0Z1Z0B6
        # &amp;CLIENTE=3025146996&amp;CAJA=3025&amp;CAMINO=6025&amp;GCUENTA=30250109000000811400001861
        # &amp;TIPE=2&amp;DEDONDE=7327&amp;CODREANUDA=                    &amp;CLAV=@@@@
        # &amp;CIAS=@@@@@@&amp;cuentaFormateadaGCUENTA=ES97 3025 0900 8114 0000 1861 (compte corrent)
        # &amp;NCTA=000009001400001861&amp;fecha-ini=01/05/2018&amp;FDES=01052018&amp;FINI=01052018&amp;FFIN=
        # &amp;FHAS=&amp;periodo=entrefechas&amp;orden=ascendente&amp;NUM_REANUDACIONES=15&amp;TIENEFILTRO=S
        # &amp;NOPE=&amp;NMOV=&amp;OPERACIONENLACE=8490'
        mov_req_url_htmlescaped = extract.re_first_or_blank(
            r"(?si)cargarConsultaMovimientos\('(.*?)'\)",
            account_html
        )
        if not mov_req_url_htmlescaped:
            logger.warning('Incorrect cuenta: {}.\n\nNo link to details. Skip'.format(account_html))
            continue
        mov_req_url = html.unescape(mov_req_url_htmlescaped)
        mov_req_url_parsed = urllib.parse.urlparse(mov_req_url)  # type: ParseResult

        mov_req_url_raw = mov_req_url_parsed.path  # '/BEWeb/0130/0130/oper5838_d_mcd.action'

        # {'CTASEL': '', 'LLAMADA': 'D2C523S0C3F0C0F1D021', 'ultimosMvtosCheck': '0', 'CTAFOR': '', 'IDIOMA': '01',
        #  'OPERAC': '9827', 'CAMINO': '0130', 'CAJA': '0130', 'GCUENTA': '01300100120000690150189984',
        #  'CLIENTE': '0130060779'})
        mov_req_params = {
            k: vals[0]
            for k, vals in urllib.parse.parse_qs(mov_req_url_parsed.query).items()
        }

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

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
    """
    < table class ="tabla" id="CONSMOV" >
        < caption class ="oculta" > Movimientos de la cuenta < /caption >
            < thead > < tr class ="titulo_tabla" >
                < th id = "cab0" class ="first wp20" scope="col" > FECHA DE OPERACI\xd3N < /th >
                < th id = "cab1" class ="wp30" scope="col" > CONCEPTO < /th >
                < th id = "cab2" class ="wp20" scope="col" > FECHA VALOR < /th >
                < th id = "cab3" class ="wp15 arght" scope="col" > IMPORTE < /th >
                < th id = "cab4" class ="wp15 arght" scope="col" > SALDO < /th > < / tr >
            < / thead >
            < tbody >
                < tr class ="even" >
                    < td class ="even first wp20" > 10/ 04 / 2023 < /td >
                    < td class ="even wp30" >
                        < a href = "/BEWeb/3025/6025/not0934_d_0POP.action;jsessionid=M2aa0MduCkX5nPt6fSr5HZaV.tlis?OPERACION=not0934_d_0POP&IDIOMA=01&OPERAC=9765&LLAMADA=Z242W1D02120W04220E2&CLIENTE=3025288506&CAJA=3025&CAMINO=6025&TIPO_PETICION=2000&GCUENTA=30250500020000476118001645&TIPOCUENTA=C&FECHA_INICIAL=11-04-2023&FECHA_FINAL=11-04-2023&FECHA=FAST11-04-2023&CADENA_BUSCAR=4162067408&CLIEDOCS=0030248450" title = "Abre documento pdf del movimiento: LIQUIDACION PRESTAMO/AVAL. (abre en ventana nueva)" target = "_blank" > LIQUIDACION PRESTAMO / AVAL < / a > < / td > < td class ="even wp20" > 10/ 04 / 2023 < /td > < td class ="even wp15 arght" >  < span class ="c_red" > & # 45;3.976,28 EUR < td class ="even wp15 arght" > 5.527, 26 & nbsp;EUR
                    < /td >
                < / tr >
                < tr class ="odd" >
                    < td class ="odd first wp20" > 05/ 04 / 2023 < /td >
                    < td class ="odd wp30" >
                        < a href = "/BEWeb/3025/6025/not0934_d_0POP.action;jsessionid=M2aa0MduCkX5nPt6fSr5HZaV.tlis?OPERACION=not0934_d_0POP&IDIOMA=01&OPERAC=9765&LLAMADA=Z242W1D02120W04220E2&CLIENTE=3025288506&CAJA=3025&CAMINO=6025&TIPO_PETICION=2000&GCUENTA=30250100020000451433460500&TIPOCUENTA=C&FECHA_INICIAL=05-04-2023&FECHA_FINAL=05-04-2023&FECHA=FAST05-04-2023&CADENA_BUSCAR=4155312813&CLIEDOCS=0030248450" title = "Abre documento pdf del movimiento: TRANSF CTA DE:25 OSONA BUS, S.A. (abre en ventana nueva)" target = "_blank" > TRANSF CTA DE: 25 OSONA BUS, S.A < / a >
                    < / td >
                    < td class ="odd wp20" > 05/ 04 / 2023 < /td >
                    < td class ="odd wp15 arght" >  < span class ="c_green" > 2.000, 00 & nbsp;EUR < /span >  < /td >
                    < td class ="odd wp15 arght" > 9.503, 54 & nbsp;EUR < /td >
                < / tr >
            < / tbody >
    < / table >
    """
    movs_table = extract.re_first_or_blank('(?si)<table class="tabla" id="CONSMOV">.*?</tbody>', resp_text.replace('\n', '').replace('\t', ''))
    rows = [row for row in re.findall('(?si)<tr[^>]*>(.*?)</tr>', movs_table)]
    movements_parsed_desc = []

    for mov_html in rows:
        cells = [cell.strip() for cell in re.findall('(?si)<td[^>]*>(.*?)</td>', mov_html)]
        if len(cells) < 4:
            if 'th' in mov_html:
                continue
            else:
                logger.warning(
                    "{}: parse movements: can't extract data. Check the layout:\n{}".format(
                        fin_ent_account_id,
                        mov_html
                    )
                )
                continue

        operation_date = cells[0]  # 06/03/2023
        value_date = cells[2]  # 06/03/2023

        if not (operation_date and value_date):
            logger.warning(
                "{}: parse movements: can't extract dates of movement. Check the layout:\n{}".format(
                    fin_ent_account_id,
                    mov_html
                )
            )
            continue

        descr = extract.re_first_or_blank(
            '(?si)<a[^>]*>(.*?)</a>',
            cells[1]
        )
        if not descr:
            descr = cells[1]

        pdf_link = extract.re_first_or_blank(
            '(?si)href="(.*?)" title',
            cells[1]
        )
        amount = convert.to_float(
            extract.re_first_or_blank(
                '(?si)<span[^>]*>(.*?)</span>',
                cells[3]
            ).replace('\xa0', '')
        )
        temp_balance = convert.to_float(cells[4].replace('\xa0', ''))
        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
            'receipt_params': {
                'pdf_link': pdf_link
            }
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc


def parse_more_movements(resp_text: str, fin_ent_account_id: str,
                         logger: ScrapeLogger) -> List[MovementParsed]:
    mov_text = resp_text.replace('datosDetalle = ', '').replace('cabeceras', '"cabeceras"').replace('estilos', '"estilos"').replace('filas', '"filas"')
    mov_dict = json.loads(mov_text)
    next_page = mov_dict['CODAVANCE']
    paginator = mov_dict['PAGINAACTUAL']
    rows = mov_dict['datos']['filas']

    movements_parsed_desc = []
    for row in rows:
        operation_date = row[0]
        value_date = row[2]

        descr = extract.re_first_or_blank(
            '(?si)<a[^>]*>(.*?)</a>',
            row[1]
        )
        if not descr:
            descr = row[1]
        pdf_link = extract.re_first_or_blank(
            '(?si)href="(.*?)" title',
            row[1]
        )

        amount = convert.to_float(html.unescape(row[3]).split(' ')[0])
        temp_balance = convert.to_float(html.unescape(row[4]).split(' ')[0])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
            'receipt_params': {
                'pdf_link': pdf_link
            }
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc, next_page, paginator

