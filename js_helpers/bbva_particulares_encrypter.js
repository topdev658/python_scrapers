// from login.min.js
// session cookie generator
function e() {
    var e = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
    return e.replace(/[xy]/g, function (e) {
        var t = 16 * Math.random() | 0
            , n = "x" === e ? t : 3 & t | 8
        return n.toString(16)
    })
}

/**
 * node bbva_particulares_encrypter.js
 */
(function () {
    var contractid = e();
    console.log(contractid);
})();


