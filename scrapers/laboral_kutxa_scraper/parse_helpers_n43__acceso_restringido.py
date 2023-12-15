import re
from typing import List, Dict, Tuple

from custom_libs import extract


def get_access_id(resp_text: str) -> str:
    access_id = extract.re_first_or_blank(
        r'(?s)<frame src="/nuevoacceso/AccesoRestringido\.asp\?Id=([\d]*?)" name="ventana_principal" scrolling="auto" MARGINHEIGHT="0" MARGINWIDTH="0">',
        resp_text
    )
    return access_id

def get_accounts(resp_text: str) -> List[str]:
    accounts_tuples = re.findall(
        r"(?s)<OPTION value='(.*?)'>(.*?)</OPTION>",
        resp_text
    )
    accounts = [tup[0] for tup in accounts_tuples]
    return accounts

def get_filter_form_params(resp_text: str) -> Dict:
    form_params = dict()
    form_params["Id"] = extract.re_first_or_blank(
        r"(?s)<INPUT TYPE='hidden' NAME='Id' value='([\d]*?)' />",
        resp_text
    )
    form_params["Teradata"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="Teradata" VALUE="(.*?)">',
        resp_text
    )
    form_params["tipo"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="tipo" VALUE="(.*?)">',
        resp_text
    )
    form_params["DesdeMenu"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="DesdeMenu" VALUE="(.*?)">',
        resp_text
    )
    form_params["ULTIMOREG"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="ULTIMOREG" VALUE="(.*?)">',
        resp_text
    )
    form_params["FICHERO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="FICHERO" VALUE="(.*?)">',
        resp_text
    )
    form_params["NUMERO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="NUMERO" VALUE="(.*?)">',
        resp_text
    )
    form_params["SENTIDO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="SENTIDO" VALUE="(.*?)">',
        resp_text
    )
    form_params["HISTORICO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="HISTORICO" VALUE="(.*?)">',
        resp_text
    )
    form_params["PRIMERO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="PRIMERO" VALUE="(.*?)">',
        resp_text
    )
    form_params["FECHAPRIMERO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="FECHAPRIMERO" VALUE="(.*?)">',
        resp_text
    )
    form_params["FECHAULTIMO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="FECHAULTIMO" VALUE="(.*?)">',
        resp_text
    )
    form_params["REGISTROS"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="REGISTROS" VALUE="(.*?)">',
        resp_text
    )
    form_params["NUMREG"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="NUMREG" VALUE="(.*?)">',
        resp_text
    )
    form_params["SALDONUEVO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="SALDONUEVO" VALUE="(.*?)">',
        resp_text
    )
    signosaldo = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="SIGNOSALDO" VALUE="(.*?)">',
        resp_text
    )
    if signosaldo == " ":
        form_params["SIGNOSALDO"] = "+"
    else:
        form_params["SIGNOSALDO"] = "-"
    form_params["OPCION"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="OPCION" VALUE="([\d]*?)">',
        resp_text
    )
    form_params["NUMOPE"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="NUMOPE" VALUE="(.*?)">',
        resp_text
    )
    form_params["SALDO"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="SALDO" VALUE="(.*?)">',
        resp_text
    )
    signo = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="SIGNO" VALUE="(.*?)">',
        resp_text
    )
    if signo == " ":
        form_params["SIGNO"] = "+"
    else:
        form_params["SIGNO"] = "-"
    form_params["REGOPER"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="REGOPER" VALUE="(.*?)">',
        resp_text
    )
    form_params["CONTADOR"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="CONTADOR" VALUE="(.*?)">',
        resp_text
    )
    form_params["NORDEN"] = extract.re_first_or_blank(
        r'(?s)<INPUT TYPE="hidden" NAME="NORDEN" VALUE="(.*?)">',
        resp_text
    )
    form_params["NRegOpe"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="NRegOpe" value="(.*?)">',
        resp_text
    )
    form_params["NumRec"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="NumRec" value="(.*?)">',
        resp_text
    )
    form_params["SubNum"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="SubNum" value="(.*?)">',
        resp_text
    )
    form_params["NumDis"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="NumDis" value="(.*?)">',
        resp_text
    )
    form_params["CapAmorPag"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="CapAmorPag" value="(.*?)">',
        resp_text
    )
    form_params["ImpIntPag"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="ImpIntPag" value="(.*?)">',
        resp_text
    )
    form_params["ImpSubPag"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="ImpSubPag" value="(.*?)">',
        resp_text
    )
    form_params["ImpMorPag"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="ImpMorPag" value="(.*?)">',
        resp_text
    )
    form_params["TotalPag"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="TotalPag" value="(.*?)">',
        resp_text
    )
    form_params["CapAmorImp"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="CapAmorImp" value="(.*?)">',
        resp_text
    )
    form_params["ImpIntImp"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="ImpIntImp" value="(.*?)">',
        resp_text
    )
    form_params["ImpMorImp"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="ImpMorImp" value="(.*?)">',
        resp_text
    )
    form_params["TotalImp"] = extract.re_first_or_blank(
        r'(?s)<INPUT type="hidden" name="TotalImp" value="(.*?)">',
        resp_text
    )
    form_params["txtCsb43"] = "0"
    form_params["txtExcel"] = ""
    form_params["fechas"] = "F"
    return form_params


def get_account_number(account_full_number: str) -> str:
    return extract.re_first_or_blank(
        r'(?s)([\d]*?)@',
        account_full_number
    )

def get_complete_account(resp_text:str) -> Tuple:
    entity_code = resp_text[2:6]
    branch_code = resp_text[6:10]
    account_number = resp_text[10:20]
    return entity_code, branch_code, account_number