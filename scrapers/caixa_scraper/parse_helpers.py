import datetime
import json
import re
import traceback
import urllib.parse
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs.myrequests import Response
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from scrapers.caixa_scraper.meta import CompanyUrlData, MovementUrlData, SERVICE_LINKS


def get_companies_links_datas(resp: Response) -> List[CompanyUrlData]:
    """
    company = bank user = Cambiar usuario
    then init_url can be used to scrape each company (bank user)
    :return:
     [
        CompanyLinkData(
            company_title_in_list='*MAS MOTOR S.A.',
            init_url='https:..../WAP/SPDServlet?WebLogicSession='
                     'jOZULdgRMHvSkOkveIju52hYmJdTf3Xcr3tz39cSys3f9JJ-l8Zw!'
                     '-1712696576!1186788744!1483176007697&amp;id_params=1492212472'
        ),
        ...
     ]
    """
    companies_html = extract.re_first_or_blank('(?si)<div id="contenidoBody">.*</html>', resp.text)

    companies_links = []
    for href_raw, text_w_tags in re.findall('(?si)<a.*?href="(.*?)".*?>(.*?)</a', companies_html):
        text = extract.remove_tags(text_w_tags)
        href = extract.unescape(href_raw)

        if text not in SERVICE_LINKS:
            companies_links.append(
                CompanyUrlData(
                    urllib.parse.urljoin(resp.url, href),
                    text
                )
            )

    return companies_links


def get_organization_title_if_one_org(html_text: str) -> str:
    """
    use this function to get name if one organization
    """
    return extract.re_first_or_blank('<p class="userName">(.*?)</p>', html_text).strip()


def get_accounts_to_process(resp) -> List[Tuple[str, str]]:
    """
    extract all links from accs page and process unique urls
    add acc as tuple of unique links and not blank text
    """

    accounts_html = extract.re_first_or_blank('(?si)<div id="contenidoBody">.*</html>', resp.text)

    accounts_tuples = []
    urls = []  # type: List[str]

    # NOTES:
    # INCLAM (191510) contains several tabs with links with texts: 'Mis cuentas', 'Más cuentas'
    # Some accounts of other customers renamed and doesn't contain 'ES' in title
    # Possible way to extract but then need to filter by text !=  'Mis cuentas' or 'Más cuentas'
    # for href, text_raw in re.findall('(?si)<a.*?href="(.*?)".*?>(.*?)</a', accounts_html):

    # Correct way to extract but fragile if class 'secundariaFont' will be changed
    for href, text_raw in re.findall(
            r'(?si)<td[^>]*class="[^"]*filaTablaCD__elemento">\s*<a.*?href="(.*?)".*?>(.*?)</a',
            accounts_html):
        url = urllib.parse.urljoin(resp.url, extract.unescape(href))
        text = extract.remove_tags(text_raw)
        if text and (url not in urls):
            accounts_tuples.append((url, text))
            urls.append(url)

    return accounts_tuples


def _get_mov_date_obj(date_part_str, prev_date_obj, fin_ent_account_id, logger) -> datetime.datetime:
    """
    '16/07' and modify to '16/07/2017'
    handle case if mov from previous year:
    if calculated date > current date then calc.year = curr.year - 1

    even using calculated year, possible case when 2016 (or less) will be calculated as 2017
    if date (day/mo) of prev year less than current date (day/mo)
    use additional checkups (direct extractions) in main code
    """

    date_for_year_obj = prev_date_obj if prev_date_obj else datetime.datetime.utcnow()

    # first, try with current year
    # then do step back on exception
    # loop over 10 years to avoid infinite loop
    # on unexpected situation
    year = date_for_year_obj.year  # type: int
    date_obj = datetime.datetime.now()  # suppress linter
    for _ in range(10):
        date_str = date_part_str + "/" + str(year)
        try:
            date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')
            break
        # wrong year, most probable reason: 29/02
        # move to one previous year to find leap year
        except ValueError as exc:
            if 'day is out of range for month' in str(exc):
                year -= 1
                logger.info(
                    'Handled exception: "{}" for predicted date {}. '
                    'Set previous year to get (probably) correctly predictied date: {}'.format(
                        exc,
                        date_str,
                        year
                    )
                )
        except:
            raise Exception(
                "{}: can't get_mov_date_obj from date_str={} and year={}. "
                "NEED TO HANDLE THIS CASE IN THE CODE.\n{}".format(
                    fin_ent_account_id,
                    date_str,
                    date_for_year_obj.year,
                    traceback.format_exc()
                ))

    if date_obj > date_for_year_obj:
        date_str = date_part_str + "/" + str(date_for_year_obj.year - 1)
        date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')

    return date_obj


