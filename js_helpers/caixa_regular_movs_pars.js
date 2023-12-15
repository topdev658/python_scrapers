
var SCRIPTLET_SESION  = "/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436";
var LIT_NO_DISPONIBLE = "En estos momentos no está disponible.";
var idFila = "";
function init() {

if (isDefined(top.Inferior.Menu.gestionaMenu)) {


var listaMenu = top.Inferior.Menu.document.getElementById('lista0');
if (listaMenu!=null) {

if (listaMenu.style.display != 'block') {
top.Inferior.Menu.gestionaMenu('menu0');
}
}

top.Inferior.Menu.gestionaMenu('menu0_0');

}
var capa_pta = document.getElementById("PTS0");
var capa_eur = document.getElementById("EUR0");
capa_eur.style.textAlign = 'right';
capa_pta.style.textAlign = 'right';
definirMoneda();

var miniBanner = document.getElementById("miniBanner");
var miniBannerOculto = document.getElementById("miniBannerOculto");
if (miniBanner!=null && miniBannerOculto!=null) {
if (miniBannerOculto.innerHTML != "") {
var content = $('#miniBannerOculto').html();
$('#miniBanner').html(content);
}
}
}
function definirMoneda() {
var f=document.forms[0];
var numFilas = f.NumFilasTabla.value;
switch (parseInt(f.FLAG_MONEDA.value)) {

case 0:
capa('EUR','PTS',numFilas);
break;

case 1:
capa('PTS','EUR',numFilas);
break;

default:
capa('PTS','EUR',numFilas);
break;
}
}
// NOTE: open movements page
function enviar(indice, codMoneda){
var f = document.forms[0];
var capa_pta = document.getElementById("PTS0");
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}
f.REFVAL_SIMPLE_NUMERO_CUENTA.value = TablaBean01_RefVal1[indice];
f.ORIGEN_INVOCACION.value = f.PN.value + f.PE.value;
f.CLICK_ORIG.value = "EOC_" + f.PN.value + "_" + f.PE.value;
f.ALIAS_CUENTA.value = TablaBean01_RefVal2[indice];
f.FLAG_KEEP_THE_CHANGE.value = TablaBean01_RefVal3[indice];
f.MONEDA.value = codMoneda;
f.PN.value="GCT";
f.PE.value="16";
f.target = "Cos";
f.submit();
}

function enviarMovimientos(indice, codMoneda){
var f = document.forms[0];
var capa_pta = document.getElementById("PTS0");
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}
// TablaBean01_RefVal1 contains list with accounts ids for movements
// LOADED IN
// <script id="TablaBean01EvalScript" language="javascript" type="text/javascript">var TablaBean01_RefVal1= new Array("D0mbUI40GhMPSZtQjjQaEwAAAWekGROpmtEZy9EORAY","D0mbUI7f35EPSZtQjt_fkQAAAWekGROp_dqCsnDd9VE","D0mbUI43HWgPSZtQjjcdaAAAAWekGROpYwwXVdAffVg","","");
// var TablaBean01_RefVal2= new Array("","","","","");
// var TablaBean01_RefVal3= new Array("N","N","N","","");
// </script>
// IN FRAME "Inferior"
f.REFVAL_SIMPLE_NUMERO_CUENTA.value = TablaBean01_RefVal1[indice];
f.ORIGEN_INVOCACION.value = f.PN.value + f.PE.value;
f.CLICK_ORIG.value = "EOC_" + f.PN.value + "_" + f.PE.value;
f.ALIAS_CUENTA.value = TablaBean01_RefVal2[indice];
f.FLAG_KEEP_THE_CHANGE.value = TablaBean01_RefVal3[indice];
f.MONEDA.value = codMoneda;
f.PN.value="GCT";
f.PE.value="200";
f.target = "Cos";
f.submit();
}
function linkpeu(){
document.forms[0].target = "Cos";
if (top.flagPE=='P') {
top.frames['Inferior'].frames['Menu'].prelanzar('POS','10',7,6,null,null,null);
} else {
top.frames['Inferior'].frames['Menu'].prelanzar('POS','10',3,3,null,null,null);
}
}



function lenkpeu(num){
f=document.forms[0];
f.target = "Cos";
if (num==1) {
top.clickorig = "PPA_" + f.PN.value + "_" + f.PE.value;
top.frames['Inferior'].frames['Menu'].prelanzar('POS','0',0,0,0,null,null);
}
if (num==4) {
top.frames['Inferior'].frames['Menu'].lanzarB('POG','1',"","PPA_" + f.PN.value + "_" + f.PE.value);
}
}
function imprimir() {
if (window.print) {
window.print()
}
else {
InicializaErrores()
AddError("Su navegador no soporta esta opción. Para imprimir seleccione la opción de menú Archivo-Imprimir...");
ProcesaErrores("Mis cuentas")
}
}
function linkCCT() {
f=document.forms[0];
f.PN.value="CCT";
f.PE.value="1";
f.TORNA_PN_CCT.value="GCT";
f.TORNA_PE_CCT.value="11";
f.CLICK_ORIG.value = "EOC_"+ f.PN.value+"_" + f.PE.value;
f.PN.value="CCT";
f.PE.value="1";
f.target = "Cos";
f.submit();
}

