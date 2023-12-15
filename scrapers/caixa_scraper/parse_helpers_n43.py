import re
from datetime import datetime
from typing import List, Tuple

from custom_libs import extract
from custom_libs.date_funcs import month_esp_to_num_str_short
from .custom_types import N43FromList

# 'Ext.C43/3 SEPA', 'Ext.Tes.C43/3', 'C43 SEPA+c.ad.'
DOWNLOAD_FILES_CONTAINING = [
    'C43/3',
    'C43 SEPA',
    'C43 concepto ad'
]


def _get_vals_from_str_array(resp_text: str, arr_varname: str) -> List[str]:
    """
    Parses
    var ListaFicherosRecepcion_RefVal5= new Array("TT100421.755","TT120421.423","TT180421.767","TT090421.978","TT170421.719");
    """
    arr_text = extract.re_first_or_blank(r'var {}\s*=\s*new Array\((.*?)\)'.format(arr_varname), resp_text)
    # '"TT100421.755","TT120421.423",...'
    vals = [v.strip('" ') for v in arr_text.split(',')]
    return vals


def get_clave_continuacion_param(resp_text: str) -> str:
    """
    Parses
    case 1:
        f.PN.value="FTR";
        f.PE.value="70";

        f.CLAVE_CONTINUACION.value="n12yZQ7FA9efXbJlDsUD1wAAAXkDTADUG2s4E~ml6V4";
    (case 1 is important!)
    """
    clave_contnuacion_param = extract.re_first_or_blank(
        r'(?si)case 1:[^:]+f.CLAVE_CONTINUACION.value\s*=\s*"(.*?)"',
        resp_text
    )
    return clave_contnuacion_param


def get_n43_form_param_by_name(resp_text: str, param_name: str):
    """Parses
    f.USUARI_SAU.value = "0003751317";"""
    param_val = extract.re_first_or_blank(r'f\d*.{}.value\s*=\s*"(.*?)"'.format(param_name), resp_text)
    return param_val


def get_format_and_estilo_params(resp_text: str) -> Tuple[str, str]:
    """
    Parses
    "JavaScript:setOpcion(3,'RMHC9997302002','RMHC999730200201')"
    where
    // RMHC9997302002 -- FORMAT
    // RMHC999730200201 -- ESTILO
    """
    f_param, e_param = re.findall(r"JavaScript:setOpcion\(3,'([\w\d]+)','([\w\d]+)'\)", resp_text)[0]
    return f_param, e_param


