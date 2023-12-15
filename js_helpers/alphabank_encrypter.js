// from  <script src="/Login/bundles/rsa?v=YszIIcG7s6me4M8TzrSs2CgWZR9G-omZWgaddEMSukg1"></script>

var navigator = {
  appName : "Netscape",
  appVersion: "5.0 (X11)"
};

// expecting window.crypto
var window = {};
var document = {};

function BigInteger(n, t, i) {
  n != null && ("number" == typeof n ? this.fromNumber(n, t, i) : t == null && "string" != typeof n ? this.fromString(n, 256) : this.fromString(n, t))
}

function nbi() {
  return new BigInteger(null)
}

function am1(n, t, i, r, u, f) {
  while (--f >= 0) {
    var e = t * this[n++] + i[r] + u
    u = Math.floor(e / 67108864)
    i[r++] = e & 67108863
  }
  return u
}

function am2(n, t, i, r, u, f) {
  for (var o = t & 32767, s = t >> 15; --f >= 0;) {
    var e = this[n] & 32767, h = this[n++] >> 15, c = s * e + h * o
    e = o * e + ((c & 32767) << 15) + i[r] + (u & 1073741823)
    u = (e >>> 30) + (c >>> 15) + s * h + (u >>> 30)
    i[r++] = e & 1073741823
  }
  return u
}

function am3(n, t, i, r, u, f) {
  for (var o = t & 16383, s = t >> 14; --f >= 0;) {
    var e = this[n] & 16383, h = this[n++] >> 14, c = s * e + h * o
    e = o * e + ((c & 16383) << 14) + i[r] + u
    u = (e >> 28) + (c >> 14) + s * h
    i[r++] = e & 268435455
  }
  return u
}

function int2char(n) {
  return BI_RM.charAt(n)
}

function intAt(n, t) {
  var i = BI_RC[n.charCodeAt(t)]
  return i == null ? -1 : i
}

function bnpCopyTo(n) {
  for (var t = this.t - 1; t >= 0; --t) n[t] = this[t]
  n.t = this.t
  n.s = this.s
}

function bnpFromInt(n) {
  this.t = 1
  this.s = n < 0 ? -1 : 0
  n > 0 ? this[0] = n : n < -1 ? this[0] = n + this.DV : this.t = 0
}

function nbv(n) {
  var t = nbi()
  return t.fromInt(n), t
}

function bnpFromString(n, t) {
  var r,
  u;
  if (t == 16) r = 4;
   else if (t == 8) r = 3;
   else if (t == 256) r = 8;
   else if (t == 2) r = 1;
   else if (t == 32) r = 5;
   else if (t == 4) r = 2;
   else {
    this.fromRadix(n, t);
    return
  }
  this.t = 0;
  this.s = 0;
  for (var f = n.length, e = !1, i = 0; --f >= 0; ) {
    if (u = r == 8 ? n[f] & 255 : intAt(n, f), u < 0) {
      n.charAt(f) == '-' && (e = !0);
      continue
    }
    e = !1;
    i == 0 ? this[this.t++] = u : i + r > this.DB ? (this[this.t - 1] |= (u & (1 << this.DB - i) - 1) << i, this[this.t++] = u >> this.DB - i)  : this[this.t - 1] |= u << i;
    i += r;
    i >= this.DB && (i -= this.DB)
  }
  r == 8 && (n[0] & 128) != 0 && (this.s = - 1, i > 0 && (this[this.t - 1] |= (1 << this.DB - i) - 1 << i));
  this.clamp();
  e && BigInteger.ZERO.subTo(this, this)
}

function bnpClamp() {
  for (var n = this.s & this.DM; this.t > 0 && this[this.t - 1] == n;) --this.t
}

