import re
from datetime import datetime
from typing import List

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import CorrespondenceDocParsed
from .custom_types import CorrespondenceAccountOption


def get_correspondence_account_options(resp_text: str) -> List[CorrespondenceAccountOption]:
    """
    Parses
    <option value="0121780000763400008898">IBAN ES70 2048 2178 7634 0000 8898 - CUENTA
                                        CORRIENTE
    </option>
    <option value="1621780000759804000498"> 2048-2178-75-9804000498 - AVALES</option>
    """
    accounts_from_dropdown = []  # type: List[CorrespondenceAccountOption]
    dropdown_html = extract.re_first_or_blank('(?si)<select name="GCUENTA".*?</select>', resp_text)
    dropdown_options = re.findall('(?si)<option.*?value="([^"]+)"[^>]?>(.*?)</option>', dropdown_html)
    for opt in dropdown_options:
        opt_value = opt[0]
        opt_text = opt[1]
        account_name = opt_text
        if ' - ' in account_name:
            account_name = account_name.split(' - ')[0]
        account_no = re.sub('[IBAN ]', '', account_name)
        account_from_dropdown = CorrespondenceAccountOption(
            # 20480903959200000012 / ES7020482178763400008898
            account_no=account_no,
            # 1209030000959200000012 / 0121780000763400008898
            gcuenta_param=opt_value,
            # 20480903959200000012 / 20482178763400008898
            cuentaenvia_param=account_no[-20:],
            # 2048-0903-95-9200000012 - FACTORING / IBAN ES70 2048 2178 7634 0000 8898 - CUENTA CORRIENTE
            ibanorigen_param=opt_text,
        )
        accounts_from_dropdown.append(account_from_dropdown)
    return accounts_from_dropdown