def get_movements_from_html_list(resp, fin_ent_account_id, logger) -> List[MovementUrlData]:
    # [
    #   ('/WAP/SPDServlet?WebLogicSession=.....69323!1483304881393&amp;id_params
    # =1405673001',
    #   'C. 333896405 2712',
    #   <td...>+1000.99<..></td>,
    #   '<tr...>28/12/2016<..></tr>'),
    #   ...
    # ]

    movements_from_html_list = []

    movements_html = extract.re_first_or_blank('(?si)<div id="contenidoBody">.*</html>', resp.text)
    # use 'dirty' regexp to extraxt html only to avoid hanging on parsing, then use extract.remove_tags
    # last one could be 'Ver más movimientos'
    movements_htmls = [
        mov for mov in re.findall('(?si)<tr[^>]*tipoMovimiento.*?</tr>',
                                  movements_html)
        if 'Ver más movimientos' not in mov
    ]

    prev_date_obj = None

    for mov_html in movements_htmls:
        # parse '16/07' and modify to '16/07/2017'
        date_part_str = extract.remove_tags(
            extract.re_first_or_blank(
                '<a.*?</a>',
                mov_html
            )
        )
        # handle probable case
        if not date_part_str:
            continue

        date_obj = _get_mov_date_obj(date_part_str, prev_date_obj, fin_ent_account_id, logger)

        prev_date_obj = date_obj

        url = urllib.parse.urljoin(
            resp.url,
            extract.unescape(
                extract.re_first_or_blank(
                    'a href="(.*?)"',
                    mov_html
                )
            )
        )
        temp_balance_str = extract.remove_tags(
            extract.re_first_or_blank(
                '(?si)<td[^>]*textoDerecha.*?</td>',
                mov_html
            )
        )

        temp_balance = convert.to_float(temp_balance_str)

        mov = MovementUrlData(
            date=date_obj,
            url=url,
            temp_balance=temp_balance
        )

        movements_from_html_list.append(mov)

    return movements_from_html_list