function exportar() {
var f=document.forms[0];
f.target = "Oculto";
f.PN.value = "GCT";
f.PE.value = "107";
f.CLICK_ORIG.value = "FLX_"+ f.PN.value+"_" + f.PE.value;
f.submit();
f.PN.value = "GCT";
f.PE.value = "11";
}



function linkFOI() {
f=document.forms[0];
f.PN.value="FOI";
f.PE.value="20";
f.TORNA_PN_CCT.value="GCT";
f.TORNA_PE_CCT.value="11";
f.CLICK_ORIG.value = "EOC_"+ f.PN.value+"_" + f.PE.value;
f.target = "Cos";
f.submit();
}


var descProducte = "Pagos - Cuaderno 34 / 34.1";
var clauPro = "00001PAG00001";
function enlaces(PNDestino,PEDestino, url, EntornoMenu,PNMenu,PEMenu,clickOrig){

var url_aux = url;
var idx1=-1;
var idx2=0;
var seguir = true;
var error = false;
var aux1= "";
var aux1Var;
var myeval = "";
while (seguir) {
idx1 = url.indexOf("{", idx1+1);

if (idx1==-1) {
seguir = false;
} else {
idx2=url.indexOf("}", idx1);
if (idx2==-1) {
seguir = false;
error = true;
} else {
aux1 = url.substring(idx1 + 1, idx2);
eval ('aux1Var='+aux1);
url_aux = url_aux.replace("{"+aux1+"}", aux1Var);
}
}
}
if (!error) {
url = url_aux;
}

clickorig = clickOrig + "_" + document.forms[0].PN.value + "_" +document.forms[0].PE.value
top.Inferior.Menu.lanzarLO(EntornoMenu,PNDestino,PEDestino,url,clickorig,PNMenu,PEMenu);
}
function correspondenciaBKB() {
var f =document.forms[0];
var capa_pta = document.getElementById("PTS0");
f.PN.value = "GCT";
f.PE.value = "130";
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}
f.CLICK_ORIG.value = "EOC_"+ f.PN.value+"_" + f.PE.value;
f.target = "Cos";
f.submit();
}
function irMisFinanzas() {
var f =document.forms[0];
f.PN.value = "GFM";
f.PE.value = "405";
f.CLICK_ORIG.value = "EOC_"+ f.PN.value+"_" + f.PE.value;
f.target = "Cos";
f.submit();
}
function irMisFinanzas2(pn, pe, parametros) {
var formName = "goPNPE";
removeAllFormField(formName);
addFormField(formName, "PN", pn);
addFormField(formName, "PE", pe);
addFormField(formName, "CLICK_ORIG", "EOC_"+ document.forms[0].PN.value+"_" + document.forms[0].PE.value);
if (parametros!=null && parametros!="") {
var param = parametros.split("=");
addFormField(formName, param[0], param[1]);
}
with (document.forms[formName]) {
target="Cos";
submit();
}
}


function visualizarMovimientos(urlParams, id_origen, id_destino) {
idFila = id_origen;

var div = $('#'+idFila+'Oculta').find('div#' + idFila + 'DivAjax');
var contenido_div = div.html();
var atr_display_tr = $('#'+idFila+'Oculta').css('display');
var error_extracto_reducido = $('#'+idFila+'Oculta').find("div#errorExtractoReducido");
var divTraspasoRapido = $('#'+idFila+'Oculta').find("div#divTraspasoRapido");

if (error_extracto_reducido.length && error_extracto_reducido.html().trim()!="") {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);
}


bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, traspasoRapidoOK], traspasoRapidoNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);

} else {


if (divTraspasoRapido.length!=0) {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);
}


bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, traspasoRapidoOK], traspasoRapidoNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);

} else {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);

} else {


if (contenido_div.trim()!="") {

abrirFilaTraspasoRapido(id_origen);

} else {

bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, visualizarMovimientosOK], visualizarMovimientosNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);
}
}
}
}
}
function visualizarMovimientosOK(data, textStatus, jqXHR, params, objOrigen, objDestino, objDestinoEvalScript) {

var divOculto = document.getElementById("divOculto");
divOculto.innerHTML = data;
if (document.getElementById('jsCampanya')==null) {
ejecutaScript(data,"javaScriptStrCTX");
} else {
while (document.getElementById('jsCampanya')!=null) {
$("#jsCampanya").remove();
}
ejecutaScript(data,"javaScriptStrCTX");
}

var divOculto = document.getElementById("divOculto");
divOculto.innerHTML = data;
var elementos = document.getElementsByClassName("contenedor-globus");
for(i=0; i<elementos.length;i++){

elementos[i].parentNode.style.top="-60px";
elementos[i].parentNode.style.padding="0px";
}

divOculto.innerHTML = "";
desbloquearCursor();
}
function visualizarMovimientosNOK() {
ControlError (null, null, null, null);
}


