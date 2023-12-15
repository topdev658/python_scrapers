import html
import json
import re
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed

DSE_DOJO_VERSION = '1.10.0 (e124479)'
DSE_TIMEZONE = "Europe/Madrid"


def extract_page_html_from_json(resp_json: dict) -> str:
    return html.unescape(resp_json['page'])


def get_additional_login_action(resp_text: str) -> str:
    """
    Parses
    <div id="LoginConfig_gBPHiddenOperacion" dojoType="gbp.internet.dijit.GBPHiddenField"
    name="0xdd94adc77daef0ed4c7fe7ec91efd102fd675481d777252e"
    value="/GBP.0746_CI_ARP.BTT_Local.AreaPersonal/ARP0038M.transaction"></div>
    """
    additional_action = extract.re_first_or_blank(
        '(?si)id="LoginConfig_gBPHiddenOperacion".*?value="(.*?)"',
        resp_text
    )
    return additional_action


def get_dynatrace_header(url: str) -> str:
    return extract.re_first_or_blank('/([^/]+)[.]transaction', url)


def get_dse_new_desktop_session_check_param(resp_text: str) -> str:
    dse_new_desktop_session_check_param = extract.re_first_or_blank(
        'dse_new_desktop_session_check=(\d+)',
        resp_text
    )
    return dse_new_desktop_session_check_param


def get_contracts_num(resp_text: str) -> int:
    """
    Expects:
        storeData="[{"nombreEntidad":"BANCO POPULAR ESPA\u00d1OL, S.A.",...,"nomTitContrato":"LACABULAN SL"},
        {"nombreEntidad":"BANCO POPULAR ESPA\u00d1OL, S.A.",..., "nomTitContrato":"LACABULAN SL"}]"
    """
    store_data_str = extract.re_first_or_blank('storeData\=\"(\[{.*?}\])"', resp_text)
    store_data = json.loads(store_data_str)
    return len(store_data)


def _get_basic_form_params(resp_text: str, form_id: str,
                           dse_new_desktop_session_check_param: str) -> dict:
    # contains 'dse_form_cipher'='0x7277396a70727630687530' or similar

    # Old approach with exact form
    # btt_params = json.loads(extract.re_first_or_blank(
    #     '(?si)<form id="{}".*?bttParams="(.*?)" action="Request"'.format(form_id),
    #     html_str
    # ))

    # New approach with less strict conditions due to only several fields are used from btt barams
    # and they are the same for all places of btt params from the page
    # (it looks like btt params are the same at all places of the page)
    btt_params = json.loads(extract.re_first_or_blank(
        '(?si)form[^>]*bttParams="(.*?)" action',
        resp_text
    ))

    table_dataNameForList_param = extract.re_first_or_blank(
        'storeDataName="(.*?)"',
        resp_text
    )

    table_dataName_param = extract.re_first_or_blank(
        'storeDataName.*?\sname="(.*?)"', resp_text
    )

    req_params_select_contract = {
        "_SD": btt_params['_SD'],
        "dse_operationName": None,  # fill it manually
        "dse_dojo_version": DSE_DOJO_VERSION,
        "dse_pageId": btt_params['dse_pageId'],
        "dse_tableSelectedRows": {
            "table_dataName": table_dataName_param,
            "table_dataNameForList": table_dataNameForList_param,
            "rowsIndexes": None,  # fill it manually
            "isSingleSelect": "true",
            "tableId": None,  # fill it manually
        },
        "dse_applicationId": "-1",
        "dse_new_desktop_session_check": dse_new_desktop_session_check_param,
        "dse_sessionId": btt_params['dse_sessionId'],
        "dse_processorState": None,  # fill it manually
        "dse_processorId": btt_params['dse_processorId'],
        "dse_form_submitted": form_id,
        "dse_nextEventName": None,  # fill it manually
        "dse_timezone": DSE_TIMEZONE,
        "dse_triggered_ecaRules": []  # fill it manually if necessary
    }

    return req_params_select_contract


