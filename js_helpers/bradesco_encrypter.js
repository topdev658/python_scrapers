'use strict';

var navigator = {
    appName: 'Netscape',
    appVersion: '5.0 (X11)'
};

var window = {}; // window.crypto is used


var bla124;
var bla122;
var bla12;
var BI_FP = 52;
var BI_RM = "0123456789abcdefghijklmnopqrstuvwxyz";
var BI_RC = new Array();
var rr, vv;
var as1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var as4 = "=";
var as3 = 256;
var c1;
var as2 = 0xdeadbeefcafe;
var j_lm = ((as2 & 0xffffff) == 0xefcafe);

function blabla1_int(x) {
    bla122[bla12++] ^= x & 255;
    bla122[bla12++] ^= (x >> 8) & 255;
    bla122[bla12++] ^= (x >> 16) & 255;
    bla122[bla12++] ^= (x >> 24) & 255;
    if (bla12 >= as3) bla12 -= as3;
}

function blabla12() {
    blabla1_int(new Date().getTime());
}

if (bla122 == null) {
    bla122 = new Array();
    bla12 = 0;
    var t;
    if (navigator.appName == "Netscape" && navigator.appVersion < "5" && window.crypto) {
        var z = window.crypto.random(32);
        for (t = 0; t < z.length; ++t) bla122[bla12++] = z.charCodeAt(t) & 255;
    }
    while (bla12 < as3) {
        t = Math.floor(65536 * Math.random());
        bla122[bla12++] = t >>> 8;
        bla122[bla12++] = t & 255;
    }
    bla12 = 0;
    blabla12();
}

function bla123() {
    if (bla124 == null) {
        blabla12();
        bla124 = bla133();
        bla124.a2(bla122);
        for (bla12 = 0; bla12 < bla122.length; ++bla12)
            bla122[bla12] = 0;
        bla12 = 0;
    }
    return bla124.a3();
}

function a1(ba) {
    var i;
    for (i = 0; i < ba.length; ++i) ba[i] = bla123();
}

function B1() {
}

B1.prototype.A1 = a1;

function B2() {
    this.i = 0;
    this.j = 0;
    this.S = new Array();
}

function A2(key) {
    var i, j, t;
    for (i = 0; i < 256; ++i) this.S[i] = i;
    j = 0;
    for (i = 0; i < 256; ++i) {
        j = (j + this.S[i] + key[i % key.length]) & 255;
        t = this.S[i];
        this.S[i] = this.S[j];
        this.S[j] = t;
    }
    this.i = 0;
    this.j = 0;
}

function A3() {
    var t;
    this.i = (this.i + 1) & 255;
    this.j = (this.j + this.S[this.i]) & 255;
    t = this.S[this.i];
    this.S[this.i] = this.S[this.j];
    this.S[this.j] = t;
    return this.S[(t + this.S[this.i]) & 255];
}

B2.prototype.a2 = A2;
B2.prototype.a3 = A3;

function bla133() {
    return new B2();
}

function B3(a, b, c) {
    if (a != null)
        if ("number" == typeof a) this.fromNumber(a, b, c);
        else if (b == null && "string" != typeof a) this.E3(a, 256); else this.E3(a, b);
}

function nbi() {
    return new B3(null);
}

function am1(i, x, w, j, c, n) {
    while (--n >= 0) {
        var v = x * this[i++] + w[j] + c;
        c = Math.floor(v / 0x4000000);
        w[j++] = v & 0x3ffffff;
    }
    return c;
}

function am2(i, x, w, j, c, n) {
    var xl = x & 0x7fff, xh = x >> 15;
    while (--n >= 0) {
        var l = this[i] & 0x7fff;
        var h = this[i++] >> 15;
        var m = xh * l + h * xl;
        l = xl * l + ((m & 0x7fff) << 15) + w[j] + (c & 0x3fffffff);
        c = (l >>> 30) + (m >>> 15) + xh * h + (c >>> 30);
        w[j++] = l & 0x3fffffff;
    }
    return c;
}

