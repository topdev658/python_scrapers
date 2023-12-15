import re
from datetime import datetime
from typing import List, Optional

from custom_libs import extract
from custom_libs.date_funcs import convert_date_to_db_format
from project.custom_types import CorrespondenceDocParsed, DocumentTextInfo
from scrapers.bankia_scraper.parse_helpers import _get_date_to_str


def get_correspondence_from_list(data: dict) -> List[CorrespondenceDocParsed]:
    """
    {'identificadorBuzon': '34010000163136',
     'codigoGrupoComunicacion': '2',
     'codigoTipoDocumento': '2390',
     'descripcionLargaComunicacion': 'Transferencia emitida                             ',
     'descripcionCortaComunicacion': '                  ',
     'descripcionAbreviadaComunicacion': '          ',
     'fechaComunicacion': {'valor': '5.02.2019'},
     'codigoProductoUrsus': '10600',
     'identificadorProducto': '41236000045796',
     'indicadorEstadoComunicacion': false,
     'numeroPaginasComunicacion': 1,
     'fechaVisualizacionComunicacion': {'valor': '1.01.1900'},
     'indicadorDisponibilidadDocumento': false,
     'fechaCaducidadComunicacion': {'valor': '2900-01-01-00.00.00.000000'},
     'claveDocumentoComunicacion': '1',
     'nombreProducto': 'Cuenta Corriente',
     'descripcionCategoria': 'Transferencias'}
    """

    documents_raw_data = data['data']['comunicaciones']
    corrs = []  # type: List[CorrespondenceDocParsed]
    for document_raw_data in documents_raw_data:
        # document_parsed = {
        #     'product_id': document_raw_data['identificadorProducto'].strip(),
        #     'product_type': document_raw_data.get('nombreProducto', ''),  # optional
        #     'date': document_raw_data['fechaComunicacion']['valor'],
        #     'description': document_raw_data['descripcionLargaComunicacion'].strip(),
        #     'document_type': document_raw_data['descripcionCategoria'],
        #     'req_args': document_raw_data
        # }
        corr = CorrespondenceDocParsed(
            type=document_raw_data['descripcionCategoria'],
            account_no=document_raw_data['identificadorProducto'].strip(),
            operation_date=datetime.strptime(document_raw_data['fechaComunicacion']['valor'], '%d.%m.%Y'),
            value_date=None,
            amount=None,
            currency=None,
            descr=document_raw_data['descripcionLargaComunicacion'].strip(),
            extra={
                'req_args': document_raw_data,
                'product_type': document_raw_data.get('nombreProducto', '')  # ==account_type, optional
            }
        )

        corrs.append(corr)

    return corrs


def get_document_text_info(document_text: str) -> Optional[DocumentTextInfo]:
    """DocumentTextInfo from PDF for more accurate data"""
    if not document_text:
        return None

    operational_date = ""
    value_date = ""
    amount_str = None  # type: Optional[str]
    description = None  # type: Optional[str]
    if re.search('(?si)^TRANSFERENCIA RECIBIDA', document_text):
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('FECHA VALOR:\n(.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = extract.re_first_or_blank('IMPORTE:\n(.*?)\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        payer = extract.re_first_or_blank('ORDENANTE:\n(.*?)\n', document_text).strip()
        payer = ' '.join(payer.split()[:2])
        description = 'TRANSFERENCIA DE%{}%'.format(payer)

    elif re.search('(?si)^COMISIONES POR SERVICIOS', document_text):
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nal (.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = extract.re_first_or_blank('Cargo: (.*?) EUR\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)  # OJO OJO que hay varios
        description = 'CARGO POR COBRO DE SERVICIOS%'

    elif re.search('(?si)^RECIBO DE AVAL', document_text):
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nVENCIMIENTO\n(.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = extract.re_first_or_blank('\nTOTAL RECIBO\n(.*?)\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)
        description = 'CARGO GASTOS DE PRESTAMO%'

    elif re.search('(?si)^RECIBO DE PRÉSTAMO', document_text):
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nA (.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = extract.re_first_or_blank('\nTOTAL CARGADO:\n(.*?)\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)
        description = None

    elif re.search('(?si)^JUSTIFICANTE DE OPERACIÓN', document_text):
        # FECHA OPERACIÓN: 2019-04-17
        operational_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nFECHA OPERACIÓN: (.*?)\n', document_text).strip()
        )
        # amount = extract.re_first_or_blank('TITULAR: .*?\nTITULAR: .*?\n(.*?)\nCONCEPTO\n', document_text)\
        amount_str = extract.re_first_or_blank('\nTITULAR: .*?\n(.*?)\nCONCEPTO\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)
        description = '%RECIBO IMPUESTOS%'

    elif re.search('(?si)^COMPROBANTE PAGO', document_text):
        # FEC.OPERACION 17.ABR.2019
        operational_date = convert_date_to_db_format(_get_date_to_str(
            extract.re_first_or_blank('\nFEC.OPERACION (.*?)\n', document_text).strip().replace('.', '/')
        ))
        amount_str = extract.re_first_or_blank('IMPORTE:\n(.*?)\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)
        description = '%PAGO%'

    elif re.search('(?si)^TRANSFERENCIA EMITIDA', document_text) or \
            re.search('(?si)^TRANSFERENCIA INMEDIATA EMITIDA', document_text):
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('EMISIÓN:\n(.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = extract.re_first_or_blank('IMPORTE:\n(.*?)\n', document_text) \
            .strip().replace('.', '').replace(',', '.')
        if amount_str:
            amount_str = "-{}".format(amount_str)
        # description = '%ORDEN DE TRASPASO%'
        description = None

    elif re.search('(?si)^ADEUDO/RECIBO', document_text):
        operational_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nFECHA OPERACIÓN:\n(.*?)\n', document_text).strip().replace('.', '/')
        )
        value_date = convert_date_to_db_format(
            extract.re_first_or_blank('\nFECHA VALOR:\n(.*?)\n', document_text).strip().replace('.', '/')
        )
        amount_str = "-{}".format(extract.re_first_or_blank('IMPORTE:\n(.*?)\n', document_text)
                                  .strip().replace('.', '').replace(',', '.'))
        creditor = extract.re_first_or_blank('ACREEDOR:\n(.*?)\n', document_text).strip()
        creditor = ' '.join(creditor.split()[:2])
        if not creditor:
            return None
        description = '%{}%'.format(creditor)

    else:
        return None

    if not amount_str:
        return None

    return DocumentTextInfo(
        OperationalDate=operational_date,
        ValueDate=value_date,
        Amount=float(amount_str),
        StatementDescription=description
    )
