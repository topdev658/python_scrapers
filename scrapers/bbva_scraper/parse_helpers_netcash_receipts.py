import re
from collections import OrderedDict
from datetime import datetime
from typing import List, Optional

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed, DOCUMENT_TYPE_CORRESPONDENCE
from .custom_types import AccountForCorrespondence


def _get_corr_currency(currency_cell: str) -> Optional[str]:
    """
    >>> _get_corr_currency('164.800,00 &euro;')
    'EUR'
    >>> _get_corr_currency('164.800,00 USD')
    'USD'
    """
    currency_str = extract.re_first_or_blank('[a-zA-Z&;€$£]+', currency_cell)
    return convert.to_currency_code(currency_str)


def get_accounts_for_corr(resp_text: str) -> List[AccountForCorrespondence]:
    """Parses
    <select name="listaCuentas" size="8" multiple>
        <option value="0@EUR0182 2351 41 0201507277">0182 2351 41 0201507277 EUR   &nbsp;</option>
        <option value="1@EUR0182 2351 42 0201513528">0182 2351 42 0201513528 EUR   &nbsp;</option>
        <option value="2@USD0182 2351 48 2012008039">0182 2351 48 2012008039 USD   &nbsp;</option>
    </select>
    """
    accounts_for_corr = []  # type: List[AccountForCorrespondence]
    accounts_el = extract.re_first_or_blank('(?si)<select .*? name="listaCuentas"(.*?)</select>',
                                            resp_text)
    acc_htmls = re.findall('(?si)<option.*?</option>', accounts_el)
    for acc_html in acc_htmls:
        req_param = extract.re_first_or_blank('value="(.*?)"', acc_html)
        ix = req_param.split('@')[0]
        currency = extract.re_first_or_blank('@([A-Z]+)', req_param)
        account_no_raw = extract.re_first_or_blank('@{}([0-9 ]+)'.format(currency), req_param)
        account_no = iban_builder.build_iban('ES', account_no_raw)
        # '0182 2351 41 0201507277 EUR'
        title = extract.remove_tags(extract.re_first_or_blank('>([^<]+)<', acc_html))
        acc_for_corr = AccountForCorrespondence(
            account_no=account_no,
            req_param=req_param,
            title=title,
            ix=ix,
            currency=currency
        )
        accounts_for_corr.append(acc_for_corr)
    return accounts_for_corr


def get_corr_organization_title(resp_text: str) -> str:
    """Parses resp_corr_filtered
    ...
        <tr>
        <td class="bgfila2" colspan="2">
            <p class="tright"><strong>[Cuenta 1/3]</strong></p>
        </td>
    </tr>
    <tr>
        <td class="bgfila2"><p class="txtdato"><strong>0182 2351 41 0201507277&nbsp;EUR&nbsp;&nbsp;<br>GAMBASTAR S.L.  </strong></p></td>
        <td class="bgfila2"><p class="txtdato"><strong>BANCO BILBAO VIZCAYA ARGENTARIA S.A.    <br>BURGOS-SORIA EMPRESAS                   </strong></p></td>
    </tr>
    """
    org_title = extract.re_first_or_blank(
        r'(?si)\[Cuenta.*?<br>(.*?)</strong></p></td>', resp_text
    ).strip()
    return org_title


def get_correspondence_from_list(
        logger: ScrapeLogger,
        resp_text: str,
        account_no: str) -> List[CorrespondenceDocParsed]:
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank(
        """(?si)<table class='tabla_espana' border=0 cellpadding=3 cellspacing=0 width="100%">.*?</table>""",
        resp_text
    )
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        cells = [extract.remove_tags(cell) for cell in re.findall('<td[^>]*>(.*?)</td>', tr)]
        if len(cells) != 7:
            continue
        # Header
        if cells[1] == 'Documento':
            continue
        amount = convert.to_float(cells[4])
        currency = _get_corr_currency(cells[4])
        if not currency:
            logger.warning("{}: get_correspondence_from_list: can't extract currency. Use None. "
                           "RESPONSE PART:\n{}".format(account_no, cells[4]))
        descr = cells[1]
        corr_type = DOCUMENT_TYPE_CORRESPONDENCE
        corr_date = datetime.strptime(cells[3], '%d-%m-%Y')
        # ['0182', '2351', '083', '000003480', 'E5', '4480277254', 'N', '11-08-2020', 1]
        # -> for
        # https://www.bbvanetcash.com/SESTLSB/bbvacashm/servlet/OperacionCBTFServlet
        # ?proceso=TLBHPrCVConsultaAvanzada
        # &operacion=TLBHOpCVVisualizacionPDF
        # &accion=execute
        # &codBancsb=0182
        # &codCOfici=2351
        # &codCContr=083
        # &codCFolio=000003480
        # &codNMes=E5
        # &qnuNEnvio=4480277254
        # &xsnConsulta=S
        # &fechaDocumento=11-08-2020
        # &xtiTipocta=P
        # &tipoOperacion=V
        req_pdf_params_list = [
            re.sub(r"['\s]", '', el)
            for el in
            extract.re_first_or_blank(r'javascript:lanzarPDF\((.*?)\);', tr).split(',')
        ]
        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=currency,
            descr=descr,
            extra={
                'req_pdf_params': OrderedDict([
                    ('proceso', 'TLBHPrCVConsultaAvanzada'),
                    ('operacion', 'TLBHOpCVVisualizacionPDF'),
                    ('accion', 'execute'),
                    ('codBancsb', req_pdf_params_list[0]),
                    ('codCOfici', req_pdf_params_list[1]),
                    ('codCContr', req_pdf_params_list[2]),
                    ('codCFolio', req_pdf_params_list[3]),
                    ('codNMes', req_pdf_params_list[4]),
                    ('qnuNEnvio', req_pdf_params_list[5]),
                    ('xsnConsulta', 'S'),
                    ('fechaDocumento', req_pdf_params_list[7]),
                    ('xtiTipocta', 'P'),
                    ('tipoOperacion', 'V')
                ])
            }
        )
        corrs_from_list.append(corr)
    return corrs_from_list