def get_correspondence_from_list(
        logger: ScrapeLogger,
        resp_text: str,
        account_no: str) -> List[CorrespondenceDocParsed]:
    """
    Parses and reproduces JS behavior
    <!-- CUENTA x|20482178763400008898| -->
    <!-- FECHA x|06-07-2020| -->
    <!-- FORMATO x|0161| -->
    <!-- NOMBRE_FORMATO x|ORDEN MOVIMIENTOS DE FONDOS RECIBIDOS| -->
    <!-- REGISTROS x|1| -->
    <!-- COMENTARIOS x|ALTUNA Y URIA, S.A.| -->
    <!-- DESDE_REGISTRO x|3600953| -->
    <!-- HASTA_REGISTRO x|3600953| -->
    <!-- ATRIBUTOS x|      <REFERENCIA>000FE3FE070043800058</REFERENCIA>   <DATO3>25.000,00</DATO3>   <DATO2>TRASP CRN A LIBERBANK</DATO2>   <DATO4></DATO4>   <DATO5></DATO5>   <DATO1>ALTUNA Y URIA, S.A.</DATO1>      | -->
    <!-- PENDIENTE x|1| -->
    <!-- FAMILIA x|BE0003| -->
    <script type="text/javascript">
    var color = (0 % 2 == 0) ? 'impar' : 'par';
    var importe = '
        <REFERENCIA>000BG6BG080043800058</REFERENCIA>
        <DATO1></DATO1>
        <DATO2>2178-9804000480 000000</DATO2>
        <DATO4></DATO4>
        <DATO3>230,20</DATO3>
        '.split("<DATO3>");
    if (importe.length > 1) {
        importe = importe[1].split("</DATO3>");
        importe = importe[0]; 25.000,00
    } else
        importe = '';

    var texto1 = '
        <REFERENCIA>000BG6BG080043800058</REFERENCIA>
        <DATO1></DATO1>
        <DATO2>2178-9804000480 000000</DATO2>
        <DATO4></DATO4>
        <DATO3>230,20</DATO3>
        '.split("<DATO1>");
    if (texto1.length > 1) {
        texto1 = texto1[1].split("</DATO1>");
        texto1 = texto1[0];
    } else
        texto1 = '';

    var texto2 = '
        <REFERENCIA>000BG6BG080043800058</REFERENCIA>
        <DATO1></DATO1>
        <DATO2>2178-9804000480 000000</DATO2>
        <DATO4></DATO4>
        <DATO3>230,20</DATO3>
        '.split("<DATO2>");
    if (texto2.length > 1) {
        texto2 = texto2[1].split("</DATO2>");
        texto2 = texto2[0];
    } else
        texto2 = '';

    var texto3 = '
        <REFERENCIA>000BG6BG080043800058</REFERENCIA>
        <DATO1></DATO1>
        <DATO2>2178-9804000480 000000</DATO2>
        <DATO4></DATO4>
        <DATO3>230,20</DATO3>
        '.split("<DATO4>");
    if (texto3.length > 1) {
        texto3 = texto3[1].split("</DATO4>");
        texto3 = texto3[0];
    } else
        texto3 = '';

    var descripcion = "";
    if (texto1 != '') {
        descripcion = texto1;
    }
    if (texto2 != '') {
        if (descripcion != '') descripcion = descripcion + "<br>" + texto2;
        else descripcion = texto2;
    }
    if (texto3 != '') {
        if (descripcion != '') descripcion = descripcion + "<br>" + texto3;
        else descripcion = texto3;
    }
                var color = (cont % 2 == 0) ? 'impar' : 'par';
                cont++;
                document.write('<tr class=' + color + '>');
            </script>
            <td>01-07-2020</td>
            <td>
                <script>
                    var cuenta = '20482178763400008898';
                    if (('BE0003' == 'BE0003') || ('BE0003' == 'BE0004')) {
                        var ibancuenta = getIbanCuenta('763400008898');
                        document.write(ibancuenta);
                    } else {
                        if (cuenta.length != 8) {
                            var pri = cuenta.substring(0, 4);
                            var sec = cuenta.substring(4, 8);
                            var ter = cuenta.substring(8, 10);
                            var cuar = cuenta.substring(10);
                            document.write(cuenta);
                        }
                    }
                </script>
            </td>

            <td class="dato-visible">
                <div class="columnaConcepto">
                    <script>
                        //document.write('<span id="visible_leido'+cont+'">');
                        document.write('<img id="visible_leido' + cont + '" src="/5485/imagenes/sobre_cerrado_gris.png" />');
                        //document.write('</span>');
                        document.write('&nbsp;<a onclick="javascript:modificarLeido(' + cont + ')" class="docNoLeido marron" href="/BEWeb/2048/5485/not6580_d_0.action?OPERACION=not6580_d_0&IDIOMA=01&OPERAC=6578&LLAMADA=43A3Z3A051D0B0R1F0B3&CLIENTE=2048099385&CAJA=2048&CAMINO=5485&amp;GCUENTA=20480121780000763400008898&amp;CUENTA=20482178763400008898&amp;FECHA=01-07-2020&amp;DESDE_REGISTRO=885749&amp;HASTA_REGISTRO=885749&amp;FORMATO_INICIAL=0178&amp;DEDONDE=9713&amp;CLIENTE=2048099385" title="Ver PDF" target="_blank">Transferencia Realizada - Sepa</a>');

    """
    corrs_from_list = []  # type: List[CorrespondenceDocParsed]
    corrs_table_html = extract.re_first_or_blank('(?si)<table[^>]*class="generica">(.*?)</table>', resp_text)
    corr_htmls = re.findall(
        r'(?si)<!-- CUENTA.*?title="Ver PDF"'
        "",
        corrs_table_html
    )
    for corr_html in corr_htmls:
        # Check for wide mathing de to missing PDF for some document
        if len(re.findall('<!-- CUENTA', corr_html)) > 1:
            logger.error('{}: get_correspondence_from_list: parsing error for corr_html:\n{}\n\nSkip'.format(
                account_no,
                corr_html
            ))
            continue
        corr_date_str = extract.re_first_or_blank(r'<!-- FECHA x\|(.*?)\|', corr_html)  # 06-07-2020
        amount_str = extract.re_first_or_blank('<DATO3>(.*?)</DATO3>', corr_html)  # 25.000,00
        amount = convert.to_float(amount_str) if amount_str else None
        # join parts and remove extra blank lines
        descr = re.sub(
            r'\n\n',
            '\n',
            extract.re_first_or_blank('<DATO1>(.*?)</DATO1>', corr_html) + '\n' +
            extract.re_first_or_blank('<DATO2>(.*?)</DATO2>', corr_html) + '\n' +
            extract.re_first_or_blank('<DATO4>(.*?)</DATO4>', corr_html)
        ).strip()
        corr_type = extract.re_first_or_blank(r'<!-- NOMBRE_FORMATO x\|(.*?)\| -->', corr_html)
        req_link = extract.re_first_or_blank(r'href="([^"]+)"\s+title="Ver PDF"', corr_html)
        corr = CorrespondenceDocParsed(
            account_no=account_no,
            type=corr_type,
            operation_date=datetime.strptime(corr_date_str, '%d-%m-%Y'),  # 06-07-2020
            value_date=None,
            descr=descr,
            amount=amount,
            currency=None,
            extra={
                'req_link': req_link
            }
        )
        corrs_from_list.append(corr)

    return corrs_from_list
