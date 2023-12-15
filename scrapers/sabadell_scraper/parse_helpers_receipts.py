import re
from collections import OrderedDict
from datetime import datetime
from typing import List, Dict, Optional

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project.custom_types import CorrespondenceDocParsed
from .custom_types import AccountForCorrespondence


def get_orgs_and_accounts_for_correspondence(resp_text: str) -> Dict[str, List[AccountForCorrespondence]]:
    """
    :return: {org_title: [accounts_for_corr]}
    Parses
        empresasCuentas[3][0] = "CORPEDIFICACIONS, S.L.";
        ...
        empresasCuentas[3][1] = "0105-0001832190$$00810105120001832190 : CUENTA CORRIENTE";
        empresasCuentas[3][2] = "5084-0001577561$$00815084060001577561 : CUENTA CORRIENTE";
        empresasCuentas[3][3] = "0105-0000380544$$00810105110000380544 : CUENTA DEPOSITOS A PLAZO FIJO";
        empresasCuentas[3][4] = "0105-0000380643$$00810105190000380643 : CUENTA DEPOSITOS A PLAZO FIJO";
        empresasCuentas[3][5] = "0901-6023625389$$00810901216023625389 : CUENTA VALORES";
    """
    orgs_titles = re.findall(r'empresasCuentas\[\d+]\[0]\s*=\s*"(.*?)"', resp_text)
    orgs_and_accounts = {}  # type: Dict[str, List[AccountForCorrespondence]]
    for org_ix, org_title in enumerate(orgs_titles):
        orgs_and_accounts[org_title] = []
        # ["0105-0001832190$$00810105120001832190 : CUENTA CORRIENTE", ...]
        accounts_strs = re.findall(r'empresasCuentas\[{}]\[\d+]\s*=\s*"([^"]+\$\$[^"]+)"'.format(org_ix), resp_text)
        for acc_str in accounts_strs:
            req_param, account_title = acc_str.split('$$')
            acc = AccountForCorrespondence(
                account_title=account_title,  # '00810105120001832190 : CUENTA CORRIENTE'
                req_param=req_param  # '0105-0001832190'
            )
            orgs_and_accounts[org_title].append(acc)
    return orgs_and_accounts


