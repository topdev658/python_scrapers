// from https://banking.eurocajarural.es/3081/3081/scripts.5b0770b36c54d42dc56c.js
function des(i, t, r, e, n, g) {
  var a,
      d,
      s,
      o,
      u,
      b,
      h,
      l,
      f,
      c,
      x,
      y,
      A,
      v,
      w = new Array(16843776, 0, 65536, 16843780, 16842756, 66564, 4, 65536, 1024, 16843776, 16843780, 1024, 16778244, 16842756, 16777216, 4, 1028, 16778240, 16778240, 66560, 66560, 16842752, 16842752, 16778244, 65540, 16777220, 16777220, 65540, 0, 1028, 66564, 16777216, 65536, 16843780, 4, 16842752, 16843776, 16777216, 16777216, 1024, 16842756, 65536, 66560, 16777220, 1024, 4, 16778244, 66564, 16843780, 65540, 16842752, 16778244, 16777220, 1028, 66564, 16843776, 1028, 16778240, 16778240, 0, 65540, 66560, 0, 16842756),
      m = new Array( - 2146402272, - 2147450880, 32768, 1081376, 1048576, 32, - 2146435040, - 2147450848, - 2147483616, - 2146402272, - 2146402304, - 2147483648, - 2147450880, 1048576, 32, - 2146435040, 1081344, 1048608, - 2147450848, 0, - 2147483648, 32768, 1081376, - 2146435072, 1048608, - 2147483616, 0, 1081344, 32800, - 2146402304, - 2146435072, 32800, 0, 1081376, - 2146435040, 1048576, - 2147450848, - 2146435072, - 2146402304, 32768, - 2146435072, - 2147450880, 32, - 2146402272, 1081376, 32, 32768, - 2147483648, 32800, - 2146402304, 1048576, - 2147483616, 1048608, - 2147450848, - 2147483616, 1048608, 1081344, 0, - 2147450880, 32800, - 2147483648, - 2146435040, - 2146402272, 1081344),
      M = new Array(520, 134349312, 0, 134348808, 134218240, 0, 131592, 134218240, 131080, 134217736, 134217736, 131072, 134349320, 131080, 134348800, 520, 134217728, 8, 134349312, 512, 131584, 134348800, 134348808, 131592, 134218248, 131584, 131072, 134218248, 8, 134349320, 512, 134217728, 134349312, 134217728, 131080, 520, 131072, 134349312, 134218240, 0, 512, 131080, 134349320, 134218240, 134217736, 512, 0, 134348808, 134218248, 131072, 134217728, 134349320, 8, 131592, 131584, 134217736, 134348800, 134218248, 520, 134348800, 131592, 8, 134348808, 131584),
      N = new Array(8396801, 8321, 8321, 128, 8396928, 8388737, 8388609, 8193, 0, 8396800, 8396800, 8396929, 129, 0, 8388736, 8388609, 1, 8192, 8388608, 8396801, 128, 8388608, 8193, 8320, 8388737, 1, 8320, 8388736, 8192, 8396928, 8396929, 129, 8388736, 8388609, 8396800, 8396929, 129, 0, 0, 8396800, 8320, 8388736, 8388737, 1, 8396801, 8321, 8321, 128, 8396929, 129, 1, 8192, 8388609, 8193, 8396928, 8388737, 8193, 8320, 8388608, 8396801, 128, 8388608, 8192, 8396928),
      p = new Array(256, 34078976, 34078720, 1107296512, 524288, 256, 1073741824, 34078720, 1074266368, 524288, 33554688, 1074266368, 1107296512, 1107820544, 524544, 1073741824, 33554432, 1074266112, 1074266112, 0, 1073742080, 1107820800, 1107820800, 33554688, 1107820544, 1073742080, 0, 1107296256, 34078976, 33554432, 1107296256, 524544, 524288, 1107296512, 256, 33554432, 1073741824, 34078720, 1107296512, 1074266368, 33554688, 1073741824, 1107820544, 34078976, 1074266368, 256, 33554432, 1107820544, 1107820800, 524544, 1107296256, 1107820800, 34078720, 0, 1074266112, 1107296256, 524544, 33554688, 1073742080, 524288, 0, 1074266112, 34078976, 1073742080),
      C = new Array(536870928, 541065216, 16384, 541081616, 541065216, 16, 541081616, 4194304, 536887296, 4210704, 4194304, 536870928, 4194320, 536887296, 536870912, 16400, 0, 4194320, 536887312, 16384, 4210688, 536887312, 16, 541065232, 541065232, 0, 4210704, 541081600, 16400, 4210688, 541081600, 536870912, 536887296, 16, 541065232, 4210688, 541081616, 4194304, 16400, 536870928, 4194304, 536887296, 536870912, 16400, 536870928, 541081616, 4210688, 541065216, 4210704, 541081600, 0, 541065232, 16, 16384, 541065216, 4210704, 16384, 4194320, 536887312, 0, 541081600, 536870912, 4194320, 536887312),
      R = new Array(2097152, 69206018, 67110914, 0, 2048, 67110914, 2099202, 69208064, 69208066, 2097152, 0, 67108866, 2, 67108864, 69206018, 2050, 67110912, 2099202, 2097154, 67110912, 67108866, 69206016, 69208064, 2097154, 69206016, 2048, 2050, 69208066, 2099200, 2, 67108864, 2099200, 67108864, 2099200, 2097152, 67110914, 67110914, 69206018, 69206018, 2, 2097154, 67108864, 67110912, 2097152, 69208064, 2050, 2099202, 69208064, 2050, 67108866, 69208066, 69206016, 2099200, 0, 2, 69208066, 0, 2099202, 69206016, 2048, 67108866, 67110912, 2048, 2097154),
      B = new Array(268439616, 4096, 262144, 268701760, 268435456, 268439616, 64, 268435456, 262208, 268697600, 268701760, 266240, 268701696, 266304, 4096, 64, 268697600, 268435520, 268439552, 4160, 266240, 262208, 268697664, 268701696, 4160, 0, 0, 268697664, 268435520, 268439552, 266304, 262144, 266304, 262144, 268701696, 4096, 64, 268697664, 4096, 266304, 268439552, 64, 268435520, 268697600, 268697664, 268435456, 262144, 268439616, 0, 268701760, 262208, 268435520, 268697600, 268439552, 268439616, 0, 268701760, 266240, 266240, 4160, 4160, 262208, 268435456, 268701696),
      D = des_createKeys(hexToString(i)),
      S = 0,
      I = t.length,
      H = 0,
      P = 32 == D.length ? 3 : 9;
  l = 3 == P ? r ? new Array(0, 32, 2) : new Array(30, - 2, - 2) : r ? new Array(0, 32, 2, 62, 30, - 2, 64, 96, 2) : new Array(94, 62, - 2, 32, 64, 2, 30, - 2, - 2),
      2 == g ? t += '        ' : 1 == g ? (s = 8 - I % 8, t += String.fromCharCode(s, s, s, s, s, s, s, s), 8 == s && (I += 8)) : 3 == g && (t += '\x00\x00\x00\x00\x00\x00\x00\x00');
  var T = '',
      k = '';
  for (1 == e && (f = n.charCodeAt(S++) << 24 | n.charCodeAt(S++) << 16 | n.charCodeAt(S++) << 8 | n.charCodeAt(S++), x = n.charCodeAt(S++) << 24 | n.charCodeAt(S++) << 16 | n.charCodeAt(S++) << 8 | n.charCodeAt(S++), S = 0); S < I; ) {
    for (b = t.charCodeAt(S++) << 24 | t.charCodeAt(S++) << 16 | t.charCodeAt(S++) << 8 | t.charCodeAt(S++), h = t.charCodeAt(S++) << 24 | t.charCodeAt(S++) << 16 | t.charCodeAt(S++) << 8 | t.charCodeAt(S++), 1 == e && (r ? (b ^= f, h ^= x) : (c = f, y = x, f = b, x = h)), b ^= (s = 252645135 & (b >>> 4 ^ h)) << 4, b ^= (s = 65535 & (b >>> 16 ^ (h ^= s))) << 16, b ^= s = 858993459 & ((h ^= s) >>> 2 ^ b), b ^= s = 16711935 & ((h ^= s << 2) >>> 8 ^ b), b = (b ^= (s = 1431655765 & (b >>> 1 ^ (h ^= s << 8))) << 1) << 1 | b >>> 31, h = (h ^= s) << 1 | h >>> 31, d = 0; d < P; d += 3) {
      for (A = l[d + 1], v = l[d + 2], a = l[d]; a != A; ) s = b,
          b = h,
          h = s ^ (m[(o = h ^ D[a]) >>> 24 & 63] | N[o >>> 16 & 63] | C[o >>> 8 & 63] | B[63 & o] | w[(u = (h >>> 4 | h << 28) ^ D[a + 1]) >>> 24 & 63] | M[u >>> 16 & 63] | p[u >>> 8 & 63] | R[63 & u]),
          a += v;
      s = b,
          b = h,
          h = s
    }
    h = h >>> 1 | h << 31,
        h ^= s = 1431655765 & ((b = b >>> 1 | b << 31) >>> 1 ^ h),
        h ^= (s = 16711935 & (h >>> 8 ^ (b ^= s << 1))) << 8,
        h ^= (s = 858993459 & (h >>> 2 ^ (b ^= s))) << 2,
        h ^= s = 65535 & ((b ^= s) >>> 16 ^ h),
        h ^= s = 252645135 & ((b ^= s << 16) >>> 4 ^ h),
        b ^= s << 4,
    1 == e && (r ? (f = b, x = h) : (b ^= c, h ^= y)),
        k += String.fromCharCode(b >>> 24, b >>> 16 & 255, b >>> 8 & 255, 255 & b, h >>> 24, h >>> 16 & 255, h >>> 8 & 255, 255 & h),
    512 == (H += 8) && (T += k, k = '', H = 0)
  }
  return T + k
}
function des_createKeys(i) {
  for (var t, r, e, n, g, a = new Array(0, 4, 536870912, 536870916, 65536, 65540, 536936448, 536936452, 512, 516, 536871424, 536871428, 66048, 66052, 536936960, 536936964), d = new Array(0, 1, 1048576, 1048577, 67108864, 67108865, 68157440, 68157441, 256, 257, 1048832, 1048833, 67109120, 67109121, 68157696, 68157697), s = new Array(0, 8, 2048, 2056, 16777216, 16777224, 16779264, 16779272, 0, 8, 2048, 2056, 16777216, 16777224, 16779264, 16779272), o = new Array(0, 2097152, 134217728, 136314880, 8192, 2105344, 134225920, 136323072, 131072, 2228224, 134348800, 136445952, 139264, 2236416, 134356992, 136454144), u = new Array(0, 262144, 16, 262160, 0, 262144, 16, 262160, 4096, 266240, 4112, 266256, 4096, 266240, 4112, 266256), b = new Array(0, 1024, 32, 1056, 0, 1024, 32, 1056, 33554432, 33555456, 33554464, 33555488, 33554432, 33555456, 33554464, 33555488), h = new Array(0, 268435456, 524288, 268959744, 2, 268435458, 524290, 268959746, 0, 268435456, 524288, 268959744, 2, 268435458, 524290, 268959746), l = new Array(0, 65536, 2048, 67584, 536870912, 536936448, 536872960, 536938496, 131072, 196608, 133120, 198656, 537001984, 537067520, 537004032, 537069568), f = new Array(0, 262144, 0, 262144, 2, 262146, 2, 262146, 33554432, 33816576, 33554432, 33816576, 33554434, 33816578, 33554434, 33816578), c = new Array(0, 268435456, 8, 268435464, 0, 268435456, 8, 268435464, 1024, 268436480, 1032, 268436488, 1024, 268436480, 1032, 268436488), x = new Array(0, 32, 0, 32, 1048576, 1048608, 1048576, 1048608, 8192, 8224, 8192, 8224, 1056768, 1056800, 1056768, 1056800), y = new Array(0, 16777216, 512, 16777728, 2097152, 18874368, 2097664, 18874880, 67108864, 83886080, 67109376, 83886592, 69206016, 85983232, 69206528, 85983744), A = new Array(0, 4096, 134217728, 134221824, 524288, 528384, 134742016, 134746112, 16, 4112, 134217744, 134221840, 524304, 528400, 134742032, 134746128), v = new Array(0, 4, 256, 260, 0, 4, 256, 260, 1, 5, 257, 261, 1, 5, 257, 261), w = i.length > 8 ? 3 : 1, m = new Array(32 * w), M = new Array(0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0), N = 0, p = 0, C = 0; C < w; C++) {
    n = i.charCodeAt(N++) << 24 | i.charCodeAt(N++) << 16 | i.charCodeAt(N++) << 8 | i.charCodeAt(N++),
        n ^= (e = 252645135 & (n >>> 4 ^ (g = i.charCodeAt(N++) << 24 | i.charCodeAt(N++) << 16 | i.charCodeAt(N++) << 8 | i.charCodeAt(N++)))) << 4,
        n ^= e = 65535 & ((g ^= e) >>> - 16 ^ n),
        n ^= (e = 858993459 & (n >>> 2 ^ (g ^= e << - 16))) << 2,
        n ^= e = 65535 & ((g ^= e) >>> - 16 ^ n),
        n ^= (e = 1431655765 & (n >>> 1 ^ (g ^= e << - 16))) << 1,
        n ^= e = 16711935 & ((g ^= e) >>> 8 ^ n),
        e = (n ^= (e = 1431655765 & (n >>> 1 ^ (g ^= e << 8))) << 1) << 8 | (g ^= e) >>> 20 & 240,
        n = g << 24 | g << 8 & 16711680 | g >>> 8 & 65280 | g >>> 24 & 240,
        g = e;
    for (var R = 0; R < M.length; R++) M[R] ? (n = n << 2 | n >>> 26, g = g << 2 | g >>> 26) : (n = n << 1 | n >>> 27, g = g << 1 | g >>> 27),
        m[p++] = (t = a[(n &= - 15) >>> 28] | d[n >>> 24 & 15] | s[n >>> 20 & 15] | o[n >>> 16 & 15] | u[n >>> 12 & 15] | b[n >>> 8 & 15] | h[n >>> 4 & 15]) ^ (e = 65535 & ((r = l[(g &= - 15) >>> 28] | f[g >>> 24 & 15] | c[g >>> 20 & 15] | x[g >>> 16 & 15] | y[g >>> 12 & 15] | A[g >>> 8 & 15] | v[g >>> 4 & 15]) >>> 16 ^ t)),
        m[p++] = r ^ e << 16
  }
  return m
}
function hexToString(i) {
  for (var t = '', r = '0x' == i.substr(0, 2) ? 2 : 0; r < i.length; r += 2) t += String.fromCharCode(parseInt(i.substr(r, 2), 16));
  return t
}
function stringToHex(i) {
  for (var t = '', r = new Array('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'), e = 0; e < i.length; e++) t += r[i.charCodeAt(e) >> 4] + r[15 & i.charCodeAt(e)];
  return t
}
function MOD(i, t) {
  return stringToHex(des(i, t, 1, 1, '\x00\x00\x00\x00\x00\x00\x00\x00', 1))
}
function MOD_ECB(i, t) {
  return stringToHex(des(i, t, 1, 0))
}
var maxDigits,
    ZERO_ARRAY,
    bigZero,
    bigOne,
    biRadixBase = 2,
    biRadixBits = 16,
    bitsPerDigit = biRadixBits,
    biRadix = 65536,
    biHalfRadix = biRadix >>> 1,
    biRadixSquared = biRadix * biRadix,
    maxDigitVal = biRadix - 1,
    maxInteger = 9999999999999998;
