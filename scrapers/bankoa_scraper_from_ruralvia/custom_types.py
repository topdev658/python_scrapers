from collections import namedtuple

# ReceiptOption = namedtuple('ReceiptOption', [
#     'descr_part',  # as str
#     'req_params'  # as ReceiptReqParams
# ])
#
SettlementReqParams = namedtuple('SettlementReqParams', [
    'FECHA_LIQ',  # '29-11-2019'
    'TIPO_LIQ',  # 'FACTURACION' # 'CONSTITUCION'
    'SITUACION',  # 'IMPUTADO'
    'IMPORT',  # '1.450,19'
    'PERIODO_LIQ_INI',  # '29-10-2019'
    'PERIODO_LIQ_FIN'  # '29-11-2019'
])

SettlementParsed = namedtuple('SettlementParsed', [
    'fecha_liq',  # '29-11-2019'
    'tipo_liq',  # 'FACTURACION' # 'CONSTITUCION'
    'situacion',  # 'IMPUTADO'
    'importe_str',  # '1.450,19'
    'periodo_liq_ini',  # '29-10-2019'
    'periodo_liq_fin',
    'capital_facturado',    # '1.126,63'    FACTURACION
    'interes_deudor',       # '71,87'       Only on FACTURACION
    'impuestos',            # '251,69'      CONSTITUCION and FACTURACION
    'comision_apertura',    # '250,00'      Only on CONSTITUCION
    'numero_factura',        # 'L2000194'
    'precio_pendiente'
])

# abrirDoc('01380001120195420021', '0138', '03-02-2020 00:00:00.000', '02-02-2020 00:00:00.000',  '-479.91', 'HL','195420021','0000056','','0');return false;" >
PDFReqParams = namedtuple('PDFReqParams', [
    'acuerdo',          #    '01380001120195420021' -> '0195420021'
    'Entidad',          #                    '0138' -> '0138'
    'fechaValor',       # '03-02-2020 00:00:00.000' -> '2020-02-02'
    'fechaOperacion',   # '02-02-2020 00:00:00.000' -> '2020-02-03'
    'importe',          #                 '-479.91' -> '479.91'
    'origenApunte',     #                      'HL' -> 'HL'
    'clavePagina',      #      'BDP_PAS_GENERA_DOC' -> 'BDP_PAS_GENERA_DOC'
    'acuerdoDocumento', #               '195420021' -> '195420021'
    'numeroSecuencialApunteDoc',  #       '0000056' -> '0000056'
    'codigoDocumento',  #                        '' -> ''
    'numSecPDF',        #                       '0' -> '0'
])

PDFParsed = namedtuple('PDFParsed', [
    'fee_number',
    'pending_repayment',
])

# LeasingAccount = namedtuple('LeasingAccount', [
# #     'account_no',  # str
# #     'name',  # str
# # ])
