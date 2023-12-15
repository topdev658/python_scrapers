var biRadixBits = 16,
    bitsPerDigit = biRadixBits,
    biRadix = 65536,
    biHalfRadix = biRadix >>> 1,
    biRadixSquared = biRadix * biRadix,
    maxDigitVal = biRadix - 1,
    maxDigits,
    ZERO_ARRAY,
    bigZero,
    bigOne

function setMaxDigits(a) {
    maxDigits = a
    ZERO_ARRAY = Array(maxDigits)
    for (a = 0; a < ZERO_ARRAY.length; a++) ZERO_ARRAY[a] = 0
    bigZero = new BigInt
    bigOne = new BigInt
    bigOne.digits[0] = 1
}

setMaxDigits(20)
var dpl10 = 15,
    lr10 = biFromNumber(1000000000000000)

function BigInt(a) {
    this.digits = 'boolean' == typeof a && 1 == a ? null : ZERO_ARRAY.slice(0)
    this.isNeg = !1
}

function biCopy(a) {
    var b = new BigInt(!0)
    b.digits = a.digits.slice(0)
    b.isNeg = a.isNeg
    return b
}

function biFromNumber(a) {
    var b = new BigInt
    b.isNeg = 0 > a
    a = Math.abs(a)
    for (var c = 0; 0 < a;) b.digits[c++] = a & maxDigitVal,
        a >>= biRadixBits
    return b
}

function reverseStr(a) {
    for (var b = '', c = a.length - 1; -1 < c; --c) b += a.charAt(c)
    return b
}

var hexatrigesimalToChar = '0123456789abcdefghijklmnopqrstuvwxyz'.split('')

function biToString(a, b) {
    var c = new BigInt
    c.digits[0] = b
    for (var d = biDivideModulo(a, c), e = hexatrigesimalToChar[d[1].digits[0]]; 1 == biCompare(d[0], bigZero);) d = biDivideModulo(d[0], c),
        digit = d[1].digits[0],
        e += hexatrigesimalToChar[d[1].digits[0]]
    return (a.isNeg ? '-' : '') + reverseStr(e)
}

var hexToChar = '0123456789abcdef'.split('')

function digitToHex(a) {
    var b = ''
    for (i = 0; 4 > i; ++i) b += hexToChar[a & 15],
        a >>>= 4
    return reverseStr(b)
}

function biToHex(a) {
    var b = ''
    biHighIndex(a)
    for (var c = biHighIndex(a); -1 < c; --c) b += digitToHex(a.digits[c])
    return b
}

function charToHex(a) {
    return 48 <= a && 57 >= a ? a - 48 : 65 <= a && 90 >= a ? 10 + a - 65 : 97 <= a && 122 >= a ? 10 + a - 97 : 0
}

function hexToDigit(a) {
    for (var b = 0, c = Math.min(a.length, 4), d = 0; d < c; ++d) b <<= 4,
        b |= charToHex(a.charCodeAt(d))
    return b
}

function biFromHex(a) {
    for (var b = new BigInt, c = a.length, d = 0; 0 < c; c -= 4, ++d) b.digits[d] = hexToDigit(a.substr(Math.max(c - 4, 0), Math.min(c, 4)))
    return b
}

function biFromString(a, b) {
    var c = '-' == a.charAt(0),
        d = c ? 1 : 0,
        e = new BigInt,
        g = new BigInt
    g.digits[0] = 1
    for (var f = a.length - 1; f >= d; f--) var h = a.charCodeAt(f),
        h = charToHex(h),
        h = biMultiplyDigit(g, h),
        e = biAdd(e, h),
        g = biMultiplyDigit(g, b)
    e.isNeg = c
    return e
}

function biDump(a) {
    return (a.isNeg ? '-' : '') + a.digits.join(' ')
}

