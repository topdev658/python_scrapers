import io
import re
from typing import List, Tuple

import PyPDF2

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

ENTINY_IBAN_DIGITS = '0216'


def get_webid_param(resp_text: str) -> str:
    return extract.re_first_or_blank(r"EN.AddNode\('Data_WebId','(.*?)'", resp_text)


def get_data_persistence_param(resp_text: str) -> str:
    return extract.re_first_or_blank(r"(?s)EN.AddNode\('Data_Persistance','(.*?)'", resp_text)


def get_organization_title(resp_text: str) -> str:
    return (
        extract.re_first_or_blank(
            '(?si)<span class="ei_tpl_appl_info_presentation_name">(.*?)</span>',
            resp_text
        ).strip()
    )


def get_account_iban(resp_content: bytes) -> str:
    pdf_file = io.BytesIO(resp_content)
    pdf = PyPDF2.PdfFileReader(pdf_file)
    # DOCUMENTO DE IDENTIFICACIÓN BANCARIANúmero de Identificación Bancaria (NIB)Entidad0216Sucursal1083D.C.02Nº
    # cuenta0500035849DivisaEURIdentificador internacional de cuenta bancariaIBAN (International Bank Account
    # Number)ES87       0216       1083       0205       0003       5849SucursalMARIA DE MOLINA, EMPRESASBIC (
    # Bank Identifier Code)CMCIESMMPAY THROUGH CMCIFRPADirección de la sucursalMARIA DE MOLINA, EMPRESASC/ MARIA
    # DE MOLINA, 3428006 MADRID% 34912153560 Titular de la cuenta (Account Owner)INCLAM SACALLE LIMONERO NUM
    # 2228020 MADRID\nEntregue este documento al organismo que necesite conocer sus\nreferencias bancarias para
    # la domiciliación de sus transferencias orecibos.ZONA RESERVADA AL DESTINATARIO DELDOCUMENTO'
    text = pdf.getPage(0).extractText()
    iban = re.sub(r'\s+', '', extract.re_first_or_blank(r'(?si)IBAN.*?(ES[\d\s]+)', text))
    return iban


