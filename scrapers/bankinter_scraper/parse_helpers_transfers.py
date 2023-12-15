import glob
import html
import os
import re
import traceback
import unittest
from datetime import datetime
from typing import Dict, List, Tuple

from fitz import fitz  # pymupdf importing name

from custom_libs import extract
from custom_libs import pdf_funcs
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import DBTransferFilter, TransferParsed, MovementParsed

AVIA_NORMAL_TRANSFER_BANK_CODE = 'TRAN'
AVIA_FACTURAS_CONTRATO_GIP_TRANSFER_BANK_CODE = 'FACTURAS CONTRATO GIP'
AVIA_SWIFT_TRANSFER_BANK_CODE = 'SWIFT'
AVIA_TRASPASO_D_TRASNFER_BANK_CODE = 'TRASPASO D.'

EMPTY_TRANSFER_FIELD_DEFAULT_VALUE = 'N/A'


# JF: for dev
def parse_normal_transfer(
        document_text: str):
    cwd = os.getcwd()
    if document_text == '':
        document_text = open('scrapers\\bankinter_scraper\\dev\\tran_normal_transfer_pdf_text.txt', 'r').read()
    return


# JF: for dev
def get_transfer_parsed(transfer_filters):
    open('dev\\misc.xml')
    with open('') as f:
        f.read()
        return


# JF: for dev
def _save_pdf_file(self,
                   pdf_content: bytes,
                   transfer_type: str) -> None:
    """Extracts text from the first page of pdf document (fast)"""
    if not pdf_content:
        return

    # fitz.Document == fitz.open; fitz.Document provides autocomplete
    pdf = fitz.Document(stream=pdf_content, filetype="pdf")
    now = datetime.now()
    str_now = str(now).replace(':', '-')
    file_name = transfer_type + '-' + str_now
    location = 'scrapers\\bankinter_scraper\\dev\\transfer_files\\'

    pdf.save(location + file_name + ".pdf")

    flags = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE
    text_page = pdf.load_page(0).get_displaylist().get_textpage(flags)

    text = text_page.extractHTML()
    f = open(location + file_name + '.html', 'w')
    f.write(text)
    f.close()

    text = text_page.extractText()
    f = open(location + file_name + '.txt', 'w')
    f.write(text)
    f.close()

    return


def parse_transfer_fields_from_movement(
        logger: ScrapeLogger,
        fin_ent_account_id: str,
        movement_parsed: MovementParsed) -> Tuple[bool, Dict[str, str]]:
    parsed_transfer_fields = {}  # type: Dict[str, str]
    try:
        transfer_filters = movement_parsed['transfer_filters']
        bank_code = transfer_filters[0].BankCode  # type: str
        if bank_code == AVIA_TRASPASO_D_TRASNFER_BANK_CODE:
            parsed_transfer_fields = parse_traspaso_d_transfer_fields(logger, movement_parsed['description'])
        else:
            # TODO VB: why w/o log msg?
            return False, parsed_transfer_fields
    except Exception as _e:
        logger.error(
            '{}: failed parsing transfers fields from movement: {} '
            'HANDLED EXCEPTION: {}'.format(
                fin_ent_account_id,
                movement_parsed,
                traceback.format_exc()
            )
        )
        return False, parsed_transfer_fields

    return True, parsed_transfer_fields


def get_empty_receipt_parsed_transfer_fields(default_text: str) -> Dict[str, str]:
    parsed_transfer_fields = {}  # type: Dict[str, str]

    parsed_transfer_fields['Ordenante'] = default_text
    parsed_transfer_fields['Observaciones'] = default_text
    parsed_transfer_fields['Banco ordenante'] = default_text
    parsed_transfer_fields['Referencia beneficiario'] = default_text
    parsed_transfer_fields['Referencia ordenante'] = default_text
    parsed_transfer_fields['Por cuenta de'] = default_text
    return parsed_transfer_fields


def parse_transfer_fields_from_pdf(
        logger: ScrapeLogger,
        transfer_filters: List[DBTransferFilter],
        pdf_content: bytes) -> Dict[str, str]:
    parsed_transfer_fields = {}  # type: Dict[str, str]
    try:
        if not transfer_filters:
            return parsed_transfer_fields

        bank_code = transfer_filters[0].BankCode
        # _save_pdf_file(pdf_content, bank_code)
        if bank_code == AVIA_NORMAL_TRANSFER_BANK_CODE:
            pdf_html = pdf_funcs.get_text(pdf_content, 'html')
            parsed_transfer_fields = parse_normal_transfer_fields(logger, pdf_html)

        if bank_code == AVIA_FACTURAS_CONTRATO_GIP_TRANSFER_BANK_CODE:
            pdf_html = pdf_funcs.get_text(pdf_content, 'html')
            parsed_transfer_fields = parse_facturas_contrato_gip_transfer_fields(logger, pdf_html)

        if bank_code == AVIA_SWIFT_TRANSFER_BANK_CODE:
            pdf_text = pdf_funcs.get_text(pdf_content)
            parsed_transfer_fields = parse_swift_transfer_fields(logger, pdf_text)

    except Exception as _e:
        logger.error(
            'Failed parsing transfers fields: {!r} '
            'HANDLED EXCEPTION: {}'.format(pdf_content, traceback.format_exc()))
    finally:
        return parsed_transfer_fields


