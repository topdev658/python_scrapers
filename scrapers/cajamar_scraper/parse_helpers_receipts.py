import re
from datetime import datetime
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed, DOCUMENT_TYPE_CORRESPONDENCE


def get_accounts_nos_for_correspondence(resp_text: str) -> List[str]:
    """
    Parses
    (from 01_resp_filter_form.html):

    ['zul.inp.Combobox','e1DPg',{id:'NCTA_ALIAS',
    $$onSelect:false,$$0onSelect:true,$onChanging:true,$$0onChanging:true,$$onError:false,$$0onError:true,
    $$onChange:false,$$1onChange:true,width:'280px',left:'370px',top:'320px',sclass:'rpv',
    tabindex:0,_value:'ES25 3058 5601 1727 2000 1859',readonly:true,selectedItemUuid_:'e1DPh'},{},[
        ['zul.inp.Comboitem','e1DPh',{label:'ES25 3058 5601 1727 2000 1859'},{},[]],
        ['zul.inp.Comboitem','e1DPi',{label:'ES94 3058 5601 1727 9900 0036'},{},[]]]],
    ['zul.wgt.Toolbarbutton','e1DPj',{id:'AYUDA_SEDE',visible:false,
    $onClick:true,left:'100px',top:'520px',sclass:'help',tabindex:0,mode:'default'},{},[]]]],
    """

    # ES25 3058 5601 1727 2000 1859 -> NCTA_ALIAS: 560127200001859
    accs_html = extract.re_first_or_blank("""(?si)NCTA_LISTA.*?zul.wgt.Toolbarbutton""", resp_text)
    # ['ES2530585601172720001859', ...]
    accounts_nos = [
        acc_no.replace(' ', '')
        for acc_no in re.findall(r"zul.inp.Comboitem.*?label:'(ES[\d\s]+)'", accs_html)
    ]
    return accounts_nos


def _param_val(html_str: str, param_name: str) -> str:
    """Extracts value by parameter  name from ZKAU response (for correspondence)
    Parses
    {'data-title'{'data-title':'Importe'},align:null,valign:null},{},[
      ['zul.wgt.Label','k55Tj0',{},{},[]]]]:'Documento'},align:null,valign:null},{},
      [['zul.wgt.Label','k55Th0',{value:'INFORMACI\xD3N'}
    {'data-title':'Importe' },align:null,valign:null},{},[['zul.wgt.Label','k55Tj0',{},{},[]]]]
    """
    val_escaped = extract.re_first_or_blank("(?si)'data-title':'{}'[^]]+value:'(.*?)'".format(param_name), html_str)
    # 'INFORMACI\\xD3N' -> 'INFORMACIÓN'
    val_str = val_escaped.encode('utf8').decode('unicode_escape')
    return val_str


