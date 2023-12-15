import re
from datetime import datetime
from typing import List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed

NO_CORRESP_MARKER = 'No existen registros para la pestaña seleccionada'


def get_num_pages_with_corr(resp_text: str) -> int:
    num_str = extract.re_first_or_blank(r'Página \d+ de (\d+)', resp_text)
    if not num_str:
        return 1
    return int(num_str)


def get_all_cuentas_param_for_corr(resp_text: str) -> str:
    """
    Parses
    <input type="hidden" name="ctasvivas" value="20859660310330231072-AH-C.CTE-#20859660388300470098-AH-DIVI.-#96605800048835-DX-COE-#6001753272-MP--#96605800582518-DX-COE-#4920712131-LD-DCTO-#4920712229-LD-DCTO-#4923169102-LD-CONF-#4924176985-LD-CONF-#">
    :return: '#AH,20859660310330231072#AH,20859660388300470098#DX,96605800048835#MP,6001753272#DX,96605800582518#LD,4920712131#LD,4920712229#LD,4923169102#LD,4924176985#'
    """
    accs_raw_str = extract.form_param(resp_text, 'ctasvivas')
    # '"20859660310330231072-AH-C.CTE-'..
    accs_raw_strs = accs_raw_str.split('#')
    # '#AH,20859660310330231072'
    accs = []  # type: List[str]
    for acc_raw_str in accs_raw_strs:
        tokens = acc_raw_str.split('-')  # ['20859660310330231072', 'AH', 'C.CTE', '']
        if len(tokens) != 4:
            continue
        accs.append('#{},{}'.format(tokens[1], tokens[0]))
    return ''.join(accs) + '#'


def _split(text: str, by='#') -> List[str]:
    """
    :param text: #DX#SE#PR#
    :param by: '#'
    :return: ['DX', 'SE', 'PR']
    """
    vals = text.split(by)
    # drop empty markers
    if vals[0] == '' and vals[-1] == '':
        vals = vals[1:-1]
    return vals


def get_pdf_params(resp_text: str) -> List[str]:
    """See dev_corresp/resp_pdf_data_form.html
    Returns specific req params for each correspondence from the page. Parses
    <form name="formValores">
        <input type="hidden" name="idoperacion" value="527_1">
        <input type="hidden" name="canal" value="IBE">
        <input type="hidden" name="entidad" value="2085">
        <input type="hidden" name="dispositivo" value="INTR">
        <input type="hidden" name="limitCuentas" value="">

        <input type="hidden" name="fechacarta" value="#2020/08/10#2020/08/07#2020/08/07#2020/07/31#2020/07/24#2020/07/23#2020/07/09#2020/07/01#2020/07/01#2020/06/25#2020/06/24#2020/06/24#2020/06/16#2020/06/16#2020/06/16#">
        <input type="hidden" name="descripcion" value="#COM.EXT.AMORTIZACION DE FINANCIACION#TRANSFERENCIAS#INF.PRESTAMOS FACTURACION CENTRALIZADA#EXTRACTO MOVIMIENTOS#TRANSFERENCIAS#COM.EXT.AMORTIZACION DE FINANCIACION#TRANSFERENCIAS#EXTRACTO MOVIMIENTOS#EXTRACTO MOVIMIENTOS#COM.EXT.AMORTIZACION DE FINANCIACION#TRANSFERENCIAS#COM.EXT.AMORTIZACION DE FINANCIACION#EXTRACTOS LIQUIDACION#EXTRACTOS LIQUIDACION#LIQUIDACION INTERESES#">
        <input type="hidden" name="importe" value="#0#125000#0#0#25000#0#45000#0#0#0#100000#0#14,21#9#9#">
        <input type="hidden" name="moneda" value="#ESP#EUR#ESP#ESP#EUR#ESP#EUR#ESP#ESP#ESP#EUR#ESP#USD#EUR#EUR#">
        <input type="hidden" name="numpag" value="#1#1#1#1#1#1#1#1#1#1#1#1#1#1#1#">
        <input type="hidden" name="codcontr" value="#DX#SE#PR#AH#SE#DX#SE#AH#AH#DX#SE#DX#AH#AH#AH#">
        <input type="hidden" name="numcontr" value="#20859660315800582518#999999020042831244       #60901212150039P000007#20859660310330231072#999999006041830664       #20859660315800582518#999999091040730083       #20859660388300470098#20859660310330231072#20859660315800582518#999999076039629346       #20859660315800582518#20859660388300470098#20859660310330231072#20859660310330231072#">
        <input type="hidden" name="indcons" value="#N#N#N#N#N#N#N#N#S#S#S#S#S#S#S#">

        <input type="hidden" name="doc1apag" value="#LF599 #LSE11C#LPR06A#I0031D#LSE11C#LF599 #LSE11C#I0031D#I0031D#LF599 #LSE11C#LF599 #I0111 #I0111 #I5197A#">
        <input type="hidden" name="ver1apag" value="#2#0#0#2#0#2#0#2#2#2#0#2#2#2#4#">
        <input type="hidden" name="codref" value="#200810001990000054#200807000990000015#200808000180021586#200801000330217375#200724001140000001#200723002780000094#200709001390000013#200701002240225463#200701002240225178#200625002400000153#200624001060000015#200624002340000107#200622002060052784#200622002060052193#200617001860040377#">
        <input type="hidden" name="codctaaso" value="#  #AH#AH#  #AH#  #AH#  #  #  #AH#  #  #  #  #">
        <input type="hidden" name="numctaaso" value="#                         #20859660310330231072#20859660310330231072#                         #20859660310330231072#                         #20859660310330231072#                         #                         #                         #20859660310330231072#                         #                         #                         #                         #">
        <input type="hidden" name="accesoduppapel" value="#SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #">
        <input type="hidden" name="accesodupfax" value="#SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #">
        <input type="hidden" name="accesodupmail" value="#SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #SSS   #">
        <input type="hidden" name="claf" value="#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#1 B09417932  00#">
        <input type="hidden" name="idioma" value="#01#01#01#01#01#01#01#01#01#01#01#01#01#01#01#">
        <input type="hidden" name="disponibleonline" value="#S#S#S#S#S#S#S#S#S#S#S#S#S#S#S#">
        <input type="hidden" name="menus" value="#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#SSS#">
    </form>

    :return
        # S#200625002400000153#1 B09417932  00# #LF599 #2#1#DX#20859660315800582518#  #                         #0#ESP#2020/06/25#S#01
        # S#200518000350001242#1 B09417932  00# #I0552 #2#1#AH#20859660310330231072#  #                         #72.6#EUR#2020/05/18#S
    """
    _, vals = extract.build_req_params_from_form_html_patched(resp_text, 'formValores')
    # [1:-1] drops results for leadind and trailing '#' (empty '')
    disponibleonline_vals = _split(vals['disponibleonline'])  # ' S' todo check
    codref_vals = _split(vals['codref'])  # '200810001990000054'
    claf_vals = _split(vals['claf'])  # '1 B09417932  00'
    doc1apag_vals = _split(vals['doc1apag'])  # 'LF599 '
    ver1apag_vals = _split(vals['ver1apag'])  # '2'
    numpag_vals = _split(vals['numpag'])  # '1'
    codcontr_vals = _split(vals['codcontr'])  # 'DX'
    numcontr_vals = _split(vals['numcontr'])  # '20859660310330231072'
    codctaaso_vals = _split(vals['codctaaso'])  # '  '/ 'AH'  ???
    numctaaso_vals = _split(vals['numctaaso'])  # '                         ' / '20859660310330231072' ???
    importe_vals = _split(vals['importe'])  # '14,21'
    moneda_vals = _split(vals['moneda'])  # 'EUR'
    fechacarta_vals = _split(vals['fechacarta'])  # '2020/08/10'
    indcons_vals = _split(vals['indcons'])  # 'S'  todo check
    idioma_vals = _split(vals['idioma'])  # '01'
    # Req params for every PDF from the page
    req_pdf_param_list = []  # type: List[str]
    for i in range(len(claf_vals)):
        req_pdf_param = '#'.join([
            disponibleonline_vals[i],
            codref_vals[i],
            claf_vals[i],
            ' ',  # !
            doc1apag_vals[i],
            ver1apag_vals[i],
            numpag_vals[i],
            codcontr_vals[i],
            numcontr_vals[i],
            codctaaso_vals[i],
            numctaaso_vals[i],
            importe_vals[i],
            moneda_vals[i],
            fechacarta_vals[i],
            indcons_vals[i],
            idioma_vals[i]
        ])
        req_pdf_param_list.append(req_pdf_param)
    return req_pdf_param_list