def parse_normal_transfer_fields(
        logger: ScrapeLogger,
        html_text: str) -> Dict[str, str]:
    parsed_transfer_fields = {}  # type: Dict[str, str]
    # '''
    # <div id="page0" style="position:relative;width:595pt;height:280pt;background-color:white">
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Fecha</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:85pt"><span style="font-family:Bankinter,serif;font-size:7pt">Oficina</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:269pt"><span style="font-family:Bankinter,serif;font-size:7pt">Moneda</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:85pt"><span style="font-family:Bankinter,serif;font-size:7pt">9435 - C.G. VIZCAYA</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:269pt"><span style="font-family:Bankinter,serif;font-size:7pt">EUR</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:311pt"><span style="font-family:Bankinter,serif;font-size:7pt">N&#xfa;mero de Transferencia</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:311pt"><span style="font-family:Bankinter,serif;font-size:7pt">202101020075110</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:61pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:9pt;color:#f56900">Abono por transferencia inmediata</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:245pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Titulares</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:253pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:6pt">ESERGUI DISTESER SL</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:245pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:7pt">Para cualquier informaci&#xf3;n, ll&#xe1;menos a Banca Telef&#xf3;nica, 91 657 88 00</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:254pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:6pt">F00805  R. M. MADRID, T.1.857, F220, H.9.643, N.I.F., A-28-157360</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:72pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Ordenante</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:72pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Por cuenta de</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:79pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">ANNA VAQUERO SALA</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:97pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Observaciones</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:97pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Beneficiario</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:104pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">factura 0C120480-Anna Vaquero Sala</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:104pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:6pt">AVIA</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:134pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Banco ordenante</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:134pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Referencia beneficiario</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:141pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">CAIXABANK</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:147pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">2100 0716</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:141pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:6pt">CORE</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:159pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Referencia ordenante</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:159pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Liquidaci&#xf3;n transferencia</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Nominal:       </span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:329pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Comisiones:    </span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:404pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Correo:        </span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:478pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Total gastos</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:7pt">330,00</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:329pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:404pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:478pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:186pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Tipo de gasto:</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Fecha emisi&#xf3;n</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:141pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Fecha valor</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt;color:#f56900">Importe abonado</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:141pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt;color:#f56900">330,00</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:214pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Abonamos en su cuenta el apunte que se detalla.</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:224pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">N&#xba; IBAN</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:224pt;left:155pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">BIC</span></b></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:234pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">ES50 0128 9435 7401 0000 9167</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:234pt;left:155pt"><span style="font-family:Bankinter,serif;font-size:6pt">BKBKESMM</span></p>
    # <p style="position:absolute;white-space:pre;margin:0;padding:0;top:260pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:5pt">A04           01  20210102  53  00005502598</span></p>
    # </div>
    # '''
    try:

        unescaped_text = html.unescape(html_text)
        lines = re.findall(r'(?si)(top):(.*?)pt;(left):(.*?)pt.*?<span.*?>(.*?)</span', unescaped_text)
        # '''
        # <class 'list'>: [('top', '39', 'left', '28', 'Fecha'),
        # ('top', '39', 'left', '85', 'Oficina'),
        # ('top', '39', 'left', '269', 'Moneda'),
        # ('top', '48', 'left', '28', '02-01-21'),
        # ('top', '48', 'left', '85', '9435 - C.G. VIZCAYA'),
        # ('top', '48', 'left', '269', 'EUR'),
        # ('top', '39', 'left', '311', 'Número de Transferencia'),
        # ('top', '48', 'left', '311', '202101020075110'),
        # ('top', '61', 'left', '28', 'Abono por transferencia inmediata'),
        # ('top', '245', 'left', '28', 'Titulares'),
        # ('top', '253', 'left', '28', 'ESERGUI DISTESER SL'),
        # ('top', '245', 'left', '246', 'Para cualquier información, llámenos a Banca Telefónica, 91 657 88 00'),
        # ('top', '254', 'left', '246', 'F00805  R. M. MADRID, T.1.857, F220, H.9.643, N.I.F., A-28-157360'),
        # ('top', '72', 'left', '28', 'Ordenante'),
        # ('top', '72', 'left', '255', 'Por cuenta de'),
        # ('top', '79', 'left', '28', 'ANNA VAQUERO SALA'),
        # ('top', '97', 'left', '28', 'Observaciones'),
        # ('top', '97', 'left', '255', 'Beneficiario'),
        # ('top', '104', 'left', '28', 'factura 0C120480-Anna Vaquero Sala'),
        # ('top', '104', 'left', '255', 'AVIA'),
        # ('top', '134', 'left', '28', 'Banco ordenante'),
        # ('top', '134', 'left', '255', 'Referencia beneficiario'),
        # ('top', '141', 'left', '28', 'CAIXABANK'),
        # ('top', '147', 'left', '28', '2100 0716'),
        # ('top', '141', 'left', '255', 'CORE'),
        # ('top', '159', 'left', '28', 'Referencia ordenante'),
        # ('top', '159', 'left', '255', 'Liquidación transferencia'),
        # ('top', '166', 'left', '255', 'Nominal:       '),
        # ('top', '166', 'left', '329', 'Comisiones:    '),
        # ('top', '166', 'left', '404', 'Correo:        '),
        # ('top', '166', 'left', '478', 'Total gastos'),
        # ('top', '174', 'left', '255', '330,00'),
        # ('top', '174', 'left', '329', '0,00'),
        # ('top', '174', 'left', '404', '0,00'),
        # ('top', '174', 'left', '478', '0,00'),
        # ('top', '186', 'left', '28', 'Tipo de gasto:'),
        # ('top', '194', 'left', '28', 'Fecha emisión'),
        # ('top', '194', 'left', '141', 'Fecha valor'),
        # ('top', '194', 'left', '255', 'Importe abonado'),
        # ('top', '202', 'left', '28', '02-01-21'),
        # ('top', '202', 'left', '141', '02-01-21'),
        # ('top', '202', 'left', '255', '330,00'),
        # ('top', '214', 'left', '28', 'Abonamos en su cuenta el apunte que se detalla.'),
        # ('top', '224', 'left', '28', 'Nº IBAN'),
        # ('top', '224', 'left', '155', 'BIC'),
        # ('top', '234', 'left', '28', 'ES50 0128 9435 7401 0000 9167'),
        # ('top', '234', 'left', '155', 'BKBKESMM'),
        # ('top', '260', 'left', '246', 'A04           01  20210102  53  00005502598')]
        # '''
        ordenante_header = [x for x in lines if x[4] == 'Ordenante'][0]
        observaciones_header = [x for x in lines if x[4] == 'Observaciones'][0]
        banco_ordenante_header = [x for x in lines if x[4] == 'Banco ordenante'][0]
        referencia_ordenante_header = [x for x in lines if x[4] == 'Referencia ordenante'][0]
        tipo_gasto_header = [x for x in lines if 'Tipo de gasto' in x[4]][0]

        ordenante_header_left = ordenante_header[3]

        lines_under_ordenante = [x for x in lines if x[3] == ordenante_header_left]
        ordenante_header_index = lines_under_ordenante.index(ordenante_header)
        observaciones_header_index = lines_under_ordenante.index(observaciones_header)
        banco_ordenante_header_index = lines_under_ordenante.index(banco_ordenante_header)
        referencia_ordenante_header_index = lines_under_ordenante.index(referencia_ordenante_header)
        tipo_gasto_header_index = lines_under_ordenante.index(tipo_gasto_header)

        ordenante_value_lines = lines_under_ordenante[ordenante_header_index + 1:observaciones_header_index]
        ordenante = ''  # type: str
        for line in ordenante_value_lines:
            ordenante = ordenante + line[4]
            ordenante.strip()

        observaciones_value_lines = lines_under_ordenante[observaciones_header_index + 1:banco_ordenante_header_index]
        observaciones = ''  # type: str
        for line in observaciones_value_lines:
            observaciones = observaciones + line[4]
            observaciones.strip()

        banco_ordenante_value_lines = \
            lines_under_ordenante[banco_ordenante_header_index + 1:referencia_ordenante_header_index]
        banco_ordenante = ''  # type: str
        for line in banco_ordenante_value_lines:
            banco_ordenante = banco_ordenante + line[4]
            banco_ordenante.strip()

        referencia_ordenante_value_lines = \
            lines_under_ordenante[referencia_ordenante_header_index + 1:tipo_gasto_header_index]
        referencia_ordenante = ''  # type: str
        for line in referencia_ordenante_value_lines:
            referencia_ordenante = referencia_ordenante + line[4]
            referencia_ordenante.strip()

        referencia_beneficiario_header = [x for x in lines if x[4] == 'Referencia beneficiario'][0]
        liquidacion_header = [x for x in lines if x[4] == 'Liquidación transferencia'][0]
        referencia_beneficiario_header_left = referencia_beneficiario_header[3]
        lines_under_beneficiario = [x for x in lines if x[3] == referencia_beneficiario_header_left]

        referencia_beneficiario_header_index = lines_under_beneficiario.index(referencia_beneficiario_header)
        liquidacion_header_index = lines_under_beneficiario.index(liquidacion_header)

        referencia_beneficiario_value_lines = \
            lines_under_beneficiario[referencia_beneficiario_header_index + 1:liquidacion_header_index]
        referencia_beneficiario = ''  # type: str
        for line in referencia_beneficiario_value_lines:
            referencia_beneficiario = referencia_beneficiario + line[4]
            referencia_beneficiario.strip()

        parsed_transfer_fields['Ordenante'] = ordenante
        parsed_transfer_fields['Observaciones'] = observaciones
        parsed_transfer_fields['Banco ordenante'] = banco_ordenante
        parsed_transfer_fields['Referencia beneficiario'] = referencia_beneficiario
        parsed_transfer_fields['Referencia ordenante'] = referencia_ordenante
    except Exception as _e:
        logger.error(
            'Failed parsing swift transfers fields: {} '
            'HANDLED EXCEPTION: {}'.format(html_text, traceback.format_exc()))
    finally:
        return parsed_transfer_fields


