import re
from typing import List

from custom_libs import extract

__version__ = '1.1.0'
__changelog__ = """
get_acc_nos_for_n43: upd
"""


def get_acc_nos_for_n43(resp_text: str) -> List[str]:
    """Extracts accounts (account numbers).
    Parses dev/10_resp_filter_form
    ['zul.box.Vlayout','iR2Q8',{id:'DATOS_CUENTA',sclass:'rpv',spacing:'5px'},{},[
        ['zul.wgt.Label','iR2Q9',{id:'TITULO_CUENTA',sclass:'second-title',value:'Seleccione la cuenta'},{},[]],
        ['zul.inp.Combobox','iR2Qa',{id:'NCTA_ALIAS',$$onSelect:false,$$0onSelect:true,$onChanging:true,$$0onChanging:true,$$onError:false,$$0onError:true,$$onChange:false,$onChange:true,$$1onChange:true,width:'280px',left:'0px',top:'0px',sclass:'rpv',tabindex:0,_value:'ES92 3058 0098 6110 2180 0058',readonly:true,selectedItemUuid_:'iR2Qb'},{},[
            ['zul.inp.Comboitem','iR2Qb',{label:'ES92 3058 0098 6110 2180 0058',description:'Poliza Grupo Control'},{},[]],
            ['zul.inp.Comboitem','iR2Qc',{label:'ES59 3058 0098 6027 2000 0750',description:'Cuenta Corriente GControl'},{},[]],
            ['zul.inp.Comboitem','iR2Qd',{label:'ES30 3058 0098 6910 2180 5923',description:'POLIZA COVID19'},{},[]]]]]],
    ['zul.box.Vlayout','iR2Qe',{id:'DATOS_FECHA',sclass:'rpv',spacing:'5px'},{},[
    ALSO
    ['zul.inp.Comboitem','cOwIb',{cssflex:false,label:'ES23 3058 0962 1427 2002 4084'},{},[]],
    """

    accs_html = extract.re_first_or_blank(
        "(?si)TITULO_CUENTA.*?'zul.box.Vlayout'",
        resp_text
    )

    # Same as fin_ent_account_id
    # ['ES9230580098611021800058', ...]
    acc_nos = [
        acc_no.replace(' ', '')
        for acc_no in re.findall("'zul.inp.Comboitem'.*?label:'(.*?)'", accs_html)
    ]

    return acc_nos


def get_file_download_button_id(resp_text: str) -> str:
    """Parses dev_n43/20_resp_filtered.html
    ['zul.wgt.Toolbarbutton','hS3Q8',{id:'LINK',$$onCheck:false,
    $onClick:true,left:'0px',top:'0px',tabindex:0,label:'Descargar fichero C43'
    """
    # always on one line in html
    # hS3Q8
    button_id = extract.re_first_or_blank(
        r"'zul.wgt.Toolbarbutton','([^']+)'[^[]+'Descargar fichero C43'",
        resp_text
    )
    return button_id


def get_file_link(resp_text: str) -> str:
    """Parses dev_n43/30_resp_file_link.html
    ["download",["\/BE\/zkau\/view\/z_hrf\/dwnmed-0\/4fs\/Documento.txt"]]
    to '/BE/zkau/view/z_fg7/dwnmed-0/t5k1/Documento.txt'
    """
    file_link = extract.re_first_or_blank(r'\["download",\s*\["(.*?)"]]', resp_text).replace('\\', '')
    return file_link
