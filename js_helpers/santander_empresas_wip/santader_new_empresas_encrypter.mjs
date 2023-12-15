import JSEncrypt from './santander_empresas_wip/jsencrypt/JSEncrypt.js';

// function t() {
//     this.n = null,
//         this.e = 0,
//         this.d = null,
//         this.p = null,
//         this.q = null,
//         this.dmp1 = null,
//         this.dmq1 = null,
//         this.coeff = null
// }
//
// t.prototype.doPublic = function(t) {
//     return t.modPowInt(this.e, this.n)
// }
//
// // this is called with pwd
// t.prototype.encrypt = function(t) {
//     var e = new me;
//     return e.setPublicKey("-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwYq0hHQayVsX3xuFDnuH\nhDg6oBgSAq33oNjgrzH3wbLeIIs/++CpypGzg/5W26GC50MOMuakL+UfIAk9mDxL\n5QhB6XkkDRVhyUOGrTLwGDnyXE5+MPYZmf8wPy7sESzLFTw/3isEgmJh6WRnYH2F\nnHWnvCsE3Ow710OKLpG8eh0/kjH0rYP+KrqcxTfD72SABytNcyXFjT1hhW4YFEMV\nLASKpkzo8mxhiiXNcha+x1oekxoVPmD/FtF9PPvWKn2yhzSfo4TPOtspA5GNIB+T\nz+v6kjc3nwBB1LDOat9+lVI0VxxQ0+PxPFPyurSGhoTL9p0JC+bRmrZkWzALh+jY\nFwIDAQAB\n-----END PUBLIC KEY-----"),
//         // t - passwd
//         e.encrypt(t).toString()
// }
//
// // TOTALLY AS FOR PARTICULARES
//
// // see particulares
// // function RSAEncrypt(text, digestFn) {
// //     void 0 === digestFn && (digestFn = pkcs1pad2);
// //     var m = digestFn(text,(this.n.bitLength()+7)>>3);
// //     if(m == null) return null;
// //     var c = this.doPublic(m);
// //     if(c == null) return null;
// //     var h = c.toString(16);
// //     if((h.length & 1) == 0) return h; else return "0" + h;
// // }
// t.prototype.encrypt = function(passwd) {
//     var e = this.n.bitLength() + 7 >> 3
//         // n is result of pkcs1pad2(passwd, e)
//         , n = function(t, e) {
//         if (e < t.length + 11)
//             return console.error("Message too long for RSA"),
//                 null;
//         for (var n = [], i = t.length - 1; i >= 0 && e > 0; ) {
//             var r = t.charCodeAt(i--);
//             r < 128 ? n[--e] = r : r > 127 && r < 2048 ? (n[--e] = 63 & r | 128,
//                 n[--e] = r >> 6 | 192) : (n[--e] = 63 & r | 128,
//                 n[--e] = r >> 6 & 63 | 128,
//                 n[--e] = r >> 12 | 224)
//         }
//         n[--e] = 0;
//         for (var o = new ae, s = []; e > 2; ) {
//             for (s[0] = 0; 0 == s[0]; )
//                 o.nextBytes(s);
//             n[--e] = s[0]
//         }
//         return n[--e] = 2,
//             n[--e] = 0,
//             new jt(n)
//     }(passwd, e);
//     if (null == n)
//         return null;
//     //
//     var i = this.doPublic(n);
//     if (null == i)
//         return null;
//     for (var r = i.toString(16), o = r.length, s = 0; s < 2 * e - o; s++)
//         r = "0" + r;
//     return r
// }


//   public encrypt(pass: string): string {
//     const crypt = new JSEncrypt();
//     const secret =
//       '-----BEGIN PUBLIC KEY-----\n' +
//       'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwYq0hHQayVsX3xuFDnuH\n' +
//       'hDg6oBgSAq33oNjgrzH3wbLeIIs/++CpypGzg/5W26GC50MOMuakL+UfIAk9mDxL\n' +
//       '5QhB6XkkDRVhyUOGrTLwGDnyXE5+MPYZmf8wPy7sESzLFTw/3isEgmJh6WRnYH2F\n' +
//       'nHWnvCsE3Ow710OKLpG8eh0/kjH0rYP+KrqcxTfD72SABytNcyXFjT1hhW4YFEMV\n' +
//       'LASKpkzo8mxhiiXNcha+x1oekxoVPmD/FtF9PPvWKn2yhzSfo4TPOtspA5GNIB+T\n' +
//       'z+v6kjc3nwBB1LDOat9+lVI0VxxQ0+PxPFPyurSGhoTL9p0JC+bRmrZkWzALh+jY\n' +
//       'FwIDAQAB\n' +
//       '-----END PUBLIC KEY-----';
//
//     crypt.setPublicKey(secret);
//     const encripted = crypt.encrypt(pass);
//     return encripted.toString();
//   }
function encrypt(pass) {
    let crypt = new JSEncrypt();
    let secret =
        '-----BEGIN PUBLIC KEY-----\n' +
        'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwYq0hHQayVsX3xuFDnuH\n' +
        'hDg6oBgSAq33oNjgrzH3wbLeIIs/++CpypGzg/5W26GC50MOMuakL+UfIAk9mDxL\n' +
        '5QhB6XkkDRVhyUOGrTLwGDnyXE5+MPYZmf8wPy7sESzLFTw/3isEgmJh6WRnYH2F\n' +
        'nHWnvCsE3Ow710OKLpG8eh0/kjH0rYP+KrqcxTfD72SABytNcyXFjT1hhW4YFEMV\n' +
        'LASKpkzo8mxhiiXNcha+x1oekxoVPmD/FtF9PPvWKn2yhzSfo4TPOtspA5GNIB+T\n' +
        'z+v6kjc3nwBB1LDOat9+lVI0VxxQ0+PxPFPyurSGhoTL9p0JC+bRmrZkWzALh+jY\n' +
        'FwIDAQAB\n' +
        '-----END PUBLIC KEY-----';

    crypt.setPublicKey(secret);
    const encripted = crypt.encrypt(pass);
    console.log(encripted.toString());
}


(function () {
    let userpass = process.argv[2];
    encrypt(userpass)
})();