def parse_facturas_contrato_gip_transfer_fields(
        logger: ScrapeLogger,
        html_text: str) -> Dict[str, str]:
    """ Parses
        <div id="page0" style="position:relative;width:595pt;height:841pt;background-color:white">
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:74pt;left:55pt"><span style="font-family:Bankinter,serif;font-size:7pt">Fecha</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:74pt;left:111pt"><span style="font-family:Bankinter,serif;font-size:7pt">Oficina</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:74pt;left:296pt"><span style="font-family:Bankinter,serif;font-size:7pt">Moneda</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:84pt;left:55pt"><span style="font-family:Bankinter,serif;font-size:7pt">20-01-21</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:84pt;left:111pt"><span style="font-family:Bankinter,serif;font-size:7pt">1785 - MALAGA AG.5</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:84pt;left:296pt"><span style="font-family:Bankinter,serif;font-size:7pt">EUR</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:76pt;left:338pt"><span style="font-family:Bankinter,serif;font-size:7pt">N&#xfa;mero transferencia</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:76pt;left:453pt"><span style="font-family:Bankinter,serif;font-size:7pt">Hoja</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:85pt;left:338pt"><span style="font-family:Bankinter,serif;font-size:7pt">      210001</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:85pt;left:453pt"><span style="font-family:Bankinter,serif;font-size:7pt">1</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:107pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:9pt;color:#f56600">Pago por transferencia</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:121pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:9pt;color:#f56600">M&#xe1;s  beneficios  que  nunca.  Consulte sus facturas, elija  cu&#xe1;ndo y c&#xf3;mo y le avisaremos a su m&#xf3;vil o e-mail</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:133pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:9pt;color:#f56600">&#xa1;Gratis!. Antic&#xed;pe el cobro de sus facturas en tiempo real. Todo ello en http://www.confirminet.com</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:171pt;left:352pt"><span style="font-family:Bankinter,serif;font-size:7pt">LOGISMALAGA  S.L.</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:180pt;left:352pt"><span style="font-family:Bankinter,serif;font-size:7pt">CRTA N-344, KM 113</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:190pt;left:352pt"><span style="font-family:Bankinter,serif;font-size:7pt">41564 SEVILLA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:199pt;left:352pt"><span style="font-family:Bankinter,serif;font-size:7pt">SEVILLA                             9435</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:804pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">Para cualquier reclamaci&#xf3;n, ll&#xe1;menos al Servicio de Atenci&#xf3;n al Cliente, 901 135 135</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:813pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:6pt">F08502</span><b><span style="font-family:Bankinter,serif;font-size:6pt;color:#f56600"> R. M. MADRID, T.1.857, F220, H.9.643, N.I.F., A-28-157360</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:271pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Muy Sres. nuestros:</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:292pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">De acuerdo con las instrucciones recibidas, adjunto le enviamos el documento de pago correspondiente a la/s facturas/s</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:302pt;left:55pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">cuyos datos se rese&#xf1;an y al que pertenece la presente liquidaci&#xf3;n, esperando que merezca su conformidad.</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:323pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">  FACTURA / ABONO   FECHA    FECHA       INTERES                  TAE</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:331pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">     REFERENCIA     VCTO.    VALOR   PLZ   (%)     NOMINAL        (%)</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:339pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">  ________________ ________ ________ ___ _______ _____________  _______</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:347pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">  0B991115         21-01-21 20-01-21      0,0000      8.449,43    0,00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:355pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">  0B991115                           INTERESES .:</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:363pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">                                     COMISION ..:</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:371pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">                                     GESTION ...:</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:379pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">                                                 _____________</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:387pt;left:55pt"><span style="font-family:CourierHP,serif;font-size:8pt">                                     EFECTIVO ..:     8.449,43</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:408pt;left:53pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Ordenante</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:408pt;left:257pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Banco beneficiario</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:418pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">BANKINTER S.A.</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:418pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">BANKINTER S.A.</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:426pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">PLAZA DE PEDRO EGUILLOR, 1</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:434pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">48008 SEVILLA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:442pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">       0128-9435         0100009167</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:462pt;left:53pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Beneficiario</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:462pt;left:257pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Por cuenta de</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:462pt;left:517pt"><b><span style="font-family:Bankinter,serif;font-size:8pt;color:#f56600">Importe</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:472pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">LOGISMALAGA  S.L.</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:480pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">CRTA N-344, KM 113</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:496pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">41564 SEVILLA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:504pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">SEVILLA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:472pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">LOGISMALAGA SL</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:480pt;left:257pt"><span style="font-family:Bankinter,serif;font-size:7pt">AV CERVANTES    29500-ALORA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:472pt;left:503pt"><b><span style="font-family:Bankinter,serif;font-size:7pt;color:#f56600">         8.449,43</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:524pt;left:53pt"><b><span style="font-family:Bankinter,serif;font-size:8pt">Total de la orden</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:534pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">OCHO MIL CUATROCIENTAS CUARENTA Y NUEVE CON CUARENTA Y TRES******************</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:542pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:7pt">*****************************************************************************</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:822pt;left:53pt"><span style="font-family:Bankinter,serif;font-size:5pt">B18           01  20210120  03  00001147631</span></p>
        </div>
    """

    parsed_transfer_fields = {}  # type: Dict[str, str]

    try:

        unescaped_text = html.unescape(html_text)
        lines = re.findall(r'(?si)(top):(.*?)pt;(left):(.*?)pt.*?<span.*?>(.*?)</span', unescaped_text)
        '''<class 'list'>: [
        ('top', '74', 'left', '55', 'Fecha'), 
        ('top', '74', 'left', '111', 'Oficina'),
        ('top', '74', 'left', '296', 'Moneda'), 
        ('top', '84', 'left', '55', '20-01-21'),
        ('top', '84', 'left', '111', '1785 - MALAGA AG.5'), 
        ('top', '84', 'left', '296', 'EUR'),
        ('top', '76', 'left', '338', 'Número transferencia'), 
        ('top', '76', 'left', '453', 'Hoja'),
        ('top', '85', 'left', '338', '      210001'), 
        ('top', '85', 'left', '453', '1'),
        ('top', '107', 'left', '55', 'Pago por transferencia'), 
        ('top', '121', 'left', '55', 'Más  beneficios  que  nunca.  Consulte sus facturas, elija  cuándo y cómo y le avisaremos a su móvil o e-mail'),
        ('top', '133', 'left', '55','¡Gratis!. Anticípe el cobro de sus facturas en tiempo real. Todo ello en http://www.confirminet.com'),
        ('top', '171', 'left', '352', 'LOGISMALAGA  S.L.'),
        ('top', '180', 'left', '352', 'CRTA N-344, KM 113'),
        ('top', '190', 'left', '352', '41564 SEVILLA'),
        ('top', '199', 'left', '352', 'SEVILLA                             9435'), 
        ('top', '804', 'left', '53', 'Para cualquier reclamación, llámenos al Servicio de Atención al Cliente, 901 135 135'),
        ('top', '813', 'left', '53', 'F08502'), 
        ('top', '271', 'left', '55', 'Muy Sres. nuestros:'), 
        ('top', '292', 'left', '55', 'De acuerdo con las instrucciones recibidas, adjunto le enviamos el documento de pago correspondiente a la/s facturas/s'),
        ('top', '302', 'left', '55', 'cuyos datos se reseñan y al que pertenece la presente liquidación, esperando que merezca su conformidad.'),
        ('top', '323', 'left', '55', '  FACTURA / ABONO   FECHA    FECHA       INTERES                  TAE'), 
        ('top', '331', 'left', '55',  '     REFERENCIA     VCTO.    VALOR   PLZ   (%)     NOMINAL        (%)'), 
        ('top', '339', 'left', '55',  '  ________________ ________ ________ ___ _______ _____________  _______'), 
        ('top', '347', 'left', '55',  '  0B991115         21-01-21 20-01-21      0,0000      8.449,43    0,00'),
        ('top', '355', 'left', '55', '  0B991115                           INTERESES .:'),
        ('top', '363', 'left', '55', '                                     COMISION ..:'),
        ('top', '371', 'left', '55', '                                     GESTION ...:'),
        ('top', '379', 'left', '55', '                                                 _____________'),
        ('top', '387', 'left', '55', '                                     EFECTIVO ..:     8.449,43'),
        ('top', '408', 'left', '53', 'Ordenante'), ('top', '408', 'left', '257', 'Banco beneficiario'),
        ('top', '418', 'left', '53', 'BANKINTER S.A.'), ('top', '418', 'left', '257', 'BANKINTER S.A.'),
        ('top', '426', 'left', '257', 'PLAZA DE PEDRO EGUILLOR, 1'),
        ('top', '434', 'left', '257', '48008 SEVILLA'),
        ('top', '442', 'left', '257', '       0128-9435         0100009167'),
        ('top', '462', 'left', '53', 'Beneficiario'), 
        ('top', '462', 'left', '257', 'Por cuenta de'),
        ('top', '462', 'left', '517', 'Importe'), 
        ('top', '472', 'left', '53', 'LOGISMALAGA  S.L.'),
        ('top', '480', 'left', '53', 'CRTA N-344, KM 113'),
        ('top', '496', 'left', '53', '41564 SEVILLA'), 
        ('top', '504', 'left', '53', 'SEVILLA'),
        ('top', '472', 'left', '257', 'LOGISMALAGA SL'),
        ('top', '480', 'left', '257', 'AV CERVANTES    29500-ALORA'),
        ('top', '472', 'left', '503', '         8.449,43'),
        ('top', '524', 'left', '53', 'Total de la orden'), 
        ('top', '534', 'left', '53', 'OCHO MIL CUATROCIENTAS CUARENTA Y NUEVE CON CUARENTA Y TRES******************'),
        ('top', '542', 'left', '53', '*****************************************************************************'),
        ('top', '822', 'left', '53', 'B18           01  20210120  03  00001147631')
        ]'''
        por_cuenta_de_header = [x for x in lines if x[4] == 'Por cuenta de'][0]
        por_cuenta_de_header_left = por_cuenta_de_header[3]
        lines_under_por_cuenta_de = [x for x in lines if x[3] == por_cuenta_de_header_left]
        por_cuenta_de_header_index = lines_under_por_cuenta_de.index(por_cuenta_de_header)

        # Customer AVIA requires first line of 'Por cuenta de' value for facturas contrato gip transfers
        if len(lines_under_por_cuenta_de) > por_cuenta_de_header_index:
            por_cuenta_de = lines_under_por_cuenta_de[por_cuenta_de_header_index + 1][4]
            # Way to get desired value from pdf extracted text intsead html
            # lines_around_por_cuenta_de_value = extract.re_first_or_blank(r'(?si)Por cuenta de.*?Importe\n(.*?)\nTotal', pdf_text).split('\n')
            # if len(lines_around_por_cuenta_de_value) > 3:
            #     por_cuenta_de = lines_around_por_cuenta_de_value[len(lines_around_por_cuenta_de_value) - 3]
            parsed_transfer_fields['Por cuenta de'] = por_cuenta_de

    except Exception as _e:
        logger.error(
            'Failed parsing facturas contrato gip transfers fields: {} '
            'HANDLED EXCEPTION: {}'.format(html_text, traceback.format_exc()))
    finally:
        return parsed_transfer_fields