def get_movements_from_xml_list(resp, fin_ent_account_id, logger) -> List[MovementUrlData]:
    movements_from_xml_list = []

    resp_text_for_json = extract.re_first_or_blank(r'(?si)callBack_movimientosCuenta\((.*)\)', resp.text)

    if not resp_text_for_json:
        return []

    resp_text_clean = resp_text_for_json.strip().replace('\n', '').replace('idLista:', '"idLista":')
    data = json.loads(resp_text_clean)

    prev_date_obj = None

    for m_data in data['items']:
        """
        {'conceptoCantidad': {'moneda': 'EUR', 'value': '-861,81'}, 'saldo': {'moneda': 'EUR', 'value': '+19.050,
        77'}, 'conceptoTexto': {'value': 'SANTANDER CONSU...'}, 'fechaMovimiento': {'value': '17/07'}, 'enlaceFila': 
        {'href': '/GPeticiones;WebLogicSession=c8c8ZnDThy1dkRTyykvhHS3SwY9BLv2vKkBWl71nKNhLWqScV7Xz!1900730233
        !358268359?PN=GCT&amp;PE=103&amp;PN_ORIGEN=GCT&amp;PE_ORIGEN=16&amp;LLEGA=1&amp;PESTANA_ELEGIR=1&amp
        ;NUMERO_CUENTA=0012100914420020600000032502&amp;CUENTA=0012100914420020600000032502&amp;NUMERO_MOVIMIENTO
        =0000996&amp;FECHA_CONTABLE=2017198&amp;INDICADOR_COMUNICADOS=N&amp;INDICADOR_FRACCIONADO=N&amp;REF_CUENTA
        =bgbcM%7EkxE3huBtwz6TETeAAAAV1VvzwCR1cK2oUy6Ys%3AGCT%3A102&amp;CLOPWW=035&amp;SUBCLO=00064&amp;IMPORTE_COM
        =000000000086181&amp;SIGNO_IMPORTE_COM=-&amp;MONEDA_COM=EUR&amp;SALDO_ACTUAL=000000000507354&amp
        ;SIGNO_SALDO_ACTUAL=%2B&amp;FECHA_VALOR=17072017&amp;INDICA_SALDO=NNNN&amp;TIPO_BUSQUEDA=05&amp;FECHA_COM
        =17072017&amp;TIPO_COMUNICADO=00000&amp;DESC_COMUNICADO=SANTANDER+CONSUM.&amp;REMITENTE=A79082244005&amp
        ;NUMERO_RECIBO=095386303210307&amp;OPCION_OPERACION=LISTACLOP&amp;CLICK_ORIG=FLX_GCT_100&amp;CLAVE_ANTERIOR
        =0F20171980000996+++++++19050772017182&amp;CLAVE_CONTINUACION_SUM=0F20171980000996+++++++19050772017182&amp
        ;CLAVE_CONTINUACION_DETALLE_3496=0F20171980000996+++++++19050772017182&amp;CLAVE_DETALLE_3496=D_3496_0&amp
        ;NUMERO_SUBMOVIMIENTO=&amp;ALIAS_CUENTA=++-++Mas+Motor'}}
        """

        date_part_str = m_data['fechaMovimiento']['value']
        date_obj = _get_mov_date_obj(date_part_str, prev_date_obj, fin_ent_account_id, logger)
        prev_date_obj = date_obj

        url = urllib.parse.urljoin(
            resp.url,
            extract.unescape(m_data['enlaceFila']['href'])
        )

        temp_balance = convert.to_float(m_data['saldo']['value'])

        mov = MovementUrlData(
            date=date_obj,
            url=url,
            temp_balance=temp_balance
        )

        movements_from_xml_list.append(mov)

    return movements_from_xml_list


def get_account_parsed_from_acc_details_page(html_text: str) -> AccountParsed:
    """Will return balance_available as balance for credit accounts"""

    # [['Saldo:', '+1.207,34 €'], ['IBAN:', 'ES53 2100 2570 9002 1004 2530'], ...]
    data_lists = [[extract.remove_tags(column) for column in re.findall('<td.*?>(.*?)</td>', row)]
                  for row in re.findall('<tr.*?>(.*?)</tr>', html_text)]

    account_no = ''
    balance_available_str = ''
    balance_str = ''
    for data_list in data_lists:
        if data_list[0] == 'IBAN:':
            account_no = data_list[1].replace(' ', '')
        # should be 10 € if used 90 € of credit 100 € and 10 € unused
        if data_list[0] == 'Saldo Actual:':
            balance_available_str = data_list[1]
        # should be -90 € if used 90 € of credit 100 €
        if data_list[0] == 'Saldo:':
            balance_str = data_list[1]

    balance_available = convert.to_float(balance_available_str)
    currency_sign = balance_available_str.split()[-1].strip()
    if currency_sign == '€':
        currency = 'EUR'
    elif currency_sign == '£':
        currency = 'GBP'
    elif len(currency_sign) == 3:
        currency = currency_sign
    else:
        currency = 'USD'
    # for credit accs balance will be < 0
    balance = convert.to_float(balance_str)
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    account_parsed = {
        'account_no': account_no,
        # IMPORTANT: we use balance_available for credit accs (equal to balance if debit acc)
        'balance': balance_available,
        'account_type': account_type,
        'currency': currency,
    }
    return account_parsed


