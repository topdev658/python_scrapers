import re
from typing import List
from datetime import datetime

from custom_libs import extract
from custom_libs import convert
from project.custom_types import CorrespondenceDocParsed, DOCUMENT_TYPE_CORRESPONDENCE
from .custom_types import ReceiptOption, ReceiptReqParams, AccountForCorrespondence


def get_receipts_options(resp_text: str) -> List[ReceiptOption]:
    """
    Parses

    <A class="ctTxBlBold" href="#" OnClick="nuevaVentana('23','3064971','01287712100000395',
    20190606,20190606,'1','1');return false;">TRANSFERENCIA DE Stin, S.A.</A></TD><TD
    width="28%">&nbsp;</TD>
    </TR>

    OR

    <A class="ctTxBlBold" href="#" OnClick="nuevaVentana('23','2886627','01287712500001871',
    20190606,20190606,'1','1');return false;">LIQUIDACION DE AVAL</A>

    into

    ReceiptOption
    """

    # [("'23','3064971','01287712100000395',20190606,20190606,'1','1'", "DE Stin, S.A."), ...]
    receipt_opts_raw = re.findall(
        r'(?si)<A class="ctTxBlBold"[^>]+nuevaVentana\(([^>]+)\);return[^>]+>'
        r'\w+\s+\w+\s+([^<]+)</A>', resp_text)

    receipts_options = []  # type: List[ReceiptOption]
    for opt in receipt_opts_raw:
        req_params_list = [p.strip("'") for p in opt[0].split(',')]  # ['23', '3064971', ...]
        req_params = ReceiptReqParams(
            semana=req_params_list[0],
            envio=req_params_list[1],
            cuenta=req_params_list[2],
            fecha=req_params_list[3],
            fecha_valor=req_params_list[4]
        )
        receipt_option = ReceiptOption(
            descr_part=opt[1].strip(),  # 'Stin, S.A.'
            req_params=req_params
        )
        receipts_options.append(receipt_option)

    return receipts_options


def get_accounts_for_correspondence(resp_text: str) -> List[AccountForCorrespondence]:
    accs_for_corr = []  # type: List[AccountForCorrespondence]
    accs_el = extract.re_first_or_blank(r'(?si)<select\s+id="CUENTA_sel".*?</select>', resp_text)
    # <option value="01289426140000214">
    #   9426/14.000021.4&nbsp;CTAS CORR. MON. EXTR. RESIDENT
    # </option>
    # -> ('01289426140000214', '9426/14.000021.4')
    opts = re.findall(r'(?si)<option value="(.*?)">(.*?)</option>', accs_el)
    for opt in opts:
        if not opt[0]:
            continue  # skip 'Select account'
        acc_displayed_raw_split = re.split(r'\s', extract.remove_tags(opt[1]))
        acc_for_corr = AccountForCorrespondence(
            account_displayed=acc_displayed_raw_split[0],
            fin_ent_account_id=opt[0]
        )
        accs_for_corr.append(acc_for_corr)
    return accs_for_corr


def get_correspondence_from_list(resp_text: str, account_no: str) -> List[CorrespondenceDocParsed]:
    corrs = []  # type: List[CorrespondenceDocParsed]
    corr_table = extract.re_first_or_blank('(?si)<table[^>]+id="tablaDin_tabla".*?</table>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        """
        <tr id="semana=37envio=1578902cuenta=01289426100003607fecha=20200910persona=40607476tot_pag=1fecha_valor=20200910ind_csf=1ind_anyo=Anum_pag=006">
            <td class="iguales" headers="opc_sel">
                <span class="gwt-CheckBox">
                <input onKeyPress="seleccionar_fila(this);" onclick="seleccionar_fila(this);" type="checkbox" id="check_sel1" name="check_sel1" value="#1#">
                </span>
            </td>
            <td class="fecha" headers="fecha_sel">10/09/2020</td>
            <td headers="concepto_sel">
                <a href="empresas+cuentas+frame?semana=37&amp;envio=1578902&amp;cuenta=01289426100003607&amp;fecha=20200910&amp;persona=40607476&amp;tot_pag=1&amp;fecha_valor=20200910&amp;ind_csf=1&amp;ind_anyo=A" id="enlace_tipo1_1" onClick="tb_popUpLinkHelp(this, 'width=700,height=550,top=0,left=0'); return false;" target="Visualizador" title="LIQUIDACIÓN AMORTIZACIÓN FINANCIACI. Abre ventana nueva" class="for_enlace_02">
                    LIQUIDACIÓN AMORTIZACIÓN FINANCIACI
                    <img class="img_ventananueva_01" src="../../img/linkext.gif" alt="Abre ventana nueva">
                </a>
            </td>
            <td class="numero" headers="importe_sel">109.762,69</td>
        </tr>
        """
        cells = re.findall('(?si)<td.*?</td>', tr)
        if not cells:
            continue
        corr_date_str = extract.remove_tags(cells[1])
        corr_date = datetime.strptime(corr_date_str, '%d/%m/%Y')
        corr_type = DOCUMENT_TYPE_CORRESPONDENCE
        amount_str = extract.remove_tags(cells[3])
        amount = convert.to_float(amount_str)
        descr = extract.text_wo_scripts_and_tags(cells[2])
        req_link = extract.re_first_or_blank('href="(.*?)"', cells[2])
        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=None,
            descr=descr,
            extra={
                'req_link': req_link
            }
        )
        corrs.append(corr)
    return corrs