function setMaxDigits(i) {
  ZERO_ARRAY = new Array(maxDigits = i);
  for (var t = 0; t < ZERO_ARRAY.length; t++) ZERO_ARRAY[t] = 0;
  bigZero = new BigInt,
      (bigOne = new BigInt).digits[0] = 1
}
setMaxDigits(20);
var dpl10 = 15,
    lr10 = biFromNumber(1000000000000000);
function BigInt(i) {
  this.digits = 'boolean' == typeof i && 1 == i ? null : ZERO_ARRAY.slice(0),
      this.isNeg = !1
}
function biFromDecimal(i) {
  for (var t, r = '-' == i.charAt(0), e = r ? 1 : 0; e < i.length && '0' == i.charAt(e); ) ++e;
  if (e == i.length) t = new BigInt;
  else {
    var n = (i.length - e) % dpl10;
    for (0 == n && (n = dpl10), t = biFromNumber(Number(i.substr(e, n))), e += n; e < i.length; ) t = biAdd(biMultiply(t, lr10), biFromNumber(Number(i.substr(e, dpl10)))),
        e += dpl10;
    t.isNeg = r
  }
  return t
}
function biCopy(i) {
  var t = new BigInt(!0);
  return t.digits = i.digits.slice(0),
      t.isNeg = i.isNeg,
      t
}
function biFromNumber(i) {
  var t = new BigInt;
  t.isNeg = i < 0,
      i = Math.abs(i);
  for (var r = 0; i > 0; ) t.digits[r++] = i & maxDigitVal,
      i = Math.floor(i / biRadix);
  return t
}
function reverseStr(i) {
  for (var t = '', r = i.length - 1; r > - 1; --r) t += i.charAt(r);
  return t
}
var hexatrigesimalToChar = new Array('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z');
function biToString(i, t) {
  var r = new BigInt;
  r.digits[0] = t;
  for (var e = biDivideModulo(i, r), n = hexatrigesimalToChar[e[1].digits[0]]; 1 == biCompare(e[0], bigZero); ) e = biDivideModulo(e[0], r),
      digit = e[1].digits[0],
      n += hexatrigesimalToChar[e[1].digits[0]];
  return (i.isNeg ? '-' : '') + reverseStr(n)
}
function biToDecimal(i) {
  var t = new BigInt;
  t.digits[0] = 10;
  for (var r = biDivideModulo(i, t), e = String(r[1].digits[0]); 1 == biCompare(r[0], bigZero); ) r = biDivideModulo(r[0], t),
      e += String(r[1].digits[0]);
  return (i.isNeg ? '-' : '') + reverseStr(e)
}
var hexToChar = new Array('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f');
function digitToHex(t) {
  var r = '';
  for (i = 0; i < 4; ++i) r += hexToChar[15 & t],
      t >>>= 4;
  return reverseStr(r)
}
function biToHex(i) {
  for (var t = '', r = (biHighIndex(i), biHighIndex(i)); r > - 1; --r) t += digitToHex(i.digits[r]);
  return t
}
function charToHex(i) {
  return i >= 48 && i <= 57 ? i - 48 : i >= 65 && i <= 90 ? 10 + i - 65 : i >= 97 && i <= 122 ? 10 + i - 97 : 0
}
function hexToDigit(i) {
  for (var t = 0, r = Math.min(i.length, 4), e = 0; e < r; ++e) t <<= 4,
      t |= charToHex(i.charCodeAt(e));
  return t
}
function biFromHex(i) {
  for (var t = new BigInt, r = i.length, e = 0; r > 0; r -= 4, ++e) t.digits[e] = hexToDigit(i.substr(Math.max(r - 4, 0), Math.min(r, 4)));
  return t
}
function biFromString(i, t) {
  var r = '-' == i.charAt(0),
      e = r ? 1 : 0,
      n = new BigInt,
      g = new BigInt;
  g.digits[0] = 1;
  for (var a = i.length - 1; a >= e; a--) n = biAdd(n, biMultiplyDigit(g, charToHex(i.charCodeAt(a)))),
      g = biMultiplyDigit(g, t);
  return n.isNeg = r,
      n
}
function biDump(i) {
  return (i.isNeg ? '-' : '') + i.digits.join(' ')
}
function biAdd(i, t) {
  var r;
  if (i.isNeg != t.isNeg) t.isNeg = !t.isNeg,
      r = biSubtract(i, t),
      t.isNeg = !t.isNeg;
  else {
    r = new BigInt;
    for (var e, n = 0, g = 0; g < i.digits.length; ++g) r.digits[g] = (e = i.digits[g] + t.digits[g] + n) % biRadix,
        n = Number(e >= biRadix);
    r.isNeg = i.isNeg
  }
  return r
}
function biSubtract(i, t) {
  var r;
  if (i.isNeg != t.isNeg) t.isNeg = !t.isNeg,
      r = biAdd(i, t),
      t.isNeg = !t.isNeg;
  else {
    var e,
        n;
    r = new BigInt,
        n = 0;
    for (var g = 0; g < i.digits.length; ++g) r.digits[g] = (e = i.digits[g] - t.digits[g] + n) % biRadix,
    r.digits[g] < 0 && (r.digits[g] += biRadix),
        n = 0 - Number(e < 0);
    if ( - 1 == n) {
      for (n = 0, g = 0; g < i.digits.length; ++g) r.digits[g] = (e = 0 - r.digits[g] + n) % biRadix,
      r.digits[g] < 0 && (r.digits[g] += biRadix),
          n = 0 - Number(e < 0);
      r.isNeg = !i.isNeg
    } else r.isNeg = i.isNeg
  }
  return r
}
function biHighIndex(i) {
  for (var t = i.digits.length - 1; t > 0 && 0 == i.digits[t]; ) --t;
  return t
}
function biNumBits(i) {
  var t,
      r = biHighIndex(i),
      e = i.digits[r],
      n = (r + 1) * bitsPerDigit;
  for (t = n; t > n - bitsPerDigit && 0 == (32768 & e); --t) e <<= 1;
  return t
}
function biMultiply(i, t) {
  for (var r, e, n, g = new BigInt, a = biHighIndex(i), d = biHighIndex(t), s = 0; s <= d; ++s) {
    for (r = 0, n = s, j = 0; j <= a; ++j, ++n) e = g.digits[n] + i.digits[j] * t.digits[s] + r,
        g.digits[n] = e & maxDigitVal,
        r = e >>> biRadixBits;
    g.digits[s + a + 1] = r
  }
  return g.isNeg = i.isNeg != t.isNeg,
      g
}
function biMultiplyDigit(i, t) {
  var r,
      e,
      n;
  result = new BigInt,
      r = biHighIndex(i),
      e = 0;
  for (var g = 0; g <= r; ++g) n = result.digits[g] + i.digits[g] * t + e,
      result.digits[g] = n & maxDigitVal,
      e = n >>> biRadixBits;
  return result.digits[1 + r] = e,
      result
}
function arrayCopy(i, t, r, e, n) {
  for (var g = Math.min(t + n, i.length), a = t, d = e; a < g; ++a, ++d) r[d] = i[a]
}
var highBitMasks = new Array(0, 32768, 49152, 57344, 61440, 63488, 64512, 65024, 65280, 65408, 65472, 65504, 65520, 65528, 65532, 65534, 65535);
function biShiftLeft(i, t) {
  var r = Math.floor(t / bitsPerDigit),
      e = new BigInt;
  arrayCopy(i.digits, 0, e.digits, r, e.digits.length - r);
  for (var n = t % bitsPerDigit, g = bitsPerDigit - n, a = e.digits.length - 1, d = a - 1; a > 0; --a, --d) e.digits[a] = e.digits[a] << n & maxDigitVal | (e.digits[d] & highBitMasks[n]) >>> g;
  return e.digits[0] = e.digits[a] << n & maxDigitVal,
      e.isNeg = i.isNeg,
      e
}
var lowBitMasks = new Array(0, 1, 3, 7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383, 32767, 65535);
function biShiftRight(i, t) {
  var r = Math.floor(t / bitsPerDigit),
      e = new BigInt;
  arrayCopy(i.digits, r, e.digits, 0, i.digits.length - r);
  for (var n = t % bitsPerDigit, g = bitsPerDigit - n, a = 0, d = a + 1; a < e.digits.length - 1; ++a, ++d) e.digits[a] = e.digits[a] >>> n | (e.digits[d] & lowBitMasks[n]) << g;
  return e.digits[e.digits.length - 1] >>>= n,
      e.isNeg = i.isNeg,
      e
}
function biMultiplyByRadixPower(i, t) {
  var r = new BigInt;
  return arrayCopy(i.digits, 0, r.digits, t, r.digits.length - t),
      r
}
function biDivideByRadixPower(i, t) {
  var r = new BigInt;
  return arrayCopy(i.digits, t, r.digits, 0, r.digits.length - t),
      r
}
function biModuloByRadixPower(i, t) {
  var r = new BigInt;
  return arrayCopy(i.digits, 0, r.digits, 0, t),
      r
}
function biCompare(i, t) {
  if (i.isNeg != t.isNeg) return 1 - 2 * Number(i.isNeg);
  for (var r = i.digits.length - 1; r >= 0; --r) if (i.digits[r] != t.digits[r]) return i.isNeg ? 1 - 2 * Number(i.digits[r] > t.digits[r]) : 1 - 2 * Number(i.digits[r] < t.digits[r]);
  return 0
}
function biDivideModulo(i, t) {
  var r,
      e,
      n = biNumBits(i),
      g = biNumBits(t),
      a = t.isNeg;
  if (n < g) return i.isNeg ? ((r = biCopy(bigOne)).isNeg = !t.isNeg, i.isNeg = !1, t.isNeg = !1, e = biSubtract(t, i), i.isNeg = !0, t.isNeg = a) : (r = new BigInt, e = biCopy(i)),
      new Array(r, e);
  r = new BigInt,
      e = i;
  for (var d = Math.ceil(g / bitsPerDigit) - 1, s = 0; t.digits[d] < biHalfRadix; ) t = biShiftLeft(t, 1),
      ++s,
      ++g,
      d = Math.ceil(g / bitsPerDigit) - 1;
  e = biShiftLeft(e, s),
      n += s;
  for (var o = Math.ceil(n / bitsPerDigit) - 1, u = biMultiplyByRadixPower(t, o - d); - 1 != biCompare(e, u); ) ++r.digits[o - d],
      e = biSubtract(e, u);
  for (var b = o; b > d; --b) {
    var h = b >= e.digits.length ? 0 : e.digits[b],
        l = b - 1 >= e.digits.length ? 0 : e.digits[b - 1],
        f = b - 2 >= e.digits.length ? 0 : e.digits[b - 2],
        c = d >= t.digits.length ? 0 : t.digits[d],
        x = d - 1 >= t.digits.length ? 0 : t.digits[d - 1];
    r.digits[b - d - 1] = h == c ? maxDigitVal : Math.floor((h * biRadix + l) / c);
    for (var y = r.digits[b - d - 1] * (c * biRadix + x), A = h * biRadixSquared + (l * biRadix + f); y > A; ) --r.digits[b - d - 1],
        y = r.digits[b - d - 1] * (c * biRadix | x),
        A = h * biRadix * biRadix + (l * biRadix + f);
    (e = biSubtract(e, biMultiplyDigit(u = biMultiplyByRadixPower(t, b - d - 1), r.digits[b - d - 1]))).isNeg && (e = biAdd(e, u), --r.digits[b - d - 1])
  }
  return e = biShiftRight(e, s),
      r.isNeg = i.isNeg != a,
  i.isNeg && (r = a ? biAdd(r, bigOne) : biSubtract(r, bigOne), e = biSubtract(t = biShiftRight(t, s), e)),
  0 == e.digits[0] && 0 == biHighIndex(e) && (e.isNeg = !1),
      new Array(r, e)
}
function biDivide(i, t) {
  return biDivideModulo(i, t) [0]
}
function biModulo(i, t) {
  return biDivideModulo(i, t) [1]
}
function biMultiplyMod(i, t, r) {
  return biModulo(biMultiply(i, t), r)
}
function biPow(i, t) {
  for (var r = bigOne, e = i; 0 != (1 & t) && (r = biMultiply(r, e)), 0 != (t >>= 1); ) e = biMultiply(e, e);
  return r
}
function biPowMod(i, t, r) {
  for (var e = bigOne, n = i, g = t; 0 != (1 & g.digits[0]) && (e = biMultiplyMod(e, n, r)), 0 != (g = biShiftRight(g, 1)).digits[0] || 0 != biHighIndex(g); ) n = biMultiplyMod(n, n, r);
  return e
}
function BarrettMu(i) {
  this.modulus = biCopy(i),
      this.k = biHighIndex(this.modulus) + 1;
  var t = new BigInt;
  t.digits[2 * this.k] = 1,
      this.mu = biDivide(t, this.modulus),
      this.bkplus1 = new BigInt,
      this.bkplus1.digits[this.k + 1] = 1,
      this.modulo = BarrettMu_modulo,
      this.multiplyMod = BarrettMu_multiplyMod,
      this.powMod = BarrettMu_powMod
}
function BarrettMu_modulo(i) {
  var t = biDivideByRadixPower(i, this.k - 1),
      r = biDivideByRadixPower(biMultiply(t, this.mu), this.k + 1),
      e = biSubtract(biModuloByRadixPower(i, this.k + 1), biModuloByRadixPower(biMultiply(r, this.modulus), this.k + 1));
  e.isNeg && (e = biAdd(e, this.bkplus1));
  for (var n = biCompare(e, this.modulus) >= 0; n; ) n = biCompare(e = biSubtract(e, this.modulus), this.modulus) >= 0;
  return e
}
function BarrettMu_multiplyMod(i, t) {
  var r = biMultiply(i, t);
  return this.modulo(r)
}
function BarrettMu_powMod(i, t) {
  var r = new BigInt;
  r.digits[0] = 1;
  for (var e = i, n = t; 0 != (1 & n.digits[0]) && (r = this.multiplyMod(r, e)), 0 != (n = biShiftRight(n, 1)).digits[0] || 0 != biHighIndex(n); ) e = this.multiplyMod(e, e);
  return r
}
function RSAKeyPair(i, t, r) {
  this.e = biFromHex(i),
      this.d = biFromHex(t),
      this.m = biFromHex(r),
      this.chunkSize = 2 * biHighIndex(this.m),
      this.radix = 16,
      this.barrett = new BarrettMu(this.m)
}
function twoDigit(i) {
  return (i < 10 ? '0' : '') + String(i)
}
function encryptedString(i, t) {
  for (var r = new Array, e = t.length, n = 0; n < e; ) r[n] = t.charCodeAt(n),
      n++;
  for (; r.length % i.chunkSize != 0; ) r[n++] = 0;
  var g,
      a,
      d,
      s = r.length,
      o = '';
  for (n = 0; n < s; n += i.chunkSize) {
    for (d = new BigInt, g = 0, a = n; a < n + i.chunkSize; ++g) d.digits[g] = r[a++],
        d.digits[g] += r[a++] << 8;
    var u = i.barrett.powMod(d, i.e);
    o += (16 == i.radix ? biToHex(u) : biToString(u, i.radix)) + ' '
  }
  return o.substring(0, o.length - 1)
}
function decryptedString(i, t) {
  var r,
      e,
      n,
      g = t.split(' '),
      a = '';
  for (r = 0; r < g.length; ++r) {
    var d;
    for (d = 16 == i.radix ? biFromHex(g[r]) : biFromString(g[r], i.radix), n = i.barrett.powMod(d, i.d), e = 0; e <= biHighIndex(n); ++e) a += String.fromCharCode(255 & n.digits[e], n.digits[e] >> 8)
  }
  return 0 == a.charCodeAt(a.length - 1) && (a = a.substring(0, a.length - 1)),
      a
}