def get_balance_after_movement(movement_amount_str: str, balance_before: float) -> float:
    """calculate balance_after previous movement"""

    amount = convert.to_float(movement_amount_str)
    balance_after = round(balance_before - amount, 2)
    return balance_after


def get_movement_parsed_from_html(resp, mov_url_data: MovementUrlData) -> MovementParsed:
    movement_details_map = {
        'Nº cuenta:': 'account_no',
        'Concepto:': 'description',
        'Concepto específico:': 'description_details',
        'Importe:': 'amount',
        'Fecha:': 'operation_date',
        'Fecha valor:': 'value_date',
        # column 'Más datos' in the mov list
        'Remitente:': 'description_additional_info'
    }

    # {'': 'Desconectar',
    #  'description': 'MANTENIMIENTO',
    #  'value_date': '01/01/2017',
    #  'amount': '-12,00  Euros',
    #  'operation_date': '01/01/2017',
    #  'account_no': 'ES52 2100 9144 3002 0003 2502'}
    movement_parsed = {
        movement_details_map.get(extract.remove_tags(title), ''): extract.remove_tags(value)
        for title, value
        in re.findall('<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>', resp.text)
    }  # type: MovementParsed

    # check is correct parsing
    if 'amount' not in movement_parsed:
        return {}

    movement_parsed['temp_balance'] = mov_url_data.temp_balance
    movement_parsed['amount'] = convert.to_float(movement_parsed['amount'])
    movement_parsed['account_no'] = movement_parsed['account_no'].replace(' ', '')
    if 'description' not in movement_parsed:
        movement_parsed['description'] = movement_parsed['description_details']
    if 'description_additional_info' in movement_parsed:
        movement_parsed['description'] = '{} ({})'.format(
            movement_parsed['description'],
            movement_parsed['description_additional_info']
        )
        movement_parsed.pop('description_additional_info')

    # clean of unused keys
    movement_parsed.pop('description_details')
    if '' in movement_parsed:
        movement_parsed.pop('')

    return movement_parsed


def get_movement_parsed_from_xml(resp, mov_url_data: MovementUrlData, logger) -> MovementParsed:
    movement_parsed = {}  # type: MovementParsed

    movement_parsed['account_no'] = extract.re_first_or_blank(
        r'<wax:label>Nº cuenta:</wax:label>\s*<wax:descripcion>(.*?)</wax:descripcion>',
        resp.text
    ).replace(' ', '')

    movement_parsed['description'] = extract.re_first_or_blank(
        r'(?si)<wax:label>[^<]*concepto[^<]*</wax:label>\s*<wax:descripcion>(.*?)</wax:descripcion>',
        resp.text
    )

    # column 'Más datos' in the mov list
    description_additional_info = extract.re_first_or_blank(
        r'(?si)<wax:label>[^<]*Remitente[^<]*</wax:label>\s*<wax:descripcion>(.*?)</wax:descripcion>',
        resp.text
    )

    if description_additional_info:
        movement_parsed['description'] = '{} ({})'.format(
            movement_parsed['description'],
            description_additional_info
        )

    movement_parsed['operation_date'] = extract.re_first_or_blank(
        r'<wax:label>Fecha:</wax:label>\s*<wax:descripcion>(.*?)</wax:descripcion>',
        resp.text
    )
    movement_parsed['value_date'] = extract.re_first_or_blank(
        r'<wax:label>Fecha valor:</wax:label>\s*<wax:descripcion>(.*?)</wax:descripcion>',
        resp.text
    )

    # ('861,81', '-')
    amount_raw = extract.re_first_or_blank(
        r'<wax:label>Importe:</wax:label>\s*<wax:cantidad.*?valor="(.*?)".*?signo="(.*?)"/>',
        resp.text
    )
    try:
        movement_parsed['amount'] = convert.to_float(amount_raw[1] + amount_raw[0])
    except IndexError as exc:
        logger.error(
            'Movements parsing error: {}\n{}\n\n{}'.format(exc, mov_url_data, resp.text)

        )
        movement_parsed['amount'] = 0
    movement_parsed['temp_balance'] = mov_url_data.temp_balance

    return movement_parsed
