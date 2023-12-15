function encrypt(theText, salt) {

	var textos = [];
	textos[0] = "a";
	textos[1] = "b";
	textos[2] = "c";
	textos[3] = "d";
	textos[4] = "e";
	textos[5] = "e";
	var r = "";
	var as = "";
	for (var i = 0; i < theText.length; i++){
		if (salt>0 && salt<133)
			as = salt + theText.charCodeAt(i);
		else
			as = (133) + theText.charCodeAt(i);
		as = as.toString(16);
		var aleat = Math.random() * 9;
		var caract = Math.random() * 5;
		r = r + (as.substring(1,2) + textos[Math.round(caract)]+ as.substring(0,1)+ parseInt(Math.round(aleat)));
	}
	return r;
}

/**
 * node cajamar_encrypter.js 189315 71CC5875F175A652 0000000000000000 001 48
 */
(function () {
    var text  = process.argv[2];       // theText
    var salt = +process.argv[3];        // salt

    var encrypted = encrypt(text, salt);
    console.log(encrypted);
})();