function bnToString(n) {
  var t;
  if (this.s < 0) return '-' + this.negate().toString(n);
  if (n == 16) t = 4;
   else if (n == 8) t = 3;
   else if (n == 2) t = 1;
   else if (n == 32) t = 5;
   else if (n == 4) t = 2;
   else return this.toRadix(n);
  var o = (1 << t) - 1,
  u,
  f = !1,
  e = '',
  r = this.t,
  i = this.DB - r * this.DB % t;
  if (r-- > 0) for (i < this.DB && (u = this[r] >> i) > 0 && (f = !0, e = int2char(u)); r >= 0; ) i < t ? u = (this[r] & (1 << i) - 1) << t - i | this[--r] >> (i += this.DB - t)  : (u = this[r] >> (i -= t) & o, i <= 0 && (i += this.DB, --r)),
  u > 0 && (f = !0),
  f && (e += int2char(u));
  return f ? e : '0'
}

function bnNegate() {
  var n = nbi()
  return BigInteger.ZERO.subTo(this, n), n
}

function bnAbs() {
  return this.s < 0 ? this.negate() : this
}

function bnCompareTo(n) {
  var t = this.s - n.s, i
  if (t != 0) return t
  if (i = this.t, t = i - n.t, t != 0) return this.s < 0 ? -t : t
  while (--i >= 0) if ((t = this[i] - n[i]) != 0) return t
  return 0
}

function nbits(n) {
  var i = 1, t
  return (t = n >>> 16) != 0 && (n = t, i += 16), (t = n >> 8) != 0 && (n = t, i += 8), (t = n >> 4) != 0 && (n = t, i += 4), (t = n >> 2) != 0 && (n = t, i += 2), (t = n >> 1) != 0 && (n = t, i += 1), i
}

function bnBitLength() {
  return this.t <= 0 ? 0 : this.DB * (this.t - 1) + nbits(this[this.t - 1] ^ this.s & this.DM)
}

function bnpDLShiftTo(n, t) {
  for (var i = this.t - 1; i >= 0; --i) t[i + n] = this[i]
  for (i = n - 1; i >= 0; --i) t[i] = 0
  t.t = this.t + n
  t.s = this.s
}

function bnpDRShiftTo(n, t) {
  for (var i = n; i < this.t; ++i) t[i - n] = this[i]
  t.t = Math.max(this.t - n, 0)
  t.s = this.s
}

function bnpLShiftTo(n, t) {
  for (var u = n % this.DB, e = this.DB - u, o = (1 << e) - 1, r = Math.floor(n / this.DB), f = this.s << u & this.DM, i = this.t - 1; i >= 0; --i) t[i + r + 1] = this[i] >> e | f, f = (this[i] & o) << u
  for (i = r - 1; i >= 0; --i) t[i] = 0
  t[r] = f
  t.t = this.t + r + 1
  t.s = this.s
  t.clamp()
}

function bnpRShiftTo(n, t) {
  var i, r
  if (t.s = this.s, i = Math.floor(n / this.DB), i >= this.t) {
    t.t = 0
    return
  }
  var u = n % this.DB, f = this.DB - u, e = (1 << u) - 1
  for (t[0] = this[i] >> u, r = i + 1; r < this.t; ++r) t[r - i - 1] |= (this[r] & e) << f, t[r - i] = this[r] >> u
  u > 0 && (t[this.t - i - 1] |= (this.s & e) << f)
  t.t = this.t - i
  t.clamp()
}

function bnpSubTo(n, t) {
  for (var r = 0, i = 0, u = Math.min(n.t, this.t); r < u;) i += this[r] - n[r], t[r++] = i & this.DM, i >>= this.DB
  if (n.t < this.t) {
    for (i -= n.s; r < this.t;) i += this[r], t[r++] = i & this.DM, i >>= this.DB
    i += this.s
  } else {
    for (i += this.s; r < n.t;) i -= n[r], t[r++] = i & this.DM, i >>= this.DB
    i -= n.s
  }
  t.s = i < 0 ? -1 : 0
  i < -1 ? t[r++] = this.DV + i : i > 0 && (t[r++] = i)
  t.t = r
  t.clamp()
}