def get_accounts_parsed(resp_text: str, logger: ScrapeLogger) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]

    # <tr id="I0:A2:al.F_0.F4_0.A1:T" class="_c1  _c1">
    # <td colspan="1" class="decalrupt1 decal1 _c1 i _c1"><a id="I0:A2:al.F_0.F4_0.A1:L"
    # href="https://www.targobank.es/es/banque/mouvements.html?webid
    # =6ecb0eb794f515445ea6cb0e06193cc62066f607119726006c993e755a6b324a" target="_self"><span class="_c1
    # ei_sdsf_title _c1">CREDITO CON GARANTIA PERSONAL</span>   <span class="nowrap">I INCLAM SA</span>
    # <span>-</span>   <span class="nowrap doux">1083 0500035849</span></a>  </td><td class="d nowrap _c1 i
    # ei_sdsf_solde _c1"><span class="ei_sdsf_montant _c1 neg _c1">-247.234,94 EUR</span></td><td
    # id="I0:A2:al.F_0.F4_0.A1:A:T" class="a_actions nowrap _c1 i _c1"><a id="I0:A2:al.F_0.F4_0.A1:A:C1"
    # title="Acciones" href="#" class="needscript act popmenu"><span>Acciones</span></a><span class="hideifscript"><a
    #  href="https://www.targobank.es/es/banque/virements/vplw_vi.html?_widdeb
    # =6ecb0eb794f515445ea6cb0e06193cc62066f607119726006c993e755a6b324a&amp;_caller=SF"
    # class="hideifscript">Transferencia entre sus cuentas</a> | <a
    # href="https://www.targobank.es/es/banque/virements/vplw_veefue.html?_widdeb
    # =6ecb0eb794f515445ea6cb0e06193cc62066f607119726006c993e755a6b324a&amp;_caller=SF"
    # class="hideifscript">Transferencia nacional o U.E.</a> | <a
    # href="https://www.targobank.es/es/banque/virements/vplw_shis.html" class="hideifscript">Hist&#243;rico de las
    # transferencias</a> | <a href="https://www.targobank.es/es/client/rib.cgi?webid
    # =6ecb0eb794f515445ea6cb0e06193cc62066f607119726006c993e755a6b324a&amp;nb=1" class="hideifscript">IBAN</a> | <a
    # href="https://www.targobank.es/es/banque/MMU2_Default.aspx" class="hideifscript">Documentos V&#237;a
    # Internet</a></span></td>
    # </tr>
    accounts_htmls = re.findall(
        '(?si)<tr[^<]*class="_c1.*?</tr>', resp_text)

    for account_html in accounts_htmls:
        # <span class="_c1 nowrap doux _c1">2899 8400216756</span>  -- ok
        # <span class="_c1 nowrap doux _c1">29961000342332</span>  -- skip
        iban_part = extract.re_first_or_blank(
            r'<span class="_c1 nowrap doux _c1">([\d\s]+)</span>',
            account_html
        ).strip()

        title = extract.re_first_or_blank(
            '(?s)<span class="_c1 ei_sdsf_title _c1">(.*?)</span>',
            account_html
        )

        if not any(m in title for m in ['CREDITO', 'CUENTA']):
            logger.info("Account '{}' is not a cuenta/credito. Skip".format(title))
            continue

        if not iban_part:
            logger.error(
                "Can't parse iban_part. "
                "Check the scraper. Skip the account: {}. Account HTML: {}".format(
                    title,
                    account_html
                )
            )
            continue

        iban_parts = iban_part.split(' ')
        if len(iban_parts) != 2:
            logger.warning(
                "Can't dedicate branch and account_no suffix from iban_part '{}'. "
                "Probably, it's not a current/credit account. Skip the account: {}. Account HTML: {}".format(
                    iban_part,
                    title,
                    account_html
                )
            )
            continue

        branch, acc_no = iban_parts  # tuple, 2 vals

        try:
            account_iban = iban_builder.build_iban_complex('ES', ENTINY_IBAN_DIGITS, branch, acc_no)
        except Exception as exc:
            logger.error("Can't build IBAN: exc {}. Skip account: {}".format(
                exc, account_html
            ))
            continue

        # 'https://www.targobank.es/es/banque/mouvements.cgi?webid
        # =693094e67fb0a66dcafeeace8f8bffe3c0ecb793c49373d2da028728f56cebe3&rib
        # =02161274510600083697EUR'
        req_movs_url = extract.re_first_or_blank('href="(.*?)"', account_html)
        if 'mouvements' not in req_movs_url:
            logger.info("Account '{}' is not a cuenta/credito (no link to movements). Skip".format(title))
            continue

        # -247.234,94 EUR
        balance_str = extract.re_first_or_blank('<span class="ei_sdsf_montant _c1 (neg|pos) _c1">(.*?)</span>',
                                                account_html)[1]

        balance = convert.to_float(balance_str)
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        currency = balance_str[-3:].upper()

        fin_ent_account_id = account_iban[4:] + currency.upper()
        # iban_pdf_url = extract.get_link_by_text(account_html, '', 'IBAN')

        account_parsed = {
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'req_movs_url': req_movs_url,
            # 'iban_pdf_url': iban_pdf_url,
            'title': title,
            'account_no': account_iban,
            'financial_entity_account_id': fin_ent_account_id  # 02162899648800142803EUR
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _clean_descr(descr_raw: str, oper_date: str) -> str:
    """
    >>> t = '27/01/2021 CUO PRES 23270 29911000320838 23270 29911000320838  Fecha de valor:  27/01/2021  Fecha de valor:  27/01/2021 -265,43 EUR'
    >>> d = '27/01/2021'
    >>> _clean_descr(t, d)
    'CUO PRES 23270 29911000320838 23270 29911000320838'

    >>> t = '27/01/2021 CUO PRES 23270 29911000320838 23270 29911000320838'
    >>> d = '27/01/2021'
    >>> _clean_descr(t, d)
    'CUO PRES 23270 29911000320838 23270 29911000320838'

    >>> t = 'CUO PRES 23270 29911000320838 23270 29911000320838'
    >>> d = '27/01/2021'
    >>> _clean_descr(t, d)
    'CUO PRES 23270 29911000320838 23270 29911000320838'

    >>> t = "Detalles  20/01/2021  Cliquer pour déplier ou plier le détail de l\'opération  VIGUECONS ESTEVEZ, S.L. NOTPROVIDED TRASPASO A TBANEUR2388  Fecha de valor:  20/01/2021  Fecha de valor:  20/01/2021 +1.000,00 EUR"
    >>> d = '20/01/2021'
    >>> _clean_descr(t, d)
    'VIGUECONS ESTEVEZ, S.L. NOTPROVIDED TRASPASO A TBANEUR2388'
    """
    # all cases: -a 22622 01/01/2021
    descr1 = descr_raw.lstrip(oper_date)
    descr2 = descr1.split('Fecha de valor:')[0]
    descr3 = re.sub(r"(?si)Detalles\s*\d+/\d+/\d+\s*Cliquer pour déplier ou plier le détail de l\'opération", '', descr2)
    descr4 = descr3.strip()
    descr5 = re.sub(r'\s\s+', ' - ', descr4)  # replace new line to ' - '
    return descr5


def parse_mov_4columns(cells: List[str], temp_balance: float) -> Tuple[MovementParsed, str]:
    """Parses dev/resp_movs_4_columns_view.html
    :returns (movement_parsed, err_reason) for 4-column movement"""
    # -a 22622
    operation_date = cells[0]
    value_date = cells[1]
    descr = _clean_descr(cells[2], operation_date)
    # access -u 264489 -a 14523 has additional column Cambio
    # with ix=3 in previous UI version, so, it's better to use neg ix

    try:
        amount = convert.to_float(cells[-1])  # cells[-2]
    except Exception as exc:
        reason = "can't parse amount: EXC `{}`".format(exc)
        return {}, reason

    mov_parsed = {
        'operation_date': operation_date,
        'value_date': value_date,
        'description': descr,
        'amount': amount,
        'temp_balance': temp_balance
    }
    return mov_parsed, ""


def parse_mov_3columns(cells: List[str], temp_balance: float) -> Tuple[MovementParsed, str]:
    """Parses dev/resp_movs_3_columns_view.html (-a 22622)
    :returns (movement_parsed, err_reason) for 3-column movement
    """

    operation_date = cells[0]
    # Extract value_date from the column with description
    value_date_msg = extract.re_first_or_blank(r'Fecha de valor:\s+\d+/\d+/\d+', cells[1])
    if not value_date_msg:
        reason = "can't parse value date"
        return {}, reason
    value_date = extract.re_first_or_blank(r'\d+/\d+/\d+', value_date_msg)  # 20/03/2019
    descr = _clean_descr(cells[1], operation_date)

    try:
        amount = convert.to_float(cells[-1])  # cells[-2]
    except Exception as exc:
        reason = "can't parse amount: EXC `{}`".format(exc)
        return {}, reason

    mov_parsed = {
        'operation_date': operation_date,
        'value_date': value_date,
        'description': descr,
        'amount': amount,
        'temp_balance': temp_balance
    }
    return mov_parsed, ""


def get_movements_parsed(resp_text: str, fin_ent_acc_id: str, logger: ScrapeLogger) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]

    movements_table_html = extract.re_first_or_blank(
        '(?si)<table width="100%" cellspacing="1" summary="" class="[^"]*liste[^"]*">.*?</table>',
        resp_text
    ) or extract.re_first_or_blank(
        '(?si)<table cellspacing="1" summary="" class="[^"]*liste[^"]*" style="width:100%;">.*?</table>',
        resp_text
    )

    # <tr>
    # <td class="h c nowrap _c1 i _c1">26/11/2018</td><td class="h c nowrap _c1 i _c1">26/11/2018</td><td class="g
    # ei_decal1 _c1 i _c1"> <div>
    # <div id="I1:d1.D4:A:ub.ut.F3_0.F4_0.E:D">
    # <div id="I1:d1.D4:A:ub.ut.F3_0.F4_0.E:button" title="Desplegar">
    # <a id="I1:d1.D4:A:ub.ut.F3_0.F4_0.E:A" class="_c2 afficher _c2 pointer"> </a>   CNF VTO 24/11/2018 - REMESA DE
    # </div><div id="I1:d1.D4:A:ub.ut.F3_0.F4_0.E:content" class="hideifscript">
    #  01/10/2018-BIOS TECHNOLOGY SOLU
    # </div>
    # </div>
    # </div> </td><td class="d nowrap h _c1 i _c1"><span class="_c1 neg _c1">-92.764,45 EUR</span></td><td class="d
    # nowrap h _c1 i _c1">-247.234,94 EUR</td>
    # </tr>
    movements_htmls = re.findall(
        r'(?si)<tr>\s*<td class="h.*?</tr>',
        movements_table_html
    )

    # If 'Cuyas operaciones registradas' (registered movements) at the movs page, then
    # Saldo is including future movs.
    # In this case extract balance from 'Cuyas operaciones registradas'

    # <span class="nowrap">Saldo al 26/01/2019   :</span><span class="...">+0,00 EUR</span>

    # '<span>Cuyas operaciones futuras: <span class="..."><span class="...">-39,19 EUR</span> </span></span>'
    err_msg = ("{}: get_movements_parsed: can't parse temp_balance. Check the layout. "
               "Skip now. RESPONSE:\n{}".format(fin_ent_acc_id, resp_text))
    for pattern, section in [
        (r'(?si)Cuyas operaciones registradas:</span>(.*?)</span>',
         'Registered operations'),  # -a 20702
        (r'(?si)Saldo[^<]*</span>\s*<span[^>]*>(.*?)</span>',
         'Saldo'),  # -a 22622
    ]:
        temp_balance_str = extract.re_first_or_blank(
            pattern,
            resp_text
        )
        if temp_balance_str:
            try:
                temp_balance = convert.to_float(extract.remove_tags(temp_balance_str))
                logger.info("{}: got balance from '{}' section".format(
                    fin_ent_acc_id,
                    section
                ))
                break
            except Exception as exc:
                logger.error(err_msg)
                return []
    else:
        logger.error(err_msg)
        return []

    for mov_html in movements_htmls:

        # ['19/05/2017', '19/05/2017', 'S.T.M.- GRUPA D.O.O. NOTPROVIDED FACTURA 1712002506',
        #  '+ 2.601,31 EUR', '+ 101.062,09 EUR']
        cells = [extract.remove_tags(col_html) for col_html in
                 re.findall('(?si)<td[^>]*>(.*?)</td', mov_html)]

        # for a linter
        mov_parsed = {}  # type: MovementParsed

        if len(cells) == 4:
            mov_parsed, reason = parse_mov_4columns(cells, temp_balance)
        elif len(cells) == 3:
            mov_parsed, reason = parse_mov_3columns(cells, temp_balance)
        else:
            reason = 'Unexpected number of the columns'
        if reason:
            logger.error("{}: {}. Cells: {}. Skip movements".format(
                fin_ent_acc_id,
                reason,
                cells
            ))
            return []

        # mov_parsed is always with the fields here
        temp_balance = round(mov_parsed['temp_balance'] - mov_parsed['amount'], 2)
        movements_parsed_desc.append(mov_parsed)

    return movements_parsed_desc