def get_mas_tarde_params(resp_text: str,
                         dse_new_desktop_session_check_param: str) -> dict:
    """

    extract
    '{+"_SD":"1_2_1_OtmjSbjXtXS08YizrYchX5ajha8Ns1GzKGJFHH6PUfN6Zp3e",
    +"dse_applicationId":"-1",
    +"dse_pageId":"3",
    +"dse_processorId":"IWCEFOEJHIBIGGJKAPDWFKBKDGGPJIDGAQJNDEHQ",
    -"dse_webURL":"https:\\/\\/192.168.204.232\\/GBP.0738_CI_CUE.BTT_Local.Cuentas\\/",
    +"dse_processorState":"PANCUE0031CVerde",
    +"dse_sessionId":"cFDwbDVIlbvn7W5AGjdJ13x",
    +"dse_form_submitted":"CUE0031CVerde_gBPForm",
    +"dse_nextEventName":"masTarde",
    +"dse_operationName":"CUE0031C",
    -"dse_form_cipher":"0x376a626e7872316d624143"}'

    convert to

    {+"dse_processorId":"DOHRCJAUFYDRIGGTGGGZGRIFDJEBAMGOBPEWEJBG",
    +"_SD":"1_2_1_6H6HF4fT7w3Cc8g1jgaRJ6jUjJcFs6ZkTbM-tkaBlCTrEqCt",
    +"dse_pageId":"3",
    +"dse_form_submitted":"CUE0031CVerde_gBPForm",
    -+"dse_searchProcessor":"PANCUE0031CVerde",
    +"dse_operationName":"CUE0031C",
    +"dse_new_desktop_session_check":"2508623110104651792",
    +"dse_processorState":"PANCUE0031CVerde",
    +"dse_applicationId":"-1",
    "dse_errorPage":"PAN/CUE0031CVerde.jsp",
    "dse_dojo_version":"1.10.0 (e124479)",
    +"dse_nextEventName":"masTarde",
    -+"dse_submitFormId":"CUE0031CVerde_gBPForm",
    +"dse_sessionId":"Id_5BVw23ry614osPRqxh7a",
    -+"dse_timezone":"Europe/Moscow",
    -+"dse_triggered_ecaRules":["ecaRule"]}"""
    page_text = resp_text
    try:
        page_text = json.loads(resp_text)['page']
    except:
        pass
    btt_params_str = extract.re_first_or_blank('(?si)text="Realizar m\w+s tarde" bttParams="(.*?)"', page_text)
    btt_params = json.loads(btt_params_str)
    btt_params['dse_submitFormId'] = btt_params['dse_form_submitted']
    btt_params['dse_timezone'] = DSE_TIMEZONE
    btt_params['dse_triggered_ecaRules'] = ['ecaRule']
    btt_params['dse_searchProcessor'] = btt_params['dse_processorState']
    btt_params['dse_new_desktop_session_check'] = dse_new_desktop_session_check_param
    btt_params['dse_dojo_version'] = DSE_DOJO_VERSION
    # btt_params['dse_errorPage'] = 'PAN/CUE0031CVerde.jsp' # unnecessary

    # remove unused
    btt_params['dse_form_cipher'] = None
    btt_params['dse_webURL'] = None

    return btt_params


def get_select_contract_req_params(resp_text: str,
                                   dse_new_desktop_session_check_param: str,
                                   contract_num: int) -> dict:
    form_id = 'CUE9000C_SeleccionContrato_gBPForm'
    req_params_select_contract = _get_basic_form_params(resp_text, form_id, dse_new_desktop_session_check_param)

    req_params_select_contract['dse_nextEventName'] = "continuar"
    req_params_select_contract['dse_operationName'] = "CUE9000C"
    req_params_select_contract['dse_tableSelectedRows']['tableId'] = "CUE9000C_SeleccionContrato_gBPTable"
    req_params_select_contract['dse_tableSelectedRows']['rowsIndexes'] = ["{}".format(contract_num)]
    req_params_select_contract['dse_processorState'] = 'PaginaSeleccionContrato'

    return req_params_select_contract


