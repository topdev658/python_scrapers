// Bank of america encrypt functions from cc.go (loaded from bankofamerica.com/smallbusiness)

// Will be called from Ba() as part of   Da.encode(Aa(Q.stringify(s)))
var Da = {
  _keyStr: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/\x3d", encode: function (a) {
    var b = "", c, d, e, f, g, k, l = 0
    for (a = Da._utf8_encode(a); l <
    a.length;) c = a.charCodeAt(l++), d = a.charCodeAt(l++), e = a.charCodeAt(l++), f = c >> 2, c = (c & 3) << 4 | d >> 4, g = (d & 15) << 2 | e >> 6, k = e & 63, isNaN(d) ? g = k = 64 : isNaN(e) && (k = 64), b = b + this._keyStr.charAt(f) + this._keyStr.charAt(c) + this._keyStr.charAt(g) + this._keyStr.charAt(k)
    return b
  }, _utf8_encode: function (a) {
    for (var b = "", c = 0; c < a.length; c++) {
      var d = a.charCodeAt(c)
      128 > d ? b += String.fromCharCode(d) : (127 < d && 2048 > d ? b += String.fromCharCode(d >> 6 | 192) : (b += String.fromCharCode(d >> 12 | 224), b += String.fromCharCode(d >> 6 & 63 | 128)), b += String.fromCharCode(d &
        63 | 128))
    }
    return b
  }
}

function k(a) {
  try {
    "js-errors" in s || (s["js-errors"] = []), s["js-errors"].push(a.toString())
  } catch (b) {
  }
}

function Aa(a) {
  try {
    for (var b = "", c = [89, 231, 225, 55], d = 0; d < a.length; d++) b += String.fromCharCode(a.charCodeAt(d) ^ c[d % c.length])
    return b
  } catch (e) {
    return k(e), ""
  }
}

// Example, will not be used directly
function Ba() {
  // Wa defined as a const below in the script
  f.methods & Wa && "undefined" !== typeof Storage ? Ca(localStorage) : f.methods &
  Xa && "undefined" !== typeof Storage ? Ca(sessionStorage) : 0 < Object.keys(l.bfd).length && g("bfd", l.bfd)
  void 0 != window.accertifyNamespace && (window.accertifyNamespace.sendPtno(), window.accertifyNamespace.sendAll(), 0 < P.length && g("uba", P))
  if (f.methods & Ya) {
    for (var a = "", b = Sa(Aa(unescape(encodeURIComponent(Q.stringify(s))))), c = 0; c < b.length; c++) a += String.fromCharCode(b[c])
    return "x9x91" + a
  }
  // Final encrypt step, Q is JSON
  return Da.encode(Aa(JSON.stringify(s)))
}


/**
 * node bank_of_america_enc.js '{"sid":"933928f25519a10e","tid":"5678","_t":"ZGNkY2U1MmYtMWI4ZC00MDQ4LWJjMjgtYjRlNjg0MTEzYjllOjE1NTEwNDM1NDMyNjM","cf_flags":155687923,"cookie-_cc":"NTUzZTNhYzMtNjVlOS00ZjYz","timing-sc":15,"time-unix-epoch-ms":1551043622006,"time-local":"2/25/2019, 12:27:02 AM","time-string":"Mon Feb 25 2019 00:27:02 GMT+0300 (MSK)","time-tz-offset-minutes":-180,"time-tz-has-dst":"false","time-tz-dst-active":"false","time-tz-std-offset":-180,"time-tz-fixed-locale-string":"3/6/2014, 7:58:39 AM","timing-ti":1,"dom-local-tag":"ODI5NDc1YzItYjIyMy00NTMw","timing-ls":0,"dom-session-tag":"YThmNjk5MDUtYzFlNS00OWFk","timing-ss":0,"navigator.appVersion":"5.0 (X11)","navigator.appName":"Netscape","navigator.buildID":"20171024165158","navigator.product":"Gecko","navigator.platform":"Linux x86_64","navigator.language":"en-US","navigator.oscpu":"Linux x86_64","navigator.userAgent":"Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0","navigator.cookieEnabled":"true","navigator.appCodeName":"Mozilla","navigator.productSub":"20100101","timing-no":4,"window.devicePixelRatio":"1","window.hi...}'
 *
 */
(function () {
  var sessionData = process.argv[2]
  var encrypted = Da.encode(Aa(sessionData))
  
  console.log(encrypted)
})()
