"""Independent module to be able to include
into SantanderOrgWFilialesNuevoLoginReceiptsScraper and
into SantanderOrgWFilialesReceiptsScraper
without changes.
"""
from datetime import datetime
import traceback
from typing import Optional, Union, List, Dict, Tuple

from custom_libs import extract, pdf_funcs
from custom_libs.myrequests import MySession
from project.custom_types import (
    AccountParsed, AccountScraped, MovementParsed, MovementScraped
)
from .custom_types import IbanData

RECEIPT_TYPE_CODES = {
    '02': 'Adeudo varios concepto',
    '120': 'Peticiones de divisa',
    '136': 'Cargo oper. tarjeta',
    '01': 'Abono varios concepto',
    '200': 'Ints.Com.Gtos.Mone',
    '70': 'Adeudo transferencia',
    '69': 'Abono transferencia',
    '81': 'Operaciones varias',
    '82': 'Operaciones varias',
    '37': 'Efts.Descont.S/EXT',
    '29': 'Abono remesa efectos',
    '35': 'Ingreso de cheques',
    '36': 'Pago de cheques',
    '43': 'Ingreso en efectivo',
    '44': 'Pago en efectivo',
    '52': 'Efecto a su cargo',
    '56': 'Devoluciones efectos',
    '58': 'Devoluciones cheques',
    '71': 'Transferencias recibidas',
    '071': 'Transferencias recibidas',
    '72': 'Transferencias emitidas',
    '072': 'Transferencias emitidas',
    '74': 'Cargo documentos varios',
    '99': 'Ingreso desde tarjetas',
    '100': 'Adeudo inter/comis/gastos',
    '135': 'Abono operación tarjeta',
    '173': 'Abono remesas recibos',
    '174': 'Cargo de recibos',
    '175': 'Reembolsos de saldo',
    '176': 'Reembolsos de saldo',
    '119': 'Transferencias recibidas'
}

__version__ = '2.1.0'
__changelog__ = """
2.1.0 2023.07.03
download_temporary_receipt: modified req_url and added required auth_headers
get_receipt_req_params: 
    added mandatory param idMovimiento to receipt_req_params list
    fixed codigo_operacion not in RECEIPT_TYPE_CODES case
2.0.0 2023.04.17
download_movement_receipt: implemented logic to download temporary receipts apart from the final ones
_pdf_parsed_text: delete generation datetime from pdf text to calculate checksum and avoid duplicates on each download
download_temporary_receipt: new method to download receipts temporary with receipt req params
get_receipt_req_params: 
    parse receipt request params from movement and account parsed to get right temporary receipt 
    (the bank generates the PDF text with the data we provide)
added RECEIPT_TYPE_CODES to get 'tipo_operacion'
1.6.0
removed call to basic_save_receipt_pdf_and_update_db 
(only basic_save_receipt_pdf_as_correspondence is needed now) 
1.5.0
check for ok after basic_save_receipt_pdf_as_correspondence
1.4.0
save receipt metadata with checksum
1.3.0
save receipt as correspondence
1.2.0
handle 'no real receipt' cases
1.1.1
upd log msg
1.1.0
download_movement_receipt: use getter to avoid exception for movs from filiales
"""

NO_RECEIPT_MSG = '{"message":null,"code":"INTERNAL_SERVER_ERROR"}'
T = Union['SantanderEmpresasReceiptsScraper', 'SantanderEmpresasNuevoReceiptsScraper']


def build_iban_data(account_no: str, account_parsed: Optional[AccountParsed]) -> IbanData:
    if account_parsed:
        iban_data = IbanData(
            countryIban=account_parsed['iban_data']['countryIban'],
            dcIban=account_parsed['iban_data']['dcIban'],
            entity=account_parsed['iban_data']['entity'],
            office=account_parsed['iban_data']['office'],
            dc=account_parsed['iban_data']['dc'],
            accountNumber=account_parsed['iban_data']['accountNumber']
        )
        return iban_data

    # For ES2500491800112010632768
    iban_data = IbanData(
        countryIban=account_no[:2],  # "ES"
        dcIban=account_no[2:4],  # 25
        entity=account_no[4:8],  # 0049
        office=account_no[8:12],  # 1800
        dc=account_no[12:14],  # 11
        accountNumber=account_no[14:]  # 2010632768
    )
    return iban_data


def _pdf_parsed_text(resp_pdf_content: bytes) -> Tuple[str, bool]:
    """ Delete generation datetime from pdf text to calculate checksum and avoid duplicates on each download
        Example:
            "Fecha y hora de la petición: 13/04/2023 13:51:37 Detalle del movimiento..."
            to
            "Fecha y hora de la petición: Detalle del movimiento..."
    """
    pdf_text = pdf_funcs.get_text(resp_pdf_content)
    pdf_datetime_generation = extract.re_first_or_blank(  # 13/04/2023 13:51:37
        r'\d{2}/\d{2}/\d{4}.*\d{2}:\d{2}:\d{2}',
        pdf_text
    )
    if pdf_datetime_generation:
        pdf_text_wo_generation_date = pdf_text.replace(pdf_datetime_generation, '')
        return pdf_text_wo_generation_date, True

    return pdf_text, False