function traspasoRapido(urlParams, id_origen, id_destino){
idFila = id_origen;

var div = $('#'+idFila+'Oculta').find('div#' + idFila + 'DivAjax');
var atr_display_tr = $('#'+idFila+'Oculta').css('display');
var error_extracto_reducido = $('#'+idFila+'Oculta').find("div#errorExtractoReducido");
var divTablaBeanExtractoReducido = $('#'+idFila+'Oculta').find("#tablaBeanExtractoReducido");

borrarContenidoFilasOcultas();

if (error_extracto_reducido.length && error_extracto_reducido.html().trim()!="") {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);
}


bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, traspasoRapidoOK], traspasoRapidoNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);

} else {


if (divTablaBeanExtractoReducido.length!=0) {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);
}


bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, traspasoRapidoOK], traspasoRapidoNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);

} else {


if (atr_display_tr=="table-row") {

abrirFilaTraspasoRapido(id_origen);

} else {


bloquearCursor();
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, traspasoRapidoOK], traspasoRapidoNOK);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);
}
}
}
}
function borrarContenidoFilasOcultas() {
$('#TablaBean01 tr[id^="data_"]').each(function (index) {
$(this).find('*[id*=DivAjax]').each(function (index) {
$(this).html("");

});
});
}
function traspasoRapidoOK() {
desbloquearCursor();
}
function traspasoRapidoNOK() {
ControlError (null, null, null, null);
}


function continuarTraspasoRapido(cuentaOrig) {
InicializaErroresTR();
ProcesaErroresTR();
var cuentaDest = "";
var elemento = document.getElementById("selectCuentaDestino");
if (elemento!=null) {
cuentaDest = elemento.options[elemento.selectedIndex].value;
if (cuentaDest == 'INI' || cuentaDest == 'SIG'  || cuentaDest == 'SEL' || cuentaDest == '') {
AddErrorTR("Debe seleccionar una cuenta destino");
AddErrorTipoTR("selectCuentaDestino");
}
}
var importe = "";
elemento = document.getElementById("campoImporte");
if (elemento!=null) {
importe = validaImporte2("campoImporte");
}
if (ProcesaErroresTR()) {
var urlParams = "PN=TTU&PE=37";
urlParams += "&IMPORTE=";
urlParams += importe;
urlParams += "&REFVAL_SIMPLE_CUENTA_ORIGEN=";
urlParams += cuentaOrig;
urlParams += "&REFVAL_SIMPLE_CUENTA_DESTINO=";
urlParams += cuentaDest;
urlParams += "&idFilaCuenta=";
urlParams += idFila;
urlParams += "&CLICK_ORIG=";
urlParams += "FLX_GCT_11";
bloquearCursor();

var id_origen = idFila;
var id_destino = idFila + 'DivAjax';
abrirFilaTraspasoRapido(id_origen);
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, refrescaResultadoTraspasoRapido], errorRefrescaResultadoTraspasoRapido);
procesaAjaxQueueMB(AjaxQueueMB,true);
abrirFilaTraspasoRapido(id_origen);
}
}
function refrescaResultadoTraspasoRapido(data, textStatus, jqXHR, params, objOrigen, objDestino, objDestinoEvalScript) {

var divOcultoTR = document.getElementById("divOcultoTR");
divOcultoTR.innerHTML = data;

if(document.getElementById("evaluaScript_ttu37")){
refrescaTablaCuentas();
} else {





divOcultoTR.innerHTML = "";

desbloquearCursor();
}
}
function refrescaTablaCuentas() {
var f = document.forms[0];
var capa_pta = document.getElementById("PTS0");
f.PN.value = "GCT";
f.PE.value = "111";
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}
f.CLICK_ORIG.value = "AJAX_"+ f.PN.value+"_" + f.PE.value;
var paramsAjax=$("form[name=formPrincipal]").serialize();
enviaAsincrono(SCRIPTLET_SESION, paramsAjax, 'contenedorTablaInventarioCuentas', 'POST', paginacionInventarioCuentasOK, paginacionInventarioCuentasNOK);
}
function errorRefrescaResultadoTraspasoRapido() {
var html = '';
html+='<div id="errorResultadoTraspasoRapido">';
html+='<div class="ltxt">';
html+='<span class="bold ">';
html+=LIT_NO_DISPONIBLE;
html+='</span>';
html+='</div>';
html+='</div>';

document.getElementById(idFila + 'DivAjax').innerHTML = html;
desbloquearCursor();
}


