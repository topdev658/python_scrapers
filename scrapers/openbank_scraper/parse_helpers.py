import re
from typing import List

from project.custom_types import (ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT,
                                  AccountParsed, MovementParsed)


def get_accounts_parsed_from_json(resp_json: dict) -> List[AccountParsed]:
    """Parses
    {'datosSalidaCarteras': None,
    'datosSalidaCodIban': {'datosIban': [{'codIban': {'codbban': '00730100500444385403          ',
                                                   'digitodecontrol': '32',
                                                   'pais': 'ES'}},
                                      ...]},
    'datosSalidaContratosIntervDirec': None,
    'datosSalidaContratosPosGlobal': None,
    'datosSalidaCuentas': {'cuentas': [
    {'aplisub1': '00000707',
     'catalogData': {'estandar': 'BASICO EURO '
                                 'CIC',
                     'producto': 'CUENTA '
                                 'CORRIENTE',
                     'subtipo': 'C.C.OPERATIVA'},
     'cnuevo': {'numerodecontrato': '0733170',
                'producto': '300'},
     ....
                'cvinculada': None},
     'cviejo': {'numerodecontrato': '4385403',  <------ get this to compare with acc iban
                'subgrupo': '044'},
     'descIntervenciones': {'nomFormInterv': None,
                            'nomTipInterv': 'APODERADO                     ',
                            'ordenInterv': None},
     'descripcion': 'ECHEVARRI TURISMOS  ',
     'fechaapertura': None,
     'fecimp': '2018-10-30',
     'filtros': {'bloque': None, 'valido': 'S'},
     'indicadorAcceso': 'O',
     'isRoboAccount': False,
     'limite': {'divisa': '', 'importe': None},
     'nomTipInterv': None,
     'nombretitular': 'ECHEVARRI TURISMOS ' <--- organization title
                      'SA                                                          ',
     'saldoActual': {'divisa': 'EUR',
                     'importe': 919.88},
     'saldoActualEuros': {'divisa': 'EUR',
                          'importe': 919.88},
     'saldoContNatural': {'divisa': '',
                          'importe': None},
     'saldosCuenta': {'contrato': {'numerodecontrato': '0733170',
                                   'producto': '300'},
                      'descLimiteDescubierto': 'NORMAL    ',
                      'descProducto': 'CUENTA '
                                      'CORRIENTE '
                                      'OPEN                   ',
                      'fechaAperturaContrato': '2005-11-08',
                      'importeAutorizado': {'divisa': 'EUR',
                                            'importe': 0.0},
                      'importeDescubierto': {'divisa': 'EUR',
                                             'importe': 0.0},
                      'importeDispuesto': {'divisa': 'EUR',
                                           'importe': 919.88},
                      'importeLimite': {'divisa': 'EUR',
                                        'importe': 0.0},
                      'importePendiente': {'divisa': 'EUR',
                                           'importe': 0.0},
                      'importeRetenido': {'divisa': 'EUR',
                                          'importe': 0.0},
                      'importeSaldo': {'divisa': 'EUR',
                                       'importe': 919.88},
                      'indicadorAVISOA': None,
                      'indicadorINDACCI': None,
                      'retCodigo': '0',
                      'subtipo': {'subtipodeproducto': '800',
                                  'tipodeproducto': {'empresa': '0073',
                                                     'tipodeproducto': '300'}}},
     'tipoCuenta': 'P'},

     ....
    """

    accounts_parsed = []  # type: List[AccountParsed]

    # to get iban by suffix later
    # {'4385403': 'ES3200730100500444385403', ...}
    accounts_suffixes_to_ibans = {
        iban_dict['codIban']['codbban'].strip()[-7:]:
            '{}{}{}'.format(iban_dict['codIban']['pais'],
                            iban_dict['codIban']['digitodecontrol'],
                            iban_dict['codIban']['codbban']).strip()
        for iban_dict
        in resp_json.get('datosSalidaCodIban', {}).get('datosIban', [])
    }

    for acc_dict in resp_json.get('datosSalidaCuentas', {}).get('cuentas', []):
        acc_iban_suffix = acc_dict['cviejo']['numerodecontrato']

        account_iban = accounts_suffixes_to_ibans[acc_iban_suffix]
        currency = acc_dict['saldoActual']['divisa']
        balance = float(acc_dict['saldoActual']['importe'])  # float
        organization_title = re.sub(r'\s+', ' ', acc_dict['nombretitular']).strip()

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_parsed = {
            'organization_title': organization_title,
            'account_no': account_iban,
            'balance': balance,
            'currency': currency,
            'account_type': account_type
        }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed_from_json(resp_json: dict) -> List[MovementParsed]:
    """Parses
     'movimientos': [{'categoriaGanadora': {'category': 'Movimientos excluidos de '
                                                    'la contabilidad',
                                        'online': True,
                                        'relevance': 0.515458603519299,
                                        'subcategory': 'Transferencias entre '
                                                       'cuentas propias'},
                  'categorias': [{'category': 'Movimientos excluidos de la '
                                              'contabilidad',
                                  'online': True,
                                  'relevance': 0.515458603519299,
                                  'subcategory': 'Transferencias entre cuentas '
                                                 'propias'},
                                 {'category': 'Transferencias, gastos '
                                              'bancarios y préstamos',
                                  'online': True,
                                  'relevance': 0.484531087308141,
                                  'subcategory': 'Transferencias'},
                                 {'category': 'Otros gastos',
                                  'online': True,
                                  'relevance': 1.0309172560045377e-05,
                                  'subcategory': 'Otros gastos'}],
                  'conceptoTabla': 'TRANSFERENCIA A FAVOR DE GALDACAUTO SL '
                                   'CONCEPTO TRASPASO A '
                                   'GDK                                      ',
                  'contratoPrincipalOperacion': {'numerodecontrato': 'BGRDTPG',
                                                 'producto': '632'},
                  'diaMvto': 99999,
                  'fechaOperacion': '2018-10-30',
                  'fechaValor': '2018-10-30',
                  'importe': {'divisa': 'EUR', 'importe': -9000},
                  'indFinanciacion': 'N',
                  'nummov': 1,
                  'operacionDGO': {'centro': {'centro': '0100',
                                              'empresa': '0073'},
                                   'codigoterminaldgo': 'IP900',
                                   'numerodgo': 45478},
                  'recibo': False,
                  'saldo': {'divisa': 'EUR', 'importe': 919.88},
                  'subtipoContratoPrincipal': {'subtipodeproducto': '003',
                                               'tipodeproducto': {'empresa': '0073',
                                                                  'tipodeproducto': '632'}}},


    ....
    """

    movements_parsed_desc = []  # type: List[MovementParsed]
    movs_dicts = resp_json.get('movimientos', [])

    for mov_dict in movs_dicts:
        operation_date = mov_dict['fechaOperacion']
        value_date = mov_dict['fechaValor']  # 2018-10-30

        description = re.sub(r'\s+', ' ', mov_dict['conceptoTabla']).strip()
        temp_balance = float(mov_dict['saldo']['importe'])
        amount = float(mov_dict['importe']['importe'])

        movement_parsed = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc
