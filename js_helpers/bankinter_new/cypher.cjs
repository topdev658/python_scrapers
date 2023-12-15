// var crypto = require('crypto').webcrypto;

(function (exports) {
    'use strict';
    const crypto = require('crypto').webcrypto;
    const {Jose} = require('./jose.min.js');  // jose-jwe

    var cryptographer = new Jose.WebCryptographer();
    cryptographer.setContentSignAlgorithm("RS256");

    const toUTF8Char = (l) => "%" + ("00" + l.charCodeAt(0).toString(16)).slice(-2);
    const decodeToUTF8String = (n) => decodeURIComponent(atob(n).split("").map(toUTF8Char).join(""));


    //                         l.prototype.sanitizeKey = function (l) {
    //                             return Object.freeze(Object.assign({
    //                             }, l, {
    //                                 n: this._trimLeadingZeros(l.n)
    //                             }))
    //                         },
    //                         l.prototype.encrypt = function (l, n) { // VB: main decrypt fn
    //                             var u = U_.Jose.Utils.importRsaPublicKey(Object.assign({
    //                             }, n), n.alg);
    //                             return Q(new U_.JoseJWE.Encrypter(this._cryptographer, u).encrypt(l))
    //                         },
    //                         l.prototype.sign = function (l, n) {
    //                             var u = new U_.JoseJWS.Signer(this._cryptographer);
    //                             return Q(u.addSigner(Object.assign({
    //                             }, n), n.kid).then((function () {
    //                                 return u.sign(l)
    //                             })).then((function (l) {
    //                                 return l.CompactSerialize()
    //                             })))
    //                         },
    //                         l.prototype.decrypt = function (l, n) {
    //                             var u = JSON.parse(z_.decodeToUTF8String(l.split('.') [0])),
    //                                 e = U_.Jose.Utils.importRsaPrivateKey(Object.assign({
    //                                 }, n), u.alg);
    //                             return Q(new U_.JoseJWE.Decrypter(this._cryptographer, e).decrypt(l))
    //                         },
    //                         l.prototype.verify = function (l, n) {
    //                             var u = new U_.JoseJWS.Verifier(this._cryptographer, l);
    //                             return Q(u.addRecipient(Object.assign({
    //                             }, n), n.kid).then((function () {
    //                                 return u.verify()
    //                             })).then((function (l) {
    //                                 return l && l[0] ? l[0].payload : null
    //                             })))
    //                         },
    //                         l.prototype._trimLeadingZeros = function (l) {
    //                             if (null == l) return l;
    //                             for (var n = z_.decode(l, !0), u = 0; u < n.length && 0 === n[u]; ) u++;
    //                             return n = n.slice(u),
    //                                 z_.encode(n, !0)
    //                         },
    //                         l
    //                 }(),

    // parts of B_

    // 24896
    /**
     *
     * @param {String} msg
     * @param {Object} rsaPrivObj
     * @returns {Promise<string>}
     */
    const decrypt = function (msg, rsaPrivObj) {
        let u = JSON.parse(decodeToUTF8String(msg.split('.') [0])),
            rsaPrivKey = Jose.Utils.importRsaPrivateKey(Object.assign({
            }, rsaPrivObj), u.alg);
        return new Jose.JoseJWE.Decrypter(cryptographer, rsaPrivKey).decrypt(msg)
    }

    // 24883
    /**
     *
     * @param {String} msg
     * @param {Object} rsaPubObj
     * @returns {Promise<string>}
     */
    const encrypt = function (msg, rsaPubObj) { // VB: main decrypt fn
        var rsaPubKey = Jose.Utils.importRsaPublicKey(Object.assign({
        }, rsaPubObj), rsaPubObj.alg);
        return new Jose.JoseJWE.Encrypter(cryptographer, rsaPubKey).encrypt(msg)
    }

    // 24888
    /**
     *
     * @param {String} msg
     * @param {Object} rsaPrivObj
     * @returns {*}
     */
    const sign = function (msg, rsaPrivObj) {
        var signer = new Jose.JoseJWS.Signer(cryptographer);
        return signer.addSigner(Object.assign({}, rsaPrivObj), rsaPrivObj.kid).then((function () {
            return signer.sign(msg)
        })).then((function (l) {
            return l.CompactSerialize()
        }))
    }

    const decryptExample = function(pubKeyObj) {
        var cryptographer = new Jose.WebCryptographer();
        // {
        //     n:
        //         "c2:4b:af:0f:2d:2b:ad:36:72:a7:91:0f:ee:30:a0:95:d5:3a:46:82:86:96:7e:42:c6:fe:8f:20:97:af:49:f6:48:a3:91:53:ac:2e:e6:ec:9a:9a:e0:0a:fb:1c:db:44:40:5b:8c:fc:d5:1c:cb:b6:9b:60:c0:a8:ac:06:f1:6b:29:5e:2f:7b:09:d9:93:32:da:3f:db:53:9c:2e:ea:3b:41:7f:6b:c9:7b:88:9f:2e:c5:dd:42:1e:7f:8f:04:f6:60:3c:fe:43:6d:32:10:ce:8d:99:cb:76:f7:10:97:05:af:28:1e:39:0f:78:35:50:7b:8e:28:22:a4:7d:11:51:22:d1:0e:ab:6b:6f:96:cb:cf:7d:eb:c6:aa:a2:6a:2e:97:2a:93:af:a5:89:e6:c8:bc:9f:fd:85:2b:0f:b4:c0:e4:ca:b5:a7:9a:01:05:81:93:6b:f5:8d:1c:f7:f3:77:0e:6e:53:34:92:0f:48:21:34:33:44:14:5e:4a:00:41:3a:7d:cb:38:82:c1:65:e0:79:ea:a1:05:84:b2:6e:40:19:77:1a:0e:38:4b:28:1f:34:b5:cb:ac:c5:2f:58:51:d7:ec:a8:08:0e:7c:c0:20:c1:5e:a1:4d:b1:30:17:63:0e:e7:58:8e:7f:6e:9f:a4:77:8b:1e:a2:d2:2e:1b:e9",
        //     e: 65537
        // },
        var rsa_key = Jose.Utils.importRsaPublicKey(pubKeyObj, "RSA-OAEP");
        var encrypter = new Jose.JoseJWE.Encrypter(cryptographer, rsa_key);
        encrypter
            .encrypt("hello world")
            .then(function(result) {
                console.log(result);
            })
            .catch(function(err) {
                console.error(err);
            });
    }

    // REQ: 25428
    // var yw = function () {
    //         function l(l, n) {
    //             var u;
    //             this._callback = n;
    //             try {
    //                 u = JSON.stringify(l)
    //             } catch (e) {
    //                 u = l.toString()
    //             }
    //             // u = '{"answers":[{"id":"a5a20vMMGlJxaf7","challengeType":"USER","pattern":"KD(1647727898313;tag:INPUT;id:a5a20vMMGlJxaf7;mod:2;code:17)KD(378;code:86)KU(44;code:86)KU(99;mod:0;code:17)","challengeAnswer":"B09417932"},{"id":"107fz91kln1iiMK","challengeType":"PASSWORD","pattern":"KD(1647727905782;tag:INPUT;id:107fz91kln1iiMK;mod:2;code:17)KD(174)KU(56)KU(96;mod:0;code:17)","challengeAnswer":"27787a75bf952449e44e6fbbba473bd1e86227ed721ad52022b0eada87347b2c"}],"backToPrevious":false}'
    //             this._obs = is(u) // observable
    //         }
    //         return l.prototype.encrypt = function (l) {
    //             return this._obs = this._obs.pipe(function (l) {
    //                 // enhanced key from handshake resp decrypted
    //                 // l = {
    //                 //     "kty": "RSA",
    //                 //     "kid": "server_d2710IA24M4PJqCPMOQieWCYbpWS8LDHkCZAt",
    //                 //     "n": "lVAAa_OGh8mQARR0-NIKpXw7JPfS2sLvcgeoiAVAghoNEaoRbNjdriqYiGF_4geLGIvYPRwOFWHD9gSJmB-utW1m9bTAv2V_WRKEnIewleqndD2sx7TKLvwWTgAw60Qpo3irPPtc3w_7BTqnkV2TXp_bZNzsJcyrILVvCDFkaftPRSgcZRoimrmg7yvpUnm6RUJANd95_RguPrf2xg4rSr6XQjEF-tAY4Grm5_vxwjnHVX9JdaLQQxYJY3lbXtzkKNubvHALAD93XXOJ2jYgZHywrjtb1jY4cE3d5rnnSTLpGc78dRhHUHYZkXPQ-_CceVfNhDFYPGnHBIWJV-YD0Q",
    //                 //     "e": "AQAB",
    //                 //     "alg": "RSA-OAEP"
    //                 // }
    //
    //                 // n = '{"answers":[{"id":"a5a20vMMGlJxaf7","challengeType":"USER","pattern":"KD(1647727898313;tag:INPUT;id:a5a20vMMGlJxaf7;mod:2;code:17)KD(378;code:86)KU(44;code:86)KU(99;mod:0;code:17)","challengeAnswer":"B09417932"},{"id":"107fz91kln1iiMK","challengeType":"PASSWORD","pattern":"KD(1647727905782;tag:INPUT;id:107fz91kln1iiMK;mod:2;code:17)KD(174)KU(56)KU(96;mod:0;code:17)","challengeAnswer":"27787a75bf952449e44e6fbbba473bd1e86227ed721ad52022b0eada87347b2c"}],"backToPrevious":false}'
    //                 return Gs((function (n) {
    //                     return encrypt(n, 'function' == typeof l ? l(n) : l)
    //                 }))
    //             }(l)),
    //                 this
    //         },
    //             l.prototype.sign = function (l) {
    //                 return this._obs = this._obs.pipe(function (l) {
    //                     // client generated private key
    //                     // l = {
    //                     //     "kty": "RSA",
    //                     //     "n": "mxmAF3AhYEdtqaaDi7P-MHuoZMdAo_T3zVvgg-9SbBVfLH1_75YXjtYfYgLF6PYb7MwG8tEzqMymRXDVSX_GweaWrvM0yz6qPoMJ3ZQBcpS9KPJ_m2lVRdaQNsdyB5ElmHA7zDgssIapMvxQfV2bKPh7HHFIiZdMXHH5oFn4wJs",
    //                     //     "e": "AQAB",
    //                     //     "d": "KYS0gNGv5Y2JYhIkgZe_sivQApZCDAHN-eef3MGKT0uTTB4WSsTjboWMJhj28Ks9A3EEZSiySvvpgIo5VjEBu8h2o8tkZwwJTIwlWfBchJtbpAbttBKv0qH1yBYeoZKdDHm1OMFQUOkX9o6r7v5Nn8Uma1kcWDeA5hVP8c5mB8E",
    //                     //     "p": "yIG1ztRDEWPw6EKWxJVAzy91RLGDj5pSqOD5dNPW3AO4EKfRdl_GPgRTRB1f90itEfgwLoRT3uJm3EcuICWFQQ",
    //                     //     "q": "xgacUeyPfuu4YJQZpNuG3lW9-QhD7ZtD73bW8dEV3IeetiiYZ4gNA8cL_3YXUYxgu51VwWGKC0-iL8qUg0VC2w",
    //                     //     "dp": "pxzkyPPEylO_z_Tf8AxtrcDiPlStUBzRVAveHe8JnupCmS8lt0Fv2vSD6buJ5nJePSHcFokX1iZgkKuK2CQtgQ",
    //                     //     "dq": "uwuddeh7dggTJO5e9pAA6VuV0HdVKkchOTxINSsoeiCD8k2P_yLMIEhP9eHGjtmIuU4YpUuLh7mVWY0BEKlIRw",
    //                     //     "qi": "FRmaoZNZ7MARl36PgcnmViI7g_IAGs8x-GGaxjeeDl4dwRRFz54BgQHvnv-QDWmJVoEY37rGRURyHwCIo4zmxw",
    //                     //     "alg": "RS256"
    //                     // }
    //
    //                     // n = '{"answers":[{"id":"a5a20vMMGlJxaf7","challengeType":"USER","pattern":"KD(1647727898313;tag:INPUT;id:a5a20vMMGlJxaf7;mod:2;code:17)KD(378;code:86)KU(44;code:86)KU(99;mod:0;code:17)","challengeAnswer":"B09417932"},{"id":"107fz91kln1iiMK","challengeType":"PASSWORD","pattern":"KD(1647727905782;tag:INPUT;id:107fz91kln1iiMK;mod:2;code:17)KD(174)KU(56)KU(96;mod:0;code:17)","challengeAnswer":"27787a75bf952449e44e6fbbba473bd1e86227ed721ad52022b0eada87347b2c"}],"backToPrevious":false}'
    //                     return Gs((function (n) {
    //                         return sign(n, 'function' == typeof l ? l(n) : l)
    //                     }))
    //                 }(l)),
    //                     this
    //             },
    //             l.prototype.execute = function () {
    //                 var l = this;
    //                 return this._obs.pipe(Gs((function (n) {
    //                     return l._callback(n)
    //                 })))
    //             },
    //             l
    //     }()

    // return l.prototype.encrypt = function (l) {
    //     return this._obs = this._obs.pipe(function (l) {
    //         // enhanced key from handshake resp decrypted
    //         // l = {
    //         //     "kty": "RSA",
    //         //     "kid": "server_d2710IA24M4PJqCPMOQieWCYbpWS8LDHkCZAt",
    //         //     "n": "lVAAa_OGh8mQARR0-NIKpXw7JPfS2sLvcgeoiAVAghoNEaoRbNjdriqYiGF_4geLGIvYPRwOFWHD9gSJmB-utW1m9bTAv2V_WRKEnIewleqndD2sx7TKLvwWTgAw60Qpo3irPPtc3w_7BTqnkV2TXp_bZNzsJcyrILVvCDFkaftPRSgcZRoimrmg7yvpUnm6RUJANd95_RguPrf2xg4rSr6XQjEF-tAY4Grm5_vxwjnHVX9JdaLQQxYJY3lbXtzkKNubvHALAD93XXOJ2jYgZHywrjtb1jY4cE3d5rnnSTLpGc78dRhHUHYZkXPQ-_CceVfNhDFYPGnHBIWJV-YD0Q",
    //         //     "e": "AQAB",
    //         //     "alg": "RSA-OAEP"
    //         // }
    //
    //         // n = '{"answers":[{"id":"a5a20vMMGlJxaf7","challengeType":"USER","pattern":"KD(1647727898313;tag:INPUT;id:a5a20vMMGlJxaf7;mod:2;code:17)KD(378;code:86)KU(44;code:86)KU(99;mod:0;code:17)","challengeAnswer":"B09417932"},{"id":"107fz91kln1iiMK","challengeType":"PASSWORD","pattern":"KD(1647727905782;tag:INPUT;id:107fz91kln1iiMK;mod:2;code:17)KD(174)KU(56)KU(96;mod:0;code:17)","challengeAnswer":"27787a75bf952449e44e6fbbba473bd1e86227ed721ad52022b0eada87347b2c"}],"backToPrevious":false}'
    //         return Gs((function (n) {
    //             return encrypt(n, 'function' == typeof l ? l(n) : l)
    //         }))
    //     }(l)),
    //         this
    // },

    // 25439
    /**
     *
     * @param msgSigned {String}
     * @param rsaPubObj {Object}
     * @returns {Promise<string>}
     */
    const encryptReq = function (msgSigned, rsaPubObj) {
        return encrypt(msgSigned, rsaPubObj)
    }


    // l.prototype.sign = function (l) {
    //     return this._obs = this._obs.pipe(function (l) {
    //         // client generated private key
    //         // l = {
    //         //     "kty": "RSA",
    //         //     "n": "mxmAF3AhYEdtqaaDi7P-MHuoZMdAo_T3zVvgg-9SbBVfLH1_75YXjtYfYgLF6PYb7MwG8tEzqMymRXDVSX_GweaWrvM0yz6qPoMJ3ZQBcpS9KPJ_m2lVRdaQNsdyB5ElmHA7zDgssIapMvxQfV2bKPh7HHFIiZdMXHH5oFn4wJs",
    //         //     "e": "AQAB",
    //         //     "d": "KYS0gNGv5Y2JYhIkgZe_sivQApZCDAHN-eef3MGKT0uTTB4WSsTjboWMJhj28Ks9A3EEZSiySvvpgIo5VjEBu8h2o8tkZwwJTIwlWfBchJtbpAbttBKv0qH1yBYeoZKdDHm1OMFQUOkX9o6r7v5Nn8Uma1kcWDeA5hVP8c5mB8E",
    //         //     "p": "yIG1ztRDEWPw6EKWxJVAzy91RLGDj5pSqOD5dNPW3AO4EKfRdl_GPgRTRB1f90itEfgwLoRT3uJm3EcuICWFQQ",
    //         //     "q": "xgacUeyPfuu4YJQZpNuG3lW9-QhD7ZtD73bW8dEV3IeetiiYZ4gNA8cL_3YXUYxgu51VwWGKC0-iL8qUg0VC2w",
    //         //     "dp": "pxzkyPPEylO_z_Tf8AxtrcDiPlStUBzRVAveHe8JnupCmS8lt0Fv2vSD6buJ5nJePSHcFokX1iZgkKuK2CQtgQ",
    //         //     "dq": "uwuddeh7dggTJO5e9pAA6VuV0HdVKkchOTxINSsoeiCD8k2P_yLMIEhP9eHGjtmIuU4YpUuLh7mVWY0BEKlIRw",
    //         //     "qi": "FRmaoZNZ7MARl36PgcnmViI7g_IAGs8x-GGaxjeeDl4dwRRFz54BgQHvnv-QDWmJVoEY37rGRURyHwCIo4zmxw",
    //         //     "alg": "RS256"
    //         // }
    //
    //         // n = '{"answers":[{"id":"a5a20vMMGlJxaf7","challengeType":"USER","pattern":"KD(1647727898313;tag:INPUT;id:a5a20vMMGlJxaf7;mod:2;code:17)KD(378;code:86)KU(44;code:86)KU(99;mod:0;code:17)","challengeAnswer":"B09417932"},{"id":"107fz91kln1iiMK","challengeType":"PASSWORD","pattern":"KD(1647727905782;tag:INPUT;id:107fz91kln1iiMK;mod:2;code:17)KD(174)KU(56)KU(96;mod:0;code:17)","challengeAnswer":"27787a75bf952449e44e6fbbba473bd1e86227ed721ad52022b0eada87347b2c"}],"backToPrevious":false}'
    //         return Gs((function (n) {
    //             return sign(n, 'function' == typeof l ? l(n) : l)
    //         }))
    //     }(l)),
    //         this
    // },

    // 25447
    const signReq = function (msgObj, rasPrivObj) {
        let msg = JSON.stringify(msgObj);
        return sign(msg, rasPrivObj)
    }

    // 50337
    const enhanceClientKey = function (l) {
        return Object.assign({
        }, l, {
            alg: 'RS256'
        })
    }

    // 50343
    const enhanceServerKey = function (l) {
        return Object.assign({
        }, l, {
            alg: 'RSA-OAEP'
        })
    }


    // 50297, for DEV
    const updateChallengeAnswersRaw = function (l, n, u, e) {
        // this = {service: baseUrl: "/seguridad/api/authorization/v0"}...

        //
        // l = {
        //     "id": "76f6PkCuqC8TQWareQvd5HptSUnwd9fDl5p5r",
        //     "interactionId": "9c08c799a6f9d1c5",
        //     "type": "ACCESS",
        //     "flow": "DEFAULT",
        //     "status": "PENDING",
        //     "validUntil": "2022-03-19T21:02:34",
        //     "visualizationData": {
        //         "theme": "companiesbanking"
        //     },
        //     "identificationData": {
        //         "clientData": {
        //             "clientId": "empresas-web",
        //             "displayName": "empresas-web"
        //         },
        //         "secondClientData": {}
        //     },
        //     "integrationData": {
        //         "system": "CA",
        //         "caSessionId": "a1a1b51a-3b87-470d-935c-a68623026461"
        //     },
        //     "challenges": [
        //         {
        //             "challengeType": "USER",
        //             "id": "694bHVWxMCLenXr",
        //             "challengeStatus": "PENDING"
        //         },
        //         {
        //             "challengeType": "PASSWORD",
        //             "id": "5a8dmt0S5zxbfPA",
        //             "challengeStatus": "PENDING",
        //             "challengeMethod": "SALTED_SHA256_SHA1",
        //             "challengeSeed": "yi9VQEfL8lnHuadckBdaMokUnDu7WxmFHMR5yFlQsprSNPGwWyM0OGjduzmTRIQb"
        //         }
        //     ],
        //     "consents": [],
        //     "additionalInfo": {},
        //     "messages": [],
        //     "existsAdditionalConsents": false,
        //     "backAllowed": false,
        //     "allowedFlowPreferences": [
        //         "REACTIVATION_WITH_IDDOCS"
        //     ]
        // }

        // username, userpass
        // n = {
        //     "answers": [
        //         {
        //             "id": "694bHVWxMCLenXr",
        //             "challengeType": "USER",
        //             "pattern": "KD(1647723645041;tag:INPUT;id:694bHVWxMCLenXr;mod:2;code:17)KD(154;code:86)KU(69;code:86)KU(115;mod:0;code:17)",
        //             "challengeAnswer": "B09417932"
        //         },
        //         {
        //             "id": "5a8dmt0S5zxbfPA",
        //             "challengeType": "PASSWORD",
        //             "pattern": "KD(1647723675222;tag:INPUT;id:5a8dmt0S5zxbfPA;mod:2;code:17)KD(372)KU(170)KU(33;mod:0;code:17)",
        //             "challengeAnswer": "e2754dabd916fa8acd4cb1d1e12cb26eae6031c477cad18149813f59fca9ee2e"
        //         }
        //     ],
        //     "backToPrevious": false
        // }

        // client generated private key
        // u = {
        //     "kty": "RSA",
        //     "n": "vmvj2edCo9DUrelSflnX6g97pzVZOIv1ZHC4WQuzy_5xS-xffKaP-LND02rGDvKvGJVBgTEIcSG1_VVRE-8cP_kxN-HfTt5MUOIG236pLwVIxBO8-xPI8YQmgsYlv3aEU1bw1FIxE-AtpNTzik-pmEvy8ucNJLkDyXbXQw5G71s",
        //     "e": "AQAB",
        //     "d": "WRlQhuAPrWkEas-Wuuo8_hb6i9WJhszuKG4ZxAiWu2e2CYlzcHbbPMpcfSsju1DQnxcPjGyt_4l_hycJheNG-tSDwpnBZ25f3xKz6AFIxKf4q_pZoJ642AsSTEjbGIQG9rQdrMLZjx-6T7qu5SkPfBtI0apVtV8VrZmfI05r5OE",
        //     "p": "8wKq6b926C6p9wgaX1HG_aqBlecqp4aFE0Y7n5SWCd_b-wBc9GX-9joMFLfT8KYRrBkUAa8i70TmIvtC9y3JSw",
        //     "q": "yJmZhU96MgMgNI9y_2T7LcAapSAhe1UkdFRVLs25uS8O6-b5rbvWhDUaENjtshC_hzloqHJarIa5MPlexZE4MQ",
        //     "dp": "ZMltc2bqfR-ldIRS08fJ_TkzZ6WppjN_i9_sKKJqnAvRY8fhxadr2Fl42zrm1v85gyQfjRdDKPNtc4K8YmIGAw",
        //     "dq": "laL2gRobRelNAcgr-VVjhOozNg_0yeJmUhyCempd60SuNczTXQSsbWyLKBwZm2Wg6YcqidTbzKymwmCSkH_WUQ",
        //     "qi": "OvFD2Vb1_rWlUlmLDFKY2le3abhIeh_rvEeaLotZixZ5PH6qg8N0RSDhXDDLTEl1TxLuEOSO2CfDTlYhADtOWg"
        // }

        // key from handshake resp decrypted
        // e = {
        //     "kty": "RSA",
        //     "kid": "server_76f6PkCuqC8TQWareQvd5HptSUnwd9fDl5p5r",
        //     "n": "6fSUjFPu5xWxWTvqttq0v23wcZ2lXf-lVXsLtHTDLC4KK3Z7dWS0JIW9nKJy7q7VlQT38Z48CQqWpvY5ZsDmeSKKZ871CWYKk1HyG0u2bxTIT5_geNIte2EPrveTbHi1GcY9Yvk4hdlLKTiRWVLmL5IerK9xsJMX52UBbNIHHgCEXc6MkvWwkdI772mE-x0vyNpsE-dQML16ew3oubuT_2KJRX0_efRvovFY_IPLA6tiKl8gRaDpIQGkQh_qjRmvBPm0MolGTtWA0VpLEOvd4w6psCJsqq2BtUu8yV8Wl6TEChiyo3YlanpCGNAfyht-jz47lx2O4VgLpPP38FS6iQ",
        //     "e": "AQAB"
        // }

        // 49533, see helpers_obf:  l.prototype.sign = function (l, n)
        // REAL PIPE
        // 1. encrypt stringify json answer with enhanced key from handshake resp decrypted
        // 2. sign stringify json answer with client generated private key
        return this._service.updateChallengeAnswers(l.id, n) // compose req
            .sign(enhanceClientKey(u))
            .encrypt(enhanceServerKey(e))
            .execute()
            .pipe(Gs((function (l) {return l.decrypt(u).verify(e).execute()
            })))
    }

    // 49533
    // REAL PIPE (see updateChallengeAnswersRaw)
    // 1. encrypt stringify json answer with enhanced key from handshake resp decrypted
    // 2. sign stringify json answer with client generated private key
    // updateChallengeAnswers -> signEncryptReq
    const signEncryptReq = async (msgObj, clientPrivKeyObj, serverPubKeyObj) => {
        let msgSig = await signReq(msgObj, enhanceClientKey(clientPrivKeyObj))
        return await encryptReq(msgSig, enhanceServerKey(serverPubKeyObj))
    }

    /**
     * @returns {Object}
     */
    const algorithmRSA = {
        name: 'RSA-OAEP',
        modulusLength: 1024,
        publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
        hash: {name: 'SHA-256'},
    };

    const generateKeyPair = async () => {
        const keyPair = await crypto.subtle.generateKey(algorithmRSA, true, ['decrypt']);
        const publicKey = await crypto.subtle.exportKey('jwk', keyPair.publicKey);
        const privateKey = await crypto.subtle.exportKey('jwk', keyPair.privateKey);

        // [{
        //     key_ops: [ 'decrypt' ],
        //     ext: true,
        //     kty: 'RSA',
        //     n: 'nLUvrSi5s4T8dI4zQ5Hu2r7CiDm63-_rQKXhHCfgc8k4E342qZ5lpxhrK1X8J8s9T_GyflCD4xA-i3ed2EivRI_KZkz_Te_OjMbExY2IjATfjs7MtqM3VjKyfK-qU_IXdpG0FEyOBn99NLNvMPprnVDtc1k1ncFkrtN9z6CJ9q0',
        //     e: 'AQAB',
        //     d: 'avP6Yyttesmj6AT5lf9uztrtOD52fcpofIn6VtYcicnmvN8ifae-50lyM3SPEbXT1dE3KqDXMszucw-jqm8JNyeYag-CMrTRWHZoDCGXW0RyktCNsZ9LAOhNxKAEcIz2AVXBdhbLQ58bowlyyd2pnkIDNqNpDXlyqF-jPzTOJOE',
        //     p: 'zLIcGgBGrJg3Hcw8LroYshcJrnHjBNfjSnsaquTUSiiHF4SD6igLNDMCbYsSbYBWiyEKw2OkX7inx-RZo1kTdQ',
        //     q: 'w_wGLutxGr9xFQH6INTGjbTF372seJEF_t8Jne2ZVZr7y5oJVx8PpmMTMdfaNgTAZtzKcIo_7LzCBpIf26IHWQ',
        //     dp: 'f9BvT6UAfGEHeWm_4oV9SiaseurOEIYlfKplunPsQuoPgJXUMPAUHuIDEBeYyBss7u8Q43RifQq2aVCi0CacyQ',
        //     dq: 'wHh_8hBTUbt1aPY6GYgdPwmr0qHKAdYbF0UfgrPXBJVid3_dcGwWyIdAUJD1wltEQUDQp1l-khaGTkGve9lScQ',
        //     qi: 'SMcKKlVY_9XlKgJydVwVEYdXRdj4jus1DWW2PvkbEuI2cGVP2Rgx_f1XJ8dS1tql80im8nrtknQZCbkK9fuYAg',
        //     alg: 'RSA-OAEP-256'
        // }, ...
        // ]
        return {privateKey, publicKey};
    };

    exports.cypher = {
        generateKeyPair,
        decrypt,
        signEncryptReq
    };
}('undefined' !== typeof exports && exports || 'undefined' !== typeof window && window || global));


