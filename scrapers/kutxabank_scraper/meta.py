import re

LOGIN_ADDITIONAL_QUESTIONS_URL_SIGN = 'NASApp/BesaideNet2/Gestor?PRESTACION=login&FUNCION=login&ACCION=preseleccion'
LOGGED_URL_SIGN = 'NASApp/BesaideNet2/pages/resumen/resumen_posiciones.iface'


class Login:
    class Rex:
        resp_init_idSegmento = re.compile(r'id="idSegmento"\s*value="(.*?)"')
        resp_step1_data_logon_portl = re.compile(r'name="DATA_LOGON_PORTAL"\s*value="(.*?)"')

        refresh_url = re.compile(r'meta\s*http-equiv="refresh".*?url=(.*?)"')


class UserAccountPositionTab:
    class Rex:
        """
        <tr class="iceDatTblRow posicicones_tablaListaContratosRow posiciones_textoTabla3n" 
        id="formPAS:j_id94:0:data1:0"><td class="iceDatTblCol posicicones_tablaListaContratosCol 
        posiciones_columna1Posicion"><span class="iceOutTxt" id="formPAS:j_id94:0:data1:0:numeroCuenta">2095 5205 60 
        3910361950</span></td><td class="iceDatTblCol posicicones_tablaListaContratosCol 
        posiciones_columna2Posicion"><span class="iceOutTxt" id="formPAS:j_id94:0:data1:0:alias">LGI CTA 
        CREDITO</span></td><td class="iceDatTblCol posicicones_tablaListaContratosCol posiciones_columna3Posicion"><a 
        class="iceCmdLnk enlaceAccesoDirecto" href="javascript:;" id="formPAS:j_id94:0:data1:0:j_id100:0:j_id104" 
        onblur="setFocus(&#39;&#39;);" onclick="var form=formOf(this);form[
        &#39;formPAS:_idcl&#39;].value=&#39;formPAS:j_id94:0:data1:0:j_id100:0:j_id104&#39;;return iceSubmit(form,
        this,event);" onfocus="setFocus(this.id);" style="float:left;" title="&Uacute;ltimos movimientos"><span 
        class="iceOutTxt" id="formPAS:j_id94:0:data1:0:j_id100:0:j_id105">Movimientos</span></a>\n<span 
        class="iceOutTxt" id="formPAS:j_id94:0:data1:0:j_id100:1:j_id101" style="float:left;font-size: 
        11px;">&nbsp;-&nbsp;</span>\n<a class="iceCmdLnk enlaceAccesoDirecto" href="javascript:;" 
        id="formPAS:j_id94:0:data1:0:j_id100:1:j_id104" onblur="setFocus(&#39;&#39;);" onclick="var form=formOf(
        this);form[&#39;formPAS:_idcl&#39;].value=&#39;formPAS:j_id94:0:data1:0:j_id100:1:j_id104&#39;;return 
        iceSubmit(form,this,event);" onfocus="setFocus(this.id);" style="float:left;" title="Transferencia"><span 
        class="iceOutTxt" id="formPAS:j_id94:0:data1:0:j_id100:1:j_id105">Transferencia</span></a></td><td 
        class="iceDatTblCol posicicones_tablaListaContratosCol posiciones_columna4Posicion"><span class="iceOutTxt 
        posiciones_saldoNegativo" id="formPAS:j_id94:0:data1:0:disponible">-1.943.650,36 € </span></td></tr>
        """  # noqa
        accounts_form = re.compile('(?si)<form.*?id="formPAS".*?</form>')
        account_row = re.compile('(?si)<tr class="iceDatTblRow.*?</tr>')

        class AccountRow:
            account_number = re.compile('(?si):numeroCuenta">(.*?)</span>')  # '2095 5205 60 3910361950'
            account_balance = re.compile('(?si)disponible">(.*?)</span>')  # '-1.943.650,36 € '
            account_id_from_account_number = re.compile(r'\s(\d+?)$')  # '3910361950'


class Logged:
    class Rex:
        ice_session_id = re.compile(r"container\s*=\s*'(.*?):1")

    class Re:
        acc_option_form_id_pattern = r'for="(.*?)"\s*>\s*{}\s*</label>'