function biAdd(a, b) {
    var c
    if (a.isNeg != b.isNeg) b.isNeg = !b.isNeg,
        c = biSubtract(a, b),
        b.isNeg = !b.isNeg
    else {
        c = new BigInt
        for (var d = 0, e = 0; e < a.digits.length; ++e) d = a.digits[e] + b.digits[e] + d,
            c.digits[e] = d & 65535,
            d = Number(d >= biRadix)
        c.isNeg = a.isNeg
    }
    return c
}

function biSubtract(a, b) {
    var c
    if (a.isNeg != b.isNeg) b.isNeg = !b.isNeg,
        c = biAdd(a, b),
        b.isNeg = !b.isNeg
    else {
        c = new BigInt
        for (var d, e = d = 0; e < a.digits.length; ++e) d = a.digits[e] - b.digits[e] + d,
            c.digits[e] = d & 65535,
        0 > c.digits[e] && (c.digits[e] += biRadix),
            d = 0 - Number(0 > d)
        if (-1 == d) {
            for (e = d = 0; e < a.digits.length; ++e) d = 0 - c.digits[e] + d,
                c.digits[e] = d & 65535,
            0 > c.digits[e] && (c.digits[e] += biRadix),
                d = 0 - Number(0 > d)
            c.isNeg = !a.isNeg
        } else c.isNeg = a.isNeg
    }
    return c
}

function biHighIndex(a) {
    for (var b = a.digits.length - 1; 0 < b && 0 == a.digits[b];) --b
    return b
}

function biNumBits(a) {
    var b = biHighIndex(a)
    a = a.digits[b]
    var b = (b + 1) * bitsPerDigit,
        c
    for (c = b; c > b - bitsPerDigit && 0 == (a & 32768); --c) a <<= 1
    return c
}

function biMultiply(a, b) {
    for (var c = new BigInt, d, e = biHighIndex(a), g = biHighIndex(b), f, h = 0; h <= g; ++h) {
        d = 0
        f = h
        for (j = 0; j <= e; ++j, ++f) d = c.digits[f] + a.digits[j] * b.digits[h] + d,
            c.digits[f] = d & maxDigitVal,
            d >>>= biRadixBits
        c.digits[h + e + 1] = d
    }
    c.isNeg = a.isNeg != b.isNeg
    return c
}

function biMultiplyDigit(a, b) {
    var c,
        d
    result = new BigInt
    c = biHighIndex(a)
    for (var e = d = 0; e <= c; ++e) d = result.digits[e] + a.digits[e] * b + d,
        result.digits[e] = d & maxDigitVal,
        d >>>= biRadixBits
    result.digits[1 + c] = d
    return result
}

function arrayCopy(a, b, c, d, e) {
    for (e = Math.min(b + e, a.length); b < e; ++b, ++d) c[d] = a[b]
}

var highBitMasks = [
    0,
    32768,
    49152,
    57344,
    61440,
    63488,
    64512,
    65024,
    65280,
    65408,
    65472,
    65504,
    65520,
    65528,
    65532,
    65534,
    65535
]

function biShiftLeft(a, b) {
    var c = Math.floor(b / bitsPerDigit),
        d = new BigInt
    arrayCopy(a.digits, 0, d.digits, c, d.digits.length - c)
    for (var c = b % bitsPerDigit, e = bitsPerDigit - c, g = d.digits.length - 1, f = g - 1; 0 < g; --g, --f) d.digits[g] = d.digits[g] << c & maxDigitVal | (d.digits[f] & highBitMasks[c]) >>> e
    d.digits[0] = d.digits[g] << c & maxDigitVal
    d.isNeg = a.isNeg
    return d
}

var lowBitMasks = [
    0,
    1,
    3,
    7,
    15,
    31,
    63,
    127,
    255,
    511,
    1023,
    2047,
    4095,
    8191,
    16383,
    32767,
    65535
]