def parse_swift_transfer_fields(
        logger: ScrapeLogger,
        pdf_text: str) -> Dict[str, str]:
    parsed_transfer_fields = {}  # type: Dict[str, str]
    # '''
    # Fecha
    # Oficina
    # Moneda
    # 04-01-21
    # 9011 - SOPORTE NEGOCIO INTERNACIONAL
    # EUR
    # Núm. documento
    # 000283736
    # Abono o adeudo
    # Titulares
    # ESERGUI DISTESER SL
    # Para cualquier información, llámenos a Banca Telefónica, 91 657 88 00
    # F09600  R. M. MADRID, T.1.857, F220, H.9.643, N.I.F., A-28-157360
    # Concepto
    # Importe
    #     ABONO TRANSFERENCIA TARGET
    # 4.000.000,00
    #     REFª: PO:  ESTACIONES DE SERVICIO DE REF:  TRASPASO ESERGUI DISTES
    #     NOMINAL INSTRUIDO EN ORIGEN      4.000.000,00-EUR
    # C.C
    # Fecha valor
    # Total importe
    # 018
    # 04-01-21
    # 4.000.000,00
    # Abonamos  en su cuenta el apunte que se detalla.
    # IBAN
    # ES50 0128 9435 7401 0000 9167
    # A96           01  20210104  01  00003089476'''

    try:
        concept_ref_line = extract.re_first_or_blank(r'(?si)REF.+?: PO:(.*?)REF:(.*?)\n', pdf_text)
        if len(concept_ref_line) == 2:
            ordenante = concept_ref_line[0].strip()
            descripcion = concept_ref_line[1].strip()
            parsed_transfer_fields['REF*: PO:'] = ordenante
            parsed_transfer_fields['REF:'] = descripcion
        else:
            logger.error(
                'Could not parse swift transfer fields: {}'.format(pdf_text)
            )
    except Exception as _e:
        logger.error(
            'Failed parsing swift transfers fields: {} '
            'HANDLED EXCEPTION: {}'.format(pdf_text, traceback.format_exc()))
    finally:
        return parsed_transfer_fields