def get_correspondence_docs_parsed(resp_text: str, account_req_param: str) -> List[CorrespondenceDocParsed]:
    """
    Parses

    <script>refDocument[parseInt("0")]="20210603000000244684";refPdf[parseInt("0")]="PROC=3&ACCI=1&VISO=PDF&TIPO=DCON&CCON=01DV 101050000018280&FCHD=03/06/2021&NUMO=2021-06-03-10.40.06.768441";refCheck[parseInt("0")]="0";refLeido[parseInt("0")]="N";</script>

    <tr class="fila2" id="rowToStylize_0">

        <td headers="checker" class=a11 valign=center align=center>
            <input type="checkbox" name="ref_0" onclick="javascript:changeStyle('0');"/></td>
        <td headers="fecha" axis="number" class=a11 height=15 valign=center align=center nowrap id="fecha_0" title="2021-06-03"  onClick="javascript:downloadDoc(0);" onmouseover="javascript:this.style.cursor='hand';">
            03/06/2021&nbsp;&nbsp;
        </td>
        <td headers="tipo" axis="sstring" class=a11 height=15 valign=center align=left wrap id="tipo_0"  title="TRANSFERENCIA A LATELIE DE MIKI BEUMALA, S.L." onClick="javascript:downloadDoc(0);" onmouseover="javascript:this.style.cursor='hand';">
            TRANSFERENCIA A LATELIE DE MIKI BEUMALA, S.L.
        </td>
        <td headers="cuenta" axis="sstring" class=a11 height=15 valign=center align=center nowrap id="cuenta_0"  onClick="javascript:downloadDoc(0);" onmouseover="javascript:this.style.cursor='hand';">
            &nbsp;&nbsp;00810105120001828089
        </td>
        <td headers="importe" axis="number" class=a11 height=15 valign=center align=right nowrap id="importe_0" title="-5130.40"  onClick="javascript:downloadDoc(0);" onmouseover="javascript:this.style.cursor='hand';">
            &nbsp;&nbsp;-5.130,40&nbsp;&euro;
        </td>
        <td headers="categoria" axis="sstring" class=a11 height=15 valign=center align=left id="categoria_0"  onClick="javascript:downloadDoc(0);" onmouseover="javascript:this.style.cursor='hand';">
            &nbsp;&nbsp;Movimientos y otros
        </td>
        <td headers="pdf" class=a11 height=15 valign=center align=center>
            <a href="javascript:downloadDoc(0);" style="text-decoration:none"><img src="/txempbs/images/pdf.gif" width="16" height="16" style="border:none"/></a>
        </td>
        <input type="hidden" name="mail[0].contrato" value="101050000018280"/>
        <input type="hidden" name="mail[0].entidad" value="01"/>
        <input type="hidden" name="mail[0].idDocument" value="20210603000000244684"/>
        <input type="hidden" name="mail[0].producto" value="DV"/>
        <input type="hidden" name="mail[0].read" value=""/>
        <input type="hidden" name="mail[0].idPdf" value="PROC=3&ACCI=1&VISO=PDF&TIPO=DCON&CCON=01DV 101050000018280&FCHD=03/06/2021&NUMO=2021-06-03-10.40.06.768441"/>
    </tr>
    """
    corrs = []  # type: List[CorrespondenceDocParsed]
    trs = re.findall(r'(?si)<tr class="fila\d*".*?</tr>', resp_text)
    for tr in trs:
        # '0'
        num = extract.re_first_or_blank(r'mail\[(\d+)]', tr)
        # 101050000018280
        idcontrato = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].contrato"\s+value="(.*?)"', tr)
        # '01'
        entidad = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].entidad"\s+value="(.*?)"', tr)
        # '20210505000000319756'
        id_document = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].idDocument"\s+value="(.*?)"', tr)
        # '"PROC=3&ACCI=1&VISO=PDF&TIPO=DCON&CCON=01DV+101050000018280&FCHD=05/05/2021&NUMO=2021-05-05-00.41.00.156904"'
        id_pdf = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].idPdf"\s+value="(.*?)"', tr)
        # 'DV'
        producto = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].producto"\s+value="(.*?)"', tr)
        # 'N'
        read_param = extract.re_first_or_blank(r'<input[^<]+name="mail\[\d+].read"\s+value="(.*?)"', tr) or 'N'
        extra = {
            'req_params': OrderedDict([
                ('num', num),
                ('idcontrato', idcontrato),
                ('entidad', entidad),
                ('idDocument', id_document),
                ('idPdf', id_pdf),
                ('producto', producto),
                ('read', read_param),
                ('contrato.selectable-index', account_req_param),  # '0105-0001828089'
                ('isSearcher', 'true')
            ])
        }

        # tds = [extract.text_wo_scripts_and_tags(t) for t in re.findall('(?si)<td.*</td>', tr)]

        # Movimientos y otros
        corr_type = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
            '(?si)<td headers="categoria".*?</td>',
            tr
        ))

        # from 03/06/2021
        oper_date = datetime.strptime(extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
            '(?si)<td headers="fecha".*?</td>',
            tr
        )), '%d/%m/%Y')
        account_no = iban_builder.build_iban(
            'ES',
            # 00810105120001828089
            extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
                '(?si)<td headers="cuenta".*?</td>',
                tr
            ))
        )
        amount = None  # type: Optional[float]
        currency = None  # type: Optional[str]
        # '-5.130,40 €'
        amount_currency = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
            '(?si)<td headers="importe".*?</td>',
            tr
        ))
        if amount_currency:
            # -5130.40
            amount = float(extract.re_first_or_blank('(?si)<td headers="importe"[^>]+title="(.*?)"', tr))
            currency_str = amount_currency.split()[1]
            currency = convert.to_currency_code(currency_str)

        descr = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
            '(?si)<td headers="tipo".*?</td>',
            tr
        ))

        corr_parsed = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=oper_date,
            value_date=None,
            amount=amount,
            currency=currency,
            descr=descr,
            extra=extra  # any extra info appropriate for a specific scraper
        )
        corrs.append(corr_parsed)
    return corrs
