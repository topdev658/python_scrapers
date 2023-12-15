function getKeyRandom() {
    var sessionId=getCookie("JSESSIONID");
    if (!Date.now) {
        Date.now = function() { return new Date().getTime(); }
    }
    var crypto = window.crypto || window.msCrypto;
    var cryptoValue = "";
    if(typeof(crypto)!='undefined') {
        var randomValuesArray = new Int32Array(1);
        cryptoValue = Math.abs(crypto.getRandomValues(randomValuesArray)[0]);
    } else {
        cryptoValue = randomString(10);
    }
    if (sessionId==null || sessionId==""){
        keyRandom = cryptoValue + Date.now();
    } else {
        keyRandom = sessionId.substring(0,7) + cryptoValue + Date.now();  //  <----------------
    }
    return keyRandom;
}