def get_mov_page_req_params(resp_text: str,
                            dse_new_desktop_session_check_param: str,
                            account_idx):
    form_id = 'CUE0007C_Busq_MisCue_formCuerpo'
    req_params_select_account = _get_basic_form_params(resp_text, form_id, dse_new_desktop_session_check_param)

    req_params_select_account['dse_nextEventName'] = "busqMov"
    req_params_select_account['dse_operationName'] = "CUE0007C"
    req_params_select_account['dse_tableSelectedRows']['tableId'] = "CUE0007C_Busq_MisCue_tablaResBusq"
    req_params_select_account['dse_tableSelectedRows']['rowsIndexes'] = ["{}".format(account_idx)]
    req_params_select_account['dse_processorState'] = 'CUE0007C_Busq_MisCue'
    req_params_select_account['dse_triggered_ecaRules'] = [
        "ecaClikLink",
        "ecaPanelMultinea",
        "ecaTMov",
        "ecaEtAyudaPor",
        "ecaSaldoCero",
        "ecaImpDesde",
        "ecaImpHasta",
        "ecaOnLoaded"
    ]

    return req_params_select_account


def get_credit_acc_mov_page_req_params(resp_text: str, dse_new_desktop_session_check_param, account_idx):
    form_id = 'CUE0019C_Busq_CtaCdto_formCuerpo'  # CUE0019C_Busq_CtaCdto_panelPral
    req_params_select_account = _get_basic_form_params(resp_text, form_id, dse_new_desktop_session_check_param)

    req_params_select_account['dse_nextEventName'] = "ok754"
    req_params_select_account['dse_operationName'] = "CUE0019C"
    req_params_select_account['dse_tableSelectedRows']['tableId'] = "CUE0019C_Busq_CtaCdto_tabla754"
    req_params_select_account['dse_tableSelectedRows']['rowsIndexes'] = ["{}".format(account_idx)]
    req_params_select_account['dse_processorState'] = 'CUE0019C_Busq_CtaCdto'
    req_params_select_account["dse_searchProcessor"] = 'CUE0019C_Busq_CtaCdto'
    req_params_select_account["dse_errorPage"] = "CtasDeCdto/CUE0019C_Busq_CtaCdto.jsp"
    req_params_select_account["dse_submitFormId"] = "CUE0019C_Busq_CtaCdto_formCuerpo"
    req_params_select_account['dse_triggered_ecaRules'] = [
        "ecaIniCta", "Comprobar numero de productos", "ecaCargaSubmit", "ecaMostrarCtaCred",
        "ecaPtProxPag", "ecaTextoCta", "ecaTextoPlan", "ecaTextoCtaEspeci", "ecaTextoCtasDep",
        "ecaTextoImp", "ecaTextoFond", "ecaPtFondos", "ecaTextoFondSel", "ecaTextoCarteraVal",
        "ecaTextoAFin", "ecaTextoCFondo", "ecaTextoTar", "ecaTarWi", "ecaTextoTarRep",
        "ecaTextoPres", "ecaTextoCtaCred", "ecaTextoCre", "ecaTextoCar", "ecaTextoFin",
        "ecaTextoSegVida", "ecaTextoSegAho", "ecaTextoSegGral", "ecaTextoTpv",
        "ecaTarjetasEstilo"
    ]

    return req_params_select_account