function seleccionCuentaDestinoTraspasoRapido(param1, param2, param3) {

var selectBox = document.getElementById("selectCuentaDestino");
var selectedValue = selectBox.options[selectBox.selectedIndex].value;

var params=selectedValue.split("::");
if (params.length==3) {
param1=params[0];
param2=params[1];
param3=params[2];
} else{
param1=selectedValue;
}



if (param1=="INI" || param1=="SIG") {
var urlParams = "PN=GCT&PE=134";
urlParams += "&REFVAL_SIMPLE_CLAU_CONTINUACIO=";
if (param1=="INI") {
var CLAU_CONTINUACIO_INI = "D0mbUI4GX5QPSZtQjgZflAAAAWekGROpx~51_9fhWTw"
;
urlParams += CLAU_CONTINUACIO_INI;
} else {
urlParams += param2;
}
urlParams += "&REFVAL_SIMPLE_NUMERO_CUENTA=";
urlParams += param3;
urlParams += "&ORIGEN_INVOCACION=PAG_CUENTA_DESTINO";
urlParams += "&TIPO_LISTA_CUENTAS_TRASPASO_RAPIDO=DESTINO";
urlParams += "&CLICK_ORIG=";
urlParams += "PAG_GCT_134";
bloquearCursor();
enviaAsincrono(SCRIPTLET_SESION, urlParams, 'DIVSelectCuentasDestino', 'POST', refrescaSelectCuentasDestino, errorRefrescaSelectCuentasDestino);
}
}
function refrescaSelectCuentasDestino() {
var html = http_request.responseText;
if (html!=null && $.trim(html)!="" && html.indexOf("divListaCuentasTraspasoRapidoError") > -1) {
document.getElementById(idFila + 'DivAjax').innerHTML = html;
} else {
$('#selectCuentaDestino').parent().html(html);
}
desbloquearCursor();
}
function errorRefrescaSelectCuentasDestino() {
var html = '';
html+='<div id="errorRefrescaSelectCuentasDestino">';
html+='<div class="ltxt">';
html+='<span class="bold ">';
html+=LIT_NO_DISPONIBLE;
html+='</span>';
html+='</div>';
html+='</div>';

document.getElementById(idFila + 'DivAjax').innerHTML = html;
desbloquearCursor();
}


function pagInicio(){
var f =document.forms[0];
var capa_pta = document.getElementById("PTS0");
f.PN.value = "GCT";
f.PE.value = "111";
f.CLAVE_CONTINUACION_CLCOTG.value="000"
f.CLAVE_CONTINUACION_TOOFCU.value="000000000000000 000000000000000 "
f.CLAVE_CONTINUACION_TOGECU.value="00000000000 000000000000000 "
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}

f.CLICK_ORIG.value = "PAG_"+ f.PN.value+"_11";
var paramsAjax=$("form[name=formPrincipal]").serialize();
bloquearCursor();
enviaAsincrono(SCRIPTLET_SESION, paramsAjax, 'contenedorTablaInventarioCuentas', 'POST', paginacionInventarioCuentasOK, paginacionInventarioCuentasNOK);
}
function pagSiguiente() {
var f = document.forms[0];
var capa_pta = document.getElementById("PTS0");
f.PN.value = "GCT";
f.PE.value = "111";
if (capa_pta.style.display == 'none') {
f.FLAG_MONEDA.value = 0
} else {
f.FLAG_MONEDA.value = 1
}

f.CLICK_ORIG.value = "PAG_"+ f.PN.value+"_11";
f.CLAVE_CONTINUACION_CLCOTG.value=f.CLAVE_CONTINUACION_CLCOTG_SIG.value;
f.CLAVE_CONTINUACION_TOOFCU.value=f.CLAVE_CONTINUACION_TOOFCU_SIG.value;
f.CLAVE_CONTINUACION_TOGECU.value=f.CLAVE_CONTINUACION_TOGECU_SIG.value;
var paramsAjax=$("form[name=formPrincipal]").serialize();
bloquearCursor();
enviaAsincrono(SCRIPTLET_SESION, paramsAjax, 'contenedorTablaInventarioCuentas', 'POST', paginacionInventarioCuentasOK, paginacionInventarioCuentasNOK);
}
function paginacionInventarioCuentasOK() {
var html = http_request.responseText;

var divOculto = document.getElementById("divOculto");
divOculto.innerHTML = html;

$(divOculto).find('#contenedorTablaInventarioCuentasAJAX').each(function () {
document.getElementById('contenedorTablaInventarioCuentas').innerHTML = $(this).html();
});

if(document.getElementById("evaluaScript_GCT111_ERROR")){

eval(document.getElementById("evaluaScript_GCT111_ERROR").innerHTML);
} else {


if(document.getElementById("evaluaScript_GCT111")){

eval(document.getElementById("evaluaScript_GCT111").innerHTML);

$(divOculto).find("#TablaBean01EvalScript").each(function (index) {
jQuery.globalEval($(this).html());
});

var divOcultoTR = document.getElementById("divOcultoTR");

if (divOcultoTR!=null && divOcultoTR.innerHTML!="") {

if(document.getElementById("evaluaScript_ttu37")){
eval(document.getElementById("evaluaScript_ttu37").innerHTML);
}

var divTraspasoRapido = $('#'+idFila+'Oculta').find('div#' + idFila + 'DivAjax');

$(divTraspasoRapido).html(divOcultoTR.innerHTML);

abrirFilaTraspasoRapido(idFila);



divOcultoTR.innerHTML = "";
}
}
}

divOculto.innerHTML = "";

initTooltips();

desbloquearCursor();
}
function paginacionInventarioCuentasNOK() {
var html = '';
html+='<div id="errorSolicitarInfoTraspasoRapido" style="padding:0 14px 0 14px;">';
html+='<div class="ltxt">';
html+='<span class="bold ">';
html+=LIT_NO_DISPONIBLE;
html+='</span>';
html+='</div>';
html+='</div>';
document.getElementById('contenedorTablaInventarioCuentas').innerHTML = html;
desbloquearCursor();
}