function MOD(i, t) {
  if ( - 1 != i.indexOf('|') && void 0 !== encryptedString && null != encryptedString) {
    var r = i.split('|');
    return encryptedString(new RSAKeyPair(r[0], r[0], r[1]), t)
  }
  return stringToHex(des(i, t, 1, 1, '\x00\x00\x00\x00\x00\x00\x00\x00', 1))
}


// see https://banking.eurocajarural.es/3081/3081/18.8e11a16878fae991a8ab.js
// n.prototype.conexion = function (n, l, t) {
//   var o = this;
//   if (void 0 === t && (t = !0), this.username = n, this.password = l, '' === this.claveCalcula.trim() || '' === n.trim() || '' === l.trim()) return null;
//   this.password = MOD(this.claveCalcula, this.password); // VB encryption here
//   var e = '' + B.a.urlBEWeb + B.a.actionConexion,
//   a = (new L.i).set('SELLO', this.sello).set('OPERACION', this.operacion).set('BROKER', this.broker).set('PINV3', 'si').set('PIN', this.password);
//   return a = void 0 !== B.a.loginNOUSU && '' !== B.a.loginNOUSU ? a.append('PAN', B.a.loginNOUSU).append('PANENT', this.username) : a.append('PAN', this.username),
//   this.httpClient.post(e, a).pipe(Object(k.a) ((function (n) {
//     return null != n && void 0 !== n.resultado ? 'OK' === n.resultado && t ? o.tratarRespuestaLogin(n) : ('KO' === n.resultado && '0936' === n.codigoerror && (o.idTrans = n.idTrans.trim(), o.tipSeg = n.tipSeg.trim(), o.storeSCA.dispatch({
//       type: q.a.STORE_SCA_UPDATE,
//       payload: {
//         scaSolicitado: !0,
//         idTrans: n.idTrans.trim(),
//         tipSeg: n.tipSeg.trim(),
//         pan: o.username
//       }
//     })), n) : null
//   }), (function (n) {
//     return null
//   })))
// }


/**
 * node eurocajarural_encrypter.js  "010001|00a200c35401a4a19d96a9b968912125ab" "203855"
 * 83ecc45223b7984677518da8fd059e2c
 */
(function () {
  // to call emulated MOD(this.claveCalcula, this.password);
  var clave  = process.argv[2];  // claveCalcula from inicio_identificacion_sello.action
  var userpass =  process.argv[3];
  var encrypted = MOD(clave, userpass);
  console.log(encrypted);
})();