def get_mov_filter_params(resp_text: str, date_from_str: str, date_to_str: str, dse_new_desktop_session_check_param):
    """
    Note: for testing purposes range between date_from_str to date_to_str can't be
    larger then 4 months (or it will be restricted implicitly)
    """
    form_id = 'CUE0014C_Busq_MisCuentas_RelMov_Formulario'

    # contains 'dse_form_cipher'='0x7277396a70727630687530' or similar
    try:
        btt_params = json.loads(extract.re_first_or_blank(
            '<form id="{}".*?bttParams="(.*?)" action="Request"'.format(form_id),
            resp_text
        ))
    except:
        btt_params = {}  # todo remove on prod

    form_html = extract.re_first_or_blank(
        '(?si)<form.*?id\s*=\s*"{}".*?</form>'.format(form_id),
        resp_text
    )

    fields_tuples_w_values = re.findall(
        '''(?si)<input[^>]*id="([^"]*)"[^>]*name="([^"]*)"[^>]*value="([^"]*)"''',
        form_html
    )

    fields_tuples_wo_values = re.findall(
        '''(?si)<input[^>]*id="([^"]*)"[^>]*name="([^"]*)"''',
        form_html
    )

    hidden_fields_w_values = re.findall(
        'id="([^"]*)"\s*dojoType="gbp.internet.dijit.GBPHiddenField" name="(.*?)" value="(.*?)"',
        form_html
    )

    hidden_fields_wo_values = re.findall(
        'id="([^"]*)"\s*dojoType="gbp.internet.dijit.GBPHiddenField" name="([^"]*)">',
        form_html
    )

    labels_w_text = re.findall(
        '(?i)id="([^"]*)"[^>]*name="([^"]*)"[^>]*text\s*=\s*"([^"]*)"',
        form_html
    )

    labels_w_values = re.findall(
        '(?i)id="([^"]*)"[^>]*name="([^"]*)"[^>]*value\s*=\s*"([^"]*)"',
        form_html
    )

    labels_w_twovalues = re.findall(
        '(?i)id="([^"]*)"[^>]*name="([^"]*)"[^>]*\s(\w+value)\s*=\s*"([^"]*)"[^>]+\s(\w+value)\s*=\s*"([^"]*)"',
        form_html
    )

    all_labels_names_only = re.findall(
        '(?i)<label[^>]*id="([^"]*)"[^>]*name="([^"]*)',
        form_html
    )

    all_params = {}

    for id, name in (hidden_fields_wo_values + fields_tuples_wo_values + all_labels_names_only):
        all_params[id] = {'name': name, 'value': ''}

    for id, name, value in (labels_w_text + labels_w_values + fields_tuples_w_values + hidden_fields_w_values):
        all_params[id] = {'name': name, 'value': value}

    for id, name, value1_title, value1, value2_title, value2 in labels_w_twovalues:
        all_params[id] = {'name': name, value1_title: value1, value2_title: value2}

    req_params_ids = (
        'CUE0014C_Busq_MisCuentas_RelMov_mostrarLeyenda3',
        'CUE0014C_Busq_MisCuentas_RelMov_mostrarLeyenda2',
        'CUE0014C_Busq_MisCuentas_RelMov_listCon',
        'CUE0014C_Busq_MisCuentas_RelMov_tipoSubmit',
        'CUE0014C_Busq_MisCuentas_RelMov_index',
        'CUE0014C_Busq_MisCuentas_RelMov_rbTodos',
        'CUE0014C_Busq_MisCuentas_RelMov__SD',
        'CUE0014C_Busq_MisCuentas_RelMov_indErrorImporte',
        'CUE0014C_Busq_MisCuentas_RelMov_indErrorFechaOp',
        'CUE0014C_Busq_MisCuentas_RelMov_auxImpHasta',
        'CUE0014C_Busq_MisCuentas_RelMov_auxRenderStringPt',
        'CUE0014C_Busq_MisCuentas_RelMov_fOpDesde',
        'CUE0014C_Busq_MisCuentas_RelMov_idioma',
        'CUE0014C_Busq_MisCuentas_RelMov_siAlerta',
        'CUE0014C_Busq_MisCuentas_RelMov_indFDesdeVacia',
        'CUE0014C_Busq_MisCuentas_RelMov_auxFMin',
        'CUE0014C_Busq_MisCuentas_RelMov_dateHoy',
        'CUE0014C_Busq_MisCuentas_RelMov_fOpHasta',
        'CUE0014C_Busq_MisCuentas_RelMov_indFHastaVacia',
        'CUE0014C_Busq_MisCuentas_RelMov_auxImpDesde',
        'CUE0014C_Busq_MisCuentas_RelMov_indBusqAvanzada',
        'CUE0014C_Busq_MisCuentas_RelMov_rbOperacion',
        'CUE0014C_Busq_MisCuentas_RelMov_indFechasOpVacias',
        'CUE0014C_Busq_MisCuentas_RelMov_saldo',
        'CUE0014C_Busq_MisCuentas_RelMov_impHasta',
        'CUE0014C_Busq_MisCuentas_RelMov_impDesde',
        'CUE0014C_Busq_MisCuentas_RelMov_idDocumentum',
        'CUE0014C_Busq_MisCuentas_RelMov_fValHasta',
    )

    req_params = btt_params.copy()
    for param_id in req_params_ids:
        param = all_params.get(param_id) or {'name': '', 'value': ''}
        req_params[param['name']] = param.get('value')

    # set several params manually
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_impHasta']['name']] = {
        'codMon': "", 'amount': ""
    }
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_impDesde']['name']] = {
        'codMon': "", 'amount': ""
    }
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_saldo']['name']] = {
        'codMon': all_params['CUE0014C_Busq_MisCuentas_RelMov_saldo'].get('codMonValue', ""),
        'amount': all_params['CUE0014C_Busq_MisCuentas_RelMov_saldo'].get('amountValue', ""),
    }

    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_rbTodos']['name']] = 'T'
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_rbOperacion']['name']] = None

    # set dates filter
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_fOpDesde']['name']] = date_from_str
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_auxFMin']['name']] = date_from_str
    # not working. current date will be used
    req_params[all_params['CUE0014C_Busq_MisCuentas_RelMov_dateHoy']['name']] = date_to_str

    dse_params = {
        'dse_new_desktop_session_check': dse_new_desktop_session_check_param,
        'dse_triggered_ecaRules': ["ecaClikLink", "ecaPanelMultinea", "ecaTMov",
                                   "ecaEtAyudaPor", "ecaSaldoCero", "ecaImpDesde",
                                   "ecaImpHasta", "ecaFOpDesde", "ecaFOpHasta", "ecaBuscar"],
        'dse_timezone': DSE_TIMEZONE,
        "dse_errorPage": "MisCuentas/CUE0014C_Busq_MisCuentas_RelMov.jsp",
        "dse_submitFormId": "CUE0014C_Busq_MisCuentas_RelMov_Formulario",
        "dse_searchProcessor": "MisCuentasCUE0014C_Busq_MisCuentas_RelMov",
        "dse_dojo_version": DSE_DOJO_VERSION,
    }

    req_params.update(dse_params)
    return req_params