def get_correspondence_from_list(resp_text: str,
                                 logger: ScrapeLogger) -> Tuple[bool, List[CorrespondenceDocParsed]]:
    corrs = []  # type: List[CorrespondenceDocParsed]
    if NO_CORRESP_MARKER in resp_text:
        return True, []
    pdf_params = get_pdf_params(resp_text)
    corr_table = extract.re_first_or_blank('(?si)<table[^>]+estilotabla.*?</table>', resp_text)
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    corr_ix = 1  # since 1 as the page param
    for tr in trs:
        tds = re.findall('(?si)<td.*?>(.*?)</td>', tr)
        if 'Estado' in tds[1]:
            continue  # header
        corr_date = tds[2]  # 10.08.2020
        corr_type = extract.text_wo_scripts_and_tags(tds[3])
        amount = None
        # Get from
        # '<script type="text/javascript">document.write(dar_formato(\'72,6\'));</script>' -> 72,6 -> 72.6
        # '<script type="text/javascript">document.write(dar_formato(\'9\'));</script>' -> 9 -> 9.00
        amount_str = extract.re_first_or_blank(r"dar_formato\('(.*?)'\)", tds[4].replace('\\', ''))
        if amount_str:
            amount = convert.to_float(amount_str)
        currency_str = tds[5].strip()
        if currency_str and not amount:
            logger.error("WRONG LAYOUT. Can't parse correspondence correctly. "
                         "Skip. Wrong corr:\n{}".format(tr))
            continue
        currency = convert.to_currency_code(currency_str)
        # w/o IBAN's ESXX
        # 20859660315800582518, 60901212150039P000007,
        account_no_raw = tds[6]
        account_no = account_no_raw
        try:
            account_no = iban_builder.build_iban('ES', account_no_raw)
        except:
            pass  # not a valid IBAN, keep it as is
        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_no,
            operation_date=datetime.strptime(corr_date, '%d.%m.%Y'),
            value_date=None,
            amount=amount,
            currency=currency,
            descr='',
            extra={
                'ix': corr_ix,
                'pdf_param': pdf_params[corr_ix - 1]  # -1 for normal ix from the list
            }
        )
        corrs.append(corr)
        corr_ix += 1
    return True, corrs
