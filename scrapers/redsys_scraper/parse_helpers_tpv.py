from datetime import datetime
from typing import List, Optional

from custom_libs import convert
from project.custom_types import MovementTPV
from . import translate


def _none_to_blank_str(val: Optional[str]) -> str:
    return '' if val is None else val


def _blank_str_to_none(val: Optional[str]) -> Optional[str]:
    return None if not val else val


def _get_logout_val(mov: dict) -> Optional[str]:
    """
    CierreSesion

    Reproduces
    <td
        data-ng-if="columnasOperaciones.cierreSesion.fn_is_showeable(columnasOperaciones.cierreSesion) ">
        {{operacion.indicadorLoteAdquirente}}
        <span data-ng-if="operacion.indicadorLoteAdquirente!=null || operacion.indicadorNumeroCajonDescuento!=null">
        /
        </span>
        {{operacion.indicadorNumeroCajonDescuento}}
    </td>
    """
    logout_val = str(_none_to_blank_str(mov['indicadorLoteAdquirente']))  # type: Optional[str]
    if mov['indicadorLoteAdquirente'] is not None or mov['indicadorNumeroCajonDescuento'] is not None:
        logout_val += '/'
    logout_val += str(_none_to_blank_str(mov['indicadorNumeroCajonDescuento']))
    return logout_val if logout_val else None


def _get_payment_type(mov: dict) -> Optional[str]:
    """
    TipoPago

    Reproduces
    <td
        data-ng-if="columnasOperaciones.litMetodoPago.fn_is_showeable(columnasOperaciones.litMetodoPago)">
        {{('operaciones.resultados.tipoPago.'+operacion.litMetodoPago)|translate}}
    </td>
    """
    # "litMetodoPago": null -> ''
    # "litMetodoPago": "T" -> "operaciones.resultados.tipoPago.T": "Tradicional"
    payment_type = translate.es('operaciones.resultados.tipoPago.{}'.format(
        _none_to_blank_str(mov['litMetodoPago'])
    ))
    return payment_type if payment_type else None


def _get_date(mov: dict) -> datetime:
    dt_fmt = '%Y-%m-%d-%H.%M.%S.%f'  # "2021-03-10-09.06.56.45"
    mov_date = datetime.strptime(mov['fechaOperacion'], dt_fmt)
    # DB inserts millis with error:
    # It can't save '2021-03-25 16:19:10.485' and converts it to '2021-03-25 16:19:10.487'
    # So, we'll drop millis to avoid saving incorrect data
    mov_date_no_millis = datetime(
        year=mov_date.year,
        month=mov_date.month,
        day=mov_date.day,
        hour=mov_date.hour,
        minute=mov_date.minute,
        second=mov_date.second
    )
    return mov_date_no_millis


def _get_order_number(mov: dict) -> str:
    """
    NumeroPedido

    <td
            data-ng-if="operacion.numeroPedidoOperacionPasarela4B!=null && columnasOperaciones.numeroPedido.fn_is_showeable(columnasOperaciones.numeroPedido)">{{operacion.numeroPedidoOperacionPasarela4B}}</td>
    <td
            data-ng-if="operacion.numeroPedidoOperacionPasarela4B==null && columnasOperaciones.numeroPedido.fn_is_showeable(columnasOperaciones.numeroPedido)">{{operacion.numeroPedido}}</td>
    """
    order_number = ''
    if mov['numeroPedidoOperacionPasarela4B'] is not None:
        order_number = mov['numeroPedidoOperacionPasarela4B']
    else:
        order_number = mov['numeroPedido']
    return order_number


def _get_net_amount(mov: dict) -> Optional[str]:
    """
    ImporteNeto

    Reproduces
    <td
    data-ng-if="columnasOperaciones.importeNetoTransaccion.fn_is_showeable(columnasOperaciones.importeNetoTransaccion)">
    <span data-ng-if="operacion.idAutorizacion=='S'">
        {{operacion.importeNetoTransaccion}} {{('reglas.monedas.tipoMoneda.978') | translate}}
    </span>
    </td>
    """
    net_amount = None
    if mov['idAutorizacion'] == 'S':
        net_amount = '{} {}'.format(
            _none_to_blank_str(mov['importeNetoTransaccion']),
            translate.es('reglas.monedas.tipoMoneda.978')
        ).strip()
    return net_amount