def download_movement_receipt(
        s: MySession,
        account_scraped: AccountScraped,
        movement_scraped: MovementScraped,
        movement_parsed: MovementParsed,
        meta: dict) -> str:
    scraper = meta['scraper']
    receipt_type = 'temporary' if not movement_parsed['has_final_receipt'] else 'final'

    mov_str = '{} (amount={} bal={})'.format(
        movement_parsed['operation_date'],
        movement_parsed['amount'],
        movement_parsed['temp_balance']
    )

    scraper.logger.info('{}: download {} receipt pdf for: {}'.format(
        account_scraped.FinancialEntityAccountId,
        receipt_type,
        mov_str
    ))

    try:
        if receipt_type == 'temporary':
            resp_pdf = download_temporary_receipt(scraper, s, account_scraped, movement_parsed, mov_str)
        else:
            resp_pdf = download_final_receipt(scraper, s, account_scraped, movement_scraped, movement_parsed, mov_str, meta)

        pdf_parsed_text, deleted_generation_datetime = _pdf_parsed_text(resp_pdf.content)
        if deleted_generation_datetime:
            scraper.logger.info('{}: delete generation datetime from {} receipt text to calculate checksum for: {}'.format(
                account_scraped.FinancialEntityAccountId,
                receipt_type,
                mov_str
            ))

        ok, receipt_parsed_text, checksum = scraper.basic_save_receipt_pdf_as_correspondence(
            account_scraped,
            movement_scraped,
            resp_pdf.content,
            pdf_parsed_text=pdf_parsed_text,
            account_to_fin_ent_fn=scraper._product_to_fin_ent_id,
        )

        return receipt_parsed_text

    except:
        scraper.logger.error("{}: {}: can't download PDF: HANDLED EXCEPTION\n{}".format(
            account_scraped.AccountNo,
            mov_str,
            traceback.format_exc()
        ))
        return ''


def download_final_receipt(
        scraper: T,
        s: MySession,
        account_scraped: AccountScraped,
        movement_scraped: MovementScraped,
        movement_parsed: MovementParsed,
        mov_str: str,
        meta: dict) -> str:

    # Need to get iban_data,
    # but also can build it locally
    account_parsed = meta.get('account_parsed')  # type: Optional[AccountParsed]
    iban_data = build_iban_data(account_scraped.AccountNo, account_parsed)

    num_mov = movement_parsed.get('num_movement') or movement_scraped.OperationalDatePosition
    req_url = ('https://empresas3.gruposantander.es/'
               'paas/api/nwe-cuentas-phoenix/public/'
               'appointments/{}'.format(num_mov))

    req_data = {
        "iban": {
            "ibanCountry": iban_data.countryIban,
            "ibanDc": iban_data.dcIban,
            "entity": iban_data.entity,
            "office": iban_data.office,
            "dc": iban_data.dc,
            "account": iban_data.accountNumber,
        },
        "currency": account_scraped.Currency,
        "date": movement_parsed['operation_date'],  # "2017-12-01"
    }

    # Handle 500 with NO_RECEIPT_MSG
    resp_codes_bad_for_proxies_mem = s.resp_codes_bad_for_proxies
    s.resp_codes_bad_for_proxies = [502, 503, 504, 403, None]  # exclude 500
    resp_pdf = s.post(
        req_url,
        headers=scraper.req_headers,
        json=req_data,
        proxies=scraper.req_proxies,
        stream=True
    )
    if resp_pdf.status_code == 500:
        if resp_pdf.text == NO_RECEIPT_MSG:
            scraper.logger.warning(
                "{}: {}: can't download PDF: no real PDF available for the mov. Skip".format(
                    account_scraped.AccountNo,
                    mov_str,
                )
            )
        else:
            scraper.logger.error("{}: {}: can't download PDF: RESPONSE:\n{}".format(
                account_scraped.AccountNo,
                mov_str,
                resp_pdf.text
            ))
        # It's allowed to return just blank descr, because
        # SantanderScraper doesn't use updated MovementsScraped with receipt_description
        # (updated by basic_download_receipts_common)
        return ''

    s.resp_codes_bad_for_proxies = resp_codes_bad_for_proxies_mem

    return resp_pdf


def download_temporary_receipt(
        scraper: T,
        s: MySession,
        account_scraped: AccountScraped,
        movement_parsed: MovementParsed,
        mov_str: str) -> str:

    # Get receipt request params from movement and account parsed to get right temporary receipt
    # because the bank generates the PDF text with the data we provide
    receipt_req_params = get_receipt_req_params(scraper, account_scraped, movement_parsed)

    req_url = ('https://empresas3.gruposantander.es/'
               'paas/api/v2/nwe-cuentas-api/v1/cuentas/'
               '{}/movimientos?type=detail-pdf'.format(account_scraped.AccountNo))  # 'ES1100495705802116014330'

    resp_pdf = s.post(
        req_url,
        headers=scraper._auth_headers(),
        json=receipt_req_params,
        proxies=scraper.req_proxies,
    )
    if resp_pdf.status_code != 200:
        scraper.logger.error("{}: can't download PDF: {}: RESPONSE:\n{}".format(
            account_scraped.AccountNo,
            mov_str,
            resp_pdf.text
        ))
    return resp_pdf


def get_receipt_req_params(
        scraper: T,
        account_scraped: AccountScraped,
        movement_parsed: MovementParsed) -> List[Dict]:
    """
    Parses
    {
        'codigoOperacion': '71',
        'conceptoCompleto': 'TRANSFERENCIA DE TALLERES TORNEIRO S.A., CONCEPTO GARANTIA DEFINITIVA EXP.: TSA0075137.',
        'docNumber': '0000000000',
        'fecha': '2023-04-11',
        'fechaOperacion': '11-04-2023',
        'fechaValor': '11-04-2023',
        'idMovimiento': '2023-07-04071000000',
        'importe': 8033.72,
        'informacionAdicional': '-',
        'moneda': 'EUR',
        'nombreArchivo': 'TRANSFERENCIA DE TALLERES TORNEIRO S.A., CONCEPTO GARANTIA DEFINITIVA EXP.: TSA0075137.',
        'numeroContrato': 'ES8600495404232616114420',
        'numeroDocumento': '0000000000',
        'oficinaOrigen': '0252',
        'referencia1': '-',
        'referencia2': '-',
        'tipoMovimiento': 'Haber',
        'tipoOperacion': 'Transferencias recibidas',
        'titularContrato': 'EMPRESA DE TRANSFORMACION AGRARIA SA SME MP'
    }
    """

    receipt_req_params = []  # type: List[Dict]
    description_extended = movement_parsed['description_extended']
    try:
        fecha = movement_parsed['operation_date']
        fecha_operacion = datetime.strptime(movement_parsed['operation_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        fecha_valor = datetime.strptime(movement_parsed['value_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        concepto = movement_parsed['description'][:60]
        conceptoaux = movement_parsed['description']
        for i in range(60, len(conceptoaux), 61):
            if movement_parsed['description'][i] == ' ':
                concepto = concepto + conceptoaux[i + 1:i + 61]
            else:
                concepto = concepto + conceptoaux[i:i + 61]

        oficina_origen = extract.re_first_or_blank(
            r'(?si)Oficina de origen:([^|]*)',
            description_extended
        ).strip() or '-'
        numero_documento = extract.re_first_or_blank(
            r'(?si)Nº Documento:([^|]*)',
            description_extended
        ).strip() or '-'
        codigo_operacion = extract.re_first_or_blank(
            r'(?si)Código de operación:([^|]*)',
            description_extended
        ).strip()
        # If codigo_operacion not in RECEIPT_TYPE_CODES, set 'CUENTAS.MOVIMIENTOS.TIPO.C_' + codigo_operacion
        # as bank custom behavior
        tipo_operacion = RECEIPT_TYPE_CODES.get(codigo_operacion, "CUENTAS.MOVIMIENTOS.TIPO.C_" + codigo_operacion)
        tipo_movimiento = extract.re_first_or_blank(
            r'(?si)Tipo de movimiento:([^|]*)',
            description_extended
        ).strip()
        referencia1 = extract.re_first_or_blank(
            r'(?si)Referencia 1:([^|]*)',
            description_extended
        ).strip() or '-'
        referencia2 = extract.re_first_or_blank(
            r'(?si)Referencia 2:([^|]*)',
            description_extended
        ).strip() or '-'
        informacion_adicional = extract.re_first_or_blank(
            r'(?si)Información adicional:([^|]*)',
            description_extended
        ).strip() or '-'
        # Fill param to get len = 5 and manage not num_movement to get '00000' instead of '0None'
        num_movimiento = str(movement_parsed['num_movement']).zfill(5) if movement_parsed['num_movement'] else '00000'
        # Id created with the concatenation of date, operation code and movement number
        id_movimiento = fecha + codigo_operacion.zfill(3) + num_movimiento

        receipt_req_params = {
            'codigoOperacion': codigo_operacion,
            'conceptoCompleto': concepto,
            'docNumber': numero_documento,
            'fecha': fecha,
            'fechaOperacion': fecha_operacion,
            'fechaValor': fecha_valor,
            'idMovimiento': id_movimiento,
            'importe': movement_parsed['amount'],
            'informacionAdicional': informacion_adicional,
            'moneda': account_scraped.Currency,
            'nombreArchivo': concepto,
            'numeroContrato': account_scraped.AccountNo,
            'numeroDocumento': numero_documento,
            'oficinaOrigen': oficina_origen,
            'referencia1': referencia1,
            'referencia2': referencia2,
            'tipoMovimiento': tipo_movimiento,
            'tipoOperacion': tipo_operacion,
            'titularContrato': account_scraped.OrganizationName
        }

    except Exception as e:
        scraper.logger.error("{}: can't parse receipt req params: UNHANDLED EXCEPTION: {} {} {}"
                          .format(e, account_scraped.AccountNo, movement_parsed['operation_date'],
                                  movement_parsed['amount']))
    return receipt_req_params