function bnpMultiplyTo(n, t) {
  var r = this.abs(), u = n.abs(), i = r.t
  for (t.t = i + u.t; --i >= 0;) t[i] = 0
  for (i = 0; i < u.t; ++i) t[i + r.t] = r.am(0, u[i], t, i, 0, r.t)
  t.s = 0
  t.clamp()
  this.s != n.s && BigInteger.ZERO.subTo(t, t)
}

function bnpSquareTo(n) {
  for (var i = this.abs(), t = n.t = 2 * i.t, r; --t >= 0;) n[t] = 0
  for (t = 0; t < i.t - 1; ++t) r = i.am(t, i[t], n, 2 * t, 0, 1), (n[t + i.t] += i.am(t + 1, 2 * i[t], n, 2 * t + 1, r, i.t - t - 1)) >= i.DV && (n[t + i.t] -= i.DV, n[t + i.t + 1] = 1)
  n.t > 0 && (n[n.t - 1] += i.am(t, i[t], n, 2 * t, 0, 1))
  n.s = 0
  n.clamp()
}

function bnpDivRemTo(n, t, i) {
  var e = n.abs(), h, u, c, a
  if (!(e.t <= 0)) {
    if (h = this.abs(), h.t < e.t) {
      t != null && t.fromInt(0)
      i != null && this.copyTo(i)
      return
    }
    i == null && (i = nbi())
    var r = nbi(), v = this.s, p = n.s, s = this.DB - nbits(e[e.t - 1])
    if (s > 0 ? (e.lShiftTo(s, r), h.lShiftTo(s, i)) : (e.copyTo(r), h.copyTo(i)), u = r.t, c = r[u - 1], c != 0) {
      var y = c * (1 << this.F1) + (u > 1 ? r[u - 2] >> this.F2 : 0), w = this.FV / y, b = (1 << this.F1) / y,
        k = 1 << this.F2, o = i.t, l = o - u, f = t == null ? nbi() : t
      for (r.dlShiftTo(l, f), i.compareTo(f) >= 0 && (i[i.t++] = 1, i.subTo(f, i)), BigInteger.ONE.dlShiftTo(u, f), f.subTo(r, r); r.t < u;) r[r.t++] = 0
      while (--l >= 0) if (a = i[--o] == c ? this.DM : Math.floor(i[o] * w + (i[o - 1] + k) * b), (i[o] += r.am(0, a, i, l, 0, u)) < a) for (r.dlShiftTo(l, f), i.subTo(f, i); i[o] < --a;) i.subTo(f, i)
      t != null && (i.drShiftTo(u, t), v != p && BigInteger.ZERO.subTo(t, t))
      i.t = u
      i.clamp()
      s > 0 && i.rShiftTo(s, i)
      v < 0 && BigInteger.ZERO.subTo(i, i)
    }
  }
}

function bnMod(n) {
  var t = nbi()
  return this.abs().divRemTo(n, null, t), this.s < 0 && t.compareTo(BigInteger.ZERO) > 0 && n.subTo(t, t), t
}

function Classic(n) {
  this.m = n
}

function cConvert(n) {
  return n.s < 0 || n.compareTo(this.m) >= 0 ? n.mod(this.m) : n
}

function cRevert(n) {
  return n
}

function cReduce(n) {
  n.divRemTo(this.m, null, n)
}

function cMulTo(n, t, i) {
  n.multiplyTo(t, i)
  this.reduce(i)
}

function cSqrTo(n, t) {
  n.squareTo(t)
  this.reduce(t)
}

function bnpInvDigit() {
  var t, n
  return this.t < 1 ? 0 : (t = this[0], (t & 1) == 0) ? 0 : (n = t & 3, n = n * (2 - (t & 15) * n) & 15, n = n * (2 - (t & 255) * n) & 255, n = n * (2 - ((t & 65535) * n & 65535)) & 65535, n = n * (2 - t * n % this.DV) % this.DV, n > 0 ? this.DV - n : -n)
}

function Montgomery(n) {
  this.m = n
  this.mp = n.invDigit()
  this.mpl = this.mp & 32767
  this.mph = this.mp >> 15
  this.um = (1 << n.DB - 15) - 1
  this.mt2 = 2 * n.t
}