function ControlError (codigoError, http_request_table, idTabla, tr_select) {
var div = $('#'+idFila+'Oculta').find('div#' + idFila + 'DivAjax');
var html='';
html+='<div id="errorExtractoReducido" style="padding:0 14px 0 14px;">';
html+='<div class="ltxt">';
html+='<span class="bold ">';
html+=LIT_NO_DISPONIBLE;
html+='</span>';
html+='</div>';
html+='</div>';
div.html(html);
desbloquearCursor();
}
function cerrarDetalles(idFilaCuenta) {
var href = $("#" + idFilaCuenta).find('[id^="celdaExtractoReducido"] a').attr('href');
window.location.href = href;
}
function cerrarDetallesTraspasoRapido(idFilaCuenta) {
InicializaErrores();
var href = $("#" + idFilaCuenta).find('[id^="celdaTraspasoRapido"] a').attr('href');
window.location.href = href;
}
function cerrarTodosLosDetallesAbiertos(borrarContenido) {
$('#TablaBean01 tr[id^="data_"]').each(function (index) {
if ($(this).attr('id').indexOf('Oculta') > -1 ) {
if ( $(this).css('display')=='' || $(this).css('display')=='block' || $(this).css('display')=='table-row')  {
$(this).attr('style','display:none');
$(this).addClass('ocultar');
if (borrarContenido) {
$(this).find("div#TablaBean01DivAjax").each(function (index) {
$(this).html("");
});
}
}
}
});
}
function verTodosMovimientosCuenta(idFilaCuenta) {
var href = $("#" + idFilaCuenta).find('td a').attr('href');
window.location.href = href;
}
function bloquearCursor(){
$.blockUI({overlayCSS: {backgroundColor: '#7F97A7', opacity: .5 }, message: null});
}
function desbloquearCursor(){
$.unblockUI({ fadeOut: 200 });
}
String.prototype.trim = function(){
return this.replace(/^[\s\xA0]+/g,'').replace(/[\s(&nbsp;)]+$/g,'');
}
function validaImporte(campoImporte) {
var importe_formateado = "";
var importe = $('#' + campoImporte).val();

if($.trim(importe)==""){
AddErrorTR("Para poder realizar el traspaso debe introducir un importe.");
AddErrorTipoTR("campoImporte");
} else {

var res1 = Verifica_Importe(importe, "E");
if (res1 != 0) {
if (res1 == 2) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
}
if (res1 == 5) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
}
if (res1 == 3) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
}
if (res1 == 4) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
}
if (res1 == 1 || res1 == 6) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
}
} else {
importe = Eliminar_Formato(importe);

if (importe > 999999999999999) {
AddErrorTR("El importe introducido para el traspaso es incorrecto.");
AddErrorTipoTR("campoImporte");
} else {
importe_formateado = Rellenar_Importe(importe,15);
$('#' + campoImporte).val(formatoImporteHOST2Importe(importe_formateado));
}
}
}
return importe_formateado;
}
function validaImporte2(campoImporte) {
var importe_formateado = "";
var temp_import = $('#' + campoImporte).val();
var errorAct = 0;

if (temp_import=='') {
AddErrorTR("Debe introducir el importe");
AddErrorTipoTR("campoImporte");
errorAct=1
}

var impaux = Eliminar_FormatoImporte(Eliminar_espacios(temp_import), "E")
if (impaux > 9999999900){
AddErrorTR("El importe no puede ser mayor que 99.999.999");
AddErrorTipoTR("campoImporte");
errorAct=1
}

if (temp_import.charAt(0) == " ") {
AddErrorTR("El importe contiene caracteres blancos");
AddErrorTipoTR("campoImporte");
}
var res = Verifica_Importe2(temp_import, "E")
if (res != 0){
if (res == 2) {
AddErrorTR("El importe contiene caracteres no admisibles");
AddErrorTipoTR("campoImporte");
}
if (res == 5) {
AddErrorTR("El importe contiene caracteres blancos");
AddErrorTipoTR("campoImporte");
}
if (res == 3) {
AddErrorTR("En el importe sólo se permiten dos decimales");
AddErrorTipoTR("campoImporte");
}
if (res == 4) {
AddErrorTR("Formato del importe incorrecto");
AddErrorTipoTR("campoImporte");
}
if (res == 1 ||res == 6) {
AddErrorTR("Importe introducido incorrecto");
AddErrorTipoTR("campoImporte");
}
if (res == 20){
AddErrorTR("Importe incorrecto: Use coma (,) para los céntimos, ej. 234,34");
AddErrorTipoTR("campoImporte");
}
errorAct=1
}


if (errorAct != 1 && impaux == 0) {
AddErrorTR("Debe introducir el importe");
AddErrorTipoTR("campoImporte");
errorAct=1
}
if (errorAct != 1) {
temp_import = Eliminar_Formato(temp_import);
importe_formateado = Rellenar_Importe(temp_import,15);
$('#' + campoImporte).val(formatoImporteHOST2Importe(importe_formateado));
}
return importe_formateado;
}