def _get_op_result_and_code(mov: dict) -> str:
    """
    Resultado operación y código

    Reproduces
    [1]
    <td
        data-ng-if="operacion.idAutorizacion=='S' && columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && operacion.metodoPago!='41' && operacion.metodoPago!='42'  && operacion.metodoPago!='52' && operacion.codigoAccion!='9915'"
        class="text-success">{{('operaciones.autorizacion.' +
    operacion.idAutorizacion) | translate }} <span
            data-ng-if="operacion.metodoPago!='54'">
            {{operacion.numAutorizacion }} </span> <span
            data-ng-if="operacion.metodoPago=='54' && operacion.estadoPaypal!=null && operacion.estadoPaypal!=''">
            ({{operacion.estadoPaypal}}) </span>
    </td>
    [2]
    <td
        data-ng-if="operacion.idAutorizacion=='N' && columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && operacion.litTipoOper!='CONSULTAS.litTipoOperF' && operacion.metodoPago!='41' && operacion.metodoPago!='42'  && operacion.metodoPago!='52' && operacion.codigoAccion!='9915'"
        class="text-danger">
        [2.1]
        <span
            data-ng-if="operacion.metodoPago=='54' && operacion.codigoAccion!='9999' && operacion.codigoAccion!='9998' && operacion.codigoAccion!='8102' && operacion.codigoAccion!='8210' && operacion.codigoAccion!='9936'"
            data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">
            {{('operaciones.autorizacion.'+ operacion.idAutorizacion) | translate }}
            ({{operacion.estadoPaypal}})
            </span>
        [2.2]
        <span
        data-ng-if="operacion.metodoPago!='54' && operacion.codigoAccion!='9929' && operacion.codigoAccion!='9999' && operacion.codigoAccion!='9998' && operacion.codigoAccion!='8102' && operacion.codigoAccion!='8210' && operacion.codigoAccion!='9936'"
        data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">
        {{('operaciones.autorizacion.'
            + operacion.idAutorizacion) | translate }}
            {{operacion.codigoAccion}}</span>
        [2.3]
        <span
        data-ng-if="operacion.metodoPago!='54' && (operacion.codigoAccion=='9999' || operacion.codigoAccion=='9998' || operacion.codigoAccion=='8102' || operacion.codigoAccion=='8210')"
        data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">
        {{('operaciones.autorizacion.sin')
            | translate }} {{operacion.codigoAccion}}</span>
        [2.4]
        <span
            data-ng-if="operacion.metodoPago!='54' && operacion.codigoAccion=='9929'"
            data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">
            {{'operaciones.anulacion' | translate }}
            {{operacion.codigoAccion}}</span>
        [2.5]
        <span
            data-ng-if="operacion.codigoAccion=='9936'"
            data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">
            {{'operaciones.tra.fase1' | translate }}
            {{operacion.codigoAccion}}</span>
    </td>
    [3]
    <td data-ng-if="operacion.idAutorizacion=='N' && columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && operacion.litTipoOper=='CONSULTAS.litTipoOperF' && operacion.metodoPago!='41' && operacion.metodoPago!='42'  && operacion.metodoPago!='52' && operacion.codigoAccion!='9915'">
        <span data-ng-if="operacion.codigoAccion!='9999' && operacion.codigoAccion!='9998' && operacion.codigoAccion!='8102' && operacion.codigoAccion!='8210'"
                data-tooltip="{{'denegada.'+operacion.codigoAccion | translate}}">{{('operaciones.autorizacion.'
            + operacion.idAutorizacion) | translate }}</span>
        <span data-ng-if="operacion.codigoAccion=='9999'  || operacion.codigoAccion=='9998' || operacion.codigoAccion=='8102' || operacion.codigoAccion=='8210'"
        class="text-success">{{('operaciones.autorizacion.sin.paygold')
            | translate }}</span>
    </td>
    [4]
    <td	data-ng-if="columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && (operacion.metodoPago=='41' || operacion.metodoPago=='52') && operacion.codigoAccion!='9915'">
        <span data-ng-if="operacion.litAutDenegOper=='CONSULTAS.pendiente' || operacion.litAutDenegOper=='DOMICILIACIONES.litEstadoDescargada'">
            {{'estado.operacion.'+operacion.litAutDenegOper | translate }} {{operacion.litEstadoOper}}</span>

        <span class="text-danger" data-ng-if="operacion.litAutDenegOper!='CONSULTAS.pendiente' && operacion.litAutDenegOper!='DOMICILIACIONES.litEstadoDescargada'">
            {{('estado.operacion.'+ operacion.litAutDenegOper) | translate }}</span>
    </td>
    [5]
    <td	data-ng-if="columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && operacion.metodoPago=='42' && operacion.codigoAccion!='9915'">
        <span class="text-success" data-ng-if="operacion.litAutDenegOper=='CONSULTAS.autorizada'">{{'estado.operacion.CONSULTAS.autorizada' | translate }} {{operacion.litEstadoOper}}</span>
        <span class="text-danger" data-ng-if="operacion.litAutDenegOper!='CONSULTAS.autorizada'">{{'estado.operacion.'+operacion.litAutDenegOper | translate }}</span>
    </td>

    [6]
    <td	data-ng-if="columnasOperaciones.idAutorizacion.fn_is_showeable(columnasOperaciones.idAutorizacion) && operacion.codigoAccion=='9915'">
        <span class="text-danger">{{'estado.operacion.cancelada' | translate }}</span>
    </td>
    """
    # [1]
    res_and_code = ''
    if mov['idAutorizacion'] == 'S' and mov['metodoPago'] not in [41, 42, 52] and mov['codigoAccion'] != 9915:
        res_and_code = translate.es('operaciones.autorizacion.{}'.format(mov['idAutorizacion']))
        if mov['metodoPago'] != 54:
            res_and_code += ' {}'.format(mov['numAutorizacion'])
        if mov['metodoPago'] == 54 and mov['estadoPaypal']:
            res_and_code += ' {}'.format(mov['estadoPaypal'])
        return res_and_code

    # [2]
    if mov['idAutorizacion'] == 'N' and mov['litTipoOper'] != 'CONSULTAS.litTipoOperF' and mov['metodoPago'] not in [41, 42, 52] and mov['codigoAccion'] != 9915:
        # text-danger
        # [2.1]
        if mov['metodoPago'] == 54 and mov['codigoAccion'] not in [9999, 9998, 8102, 8210, 9936]:
            res_and_code = '{} {}'.format(
                translate.es('operaciones.autorizacion.{}'.format(mov['idAutorizacion'])),
                mov['estadoPaypal']
            )
        # [2.2]
        elif mov['metodoPago'] != 54 and mov['codigoAccion'] not in [9929, 9999, 9998, 8102, 8210, 9936]:
            res_and_code = '{} {}'.format(
                translate.es('operaciones.autorizacion.{}'.format(mov['idAutorizacion'])),
                mov['codigoAccion']
            )
        # [2.3]
        elif mov['metodoPago'] != 54 and mov['codigoAccion'] in [9999, 9998, 8102, 8210]:
            res_and_code = '{} {}'.format(
                translate.es('operaciones.autorizacion.sin'),
                mov['codigoAccion']
            )
        # [2.4]
        elif mov['metodoPago'] != 54 and mov['codigoAccion'] == 9929:
            res_and_code = '{} {}'.format(
                translate.es('operaciones.anulacion'),
                mov['codigoAccion']
            )
        # [2.5]
        elif mov['codigoAccion'] == 9936:
            res_and_code = '{} {}'.format(
                translate.es('operaciones.tra.fase1'),
                mov['codigoAccion']
            )
        return res_and_code

    # [3]
    if mov['idAutorizacion'] == 'N' and mov['litTipoOper'] == 'CONSULTAS.litTipoOperF' and mov['metodoPago'] not in [41, 42, 52] and mov['codigoAccion'] != 9915:
        if mov['codigoAccion'] not in [9999, 9998, 8102, 8210]:
            res_and_code = translate.es('operaciones.autorizacion.{}'.format(mov['idAutorizacion']))
        else:
            res_and_code = translate.es('operaciones.autorizacion.sin.paygold')
        return res_and_code

    # [4]
    if mov['metodoPago'] in [41, 52] and mov['codigoAccion'] != 9915:
        if mov['litAutDenegOper'] in ['CONSULTAS.pendiente', 'DOMICILIACIONES.litEstadoDescargada']:
            res_and_code = '{} {}'.format(
                translate.es('estado.operacion.{}'.format(mov['litAutDenegOper'])),
                mov['litEstadoOper']
            )
        else:
            # text-danger
            res_and_code = translate.es('estado.operacion.{}'.format(mov['litAutDenegOper']))
        return res_and_code

    # [5]
    if mov['metodoPago'] == 42 and mov['codigoAccion'] != 9915:
        if mov['litAutDenegOper'] == 'CONSULTAS.autorizada':
            # text-success
            res_and_code = '{} {}'.format(
                translate.es('estado.operacion.CONSULTAS.autorizada'),
                mov['litEstadoOper']
            )
        else:
            # text-danger
            res_and_code = translate.es('estado.operacion.{}'.format(mov['litAutDenegOper']))
        return res_and_code
    # [6]
    if mov['codigoAccion'] == 9915:
        res_and_code = translate.es('estado.operacion.cancelada')
        return res_and_code
    return ''