function montConvert(n) {
  var t = nbi()
  return n.abs().dlShiftTo(this.m.t, t), t.divRemTo(this.m, null, t), n.s < 0 && t.compareTo(BigInteger.ZERO) > 0 && this.m.subTo(t, t), t
}

function montRevert(n) {
  var t = nbi()
  return n.copyTo(t), this.reduce(t), t
}

function montReduce(n) {
  for (var i, t, r; n.t <= this.mt2;) n[n.t++] = 0
  for (i = 0; i < this.m.t; ++i) for (t = n[i] & 32767, r = t * this.mpl + ((t * this.mph + (n[i] >> 15) * this.mpl & this.um) << 15) & n.DM, t = i + this.m.t, n[t] += this.m.am(0, r, n, i, 0, this.m.t); n[t] >= n.DV;) n[t] -= n.DV, n[++t]++
  n.clamp()
  n.drShiftTo(this.m.t, n)
  n.compareTo(this.m) >= 0 && n.subTo(this.m, n)
}

function montSqrTo(n, t) {
  n.squareTo(t)
  this.reduce(t)
}

function montMulTo(n, t, i) {
  n.multiplyTo(t, i)
  this.reduce(i)
}

function bnpIsEven() {
  return (this.t > 0 ? this[0] & 1 : this.s) == 0
}

function bnpExp(n, t) {
  var e
  if (n > 4294967295 || n < 1) return BigInteger.ONE
  var i = nbi(), r = nbi(), u = t.convert(this), f = nbits(n) - 1
  for (u.copyTo(i); --f >= 0;) t.sqrTo(i, r), (n & 1 << f) > 0 ? t.mulTo(r, u, i) : (e = i, i = r, r = e)
  return t.revert(i)
}

function bnModPowInt(n, t) {
  var i
  return i = n < 256 || t.isEven() ? new Classic(t) : new Montgomery(t), this.exp(n, i)
}

function Arcfour() {
  this.i = 0
  this.j = 0
  this.S = []
}

function ARC4init(n) {
  for (var i, r, t = 0; t < 256; ++t) this.S[t] = t
  for (i = 0, t = 0; t < 256; ++t) i = i + this.S[t] + n[t % n.length] & 255, r = this.S[t], this.S[t] = this.S[i], this.S[i] = r
  this.i = 0
  this.j = 0
}

function ARC4next() {
  var n
  return this.i = this.i + 1 & 255, this.j = this.j + this.S[this.i] & 255, n = this.S[this.i], this.S[this.i] = this.S[this.j], this.S[this.j] = n, this.S[n + this.S[this.i] & 255]
}

function prng_newstate() {
  return new Arcfour
}

function rng_seed_int(n) {
  rng_pool[rng_pptr++] ^= n & 255
  rng_pool[rng_pptr++] ^= n >> 8 & 255
  rng_pool[rng_pptr++] ^= n >> 16 & 255
  rng_pool[rng_pptr++] ^= n >> 24 & 255
  rng_pptr >= rng_psize && (rng_pptr -= rng_psize)
}

function rng_seed_time() {
  rng_seed_int((new Date).getTime())
}

function rng_get_byte() {
  if (rng_state == null) {
    for (rng_seed_time(), rng_state = prng_newstate(), rng_state.init(rng_pool), rng_pptr = 0; rng_pptr < rng_pool.length; ++rng_pptr) rng_pool[rng_pptr] = 0
    rng_pptr = 0
  }
  return rng_state.next()
}

function rng_get_bytes(n) {
  for (var t = 0; t < n.length; ++t) n[t] = rng_get_byte()
}

function SecureRandom() {
}

function parseBigInt(n, t) {
  return new BigInteger(n, t)
}

function linebrk(n, t) {
  for (var r = "", i = 0; i + t < n.length;) r += n.substring(i, i + t) + "\n", i += t
  return r + n.substring(i, n.length)
}

function byte2Hex(n) {
  return n < 16 ? "0" + n.toString(16) : n.toString(16)
}