def parse_traspaso_d_transfer_fields(
        logger: ScrapeLogger,
        text: str) -> Dict[str, str]:
    parsed_transfer_fields = {}  # type: Dict[str, str]
    # '''
    # TRASPASO D.9435100009923 100
    # '''
    try:
        description = text.split()[1][11:]
        parsed_transfer_fields['Descripcion'] = description
        parsed_transfer_fields['Referencia ordenante'] = text.split('.')[1].split()[0]
    except Exception as _e:
        logger.error(
            'Failed parsing traspaso transfers fields: {} '
            'HANDLED EXCEPTION: {}'.format(text, traceback.format_exc()))
    finally:
        return parsed_transfer_fields


def get_transfers_parsed_from_html_resp(
        fin_ent_account_id: str,
        resp_text: str,
        logger: ScrapeLogger) -> List[TransferParsed]:
    transfers_parsed = []  # type: List[TransferParsed]

    table_summary = re.findall('(?si)<table summary.*?(<table summary.*?</table>)\n', resp_text)

    if not table_summary:
        return transfers_parsed

    transfers_forms = re.findall('(?si)<form.*?</form>\n', table_summary[0])

    for form in transfers_forms:
        importe = float(extract.form_param(form, 'importe'))
        fecval = extract.form_param(form, 'fecval')
        orden_orig = extract.form_param(form, 'orden_orig')  # Nombre
        obs = extract.form_param(form, 'obs')  # Observaciones
        iban_ord = extract.form_param(form, 'iban_ord')  # IBAN ordenante
        # One day bank returns a complete IBAN, next day same request gets truncated to 12 first characters
        if len(iban_ord) > 12:
            iban_ord = iban_ord[:12]
        reference_orderer = extract.form_param(form, 'ref_ord')  # Referencia ordenante

        # '''
        # <form method="post" action="empresas+pagos+transferencias_recibidas_euros_det">
        # <input type="hidden" name="pantalla" value="2">
        # <input type="hidden" name="procedencia" value="IBERPAY SEPA">
        # <input type="hidden" name="fecval" value="02032021">
        # <input type="hidden" name="importe" value="363.00">
        # <input type="hidden" name="obs" value="PAGO FACTURA F2102162">
        # <input type="hidden" name="ref_ord" value="NOTPROVIDED">
        # <input type="hidden" name="ref_bene" value="">
        # <input type="hidden" name="comisiones" value="0.00">
        # <input type="hidden" name="correo" value="">
        # <input type="hidden" name="orden_orig" value="TALLERES TOHER S.L.">
        # <input type="hidden" name="iban_ord" value="ES6401825723">
        # <input type="hidden" name="bic_ord" value="BBVAESMMXXX">
        # <input type="hidden" name="direccion" value="">
        # <input type="hidden" name="pais" value="ESPAÑA">
        # <input type="hidden" name="iban_benef" value="ES0701280078970500006375">
        # <input type="hidden" name="bic_benef" value="BKBKESMM">
        # <input type="hidden" name="nombre_ban" value="BANCO BILBAO VIZCAYA ARGENTARIA S.A">
        # <input type="hidden" name="benef_origen" value="NALANDA GLOBAL, S.A.">
        # <input type="hidden" name="cta_ben" value="01280078500006375">
        # <input type="hidden" name="ind_cta_ord" value="I">
        # <input type="hidden" name="clave_empresa" value="0128">
        # <input type="hidden" name="clave_sec" value="0013980">
        # <input type="hidden" name="clave_fecha" value="20210302">
        # <input type="hidden" name="clave_ope" value="">
        # <input type="hidden" name="clave_op1" value="">
        # <input type="hidden" name="inf_ord" value="">
        # <input type="hidden" name="clave_xof" value="">
        # <input type="hidden" name="clave_trf" value="">
        # <input type="hidden" name="nomofiben" value="MADRID AG.48">
        # <input type="hidden" name="iban_bk" value="01280078500006375">
        # <input type="hidden" name="impliqu" value="363.00">
        # <input type="hidden" name="fecha_entrada" value="02032021">
        # <input type="hidden" name="nombanord" value="BANCO BILBAO VIZCAYA ARGENTARIA">
        # <input type="hidden" name="import_tot_gast" value="0.00">
        # <input type="hidden" name="ult_ord" value="">
        # <input type="hidden" name="tip_gast" value="Compartidos">
        # <input type="hidden" name="dia" value="">
        # <input type="hidden" name="mes" value="">
        # <input type="hidden" name="anio" value="">
        # <input type="hidden" name="diaH" value="">
        # <input type="hidden" name="mesH" value="">
        # <input type="hidden" name="anioH" value="">
        # <input type="hidden" name="cuenta_seleccionada" value="01280078500006375">
        # <input type="hidden" name="entidad" value="">
        # <input type="hidden" name="cuenta_beneficiaria_empresa" value="">
        # <button type="submit" class="for_botonenlace_02">202103020013980</button>
        # </form>
        # '''

        operation_date = datetime.strptime(fecval, '%d%m%Y').strftime('%d/%m/%Y')  # 30/01/2017
        value_date = datetime.strptime(fecval, '%d%m%Y').strftime('%d/%m/%Y')  # 30/01/2017

        transfer_parsed = {
            'Nombre': orden_orig,
            'Observaciones': obs,
            'IBAN ordenante': iban_ord,
            'Referencia ordenante': reference_orderer,
            'amount': importe,
            'operation_date': operation_date,
            'value_date': value_date,
        }

        transfers_parsed.append(transfer_parsed)
        logger.info(
            '{}: parsed transf {}@{}'.format(
                fin_ent_account_id,
                transfer_parsed['amount'],
                transfer_parsed['value_date'],
            ))

    # BANKINTER returns maximum of 5 five pages with transfers. With maximum 280 transfers
    # Pages 1,2,3,4 page contain 60 transfers. Page 5 contains 40 transfers.
    if len(transfers_parsed) >= 280:
        logger.info(
            '{}: bank limitation could limit number of returned transfers to 280:  {}'.format(
                fin_ent_account_id,
                transfers_parsed[0]['operation_date']
            ))

    return transfers_parsed