def _get_amount_str(mov: dict) -> str:
    """
    Importe (amount+currency)

    [1]
    <td
        data-ng-if="columnasOperaciones.importeSolicitado.fn_is_showeable(columnasOperaciones.importeSolicitado) && operacion.moneda=='978' && operacion.codigoMonedaOperacionDCC==null">{{operacion.importeSolicitado}}
        {{('reglas.monedas.tipoMoneda.'+operacion.moneda) | translate}}</td>
    [2]
    <td
            data-ng-if="columnasOperaciones.importeSolicitado.fn_is_showeable(columnasOperaciones.importeSolicitado) && operacion.moneda!='978' && operacion.codigoMonedaOperacionDCC==null">{{operacion.importeSolicitado}}
        {{('reglas.monedas.tipoMoneda.'+operacion.moneda) | translate}}
        ({{operacion.importeEuros}} {{'reglas.monedas.tipoMoneda.978'|translate}})</td>
    [3]
    <td
            data-ng-if="columnasOperaciones.importeSolicitado.fn_is_showeable(columnasOperaciones.importeSolicitado) && operacion.codigoMonedaOperacionDCC!=null">{{operacion.importeSolicitado}}
        {{('reglas.monedas.tipoMoneda.'+operacion.moneda) | translate}}
        ({{operacion.importeSolicitadoOperacionDCC}}
        {{'reglas.monedas.tipoMoneda.'+operacion.codigoMonedaOperacionDCC |
        translate}})</td>
    """
    # [1]
    if mov['moneda'] == 978 and mov['codigoMonedaOperacionDCC'] is None:
        amount_str = '{} {}'.format(
            convert.float_to_finstr(mov['importeSolicitado']),
            translate.es('reglas.monedas.tipoMoneda.{}'.format(mov['moneda']))
        )
        return amount_str
    # [2]
    if mov['moneda'] != 978 and mov['codigoMonedaOperacionDCC'] is None:
        amount_str = '{} {} ({} {})'.format(
            convert.float_to_finstr(mov['importeSolicitado']),
            translate.es('reglas.monedas.tipoMoneda.{}'.format(mov['moneda'])),
            convert.float_to_finstr(mov['importeEuros']),
            translate.es('reglas.monedas.tipoMoneda.978')
        )
        return amount_str
    # [3]
    if mov['codigoMonedaOperacionDCC'] is not None:
        amount_str = '{} {} ({} {})'.format(
            convert.float_to_finstr(mov['importeSolicitado']),
            translate.es('reglas.monedas.tipoMoneda.{}'.format(mov['moneda'])),
            convert.float_to_finstr(mov['importeSolicitadoOperacionDCC']),
            translate.es('reglas.monedas.tipoMoneda.{}'.format(mov['codigoMonedaOperacionDCC']))
        )
        return amount_str
    return ''