function pkcs1pad2(n, t) {
  var i, f, r, e, u
  if (t < n.length + 11) return null
  for (i = [], f = n.length - 1; f >= 0 && t > 0;) r = n.charCodeAt(f--), r < 128 ? i[--t] = r : r > 127 && r < 2048 ? (i[--t] = r & 63 | 128, i[--t] = r >> 6 | 192) : (i[--t] = r & 63 | 128, i[--t] = r >> 6 & 63 | 128, i[--t] = r >> 12 | 224)
  for (i[--t] = 0, e = new SecureRandom, u = []; t > 2;) {
    for (u[0] = 0; u[0] == 0;) e.nextBytes(u)
    i[--t] = u[0]
  }
  return i[--t] = 2, i[--t] = 0, new BigInteger(i)
}

function RSAKey() {
  this.n = null
  this.e = 0
  this.d = null
  this.p = null
  this.q = null
  this.dmp1 = null
  this.dmq1 = null
  this.coeff = null
}

function RSASetPublic(n, t) {
  n != null && t != null && n.length > 0 && t.length > 0 && (this.n = parseBigInt(n, 16), this.e = parseInt(t, 16))
}

function RSADoPublic(n) {
  return n.modPowInt(this.e, this.n)
}

function RSAEncrypt(n) {
  var r = pkcs1pad2(n, this.n.bitLength() + 7 >> 3), i, t
  return r == null ? null : (i = this.doPublic(r), i == null) ? null : (t = i.toString(16), (t.length & 1) == 0 ? t : "0" + t)
}

function hex2b64(n) {
  for (var i, r = "", t = 0; t + 3 <= n.length; t += 3) i = parseInt(n.substring(t, t + 3), 16), r += b64map.charAt(i >> 6) + b64map.charAt(i & 63)
  for (t + 1 == n.length ? (i = parseInt(n.substring(t, t + 1), 16), r += b64map.charAt(i << 2)) : t + 2 == n.length && (i = parseInt(n.substring(t, t + 2), 16), r += b64map.charAt(i >> 2) + b64map.charAt((i & 3) << 4)); (r.length & 3) > 0;) r += b64padchar
  return r
}

function b64tohex(n) {
  for (var t = "", i = 0, r, u = 0; u < n.length; ++u) {
    if (n.charAt(u) == b64padchar) break
    (v = b64map.indexOf(n.charAt(u)), v < 0) || (i == 0 ? (t += int2char(v >> 2), r = v & 3, i = 1) : i == 1 ? (t += int2char(r << 2 | v >> 4), r = v & 15, i = 2) : i == 2 ? (t += int2char(r), t += int2char(v >> 2), r = v & 3, i = 3) : (t += int2char(r << 2 | v >> 4), t += int2char(v & 15), i = 0))
  }
  return i == 1 && (t += int2char(r << 2)), t
}

function b64toBA(n) {
  for (var i = b64tohex(n), r = [], t = 0; 2 * t < i.length; ++t) r[t] = parseInt(i.substring(2 * t, 2 * t + 2), 16)
  return r
}

var dbits, canary = 0xdeadbeefcafe, j_lm = (canary & 16777215) == 15715070, BI_FP, BI_RM, BI_RC, rr, vv, rng_psize,
  rng_state, rng_pool, rng_pptr, t, ua, z, b64map, b64padchar
