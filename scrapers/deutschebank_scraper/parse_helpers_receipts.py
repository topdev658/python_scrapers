import re
from datetime import datetime
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed
from .custom_types import OrganizationFromDropdown


def get_organizations(resp_text: str) -> List[OrganizationFromDropdown]:
    """Parses
    notif_oKEY_10_0_0.addAttb("val","3253688GAMBASTAR, S.L")...
    notif_oVAL_10_0_1.addAttb("val","GAMBASTAR, S.L")
    """
    organizations = []  # type: List[OrganizationFromDropdown]

    # ('3253688GAMBASTAR, S.L', 'GAMBASTAR, S.L')
    organizations_raw = re.findall(
        r'(?si)notif_oKEY_10_0_0.addAttb\("val","([^"]+)"\)'
        r'.*?notif_oVAL_10_0_1.addAttb\("val","([^"]+)"\)',
        resp_text
    )

    for o in organizations_raw:
        organizations.append(
            OrganizationFromDropdown(
                title=o[1],
                req_param=o[0],
            )
        )
    return organizations


def _get_corr_val(corr_html: str, data_marker: str) -> str:
    """
    Extracts data from
        notif_oDOCU_13_2_1 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/DOCU");
        notif_oDOCU_13_2_1.addAttb("val", "RECIBO PTMO./LEASING");

    >>> _get_corr_val("/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/DOCU")
    'RECIBO PTMO./LEASING'
    """
    val = extract.re_first_or_blank(
        r'(?si){}.*?addAttb\("val",\s?"(.*?)"'.format(data_marker),
        corr_html
    )
    return val


def get_corespondence_from_list(resp_text: str) -> List[CorrespondenceDocParsed]:
    """
    Parses
        notif_oDOCU_13_2_1 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/DOCU");
        notif_oDOCU_13_2_1.addAttb("val", "RECIBO PTMO./LEASING");
        top.NotifMgr.notify(notif_oDOCU_13_2_1);
        notif_oCTA_13_2_2 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/CTA");
        notif_oCTA_13_2_2.addAttb("val", "0019.0371.01.4010014952");
        top.NotifMgr.notify(notif_oCTA_13_2_2);
        notif_oIMPORTE_13_2_3 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/IMPORTE");
        notif_oIMPORTE_13_2_3.addAttb("val", "612,08");
        top.NotifMgr.notify(notif_oIMPORTE_13_2_3);
        notif_oFECHADOC_13_2_4 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/FECHADOC");
        notif_oFECHADOC_13_2_4.addAttb("val", "29.06.2020");
        top.NotifMgr.notify(notif_oFECHADOC_13_2_4);
        notif_oINFADIC_13_2_5 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/INFADIC");
        notif_oINFADIC_13_2_5.addAttb("val", "00190371050830415266");
        top.NotifMgr.notify(notif_oINFADIC_13_2_5);
        notif_oVISIBLE_13_2_6 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/VISIBLE");
        notif_oVISIBLE_13_2_6.addAttb("val", "V");
        top.NotifMgr.notify(notif_oVISIBLE_13_2_6);
        notif_oPOSICIONES_GRUPO_13_3 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO");
        top.NotifMgr.notify(notif_oPOSICIONES_GRUPO_13_3);
        notif_oSELEC_13_3_0 = new top.DBNotif("DATACHANGED", "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/SELEC");
        notif_oSELEC_13_3_0.addAttb("val", "");
        notif_oSELEC_13_3_0.addAttb("action", "DESCAPDF");
        notif_oSELEC_13_3_0.addAttb("actionArgs", "DOCID=202006262000113454");
    """
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]

    corr_htmls = re.findall(
        r'(?si)/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/SELEC.*?'
        r'/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/VISIBLE',
        resp_text
    )
    for corr_html in corr_htmls:
        try:
            # 'RECIBO PTMO./LEASING'
            corr_type = _get_corr_val(corr_html, "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/DOCU")
            # '0019.0371.01.4010014952'
            fin_ent_account_id_raw = _get_corr_val(corr_html, "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/CTA")
            # '175.000,67' or '612,08' or ''
            amount_str = _get_corr_val(corr_html, "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/IMPORTE")
            amount = convert.to_float(amount_str) if amount_str else None
            # '00190371050830415266', '', 'GAMBASTAR S.L.' - bottom of type
            descr = _get_corr_val(corr_html, "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/INFADIC")
            # '29.06.2020'
            corr_date_raw = _get_corr_val(corr_html, "/DATOS/POSICIONES_LISTA/POSICIONES_GRUPO/FECHADOC")
            # 'DOCID=202006262000113454'
            doc_id = extract.re_first_or_blank('"DOCID=(.*?)"', corr_html)
            corr = CorrespondenceDocParsed(
                type=corr_type,
                account_no=fin_ent_account_id_raw.replace('.', ''),
                operation_date=datetime.strptime(corr_date_raw, '%d.%m.%Y'),
                value_date=None,
                amount=amount,
                currency=None,
                descr=descr,
                extra={
                    'doc_id': doc_id,
                }
            )
            corrs_from_list.append(corr)
        except Exception as e:
            pass

    return corrs_from_list