def _get_holder(mov: dict) -> Optional[str]:
    """
    Titular

    Reproduces
    <td
        data-ng-if="columnasOperaciones.nombreTitular.fn_is_showeable(columnasOperaciones.nombreTitular)">{{operacion.nombreTitular}}</td>
    """
    holder = mov['nombreTitular']
    return _blank_str_to_none(holder)


def _get_card_number(mov: dict) -> Optional[str]:
    """
    Tarjeta

    Reproduces

    <td
        data-ng-if="(hasRole('VER_TARJETA_ENMASCARADA') || hasRole('VER_TARJETA_COMPLETA')) && columnasOperaciones.tarjeta.fn_is_showeable(columnasOperaciones.tarjeta)">{{operacion.tarjeta}}
    """
    card_number = mov['tarjeta']
    return _blank_str_to_none(card_number)


def _get_terminal(mov: dict) -> int:
    """
    Terminal

    Reproduces
    <td
       data-ng-if="columnasOperaciones.terminal.fn_is_showeable(columnasOperaciones.terminal)">{{operacion.terminal}}</td>
    """
    terminal = mov['terminal']
    return terminal


def _is_user_0081():
    return True  # todo impl


def _get_operation_type(mov: dict) -> str:
    """
    Tipo operación

    Reproduces
    [1]
    <td
        data-ng-if="columnasOperaciones.litTipoOper.fn_is_showeable(columnasOperaciones.litTipoOper) && !isUser0081() ">{{operacion.litTipoOper
    | translate}}</td>
    [2]
    <td
        data-ng-if="columnasOperaciones.litTipoOper.fn_is_showeable(columnasOperaciones.litTipoOper) && isUser0081() && operacion.litTipoOper=='CONSULTAS.litTipoOperF'">{{'CONSULTAS.litTipoOperFSaba'
    | translate}}</td>
    [3]
    <td
        data-ng-if="columnasOperaciones.litTipoOper.fn_is_showeable(columnasOperaciones.litTipoOper) && isUser0081() && operacion.litTipoOper=='CONSULTAS.litTipoOper38'">{{'CONSULTAS.litTipoOper38Saba'
    | translate}}</td>
    [4]
    <td
        data-ng-if="columnasOperaciones.litTipoOper.fn_is_showeable(columnasOperaciones.litTipoOper) && isUser0081() && (operacion.litTipoOper!='CONSULTAS.litTipoOperF' && operacion.litTipoOper!='CONSULTAS.litTipoOper38')">{{operacion.litTipoOper
    | translate}}</td>
    """
    op_type = ''
    # [1]
    if not _is_user_0081():
        op_type = translate.es(mov["litTipoOper"])
        return op_type
    # [2]
    if _is_user_0081() and mov['litTipoOper'] == 'CONSULTAS.litTipoOperF':
        op_type = translate.es('CONSULTAS.litTipoOperFSaba')
        return op_type
    # [3]
    if _is_user_0081() and mov['litTipoOper'] == 'CONSULTAS.litTipoOper38':
        op_type = translate.es('CONSULTAS.litTipoOper38Saba')
        return op_type
    # [4]
    if _is_user_0081() and mov['litTipoOper'] != 'CONSULTAS.litTipoOperF' and mov['litTipoOper'] != 'CONSULTAS.litTipoOper38':
        op_type = translate.es(mov["litTipoOper"])
        return op_type
    return ''


