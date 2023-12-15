var CryptoJS = require("crypto-js");

function getToken (c,t,n){
		c||(c=""),t||(t=""),n||(n="");

		console.log("c: " + c);  // c = target path
		console.log("t: " + t);  // t = local token
		console.log("n: " + n);  // n = call params JSON string

		var a=t.substring(3,10)+t.substring(16,22)+t.substring(45,55)+c; // updTokenSign = token part + target path path
		console.log("a: " + a);

		return CryptoJS.HmacSHA512(n,a)} // HmacSHA512(callParamsJsonString, updTokenSign)

/**
 * node encrypt.js 189315 71CC5875F175A652 0000000000000000 001 48
 * node encrypt.js passphrase form.A form.D from.C callPamamLon=48
 */
(function () {
    var c  = process.argv[2];       // targetPath
    var t = process.argv[3];        // current token
    var n = process.argv[4];        // json string

    var tokenCRC = getToken(c, t, n);
    console.log("TKN-CRC: " + tokenCRC);
})();
