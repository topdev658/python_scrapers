import re
from typing import Tuple, Dict

from project.custom_types import TransferParsed


def get_account_select_options(resp_text: str) -> Tuple[bool, Dict[str, str]]:
    try:

        # <option value="0@EUR0182 1299 41 0010225005">0182 1299 41 0010225005   BBVA MUSKIZ&nbsp;</option>
        options = re.findall('(?si)<option.*?"(.*?)@.*?(\d{10})".*?</option>', resp_text)

        # {'0010225005': '0', ..., '0201503804': '2', '0208000593': '1'}
        account_select_options = {v[:10]: k for k, v in options}
    except Exception as _e:
        return False, {}

    return True, account_select_options


def get_transf_parsed_from_mov_extended_description(mov_extended_description: str) -> TransferParsed:
    """Gets a dictionary with movement extended description key, values"""
    # Use loop instead if dict comprehension to pass type checking
    transf_parsed = {}  # type: TransferParsed
    for item in mov_extended_description.split(' || ')[1:]:
        k, v = item.split(": ")
        transf_parsed[k] = v
    return transf_parsed


def get_transfer_parsed(resp_text: str) -> TransferParsed:
    transf_details = re.findall(
        '(?si)<td .*?<strong>(.*?)</strong>.*?txtdato">(.*?)</p.*?td>',
        resp_text
    )
    # {'Concepto': 'TRANSFERENCIAS',
    # 'Canal Origen': 'SOPORTE MAGNETICO',
    # 'Fecha Valor': '2020-12-31',
    # 'Cuenta Beneficiaria': 'ES5401825699620201504494',  # fin_ent_account_id
    # 'Comisión de Cargo': '0,00',
    # 'Importe Nominal': '3231,24',
    # 'Nombre Ordenante': 'FONDO FINANCIACION A COMUNIDADES AUTONOMAS (2020)',
    # 'Comisión Abono no Residente': 'null',
    # 'Nombre del beneficiario': 'ESERGUI DISTESER SL',
    # 'Tipo de transferencia': ' ',
    # 'Referencia Ordenante': '036501702586054',
    # 'Propósito de pago': ' ',
    # 'Dirección': 'PS DEL PRADO                         28014 Madrid Madrid ',
    # 'Localidad': ' ',
    # 'Tipo': 'Recibida',
    # 'Correo Cargo': '0,00',
    # 'Banco y Oficina Ordenante': 'ES1790000001200900000713',
    # 'Observaciones': 'PAGADO POR ICO GOBIERNO DE ESPANA FFCCAA 2020-S4611001A-B95799664-0D991117-00000000000010283453-2587083',
    # 'Importe Líquido': '3231,24',
    # 'Divisa': 'EUR',
    # 'Fecha Operación': '2020-12-31'}
    transf_parsed = {k: v.partition('&')[0] for k, v in transf_details}
    return transf_parsed