function formatoImporteHOST2Importe(str) {
if (str!=null && $.trim(str)!="") {
var d = parseFloat($.trim(str)) / 100;
return formatoImporte(d);
} else {
return "";
}
}
function formatoImporte(num) {
return num
.toFixed(2)
.replace(".", ",")
.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.")
}
function importeFormatoImporteHOST(cadena, longitud) {
var cadena_res = Eliminar_Formato(cadena);
var signo = "";
if (cadena.substring(0,1) == "-") {
signo = "-";
cadena_res = cadena.substring(1);
}
var longAux = longitud - cadena_res.length;
for (var i=0; i < longAux; i++)
cadena_res = "0" + cadena_res;
cadena_res = signo + cadena_res;
return cadena_res;
}
function descargaPdf() {
var formName = "goPNPE";
with (document.forms[formName]) {
target="Oculto";
submit();
}
}
function isDefined(variable) {
return (typeof variable == "undefined")?  false: true;
}
function enviarUrl(url) {
window.open(url,'window','toolbar=yes,width=650,height=400,directories=no,status=no,scrollbars=yes,resizable=yes,menubar=yes');
}
function getFieldValueFormById(formName, fieldId) {
return $('form[name=' + formName + '] input[id='+ fieldId +']').val();
}
function getFieldValueForm(formName, fieldName) {
return $('form[name=' + formName + '] input[name='+ fieldName +']').val();
}
function addFormField(formName, fieldName, fieldValue) {
$('form[name="' + formName + '"]').append('<input type="hidden" name="' + fieldName + '" value="' + fieldValue + '" />');
}
function removeAllFormField(formName) {
$('form[name="' + formName + '"] input').remove();
}
function removeFormField(formName, fieldName) {
return $('form[name=' + formName + '] input[name='+ fieldName +']').remove();
}
function setFieldValueForm(formName, fieldName, value) {
$('form[name=' + formName + '] input[name='+ fieldName +']').val(value);
}
function initTooltips() {
existTooltipError = false;
$(function() {
$( ".tooltip_active[title]" ).tooltip({
show: false,
hide: false,
position: {
at: "left top+10",
using: function( position, feedback ) {
if ($(feedback.target.element).data("tooltip-position") == "left") {
position.left -= 12;
}
$( this ).css( position );
$( "<div>" )
.addClass( "arrow" )
.addClass( feedback.vertical )
.addClass( feedback.horizontal )
.appendTo( this );
}
}
});
if ($(".tooltip_active[title]").length > 0){
existTooltipError = true;
}
});
}
function enviaOperativaLinkPrioritario(pn, pe, opt1,opt2,opt3,opt4,opt5,opt6,opt7,opt8,opt9,opt10,
opt11,opt12,opt13,opt14,opt15,opt16,opt17,opt18,opt19,opt20,opt21,opt22,opt23,opt24,opt25,opt26,
entorno,pnmenu,pemenu,parametroFijo,tipoLink,tornaPN,tornaPE){
var formName = "goPNPE";
removeAllFormField(formName);
with (document.forms[formName]) {
target="Cos";
addFormField(formName, "VTACREU_PN", pn);
addFormField(formName, "VTACREU_PE", pe);
addFormField(formName, "NUMERO_MOVIMIENTO", opt1);
addFormField(formName, "FECHA_CONTABLE", opt2);
addFormField(formName, "INDICADOR_COMUNICADOS", opt3);
addFormField(formName, "IMPORTE_COM", opt4);
addFormField(formName, "FECHA_COM", opt5);
addFormField(formName, "MONEDA_COM", opt6);
addFormField(formName, "CLOPWW", opt7);
addFormField(formName, "SUBCLO", opt8);

addFormField(formName, "TIPO_COMUNICADO", opt10);

addFormField(formName, "TIPO_BUSQUEDA", opt12);
addFormField(formName, "NUMERO_RECIBO", opt13);
addFormField(formName, "REFVAL_SIMPLE_NUMERO_CUENTA", opt14);
addFormField(formName, "FLAG_TITULO", opt15);
addFormField(formName, "REF_CUENTA", opt16);
addFormField(formName, "FLUJO_T", opt17);
addFormField(formName, "SIGNO_IMPORTE_COM", opt18);
addFormField(formName, "SIGNO_SALDO_ACTUAL", opt19);
addFormField(formName, "SALDO_ACTUAL", opt20);
addFormField(formName, "SIGNO_SALDO_RETENIDO", opt21);
addFormField(formName, "SALDO_RETENIDO", opt22);
addFormField(formName, "FECHA_VALOR", opt23);
addFormField(formName, "INDICA_SALDO", opt24);
addFormField(formName, "FLAG_KEEP_THE_CHANGE", opt25);
addFormField(formName, "INDICADOR_CANCELADA", opt26);
addFormField(formName, "PARAMETRO_FIJO", parametroFijo);
addFormField(formName, "TORNA_PN", tornaPN);
addFormField(formName, "TORNA_PE", tornaPE);
addFormField(formName, "PN", "GCT");
addFormField(formName, "PE", "104");
addFormField(formName, "FLAG_PE", top.flagPE);
var tornaPN_tornaPE = tornaPN + "_" + tornaPE;
if (tipoLink=="G"){
addFormField(formName, "CLICK_ORIG", "GLO_" + tornaPN_tornaPE);
}else if (tipoLink=="B"){
addFormField(formName, "CLICK_ORIG", "BOT_" + tornaPN_tornaPE);
}else {
addFormField(formName, "CLICK_ORIG", "EOC_" + tornaPN_tornaPE);
}
if (entorno=="*") entorno=top.flagPE;
if (pnmenu=="*") pnmenu="";
if (pemenu=="*") pemenu="";
var url= "";
url = url + "&";
url = url + $("form[name=" + formName + "]").serialize();
url = url + "&DESC_COMUNICADO=" + URLEncode(opt9);
url = url + "&REMITENTE="       + URLEncode(opt11);
top.Inferior.Menu.lanzarLO(entorno,"GCT","104",url,CLICK_ORIG.value,pnmenu,pemenu);
}
}
function ejecutaScript(textoAsincrono, id_container) {
var scripts = new Array();
var scriptsJS = new Array();
var p=textoAsincrono.indexOf("<script");
var j=0;
while(p!=-1){
var f=textoAsincrono.indexOf("</script",p);
if(f>p){
var p1=textoAsincrono.indexOf('>',p);
if(p1+1<f) {
var texAux=textoAsincrono.substring(p,p1);
if (texAux.indexOf("evaluaScript_102") < 0) {
scripts.push(textoAsincrono.substring(p1+1, f));
}
}else if (p1+1==f){
var j=textoAsincrono.indexOf("js/",p);
var j1=textoAsincrono.indexOf(".js",p);
scriptsJS.push(textoAsincrono.substring(j,j1+3));
}
p=textoAsincrono.indexOf("<script",f+1);
}else{
p=-1;
}
}



for(var i=0; i<scriptsJS.length; i++) {
$.ajax({
url: "./"+scriptsJS[i],
async: false,
dataType: "script"
})
}

for(var i=0; i<scripts.length; i++) {
var nuevoscript = document.createElement('script');
nuevoscript.text = scripts[i];
nuevoscript.id = 'jsCampanya';
nuevoscript.type = 'text/javascript';
if(scripts[i].src!=null && scripts[i].src.length>0) {
nuevoscript.src = scripts[i].src;
}
document.getElementById(id_container).appendChild(nuevoscript);
}
}
function mostrarDisponiblePAI(imagen_landing, importe_formateado, tagOmniture) {
document.forms["pai"].LND_IMAGEN.value=imagen_landing;
document.forms["pai"].LND_VALOR1.value=importe_formateado;
document.forms["pai"].submit();
}
function mostrarAntiPAI(parametros) {
if (parametros!=null && parametros!="") {
var formName = "antipai";
var click_orig = getFieldValueForm(formName, "CLICK_ORIG")
removeAllFormField(formName);
var params = parametros.split("&");
var param = null;
for (var i=0; i < params.length; i++) {
param = params[i].split("=");
addFormField(formName, param[0], param[1]);
}
addFormField(formName, "CLICK_ORIG", click_orig);
document.forms[formName].submit();
}
}