for (j_lm && navigator.appName == "Microsoft Internet Explorer" ? (BigInteger.prototype.am = am2, dbits = 30) : j_lm && navigator.appName != "Netscape" ? (BigInteger.prototype.am = am1, dbits = 26) : (BigInteger.prototype.am = am3, dbits = 28), BigInteger.prototype.DB = dbits, BigInteger.prototype.DM = (1 << dbits) - 1, BigInteger.prototype.DV = 1 << dbits, BI_FP = 52, BigInteger.prototype.FV = Math.pow(2, BI_FP), BigInteger.prototype.F1 = BI_FP - dbits, BigInteger.prototype.F2 = 2 * dbits - BI_FP, BI_RM = "0123456789abcdefghijklmnopqrstuvwxyz", BI_RC = [], rr = "0".charCodeAt(0), vv = 0; vv <= 9; ++vv) BI_RC[rr++] = vv
for (rr = "a".charCodeAt(0), vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv
for (rr = "A".charCodeAt(0), vv = 10; vv < 36; ++vv) BI_RC[rr++] = vv
if (Classic.prototype.convert = cConvert, Classic.prototype.revert = cRevert, Classic.prototype.reduce = cReduce, Classic.prototype.mulTo = cMulTo, Classic.prototype.sqrTo = cSqrTo, Montgomery.prototype.convert = montConvert, Montgomery.prototype.revert = montRevert, Montgomery.prototype.reduce = montReduce, Montgomery.prototype.mulTo = montMulTo, Montgomery.prototype.sqrTo = montSqrTo, BigInteger.prototype.copyTo = bnpCopyTo, BigInteger.prototype.fromInt = bnpFromInt, BigInteger.prototype.fromString = bnpFromString, BigInteger.prototype.clamp = bnpClamp, BigInteger.prototype.dlShiftTo = bnpDLShiftTo, BigInteger.prototype.drShiftTo = bnpDRShiftTo, BigInteger.prototype.lShiftTo = bnpLShiftTo, BigInteger.prototype.rShiftTo = bnpRShiftTo, BigInteger.prototype.subTo = bnpSubTo, BigInteger.prototype.multiplyTo = bnpMultiplyTo, BigInteger.prototype.squareTo = bnpSquareTo, BigInteger.prototype.divRemTo = bnpDivRemTo, BigInteger.prototype.invDigit = bnpInvDigit, BigInteger.prototype.isEven = bnpIsEven, BigInteger.prototype.exp = bnpExp, BigInteger.prototype.toString = bnToString, BigInteger.prototype.negate = bnNegate, BigInteger.prototype.abs = bnAbs, BigInteger.prototype.compareTo = bnCompareTo, BigInteger.prototype.bitLength = bnBitLength, BigInteger.prototype.mod = bnMod, BigInteger.prototype.modPowInt = bnModPowInt, BigInteger.ZERO = nbv(0), BigInteger.ONE = nbv(1), Arcfour.prototype.init = ARC4init, Arcfour.prototype.next = ARC4next, rng_psize = 256, rng_pool == null) {
  // TODO fills ua with 32 random [0;255] ints
  if (rng_pool = [], rng_pptr = 0, window.crypto && window.crypto.getRandomValues) for (ua = new Uint8Array(32), window.crypto.getRandomValues(ua), t = 0; t < 32; ++t) rng_pool[rng_pptr++] = ua[t]
  // old version of browser, not supported now
  if (navigator.appName == "Netscape" && navigator.appVersion < "5" && window.crypto) for (z = window.crypto.random(32), t = 0; t < z.length; ++t) rng_pool[rng_pptr++] = z.charCodeAt(t) & 255
  while (rng_pptr < rng_psize) t = Math.floor(65536 * Math.random()), rng_pool[rng_pptr++] = t >>> 8, rng_pool[rng_pptr++] = t & 255
  rng_pptr = 0
  rng_seed_time()
}

SecureRandom.prototype.nextBytes = rng_get_bytes
RSAKey.prototype.doPublic = RSADoPublic
RSAKey.prototype.setPublic = RSASetPublic
RSAKey.prototype.encrypt = RSAEncrypt
b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
b64padchar = "="

  
  // TODO MAIN PASSWORD GENERATOR
  function n(n, t, i, r, u) {
    if (n && t && i && r && u) {
      document.rsa.setPublic(t, i)
      var f = JSON.stringify({a: r, u: u, p: n})
      return document.rsa.encrypt(f)
    }
    return null
  }
  
  // generic validation
  function i() {
     return true
    // var n = !1
    // return r(), $("#N").val() || $("#E").val() || ($("#genericValidationError").removeClass("hidden"), n = !0), $("#Username").val() || ($("#genericValidationError").removeClass("hidden"), $("#Username").parent().addClass("error"), n = !0), $("#Password").val() ? $("#Password").val().length < 5 && ($("#wrongCredentialsValidationError").removeClass("hidden"), n = !0) : ($("#genericValidationError").removeClass("hidden"), $("#Password").parent().addClass("error"), n = !0), t(), n
  }
  
  function f() {
    return true
    // var n = !1
    // return r(), $("#PinDigitsAsked").val() || ($("#genericValidationError").removeClass("hidden"), n = !0), $("#N").val() || $("#E").val() || ($("#genericValidationError").removeClass("hidden"), n = !0), !$("#CardNumber").val() || $("#CardNumber").val().length < 14 ? ($("#genericValidationError").removeClass("hidden"), $("#CardNumber").parent().addClass("error"), n = !0) : $("#CardNumber").parent().removeClass("error"), ($("#DayOfBirth").val() === "" || $("#MonthOfBirth").val() === "" || $("#YearOfBirth").val() === "") && ($("#genericValidationError").removeClass("hidden"), $("#DayOfBirth").val() === "" ? $("#DayOfBirth").addClass("emptyDigitError") : $("#DayOfBirth").removeClass("emptyDigitError"), $("#MonthOfBirth").val() === "" ? $("#MonthOfBirth").addClass("emptyDigitError") : $("#MonthOfBirth").removeClass("emptyDigitError"), $("#YearOfBirth").val() === "" ? $("#YearOfBirth").addClass("emptyDigitError") : $("#YearOfBirth").removeClass("emptyDigitError"), n = !0), ($("#PinDigit0").val() === "" || $("#PinDigit1").val() === "" || $("#PinDigit2").val() === "" || $("#PinDigit3").val() === "") && ($("#genericValidationError").removeClass("hidden"), $("#PinDigit0").val() === "" ? $("#PinDigit0").addClass("emptyDigitError") : $("#PinDigit0").removeClass("emptyDigitError"), $("#PinDigit1").val() === "" ? $("#PinDigit1").addClass("emptyDigitError") : $("#PinDigit1").removeClass("emptyDigitError"), $("#PinDigit2").val() === "" ? $("#PinDigit2").addClass("emptyDigitError") : $("#PinDigit2").removeClass("emptyDigitError"), $("#PinDigit3").val() === "" ? $("#PinDigit3").addClass("emptyDigitError") : $("#PinDigit3").removeClass("emptyDigitError"), n = !0), $("#Captcha").val() ? $("#Captcha").parent().removeClass("emptyCaptchaError") : ($("#genericValidationError").removeClass("hidden"), $("#Captcha").parent().addClass("emptyCaptchaError"), n = !0), t(), n
  }
  
  function r() {
    // $("#attemptError").addClass("hidden")
    // $("#genericValidationError").addClass("hidden")
    // $("#wrongCredentialsValidationError").addClass("hidden")
    // $("#Username").parent().removeClass("error")
    // $("#Password").parent().removeClass("error")
    // $(".validation-summary-errors.text-danger").addClass("hidden")
  }
  
  function e(n, t) {
    t || (t = window.location.href)
    n = n.replace(/[\[\]]/g, "\\$&")
    var r = new RegExp("[?&]" + n + "(=([^&#]*)|&|#|$)"), i = r.exec(t)
    return i ? i[2] ? decodeURIComponent(i[2].replace(/\+/g, " ")) : "" : null
  }
  
  document.rsa = new RSAKey;
  
  // TODO emulate this
  // submitLogin = function (r, u, f) {
  //   var e
  //   $("#submitButton").attr("disabled", "disabled")
  //
  //   //         <input id="E" name="E" type="hidden" value="010001">
  //   //         <input id="N" name="N" type="hidden" value="DA8553AE975E06679D70CC818877426FA0FC1A111145A3F38AAF86A6FE0239D09C8352C5AEF46DA8E368AFF9B32C36EC07A838304D53083A86CD3EB78FF118238F1495C55915D82E1FAA6EA871DAAC6EB79631E66C832631C0CB27895E952F267BF031709EC9657FD901870AA15C8D6DF7A3DDF3557E8B9C74F0A4713A8C3B7BC9B2566C95B0036104C4592C52167505936DE309D1419A1E9E6B3AC178DE6750E47E63EB282D5F5D0BB4F68C07100ADFE7B10132127F4510EB432A834318ED15B3A7A7360B14573E9DA0DD7CEAA5C41075B552981590A1ED8FCBDD361D18299E61A6036432026AE2B2935778E653957FB5042A6EDEE977BDE607128A69E64965">
  //   //         <input id="A" name="ActivityDateTime" type="hidden" value="2019-07-06T18:13:48Z">
  //   //         <input id="U" name="UniqueIdentifier" type="hidden" value="cff77fce-412d-4fcb-a5bb-2966006e4033">
  //   //         <input id="hiddenPath" name="RedirectTo" type="hidden" />
  //
  //   var o = $("#N").val(),
  //     s = $("#E").val(),
  //     h = $("#A").val(),
  //     c = $("#U").val();
  //   f && (!f || i()) ? i && $("#submitButton").removeAttr("disabled", "disabled")
  //     // TODO e = hidden pass
  //     : (e = n(u, o, s, h, c), e ? ($("#hiddenUser").val(r),
  //       $("#hiddenPass").val(e), $("#hiddenLang").val($("#languageButton").val()),
  //     window.alphaNotify && window.alphaNotify("lin"), $("#loginForm").submit()) : ($("#genericValidationError").removeClass("hidden"), t()))
  // };


/**
 * node alphabank_encrypter.js  "201810SW" "DA8553AE975E06679D70CC818877426FA0FC1A111145A3F38AAF86A6FE0239D09C8352C5AEF46DA8E368AFF9B32C36EC07A838304D53083A86CD3EB78FF118238F1495C55915D82E1FAA6EA871DAAC6EB79631E66C832631C0CB27895E952F267BF031709EC9657FD901870AA15C8D6DF7A3DDF3557E8B9C74F0A4713A8C3B7BC9B2566C95B0036104C4592C52167505936DE309D1419A1E9E6B3AC178DE6750E47E63EB282D5F5D0BB4F68C07100ADFE7B10132127F4510EB432A834318ED15B3A7A7360B14573E9DA0DD7CEAA5C41075B552981590A1ED8FCBDD361D18299E61A6036432026AE2B2935778E653957FB5042A6EDEE977BDE607128A69E64965"  "010001" "2019-07-06T18:13:48Z" "cff77fce-412d-4fcb-a5bb-2966006e4033"
 */
(function () {
  //         <input id="E" name="E" type="hidden" value="010001">
  //         <input id="N" name="N" type="hidden" value="DA8553AE975E06679D70CC818877426FA0FC1A111145A3F38AAF86A6FE0239D09C8352C5AEF46DA8E368AFF9B32C36EC07A838304D53083A86CD3EB78FF118238F1495C55915D82E1FAA6EA871DAAC6EB79631E66C832631C0CB27895E952F267BF031709EC9657FD901870AA15C8D6DF7A3DDF3557E8B9C74F0A4713A8C3B7BC9B2566C95B0036104C4592C52167505936DE309D1419A1E9E6B3AC178DE6750E47E63EB282D5F5D0BB4F68C07100ADFE7B10132127F4510EB432A834318ED15B3A7A7360B14573E9DA0DD7CEAA5C41075B552981590A1ED8FCBDD361D18299E61A6036432026AE2B2935778E653957FB5042A6EDEE977BDE607128A69E64965">
  //         <input id="A" name="ActivityDateTime" type="hidden" value="2019-07-06T18:13:48Z">
  //         <input id="U" name="UniqueIdentifier" type="hidden" value="cff77fce-412d-4fcb-a5bb-2966006e4033">
  var pswd = process.argv[2];
  var N = process.argv[3];
  var E = process.argv[4];
  var A = process.argv[5];
  var U = process.argv[6];
  
  var encrypted = n(pswd, N, E, A, U);
  
  console.log(encrypted);
})();