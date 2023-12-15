function validateForm() {
    var b = $("#idioma").val();
    if (!validateFields(b)) {
        return false
    }
    var f = $("#cod_emp").val().toUpperCase();
    var g = $("#cod_usu").val().toUpperCase();
    var j = $("#eai_password").val().toUpperCase();

    // implement in python code
    var e = "0023";                   // <------------- e+d = 00230001 -> eai_user = 00230001+company+username
    var d = "0001";                   // <-------------
    if (f.substring(0, 1) == "3") {
        d = "0073"
    }
    var a = e + d + f;
    if (g != "ACTIVAR" && g != "UNNIM") {
        a = a + g
    }
    $("#eai_user").val(a);
    $("#cod_emp").val(f);
    $("#cod_usu").val(g);
    $("#eai_password").val(j);
    setCookie("CODIGO_ERROR", "");

    var h = getCookie("CODIGO_PRODUCTO");  // get from s.cookies in python

    if (companyVariableList.length > 0) {
        if (h == "CX" || h == "405") {
            var c = getCompanyOk(f);
            if (f.indexOf("7") == 0 && c == true) {
                $("#logonForm").attr("action", "/DFAUTH/slod_mult_mult/MigrationServlet")
            } else {
                if (!f.indexOf("7") == 0 && c == true) {
                    $("#logonForm").attr("action", "/DFAUTH/slod_mult_mult/MigrationServlet")
                } else {
                    if (f.indexOf("7") == 0 && c == false) {
                        redirectD15();
                        return false
                    } else {
                        $("#logonForm").attr("action", "/DFAUTH/slod_mult_mult/DFServlet")
                    }
                }
            }
        }
    } else {

        // implement in python code
        if (h == "CX" || h == "405") {
            if (f.indexOf("7") == 0) {
                $("#logonForm").attr("action", "/DFAUTH/slod_mult_mult/MigrationServlet")
            } else {
                $("#logonForm").attr("action", "/DFAUTH/slod_mult_mult/DFServlet")
            }
        }
    }
    $("#logonForm").submit();
    saveDataAccessCookies();
    return true
}