var erroresTR = new Array();
var erroresTipoTR = new Array();
function InicializaErroresTR() {
erroresTR = new Array();
erroresTipoTR = new Array();
var elemento = document.getElementById("id_errorTR");
if (elemento!=null) {
elemento.innerHTML = "";
}
}
function AddErrorTR(errorTR) {
erroresTR.push(errorTR);
}
function AddErrorTipoTR(errorTipoTR) {
erroresTipoTR.push(errorTipoTR);
}
function ProcesaErroresTR() {
var elemento = document.getElementById("id_errorTR");
if (elemento!=null) {
elemento.innerHTML = "";
if (erroresTR.length > 0) {
for (var i=0; i < erroresTR.length; i++) {
elemento.innerHTML += "<p>";
elemento.innerHTML += erroresTR[i];
elemento.innerHTML += "</p>";
}
$('#id_errorTR').removeClass('dnone');
marcarErrorCamposFormulario();
} else {
$('#id_errorTR').addClass('dnone');
desmarcarErrorCamposFormulario();
return true;
}
}
return false;
}
function marcarErrorCamposFormulario() {
if (erroresTR.length > 0) {
for (var i=0; i < erroresTipoTR.length; i++) {
if (!$('#' + erroresTipoTR[i]).hasClass('euros_form_error')) {
$('#' + erroresTipoTR[i]).addClass('euros_form_error');
}
}
}
}
function desmarcarErrorCamposFormulario() {
$('#selectCuentaDestino').removeClass('euros_form_error');
$('#campoImporte').removeClass('euros_form_error');
}

