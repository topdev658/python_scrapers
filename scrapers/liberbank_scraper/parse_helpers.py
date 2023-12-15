import re
from typing import List

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, AccountParsed, MovementParsed


def get_company_title(resp_text: str) -> str:
    return extract.re_first_or_blank(
        'var Nom_Cli="(.*?)";',
        resp_text
    )


def get_llamada_param(resp_text: str) -> str:
    return extract.re_first_or_blank('LLAMADA=(.*?)&', resp_text)


def get_cliente_param(resp_text: str) -> str:
    return extract.re_first_or_blank('CLIENTE=(.*?)&', resp_text)


def get_pagination_codreanud_param(resp_text: str) -> str:
    """:returns the code (if more pages available)
        or blank str (if there are no more pages)
    """
    codreanud_param = extract.re_first_or_blank(
        """(?si)<div id="paginacion">.*?var codreanud = '(.*?)';""",
        resp_text
    ).strip()
    return codreanud_param


def get_accounts_parsed_v2(logger: ScrapeLogger, resp_text: str) -> List[AccountParsed]:
    """
    another layout to parse balance
    reason: unknow, looks like they changed the layout for all endpoints
    """

    """
    datosctas[contador] = new Object();
    datosctas[contador].grupocuenta = '001';
    datosctas[contador].saldocta = '+0000000000208200'; <!-- contable -->   <------ balance sign (first char)
    if(datosctas[contador].saldocta.substring(0,1)=="-"){
        datosctas[contador].saldocta ='-20,82 ';
    }
    else{
        datosctas[contador].saldocta ='20,82 ';                             <------ balance
    }
    if (datosctas[contador].grupocuenta=='002'){
        datosctas[contador].saldoctaconsaldo=datosctas[contador].saldocta;
        //datosctas[contador].saldocta=datosctas[contador].saldocta.replace("-","");
        datosctas[contador].formapago = '#ADD8E6';
        /*
        P	Pre-Pago
        C	Crédito
        D	Débito
        A	Dual - Crédito/Débito
        */
    }
    else if (datosctas[contador].grupocuenta=='014'){//seguros
        datosctas[contador].codcompaniaaseguradora = '#ADD8E6'.substring(0,5);
        datosctas[contador].codramo = '#ADD8E6'.substring(5,7);
        /*EXCEPCION VIDATAR*/
        if('#ADD8E6' == 'C074243') datosctas[contador].saldocta = '0,00';
    }
    else if (datosctas[contador].grupocuenta=='007'){//comercios
        datosctas[contador].numcomercio = '#ADD8E6';
    }
    datosctas[contador].numcta = '20480112990000863400004553';
    datosctas[contador].productoCECA = '01';
    datosctas[contador].familia = '34';
    datosctas[contador].numctafor = replaceAll('IBAN ES26 2048 1299 8634 0000 4553','-',' ');
    datosctas[contador].clasecta = 'CUENTA CORRIENTE'.toUpperCase();                            <----- type
    datosctas[contador].aliascta = 'CUENTA CORRIENTE'.toUpperCase();
    if(datosctas[contador].aliascta == '')
        datosctas[contador].aliascta = 'CUENTA CORRIENTE'.toUpperCase();
    if(datosctas[contador].aliascta.substring(29,30)=="X")
        datosctas[contador].aliasctaSinX=datosctas[contador].aliascta.substring(0,29); //quito la X si es un alias
    else
        datosctas[contador].aliasctaSinX=datosctas[contador].aliascta;

    datosctas[contador].tiposaldocta = '000300';
    datosctas[contador].codmoneda = '978';
    datosctas[contador].desmoneda = '&euro;';
    datosctas[contador].tiporelacion = 'TI';
    datosctas[contador].autorizacioncta = 'CA';
    datosctas[contador].flag1 = '0';
    datosctas[contador].flag2 = '0';
    datosctas[contador].flag3 = '0';
    datosctas[contador].flag4 = '0';
    datosctas[contador].flag5 = '0';
    datosctas[contador].feccadu = '0000';
    datosctas[contador].estado = ' ';
    """

    accounts_htmls = re.findall(
        r'(?si)datosctas\[contador\]\s*[=]\s*new\s*Object.*?datosctas\[contador\]\.estado',
        resp_text
    )

    accounts_parsed = []
    for account_html in accounts_htmls:
        account_type_raw = extract.re_first_or_blank(
            r"datosctas\[contador\]\.clasecta = '(.*?)'",
            account_html
        )

        if account_type_raw not in ['CUENTA CORRIENTE', 'CUENTA CREDITO', 'CUENTA CORRIENTES DIVISAS']:
            continue

        account_type = (ACCOUNT_TYPE_DEBIT
                        if account_type_raw in ['CUENTA CORRIENTE', 'CUENTA CORRIENTES DIVISAS']
                        else ACCOUNT_TYPE_CREDIT)

        account_iban_raw = extract.re_first_or_blank(
            r"datosctas\[contador\]\.numctafor = replaceAll\('IBAN\s*(.*?)'",
            account_html
        ).strip()  # ES22 2048 0361 1034 0000 0832

        account_no = account_iban_raw.replace(' ', '')  # ES4620480361109700000729

        currency_raw = extract.re_first_or_blank(
            r"datosctas\[contador\]\.desmonedaLarga\s*=\s*'(.*?)'",  # euros / dólares
            account_html
        )

        # to convert possible US dollars to USD
        if currency_raw == 'euros':
            currency = 'EUR'
        elif currency_raw == 'dólares':
            currency = 'USD'
        else:
            logger.error('{}: unknown currency: {}'.format(
                account_no,
                currency_raw
            ))
            continue

        balnace_sign = extract.re_first_or_blank(
            r"datosctas\[contador\]\.saldocta = '([+-])",
            account_html
        )

        balance_str = extract.re_first_or_blank(
            r"datosctas\[contador\]\.saldocta ='(\d+.*?)'",
            account_html
        ).strip()

        balance = convert.to_float(balnace_sign + balance_str)

        codmoneda = extract.re_first_or_blank(
            r"datosctas\[contador\]\.codmoneda\s*=\s*'(.*?)'",
            account_html
        )

        numcta = extract.re_first_or_blank(
            r"datosctas\[contador\]\.numcta\s*=\s*'(.*?)'",  # 20480203610000109700000729
            account_html
        )

        account_parsed = {
            'account_no': account_no,
            'account_iban_raw': account_no,  # account_iban_raw
            'account_type': account_type,
            'currency': currency,
            'balance': balance,
            'balance_str': balance_str,  # '20.582,46', for mob req
            'codmoneda': codmoneda,  # for mov req
            'numcta': numcta,  # for mov req
            'financial_entity_account_id': numcta
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]

    mov_table = extract.re_first_or_blank('(?si)<table class="generica".*?</table>', resp_text)
    rows = re.findall('(?si)<tr.*?</tr>', mov_table)
    # 0121780000763400008898
    gcuenta_param = extract.re_first_or_blank(r"(?i)var gcuenta\s*=\s*'(.*?)';", resp_text)

    for row in rows:
        cells = [extract.remove_tags(cell) for cell in re.findall('(?si)<td.*?>(.*?)</td>', row)]

        if len(cells) < 5:
            continue  # headers

        operation_date = cells[0].replace('-', '/')
        value_date = cells[1].replace('-', '/')
        # var desc1='LIQ.REM.DESC';
        # var desc2='204821780297355035';
        descr = '{} {}'.format(
            extract.re_first_or_blank("var desc1='(.*?)';", row),
            extract.re_first_or_blank("var desc2='(.*?)';", row)
        ).strip()
        amount_abs = convert.to_float(extract.re_first_or_blank(r"(?si)var val\s*=\s*'(.*?)'", cells[8]))
        amount_sign = -1 if extract.re_first_or_blank(r"var signo\s*=\s*'(.*?)'", cells[8]) == '-' else 1
        amount = amount_sign * amount_abs
        temp_balance_abs = convert.to_float(extract.re_first_or_blank(r"(?si)var val\s*=\s*'(.*?)'", cells[9]))
        temp_balance_sign = -1 if extract.re_first_or_blank(r"var signo\s*=\s*'(.*?)'", cells[9]) == '-' else 1
        temp_balance = temp_balance_sign * temp_balance_abs

        # Receipt params
        # var CUENTACOMP1_13 = '20482178739304000808'
        # Some movs have no cuentaenvia_param, in this account_no[-20:] will be used
        cuentaenvia_param = extract.re_first_or_blank(r"var CUENTACOMP1_\d+\s*=\s*'(.*?)'", row)
        # # var clvhash111 = 'EC89A056E8899825'
        cadenabuscar_param = extract.re_first_or_blank(r"var clvhash\d+\s*=\s*'(.*?)'", row)
        has_receipt = bool(cadenabuscar_param)

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
            'has_receipt': has_receipt,
            'cadenabuscar_param': cadenabuscar_param,
            'gcuenta_param': gcuenta_param,
            'cuentaenvia_param': cuentaenvia_param,
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc


def get_movements_parsed_from_excel_html(resp_text: str) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]

    rows = re.findall('(?si)<tr.*?</tr>', resp_text)

    for row in rows:
        cells = [extract.remove_tags(cell) for cell in re.findall('(?si)<td.*?>(.*?)</td>', row)]

        if len(cells) < 5:
            continue

        operation_date = cells[0].replace('-', '/')
        value_date = cells[1].replace('-', '/')
        descr = re.sub(r'\s+', ' ', cells[2])
        amount = convert.to_float(cells[3])
        temp_balance = convert.to_float(cells[4])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