function biShiftRight(a, b) {
    var c = Math.floor(b / bitsPerDigit),
        d = new BigInt
    arrayCopy(a.digits, c, d.digits, 0, a.digits.length - c)
    for (var c = b % bitsPerDigit, e = bitsPerDigit - c, g = 0, f = g + 1; g < d.digits.length - 1; ++g, ++f) d.digits[g] = d.digits[g] >>> c | (d.digits[f] & lowBitMasks[c]) << e
    d.digits[d.digits.length - 1] >>>= c
    d.isNeg = a.isNeg
    return d
}

function biMultiplyByRadixPower(a, b) {
    var c = new BigInt
    arrayCopy(a.digits, 0, c.digits, b, c.digits.length - b)
    return c
}

function biDivideByRadixPower(a, b) {
    var c = new BigInt
    arrayCopy(a.digits, b, c.digits, 0, c.digits.length - b)
    return c
}

function biModuloByRadixPower(a, b) {
    var c = new BigInt
    arrayCopy(a.digits, 0, c.digits, 0, b)
    return c
}

function biCompare(a, b) {
    if (a.isNeg != b.isNeg) return 1 - 2 * Number(a.isNeg)
    for (var c = a.digits.length - 1; 0 <= c; --c) if (a.digits[c] != b.digits[c]) return a.isNeg ? 1 - 2 * Number(a.digits[c] > b.digits[c]) : 1 - 2 * Number(a.digits[c] < b.digits[c])
    return 0
}

function biDivideModulo(a, b) {
    var c = biNumBits(a),
        d = biNumBits(b),
        e = b.isNeg,
        g,
        f
    if (c < d) return a.isNeg ? (g = biCopy(bigOne), g.isNeg = !b.isNeg, a.isNeg = !1, b.isNeg = !1, f = biSubtract(b, a), a.isNeg = !0, b.isNeg = e) : (g = new BigInt, f = biCopy(a)),
        [
            g,
            f
        ]
    g = new BigInt
    f = a
    for (var h = Math.ceil(d / bitsPerDigit) - 1, k = 0; b.digits[h] < biHalfRadix;) b = biShiftLeft(b, 1),
        ++k,
        ++d,
        h = Math.ceil(d / bitsPerDigit) - 1
    f = biShiftLeft(f, k)
    c = Math.ceil((c + k) / bitsPerDigit) - 1
    for (d = biMultiplyByRadixPower(b, c - h); -1 != biCompare(f, d);) ++g.digits[c - h],
        f = biSubtract(f, d)
    for (; c > h; --c) {
        var d = c >= f.digits.length ? 0 : f.digits[c],
            m = c - 1 >= f.digits.length ? 0 : f.digits[c - 1],
            n = c - 2 >= f.digits.length ? 0 : f.digits[c - 2],
            l = h >= b.digits.length ? 0 : b.digits[h],
            p = h - 1 >= b.digits.length ? 0 : b.digits[h - 1]
        g.digits[c - h - 1] = d == l ? maxDigitVal : Math.floor((d * biRadix + m) / l)
        for (var q = g.digits[c - h - 1] * (l * biRadix + p), r = d * biRadixSquared + (m * biRadix + n); q > r;) --g.digits[c - h - 1],
            q = g.digits[c - h - 1] * (l * biRadix | p),
            r = d * biRadix * biRadix + (m * biRadix + n)
        d = biMultiplyByRadixPower(b, c - h - 1)
        f = biSubtract(f, biMultiplyDigit(d, g.digits[c -
        h - 1]))
        f.isNeg && (f = biAdd(f, d), --g.digits[c - h - 1])
    }
    f = biShiftRight(f, k)
    g.isNeg = a.isNeg != e
    a.isNeg && (g = e ? biAdd(g, bigOne) : biSubtract(g, bigOne), b = biShiftRight(b, k), f = biSubtract(b, f))
    0 == f.digits[0] && 0 == biHighIndex(f) && (f.isNeg = !1)
    return [g,
        f]
}

function biDivide(a, b) {
    return biDivideModulo(a, b) [0]
}

function biModulo(a, b) {
    return biDivideModulo(a, b) [1]
}