function am3(i, x, w, j, c, n) {
    var xl = x & 0x3fff, xh = x >> 14;
    while (--n >= 0) {
        var l = this[i] & 0x3fff;
        var h = this[i++] >> 14;
        var m = xh * l + h * xl;
        l = xl * l + ((m & 0x3fff) << 14) + w[j] + c;
        c = (l >> 28) + (m >> 14) + xh * h;
        w[j++] = l & 0xfffffff;
    }
    return c;
}

if (j_lm && (navigator.appName == "Microsoft Internet Explorer")) {
    B3.prototype.am = am2;
    c1 = 30;
} else if (j_lm && (navigator.appName != "Netscape")) {
    B3.prototype.am = am1;
    c1 = 26;
} else {
    B3.prototype.am = am3;
    c1 = 28;
}
B3.prototype.DB = c1;
B3.prototype.DM = ((1 << c1) - 1);
B3.prototype.DV = (1 << c1);
B3.prototype.FV = Math.pow(2, BI_FP);
B3.prototype.F1 = BI_FP - c1;
B3.prototype.F2 = 2 * c1 - BI_FP;
rr = "0".charCodeAt(0);
for (vv = 0; vv <= 9; ++vv) BI_RC[rr++] = vv;
rr = "a".charCodeAt(0);
for (vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv;
rr = "A".charCodeAt(0);
for (vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv;

function int2char(n) {
    return BI_RM.charAt(n);
}

function intAt(s, i) {
    var c = BI_RC[s.charCodeAt(i)];
    return (c == null) ? -1 : c;
}

function e1(r) {
    for (var i = this.t - 1; i >= 0; --i) r[i] = this[i];
    r.t = this.t;
    r.s = this.s;
}

function e2(x) {
    this.t = 1;
    this.s = (x < 0) ? -1 : 0;
    if (x > 0) this[0] = x; else if (x < -1) this[0] = x + DV;
    else this.t = 0;
}

function nbv(i) {
    var r = nbi();
    r.E2(i);
    return r;
}

function e3(s, b) {
    var k;
    if (b == 16) {
        k = 4;
    } else if (b == 8) {
        k = 3;
    } else if (b == 256) {
        k = 8;
    } else if (b == 2) {
        k = 1;
    } else if (b == 32) {
        k = 5;
    } else if (b == 4) {
        k = 2;
    } else {
        this.fromRadix(s, b);
        return;
    }
    this.t = 0;
    this.s = 0;
    var i = s.length, mi = false, sh = 0;
    while (--i >= 0) {
        var x = (k == 8) ? s[i] & 0xff : intAt(s, i);
        if (x < 0) {
            if (s.charAt(i) == "-") mi = true;
            continue;
        }
        mi = false;
        if (sh == 0) this[this.t++] = x;
        else if (sh + k > this.DB) {
            this[this.t - 1] |= (x & ((1 << (this.DB - sh)) - 1)) << sh;
            this[this.t++] = (x >> (this.DB - sh));
        } else {
            this[this.t - 1] |= x << sh;
        }
        sh += k;
        if (sh >= this.DB) sh -= this.DB;
    }
    if (k == 8 && (s[0] & 0x80) != 0) {
        this.s = -1;
        if (sh > 0) this[this.t - 1] |= ((1 << (this.DB - sh)) - 1) << sh;
    }
    this.E4();
    if (mi) B3.ZERO.E9(this, this);
}

function e4() {
    var c = this.s & this.DM;
    while (this.t > 0 && this[this.t - 1] == c) --this.t;
}

function eg(b) {
    if (this.s < 0) return "-" + this.negate().EG(b);
    var k;
    if (b == 16) k = 4;
    else if (b == 8) k = 3; else if (b == 2) k = 1; else if (b == 32) k = 5; else if (b == 4) k = 2;
    else return this.toRadix(b);
    var km = (1 << k) - 1, d, m = false, r = "", i = this.t;
    var p = this.DB - (i * this.DB) % k;
    if (i-- > 0) {
        if (p < this.DB && (d = this[i] >> p) > 0) {
            m = true;
            r = int2char(d);
        }
        while (i >= 0) {
            if (p < k) {
                d = (this[i] & ((1 << p) - 1)) << (k - p);
                d |= this[--i] >> (p += this.DB - k);
            } else {
                d = (this[i] >> (p -= k)) & km;
                if (p <= 0) {
                    p += this.DB;
                    --i;
                }
            }
            if (d > 0) m = true;
            if (m) r += int2char(d);
        }
    }
    return m ? r : "0";
}

function eh() {
    return (this.s < 0) ? this.negate() : this;
}

function ei(a) {
    var r = this.s - a.s;
    if (r != 0) return r;
    var i = this.t;
    r = i - a.t;
    if (r != 0) return r;
    while (--i >= 0) if ((r = this[i] - a[i]) != 0) return r;
    return 0;
}

function nbits(x) {
    var r = 1, t;
    if ((t = x >>> 16) != 0) {
        x = t;
        r += 16;
    }
    if ((t = x >> 8) != 0) {
        x = t;
        r += 8;
    }
    if ((t = x >> 4) != 0) {
        x = t;
        r += 4;
    }
    if ((t = x >> 2) != 0) {
        x = t;
        r += 2;
    }
    if ((t = x >> 1) != 0) {
        x = t;
        r += 1;
    }
    return r;
}

function ej() {
    if (this.t <= 0) return 0;
    return this.DB * (this.t - 1) + nbits(this[this.t - 1] ^ (this.s & this.DM));
}

function e5(n, r) {
    var i;
    for (i = this.t - 1; i >= 0; --i) r[i + n] = this[i];
    for (i = n - 1; i >= 0; --i) r[i] = 0;
    r.t = this.t + n;
    r.s = this.s;
}

function e6(n, r) {
    for (var i = n; i < this.t; ++i) r[i - n] = this[i];
    r.t = Math.max(this.t - n, 0);
    r.s = this.s;
}

function e7(n, r) {
    var bs = n % this.DB;
    var cbs = this.DB - bs;
    var bm = (1 << cbs) - 1;
    var ds = Math.floor(n / this.DB), c = (this.s << bs) & this.DM, i;
    for (i = this.t - 1; i >= 0; --i) {
        r[i + ds + 1] = (this[i] >> cbs) | c;
        c = (this[i] & bm) << bs;
    }
    for (i = ds - 1; i >= 0; --i) r[i] = 0;
    r[ds] = c;
    r.t = this.t + ds + 1;
    r.s = this.s;
    r.E4();
}

function e8(n, r) {
    r.s = this.s;
    var ds = Math.floor(n / this.DB);
    if (ds >= this.t) {
        r.t = 0;
        return;
    }
    var bs = n % this.DB;
    var cbs = this.DB - bs;
    var bm = (1 << bs) - 1;
    r[0] = this[ds] >> bs;
    for (var i = ds + 1; i < this.t; ++i) {
        r[i - ds - 1] |= (this[i] & bm) << cbs;
        r[i - ds] = this[i] >> bs;
    }
    if (bs > 0) r[this.t - ds - 1] |= (this.s & bm) << cbs;
    r.t = this.t - ds;
    r.E4();
}

function e9(a, r) {
    var i = 0, c = 0, m = Math.min(a.t, this.t);
    while (i < m) {
        c += this[i] - a[i];
        r[i++] = c & this.DM;
        c >>= this.DB;
    }
    if (a.t < this.t) {
        c -= a.s;
        while (i < this.t) {
            c += this[i];
            r[i++] = c & this.DM;
            c >>= this.DB;
        }
        c += this.s;
    } else {
        c += this.s;
        while (i < a.t) {
            c -= a[i];
            r[i++] = c & this.DM;
            c >>= this.DB;
        }
        c -= a.s;
    }
    r.s = (c < 0) ? -1 : 0;
    if (c < -1) r[i++] = this.DV + c;
    else if (c > 0) r[i++] = c;
    r.t = i;
    r.E4();
}

function ea(a, r) {
    var x = this.EH(), y = a.EH();
    var i = x.t;
    r.t = i + y.t;
    while (--i >= 0) r[i] = 0;
    for (i = 0; i < y.t; ++i) r[i + x.t] = x.am(0, y[i], r, i, 0, x.t);
    r.s = 0;
    r.E4();
    if (this.s != a.s) B3.ZERO.E9(r, r);
}

function eb(r) {
    var x = this.EH();
    var i = r.t = 2 * x.t;
    while (--i >= 0) r[i] = 0;
    for (i = 0; i < x.t - 1; ++i) {
        var c = x.am(i, x[i], r, 2 * i, 0, 1);
        if ((r[i + x.t] += x.am(i + 1, 2 * x[i], r, 2 * i + 1, c, x.t - i - 1)) >= x.DV) {
            r[i + x.t] -= x.DV;
            r[i + x.t + 1] = 1;
        }
    }
    if (r.t > 0) r[r.t - 1] += x.am(i, x[i], r, 2 * i, 0, 1);
    r.s = 0;
    r.E4();
}

function ec(m, q, r) {
    var pm = m.EH();
    if (pm.t <= 0) return;
    var pt = this.EH();
    if (pt.t < pm.t) {
        if (q != null) q.E2(0);
        if (r != null) this.E1(r);
        return;
    }
    if (r == null) r = nbi();
    var y = nbi(), ts = this.s, ms = m.s;
    var nsh = this.DB - nbits(pm[pm.t - 1]);
    if (nsh > 0) {
        pm.E7(nsh, y);
        pt.E7(nsh, r);
    } else {
        pm.E1(y);
        pt.E1(r);
    }
    var ys = y.t;
    var y0 = y[ys - 1];
    if (y0 == 0) return;
    var yt = y0 * (1 << this.F1) + ((ys > 1) ? y[ys - 2] >> this.F2 : 0);
    var d1 = this.FV / yt, d2 = (1 << this.F1) / yt, e = 1 << this.F2;
    var i = r.t, j = i - ys, t = (q == null) ? nbi() : q;
    y.E5(j, t);
    if (r.EI(t) >= 0) {
        r[r.t++] = 1;
        r.E9(t, r);
    }
    B3.ONE.E5(ys, t);
    t.E9(y, y);
    while (y.t < ys) y[y.t++] = 0;
    while (--j >= 0) {
        var qd = (r[--i] == y0) ? this.DM : Math.floor(r[i] * d1 + (r[i - 1] + e) * d2);
        if ((r[i] += y.am(0, qd, r, j, 0, ys)) < qd) {
            y.E5(j, t);
            r.E9(t, r);
            while (r[i] < --qd) r.E9(t, r);
        }
    }
    if (q != null) {
        r.E6(ys, q);
        if (ts != ms) B3.ZERO.E9(q, q);
    }
    r.t = ys;
    r.E4();
    if (nsh > 0) r.E8(nsh, r);
    if (ts < 0) B3.ZERO.E9(r, r);
}

function Classic(m) {
    this.m = m;
}

function ed() {
    if (this.t < 1) return 0;
    var x = this[0];
    if ((x & 1) == 0) return 0;
    var y = x & 3;
    y = (y * (2 - (x & 0xf) * y)) & 0xf;
    y = (y * (2 - (x & 0xff) * y)) & 0xff;
    y = (y * (2 - (((x & 0xffff) * y) & 0xffff))) & 0xffff;
    y = (y * (2 - x * y % this.DV)) % this.DV;
    return (y > 0) ? this.DV - y : -y;
}

function B4(m) {
    this.m = m;
    this.mp = m.ED();
    this.mpl = this.mp & 0x7fff;
    this.mph = this.mp >> 15;
    this.um = (1 << (m.DB - 15)) - 1;
    this.mt2 = 2 * m.t;
}

function A4(x) {
    var r = nbi();
    x.EH().E5(this.m.t, r);
    r.EC(this.m, null, r);
    if (x.s < 0 && r.EI(B3.ZERO) > 0) this.m.E9(r, r);
    return r;
}

function A5(x) {
    var r = nbi();
    x.E1(r);
    this.a6(r);
    return r;
}

function A6(x) {
    while (x.t <= this.mt2) x[x.t++] = 0;
    for (var i = 0; i < this.m.t; ++i) {
        var j = x[i] & 0x7fff;
        var u0 = (j * this.mpl + (((j * this.mph + (x[i] >> 15) * this.mpl) & this.um) << 15)) & x.DM;
        j = i + this.m.t;
        x[j] += this.m.am(0, u0, x, i, 0, this.m.t);
        while (x[j] >= x.DV) {
            x[j] -= x.DV;
            x[++j]++;
        }
    }
    x.E4();
    x.E6(this.m.t, x);
    if (x.EI(this.m) >= 0) x.E9(this.m, x);
}

function A8(x, r) {
    x.EB(r);
    this.a6(r);
}

function A7(x, y, r) {
    x.EA(y, r);
    this.a6(r);
}

B4.prototype.a4 = A4;
B4.prototype.a5 = A5;
B4.prototype.a6 = A6;
B4.prototype.a7 = A7;
B4.prototype.a8 = A8;

function ee() {
    return ((this.t > 0) ? (this[0] & 1) : this.s) == 0;
}

function ef(e, z) {
    if (e > 0xffffffff || e < 1) return B3.ONE;
    var r = nbi(), r2 = nbi(), g = z.a4(this), i = nbits(e) - 1;
    g.E1(r);
    while (--i >= 0) {
        z.a8(r, r2);
        if ((e & (1 << i)) > 0) z.a7(r2, g, r); else {
            var t = r;
            r = r2;
            r2 = t;
        }
    }
    return z.a5(r);
}

function ek(e, m) {
    var z;
    if (e < 256 || m.EE()) z = new Classic(m); else z = new B4(m);
    return this.EF(e, z);
}

B3.prototype.E1 = e1;
B3.prototype.E2 = e2;
B3.prototype.E3 = e3;
B3.prototype.E4 = e4;
B3.prototype.E5 = e5;
B3.prototype.E6 = e6;
B3.prototype.E7 = e7;
B3.prototype.E8 = e8;
B3.prototype.E9 = e9;
B3.prototype.EA = ea;
B3.prototype.EB = eb;
B3.prototype.EC = ec;
B3.prototype.ED = ed;
B3.prototype.EE = ee;
B3.prototype.EF = ef;
B3.prototype.EG = eg;
B3.prototype.EH = eh;
B3.prototype.EI = ei;
B3.prototype.EJ = ej;
B3.prototype.EK = ek;
B3.ZERO = nbv(0);
B3.ONE = nbv(1);

function xifds(h) {
    var i;
    var c;
    var ret = "";
    for (i = 0; i + 3 <= h.length; i += 3) {
        c = parseInt(h.substring(i, i + 3), 16);
        ret += as1.charAt(c >> 6) + as1.charAt(c & 63);
    }
    if (i + 1 == h.length) {
        c = parseInt(h.substring(i, i + 1), 16);
        ret += as1.charAt(c << 2);
    } else if (i + 2 == h.length) {
        c = parseInt(h.substring(i, i + 2), 16);
        ret += as1.charAt(c >> 2) + as1.charAt((c & 3) << 4);
    }
    while ((ret.length & 3) > 0) ret += as4;
    return ret;
}

function bla125(s) {
    var ret = "";
    var i;
    var k = 0;
    var slop;
    for (i = 0; i < s.length; ++i) {
        if (s.charAt(i) == as4) break;
        v = as1.indexOf(s.charAt(i));
        if (v < 0) continue;
        if (k == 0) {
            ret += int2char(v >> 2);
            slop = v & 3;
            k = 1;
        } else if (k == 1) {
            ret += int2char((slop << 2) | (v >> 4));
            slop = v & 0xf;
            k = 2;
        } else if (k == 2) {
            ret += int2char(slop);
            ret += int2char(v >> 2);
            slop = v & 3;
            k = 3;
        } else {
            ret += int2char((slop << 2) | (v >> 4));
            ret += int2char(v & 0xf);
            k = 0;
        }
    }
    if (k == 1) ret += int2char(slop << 2);
    return ret;
}

function asd1(s) {
    var h = bla125(s);
    var i;
    var a = new Array();
    for (i = 0; 2 * i < h.length; ++i) {
        a[i] = parseInt(h.substring(2 * i, 2 * i + 2), 16);
    }
    return a;
}

function bla131(str, r) {
    return new B3(str, r);
}

function asd2(s, n) {
    if (n < s.length + 11) {
        // console.error("Texto para encriptar muito grande.");
        return null;
    }
    var ba = new Array();
    var i = s.length - 1;
    while (i >= 0 && n > 0) ba[--n] = s.charCodeAt(i--);
    ba[--n] = 0;
    var rng = new B1();
    var x = new Array();
    while (n > 2) {
        x[0] = 0;
        while (x[0] == 0) rng.A1(x);
        ba[--n] = x[0];
    }
    ba[--n] = 2;
    ba[--n] = 0;
    return new B3(ba);
}

function bla132() {
    this.n = null;
    this.e = 0;
    this.d = null;
    this.p = null;
    this.q = null;
    this.dmp1 = null;
    this.dmq1 = null;
    this.coeff = null;
}

function em(N, E) { // N, E - big, set this.n
    if (N != null && E != null && N.length > 0 && E.length > 0) {
        this.n = bla131(N, 16);
        this.e = parseInt(E, 16);
    } else {
        alert("Chave Publica Invalida.");
    }
}

function el(x) {
    return x.EK(this.e, this.n);
}

function en(text) {
    var m = asd2(text, (this.n.EJ() + 7) >> 3);
    // var m = asd2(text, (ej() + 7) >> 3);
    if (m == null) return null;
    var c = this.EL(m);
    if (c == null) return null;
    var h = c.EG(16);
    if ((h.length & 1) == 0) return h;
    else return "0" + h;
}

function eo(text) {
    var h = this.EN(text + '\0');
    if (h) return xifds(h);
    else return null;
}

bla132.prototype.EL = el;
bla132.prototype.EM = em;
bla132.prototype.EN = en;
bla132.prototype.EO = eo;

/*
INTERFACE EXPORTAVAL PARA PAGINAS HTML
*/
function rng_seed_time() {
    blabla12();
}


// login.jsf
// setPublic(n_InternetBanking, e_InternetBanking);
function setPublic(n, e) {
    rsa.EM(n, e);
}

var rsa = new bla132();

// var vAux = cript(numControle, jQuery("#identificationForm\\:txtSenha").val());
// strData = "&senhaCript=" + encodeURIComponent(vAux);
function cript(nroControle, dados) {
    if (rsa == null) {
        alert('Erro! Modulo de criptografia nao inicializado.');
        return false;
    }
    var res = rsa.EO(nroControle + dados);
    return res;
}


/**
 * node bradesco_encrypter.js "sw101112" "654319207745677001"
 */
(function () {
    let dados = process.argv[2];
    let nroControle = process.argv[3];

    // D735CF0A...
    let n_InternetBanking = process.argv[4];
    // 10001
    let e_InternetBanking = process.argv[5];
    setPublic(n_InternetBanking, e_InternetBanking);

    var encrypted = cript(nroControle, dados);
    console.log(encrypted);
})();