def get_movements_tpv(resp_json: dict, company_no: str) -> List[MovementTPV]:
    """
    Parses 20_resp_movs.json.
    See buscar-operaciones.html angular template
    used to reproduce logic of the fields.

    {
      "numeroPedido": "210310090655",
      "controlDuplicados": 23960,
      "comercio": 336083456,
      "terminal": 1,
      "fechaOperacion": "2021-03-10-09.06.56.45",
      "estadoOperacion": "F",
      "metodoPago": 14,
      "importeEuros": 60.5,
      "codigoError": null,
      "moneda": 978,
      "referencia": null,
      "tipoTransaccion": 0,
      "fechaSession": "2021-03-10",
      "idAdquirente": 230001,
      "fechaLocalTransaccion": "210310090757",
      "idTransaccion": 145312,
      "idAutorizacion": "S",
      "numAutorizacion": "919533",
      "importeSolicitado": 60.5,
      "importeDevuelto": 0.0,
      "codigoAccion": 0,
      "tarjeta": "476663******8860",
      "fechaCaducidadTarjeta": null,
      "tipoOperacionesAsociadas": "",
      "fechaOperacionOriginal": null,
      "intervaloMinimoCuotas": null,
      "fechaTopeTransaccion": null,
      "importeTotalCoutasAPagar": null,
      "importeTotalCoutasPagadas": null,
      "direcionIpConexion": null,
      "direcionIpCliente": "90.171.41.206",
      "indicadorEmergencia": "E",
      "codigoUsuario": null,
      "usuario": null,
      "particionTabla3DS": null,
      "idMensaje3DS": null,
      "metodoPagoOriginal": null,
      "motivoCambioMetodoPago": null,
      "marcaTarjeta": 1,
      "importeSolicitadoOperacionDCC": null,
      "codigoMonedaOperacionDCC": null,
      "cambioAplicadoOperacionDCC": null,
      "markupOperacionDCC": null,
      "nombreTitular": "B82141383 - BRETONES INSTALACIONES ELECTRICAS SL",
      "idTransferenciaEmisorPreautorizacion": 5410610,
      "tipoEntrada": 2,
      "cuentaCorrienteTitular": null,
      "operacionCreditoDebito": "C",
      "codigoFracionamiento": null,
      "codigoPaisIp": 724,
      "codigoPaisTarjeta": 724,
      "operacionPremiosAsociados": null,
      "saltadoRegla": null,
      "tipoCsbAdquirente": 0,
      "csbAdquirente": 81,
      "descripcionObjetoCompra": null,
      "numeroPedidoOperacionPasarela4B": null,
      "idTransferenciaPayPal": null,
      "indicadorLoteAdquirente": 1,
      "importeNetoTransaccion": null,
      "indicadorNumeroCajonDescuento": null,
      "identificacionDispositivo": "Windows / Firefox-72.0",
      "firmaUserAgent": "2ac09a94caeb8bea34fc472365751da6e889e8c8",
      "identificadorAsociadoControlFraude": null,
      "scoreControlFraude": null,
      "identificadorTransaccionSafetyPay": null,
      "identificadorTablaDatosAdicionales": "0",
      "codigoTipoClaveOperacion": 31,
      "versionModulo": null,
      "idReglaFraude": null,
      "idAccionReglaFraude": null,
      "fechaLiquidacionMasterCard": null,
      "codigoMasterCardFinantial": null,
      "codigoErrorSIS": null,
      "idOperacionPPII": null,
      "codigoPersonalizacion": null,
      "idOperacion": null,
      "cier": null,
      "motivoReferencia": null,
      "idPrimOperPagoReferencia": null,
      "idCliente": null,
      "idPlan": null,
      "version3DSecure": null,
      "particion3DSecure2": null,
      "idMensaje3DS2": "",
      "idPsp": null,
      "metodoAut3DSecure2": null,
      "codigoEci": "07",
      "usaMpiExterno": null,
      "exencionPSD2": "00000",
      "merchantData": null,
      "modalidadDcc": null,
      "notificaciones": null,
      "operacion3dSecure": null,
      "operacion3dSecure2": null,
      "expresionReglaSaltada": null,
      "litTipoOper": "CONSULTAS.litTipoOper0",
      "litMetodoPago": "T",
      "litAutDenegOper": null,
      "litEstadoOper": null,
      "permiteAnulacion": null,
      "permiteConfirmacion": null,
      "permiteDevolucion": true,
      "estadoPaypal": null,
      "resultado": null,
      "fechaReferencia": null,
      "horaReferencia": null,
      "estadoTransferencia": null,
      "email": null,
      "telefono": null,
      "caducidadPaygold": null,
      "enlacePaygold": null,
      "nombreCliente": null,
      "nombrePlan": null,
      "nombrePsp": null,
      "permiteConfirmacionParcial": null
    }
    """
    movements_tpv_asc = []  # type: List[MovementTPV]
    mov_dicts = resp_json['contenido']

    for mov_dict in mov_dicts:

        mov_tpv = MovementTPV(
            NoComercio=company_no,  # CompanyNo
            Fecha=_get_date(mov_dict),  # datetime  # Date
            NumeroTerminal=_get_terminal(mov_dict),  # int  # Nº de terminal
            TipoOperacion=_get_operation_type(mov_dict),  # str  # Tipo operación, OperationType
            NumeroPedido=_get_order_number(mov_dict),  # str  # OrderNumber, Número de pedido
            ResultadoOperacion=_get_op_result_and_code(mov_dict),  # str  # OperationResultAndCode, Resultado operación y código
            Importe=_get_amount_str(mov_dict),  # str  # Amount
            ImporteNeto=_get_net_amount(mov_dict),  # Optional[str], NetAmount -- net amount currency
            CierreSesion=_get_logout_val(mov_dict),  # Optional[str]  # Cierre de sesión, Logout
            TipoPago=_get_payment_type(mov_dict),  # Optional[str]  # Tipo de pago, PaymentType
            NumeroTarjeta=_get_card_number(mov_dict),  # Optional[str]  # Nº Tarjeta, CardNumber
            Titular=_get_holder(mov_dict),  # Optional[str]  # Titular (contiene el CIF), Holder
        )
        movements_tpv_asc.append(mov_tpv)

    return movements_tpv_asc