function biMultiplyMod(a, b, c) {
    return biModulo(biMultiply(a, b), c)
}

function biPow(a, b) {
    for (var c = bigOne, d = a; ;) {
        0 != (b & 1) && (c = biMultiply(c, d))
        b >>= 1
        if (0 == b) break
        d = biMultiply(d, d)
    }
    return c
}

function biPowMod(a, b, c) {
    for (var d = bigOne; ;) {
        0 != (b.digits[0] & 1) && (d = biMultiplyMod(d, a, c))
        b = biShiftRight(b, 1)
        if (0 == b.digits[0] && 0 == biHighIndex(b)) break
        a = biMultiplyMod(a, a, c)
    }
    return d
}

function KeyPair(a, b, c) {
    this.e = biFromHex(a)
    this.d = biFromHex(b)
    this.m = biFromHex(c)
    this.chunkSize = 2 * biHighIndex(this.m)
    this.radix = 16
    this.barrett = new Crypto(this.m)
}

function Crypto(a) {
    this.modulus = biCopy(a)
    this.k = biHighIndex(this.modulus) + 1
    a = new BigInt
    a.digits[2 * this.k] = 1
    this.mu = biDivide(a, this.modulus)
    this.bkplus1 = new BigInt
    this.bkplus1.digits[this.k + 1] = 1
    this.modulo = Crypto_modulo
    this.multiplyMod = Crypto_multiplyMod
    this.powMod = Crypto_powMod
}

function Crypto_multiplyMod(a, b) {
    var c = biMultiply(a, b)
    return this.modulo(c)
}

function Crypto_powMod(a, b) {
    var c = new BigInt
    c.digits[0] = 1
    for (var d = a, e = b; ;) {
        0 != (e.digits[0] & 1) && (c = this.multiplyMod(c, d))
        e = biShiftRight(e, 1)
        if (0 == e.digits[0] && 0 == biHighIndex(e)) break
        d = this.multiplyMod(d, d)
    }
    return c
}

function Crypto_modulo(a) {
    var b = biDivideByRadixPower(a, this.k - 1),
        b = biMultiply(b, this.mu),
        b = biDivideByRadixPower(b, this.k + 1)
    a = biModuloByRadixPower(a, this.k + 1)
    b = biMultiply(b, this.modulus)
    b = biModuloByRadixPower(b, this.k + 1)
    a = biSubtract(a, b)
    a.isNeg && (a = biAdd(a, this.bkplus1))
    for (b = 0 <= biCompare(a, this.modulus); b;) a = biSubtract(a, this.modulus),
        b = 0 <= biCompare(a, this.modulus)
    return a
}

function encryptedString(a, b) {
    for (var c = [], d = b.length, e = 0; e < d;) c[e] = b.charCodeAt(e),
        e++
    for (; 0 != c.length % a.chunkSize;) c[e++] = 0
    for (var d = c.length, g = '', f, h, k, e = 0; e < d; e += a.chunkSize) {
        k = new BigInt
        f = 0
        for (h = e; h < e + a.chunkSize; ++f) k.digits[f] = c[h++],
            k.digits[f] += c[h++] << 8
        f = a.barrett.powMod(k, a.e)
        f = 16 == a.radix ? biToHex(f) : biToString(f, a.radix)
        g += f + ' '
    }
    return g.substring(0, g.length - 1)
}

function encrypt(a, b, c) {
    setMaxDigits(260)
    a = new KeyPair(b, '', a)
    return encryptedString(a, c + ':' + (new Date).getTime())
}

/**
 * node societegenerale_encrypter.js "c38265ea1a9e02106d8b61" "10001" "aaccja'
 */
(function () {
    var cleParam  = process.argv[2];
    var exponentParam = process.argv[3];
    var passwordAsLetters = process.argv[4];

    var encrypted = encrypt(cleParam, exponentParam, passwordAsLetters);
    console.log(encrypted);
})();