def get_n43s_from_list(resp_text: str) -> Tuple[int, List[N43FromList]]:
    """
    :return: (number_of_files,  n43s_from_list)
    """
    # Get file creation date
    # Parse
    # <tr onMouseOver="TrOver(this, 1)" onMouseOut="TrOver(this, 0)" id="" name="" class="" style="">
    # <th scope="row"  class="ltxt  medida400" >Ext.C43/3 SEPA</th>
    # <td class="ltxt  medida300" ><span>Caixa N43</span></td>
    # <td class="ltxt  medida400" ><span>18/04/2021</span><span> </span><span>17:09:00</span></td>
    files_created_at = []  # type: List[datetime]
    trs = re.findall(
        r'(?si)<tr onMouseOver="TrOver\(this, 1\)".*?</tr>',
        resp_text
    )
    # Can't just count trs, because should skip some of them
    n_files = len(trs)

    for tr in trs:
        # 'No files' marker
        if 'NO TIENES FICHEROS PENDIENTES DE DESCARGA' in tr:
            return 0, []
        tds = re.findall('(?si)<td.*?</td>', tr)
        # <td class="ltxt  medida400" ><span>18 nov 22 01:45</span></td>
        date_str, time_str = re.findall(
            r'<span>(\d{2}\s\w{3}\s\d{2}).*?(\d{2}:\d{2})<\/span>',
            tds[1]
        )[0]
        dt = datetime.strptime('{} {}'.format(get_date_to_str(date_str), time_str), '%d/%m/%y %H:%M')
        files_created_at.append(dt)

    # Parse
    # <script language="javascript" type="text/javascript">
    #     // CLAVE_ITR
    #     var ListaFicherosRecepcion_RefVal1= new Array("L_NvdQ55pt8v8291Dnmm3wAAAXiaKQf_1GIhWW9A5gA","L_NvdQ79BZAv8291Dv0FkAAAAXiaKQf_Z8qcdgAGD24","L_NvdQ4q2H4v8291DirYfgAAAXiaKQf_M2qqYIu1JqE","L_NvdQ5IAoQv8291DkgChAAAAXiaKQf_t73KnQZq2yI","L_NvdQ5A0iov8291DkDSKgAAAXiaKQf_WWnvC7NH2aU");
    #     // NOM_FICH_HP
    #     var ListaFicherosRecepcion_RefVal2= new Array("L_NvdQ2wgWIv8291DbCBYgAAAXiaKQf_opVGY14omXE","L_NvdQ3MsyUv8291DcyzJQAAAXiaKQf_HF643Nq4qH4","L_NvdQ2pdk8v8291Dal2TwAAAXiaKQf_TR5gevKpRkA","L_NvdQ5C0OAv8291DkLQ4AAAAXiaKQf_1lTHnECLqBA","L_NvdQ45G4Iv8291DjkbggAAAXiaKQf_dZheRVSUNXs");
    #     var ListaFicherosRecepcion_RefVal3= new Array("RH","RH","RH","RH","RH");
    #     // CLAU_REC
    #     var ListaFicherosRecepcion_RefVal4= new Array("00001MHC99973","00001MHC99973","00001MHC99973","00001MHC99973","00001MHC99973");
    #     // NOM_FICH_PC
    #     var ListaFicherosRecepcion_RefVal5= new Array("TT100421.755","TT120421.423","TT180421.767","TT090421.978","TT170421.719");
    #     var ListaFicherosRecepcion_RefVal6= new Array("Caixa N43","Caixa N43","Caixa N43","Caixa N43","Caixa N43");
    #     // TIPO_FICHERO
    #     var ListaFicherosRecepcion_RefVal7= new Array("Ext.C43/3 SEPA","Ext.C43/3 SEPA","Ext.C43/3 SEPA","Ext.C43/3 SEPA","Ext.C43/3 SEPA");
    # </script>
    nom_fich_hp_params = _get_vals_from_str_array(resp_text, 'ListaFicherosRecepcion_RefVal2')  # type: List[str]
    clave_itr_params = _get_vals_from_str_array(resp_text, 'ListaFicherosRecepcion_RefVal1')  # type: List[str]
    clau_rec_params = _get_vals_from_str_array(resp_text, 'ListaFicherosRecepcion_RefVal4')  # type: List[str]
    nom_fich_pc_params = _get_vals_from_str_array(resp_text, 'ListaFicherosRecepcion_RefVal5')  # type: List[str]
    tipo_fichero_params = _get_vals_from_str_array(resp_text, 'ListaFicherosRecepcion_RefVal7')  # type: List[str]

    n43s_from_list = []  # type: List[N43FromList]
    for i in range(n_files):
        # Another file format -- skip the file
        if not any(m in trs[i] for m in DOWNLOAD_FILES_CONTAINING):
            continue
        n43_from_list = N43FromList(
            file_created_at=files_created_at[i],
            nom_fich_hp_param=nom_fich_hp_params[i],
            clave_itr_param=clave_itr_params[i],
            clau_rec_param=clau_rec_params[i],
            nom_fich_pc_param=nom_fich_pc_params[i],
            tipo_fichero_param=tipo_fichero_params[i],
        )
        n43s_from_list.append(n43_from_list)
    # number_of_files is required for proper pagination
    # (it can be greater than number of n43s_from_list)
    return n_files, n43s_from_list


def get_date_to_str(text: str) -> str:
    # Converts date string with month_name to date string with month_number
    """
    >>> _get_date_to_str('15/ABR/2019')
    '15/04/2019'
    """
    try:
        # '23', 'julio', '2018'
        # 2 steps for type checker
        dmy = re.findall(r'(\d+).(\w+).(\d+)', text)[0]  # type: Tuple[str, str, str]
        d, m, y = dmy
    except:
        return ''
    m_num = month_esp_to_num_str_short(m)
    if m_num == '':
        return ''
    d = d if len(d) > 1 else '0' + d
    return "{}/{}/{}".format(d, m_num, y)