class TestParseHelpersTransfers(unittest.TestCase):
    resp_text = ''

    @classmethod
    def setUpClass(cls) -> None:
        # from  -u 203070 -a 9422
        cls.resp_text = """
        <div id="page0" style="position:relative;width:595pt;height:280pt;background-color:white">
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Fecha</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:85pt"><span style="font-family:Bankinter,serif;font-size:7pt">Oficina</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:269pt"><span style="font-family:Bankinter,serif;font-size:7pt">Moneda</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:85pt"><span style="font-family:Bankinter,serif;font-size:7pt">9435 - C.G. VIZCAYA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:269pt"><span style="font-family:Bankinter,serif;font-size:7pt">EUR</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:39pt;left:311pt"><span style="font-family:Bankinter,serif;font-size:7pt">N&#xfa;mero de Transferencia</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:48pt;left:311pt"><span style="font-family:Bankinter,serif;font-size:7pt">202101020075110</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:61pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:9pt;color:#f56900">Abono por transferencia inmediata</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:245pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Titulares</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:253pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:6pt">ESERGUI DISTESER SL</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:245pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:7pt">Para cualquier informaci&#xf3;n, ll&#xe1;menos a Banca Telef&#xf3;nica, 91 657 88 00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:254pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:6pt">F00805  R. M. MADRID, T.1.857, F220, H.9.643, N.I.F., A-28-157360</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:72pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Ordenante</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:72pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Por cuenta de</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:79pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">ANNA VAQUERO SALA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:97pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Observaciones</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:97pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Beneficiario</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:104pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">factura 0C120480-Anna Vaquero Sala</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:104pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:6pt">AVIA</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:134pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Banco ordenante</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:134pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Referencia beneficiario</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:141pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">CAIXABANK</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:147pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">2100 0716</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:141pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:6pt">CORE</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:159pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Referencia ordenante</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:159pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Liquidaci&#xf3;n transferencia</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Nominal:       </span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:329pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Comisiones:    </span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:404pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Correo:        </span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:166pt;left:478pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Total gastos</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:255pt"><span style="font-family:Bankinter,serif;font-size:7pt">330,00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:329pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:404pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:174pt;left:478pt"><span style="font-family:Bankinter,serif;font-size:7pt">0,00</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:186pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Tipo de gasto:</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Fecha emisi&#xf3;n</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:141pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">Fecha valor</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:194pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt;color:#f56900">Importe abonado</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:141pt"><span style="font-family:Bankinter,serif;font-size:7pt">02-01-21</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:202pt;left:255pt"><b><span style="font-family:Bankinter,serif;font-size:7pt;color:#f56900">330,00</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:214pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:7pt">Abonamos en su cuenta el apunte que se detalla.</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:224pt;left:28pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">N&#xba; IBAN</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:224pt;left:155pt"><b><span style="font-family:Bankinter,serif;font-size:7pt">BIC</span></b></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:234pt;left:28pt"><span style="font-family:Bankinter,serif;font-size:6pt">ES50 0128 9435 7401 0000 9167</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:234pt;left:155pt"><span style="font-family:Bankinter,serif;font-size:6pt">BKBKESMM</span></p>
        <p style="position:absolute;white-space:pre;margin:0;padding:0;top:260pt;left:246pt"><span style="font-family:Bankinter,serif;font-size:5pt">A04           01  20210102  53  00005502598</span></p>
        </div>
        """

    def test_parse_normal_transfer(self):

        transfer_fields = parse_normal_transfer_fields(ScrapeLogger("TEST", 0, 0), self.resp_text)
        self.assertEqual(len(transfer_fields), 5)
        for c in transfer_fields:
            print(c + ': ' + transfer_fields[c])

    def test_parse_normal_transfer_files(self):
        path = os.path.join(os.getcwd(), 'dev\\transfer_files')
        pattern = os.path.join(path, AVIA_NORMAL_TRANSFER_BANK_CODE + '*.html')
        files = glob.glob(pattern)
        for filename in files:
            base_name = os.path.basename(filename)
            print(base_name)
            with open(filename, 'r') as f:  # open in readonly mode
                text = f.read()
                f.close()
                self.resp_text = text
                self.test_parse_normal_transfer()