def get_correspondence_from_list(resp_text: str, account_no: str) -> List[CorrespondenceDocParsed]:
    """
    ['zul.grid.Row','nW7P70',{id:'TAB_DOCU_row_0',style:'cursor:pointer',zclass:'z-clickEvent-row',_index:0},{},[
            ['zul.wgt.Cell','nW7P80',{id:'TAB_DOCU[0].ZKCELL1',$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Checkbox','nW7P90',{id:'TAB_DOCU[0].ZKCHECKBOX1',$$onCheck:false,$$1onCheck:true,left:'280px',top:'510px',tabindex:0},{},[]]]],
            ['zul.wgt.Cell','nW7Pa0',{$onClick:true,domExtraAttrs:{'data-title':'Fecha'
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pb0',{value:'19-03-2021'},{},[]]]],
            ['zul.wgt.Cell','nW7Pc0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pd0',{value:'N'},{},[]]]],
            ['zul.wgt.Cell','nW7Pe0',{id:'TAB_DOCU[0].ZKCELL2',$onClick:true,domExtraAttrs:{'data-title':'Visto'
                },align:null,valign:null},{},[
                ['zul.wgt.Toolbarbutton','nW7Pf0',{id:'TAB_DOCU[0].ICONOSOBRE',$onClick:true,left:'390px',top:'590px',tabindex:0,image:'/BE/util_apoyo/img/esp/cl.gif',mode:'default'},{},[]]]],
            ['zul.wgt.Cell','nW7Pg0',{$onClick:true,domExtraAttrs:{'data-title':'Documento'
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Ph0',{value:'ESTAFETA TRANSFERENCIA RECIBIDA'},{},[]]]],
            ['zul.wgt.Cell','nW7Pi0',{$onClick:true,domExtraAttrs:{'data-title':'Importe'
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pj0',{value:'21,78'},{},[]]]],
            ['zul.wgt.Cell','nW7Pk0',{$onClick:true,domExtraAttrs:{'data-title':'Titular/ Librador/ Emisor'
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pl0',{value:'GRUPO CONTROL EMPRESA SEGURIDAD S.A.U.'},{},[]]]],
            ['zul.wgt.Cell','nW7Pm0',{id:'TAB_DOCU[0].ZKCELL3',$onClick:true,domExtraAttrs:{'data-title':'Descargar'
                },align:null,valign:null},{},[
                ['zul.wgt.Toolbarbutton','nW7Pn0',{id:'TAB_DOCU[0].ICONOPDF',$onClick:true,left:'0px',top:'0px',tabindex:0,image:'/BE/util_apoyo/img/esp/pdf.gif',mode:'default'},{},[]]]],
            ['zul.wgt.Cell','nW7Po0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pp0',{value:'S'},{},[]]]],
            ['zul.wgt.Cell','nW7Pq0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pr0',{},{},[]]]],
            ['zul.wgt.Cell','nW7Ps0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pt0',{},{},[]]]],
            ['zul.wgt.Cell','nW7Pu0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pv0',{value:'000009810210800058'},{},[]]]],
            ['zul.wgt.Cell','nW7Pw0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Px0',{value:'3058'},{},[]]]],
            ['zul.wgt.Cell','nW7Py0',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pz0',{},{},[]]]],
            ['zul.wgt.Cell','nW7P_1',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7P01',{value:'972278273'},{},[]]]],
            ['zul.wgt.Cell','nW7P11',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7P21',{},{},[]]]],
            ['zul.wgt.Cell','nW7P31',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7P41',{},{},[]]]],
            ['zul.wgt.Cell','nW7P51',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7P61',{},{},[]]]],
            ['zul.wgt.Cell','nW7P71',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7P81',{},{},[]]]],
            ['zul.wgt.Cell','nW7P91',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pa1',{},{},[]]]],
            ['zul.wgt.Cell','nW7Pb1',{id:'TAB_DOCU[0].ZKCELL4',$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pc1',{id:'TAB_DOCU[0].LABELDOMINIO',left:'380px',top:'590px'},{},[]]]],
            ['zul.wgt.Cell','nW7Pd1',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pe1',{value:'972278273'},{},[]]]],
            ['zul.wgt.Cell','nW7Pf1',{$onClick:true,domExtraAttrs:{'data-title':''
                },align:null,valign:null},{},[
                ['zul.wgt.Label','nW7Pg1',{value:'CORE'},{},[]]]]]],
    """
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]

    rows = re.findall(r"(?si)'zul.grid.Row'.*?\[]]]]]]", resp_text)
    for ix, row in enumerate(rows):
        corr_type = _param_val(row, 'Documento')
        corr_owner = _param_val(row, 'Titular/ Librador/ Emisor')
        # '19-03-2021'
        corr_date_str = _param_val(row, 'Fecha')
        corr_date = datetime.strptime(corr_date_str, '%d-%m-%Y')
        # '21,78'

        amount_str = _param_val(row, 'Importe')
        amount = convert.to_float(amount_str) if amount_str else None

        corr = CorrespondenceDocParsed(
            type=DOCUMENT_TYPE_CORRESPONDENCE,
            account_no=account_no,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=None,
            descr='{} {}'.format(corr_type, corr_owner),
            extra={
                'corr_ix': ix
            }
        )
        corrs_from_list.append(corr)
    return corrs_from_list