function masInfo(){
var id_destino="bloquePromoDesplegable01ContenedorBloqueDesplegableVideo";
var contenidoVideo = document.getElementById(id_destino).innerHTML;

if (contenidoVideo.trim()!="") {
controlfilahucha();
}else{
var urlParams = "PN=GCT&PE=150";
AjaxQueueMB.set("POST", true, 60000, '/GPeticiones;WebLogicSession=CrXb-eLKhAsayArsnEi2H9S7y1MCp3pzCgLR9m2kP5OJDN7KqiwG!1225849572!440257436', urlParams, $('#'+id_destino+''), $('#'+id_destino+''), null, [callBackGenericaMB, refrescaResultadoVideo], errorRefrescaResultadoVideo);
procesaAjaxQueueMB(AjaxQueueMB,true);
}
}
function controlfilahucha(){

if ($('#bloquePromoDesplegable01ContenedorBloqueDesplegable').is(':hidden')) {
$("#enlaceBloquePromoDesplegable01").addClass("see_more_open");
$('#bloquePromoDesplegable01ContenedorBloqueDesplegable').show();
} else{
pauseVideoBrightcove('#videobc');
$("#enlaceBloquePromoDesplegable01").removeClass("see_more_open");
$('#bloquePromoDesplegable01ContenedorBloqueDesplegable').hide();
}
}
function refrescaResultadoVideo (data, textStatus, jqXHR, params, objOrigen, objDestino, objDestinoEvalScript) {

$("#enlaceBloquePromoDesplegable01").addClass("see_more_open");
$("#bloquePromoDesplegable01ContenedorBloqueDesplegable").show();
}
function errorRefrescaResultadoVideo () {

var parrafoError= "<p class='mens_error_rojo_pq'><span>";
parrafoError+="En estos momentos el vídeo no está disponible, sentimos las molestias.";
parrafoError+="</span></p>";
document.getElementById("bloquePromoDesplegable01ContenedorBloqueDesplegableVideo").innerHTML=parrafoError;
$("#enlaceBloquePromoDesplegable01").addClass("see_more_open");
$("#bloquePromoDesplegable01ContenedorBloqueDesplegable").show();
}
function abrirUnaHucha() {
var EntornoMenu = "P";
var PNDestino = "GDL";
var PEDestino = "10";
var url = "&TORNA_PN=GCT&TORNA_PE=11";
var clickorig = "EOC_"+ document.forms[0].PN.value+"_" + document.forms[0].PE.value;
var PNMenu = "GDL";
var PEMenu = "1";
top.Inferior.Menu.lanzarLO(EntornoMenu,PNDestino,PEDestino,url,clickorig,PNMenu,PEMenu);
}
function mostrarRetencionesSaldo(refvalcuenta) {
var formName = "goPNPE";
removeAllFormField(formName);
with (document.forms[formName]) {
target="Cos";
addFormField(formName, "FLUJO", "GCT,11,'':GFI,7,''");
addFormField(formName, "CLICK_ORIG", "FLX_GCT_11");
addFormField(formName, "REFVAL_SIMPLE_NUMERO_CUENTA", refvalcuenta);
addFormField(formName, "PN", "GCT");
addFormField(formName, "PE", "18");
submit();
}
}
function masInfo2(){
var id_destino="bloquePromoDesplegable01ContenedorBloqueDesplegableVideo";
if (id_destino!=null) {
if (document.getElementById(id_destino).innerHTML.trim() == "") {
document.getElementById(id_destino).innerHTML = "<img class='' src='" + "./imatge/CAST_misfinanzas.png" + "'>";
}
}
if ($('#bloquePromoDesplegable01ContenedorBloqueDesplegable').is(':hidden')) {
$("#enlaceBloquePromoDesplegable01").addClass("see_more_open");
$('#bloquePromoDesplegable01ContenedorBloqueDesplegable').show();
} else{
$("#enlaceBloquePromoDesplegable01").removeClass("see_more_open");
$('#bloquePromoDesplegable01ContenedorBloqueDesplegable').hide();
}
}
function anyadirAgregacion() {
var formName = "goPNPE";
removeAllFormField(formName);
with (document.forms[formName]) {
target="Cos";
addFormField(formName, "FLUJO", "GCT,11,'':GFI,7,''");
addFormField(formName, "CLICK_ORIG", "FLX_GCT_11");
addFormField(formName, "VOLVER_PN", "GCT");
addFormField(formName, "VOLVER_PE", "11");
addFormField(formName, "PN", "AGF");
addFormField(formName, "PE", "1");
submit();
}
}
