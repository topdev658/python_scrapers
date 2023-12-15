// const {webcrypto: crypto} = require("crypto");
(function (exports) {
    'use strict';

    const crypto = require('crypto').webcrypto;

    let f = {};
    let e = {};

    e.assert = function (l, n) {
        if (!l) throw new Error(n)
    }

    let s = function (l) {
        switch (l) {
            case 'RSA-OAEP':
                return {
                    jwe_name: 'RSA-OAEP',
                    id: {
                        name: 'RSA-OAEP',
                        hash: {
                            name: 'SHA-1'
                        }
                    }
                };
            case 'RSA-OAEP-256':
                return {
                    jwe_name: 'RSA-OAEP-256',
                    id: {
                        name: 'RSA-OAEP',
                        hash: {
                            name: 'SHA-256'
                        }
                    }
                };
            case 'A128KW':
                return {
                    jwe_name: 'A128KW',
                    id: {
                        name: 'AES-KW',
                        length: 128
                    }
                };
            case 'A256KW':
                return {
                    jwe_name: 'A256KW',
                    id: {
                        name: 'AES-KW',
                        length: 256
                    }
                };
            case 'dir':
                return {
                    jwe_name: 'dir'
                };
            case 'A128CBC-HS256':
                return {
                    jwe_name: 'A128CBC-HS256',
                    id: {
                        name: 'AES-CBC',
                        length: 128
                    },
                    iv_bytes: 16,
                    specific_cek_bytes: 32,
                    auth: {
                        key_bytes: 16,
                        id: {
                            name: 'HMAC',
                            hash: {
                                name: 'SHA-256'
                            }
                        },
                        truncated_bytes: 16
                    }
                };
            case 'A256CBC-HS512':
                return {
                    jwe_name: 'A256CBC-HS512',
                    id: {
                        name: 'AES-CBC',
                        length: 256
                    },
                    iv_bytes: 16,
                    specific_cek_bytes: 64,
                    auth: {
                        key_bytes: 32,
                        id: {
                            name: 'HMAC',
                            hash: {
                                name: 'SHA-512'
                            }
                        },
                        truncated_bytes: 32
                    }
                };
            case 'A128GCM':
                return {
                    jwe_name: 'A128GCM',
                    id: {
                        name: 'AES-GCM',
                        length: 128
                    },
                    iv_bytes: 12,
                    auth: {
                        aead: !0,
                        tag_bytes: 16
                    }
                };
            case 'A256GCM':
                return {
                    jwe_name: 'A256GCM',
                    id: {
                        name: 'AES-GCM',
                        length: 256
                    },
                    iv_bytes: 12,
                    auth: {
                        aead: !0,
                        tag_bytes: 16
                    }
                };
            default:
                throw Error('unsupported algorithm: ' + l)
        }
    };

    let h = function (l) {
        switch (l) {
            case 'RS256':
            case 'RS384':
            case 'RS512':
            case 'PS256':
            case 'PS384':
            case 'PS512':
            case 'HS256':
            case 'HS384':
            case 'HS512':
            case 'ES256':
            case 'ES384':
            case 'ES512':
                return {
                    publicKey: 'verify',
                    privateKey: 'sign'
                };
            case 'RSA-OAEP':
            case 'RSA-OAEP-256':
            case 'A128KW':
            case 'A256KW':
                return {
                    publicKey: 'wrapKey',
                    privateKey: 'unwrapKey'
                };
            default:
                throw Error('unsupported algorithm: ' + l)
        }
    };

    let d = function (l) {
        switch (l) {
            case 'RS256':
                return {
                    jwa_name: 'RS256',
                    id: {
                        name: 'RSASSA-PKCS1-v1_5',
                        hash: {
                            name: 'SHA-256'
                        }
                    }
                };
            case 'RS384':
                return {
                    jwa_name: 'RS384',
                    id: {
                        name: 'RSASSA-PKCS1-v1_5',
                        hash: {
                            name: 'SHA-384'
                        }
                    }
                };
            case 'RS512':
                return {
                    jwa_name: 'RS512',
                    id: {
                        name: 'RSASSA-PKCS1-v1_5',
                        hash: {
                            name: 'SHA-512'
                        }
                    }
                };
            case 'PS256':
                return {
                    jwa_name: 'PS256',
                    id: {
                        name: 'RSA-PSS',
                        hash: {
                            name: 'SHA-256'
                        },
                        saltLength: 20
                    }
                };
            case 'PS384':
                return {
                    jwa_name: 'PS384',
                    id: {
                        name: 'RSA-PSS',
                        hash: {
                            name: 'SHA-384'
                        },
                        saltLength: 20
                    }
                };
            case 'PS512':
                return {
                    jwa_name: 'PS512',
                    id: {
                        name: 'RSA-PSS',
                        hash: {
                            name: 'SHA-512'
                        },
                        saltLength: 20
                    }
                };
            case 'HS256':
                return {
                    jwa_name: 'HS256',
                    id: {
                        name: 'HMAC',
                        hash: {
                            name: 'SHA-256'
                        }
                    }
                };
            case 'HS384':
                return {
                    jwa_name: 'HS384',
                    id: {
                        name: 'HMAC',
                        hash: {
                            name: 'SHA-384'
                        }
                    }
                };
            case 'HS512':
                return {
                    jwa_name: 'HS512',
                    id: {
                        name: 'HMAC',
                        hash: {
                            name: 'SHA-512'
                        }
                    }
                };
            case 'ES256':
                return {
                    jwa_name: 'ES256',
                    id: {
                        name: 'ECDSA',
                        hash: {
                            name: 'SHA-256'
                        }
                    }
                };
            case 'ES384':
                return {
                    jwa_name: 'ES384',
                    id: {
                        name: 'ECDSA',
                        hash: {
                            name: 'SHA-384'
                        }
                    }
                };
            case 'ES512':
                return {
                    jwa_name: 'ES512',
                    id: {
                        name: 'ECDSA',
                        hash: {
                            name: 'SHA-512'
                        }
                    }
                };
            default:
                throw Error('unsupported algorithm: ' + l)
        }
    }

    f.isString = function (l) {
        return 'string' == typeof l || l instanceof String
    }

    f.arrayish = function (l) {
        return l instanceof Array || l instanceof Uint8Array ? l : l instanceof ArrayBuffer ? new Uint8Array(l) : void e.assert(!1, 'arrayish: invalid input')
    }

    f.convertRsaKey = function (l, n) {
        var u,
            t = {},
            i = [];
        n.map((function (n) {
            void 0 === l[n] && i.push(n)
        })),
        i.length > 0 && e.assert(!1, 'convertRsaKey: Was expecting ' + i.join()),
        void 0 !== l.kty && e.assert('RSA' == l.kty, 'convertRsaKey: expecting rsa_key[\'kty\'] to be \'RSA\''),
            t.kty = 'RSA';
        try {
            d(l.alg),
                u = l.alg
        } catch (h) {
            try {
                s(l.alg),
                    u = l.alg
            } catch (m) {
                e.assert(u, 'convertRsaKey: expecting rsa_key[\'alg\'] to have a valid value')
            }
        }
        t.alg = u;
        for (var r = function (l) {
            return parseInt(l, 16)
        }, o = 0; o < n.length; o++) {
            var a = n[o],
                c = l[a];
            if ('e' == a) 'number' == typeof c && (c = f.Base64Url.encodeArray(f.stripLeadingZeros(f.arrayFromInt32(c))));
            else if (/^([0-9a-fA-F]{2}:)+[0-9a-fA-F]{2}$/.test(c)) {
                var p = c.split(':').map(r);
                c = f.Base64Url.encodeArray(f.stripLeadingZeros(p))
            } else 'string' != typeof c && e.assert(!1, 'convertRsaKey: expecting rsa_key[\'' + a + '\'] to be a string');
            t[a] = c
        }
        return t
    }

    f.arrayFromString = function (l) {
        e.assert(f.isString(l), 'arrayFromString: invalid input');
        var n = l.split('').map((function (l) {
            return l.charCodeAt(0)
        }));
        return new Uint8Array(n)
    }

    f.arrayFromUtf8String = function (l) {
        return e.assert(f.isString(l), 'arrayFromUtf8String: invalid input'),
            l = unescape(encodeURIComponent(l)),
            f.arrayFromString(l)
    }
    f.stringFromArray = function (l) {
        l = f.arrayish(l);
        // var n = new m('utf8').decode(l);
        var n = new TextDecoder('utf8').decode(l);
        try {
            return btoa(n),
                n
        } catch (t) {
            for (var u = '', e = 0; e < l.length; e++) u += String.fromCharCode(l[e]);
            return u
        }
    }

    f.utf8StringFromArray = function (l) {
        e.assert(l instanceof ArrayBuffer, 'utf8StringFromArray: invalid input');
        var n = f.stringFromArray(l);
        return decodeURIComponent(escape(n))
    }

    f.stripLeadingZeros = function (l) {
        l instanceof ArrayBuffer && (l = new Uint8Array(l));
        for (var n = !0, u = [], e = 0; e < l.length; e++) n && 0 === l[e] || (n = !1, u.push(l[e]));
        return u
    }

    f.arrayFromInt32 = function (l) {
        e.assert('number' == typeof l, 'arrayFromInt32: invalid input'),
            e.assert(l == l | 0, 'arrayFromInt32: out of range');
        for (var n = new Uint8Array(new Uint32Array([l]).buffer), u = new Uint8Array(4), t = 0; t < 4; t++) u[t] = n[3 - t];
        return u.buffer
    }


    f.arrayBufferConcat = function () {
        for (var l = [], n = 0, u = 0; u < arguments.length; u++) l.push(f.arrayish(arguments[u])),
            n += l[u].length;
        var t = new Uint8Array(n),
            i = 0;
        for (u = 0; u < arguments.length; u++) for (var r = 0; r < l[u].length; r++) t[i++] = l[u][r];
        return e.assert(i == n, 'arrayBufferConcat: unexpected offset'),
            t
    }


    f.Base64Url = {}

    f.Base64Url.toBase64Url = function (l) {
        return l.replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
    }

    f.Base64Url.fromBase64 = function (l) {
        for (var n = l.length % 4, u = n ? 4 - n : n, e = l.replace(/-/g, '+').replace(/_/g, '/'), t = 0; t < u; t++) e += '=';
        return e
    }


    f.Base64Url.b64DecodeUnicode = function (l) {
        try {
            var n = decodeURIComponent(atob(l).split('').map((function (l) {
                return '%' + ('00' + l.charCodeAt(0).toString(16)).slice(-2)
            })).join(''));
            return JSON.parse(n),
                n
        } catch (u) {
            return atob(l)
        }
    }

    f.Base64Url.b64EncodeUnicode = function (l) {
        try {
            return JSON.parse(l),
                btoa(encodeURIComponent(l).replace(/%([0-9A-F]{2})/g, (function (l, n) {
                    return String.fromCharCode('0x' + n)
                })))
        } catch (n) {
            return btoa(l)
        }
    }

    f.Base64Url.encode = function (l) {
        return e.assert(f.isString(l), 'Base64Url.encode: invalid input'),
            f.Base64Url.toBase64Url(f.Base64Url.b64EncodeUnicode(l))
    }

    f.Base64Url.encodeArray = function (l) {
        return f.Base64Url.encode(f.stringFromArray(l))
    }


    f.Base64Url.decode = function (l) {
        return e.assert(f.isString(l), 'Base64Url.decode: invalid input'),
            f.Base64Url.b64DecodeUnicode(f.Base64Url.fromBase64(l))
    }

    f.Base64Url.decodeArray = function (l) {
        return e.assert(f.isString(l), 'Base64Url.decodeArray: invalid input'),
            f.arrayFromString(f.Base64Url.decode(l))
    }

    f.sha256 = function (l) {
        return e.crypto.subtle.digest({
            name: 'SHA-256'
        }, f.arrayFromString(l)).then((function (l) {
            return f.Base64Url.encodeArray(l)
        }))
    }

    f.isCryptoKey = function (l) {
        return 'CryptoKey' == l.constructor.name || !!l.hasOwnProperty('algorithm')
    }


    const importRsaPrivateKey = function (keyObj, alg) {
        var u,
            t,
            i = h(alg);
        if ('unwrapKey' == i.privateKey) keyObj.alg || (keyObj.alg = alg),
            u = f.convertRsaKey(keyObj, [
                'n',
                'e',
                'd',
                'p',
                'q',
                'dp',
                'dq',
                'qi'
            ]),
            t = s(alg);
        else {
            var r = {
            };
            for (var o in keyObj) keyObj.hasOwnProperty(o) && (r[o] = keyObj[o]);
            t = d(alg),
            !r.alg && alg && (r.alg = alg),
                (u = f.convertRsaKey(r, [
                    'n',
                    'e',
                    'd',
                    'p',
                    'q',
                    'dp',
                    'dq',
                    'qi'
                ])).ext = !0
        }
        return crypto.subtle.importKey('jwk', u, t.id, !1, [
            i.privateKey
        ])
    }

    // 1145
    function Q(l, n) {
        return n ? function (l, n) {
            if (null != l) {
                if (function (l) {
                    return l && 'function' == typeof l[I]
                }(l)) return function (l, n) {
                    return new P((function (u) {
                        var e = new y;
                        return e.add(n.schedule((function () {
                            var t = l[I]();
                            e.add(t.subscribe({
                                next: function (l) {
                                    e.add(n.schedule((function () {
                                        return u.next(l)
                                    })))
                                },
                                error: function (l) {
                                    e.add(n.schedule((function () {
                                        return u.error(l)
                                    })))
                                },
                                complete: function () {
                                    e.add(n.schedule((function () {
                                        return u.complete()
                                    })))
                                }
                            }))
                        }))),
                            e
                    }))
                }(l, n);
                if (H(l)) return function (l, n) {
                    return new P((function (u) {
                        var e = new y;
                        return e.add(n.schedule((function () {
                            return l.then((function (l) {
                                e.add(n.schedule((function () {
                                    u.next(l),
                                        e.add(n.schedule((function () {
                                            return u.complete()
                                        })))
                                })))
                            }), (function (l) {
                                e.add(n.schedule((function () {
                                    return u.error(l)
                                })))
                            }))
                        }))),
                            e
                    }))
                }(l, n);
                if (B(l)) return J(l, n);
                if (function (l) {
                    return l && 'function' == typeof l[z]
                }(l) || 'string' == typeof l) return function (l, n) {
                    if (!l) throw new Error('Iterable cannot be null');
                    return new P((function (u) {
                        var e,
                            t = new y;
                        return t.add((function () {
                            e && 'function' == typeof e.return && e.return()
                        })),
                            t.add(n.schedule((function () {
                                e = l[z](),
                                    t.add(n.schedule((function () {
                                        if (!u.closed) {
                                            var l,
                                                n;
                                            try {
                                                var t = e.next();
                                                l = t.value,
                                                    n = t.done
                                            } catch (i) {
                                                return void u.error(i)
                                            }
                                            n ? u.complete() : (u.next(l), this.schedule())
                                        }
                                    })))
                            }))),
                            t
                    }))
                }(l, n)
            }
            throw new TypeError((null !== l && typeof l || l) + ' is not observable')
        }(l, n) : l instanceof P ? l : new P(q(l))
    }

    // 24796 -> 180646
    const G_ = function (l, n) {
        !function () {
            'use strict';
            for (var l = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', u = new Uint8Array(256), e = 0; e < l.length; e++) u[l.charCodeAt(e)] = e;
            n.encode = function (n) {
                var u,
                    e = new Uint8Array(n),
                    t = e.length,
                    i = '';
                for (u = 0; u < t; u += 3) i += l[e[u] >> 2],
                    i += l[(3 & e[u]) << 4 | e[u + 1] >> 4],
                    i += l[(15 & e[u + 1]) << 2 | e[u + 2] >> 6],
                    i += l[63 & e[u + 2]];
                return t % 3 == 2 ? i = i.substring(0, i.length - 1) + '=' : t % 3 == 1 && (i = i.substring(0, i.length - 2) + '=='),
                    i
            },
                n.decode = function (l) {
                    var n,
                        e,
                        t,
                        i,
                        r,
                        o = 0.75 * l.length,
                        a = l.length,
                        s = 0;
                    '=' === l[l.length - 1] && (o--, '=' === l[l.length - 2] && o--);
                    var c = new ArrayBuffer(o),
                        d = new Uint8Array(c);
                    for (n = 0; n < a; n += 4) e = u[l.charCodeAt(n)],
                        t = u[l.charCodeAt(n + 1)],
                        i = u[l.charCodeAt(n + 2)],
                        r = u[l.charCodeAt(n + 3)],
                        d[s++] = e << 2 | t >> 4,
                        d[s++] = (15 & t) << 4 | i >> 2,
                        d[s++] = (3 & i) << 6 | 63 & r;
                    return c
                }
        }()
    }

    // 24797 -> 84814 ENCRYPTER
    const U_ = function (l, n, u) {
        var e = {
            },
            t = {
            },
            i = {
            };
        n.setCrypto = function (l) {
            e.crypto = l
        },
        'undefined' != typeof crypto && n.setCrypto(crypto),
        'function' != typeof atob && (atob = function (l) {
            return new Buffer(l, 'base64').toString('binary')
        }),
        'function' != typeof btoa && (btoa = function (l) {
            return (l instanceof Buffer ? l : new Buffer(l.toString(), 'binary')).toString('base64')
        }),
            e.caniuse = function () {
                var l = !0;
                return (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = (l = l && 'function' == typeof Promise) && 'function' == typeof Promise.reject) && 'function' == typeof Promise.prototype.then) && 'function' == typeof Promise.all) && 'object' == typeof e.crypto) && 'object' == typeof e.crypto.subtle) && 'function' == typeof e.crypto.getRandomValues) && 'function' == typeof e.crypto.subtle.importKey) && 'function' == typeof e.crypto.subtle.generateKey) && 'function' == typeof e.crypto.subtle.exportKey) && 'function' == typeof e.crypto.subtle.wrapKey) && 'function' == typeof e.crypto.subtle.unwrapKey) && 'function' == typeof e.crypto.subtle.encrypt) && 'function' == typeof e.crypto.subtle.decrypt) && 'function' == typeof e.crypto.subtle.sign) && 'function' == typeof ArrayBuffer) && ('function' == typeof Uint8Array || 'object' == typeof Uint8Array)) && ('function' == typeof Uint32Array || 'object' == typeof Uint32Array)) && 'object' == typeof JSON) && 'function' == typeof JSON.parse) && 'function' == typeof JSON.stringify) && 'function' == typeof atob) && 'function' == typeof btoa
            },
            e.assert = function (l, n) {
                if (!l) throw new Error(n)
            },
            n.Jose = e,
            n.JoseJWE = t,
            n.JoseJWS = i;
        var r = function () {
            this.setKeyEncryptionAlgorithm('RSA-OAEP'),
                this.setContentEncryptionAlgorithm('A256GCM'),
                this.setContentSignAlgorithm('RS256')
        };
        e.WebCryptographer = r,
            r.prototype.setKeyEncryptionAlgorithm = function (l) {
                this.key_encryption = s(l)
            },
            r.prototype.getKeyEncryptionAlgorithm = function () {
                return this.key_encryption.jwe_name
            },
            r.prototype.setContentEncryptionAlgorithm = function (l) {
                this.content_encryption = s(l)
            },
            r.prototype.getContentEncryptionAlgorithm = function () {
                return this.content_encryption.jwe_name
            },
            r.prototype.setContentSignAlgorithm = function (l) {
                this.content_sign = d(l)
            },
            r.prototype.getContentSignAlgorithm = function () {
                return this.content_sign.jwa_name
            },
            r.prototype.createIV = function () {
                var l = new Uint8Array(new Array(this.content_encryption.iv_bytes));
                return e.crypto.getRandomValues(l)
            },
            r.prototype.createCek = function () {
                var l = o(this.content_encryption);
                return e.crypto.subtle.generateKey(l.id, !0, l.enc_op)
            },
            r.prototype.wrapCek = function (l, n) {
                return e.crypto.subtle.wrapKey('raw', l, n, this.key_encryption.id)
            },
            r.prototype.unwrapCek = function (l, n) {
                var u = o(this.content_encryption);
                return e.crypto.subtle.unwrapKey('raw', l, n, this.key_encryption.id, u.id, this.content_encryption.specific_cek_bytes > 0, u.dec_op)
            };
        var o = function (l) {
            var n = l.specific_cek_bytes;
            if (n) {
                if (16 == n) return {
                    id: {
                        name: 'AES-CBC',
                        length: 128
                    },
                    enc_op: [
                        'encrypt'
                    ],
                    dec_op: [
                        'decrypt'
                    ]
                };
                if (32 == n) return {
                    id: {
                        name: 'AES-CBC',
                        length: 256
                    },
                    enc_op: [
                        'encrypt'
                    ],
                    dec_op: [
                        'decrypt'
                    ]
                };
                if (64 == n) return {
                    id: {
                        name: 'HMAC',
                        hash: {
                            name: 'SHA-256'
                        }
                    },
                    enc_op: [
                        'sign'
                    ],
                    dec_op: [
                        'verify'
                    ]
                };
                if (128 == n) return {
                    id: {
                        name: 'HMAC',
                        hash: {
                            name: 'SHA-384'
                        }
                    },
                    enc_op: [
                        'sign'
                    ],
                    dec_op: [
                        'verify'
                    ]
                };
                e.assert(!1, 'getCekWorkaround: invalid len')
            }
            return {
                id: l.id,
                enc_op: [
                    'encrypt'
                ],
                dec_op: [
                    'decrypt'
                ]
            }
        };
        r.prototype.encrypt = function (l, n, u, t) {
            var i = this.content_encryption;
            if (l.length != i.iv_bytes) return Promise.reject(Error('invalid IV length'));
            if (i.auth.aead) {
                var r = i.auth.tag_bytes,
                    o = {
                        name: i.id.name,
                        iv: l,
                        additionalData: n,
                        tagLength: 8 * r
                    };
                return u.then((function (l) {
                    return e.crypto.subtle.encrypt(o, l, t).then((function (l) {
                        var n = l.byteLength - r;
                        return {
                            cipher: l.slice(0, n),
                            tag: l.slice(n)
                        }
                    }))
                }))
            }
            var s = a(i, u, [
                    'encrypt'
                ]),
                d = s[0],
                p = s[1].then((function (n) {
                    return e.crypto.subtle.encrypt({
                        name: i.id.name,
                        iv: l
                    }, n, t)
                })),
                h = p.then((function (u) {
                    return c(i, d, n, l, u)
                }));
            return Promise.all([p,
                h]).then((function (l) {
                return {
                    cipher: l[0],
                    tag: l[1]
                }
            }))
        },
            r.prototype.decrypt = function (l, n, u, t, i) {
                if (u.length != this.content_encryption.iv_bytes) return Promise.reject(Error('decryptCiphertext: invalid IV'));
                var r = this.content_encryption;
                // VB
                // r = "{\"jwe_name\":\"A256GCM\",\"id\":{\"name\":\"AES-GCM\",\"length\":256},\"iv_bytes\":12,\"auth\":{\"aead\":true,\"tag_bytes\":16}}"
                // u = Uint8Array(12)
                // n = Uint8Array(2262)
                if (r.auth.aead) {
                    var o = {
                        name: r.id.name,
                        iv: u,
                        additionalData: n,
                        tagLength: 8 * r.auth.tag_bytes
                    };
                    return l.then((function (l) {
                        var n = f.arrayBufferConcat(t, i);
                        return e.crypto.subtle.decrypt(o, l, n)
                    }))
                }
                var s = a(r, l, [
                        'decrypt'
                    ]),
                    d = s[0],
                    p = s[1],
                    h = c(r, d, n, u, t);
                return Promise.all([p,
                    h]).then((function (l) {
                    var n = l[0];
                    return function (l, n, u, t) {
                        return e.assert(u instanceof Uint8Array, 'compare: invalid input'),
                            e.assert(t instanceof Uint8Array, 'compare: invalid input'),
                            n.then((function (n) {
                                var i = e.crypto.subtle.sign(l.auth.id, n, u),
                                    r = e.crypto.subtle.sign(l.auth.id, n, t);
                                return Promise.all([i,
                                    r]).then((function (l) {
                                    var n = new Uint8Array(l[0]),
                                        u = new Uint8Array(l[1]);
                                    if (n.length != u.length) throw new Error('compare failed');
                                    for (var e = 0; e < n.length; e++) if (n[e] != u[e]) throw new Error('compare failed');
                                    return Promise.resolve(null)
                                }))
                            }))
                    }(r, d, new Uint8Array(l[1]), i).then((function () {
                        return e.crypto.subtle.decrypt({
                            name: r.id.name,
                            iv: u
                        }, n, t)
                    })).catch((function (l) {
                        return Promise.reject(Error('decryptCiphertext: MAC failed.'))
                    }))
                }))
            },
            r.prototype.sign = function (l, n, u) {
                var t = this.content_sign;
                return l.alg && (t = d(l.alg)),
                    u.then((function (u) {
                        return e.crypto.subtle.sign(t.id, u, f.arrayFromString(f.Base64Url.encode(JSON.stringify(l)) + '.' + f.Base64Url.encodeArray(n)))
                    }))
            },
            r.prototype.verify = function (l, n, u, t, i) {
                var r = this.content_sign;
                return t.then((function (t) {
                    return r = d(p(t)),
                        e.crypto.subtle.verify(r.id, t, u, f.arrayFromString(l + '.' + n)).then((function (l) {
                            return {
                                kid: i,
                                verified: l
                            }
                        }))
                }))
            },
            e.WebCryptographer.keyId = function (l) {
                return f.sha256(l.n + '+' + l.d)
            };
        var a = function (l, n, u) {
                var t = n.then((function (l) {
                    return e.crypto.subtle.exportKey('raw', l)
                }));
                return [t.then((function (n) {
                    if (8 * n.byteLength != l.id.length + 8 * l.auth.key_bytes) return Promise.reject(Error('encryptPlainText: incorrect cek length'));
                    var u = n.slice(0, l.auth.key_bytes);
                    return e.crypto.subtle.importKey('raw', u, l.auth.id, !1, [
                        'sign'
                    ])
                })),
                    t.then((function (n) {
                        if (8 * n.byteLength != l.id.length + 8 * l.auth.key_bytes) return Promise.reject(Error('encryptPlainText: incorrect cek length'));
                        var t = n.slice(l.auth.key_bytes);
                        return e.crypto.subtle.importKey('raw', t, l.id, !1, u)
                    }))]
            },
            s = function (l) {
                switch (l) {
                    case 'RSA-OAEP':
                        return {
                            jwe_name: 'RSA-OAEP',
                            id: {
                                name: 'RSA-OAEP',
                                hash: {
                                    name: 'SHA-1'
                                }
                            }
                        };
                    case 'RSA-OAEP-256':
                        return {
                            jwe_name: 'RSA-OAEP-256',
                            id: {
                                name: 'RSA-OAEP',
                                hash: {
                                    name: 'SHA-256'
                                }
                            }
                        };
                    case 'A128KW':
                        return {
                            jwe_name: 'A128KW',
                            id: {
                                name: 'AES-KW',
                                length: 128
                            }
                        };
                    case 'A256KW':
                        return {
                            jwe_name: 'A256KW',
                            id: {
                                name: 'AES-KW',
                                length: 256
                            }
                        };
                    case 'dir':
                        return {
                            jwe_name: 'dir'
                        };
                    case 'A128CBC-HS256':
                        return {
                            jwe_name: 'A128CBC-HS256',
                            id: {
                                name: 'AES-CBC',
                                length: 128
                            },
                            iv_bytes: 16,
                            specific_cek_bytes: 32,
                            auth: {
                                key_bytes: 16,
                                id: {
                                    name: 'HMAC',
                                    hash: {
                                        name: 'SHA-256'
                                    }
                                },
                                truncated_bytes: 16
                            }
                        };
                    case 'A256CBC-HS512':
                        return {
                            jwe_name: 'A256CBC-HS512',
                            id: {
                                name: 'AES-CBC',
                                length: 256
                            },
                            iv_bytes: 16,
                            specific_cek_bytes: 64,
                            auth: {
                                key_bytes: 32,
                                id: {
                                    name: 'HMAC',
                                    hash: {
                                        name: 'SHA-512'
                                    }
                                },
                                truncated_bytes: 32
                            }
                        };
                    case 'A128GCM':
                        return {
                            jwe_name: 'A128GCM',
                            id: {
                                name: 'AES-GCM',
                                length: 128
                            },
                            iv_bytes: 12,
                            auth: {
                                aead: !0,
                                tag_bytes: 16
                            }
                        };
                    case 'A256GCM':
                        return {
                            jwe_name: 'A256GCM',
                            id: {
                                name: 'AES-GCM',
                                length: 256
                            },
                            iv_bytes: 12,
                            auth: {
                                aead: !0,
                                tag_bytes: 16
                            }
                        };
                    default:
                        throw Error('unsupported algorithm: ' + l)
                }
            },
            c = function (l, n, u, t, i) {
                return n.then((function (n) {
                    var r = new Uint8Array(f.arrayFromInt32(8 * u.length)),
                        o = new Uint8Array(8);
                    o.set(r, 4);
                    var a = f.arrayBufferConcat(u, t, i, o);
                    return e.crypto.subtle.sign(l.auth.id, n, a).then((function (n) {
                        return n.slice(0, l.auth.truncated_bytes)
                    }))
                }))
            },
            d = function (l) {
                switch (l) {
                    case 'RS256':
                        return {
                            jwa_name: 'RS256',
                            id: {
                                name: 'RSASSA-PKCS1-v1_5',
                                hash: {
                                    name: 'SHA-256'
                                }
                            }
                        };
                    case 'RS384':
                        return {
                            jwa_name: 'RS384',
                            id: {
                                name: 'RSASSA-PKCS1-v1_5',
                                hash: {
                                    name: 'SHA-384'
                                }
                            }
                        };
                    case 'RS512':
                        return {
                            jwa_name: 'RS512',
                            id: {
                                name: 'RSASSA-PKCS1-v1_5',
                                hash: {
                                    name: 'SHA-512'
                                }
                            }
                        };
                    case 'PS256':
                        return {
                            jwa_name: 'PS256',
                            id: {
                                name: 'RSA-PSS',
                                hash: {
                                    name: 'SHA-256'
                                },
                                saltLength: 20
                            }
                        };
                    case 'PS384':
                        return {
                            jwa_name: 'PS384',
                            id: {
                                name: 'RSA-PSS',
                                hash: {
                                    name: 'SHA-384'
                                },
                                saltLength: 20
                            }
                        };
                    case 'PS512':
                        return {
                            jwa_name: 'PS512',
                            id: {
                                name: 'RSA-PSS',
                                hash: {
                                    name: 'SHA-512'
                                },
                                saltLength: 20
                            }
                        };
                    case 'HS256':
                        return {
                            jwa_name: 'HS256',
                            id: {
                                name: 'HMAC',
                                hash: {
                                    name: 'SHA-256'
                                }
                            }
                        };
                    case 'HS384':
                        return {
                            jwa_name: 'HS384',
                            id: {
                                name: 'HMAC',
                                hash: {
                                    name: 'SHA-384'
                                }
                            }
                        };
                    case 'HS512':
                        return {
                            jwa_name: 'HS512',
                            id: {
                                name: 'HMAC',
                                hash: {
                                    name: 'SHA-512'
                                }
                            }
                        };
                    case 'ES256':
                        return {
                            jwa_name: 'ES256',
                            id: {
                                name: 'ECDSA',
                                hash: {
                                    name: 'SHA-256'
                                }
                            }
                        };
                    case 'ES384':
                        return {
                            jwa_name: 'ES384',
                            id: {
                                name: 'ECDSA',
                                hash: {
                                    name: 'SHA-384'
                                }
                            }
                        };
                    case 'ES512':
                        return {
                            jwa_name: 'ES512',
                            id: {
                                name: 'ECDSA',
                                hash: {
                                    name: 'SHA-512'
                                }
                            }
                        };
                    default:
                        throw Error('unsupported algorithm: ' + l)
                }
            },
            p = function (l) {
                var n = '',
                    u = l.algorithm.name,
                    e = l.algorithm.hash.name;
                if ('RSASSA-PKCS1-v1_5' == u) n = 'R';
                else {
                    if ('RSA-PSS' != u) throw new Error('unsupported sign/verify algorithm ' + u);
                    n = 'P'
                }
                if (0 !== e.indexOf('SHA-')) throw new Error('unsupported hash algorithm ' + u);
                return (n += 'S') + e.substring(4)
            },
            h = function (l) {
                switch (l) {
                    case 'RS256':
                    case 'RS384':
                    case 'RS512':
                    case 'PS256':
                    case 'PS384':
                    case 'PS512':
                    case 'HS256':
                    case 'HS384':
                    case 'HS512':
                    case 'ES256':
                    case 'ES384':
                    case 'ES512':
                        return {
                            publicKey: 'verify',
                            privateKey: 'sign'
                        };
                    case 'RSA-OAEP':
                    case 'RSA-OAEP-256':
                    case 'A128KW':
                    case 'A256KW':
                        return {
                            publicKey: 'wrapKey',
                            privateKey: 'unwrapKey'
                        };
                    default:
                        throw Error('unsupported algorithm: ' + l)
                }
            };
        e.Utils = {
        };
        var f = {
            },
            m = u('QZTG').TextDecoder;
        e.Utils.importRsaPublicKey = function (l, n) {
            var u,
                t,
                i = h(n);
            if ('wrapKey' == i.publicKey) l.alg || (l.alg = n),
                u = f.convertRsaKey(l, [
                    'n',
                    'e'
                ]),
                t = s(n);
            else {
                var r = {
                };
                for (var o in l) l.hasOwnProperty(o) && (r[o] = l[o]);
                !r.alg && n && (r.alg = n),
                    t = d(r.alg),
                    (u = f.convertRsaKey(r, [
                        'n',
                        'e'
                    ])).ext = !0
            }
            return e.crypto.subtle.importKey('jwk', u, t.id, !1, [
                i.publicKey
            ])
        },
            e.Utils.importRsaPrivateKey = function (l, n) {
                var u,
                    t,
                    i = h(n);
                if ('unwrapKey' == i.privateKey) l.alg || (l.alg = n),
                    u = f.convertRsaKey(l, [
                        'n',
                        'e',
                        'd',
                        'p',
                        'q',
                        'dp',
                        'dq',
                        'qi'
                    ]),
                    t = s(n);
                else {
                    var r = {
                    };
                    for (var o in l) l.hasOwnProperty(o) && (r[o] = l[o]);
                    t = d(n),
                    !r.alg && n && (r.alg = n),
                        (u = f.convertRsaKey(r, [
                            'n',
                            'e',
                            'd',
                            'p',
                            'q',
                            'dp',
                            'dq',
                            'qi'
                        ])).ext = !0
                }
                return e.crypto.subtle.importKey('jwk', u, t.id, !1, [
                    i.privateKey
                ])
            },
            f.isString = function (l) {
                return 'string' == typeof l || l instanceof String
            },
            f.arrayish = function (l) {
                return l instanceof Array || l instanceof Uint8Array ? l : l instanceof ArrayBuffer ? new Uint8Array(l) : void e.assert(!1, 'arrayish: invalid input')
            },
            f.convertRsaKey = function (l, n) {
                var u,
                    t = {
                    },
                    i = [
                    ];
                n.map((function (n) {
                    void 0 === l[n] && i.push(n)
                })),
                i.length > 0 && e.assert(!1, 'convertRsaKey: Was expecting ' + i.join()),
                void 0 !== l.kty && e.assert('RSA' == l.kty, 'convertRsaKey: expecting rsa_key[\'kty\'] to be \'RSA\''),
                    t.kty = 'RSA';
                try {
                    d(l.alg),
                        u = l.alg
                } catch (h) {
                    try {
                        s(l.alg),
                            u = l.alg
                    } catch (m) {
                        e.assert(u, 'convertRsaKey: expecting rsa_key[\'alg\'] to have a valid value')
                    }
                }
                t.alg = u;
                for (var r = function (l) {
                    return parseInt(l, 16)
                }, o = 0; o < n.length; o++) {
                    var a = n[o],
                        c = l[a];
                    if ('e' == a) 'number' == typeof c && (c = f.Base64Url.encodeArray(f.stripLeadingZeros(f.arrayFromInt32(c))));
                    else if (/^([0-9a-fA-F]{2}:)+[0-9a-fA-F]{2}$/.test(c)) {
                        var p = c.split(':').map(r);
                        c = f.Base64Url.encodeArray(f.stripLeadingZeros(p))
                    } else 'string' != typeof c && e.assert(!1, 'convertRsaKey: expecting rsa_key[\'' + a + '\'] to be a string');
                    t[a] = c
                }
                return t
            },
            f.arrayFromString = function (l) {
                e.assert(f.isString(l), 'arrayFromString: invalid input');
                var n = l.split('').map((function (l) {
                    return l.charCodeAt(0)
                }));
                return new Uint8Array(n)
            },
            f.arrayFromUtf8String = function (l) {
                return e.assert(f.isString(l), 'arrayFromUtf8String: invalid input'),
                    l = unescape(encodeURIComponent(l)),
                    f.arrayFromString(l)
            },
            f.stringFromArray = function (l) {
                l = f.arrayish(l);
                var n = new m('utf8').decode(l);
                try {
                    return btoa(n),
                        n
                } catch (t) {
                    for (var u = '', e = 0; e < l.length; e++) u += String.fromCharCode(l[e]);
                    return u
                }
            },
            f.utf8StringFromArray = function (l) {
                e.assert(l instanceof ArrayBuffer, 'utf8StringFromArray: invalid input');
                var n = f.stringFromArray(l);
                return decodeURIComponent(escape(n))
            },
            f.stripLeadingZeros = function (l) {
                l instanceof ArrayBuffer && (l = new Uint8Array(l));
                for (var n = !0, u = [
                ], e = 0; e < l.length; e++) n && 0 === l[e] || (n = !1, u.push(l[e]));
                return u
            },
            f.arrayFromInt32 = function (l) {
                e.assert('number' == typeof l, 'arrayFromInt32: invalid input'),
                    e.assert(l == l | 0, 'arrayFromInt32: out of range');
                for (var n = new Uint8Array(new Uint32Array([l]).buffer), u = new Uint8Array(4), t = 0; t < 4; t++) u[t] = n[3 - t];
                return u.buffer
            },
            f.arrayBufferConcat = function () {
                for (var l = [
                ], n = 0, u = 0; u < arguments.length; u++) l.push(f.arrayish(arguments[u])),
                    n += l[u].length;
                var t = new Uint8Array(n),
                    i = 0;
                for (u = 0; u < arguments.length; u++) for (var r = 0; r < l[u].length; r++) t[i++] = l[u][r];
                return e.assert(i == n, 'arrayBufferConcat: unexpected offset'),
                    t
            },
            f.Base64Url = {
            },
            f.Base64Url.toBase64Url = function (l) {
                return l.replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
            },
            f.Base64Url.fromBase64 = function (l) {
                for (var n = l.length % 4, u = n ? 4 - n : n, e = l.replace(/-/g, '+').replace(/_/g, '/'), t = 0; t < u; t++) e += '=';
                return e
            },
            f.Base64Url.b64DecodeUnicode = function (l) {
                try {
                    var n = decodeURIComponent(atob(l).split('').map((function (l) {
                        return '%' + ('00' + l.charCodeAt(0).toString(16)).slice( - 2)
                    })).join(''));
                    return JSON.parse(n),
                        n
                } catch (u) {
                    return atob(l)
                }
            },
            f.Base64Url.b64EncodeUnicode = function (l) {
                try {
                    return JSON.parse(l),
                        btoa(encodeURIComponent(l).replace(/%([0-9A-F]{2})/g, (function (l, n) {
                            return String.fromCharCode('0x' + n)
                        })))
                } catch (n) {
                    return btoa(l)
                }
            },
            f.Base64Url.encode = function (l) {
                return e.assert(f.isString(l), 'Base64Url.encode: invalid input'),
                    f.Base64Url.toBase64Url(f.Base64Url.b64EncodeUnicode(l))
            },
            f.Base64Url.encodeArray = function (l) {
                return f.Base64Url.encode(f.stringFromArray(l))
            },
            f.Base64Url.decode = function (l) {
                return e.assert(f.isString(l), 'Base64Url.decode: invalid input'),
                    f.Base64Url.b64DecodeUnicode(f.Base64Url.fromBase64(l))
            },
            f.Base64Url.decodeArray = function (l) {
                return e.assert(f.isString(l), 'Base64Url.decodeArray: invalid input'),
                    f.arrayFromString(f.Base64Url.decode(l))
            },
            f.sha256 = function (l) {
                return e.crypto.subtle.digest({
                    name: 'SHA-256'
                }, f.arrayFromString(l)).then((function (l) {
                    return f.Base64Url.encodeArray(l)
                }))
            },
            f.isCryptoKey = function (l) {
                return 'CryptoKey' == l.constructor.name || !!l.hasOwnProperty('algorithm')
            },
            t.Encrypter = function (l, n) {
                this.cryptographer = l,
                    this.key_promise = n,
                    this.userHeaders = {
                    }
            },
            t.Encrypter.prototype.addHeader = function (l, n) {
                this.userHeaders[l] = n
            },
            t.Encrypter.prototype.encrypt = function (l) {
                var n,
                    u;
                'dir' == this.cryptographer.getKeyEncryptionAlgorithm() ? (n = Promise.resolve(this.key_promise), u = [
                ]) : (n = this.cryptographer.createCek(), u = Promise.all([this.key_promise,
                    n]).then((function (l) {
                    return this.cryptographer.wrapCek(l[1], l[0])
                }).bind(this)));
                var e = (function (l, n) {
                    var u = {
                    };
                    for (var e in this.userHeaders) u[e] = this.userHeaders[e];
                    u.alg = this.cryptographer.getKeyEncryptionAlgorithm(),
                        u.enc = this.cryptographer.getContentEncryptionAlgorithm();
                    var t = f.Base64Url.encode(JSON.stringify(u)),
                        i = this.cryptographer.createIV(),
                        r = f.arrayFromString(t);
                    return n = f.arrayFromUtf8String(n),
                        this.cryptographer.encrypt(i, r, l, n).then((function (l) {
                            return l.header = t,
                                l.iv = i,
                                l
                        }))
                }).bind(this, n, l) ();
                return Promise.all([u,
                    e]).then((function (l) {
                    var n = l[1];
                    return n.header + '.' + f.Base64Url.encodeArray(l[0]) + '.' + f.Base64Url.encodeArray(n.iv) + '.' + f.Base64Url.encodeArray(n.cipher) + '.' + f.Base64Url.encodeArray(n.tag)
                }))
            },
            t.Decrypter = function (l, n) {
                this.cryptographer = l,
                    this.key_promise = n,
                    this.headers = {
                    }
            },
            t.Decrypter.prototype.getHeaders = function () {
                return this.headers
            },
            t.Decrypter.prototype.decrypt = function (l) { // VB: handshake decrypter
                var n,
                    u = l.split('.');
                if (5 != u.length) return Promise.reject(Error('decrypt: invalid input'));
                if (this.headers = JSON.parse(f.Base64Url.decode(u[0])), !this.headers.alg) return Promise.reject(Error('decrypt: missing alg'));
                if (!this.headers.enc) return Promise.reject(Error('decrypt: missing enc'));
                if (this.cryptographer.setKeyEncryptionAlgorithm(this.headers.alg), this.cryptographer.setContentEncryptionAlgorithm(this.headers.enc), this.headers.crit) return Promise.reject(Error('decrypt: crit is not supported'));
                if ('dir' == this.headers.alg) n = Promise.resolve(this.key_promise);
                else {
                    var e = f.Base64Url.decodeArray(u[1]);
                    n = this.key_promise.then((function (l) {
                        return this.cryptographer.unwrapCek(e, l)
                    }).bind(this))
                }
                return this.cryptographer.decrypt(n, f.arrayFromString(u[0]), f.Base64Url.decodeArray(u[2]), f.Base64Url.decodeArray(u[3]), f.Base64Url.decodeArray(u[4])).then(f.utf8StringFromArray)
            },
            i.Signer = function (l) {
                this.cryptographer = l,
                this.key_promises = {
                },
                this.waiting_kid = 0,
                this.headers = {
                },
                this.signer_aads = {
                },
                this.signer_headers = {
                }
            },
            i.Signer.prototype.addSigner = function (l, n, u, t) {
                var i,
                    r,
                    o,
                    a = this;
                if (f.isCryptoKey(l) ? i = new Promise((function (n) {
                    n(l)
                })) : (r = u && u.alg ? u.alg : a.cryptographer.getContentSignAlgorithm(), i = e.Utils.importRsaPrivateKey(l, r, 'sign')), n) o = new Promise((function (l) {
                    l(n)
                }));
                else {
                    if (f.isCryptoKey(l)) throw new Error('key_id is a mandatory argument when the key is a CryptoKey');
                    o = e.WebCryptographer.keyId(l)
                }
                return a.waiting_kid++,
                    o.then((function (l) {
                        return a.key_promises[l] = i,
                            a.waiting_kid--,
                        u && (a.signer_aads[l] = u),
                        t && (a.signer_headers[l] = t),
                            l
                    }))
            },
            i.Signer.prototype.addSignature = function (l, n, u) {
                if (f.isString(l) && (l = JSON.parse(l)), l.payload && f.isString(l.payload) && l.protected && f.isString(l.protected) && l.header && l.header instanceof Object && l.signature && f.isString(l.signature)) return this.sign(g.fromObject(l), n, u);
                throw new Error('JWS is not a valid JWS object')
            },
            i.Signer.prototype.sign = function (l, n, u) {
                var e = this,
                    t = [
                    ];
                if (0 === Object.keys(e.key_promises).length) throw new Error('No signers defined. At least one is required to sign the JWS.');
                if (e.waiting_kid) throw new Error('still generating key IDs');
                for (var i in e.key_promises) e.key_promises.hasOwnProperty(i) && t.push(i);
                return function l(n, u, t, i, r) {
                    if (r.length) {
                        var o = r.shift(),
                            a = function (l, n, u, t, i) {
                                var r;
                                if (n || (n = {
                                }), n.alg || (n.alg = e.cryptographer.getContentSignAlgorithm(), n.typ = 'JWT'), n.kid || (n.kid = i), f.isString(l)) r = f.arrayFromUtf8String(l);
                                else try {
                                    r = f.arrayish(l)
                                } catch (o) {
                                    if (l instanceof g) r = f.arrayFromString(f.Base64Url.decode(l.payload));
                                    else {
                                        if (!(l instanceof Object)) throw new Error('cannot sign this message');
                                        r = f.arrayFromUtf8String(JSON.stringify(l))
                                    }
                                }
                                return e.cryptographer.sign(n, r, t).then((function (e) {
                                    var t = new g(n, u, r, e);
                                    return l instanceof g ? (delete t.payload, l.signatures ? l.signatures.push(t) : l.signatures = [
                                        t
                                    ], l) : t
                                }))
                            }(n, e.signer_aads[o] || u, e.signer_headers[o] || t, i[o], o);
                        return r.length && (a = a.then((function (n) {
                            return l(n, null, null, i, r)
                        }))),
                            a
                    }
                }(l, n, u, e.key_promises, t)
            };
        var g = function (l, n, u, e) {
            this.header = n,
                this.payload = f.Base64Url.encodeArray(u),
            e && (this.signature = f.Base64Url.encodeArray(e)),
                this.protected = f.Base64Url.encode(JSON.stringify(l))
        };
        g.fromObject = function (l) {
            var n = new g(l.protected, l.header, l.payload, null);
            return n.signature = l.signature,
                n.signatures = l.signatures,
                n
        },
            g.prototype.JsonSerialize = function () {
                return JSON.stringify(this)
            },
            g.prototype.CompactSerialize = function () {
                return this.protected + '.' + this.payload + '.' + this.signature
            },
            i.Verifier = function (l, n, u) {
                var t,
                    i,
                    r,
                    o,
                    a,
                    s,
                    c;
                if (this.cryptographer = l, t = l.getContentSignAlgorithm(), this.cryptographer = new e.WebCryptographer, f.isString(n)) if (i = /^([0-9a-z_\-]+)\.([0-9a-z_\-]+)\.([0-9a-z_\-]+)$/i.exec(n)) {
                    if (4 != i.length) throw new Error('wrong JWS compact serialization format');
                    n = {
                        protected: i[1],
                        payload: i[2],
                        signature: i[3]
                    }
                } else n = JSON.parse(n);
                else if ('object' != typeof n) throw new Error('data format not supported');
                r = n.protected,
                    o = n.header,
                    a = n.payload,
                    (s = n.signatures instanceof Array ? n.signatures.slice(0) : [
                    ]).forEach((function (l) {
                        l.aad = l.protected,
                            l.protected = JSON.parse(f.Base64Url.decode(l.protected))
                    })),
                    this.aad = r,
                    c = f.Base64Url.decode(r);
                try {
                    c = JSON.parse(c)
                } catch (p) {
                }
                if (!c && !o) throw new Error('at least one header is required');
                if (!c.alg) throw new Error('\'alg\' is a mandatory header');
                if (c.alg != t) throw new Error('the alg header \'' + c.alg + '\' doesn\'t match the requested algorithm \'' + t + '\'');
                if (c && c.typ && 'JWT' != c.typ) throw new Error('typ \'' + c.typ + '\' not supported');
                n.signature && s.unshift({
                    aad: r,
                    protected: c,
                    header: o,
                    signature: n.signature
                }),
                    this.signatures = [
                    ];
                for (var d = 0; d < s.length; d++) this.signatures[d] = JSON.parse(JSON.stringify(s[d])),
                    this.signatures[d].signature = f.arrayFromString(f.Base64Url.decode(s[d].signature));
                this.payload = a,
                    this.key_promises = {
                    },
                    this.waiting_kid = 0,
                u && (this.keyfinder = u)
            },
            i.Verifier.prototype.addRecipient = function (l, n, u) {
                var t,
                    i = this,
                    r = f.isCryptoKey(l) ? new Promise((function (n) {
                        n(l)
                    })) : e.Utils.importRsaPublicKey(l, u || i.cryptographer.getContentSignAlgorithm(), 'verify');
                if (n) t = new Promise((function (l) {
                    l(n)
                }));
                else {
                    if (f.isCryptoKey(l)) throw new Error('key_id is a mandatory argument when the key is a CryptoKey');
                    console.log('it\'s not safe to not pass a key_id'),
                        t = e.WebCryptographer.keyId(l)
                }
                return i.waiting_kid++,
                    t.then((function (l) {
                        return i.key_promises[l] = r,
                            i.waiting_kid--,
                            l
                    }))
            },
            i.Verifier.prototype.verify = function () {
                var l = this,
                    n = l.signatures,
                    u = l.key_promises,
                    e = l.keyfinder,
                    t = [
                    ];
                if (!(e || Object.keys(l.key_promises).length > 0)) throw new Error('No recipients defined. At least one is required to verify the JWS.');
                if (l.waiting_kid) throw new Error('still generating key IDs');
                return n.forEach((function (n) {
                    var i = n.protected.kid;
                    e && (u[i] = e(i)),
                        t.push(l.cryptographer.verify(n.aad, l.payload, n.signature, u[i], i).then((function (n) {
                            return n.verified && (n.payload = f.Base64Url.decode(l.payload)),
                                n
                        })))
                })),
                    Promise.all(t)
            }
    }

    // 24798
    const z_ = function () {
        function l() {
        }
        return l.encode = function (n, u) {
            void 0 === u && (u = !1);
            var e = Object(G_.encode) (n.buffer);
            return u && (e = l.toBase64Url(e)),
                e
        },
            l.decode = function (n, u) {
                void 0 === u && (u = !1);
                var e = n;
                return u && (e = l.toBase64(e)),
                    new Uint8Array(Object(G_.decode) (e))
            },
            l.decodeToUTF8String = function (n) {
                return decodeURIComponent(atob(n).split('').map(l.toUTF8Char).join(''))
            },
            l.isBase64url = function (l) {
                return !(!l.includes('-') && !l.includes('_'))
            },
            l.toBase64Url = function (l) {
                return l.replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
            },
            l.toBase64 = function (l) {
                for (var n = l.length % 4, u = n ? 4 - n : n, e = l.replace(/-/g, '+').replace(/_/g, '/'), t = 0; t < u; t++) e += '=';
                return e
            },
            l.toUTF8Char = function (l) {
                return '%' + ('00' + l.charCodeAt(0).toString(16)).slice( - 2)
            },
            l
    }()

    // 24831
    const B_ = function () {
        function l(l) {
            void 0 === l && (l = crypto),
                this.cryptoLib = l,
                this._cryptographer = new U_.Jose.WebCryptographer
        }
        // == cypler.generateKeyPair
        return l.prototype.generate = function (l, n, u) {
            var e = this;
            return void 0 === l && (l = 'RSA-OAEP'),
            void 0 === n && (n = 'SHA-256'),
            void 0 === u && (u = 1024),
                Q(this.cryptoLib.subtle.generateKey({
                    name: l,
                    modulusLength: u,
                    publicExponent: new Uint8Array([1,
                        0,
                        1]),
                    hash: {
                        name: n
                    }
                }, !0, [
                    'decrypt'
                ]).then((function (l) {
                    return Promise.all([e.cryptoLib.subtle.exportKey('jwk', l.privateKey),
                        e.cryptoLib.subtle.exportKey('jwk', l.publicKey)])
                })).then((function (l) {
                    return {
                        private: Object.freeze({
                            kty: l[0].kty,
                            n: l[0].n,
                            e: l[0].e,
                            d: l[0].d,
                            p: l[0].p,
                            q: l[0].q,
                            dp: l[0].dp,
                            dq: l[0].dq,
                            qi: l[0].qi
                        }),
                        public: Object.freeze({
                            kty: l[1].kty,
                            n: l[1].n,
                            e: l[1].e
                        })
                    }
                })))
        },
            l.prototype.sanitizeKey = function (l) {
                return Object.freeze(Object.assign({
                }, l, {
                    n: this._trimLeadingZeros(l.n)
                }))
            },
            l.prototype.encrypt = function (l, n) { // VB: main decrypt fn
                var u = U_.Jose.Utils.importRsaPublicKey(Object.assign({
                }, n), n.alg);
                return Q(new U_.JoseJWE.Encrypter(this._cryptographer, u).encrypt(l))
            },
            l.prototype.sign = function (l, n) {
                var u = new U_.JoseJWS.Signer(this._cryptographer);
                return Q(u.addSigner(Object.assign({
                }, n), n.kid).then((function () {
                    return u.sign(l)
                })).then((function (l) {
                    //             g.prototype.CompactSerialize = function () {
                    //                 return this.protected + '.' + this.payload + '.' + this.signature
                    //             },
                    return l.CompactSerialize()
                })))
            },
            l.prototype.decrypt = function (l, n) {
                var u = JSON.parse(z_.decodeToUTF8String(l.split('.') [0])),
                    e = U_.Jose.Utils.importRsaPrivateKey(Object.assign({
                    }, n), u.alg);
                return Q(new U_.JoseJWE.Decrypter(this._cryptographer, e).decrypt(l))
            },
            l.prototype.verify = function (l, n) {
                var u = new U_.JoseJWS.Verifier(this._cryptographer, l);
                return Q(u.addRecipient(Object.assign({
                }, n), n.kid).then((function () {
                    return u.verify()
                })).then((function (l) {
                    return l && l[0] ? l[0].payload : null
                })))
            },
            l.prototype._trimLeadingZeros = function (l) {
                if (null == l) return l;
                for (var n = z_.decode(l, !0), u = 0; u < n.length && 0 === n[u]; ) u++;
                return n = n.slice(u),
                    z_.encode(n, !0)
            },
            l
    }();

    // 24920
    const H_ = function () {
        function l() {
        }
        return l._keyEncryptBase64ReverseChangePosition = function (l, n, u) {
            for (var e = btoa(l), t = (e = e.split('').reverse().join('')) [n], i = e[u], r = 0; r < e.length; r++) {
                var o = e[r];
                o === t ? e = this.setCharAt(e, r, i) : o === i && (e = this.setCharAt(e, r, t))
            }
            return e
        },
            l._keyDecryptChangePositionReverseBase64 = function (l, n, u) {
                for (var e = l[n], t = l[u], i = 0; i < l.length; i++) {
                    var r = l[i];
                    r === e ? l = this.setCharAt(l, i, t) : r === t && (l = this.setCharAt(l, i, e))
                }
                var o = l.split('').reverse().join('');
                return atob(o)
            },
            l.setCharAt = function (l, n, u) {
                return n > l.length - 1 ? l : l.substr(0, n) + u + l.substr(n + 1)
            },
            l
    }()

    exports.helpers = {
        f,
        importRsaPrivateKey,
        G_,
        U_,
        B_,
        z_
    };

}('undefined' !== typeof exports && exports || 'undefined' !== typeof window && window || global));