def get_accounts_parsed(resp_text: str, account_type) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    accounts_json_str = extract.re_first_or_blank('storeData="(\[\{.*?\}\])"', resp_text)
    try:
        accounts_raw_dicts = json.loads(accounts_json_str)
    except Exception as exc:
        print('{}: {}'.format(exc, resp_text))
        return []

    for account_raw_dict in accounts_raw_dicts:

        if account_type == ACCOUNT_TYPE_DEBIT:
            # debit account
            account_parsed = {
                'account_no': account_raw_dict['auxNumeroAlias'].replace(' ', ''),
                'balance': convert.to_float(account_raw_dict['auxSaldo']['amount']),
                'currency': account_raw_dict['auxSaldo']['codMon'],
                'account_type': ACCOUNT_TYPE_DEBIT,
                'organization_title': account_raw_dict['nomTitContrato']
            }
        else:
            # credit account
            # check is it credit account or prestamo or leasing
            account_no = account_raw_dict['alias'].replace(' ', '')
            if not account_no:
                continue
            account_parsed = {
                'account_no': account_no,
                'balance': convert.to_float(account_raw_dict['sdoDispuesto']['amount']),
                'currency': account_raw_dict['sdoDispuesto']['codMon'],
                'account_type': ACCOUNT_TYPE_CREDIT,
                'organization_title': account_raw_dict['nomTitContrato']
            }

        accounts_parsed.append(account_parsed)

    return accounts_parsed


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    movements_parsed = []  # type: List[MovementParsed]

    for mov_item in resp_json['items']:

        temp_balance_str = extract.remove_tags(mov_item['estilo'])
        if temp_balance_str == '- - -':
            temp_balance = 0.0
        else:
            temp_balance = convert.to_float(temp_balance_str)

        movement_parsed = {
            'value_date': mov_item['fecvalorEcrmvto221'].replace('-', '/').strip(),
            'operation_date': mov_item['fecmvtoEcrmvto2211'].replace('-', '/').strip(),
            'description': re.sub('\s+', ' ',
                                  (mov_item['conceptoMov'] or mov_item['conceptoMov_label'] or '').strip()),
            'amount': convert.to_float(mov_item['importeMov']['amount']),
            'temp_balance': temp_balance,
        }

        movements_parsed.append(movement_parsed)

    return movements_parsed
