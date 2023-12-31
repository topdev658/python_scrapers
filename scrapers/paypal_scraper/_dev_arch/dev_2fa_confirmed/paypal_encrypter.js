

var window = {
    screen: [24, 24, 900, 1600, 868, 1600],
    navigator: {
        userAgent: 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0'
    }
};

var PAYPAL = {};

function encrypt () {
    "use strict";

    function i(e) {
        for (var t = 0, n = 0; n < e.length; n++) t += e.charCodeAt(n);
        return t &= t
    }

    function s(e,t,n){"undefined"!=typeof e.removeEventListener?e.removeEventListener(t,n,!1):"undefined"!=typeof e.detachEvent&&e.detachEvent("on"+t,n)}
    function o(e,t,n){"undefined"!=typeof e.addEventListener?e.addEventListener(t,n,!1):"undefined"!=typeof e.attachEvent&&e.attachEvent("on"+t,n)}

    var e, t, n = {},

        r = (
            e = {
                idForHiddenField: null,
                isExceptionThrown: !1,
                startTime: (new Date).getTime()
            },
            t = {SC_VERSION: "2.0.1", syncStatus: "data"},
        {
            initSync: function (i) {
            try {
                // i = PAYPAL.ulSync = {
                //     fnSessionId: '533dd2c5b29546fd8e8fec415e607935',  // t.f = i.fnSessionId
                //     sourceId: 'UNIFIED_LOGIN_INPUT_PASSWORD',
                //     fname: 'fn_sync_data' // e.idForHiddenField = i.fname
                // }
                i = i || {},
                    e.startTime = i.tStamp || e.startTime,
                    e.idForHiddenField = i.fname,
                    t.f = i.fnSessionId,
                    t.s = i.sourceId,
                    t.chk = {},
                    t.chk.ts = e.startTime,
                    t.chk.eteid = n.chk.init(t.f, e.startTime.toString()), // VB: need to calc
                    t.chk.tts = (new Date).getTime() - t.chk.ts,
                    t.dc = JSON.stringify(function () {
                        var t, n = ["colorDepth", "pixelDepth", "height", "width", "availHeight", "availWidth"],
                            r = {screen: {}};
                        for (r.ua = window.navigator.userAgent, t = 0; t < n.length; t += 1) r.screen[n[t]] = window.screen[n[t]];
                        return r
                    }()),
                    n.ts.init(i)
                    , n.ms.init() // VB: temp disabled
            } catch (s) {
                e.isExceptionThrown = !0, t.err = s
            }
        },
        flushData: function () {
            try {
                var i = n.ts.get() || {},
                    s = n.ms.get();
                (i.ts1 || i.ts2 || s) && (t.d = t.d || {}, t.d.ts1 = i.ts1, t.d.ts2 = i.ts2, t.d.rDT = s),
                    // document.getElementsByName(e.idForHiddenField)[0].value = encodeURIComponent(JSON.stringify(t))
                    // VB:
                    console.log(encodeURIComponent(JSON.stringify(t)))
            } catch (o) {
                e.isExceptionThrown = !0
            }
        }
    }); // r


    n.report = function (e) {
        return n.err = n.err || {}, e += n.err
    }, Array.prototype.map || (Array.prototype.map = function (e) {
        var t, n, r;
        if (null == this) throw new TypeError("this is null or not defined");
        var i = Object(this), s = i.length >>> 0;
        if ("function" != typeof e) throw new TypeError(e + " is not a function");
        for (1 < arguments.length && (t = arguments[1]), n = new Array(s), r = 0; r < s;) {
            var o, u;
            r in i && (o = i[r], u = e.call(t, o, r, i), n[r] = u), r++
        }
        return n
    }), n.chk = function () {
        function e(e, t) {
            for (var n = 32, r = 0; 0 < n--;) e[0] += (e[1] << 4 ^ e[1] >> 5) + e[1] ^ r + t[3 & r], r += -1640531527, e[1] += (e[0] << 4 ^ e[0] >> 5) + e[0] ^ r + t[r >> 11 & 3]
        }

        function t(e) {
            for (var t = 0, n = 0; n < 4; n++) t |= e.charCodeAt(n) << 8 * n;
            return isNaN(t) ? 0 : t
        }

        return {
            init: function (r, i) {
                var s, o, u, a = new Array(2), l = new Array(8), c = new Array(4), p = 0, d = 0,
                    v = r.split("").map(function (e) {
                        return e.charCodeAt(0)
                    });
                for (d = 0; d < 4; d++) c[d] = t(i.slice(4 * d, 4 * (d + 1)));
                for (d = 0; d < v.length; d += 8) s = v, o = d, (u = a)[0] = (255 & (0 | s[o])) << 24 | (255 & (0 | s[o + 1])) << 16 | (255 & (0 | s[o + 2])) << 8 | 255 & (0 | s[o + 3]) | 0, u[1] = (255 & (0 | s[o + 4])) << 24 | (255 & (0 | s[o + 5])) << 16 | (255 & (0 | s[o + 6])) << 8 | 255 & (0 | s[o + 7]) | 0, e(a, c), l[p] = a[0], l[p + 1] = a[1], p += 2;
                return l
            }
        }
    }(),
        n.ts = function () {
        function r(e, t) {
            var n, r;
            try {
                return void 0 !== t ? null !== (n = parent.window.frames[t]) && (r = n.document.getElementById(e)) : r = document.getElementById(e) || parent.document.getElementById(e), r
            } catch (i) {
            }
        }

        function u(e) {
            try {
                var t = "#" + e.id + ":-webkit-autofill";
                if (document.querySelector(t)) return !0
            } catch (n) {
            }
            return !1
        }

        function a(e, n, r) {
            if (null != e) {
                var i = new p, s = function (e) {
                    i.capture(e, r)
                }, u = {};
                u.id = e.id, u.listener = s, u.field = e, t.push(u), o(e, "keydown", s), o(e, "keyup", s)
            }
        }

        function p() {
            this.baseTime = (new Date).getTime(), this.keyIndex = 0, this.controlCount = 0, this.specialCount = 0, this.spnum = 0, this.keyIndexArray = [], this.storageArray = [], this.keeperArray = {
                8: "",
                9: "",
                13: "",
                16: "",
                17: "",
                18: "",
                37: "",
                38: "",
                39: "",
                40: "",
                46: "",
                224: "",
                91: "",
                93: "",
                219: "",
                220: "",
                "000": ""
            }, this.controlArray = {17: "", 224: "", 91: "", 93: ""}, this.capture = function (e, t) {
                var r, i;
                window.event ? r = e.keyCode : e.which && (r = e.which), void 0 === r && (r = "000");
                var s = (new Date).getTime();
                i = s - this.baseTime, this.baseTime = s, "keydown" === e.type ? r in this.keeperArray ? (this.storageArray.push("Dk" + r + ":" + i), this.specialCount = this.specialCount + 1, r in this.controlArray && (this.controlCount = this.controlCount + 1)) : (this.storageArray.push("Di" + this.keyIndex + ":" + i), this.keyIndexArray[r] = this.keyIndex, this.keyIndex++) : "keyup" === e.type && (r in this.keeperArray ? (this.storageArray.push("Uk" + r + ":" + i), r in this.controlArray && (this.controlCount = this.controlCount + 1), "000" === r && (n[t] = this.storageArray.join(""), c())) : this.keyIndexArray[r] !== undefined && this.storageArray.push("Ui" + this.keyIndexArray[r] + ":" + i)), n[t] = this.storageArray.join(""), "ts2" === t && (6 <= this.keyIndex + this.specialCount || 1 < this.controlCount && 0 < this.keyIndex) && c()
            }
        }

        var e = !1, t = [], n = {}, c = function () {
            for (var e = 0; e < t.length; ++e) {
                var n = t[e];
                "undefined" != typeof n.field && (s(n.field, "keydown", n.listener), s(n.field, "keyup", n.listener))
            }
        };
        return {
            init: function (n) {
                // TODO call
                if (n = n || {}, !1 === e && n.detail && n.detail.fields) {
                    e = !0;
                    for (var i = 0; i < n.detail.fields.length; i++) a(document.getElementById(n.detail.fields[i]), 0, "ts" + (i + 1));
                    (function () {
                        !function (t, n) {
                            for (var i = !0, s = 0; s < t.length; s++) {
                                var o = r(t[s], n);
                                void 0 === o && null === o || (o.pf_psu = u(o), o.pf_val = !!o.value, i = i && (o.pf_psu || o.pf_val))
                            }
                            i && c()
                        }(n.detail.fields, n.detail.frame)
                    }())
                }
            },
            get: function () {
                for (var t in n) n[t] = n[t] + "Uh:" + i(n[t]);
                return n
            }
        }
    }(),
        // TODO use constants
        n.ms = function () {
        function n(t) {
            if ("undefined" == typeof t.pageX) s(document, "mousemove", n); else {
                var r = (new Date).getTime();
                0 !== e.moveCounter
                && function (n, r) {
                    var i = n - e.lastTime, s = Math.abs(r.pageX - e.prevX), o = Math.abs(r.pageY - e.prevY);
                    (1 < s || 1 < o) && function (n, r) {
                        var i = Math.floor(10 * Math.random()) + 1, s = 5123 * i + r.pageX, o = 5123 * i + r.pageY,
                            u = 5123 * i + n;
                        e.rDT_local += s + "," + o + "," + u + ":", e.counter++
                    }(i, r)
                }(r, t),
                function (n, r) {
                    e.lastTime = n, e.prevX = r.pageX, e.prevY = r.pageY, e.moveCounter++
                }(r, t), (20 <= e.counter || 50 <= e.moveCounter) && s(document, "mousemove", n)
            }
        }

        var e = {prevX: 0, prevY: 0, counter: 0, moveCounter: 0, lastTime: 0, rDT_local: ""}, t = !1;
        return {
            // init: function () {
            //     t || (o(document, "mousemove", n), t = !0)
            // },
            // get: function () {
            //     return "" !== e.rDT_local ? e.rDT_local + i(e.rDT_local) + "," + e.moveCounter : undefined
            // }
            // VB:
            get: function () {
                return "36877,35976,36080:6165,5246,5147:36920,35989,35869:6277,5277,5159:52429,51403,51254:47348,46299,46133:32020,30955,30763:52522,51456,51245:26939,25884,25719:32062,31012,30784:16696,15644,15386:6457,5398,5143:6465,5396,5145:11592,10517,10253:11599,10514,10264:52586,51496,51246:6485,5383,5140:42349,41240,41000:21600,20492,37485:10737,10894,20165:17775,22"
            }
        }
    }(),
        PAYPAL.syncData = r
};

(function () {
    encrypt(window);
    let inData = {
        fnSessionId: '533dd2c5b29546fd8e8fec415e607935',  // t.f = i.fnSessionId
        sourceId: 'UNIFIED_LOGIN_INPUT_PASSWORD',
        fname: 'fn_sync_data' // e.idForHiddenField = i.fname
    };
    PAYPAL.syncData.initSync(inData);
    PAYPAL.syncData.flushData();
})();
