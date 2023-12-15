(window.webpackJsonp = window.webpackJsonp || [
]).push([[32],
    {
        '5+XA': function (n, e, t) {
            'use strict';
            var o = t('CcnG'),
                l = t('Ip0R'),
                i = t('dJ09'),
                a = t('EExS');
            t.d(e, 'b', (function () {
                return c
            })),
                t.d(e, 'c', (function () {
                    return f
                })),
                t.d(e, 'a', (function () {
                    return m
                }));
            var c = o['ɵcrt']({
                encapsulation: 0,
                styles: [
                    ['.toast-alert-container[_ngcontent-%COMP%]{background-color:#fff;z-index:40;position:fixed;right:0;top:0;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);opacity:1;transition:opacity .3s}.toast-alert-container.notVisible[_ngcontent-%COMP%]{opacity:0}.toast-alert-container[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{position:absolute;top:8px;right:8px}.toast-alert-container[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{color:#33393e;font-size:16px}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]{display:flex;padding:32px 60px 32px 24px;align-items:center;margin:0}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]{margin-right:24px}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]   img[_ngcontent-%COMP%]{height:32px;width:32px}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .toast-text[_ngcontent-%COMP%]{display:flex;flex-direction:column;max-width:212px}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .toast-text[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#33393e}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .toast-text[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:first-of-type{font-size:.875rem;font-family:Ibercaja-Light,sans-serif}.toast-alert-container[_ngcontent-%COMP%]   .toast-alert-info[_ngcontent-%COMP%]   .toast-text[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:last-of-type{margin-top:8px;font-size:1rem;line-height:18px}']
                ],
                data: {
                }
            });
            function r(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 0, 'img', [
                        ['src',
                            'assets/img/alert-error.svg']
                    ], null, null, null, null, null))
                ], null, null)
            }
            function s(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 0, 'img', [
                        ['src',
                            'assets/img/alert-successful.svg']
                    ], null, null, null, null, null))
                ], null, null)
            }
            function u(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Lo sentimos, ha habido un error, prueba a intentarlo más tarde.'
                    ]))
                ], null, null)
            }
            function d(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Tus modificaciones se han guardado con éxito. '
                    ]))
                ], null, null)
            }
            function p(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](1, null, [
                        '',
                        ''
                    ]))
                ], null, (function (n, e) {
                    n(e, 1, 0, e.component.texto)
                }))
            }
            function g(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 14, 'div', [
                        ['class',
                            'toast-alert-info']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 4, 'span', [
                        ['class',
                            'icon']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, r)),
                    o['ɵdid'](3, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, s)),
                    o['ɵdid'](5, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](6, 0, null, null, 8, 'div', [
                        ['class',
                            'toast-text']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Información'
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, u)),
                    o['ɵdid'](10, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, d)),
                    o['ɵdid'](12, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, p)),
                    o['ɵdid'](14, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0, 2 == t.estadoModificacion),
                        n(e, 5, 0, 1 == t.estadoModificacion),
                        n(e, 10, 0, 2 == t.estadoModificacion && null == t.texto),
                        n(e, 12, 0, 1 == t.estadoModificacion && null == t.texto),
                        n(e, 14, 0, null != t.texto)
                }), null)
            }
            function f(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 6, 'div', [
                        ['class',
                            'toast-alert-container notVisible']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        notVisible: 0
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeAlert() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, g)),
                    o['ɵdid'](6, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 2, 0, 0 == t.estadoModificacion);
                    n(e, 1, 0, 'toast-alert-container notVisible', o),
                        n(e, 6, 0, 0 != t.estadoModificacion)
                }), null)
            }
            function C(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'alert', [
                    ], null, null, null, f, c)),
                    o['ɵdid'](1, 245760, null, 0, i.a, [
                        a.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            var m = o['ɵccf']('alert', i.a, C, {
            }, {
            }, [
            ])
        },
        '5nOT': function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return a
            }));
            var o = t('CcnG'),
                l = t('26FU'),
                i = t('ySnG'),
                a = function () {
                    function n() {
                        this.productoSeleccionadoEmitter = new o.EventEmitter,
                            this.seleccionado = new l.a({
                            }),
                            this.seleccionadoActual = this.seleccionado.asObservable()
                    }
                    return n.prototype.enviarElementoSeleccionado = function (n) {
                        this.seleccionado.next(n)
                    },
                        n.prototype.enviarIdProductoSeleccionado = function (n) {
                            this.productoSeleccionadoEmitter.emit(n)
                        },
                        n.prototype.continuar = function () {
                            var n = this.seleccionado.value.pasos.length,
                                e = this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones.length,
                                t = !1;
                            do {
                                this.seleccionado.value.indiceSubseccion + 1 < e ? (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado != i.a.oculto && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado = i.a.completado), this.seleccionado.value.indiceSubseccion += 1, this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado == i.a.inactivo && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado = i.a.activo)) : this.seleccionado.value.indiceSeccion + 1 < n ? (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado != i.a.oculto && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado = i.a.completado), this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado != i.a.oculto && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado = i.a.completado), this.seleccionado.value.indiceSeccion += 1, this.seleccionado.value.indiceSubseccion = 0, this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado != i.a.oculto && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado = i.a.activo), this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado != i.a.oculto && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado = i.a.activo)) : t = !0
                            } while (!t && (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado == i.a.oculto || this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado == i.a.oculto));
                            this.seleccionado.value.terminada = !1,
                            t && (this.seleccionado.value.terminada = !0),
                                this.enviarElementoSeleccionado(this.seleccionado.value),
                            document.getElementsByClassName('modal-bottom') [0] && (document.getElementsByClassName('modal-bottom') [0].scrollTop = 0),
                            document.getElementById('scroll-top') && (document.getElementById('scroll-top').scrollTop = 0)
                        },
                        n.prototype.volver = function () {
                            do {
                                this.seleccionado.value.indiceSubseccion - 1 >= 0 ? this.seleccionado.value.indiceSubseccion -= 1 : this.seleccionado.value.indiceSeccion - 1 >= 0 && (this.seleccionado.value.indiceSeccion -= 1, this.seleccionado.value.indiceSubseccion = 0)
                            } while (this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].estado == i.a.oculto || this.seleccionado.value.pasos[this.seleccionado.value.indiceSeccion].subsecciones[this.seleccionado.value.indiceSubseccion].estado == i.a.oculto);
                            this.enviarElementoSeleccionado(this.seleccionado.value)
                        },
                        n.prototype.modificarOrdenPasos = function (n, e, t, o, l) {
                            return n.pasos[e].seccion = o,
                                n.pasos[t].estado = l ? i.a.oculto : i.a.inactivo,
                                n
                        },
                        n.prototype.getCleanedString = function (n) {
                            for (var e = 0; e < '"ºª`!@#$^&%*=[]{}|<>_'.length; e++) n = n.replace(new RegExp('\\' + '"ºª`!@#$^&%*=[]{}|<>_'[e], 'gi'), ' ');
                            return (n = (n = (n = (n = (n = (n = (n = n.replace(/\s+/g, ' ')).replace(/\xe7/gi, 'c')).replace(/\xe1/gi, 'a')).replace(/\xe9/gi, 'e')).replace(/\xed/gi, 'i')).replace(/\xf3/gi, 'o')).replace(/\xfa/gi, 'u')).replace(/\xf1/gi, 'n')
                        },
                        n.prototype.cleanCuenta = function (n) {
                            return (n = (n = n.replace(new RegExp(' ', 'g'), '')).replace(new RegExp('-', 'g'), '')).replace(new RegExp('/', 'g'), '')
                        },
                        n.prototype.resetEstadoPasos = function () {
                            var n = this;
                            this.seleccionado.value.pasos.forEach((function (e, t) {
                                t > n.seleccionado.value.indiceSeccion && (e.estado = i.a.inactivo, e.subsecciones.forEach((function (n) {
                                    n.estado = i.a.inactivo
                                })))
                            }))
                        },
                        n.ngInjectableDef = o.defineInjectable({
                            factory: function () {
                                return new n
                            },
                            token: n,
                            providedIn: 'root'
                        }),
                        n
                }()
        },
        EEny: function (n, e, t) {
            'use strict';
            var o = t('CcnG'),
                l = t('Ip0R'),
                i = t('aHHB'),
                a = t('bXK5');
            t('BHn8'),
                t.d(e, 'a', (function () {
                    return c
                })),
                t.d(e, 'b', (function () {
                    return d
                }));
            var c = o['ɵcrt']({
                encapsulation: 0,
                styles: [
                    ['.dropdown-container[_ngcontent-%COMP%]{position:relative}.dropdown-container.disabled[_ngcontent-%COMP%]{cursor:not-allowed}.collapsable-menu[_ngcontent-%COMP%]{position:absolute;z-index:4;background-color:#fff;opacity:0;visibility:hidden;padding:10px 15px;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);height:0;transition:height .2s cubic-bezier(.4,0,0,1.04);max-height:330px;overflow-y:auto;overflow-x:hidden}.collapsable-menu[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]{padding:10px 0;display:flex;align-items:center;width:100%}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]{padding-bottom:16px;border-bottom:1px solid rgba(51,57,62,.1)}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.8125rem;border:1px solid rgba(51,57,62,.7);border-radius:2px;width:100%;padding:11px 7px;margin:1px 0}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus{outline:0;border-color:#0b7ad0;border-width:2px;margin:0}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]::-moz-placeholder{line-height:1.25rem}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:-ms-input-placeholder{line-height:1.25rem}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]::placeholder{line-height:1.25rem}.collapsable-menu[_ngcontent-%COMP%] > div.btn-all[_ngcontent-%COMP%] + .btn-option[_ngcontent-%COMP%]{margin-top:10px}.collapsable-menu[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.8125rem;color:#33393e;margin-left:8px;white-space:nowrap;text-overflow:ellipsis;overflow:hidden;width:100%;text-align:left;line-height:17px}.collapsable-menu[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]   .custom-checkbox.selected[_ngcontent-%COMP%] + div[_ngcontent-%COMP%] + span[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]{position:relative;box-sizing:border-box;border:1px solid rgba(51,57,62,.7);border-radius:2px;font-size:.8125rem;height:48px;padding:1px 0 1px 15px;font-weight:400;color:#33393e;font-family:Ibercaja-Regular,sans-serif;background-color:transparent;display:flex;justify-content:space-between;align-items:center;width:100%}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{max-width:calc(100% - 48px);text-overflow:ellipsis;overflow:hidden;white-space:nowrap;line-height:17px}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;height:44px;width:48px;position:relative}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]:before{position:absolute;font-size:11px;padding:19px 16px;right:0;color:#33393e;transition:all .3s ease}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.show[_ngcontent-%COMP%]{z-index:2;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);padding:0 0 0 15px;margin-left:-1px}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.show[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:before{transform:rotateX(180deg);transition:all .3s ease}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.show[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%]{opacity:1;visibility:visible;top:46px;width:auto;min-width:100%;margin-left:-1px;height:auto}.dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.disabled[_ngcontent-%COMP%]{pointer-events:none;background-color:rgba(38,38,42,.08);color:rgba(0,0,0,.19);border:none}.click-device[_nghost-%COMP%]   .collapsable-menu[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .collapsable-menu[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:hover{cursor:pointer}.click-device[_nghost-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .custom-dropdown[_ngcontent-%COMP%]:hover{cursor:pointer}.no-absolute[_nghost-%COMP%]   .dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%], .no-absolute   [_nghost-%COMP%]   .dropdown-container[_ngcontent-%COMP%]   .custom-dropdown[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%]{position:inherit;height:0;padding:0;top:0;transition:height .2s cubic-bezier(.4,0,0,1.04)}.no-absolute[_nghost-%COMP%]   .dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.show[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%], .no-absolute   [_nghost-%COMP%]   .dropdown-container[_ngcontent-%COMP%]   .custom-dropdown.show[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%]{height:auto;padding:10px 15px;transition:height .2s cubic-bezier(.4,0,0,1.04),opacity .2s ease-in}']
                ],
                data: {
                }
            });
            function r(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 6, 'div', [
                        ['class',
                            'btn-all']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, null) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](2, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](3, {
                        selected: 0
                    }),
                    o['ɵdid'](4, 81920, null, 0, i.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'span', [
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = !1 !== l.selectCheck('checkbox-all-' + l.id, null) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Seleccionar todos'
                    ]))
                ], (function (n, e) {
                    var t = n(e, 3, 0, e.component.todosSeleccionados);
                    n(e, 2, 0, t),
                        n(e, 4, 0)
                }), (function (n, e) {
                    n(e, 1, 0, o['ɵinlineInterpolate'](1, 'checkbox-all-', e.component.id, ''))
                }))
            }
            function s(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'div', [
                        ['class',
                            'btn-all']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 0, 'input', [
                        ['placeholder',
                            'Búsqueda...'],
                        [
                            'type',
                            'text'
                        ]
                    ], [
                        [8,
                            'id',
                            0]
                    ], null, null, null, null))
                ], null, (function (n, e) {
                    n(e, 1, 0, o['ɵinlineInterpolate'](1, 'search-', e.component.id, ''))
                }))
            }
            function u(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 6, 'div', [
                        ['class',
                            'btn-option']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, n.context.index) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](2, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](3, {
                        selected: 0
                    }),
                    o['ɵdid'](4, 81920, null, 0, i.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'span', [
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = !1 !== l.selectCheck('checkbox-' + l.id + '-' + n.context.index, n.context.index) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted'](6, null, [
                        '',
                        ''
                    ]))
                ], (function (n, e) {
                    var t = n(e, 3, 0, e.context.$implicit.seleccionado);
                    n(e, 2, 0, t),
                        n(e, 4, 0)
                }), (function (n, e) {
                    n(e, 1, 0, o['ɵinlineInterpolate'](2, 'checkbox-', e.component.id, '-', e.context.index, '')),
                        n(e, 6, 0, e.context.$implicit.texto)
                }))
            }
            function d(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 16, 'div', [
                        ['class',
                            'dropdown-container']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        disabled: 0
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 5, 'button', [
                        ['class',
                            'custom-dropdown']
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.verMenu(t) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](4, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](5, {
                        show: 0,
                        disabled: 1
                    }),
                    (n() (), o['ɵeld'](6, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](7, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](8, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Chevron-abajo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](9, 0, null, null, 7, 'div', [
                        ['class',
                            'collapsable-menu']
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'clickOutside'],
                        [
                            'document',
                            'click'
                        ],
                        [
                            'document',
                            'touch'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'document:click' === e && (l = !1 !== o['ɵnov'](n, 10).onClick(t.target) && l),
                        'document:touch' === e && (l = !1 !== o['ɵnov'](n, 10).onClick(t.target) && l),
                        'clickOutside' === e && (l = !1 !== i.closeDropdown(t, 'dropdown-btn-' + i.id) && l),
                            l
                    }), null, null)),
                    o['ɵdid'](10, 16384, null, 0, a.a, [
                        o.ElementRef
                    ], null, {
                        clickOutside: 'clickOutside'
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, r)),
                    o['ɵdid'](12, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, s)),
                    o['ɵdid'](14, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, u)),
                    o['ɵdid'](16, 278528, null, 0, l.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 2, 0, t.disabled);
                    n(e, 1, 0, 'dropdown-container', o);
                    var l = n(e, 5, 0, t.mostrarMenu, t.disabled);
                    n(e, 4, 0, 'custom-dropdown', l),
                        n(e, 12, 0, !t.search && t.selectAll && t.model.length > 0),
                        n(e, 14, 0, t.search),
                        n(e, 16, 0, t.model)
                }), (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0, o['ɵinlineInterpolate'](1, 'dropdown-btn-', t.id, '')),
                        n(e, 7, 0, t.placeholder),
                        n(e, 9, 0, o['ɵinlineInterpolate'](1, '', t.id, ''))
                }))
            }
        },
        'HB/b': function (n, e, t) {
            'use strict';
            var o = t('CcnG'),
                l = t('Ip0R'),
                i = t('bXK5');
            t('iZGF'),
                t('pjlW'),
                t.d(e, 'a', (function () {
                    return a
                })),
                t.d(e, 'b', (function () {
                    return c
                }));
            var a = o['ɵcrt']({
                encapsulation: 0,
                styles: [
                    ['.dropdown-importes-container[_ngcontent-%COMP%]{position:relative}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]{position:relative;box-sizing:border-box;border:1px solid rgba(51,57,62,.7);border-radius:2px;font-size:.8125rem;height:48px;padding:1px 0 1px 15px;font-weight:400;color:#33393e;font-family:Ibercaja-Regular,sans-serif;background-color:transparent;display:flex;justify-content:space-between;align-items:center;width:100%}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{max-width:calc(100% - 48px);text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;height:44px;width:48px;position:relative}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]:before{position:absolute;font-size:11px;padding:19px 16px;right:0;color:#33393e;transition:all .3s ease}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input.show[_ngcontent-%COMP%]{z-index:2;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);padding:0 0 0 15px;margin-left:-1px}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input.show[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:before{transform:rotateX(180deg);transition:all .3s ease}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input.show[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%]{opacity:1;visibility:visible;top:48px;width:auto;min-width:100%;min-height:119px;margin-left:-1px;transition:height .15s ease-in-out,opacity .2s ease-in}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]{position:absolute;z-index:4;background-color:#fff;opacity:0;visibility:hidden;padding:19px 24px;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);height:0;transition:height .2s ease-out}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]{display:flex}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:last-of-type{margin-left:19px}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:flex;align-items:center}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{border:none;border-bottom:1px solid rgba(49,56,64,.3);width:109px;padding-bottom:7px;text-align:center;transition:border-bottom .3s linear .1s}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus{outline:0;border-bottom:1px solid #0b7ad0}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   input.error[_ngcontent-%COMP%]{border-bottom:1px solid #d83838!important}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]:focus::-webkit-input-placeholder{opacity:0}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   label[_ngcontent-%COMP%]{color:rgba(51,57,62,.7);font-family:Ibercaja-Regular,sans-serif;margin-right:13px;font-size:.75rem}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .mensajeError[_ngcontent-%COMP%]{visibility:hidden;color:#d83838;font-size:.75rem;padding-top:9px;font-family:Ibercaja-Regular,sans-serif;min-height:23px}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .mensajeError.showError[_ngcontent-%COMP%]{visibility:visible}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .reiniciar[_ngcontent-%COMP%]{margin-top:22px}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .reiniciar[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{padding:11px 0;cursor:pointer;font-size:.75rem;font-family:Ibercaja-Regular,sans-serif;text-transform:uppercase;font-weight:700}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu.right[_ngcontent-%COMP%]{right:0}@media screen and (max-width:767px){.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input.show[_ngcontent-%COMP%]{z-index:0;margin-bottom:150px}.dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input.show[_ngcontent-%COMP%] + .collapsable-menu[_ngcontent-%COMP%]{width:auto;z-index:0;position:absolute;top:48px;height:auto;opacity:1;transition:all .2s ease}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{align-items:flex-start;flex-direction:column}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   label[_ngcontent-%COMP%]{padding-bottom:11px}.dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .wrapper[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{text-align:left}}.click-device[_nghost-%COMP%]   .dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .dropdown-importes-container[_ngcontent-%COMP%]   .dropdown-importes-input[_ngcontent-%COMP%]:hover{cursor:pointer}.click-device[_nghost-%COMP%]   .dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .reiniciar[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .dropdown-importes-container[_ngcontent-%COMP%]   .collapsable-menu[_ngcontent-%COMP%]   .reiniciar[_ngcontent-%COMP%]:hover{color:#0b7ad0}']
                ],
                data: {
                }
            });
            function c(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 26, 'div', [
                        ['class',
                            'dropdown-importes-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 5, 'button', [
                        ['class',
                            'dropdown-importes-input']
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.verCollapse() && o),
                            o
                    }), null, null)),
                    o['ɵdid'](2, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](3, {
                        show: 0
                    }),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](5, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](6, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Chevron-abajo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 19, 'div', [
                        ['class',
                            'collapsable-menu']
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'clickOutside'],
                        [
                            'document',
                            'click'
                        ],
                        [
                            'document',
                            'touch'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'document:click' === e && (l = !1 !== o['ɵnov'](n, 10).onClick(t.target) && l),
                        'document:touch' === e && (l = !1 !== o['ɵnov'](n, 10).onClick(t.target) && l),
                        'clickOutside' === e && (l = !1 !== i.closeCollapse(t, 'dropdown-importes-btn-' + (null == i.config ? null : i.config.id)) && l),
                            l
                    }), null, null)),
                    o['ɵdid'](8, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](9, {
                        right: 0
                    }),
                    o['ɵdid'](10, 16384, null, 0, i.a, [
                        o.ElementRef
                    ], null, {
                        clickOutside: 'clickOutside'
                    }),
                    (n() (), o['ɵeld'](11, 0, null, null, 8, 'div', [
                        ['class',
                            'wrapper']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](12, 0, null, null, 3, 'div', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](13, 0, null, null, 1, 'label', [
                        ['for',
                            'minInput']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](14, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](15, 0, null, null, 0, 'input', [
                        ['autocomplete',
                            'off'],
                        [
                            'name',
                            'minInput'
                        ],
                        [
                            'type',
                            'text'
                        ]
                    ], [
                        [8,
                            'placeholder',
                            0],
                        [
                            8,
                            'value',
                            0
                        ]
                    ], [
                        [null,
                            'input'],
                        [
                            null,
                            'blur'
                        ]
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'input' === e && (o = !1 !== l.validarCampoImporte(t.target, 'min') && o),
                        'blur' === e && (o = !1 !== l.setImportes() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](16, 0, null, null, 3, 'div', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](17, 0, null, null, 1, 'label', [
                        ['for',
                            'maxInput']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](18, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](19, 0, null, null, 0, 'input', [
                        ['autocomplete',
                            'off'],
                        [
                            'name',
                            'maxInput'
                        ],
                        [
                            'type',
                            'text'
                        ]
                    ], [
                        [8,
                            'placeholder',
                            0],
                        [
                            8,
                            'value',
                            0
                        ]
                    ], [
                        [null,
                            'input'],
                        [
                            null,
                            'blur'
                        ]
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'input' === e && (o = !1 !== l.validarCampoImporte(t.target, 'max') && o),
                        'blur' === e && (o = !1 !== l.setImportes() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](20, 0, null, null, 3, 'div', [
                        ['class',
                            'mensajeError']
                    ], null, null, null, null, null)),
                    o['ɵdid'](21, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](22, {
                        showError: 0
                    }),
                    (n() (), o['ɵted'](23, null, [
                        ' ',
                        ' '
                    ])),
                    (n() (), o['ɵeld'](24, 0, null, null, 2, 'div', [
                        ['class',
                            'reiniciar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](25, 0, null, null, 1, 'span', [
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.reiniciarFiltro() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Reiniciar'
                    ]))
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 3, 0, t.mostrarCollapse);
                    n(e, 2, 0, 'dropdown-importes-input', o);
                    var l = n(e, 9, 0, t.right);
                    n(e, 8, 0, 'collapsable-menu', l);
                    var i = n(e, 22, 0, null != t.mensajeError);
                    n(e, 21, 0, 'mensajeError', i)
                }), (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, o['ɵinlineInterpolate'](1, 'dropdown-importes-btn-', t.config.id, '')),
                        n(e, 5, 0, t.config.placeholder),
                        n(e, 7, 0, null == t.config ? null : t.config.id),
                        n(e, 14, 0, t.config.labels[0]),
                        n(e, 15, 0, o['ɵinlineInterpolate'](1, '0 (', t.config.divisa, ')'), t.importeMinimoString),
                        n(e, 18, 0, t.config.labels[1]),
                        n(e, 19, 0, o['ɵinlineInterpolate'](1, '0 (', t.config.divisa, ')'), t.importeMaximoString),
                        n(e, 23, 0, t.mensajeError)
                }))
            }
        },
        OP3m: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return l
            }));
            var o = t('CcnG'),
                l = (t('3rka'), t('sE38'), t('SKFc'), function () {
                    function n(n, e, t) {
                        this._navigationControlService = n,
                            this.responsive = e,
                            this.utilsComponent = t,
                            this.confirmacion = !1,
                            this.error = !1,
                            this.personalizado = !1,
                            this.popup = !1,
                            this.modalClose = new o.EventEmitter
                    }
                    return n.prototype.ngOnInit = function () {
                    },
                        n.prototype.closeModal = function (n) {
                            this.utilsComponent.storage.verAjustesUsuarios || this.utilsComponent.storage.isModalCondiciones || this.utilsComponent.storage.isModalGDPR || this.utilsComponent.storage.isCustomModalClose ? this.modalClose.next(n) : this._navigationControlService.closeOperativas()
                        },
                        n
                }())
        },
        aHHB: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return l
            }));
            var o = t('CcnG'),
                l = function () {
                    function n(n, e) {
                        this.elem = n,
                            this.renderer = e,
                            this.selected = !1,
                            this.elementoSeleccionado = new o.EventEmitter
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this,
                            e = this.elem.nativeElement;
                        null != e && this.renderer.addClass(e, 'custom-checkbox');
                        var t = this.renderer.createElement('div');
                        this.renderer.insertBefore(e.parentElement, t, e.nextSibling),
                            this.renderer.listen(t, 'click', (function (t) {
                                t.stopPropagation(),
                                    e.classList.contains('selected') ? (n.renderer.removeClass(e, 'selected'), n.selected = !1, e.classList.contains('indeterminate') && n.renderer.removeClass(e, 'indeterminate')) : (n.renderer.addClass(e, 'selected'), n.selected = !0),
                                    n.elementoSeleccionado.emit({
                                        selected: n.selected
                                    })
                            }))
                    },
                        n.prototype.comprobarEsIndeterminado = function (n) {
                            var e = this.elem.nativeElement;
                            n && !e.classList.contains('indeterminate') ? this.renderer.addClass(e, 'indeterminate') : !n && e.classList.contains('indeterminate') && this.renderer.removeClass(e, 'indeterminate')
                        },
                        n
                }()
        },
        dJ09: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return i
            })),
                t('EExS');
            var o = t('K9Ia'),
                l = t('ny24'),
                i = function () {
                    function n(n) {
                        this.alertService = n,
                            this.unsubscribe = new o.a,
                            this.estadoModificacion = 0
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this.alertService.currentStatus.pipe(Object(l.a) (this.unsubscribe)).subscribe((function (e) {
                            n.estadoModificacion = e.estado,
                                n.texto = e.texto,
                                setTimeout((function () {
                                    n.closeAlert()
                                }), 5000)
                        }))
                    },
                        n.prototype.closeAlert = function () {
                            this.alertService.changeStatus({
                                estado: 0,
                                texto: null
                            })
                        },
                        n.prototype.ngOnDestroy = function () {
                            this.unsubscribe.next(),
                                this.unsubscribe.complete()
                        },
                        n
                }()
        },
        iZGF: function (n, e, t) {
            'use strict';
            var o = t('CcnG');
            t('pjlW'),
                t.d(e, 'a', (function () {
                    return l
                }));
            var l = function () {
                function n(n) {
                    this._validate = n,
                        this.mostrarCollapse = !1,
                        this.importeMinimoString = '',
                        this.importeMaximoString = '',
                        this.mensajeError = null,
                        this.importeSeleccionado = new o.EventEmitter,
                        this.right = !0
                }
                return n.prototype.ngOnInit = function () {
                },
                    n.prototype.validarCampoImporte = function (n, e) {
                        var t = this;
                        n.value = n.value.replace('-', ''),
                            'min' == e ? (n.value = this._validate.validarImporte(n.value, this.importeMinimoString), this.importeMinimoString = n.value) : 'max' == e && (n.value = this._validate.validarImporte(n.value, this.importeMaximoString), this.importeMaximoString = n.value),
                            setTimeout((function () {
                                t.comprobarErrorImportes(e)
                            }), 1000)
                    },
                    n.prototype.verCollapse = function () {
                        this.mostrarCollapse = !this.mostrarCollapse
                    },
                    n.prototype.closeCollapse = function (n, e) {
                        var t = document.getElementById(e),
                            o = document.getElementById(e).children[0],
                            l = document.getElementById(e).children[1];
                        null == n[0] && n[1] != t && n[1] != o && n[1] != l && (this.mostrarCollapse = !1)
                    },
                    n.prototype.reiniciarFiltro = function () {
                        this.mensajeError = null,
                            document.getElementsByName('minInput') [0].classList.remove('error'),
                            document.getElementsByName('maxInput') [0].classList.remove('error'),
                            this.importeMinimoString = '',
                            this.importeMaximoString = '',
                            this.importeSeleccionado.emit({
                                desde: null,
                                hasta: null
                            })
                    },
                    n.prototype.comprobarErrorImportes = function (n) {
                        '' != this.importeMaximoString && this.validarImportesMinMax('min') && '' != this.importeMinimoString && this.validarImportesMinMax('max') ? (this.mensajeError = null, document.getElementsByName('minInput') [0].classList.remove('error'), document.getElementsByName('maxInput') [0].classList.remove('error')) : '' != this.importeMinimoString && '' != this.importeMaximoString && (this.mensajeError = 'Debes introducir un importe superior al mínimo.', 'min' != n || this.validarImportesMinMax('min') ? 'max' != n || this.validarImportesMinMax('max') || document.getElementsByName('maxInput') [0].classList.add('error') : document.getElementsByName('minInput') [0].classList.add('error'))
                    },
                    n.prototype.validarImportesMinMax = function (n) {
                        var e = this.importeMinimoString;
                        e = (e = e.split('.').join('')).replace(',', '.');
                        var t = this.importeMaximoString;
                        if (t = (t = t.split('.').join('')).replace(',', '.'), 'min' == n) {
                            if (parseFloat(e) > parseFloat(t)) return !1
                        } else if ('max' == n && parseFloat(t) < parseFloat(e)) return !1;
                        return !0
                    },
                    n.prototype.setImportes = function () {
                        null != this.mensajeError || '' == this.importeMinimoString && '' == this.importeMaximoString ? '' == this.importeMinimoString && '' == this.importeMaximoString && this.reiniciarFiltro() : this.importeSeleccionado.emit({
                            desde: '' != this.importeMinimoString ? this.importeMinimoString : null,
                            hasta: '' != this.importeMaximoString ? this.importeMaximoString : null
                        })
                    },
                    n
            }()
        },
        jNeJ: function (n, e, t) {
            'use strict';
            var o = t('CcnG'),
                l = t('Ip0R');
            t('OP3m'),
                t('sE38'),
                t('SKFc'),
                t('3rka'),
                t.d(e, 'a', (function () {
                    return i
                })),
                t.d(e, 'b', (function () {
                    return C
                }));
            var i = o['ɵcrt']({
                encapsulation: 0,
                styles: [
                    ['.modal[_ngcontent-%COMP%]{position:fixed;display:block;background-color:rgba(51,57,62,.9);height:100vh;width:100vw;top:0;left:0;z-index:5}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]{display:flex;position:relative;height:100%;justify-content:space-around;align-items:center}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{color:#33393e;right:32px;top:21px;height:48px}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{color:#33393e}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{background-color:#f4f7fd;border-radius:2px;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);min-width:10%;overflow:auto;height:100vh;width:100vw;max-height:none;padding:20px;display:flex;justify-content:space-between}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{display:block;margin-bottom:51px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]{width:100%;height:-webkit-fit-content;height:-moz-fit-content;height:fit-content;text-align:center;padding:78px 73px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]{width:100%;max-width:715px;margin:0 auto}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]   .txt-titulo[_ngcontent-%COMP%]{font-size:2.25rem;line-height:46px;font-family:Ibercaja-Light,sans-serif;display:block;color:#33393e}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]   .txt-texto[_ngcontent-%COMP%]{margin-top:15px;font-family:Ibercaja-Light,sans-serif;font-size:1.25rem;line-height:32px;display:block;color:rgba(51,57,62,.7)}.modal.pop-up[_ngcontent-%COMP%]{display:flex;align-items:center}.modal.pop-up[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]{max-width:620px;height:65vh;margin:0 auto}.modal.pop-up[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{height:100%;width:100%}.modal.pop-up[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]{background-color:#fff}@media screen and (max-width:1023px){.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{height:48px;width:48px;right:16px;top:16px}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-size:1.5rem}}@media screen and (max-width:767px){.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]{background-color:#f4f7fd}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{display:none}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{background-color:#f4f7fd}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{background:0 0;padding:50px 0 17px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{margin-bottom:39px;text-align:center}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]   img[_ngcontent-%COMP%]{width:89px;height:89px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]{padding:0;width:auto;margin:0 auto}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{display:block;position:absolute;right:12px;top:12px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-size:1rem}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-personalizado[_ngcontent-%COMP%]{display:block;height:100%}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]{max-width:500px}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]   .txt-titulo[_ngcontent-%COMP%]{font-size:1rem;line-height:19px;font-family:Ibercaja-Medium,sans-serif}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]   .txt-texto[_ngcontent-%COMP%]{font-size:.8125rem;line-height:20px}.modal.pop-up[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{background-color:#fff}}.click-device[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{color:#33393e}.click-device[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{color:#33393e}.click-device[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   div[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   div[_ngcontent-%COMP%], .click-device[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   span[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   span[_ngcontent-%COMP%]{color:#0b7ad0}.mobile[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{overflow-y:auto}.mobile[_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-center[_ngcontent-%COMP%]   .modal-center-wrap[_ngcontent-%COMP%]{padding-bottom:109px}']
                ],
                data: {
                }
            });
            function a(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Cerrar'
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null))
                ], null, null)
            }
            function c(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null))
                ], null, null)
            }
            function r(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        '¡Todo ok!'
                    ]))
                ], null, null)
            }
            function s(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](1, null, [
                        '',
                        ''
                    ]))
                ], null, (function (n, e) {
                    n(e, 1, 0, e.component.tituloOkCustom)
                }))
            }
            function u(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 16, 'div', [
                        ['class',
                            'modal-center']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 15, 'div', [
                        ['class',
                            'modal-center-wrap']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, c)),
                    o['ɵdid'](3, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](4, 0, null, null, 8, 'div', [
                        ['class',
                            'titulo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'span', [
                        ['class',
                            'iconoOk icono']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 0, 'img', [
                        ['src',
                            'assets/img/successful.svg']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 3, 'div', [
                        ['class',
                            'txt-titulo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, r)),
                    o['ɵdid'](9, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ],
                        ngIfElse: [
                            1,
                            'ngIfElse'
                        ]
                    }, null),
                    (n() (), o['ɵand'](0, [
                        ['tituloOkCustomTemplate',
                            2]
                    ], null, 0, null, s)),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'div', [
                        ['class',
                            'txt-texto']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 0),
                    (n() (), o['ɵeld'](13, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-ok']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 1),
                    (n() (), o['ɵeld'](15, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-ok-bottom']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 2)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0, t.responsive.esTablet),
                        n(e, 9, 0, !t.tituloOkCustom, o['ɵnov'](e, 10))
                }), null)
            }
            function d(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null))
                ], null, null)
            }
            function p(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'div', [
                        ['class',
                            'modal-center']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 11, 'div', [
                        ['class',
                            'modal-center-wrap']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, d)),
                    o['ɵdid'](3, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](4, 0, null, null, 8, 'div', [
                        ['class',
                            'titulo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'span', [
                        ['class',
                            'iconoError icono']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 0, 'img', [
                        ['src',
                            'assets/img/error.svg']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'div', [
                        ['class',
                            'txt-titulo']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 3),
                    (n() (), o['ɵeld'](9, 0, null, null, 1, 'div', [
                        ['class',
                            'txt-texto']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 4),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-ko']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 5)
                ], (function (n, e) {
                    n(e, 3, 0, e.component.responsive.esTablet)
                }), null)
            }
            function g(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null))
                ], null, null)
            }
            function f(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 5, 'div', [
                        ['class',
                            'modal-center']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 4, 'div', [
                        ['class',
                            'modal-center-wrap']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, g)),
                    o['ɵdid'](3, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-personalizado']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 6)
                ], (function (n, e) {
                    n(e, 3, 0, e.component.responsive.esTablet)
                }), null)
            }
            function C(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'div', [
                        ['class',
                            'modal']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        'pop-up': 0
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 9, 'div', [
                        ['class',
                            'modal-wrapper']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, a)),
                    o['ɵdid'](5, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](6, 0, null, null, 6, 'div', [
                        ['class',
                            'modal-content']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, u)),
                    o['ɵdid'](8, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, p)),
                    o['ɵdid'](10, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, f)),
                    o['ɵdid'](12, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 2, 0, t.popup);
                    n(e, 1, 0, 'modal', o),
                        n(e, 5, 0, !t.responsive.esTablet),
                        n(e, 8, 0, t.confirmacion),
                        n(e, 10, 0, t.error),
                        n(e, 12, 0, t.personalizado)
                }), null)
            }
        },
        pTz1: function (n, e, t) {
            'use strict';
            t.d(e, 'b', (function () {
                return l
            })),
                t.d(e, 'a', (function () {
                    return o
                }));
            var o,
                l = function (n) {
                    return n[n.Basic = 1] = 'Basic',
                        n[n.Complex = 2] = 'Complex',
                        n[n.KeyValue = 3] = 'KeyValue',
                        n
                }({
                });
            !function (n) {
                n.Center = 'center',
                    n.Left = 'left',
                    n.Right = 'right'
            }(o || (o = {
            }))
        },
        pjlW: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return l
            }));
            var o = t('CcnG'),
                l = function () {
                    function n() {
                    }
                    return n.prototype.validarImporte = function (n, e) {
                        try {
                            var t = n.length,
                                o = n.indexOf(','),
                                l = null;
                            if ( - 1 != o) {
                                if (!(t - o < 4)) return null == e || null == e ? '' : e;
                                if (l = n.substring(o, t).trim(), n = n.substring(0, o).trim(), 'NaN' == new Intl.NumberFormat('es-ES', {
                                    maximumFractionDigits: 2
                                }).format(l.substring(1, l.length))) return null == e || null == e ? '' : e
                            }
                            var i = n.split('.').join('');
                            return i = i.replace(',', '.'),
                                'NaN' == (n = new Intl.NumberFormat('es-ES', {
                                    maximumFractionDigits: 2
                                }).format(i)) ? n = null == e || null == e ? '' : e : '' == i && (n = i),
                            null != l && (n += l),
                                n
                        } catch (a) {
                            return e
                        }
                    },
                        n.ngInjectableDef = o.defineInjectable({
                            factory: function () {
                                return new n
                            },
                            token: n,
                            providedIn: 'root'
                        }),
                        n
                }()
        },
        qgto: function (n, e, t) {
            'use strict';
            t.r(e);
            var o = t('CcnG'),
                l = t('5nOT'),
                i = t('ySnG'),
                a = t('3rka'),
                c = t('pTz1'),
                r = t('GZjy'),
                s = t('g1w/'),
                u = t('Yd+C'),
                d = (t('qdNA'), t('sE38')),
                p = t('SKFc'),
                g = function () {
                    function n(n, e, t, o, l, a) {
                        this._ps = n,
                            this._navigationControlServoce = e,
                            this.errorHandler = t,
                            this.responsive = o,
                            this.utilsComponent = l,
                            this.datosPersonalesCoreService = a,
                            this.navegacionDuplicado = {
                                terminada: !1,
                                indiceSeccion: 0,
                                indiceSubseccion: 0,
                                icono: 'ibercaja-icon-Copiar',
                                tituloOperativa: 'solicitud de duplicados',
                                pasos: [
                                    {
                                        seccion: 1,
                                        estado: i.a.activo,
                                        tituloSeccion: 'forma de envío',
                                        tituloFlujo: 'forma de envío',
                                        subsecciones: [
                                            {
                                                index: 1,
                                                estado: i.a.activo,
                                                tituloAtras: null,
                                                datosSeleccionados: {
                                                    dato: null,
                                                    texto: null
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        seccion: 2,
                                        estado: i.a.oculto,
                                        tituloSeccion: 'correo electrónico',
                                        tituloFlujo: 'correo electrónico',
                                        subsecciones: [
                                            {
                                                index: 1,
                                                estado: i.a.inactivo,
                                                tituloAtras: null,
                                                datosSeleccionados: {
                                                    dato: null,
                                                    texto: null
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        seccion: 2,
                                        estado: i.a.inactivo,
                                        tituloSeccion: 'confirmación',
                                        tituloFlujo: 'confirmación',
                                        subsecciones: [
                                            {
                                                index: 1,
                                                estado: i.a.inactivo,
                                                tituloAtras: null,
                                                datosSeleccionados: {
                                                    dato: null,
                                                    texto: null
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                            this.propiedadesFormaEnvio = {
                                opciones: [
                                    {
                                        id: 1,
                                        texto: 'por correo electrónico'
                                    },
                                    {
                                        id: 2,
                                        texto: 'en papel, al destinatario original'
                                    }
                                ],
                                titulo: 'selecciona la forma de envío',
                                placeholder: 'Selección del tipo de envío',
                                label: 'Selección del tipo de envío',
                                info: 'tipoEnvio'
                            },
                            this.propiedadesEmail = {
                                opciones: [
                                ],
                                titulo: 'selecciona el correo electrónico',
                                placeholder: 'dirección del correo electrónico',
                                label: 'Elige un correo electrónico',
                                info: 'email'
                            },
                            this.datosConfirmacion = {
                                titulo: 'revisa los datos',
                                elementos: [
                                ]
                            },
                            this.tableconfigCorreos = {
                                type: c.b.Basic,
                                dataTable: null,
                                dataTableMobile: null
                            },
                            this.estadoDuplicado = null
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this.utilsComponent.storage.isCustomModalClose = !1,
                            this.correosSeleccionados = this.utilsComponent.storage.mensajesSeleccionados,
                            this.setUpEmails(),
                            this.setUpDatosConfirmacion(),
                            this._ps.enviarElementoSeleccionado(this.navegacionDuplicado),
                            this._ps.seleccionadoActual.subscribe((function (e) {
                                n.navegacionDuplicado = e,
                                n.navegacionDuplicado.terminada && (n.estadoDuplicado = i.b.correcto)
                            }))
                    },
                        n.prototype.cancelar = function () {
                            this._navigationControlServoce.closeOperativas()
                        },
                        n.prototype.setUpEmails = function () {
                            var n = this;
                            this.datosPersonalesCoreService.getEmailsContacto().then((function (e) {
                                if (e.error) n.errorHandler.showModal(s.a.TiposModal.Error, s.a.ErrorMessages.ErrorGenerico, null, !0, s.a.Botones.Aceptar);
                                else for (var t = 0; t < e.emails.length; t++) n.propiedadesEmail.opciones[t] = {
                                    id: t,
                                    texto: e.emails[t].email
                                }
                            }))
                        },
                        n.prototype.setUpDatosConfirmacion = function () {
                            this.datosConfirmacion.elementos = this.correosSeleccionados
                        },
                        n.prototype.validacionDuplicadosEmail = function () {
                            var n = this;
                            this.datosConfirmacion.elementos.forEach((function (e) {
                                e.accesoDupMail.web || n.removeFromList(e)
                            }))
                        },
                        n.prototype.validacionDuplicadosPapel = function () {
                            var n = this;
                            this.datosConfirmacion.elementos.forEach((function (e) {
                                e.accesoDupPapel.web || n.removeFromList(e)
                            }))
                        },
                        n.prototype.removeFromList = function (n) {
                            var e = this.correosSeleccionados.indexOf(n);
                            - 1 !== e && this.correosSeleccionados.splice(e, 1)
                        },
                        n
                }(),
                f = t('ecC8'),
                C = t('WJVJ'),
                m = (t('bNcc'), t('BHn8')),
                P = t('26FU'),
                M = function () {
                    function n() {
                        this.summatory = {
                            type: '',
                            idxSummatory: 0
                        },
                            this.statusSummaroty = new P.a(this.summatory),
                            this.currenstStatus = this.statusSummaroty.asObservable()
                    }
                    return n.prototype.changeStatus = function (n) {
                        this.statusSummaroty.next(n)
                    },
                        n.ngInjectableDef = o.defineInjectable({
                            factory: function () {
                                return new n
                            },
                            token: n,
                            providedIn: 'root'
                        }),
                        n
                }(),
                h = t('3w9W'),
                O = t('GXhj'),
                b = t('L485'),
                _ = t('MF/L'),
                v = t('ZCTz'),
                x = t('676U'),
                w = t('ny24'),
                S = t('K9Ia'),
                y = t('tBCT'),
                I = function () {
                    return function () {
                    }
                }(),
                k = function () {
                    return function () {
                    }
                }(),
                z = function () {
                    return function () {
                    }
                }(),
                R = t('6q/G'),
                j = t('A7B1'),
                F = function () {
                    function n(n, e, t, o, l, i, a, c, r, s, u, d, p) {
                        this.notificacionesService = n,
                            this.utilsComponent = e,
                            this.loading = t,
                            this.filterSummatoryService = o,
                            this.datePipe = l,
                            this.fileService = i,
                            this.errorHandler = a,
                            this.auditoriaService = c,
                            this._navigationPanelService = r,
                            this._navigationControlService = s,
                            this.responsive = u,
                            this.productoConsultaService = d,
                            this._contadorCorrespondenciaService = p,
                            this.unsubscribe = new S.a,
                            this.errorLoad = !1,
                            this.infoNotification = {
                                icon: 'info',
                                title: 'Actualmente no dispones de ningún mensaje'
                            },
                            this.verOpciones = !1,
                            this.statusMensajes = !1,
                            this.errorMessage = '',
                            this.mostrarSelectores = !1,
                            this.mostrarFiltros = !1,
                            this.mostrarFiltrosMobile = !1,
                            this.opcionSelector = 0,
                            this.opcionSelectorTexto = '',
                            this.todosSeleccionados = !1,
                            this.esSelectorGlobal = !0,
                            this.fechasSeleccionadas = '',
                            this.showPendientesDeLeer = !1,
                            this.placeholderTipoDocFiltro = '',
                            this.tiposDocumento = [
                            ],
                            this.tiposSeleccionados = [
                            ],
                            this.tiposSeleccionadosAlias = [
                            ],
                            this.placeholderEstado = '',
                            this.estados = [
                            ],
                            this.estadosSeleccionados = [
                            ],
                            this.placeholderCuenta = '',
                            this.cuentasFiltro = [
                            ],
                            this.cuentasSeleccionadas = [
                            ],
                            this.cuentasSeleccionadasAlias = [
                            ],
                            this.placeholderImportesFiltro = '',
                            this.importesSeleccionados = '',
                            this.placeholderDestacados = '',
                            this.destacados = [
                            ],
                            this.mostrarMas = !1,
                            this.mostrarMenos = !1,
                            this.movimientosVerMenos = [
                            ],
                            this.isFiltroOtros = !1,
                            this.sinCorrespondencia = !1,
                            this.isCargaInicial = !0,
                            this.PDF_EXTENSION = '.pdf',
                            this.cuentas = [
                            ],
                            this.cuentasProductos = [
                            ],
                            this.movimientosCorrespondencia = [
                            ],
                            this.confFiltroImporte = {
                                placeholder: 'Importe',
                                id: 'mov-cuentas',
                                divisa: '€',
                                labels: [
                                    'Desde',
                                    'Hasta'
                                ]
                            },
                            this.disabledCuentas = !1,
                            this.obteniendoMensajesPendientes = !1,
                            this.navigationPanel = {
                                menu: [
                                ],
                                isDashboard: !0,
                                isBuzon: !0,
                                isProducto: !1,
                                seleccionado: null
                            }
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this.isCargaInicial = !0,
                            this.configuracionBack = {
                                copiarDatos: !1,
                                editable: !1,
                                esModal: !1,
                                maxLength: null,
                                titulo: 'Buzón de correspondencia',
                                icono_subtitulo: null,
                                texto_subtitulo: null
                            },
                            this.SetUpListadoAgrupaciones(),
                            this.productoConsultaService.getProductos.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (e) {
                                e.loaded && (n.SetUpCuentasProductosTodos(e.result), n.cuentasFiltro = [
                                ], n.SetUpCuentas())
                            }), (function (n) {
                            })),
                            this.SetUpFiltros(),
                            this.ResetFiltrosSeleccionados(),
                            this.ResetCorrespondencia(),
                            this.getMensajes(this.filtro),
                            this.cargarPanelNavegacion(),
                        this.subscriptionToContadores || (this.subscriptionToContadores = this._contadorCorrespondenciaService.getDatosContador().pipe(Object(w.a) (this.unsubscribe)).subscribe((function (e) {
                            var t = 0,
                                o = 0;
                            e.loaded && !e.error && (t = e.result.totalNoLeidos, o = e.result.destacadosNoLeidos),
                                n.itemsSumatorios = [
                                    {
                                        titulo: s.a.Titulos.Pendientes,
                                        valor: t,
                                        moneda: null,
                                        esMoneda: !1,
                                        class : 'blue',
                                        tieneTooltip: !1,
                                        tieneClick: !0
                                    },
                                    {
                                        titulo: s.a.Titulos.Destacados,
                                        valor: o,
                                        moneda: null,
                                        esMoneda: !1,
                                        class : null,
                                        tieneTooltip: !1,
                                        tieneClick: !0
                                    }
                                ]
                        }))),
                            this.loading.changeStatus({
                                type: 'principal',
                                active: !1
                            }),
                            this.isCargaInicial = !1
                    },
                        n.prototype.ngOnDestroy = function () {
                            this.unsubscribe.next(),
                                this.unsubscribe.complete(),
                                this.filterSummatoryService.changeStatus({
                                    idxSummatory: 0,
                                    type: ''
                                }),
                            this.filterSuscriber && this.filterSuscriber.unsubscribe(),
                            this.navigationSubscription && this.navigationSubscription.unsubscribe(),
                                this._contadorCorrespondenciaService.getDatosContador()
                        },
                        n.prototype.cargarSumatorios = function () {
                            this._contadorCorrespondenciaService.refrescarContador()
                        },
                        n.prototype.cargarPanelNavegacion = function () {
                            var n = this,
                                e = this._navigationControlService.pathActual;
                            this._navigationPanelService.menuNavegacion.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (t) {
                                n.navigationPanel.menu = t,
                                    n.navigationPanel.seleccionado = t.filter((function (n) {
                                        return n.path === e
                                    })) [0],
                                n.utilsComponent.storage.datosContacto.marcaGestorBancaPrivada && (n.navigationPanel.menu = n.navigationPanel.menu.filter((function (n) {
                                    return n.nombre != s.a.Operativas.InformeSituacion
                                })))
                            })),
                                this._navigationPanelService.getSeccionesCorrespondencia(e)
                        },
                        n.prototype.seleccionarSumatorio = function (n) {
                            console.log(n),
                                this.SwapList(0 === n)
                        },
                        n.prototype.SetUpFiltros = function () {
                            this.SetUpSelectores(),
                                this.SetUpEstados(),
                                this.SetUpPlaceHolders(),
                                this.SetUpDestacados(),
                                this.SetUpTiposDocumentos()
                        },
                        n.prototype.SetUpSelectores = function () {
                            this.selectores = [
                                {
                                    texto: s.a.Correspondencia.Labels.Todo,
                                    valor: 0
                                },
                                {
                                    texto: s.a.Correspondencia.Labels.Leido,
                                    valor: 1
                                },
                                {
                                    texto: s.a.Correspondencia.Labels.NoLeido,
                                    valor: 2
                                }
                            ]
                        },
                        n.prototype.SetUpTiposDocumentos = function () {
                            var n = this,
                                e = [
                                ];
                            (e = this.agrupaciones.filter(this.utilsComponent.storage.contratoSeleccionado.negocio ? function (n) {
                                    return n.esNegocio
                                }
                                : function (n) {
                                    return n.esParticular
                                })).sort((function (n, e) {
                                return n.orden > e.orden ? 1 : e.orden > n.orden ? - 1 : 0
                            }));
                            var t = 0;
                            e.forEach((function (e) {
                                n.tiposDocumento.push({
                                    id: t,
                                    texto: e.texto,
                                    idAgrupacion: e.id
                                }),
                                    t++
                            }))
                        },
                        n.prototype.SetUpEstados = function () {
                            this.estados = [
                                {
                                    id: 0,
                                    texto: s.a.Correspondencia.Labels.Leido
                                },
                                {
                                    id: 1,
                                    texto: s.a.Correspondencia.Labels.NoLeido
                                }
                            ]
                        },
                        n.prototype.SetUpDestacados = function () {
                            this.destacados = [
                                {
                                    id: 0,
                                    texto: s.a.Correspondencia.Labels.Destacados,
                                    value: !0
                                },
                                {
                                    id: 1,
                                    texto: s.a.Correspondencia.Labels.NoDestacados,
                                    value: !1
                                }
                            ]
                        },
                        n.prototype.SetUpCuentas = function () {
                            var n = this,
                                e = '';
                            this.cuentas = [
                            ],
                                0 != this.tiposSeleccionados.length ? this.cuentasProductos.forEach((function (t) {
                                    n.cuentas.push({
                                        codigoCuenta: s.a.Correspondencia.TipoCuenta.Ahorro,
                                        numeroCuenta: t.iban ? t.iban.substring(4) : t.numero.substring(4)
                                    }),
                                        e = t.iban ? t.alias + ' - *' + t.iban.slice(t.iban.length - 4) : t.alias + ' - *' + t.numero.slice(t.numero.length - 4),
                                    n.existeCuentasFiltro(e, t.claseCuenta) || n.cuentasFiltro.push({
                                        id: n.cuentasFiltro.length,
                                        texto: e,
                                        codigo: t.claseCuenta,
                                        numero: t.numero
                                    }),
                                        n.disabledCuentas = !1
                                })) : (this.cuentasFiltro.length = 0, this.disabledCuentas = !0)
                        },
                        n.prototype.SetUpCuentasFiltro = function (n) {
                            var e = this,
                                t = '';
                            this.cuentas.length = 0,
                                0 != this.tiposSeleccionados.length ? this.cuentasProductos.forEach((function (o) {
                                    o.claseCuenta == n && (e.cuentas.push({
                                        codigoCuenta: o.claseCuenta,
                                        numeroCuenta: o.iban ? o.iban.substring(4) : o.numero.substring(4)
                                    }), t = o.iban ? o.alias + ' - *' + o.iban.slice(o.iban.length - 4) : o.alias + ' - *' + o.numero.slice(o.numero.length - 4), e.existeCuentasFiltro(t, o.claseCuenta) || e.cuentasFiltro.push({
                                        id: e.cuentasFiltro.length,
                                        texto: t,
                                        codigo: o.claseCuenta,
                                        numero: o.numero
                                    }), e.disabledCuentas = !1)
                                })) : (this.cuentasFiltro.length = 0, this.disabledCuentas = !0)
                        },
                        n.prototype.existeCuentasFiltro = function (n, e) {
                            var t = !1;
                            return this.cuentasFiltro.forEach((function (o) {
                                n == o.texto && e == o.codigo && (t = !0)
                            })),
                                t
                        },
                        n.prototype.SetUpPlaceHolders = function () {
                            this.placeholderTipoDocFiltro = s.a.Correspondencia.Labels.TipoDocumento,
                                this.placeholderEstado = s.a.Correspondencia.Labels.Estado,
                                this.placeholderCuenta = s.a.Correspondencia.Labels.Cuenta,
                                this.placeholderImportesFiltro = s.a.Correspondencia.Labels.Importe,
                                this.placeholderDestacados = s.a.Correspondencia.Labels.Destacado
                        },
                        n.prototype.ResetCorrespondencia = function () {
                            this.countSeleccionados = 0,
                                this.mensajes = [
                                ],
                                this.movimientosCorrespondencia = [
                                ],
                                this.totalPaginas = 0
                        },
                        n.prototype.ResetFiltrosSeleccionados = function () {
                            this.mostrarMas = !1,
                                this.mostrarMenos = !1,
                                this.isFiltroOtros = !1,
                                this.tiposSeleccionados = [
                                ],
                                this.tiposSeleccionadosAlias = [
                                ],
                                this.estadosSeleccionados = [
                                ],
                                this.cuentasSeleccionadas = [
                                ],
                                this.cuentasSeleccionadasAlias = [
                                ],
                                this.importeMin = 0,
                                this.importeMax = 999999,
                                this.importesSeleccionados = '',
                                this.fechasSeleccionadas = '',
                                this.opcionSelector = 0,
                                this.opcionSelectorTexto = this.selectores.find((function (n) {
                                    return 0 == n.valor
                                })).texto,
                                this.showPendientesDeLeer = !1,
                                this.filtro = {
                                    columnaOrd: 1,
                                    agrupacion: [
                                    ],
                                    cuentas: [
                                    ],
                                    fechaDesde: '',
                                    fechaHasta: '',
                                    filtroDestacados: !1,
                                    filtroOtrosDocumentos: null,
                                    importeDesde: this.importeMin,
                                    importeHasta: this.importeMax,
                                    leido: null,
                                    orden: 1,
                                    paginaAMostrar: 1
                                }
                        },
                        n.prototype.getDocumentos = function () {
                            this.setRequest(),
                                this.getMensajes(this.filtro)
                        },
                        n.prototype.setRequest = function () {
                            this.setCuentasSeleccionadasFiltro(),
                                this.setAgrupacionesSeleccionadasFiltro()
                        },
                        n.prototype.setAgrupacionesSeleccionadasFiltro = function () {
                            var n = this;
                            this.filtro.agrupacion = [
                            ],
                            this.tiposSeleccionados.length > 0 && this.tiposSeleccionados.forEach((function (e) {
                                n.filtro.agrupacion.push(e)
                            }))
                        },
                        n.prototype.setCuentasSeleccionadasFiltro = function () {
                            var n = this;
                            this.filtro.cuentas = [
                            ],
                            this.cuentasSeleccionadas.length > 0 && this.cuentasSeleccionadas.forEach((function (e) {
                                var t = n.cuentasFiltro.filter((function (n) {
                                    return n.numero == e
                                })) [0];
                                if (t) {
                                    var o = new k;
                                    o.codigoCuenta = t.codigo,
                                        o.numeroCuenta = t.numero,
                                        n.filtro.cuentas.push(o)
                                }
                            }))
                        },
                        n.prototype.getMensajes = function (n) {
                            var e = this;
                            this.obteniendoMensajesPendientes || (this.obteniendoMensajesPendientes = !0, this.statusMensajes = !0, this.errorLoad = !1, this.notificacionesService.getNotifications(n).subscribe((function (n) {
                                null != n && e.updateMovimientosCorrespondenciaToShow(n),
                                    e.statusMensajes = !1,
                                    e.obteniendoMensajesPendientes = !1
                            }), (function (n) {
                                e.errorMessage = n,
                                    e.statusMensajes = !1,
                                    e.errorLoad = !0
                            })))
                        },
                        n.prototype.updateMovimientosCorrespondenciaToShow = function (n) {
                            var e = this;
                            0 == n.todos.length && 0 == n.total_Paginas_Todos ? this.sinCorrespondencia = !0 : (this.sinCorrespondencia = !1, n.todos.forEach((function (n) {
                                n.aliasCuentaAsociada = e.getAliasCuenta(n),
                                    n.seleccionado = !1,
                                    e.mensajes.push(n)
                            })), this.totalPaginas = n.total_Paginas_Todos, this.getMensajesPorMeses(), this.showMostrarMas())
                        },
                        n.prototype.getMensajesPorMeses = function () {
                            var n = this;
                            this.movimientosCorrespondencia = [
                            ],
                                this.mensajes.forEach((function (e) {
                                    var t = n.datePipe.transform(e.fecha, 'MMMM yyyy'),
                                        o = !1;
                                    n.movimientosCorrespondencia.forEach((function (n) {
                                        n.titulo == t && (n.elementos.push(e), o = !0)
                                    })),
                                    o || n.movimientosCorrespondencia.push({
                                        titulo: t,
                                        elementos: [
                                            e
                                        ]
                                    })
                                }))
                        },
                        n.prototype.getAliasCuenta = function (n) {
                            var e = n.cuentaAsociada,
                                t = this.cuentasProductos.filter((function (e) {
                                    return e.numero == n.cuentaAsociada.trim()
                                })) [0];
                            return null != t && null != t && '' != t.alias && (e = t.alias),
                                e
                        },
                        n.prototype.SwapList = function (n) {
                            this.ResetFiltrosSeleccionados(),
                                this.ResetCorrespondencia(),
                                this.showPendientesDeLeer = n,
                                n ? (this.filtro.leido = !1, this.filtro.filtroDestacados = !1) : this.filtro.filtroDestacados = !0,
                                this.getDocumentos()
                        },
                        n.prototype.resetSecondFilter = function () {
                            this.auditoriaService.postRegistrarEvento({
                                tipoEvento: _.b.BuzonBusquedaAvanzada,
                                otrosDatos: 'FILTROS. FechaDesde: ' + this.filtro.fechaDesde + ' FechaHasta: ' + this.filtro.fechaHasta + ' Cuentas: ' + this.filtro.cuentas + ' ImporteDesde: ' + this.filtro.importeDesde + ' ImporteHasta: ' + this.filtro.importeHasta + ' Leidos: ' + this.filtro.leido + ' Destacados: ' + this.filtro.filtroDestacados + ' OtrosDocumentos: ' + this.filtro.filtroOtrosDocumentos
                            }).pipe(Object(w.a) (this.unsubscribe)).subscribe(),
                                this.filtro.paginaAMostrar = 1,
                                this.mostrarMas = !1,
                                this.mostrarMenos = !1,
                                this.ResetCorrespondencia(),
                                this.getDocumentos()
                        },
                        n.prototype.seleccionar = function (n, e, t) {
                            n.selected ? (null == e && (this.mensajes.forEach(0 == this.opcionSelector ? function (n) {
                                    n.seleccionado = !0
                                }
                                : 1 == this.opcionSelector ? function (n) {
                                        n.seleccionado = !!n.leido
                                    }
                                    : function (n) {
                                        n.seleccionado = !n.leido
                                    }), this.todosSeleccionados = !0), null != e && this.mensajes.forEach((function (n) {
                                n.codRefCifrado == t.codRefCifrado && (t.seleccionado = !0)
                            }))) : (null == e && (this.mensajes.forEach((function (n) {
                                n.seleccionado = !1
                            })), this.todosSeleccionados = !1, this.customCheckboxDir.first.comprobarEsIndeterminado(!1)), null != e && (this.mensajes.forEach((function (n) {
                                n.codRefCifrado == t.codRefCifrado && (t.seleccionado = !1)
                            })), this.customCheckboxDir.first.comprobarEsIndeterminado(!0))),
                                this.countSeleccionados = this.mensajes.filter((function (n) {
                                    return n.seleccionado
                                })).length
                        },
                        n.prototype.seleccionarMensaje = function (n, e) {
                            var t = this;
                            switch (n.preventDefault(), n.stopPropagation(), null == e && null == e || (this.opcionSelector = e, this.opcionSelectorTexto = this.selectores.find((function (n) {
                                return n.valor == e
                            })).texto), this.opcionSelector) {
                                case 0:
                                    this.mensajes.forEach((function (n, e) {
                                        t.mensajes[e].seleccionado = !0
                                    }));
                                    break;
                                case 1:
                                    this.mensajes.forEach((function (n, e) {
                                        t.mensajes[e].seleccionado = !!n.leido
                                    }));
                                    break;
                                case 2:
                                    this.mensajes.forEach((function (n, e) {
                                        t.mensajes[e].seleccionado = !n.leido
                                    }))
                            }
                            this.mostrarSelectores = !1,
                                this.countSeleccionados = this.mensajes.filter((function (n) {
                                    return n.seleccionado
                                })).length
                        },
                        n.prototype.accionesMensajes = function (n) {
                            var e,
                                t,
                                o = this,
                                l = [
                                ],
                                i = '';
                            if (this.countSeleccionados > 0 && this.mensajes.length > 0) switch (n) {
                                case 'abrir':
                                    t = 0,
                                        this.mensajes.forEach((function (n, e) {
                                            n.seleccionado && (l.push(o.mensajes[e].codRefCifrado), i = i + ' {' + t + '}  Referencia: ' + o.mensajes[e].codRefCifrado, t++)
                                        })),
                                        this.auditoriaService.postRegistrarEvento({
                                            tipoEvento: _.b.BuzonAbrirDocumentoDesdeConsultaMov,
                                            otrosDatos: i
                                        }).pipe(Object(w.a) (this.unsubscribe)).subscribe(),
                                        this.descargarDocumento(l);
                                    break;
                                case 'noLeido':
                                    e = !1,
                                        this.mensajes.forEach((function (n, e) {
                                            n.seleccionado && l.push(o.mensajes[e].codRefCifrado)
                                        })),
                                        this.UpdateMensajesSeleccionados(l, e);
                                    break;
                                case 'leido':
                                    e = !0,
                                        this.mensajes.forEach((function (n, e) {
                                            n.seleccionado && l.push(o.mensajes[e].codRefCifrado)
                                        })),
                                        this.UpdateMensajesSeleccionados(l, e);
                                    break;
                                case 'duplicado':
                                    var a = void 0;
                                    a = (a = this.mensajes.filter((function (n) {
                                        return 1 == n.seleccionado
                                    }))).slice(0, 10),
                                        this.utilsComponent.storage.mensajesSeleccionados = a,
                                        this.goPedirDuplicado()
                            }
                        },
                        n.prototype.GetDocumento = function (n) {
                            var e = [
                            ];
                            e.push(n.codRefCifrado),
                                this.descargarDocumento(e)
                        },
                        n.prototype.descargarDocumento = function (n) {
                            var e = this;
                            this.notificacionesService.getDocumento(n).subscribe((function (t) {
                                var o = e.fileService.generarPdf(t.documento),
                                    l = e.datePipe.transform(new Date, 'yyyy-MM-dd', null, 'es-ES');
                                e.fileService.descargarFichero(o, l += e.PDF_EXTENSION, window),
                                    n.forEach((function (n) {
                                        var t = e.mensajes.filter((function (e) {
                                            return e.codRefCifrado == n
                                        })) [0];
                                        null != t && (t.leido = !0)
                                    })),
                                    e.UpdateMensajesSeleccionados(n, !0)
                            }), (function (n) {
                                e.errorHandler.showModal(s.a.TiposModal.Warning, s.a.ErrorMessages.ErrorDocumento, null, !0, s.a.Botones.Aceptar)
                            }))
                        },
                        n.prototype.UpdateMensajesSeleccionados = function (n, e) {
                            var t = new z;
                            t.canal = s.a.Correspondencia.Contadores.Canal,
                                t.codRefCifrado = n,
                                t.leido = e,
                                t.isCambiarTodosLeido = !1,
                                this.UpdateMensajesLeido(t)
                        },
                        n.prototype.UpdateMensajesLeido = function (n) {
                            var e = this;
                            this.notificacionesService.postCambiarEstado(n).subscribe((function (t) {
                                e._contadorCorrespondenciaService.refrescarContador(),
                                    e.UpdateStatusUI(n.leido)
                            }), (function (n) {
                                e.todosSeleccionados && e.errorHandler.showModal(s.a.TiposModal.Error, s.a.ErrorMessages.ErrorGenerico, null, !0, s.a.Botones.Aceptar)
                            }))
                        },
                        n.prototype.UpdateStatusUI = function (n) {
                            var e = this;
                            this.mensajes.forEach((function (t, o) {
                                t.seleccionado && (e.mensajes[o].leido = n)
                            }))
                        },
                        n.prototype.closeDropdown = function (n, e) {
                            var t = document.getElementById(e);
                            null == n[0] && n[1] != t && (this.mostrarSelectores = !1)
                        },
                        n.prototype.seleccionarFechas = function (n) {
                            null == n.fdesde ? (this.fechasSeleccionadas = '', this.filtro.fechaDesde = '', this.filtro.fechaHasta = '') : null == n.fhasta ? (this.fechasSeleccionadas = 'Desde ' + n.fdesde.day + '/' + n.fdesde.month + '/' + n.fdesde.year + ' hasta hoy', this.filtro.fechaDesde = n.fdesde.day + '/' + n.fdesde.month + '/' + n.fdesde.year) : n.fhasta == n.fdesde ? (this.fechasSeleccionadas = n.fdesde.day + '/' + n.fdesde.month + '/' + n.fdesde.year, this.filtro.fechaDesde = this.fechasSeleccionadas, this.filtro.fechaHasta = this.fechasSeleccionadas) : (this.fechasSeleccionadas = 'De ' + n.fdesde.day + '/' + n.fdesde.month + '/' + n.fdesde.year + ' a ' + n.fhasta.day + '/' + n.fhasta.month + '/' + n.fhasta.year, this.filtro.fechaDesde = n.fdesde.day + '/' + n.fdesde.month + '/' + n.fdesde.year, this.filtro.fechaHasta = n.fhasta.day + '/' + n.fhasta.month + '/' + n.fhasta.year),
                                this.formatFechaFiltro()
                        },
                        n.prototype.formatFechaFiltro = function () {
                            var n;
                            '' != this.filtro.fechaDesde && (n = this.filtro.fechaDesde.split('/'), this.filtro.fechaDesde = (n[0].length < 2 ? '0' + n[0] : n[0]) + '/' + (n[1].length < 2 ? '0' + n[1] : n[1]) + '/' + n[2]),
                            '' != this.filtro.fechaHasta && (n = this.filtro.fechaHasta.split('/'), this.filtro.fechaHasta = (n[0].length < 2 ? '0' + n[0] : n[0]) + '/' + (n[1].length < 2 ? '0' + n[1] : n[1]) + '/' + n[2])
                        },
                        n.prototype.seleccionarTiposDocuemento = function (n) {
                            var e = this;
                            this.tiposSeleccionados = [
                            ],
                                this.tiposSeleccionadosAlias = n.elementos,
                                this.filtro.filtroOtrosDocumentos = null;
                            var t = [
                            ];
                            if (n.elementos.length > 0) {
                                var o = !1;
                                n.elementos.forEach((function (n) {
                                    var l = e.tiposDocumento.filter((function (e) {
                                        return e.id == n
                                    })) [0];
                                    null != l && ('00' == l.idAgrupacion ? o = !0 : e.tiposSeleccionados.push(l.idAgrupacion), t.push({
                                        id: l.idAgrupacion,
                                        texto: l.texto
                                    }))
                                })),
                                    this.controlFiltroCargarCuentas(t),
                                    o && this.tiposSeleccionados.length > 1 ? this.filtro.filtroOtrosDocumentos = null : o ? (this.filtro.filtroOtrosDocumentos = !0, this.isFiltroOtros = !0) : (this.filtro.filtroOtrosDocumentos = !1, this.isFiltroOtros = !1)
                            } else this.controlFiltroCargarCuentas(t)
                        },
                        n.prototype.controlFiltroCargarCuentas = function (n) {
                            n.length > 0 || (this.cuentasFiltro = [
                            ]),
                                this.cargarComboCuentas(n)
                        },
                        n.prototype.cargarComboCuentas = function (n) {
                            var e = this;
                            this.cuentasFiltro = [
                            ],
                                0 != n.length ? n.forEach((function (n) {
                                    switch (n.id.toString()) {
                                        case s.a.Correspondencia.IdAgrupacion.Recibos:
                                        case s.a.Correspondencia.IdAgrupacion.Ahorro:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.AhorroFinanciacion:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Prestamos);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Fondos:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Fondos);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.FondosPlanes:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Fondos),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Planes);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Planes:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Planes);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Extractos:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Fondos),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Planes),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Valores),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Tarjetas),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.SegAhorro);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.InfFiscal:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Fondos),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Planes),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Valores),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.SegAhorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Prestamos);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Valores:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Valores);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Tarjetas:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Tarjetas);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Financiación:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Prestamos);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.SegurosAhorro:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.SegAhorro);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Cartera:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro),
                                                e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Cartera);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.Contratos:
                                        case s.a.Correspondencia.IdAgrupacion.Transferencias:
                                            e.SetUpCuentasFiltro(s.a.Correspondencia.TipoCuenta.Ahorro);
                                            break;
                                        case s.a.Correspondencia.IdAgrupacion.BancaDigital:
                                            e.SetUpCuentas()
                                    }
                                })) : this.SetUpCuentas()
                        },
                        n.prototype.seleccionarEstados = function (n) {
                            this.estadosSeleccionados = n.elementos,
                                this.filtro.leido = 2 == this.estadosSeleccionados.length || 0 == this.estadosSeleccionados.length ? null : 0 == this.estadosSeleccionados[0]
                        },
                        n.prototype.seleccionarCuentas = function (n) {
                            this.cuentasSeleccionadas = [
                            ],
                                this.cuentasSeleccionadasAlias = n.elementos;
                            for (var e = 0, t = this.cuentasSeleccionadasAlias; e < t.length; e++) this.cuentasSeleccionadas.push(this.cuentasFiltro[t[e]].numero)
                        },
                        n.prototype.desseleccionarCheck = function (n, e) {
                            'estados-dropdown' == n ? this.estadosFilter.desseleccionar(e) : 'tipos-dropdown' == n ? this.tiposFilter.desseleccionar(e) : 'cuentas-dropdown' == n && this.ctasFilter.desseleccionar(e),
                                this.resetSecondFilter()
                        },
                        n.prototype.borrarFiltroFechas = function () {
                            this.fechasSeleccionadas = '',
                                this.datePicker.resetearSeleccion(),
                                this.filtro.fechaDesde = '',
                                this.filtro.fechaHasta = '',
                                this.resetSecondFilter()
                        },
                        n.prototype.borrarFiltroImportes = function () {
                            this.importesSeleccionados = '',
                                this.importesFilter.reiniciarFiltro(),
                                this.filtro.importeDesde = this.importeMin,
                                this.filtro.importeHasta = this.importeMax,
                                this.resetSecondFilter()
                        },
                        n.prototype.verMasFiltros = function () {
                            this.mostrarFiltrosMobile = !this.mostrarFiltrosMobile
                        },
                        n.prototype.onWindowScroll = function () {
                            var n = document.getElementsByClassName('dashboard-sidebar-container') [0];
                            if (n) {
                                var e = n.getBoundingClientRect(),
                                    t = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
                                e.top - t < 0 ? document.getElementById('action-buttons').classList.add('absolute') : document.getElementById('action-buttons').classList.remove('absolute')
                            }
                        },
                        n.prototype.goPedirDuplicado = function () {
                            this.utilsComponent.storage.isCustomModalClose = !0,
                                this._navigationControlService.navegarOperativaEnRuta(j.a.Correspondencia.Modulo, j.a.Correspondencia.OperativaDuplicados)
                        },
                        n.prototype.enableSolicitarDuplicado = function () {
                            var n = !1;
                            return (0 == this.countSeleccionados || this.countSeleccionados > s.a.Correspondencia.MaxSolicitudDuplicado) && (n = !0),
                                n
                        },
                        n.prototype.seleccionarImportes = function (n) {
                            if (this.importeMin = 0, this.importeMax = 999999, null == n.desde && null == n.hasta) this.importesSeleccionados = '';
                            else {
                                if (null != n.desde && null == n.hasta ? this.importesSeleccionados = 'Desde ' + n.desde + ' ' + this.confFiltroImporte.divisa : null == n.desde && null != n.hasta ? this.importesSeleccionados = 'Hasta ' + n.hasta + ' ' + this.confFiltroImporte.divisa : null != n.desde && null != n.hasta && (this.importesSeleccionados = 'De ' + n.desde + ' ' + this.confFiltroImporte.divisa + ' a ' + n.hasta + ' ' + this.confFiltroImporte.divisa), null != n.desde) {
                                    var e = n.desde;
                                    e = (e = e.split('.').join('')).replace(',', '.'),
                                        this.importeMin = parseFloat(e)
                                }
                                if (null != n.hasta) {
                                    var t = n.hasta;
                                    t = (t = t.split('.').join('')).replace(',', '.'),
                                        this.importeMax = parseFloat(t)
                                }
                                this.filtro.importeDesde = this.importeMin,
                                    this.filtro.importeHasta = this.importeMax
                            }
                        },
                        n.prototype.showMostrarMas = function () {
                            this.filtro.paginaAMostrar <= this.totalPaginas && (this.mostrarMas = this.filtro.paginaAMostrar != this.totalPaginas)
                        },
                        n.prototype.verMasCorrespondencia = function (n) {
                            this.filtro.paginaAMostrar++,
                                this.getDocumentos(),
                                this.mostrarMenos = !0
                        },
                        n.prototype.verMenosCorrespondencia = function (n) {
                            this.mostrarMenos = !1,
                                this.filtro.paginaAMostrar = 1,
                                this.ResetCorrespondencia(),
                                this.getDocumentos()
                        },
                        n.prototype.SetUpListadoAgrupaciones = function () {
                            this.agrupaciones = [
                            ],
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Valores,
                                    texto: s.a.Correspondencia.Agrupacion.Valores,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 4
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Tarjetas,
                                    texto: s.a.Correspondencia.Agrupacion.Tarjetas,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 5
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.SegurosAhorro,
                                    texto: s.a.Correspondencia.Agrupacion.SegurosAhorro,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 7
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Cartera,
                                    texto: s.a.Correspondencia.Agrupacion.Cartera,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 8
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Recibos,
                                    texto: s.a.Correspondencia.Agrupacion.Recibos,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 11
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Extractos,
                                    texto: s.a.Correspondencia.Agrupacion.Extractos,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 13
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.InfFiscal,
                                    texto: s.a.Correspondencia.Agrupacion.InfFiscal,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 14
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.BancaDigital,
                                    texto: s.a.Correspondencia.Agrupacion.BancaDigital,
                                    esParticular: !0,
                                    esNegocio: !0,
                                    orden: 17
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Ahorro,
                                    texto: s.a.Correspondencia.Agrupacion.Ahorro,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 1
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Fondos,
                                    texto: s.a.Correspondencia.Agrupacion.Fondos,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 2
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Planes,
                                    texto: s.a.Correspondencia.Agrupacion.Planes,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 3
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Financiación,
                                    texto: s.a.Correspondencia.Agrupacion.Financiación,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 6
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Contratos,
                                    texto: s.a.Correspondencia.Agrupacion.Contratos,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 12
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.OtrosDocumentos,
                                    texto: s.a.Correspondencia.Agrupacion.OtrosDocumentos,
                                    esParticular: !0,
                                    esNegocio: !1,
                                    orden: 99
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.AhorroFinanciacion,
                                    texto: s.a.Correspondencia.Agrupacion.AhorroFinanciacion,
                                    esParticular: !1,
                                    esNegocio: !0,
                                    orden: 9
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.FondosPlanes,
                                    texto: s.a.Correspondencia.Agrupacion.FondosPlanes,
                                    esParticular: !1,
                                    esNegocio: !0,
                                    orden: 15
                                }),
                                this.agrupaciones.push({
                                    id: s.a.Correspondencia.IdAgrupacion.Transferencias,
                                    texto: s.a.Correspondencia.Agrupacion.Transferencias,
                                    esParticular: !1,
                                    esNegocio: !0,
                                    orden: 16
                                })
                        },
                        n.prototype.SetUpCuentasProductosTodos = function (n) {
                            var e = this;
                            this.cuentasProductos = [
                            ],
                            n.cuentas && n.cuentas.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.iban.substring(4),
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })),
                            n.tarjetas && n.tarjetas.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.pan,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: null
                                })
                            })),
                            n.comercio && n.comercio.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: null
                                })
                            })),
                            n.sumatorio.financiacion && (n.sumatorio.financiacion.avales.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.confirming.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.factoring.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.leasing.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.lineasDescuento.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.multiproductos.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.otros.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.financiacion.prestamos.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            }))),
                            n.sumatorio.seguros && (n.sumatorio.seguros.otros.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.seguros.segurosRiesgo.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            }))),
                            n.sumatorio.inversion && (n.sumatorio.inversion.depositos.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.fondos.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.otros.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.planesAhorro.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.planesPrevision.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.planesPension.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.inversion.valores.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            }))),
                            n.sumatorio.comercioExterior && (n.sumatorio.comercioExterior.cobrosPagosNacionalesInternacionales.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.comercioExterior.creditosDocumentarios.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.comercioExterior.otros.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })), n.sumatorio.comercioExterior.segurosCambio.forEach((function (n) {
                                n.ocultoBuzon || e.cuentasProductos.push({
                                    numero: n.numero,
                                    alias: n.alias,
                                    claseCuenta: n.claseCuenta,
                                    iban: n.iban
                                })
                            })))
                        },
                        n.prototype.goToPanelNavegacion = function (n) {
                            this._navigationPanelService.navegar(n.item)
                        },
                        n.prototype.reload = function (n) {
                            this.getDocumentos()
                        },
                        n
                }(),
                D = t('7duk'),
                T = t('EExS'),
                E = t('/uHP'),
                N = t('6O62'),
                A = function () {
                    function n(n, e, t, o, l) {
                        var i = this;
                        this.utilsComponent = n,
                            this.alertService = e,
                            this.personalizacionService = t,
                            this.productoConsultaService = o,
                            this._contadorCorrespondenciaService = l,
                            this.refrescarAjustes = new S.a,
                            this.cacheProductos$ = new P.a(new E.a),
                            this.getProductos = this.cacheProductos$.asObservable(),
                            this.unsubscribe = new S.a,
                            this.productoConsultaService.getProductos.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (n) {
                                if (n.error) {
                                    var e = new E.a;
                                    e.loaded = !1,
                                        e.error = !0,
                                        e.result = i.productosCached,
                                        i.cacheProductos$.next(e)
                                } else n.loaded && i.raiseProductosModificados(n.result)
                            }), (function (n) {
                                var e = new E.a;
                                e.loaded = !1,
                                    e.error = !0,
                                    e.result = i.productosCached,
                                    i.cacheProductos$.next(e)
                            }))
                    }
                    return n.prototype.raiseProductosModificados = function (n) {
                        var e = [
                            'Producto/Alias',
                            'Número producto',
                            'Visibilidad del Buzón'
                        ];
                        this.productosCached = this.obtenerTipos();
                        var t = s.a.SeccionesURI.CuentasTarjetasTPV,
                            o = this.productosCached.find((function (n) {
                                return n.id == t
                            }));
                        o && (n.cuentas.length > 0 && o.productosSeccion.push(this.MapPosGlobalToSeccionBuzon(s.a.ProductosURI.Cuenta, s.a.ProductosPersonalizacion.Cuenta, e, n.cuentas)), n.tarjetas.length > 0 && o.productosSeccion.push(this.MapPosGlobalToSeccionBuzon(s.a.ProductosURI.Tarjeta, s.a.ProductosPersonalizacion.Tarjeta, e, n.tarjetas)), n.comercio.length > 0 && o.productosSeccion.push(this.MapPosGlobalToSeccionBuzon(s.a.ProductosURI.Comercio, s.a.ProductosPersonalizacion.Comercio, e, n.comercio))),
                            t = s.a.SeccionesURI.Inversion,
                        (o = this.productosCached.find((function (n) {
                            return n.id == t
                        }))) && (n.sumatorio.inversion.depositos.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.DepositoPlazos, s.a.ProductosPersonalizacion.DepositoPlazos, e, n.sumatorio.inversion.depositos)), n.sumatorio.inversion.fondos.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Fondos, s.a.ProductosPersonalizacion.Fondos, e, n.sumatorio.inversion.fondos)), n.sumatorio.inversion.planesAhorro.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.PlanAhorro, s.a.ProductosPersonalizacion.PlanAhorro, e, n.sumatorio.inversion.planesAhorro)), n.sumatorio.inversion.planesPrevision.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.PlanPrevision, s.a.ProductosPersonalizacion.PlanPrevision, e, n.sumatorio.inversion.planesPrevision)), n.sumatorio.inversion.planesPension.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.PlanPensiones, s.a.ProductosPersonalizacion.PlanPensiones, e, n.sumatorio.inversion.planesPension)), n.sumatorio.inversion.valores.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Valores, s.a.ProductosPersonalizacion.Valores, e, n.sumatorio.inversion.valores)), n.sumatorio.inversion.otros.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Otros, s.a.ProductosPersonalizacion.Otros, e, n.sumatorio.inversion.otros))),
                            t = s.a.SeccionesURI.Financiacion,
                        (o = this.productosCached.find((function (n) {
                            return n.id == t
                        }))) && (n.sumatorio.financiacion.avales.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Avales, s.a.ProductosPersonalizacion.Avales, e, n.sumatorio.financiacion.avales)), n.sumatorio.financiacion.confirming.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Confirming, s.a.ProductosPersonalizacion.Confirming, e, n.sumatorio.financiacion.confirming)), n.sumatorio.financiacion.factoring.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Factoring, s.a.ProductosPersonalizacion.Factoring, e, n.sumatorio.financiacion.factoring)), n.sumatorio.financiacion.leasing.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Leasing, s.a.ProductosPersonalizacion.Leasing, e, n.sumatorio.financiacion.leasing)), n.sumatorio.financiacion.lineasDescuento.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.LineasDescuento, s.a.ProductosPersonalizacion.LineasDescuento, e, n.sumatorio.financiacion.lineasDescuento)), n.sumatorio.financiacion.multiproductos.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Multiproducto, s.a.ProductosPersonalizacion.Multiproducto, e, n.sumatorio.financiacion.multiproductos)), n.sumatorio.financiacion.otros.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Otros, s.a.ProductosPersonalizacion.Otros, e, n.sumatorio.financiacion.otros)), n.sumatorio.financiacion.prestamos.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Prestamos, s.a.ProductosPersonalizacion.Prestamos, e, n.sumatorio.financiacion.prestamos))),
                            t = s.a.SeccionesURI.Seguros,
                        (o = this.productosCached.find((function (n) {
                            return n.id == t
                        }))) && (n.sumatorio.seguros.otros.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Otros, s.a.ProductosPersonalizacion.Otros, e, n.sumatorio.seguros.otros)), n.sumatorio.seguros.segurosRiesgo.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.SegurosRiesgo, s.a.ProductosPersonalizacion.SegurosRiesgo, e, n.sumatorio.seguros.segurosRiesgo))),
                            t = s.a.SeccionesURI.COMEX,
                        (o = this.productosCached.find((function (n) {
                            return n.id == t
                        }))) && (n.sumatorio.comercioExterior.otros.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Otros, s.a.ProductosPersonalizacion.Otros, e, n.sumatorio.comercioExterior.otros)), n.sumatorio.comercioExterior.cobrosPagosNacionalesInternacionales.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.Cpni, s.a.ProductosPersonalizacion.Cpni, e, n.sumatorio.comercioExterior.cobrosPagosNacionalesInternacionales)), n.sumatorio.comercioExterior.creditosDocumentarios.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.CreditoDocumentario, s.a.ProductosPersonalizacion.CreditoDocumentario, e, n.sumatorio.comercioExterior.creditosDocumentarios)), n.sumatorio.comercioExterior.segurosCambio.length > 0 && o.productosSeccion.push(this.MapProductosToSeccionBuzon(s.a.ProductosURI.SegurosCambio, s.a.ProductosPersonalizacion.SegurosCambio, e, n.sumatorio.comercioExterior.segurosCambio)));
                        var l = new E.a;
                        l.loaded = !0,
                            l.result = this.productosCached,
                            this.cacheProductos$.next(l)
                    },
                        n.prototype.GetBuzonSeccion = function (n, e, t, o) {
                            return {
                                id: n,
                                titulo: e,
                                headers: t,
                                mostrarTodos: !0,
                                items: o
                            }
                        },
                        n.prototype.MapPosGlobalToSeccionBuzon = function (n, e, t, o) {
                            return {
                                id: n,
                                titulo: e,
                                headers: t,
                                mostrarTodos: !0,
                                items: this.MapPosGlobalToBuzonItem(o, e)
                            }
                        },
                        n.prototype.MapProductosToSeccionBuzon = function (n, e, t, o) {
                            return {
                                id: n,
                                titulo: e,
                                headers: t,
                                mostrarTodos: !0,
                                items: this.MapProductoToBuzonItem(o, e)
                            }
                        },
                        n.prototype.MapPosGlobalToBuzonItem = function (n, e) {
                            var t,
                                o = this,
                                l = [
                                ];
                            return n.forEach((function (n) {
                                t = o.setNumeroProducto(n, e),
                                    l.push({
                                        id: t.idProducto,
                                        alias: n.alias,
                                        nProducto: t.producto,
                                        order: n.orden,
                                        visibilidad: !n.ocultoBuzon,
                                        claseCuenta: n.claseCuenta
                                    })
                            })),
                                l
                        },
                        n.prototype.MapProductoToBuzonItem = function (n, e) {
                            var t,
                                o = this,
                                l = [
                                ];
                            return n.forEach((function (n) {
                                t = o.setNumeroProducto(n, e),
                                    l.push({
                                        id: t.idProducto,
                                        alias: n.alias,
                                        nProducto: t.producto,
                                        order: n.orden,
                                        visibilidad: !n.ocultoBuzon,
                                        claseCuenta: n.claseCuenta
                                    })
                            })),
                                l
                        },
                        n.prototype.setNumeroProducto = function (n, e) {
                            var t;
                            switch (e) {
                                case s.a.ProductosURI.Tarjeta:
                                    t = {
                                        producto: n.pan,
                                        idProducto: n.pan
                                    };
                                    break;
                                case s.a.ProductosURI.Cuenta:
                                    t = {
                                        producto: n.iban,
                                        idProducto: n.numero
                                    };
                                    break;
                                case s.a.ProductosURI.Comercio:
                                default:
                                    t = {
                                        producto: n.numero,
                                        idProducto: n.numero
                                    }
                            }
                            return t
                        },
                        n.prototype.obtenerTipos = function () {
                            var n = [
                            ];
                            return n.push(this.utilsComponent.storage.contratoSeleccionado.negocio ? {
                                    id: s.a.SeccionesURI.CuentasTarjetasTPV,
                                    texto: s.a.Titulos.Personalizacion.CuentasTarjetasComercios,
                                    productosSeccion: [
                                    ]
                                }
                                : {
                                    id: s.a.SeccionesURI.CuentasTarjetasTPV,
                                    texto: s.a.Titulos.Personalizacion.CuentasTarjetas,
                                    productosSeccion: [
                                    ]
                                }),
                                n.push({
                                    id: s.a.SeccionesURI.Inversion,
                                    texto: s.a.Titulos.Personalizacion.Inversion,
                                    productosSeccion: [
                                    ]
                                }),
                                n.push({
                                    id: s.a.SeccionesURI.Financiacion,
                                    texto: s.a.Titulos.Personalizacion.Financiacion,
                                    productosSeccion: [
                                    ]
                                }),
                                n.push({
                                    id: s.a.SeccionesURI.Seguros,
                                    texto: s.a.Titulos.Personalizacion.Seguros,
                                    productosSeccion: [
                                    ]
                                }),
                            this.utilsComponent.storage.contratoSeleccionado.negocio && n.push({
                                id: s.a.SeccionesURI.COMEX,
                                texto: s.a.Titulos.Personalizacion.COMEX,
                                productosSeccion: [
                                ]
                            }),
                                n
                        },
                        n.prototype.ordenarProductos = function (n) {
                            return n.forEach((function (n) {
                                n.items.sort((function (n, e) {
                                    return (n.order > e.order || null == n.order || 0 == n.order) && 0 != e.order ? 1 : e.order > n.order || 0 == e.order ? - 1 : 0
                                }))
                            })),
                                n
                        },
                        n.prototype.guardarProductos = function (n) {
                            var e = this;
                            if (n) {
                                for (var t = [
                                ], o = 0, l = n; o < l.length; o++) {
                                    var i = l[o],
                                        a = [
                                        ];
                                    a.push({
                                        Property: 'OcultoBuzon',
                                        Value: (!i.producto.visibilidad).toString()
                                    }),
                                        t.push({
                                            IdProducto: i.producto.id,
                                            TipoProducto: i.producto.claseCuenta,
                                            Propiedades: a
                                        })
                                }
                                this.personalizacionService.postProductos(t).subscribe((function (t) {
                                    e.alertService.changeStatus(t ? {
                                            estado: 1,
                                            texto: null
                                        }
                                        : {
                                            estado: 2,
                                            texto: null
                                        }),
                                        e.productoConsultaService.editadoOcultoBuzon(n.map((function (n) {
                                            return {
                                                numero: n.producto.id,
                                                claseCuenta: n.producto.claseCuenta,
                                                ocultoBuzon: !n.producto.visibilidad
                                            }
                                        }))),
                                        e._contadorCorrespondenciaService.invalidarCacheContador()
                                }), (function (n) {
                                    e.alertService.changeStatus({
                                        estado: 2,
                                        texto: null
                                    })
                                })),
                                    this.refrescarAjustes.next(!0)
                            } else this.alertService.changeStatus({
                                estado: 2,
                                texto: null
                            })
                        },
                        n.ngInjectableDef = o.defineInjectable({
                            factory: function () {
                                return new n(o.inject(a.a), o.inject(T.a), o.inject(N.a), o.inject(x.a), o.inject(R.a))
                            },
                            token: n,
                            providedIn: 'root'
                        }),
                        n
                }(),
                V = function () {
                    function n(n, e, t, o, l, i, a) {
                        this._buzonService = n,
                            this._loadingService = e,
                            this._navigationPanelService = t,
                            this._navigationControlService = o,
                            this.responsive = l,
                            this._contadorCorrespondenciaService = i,
                            this.utilsComponent = a,
                            this.tipos = [
                            ],
                            this.tipoSeleccionado = null,
                            this.showTooltip = !1,
                            this.productosOriginal = [
                            ],
                            this.productosSinModificar = [
                            ],
                            this.productosModificados = [
                            ],
                            this.productosSeleccionado = [
                            ],
                            this.tooltipAjustes = !1,
                            this.unsubscribe = new S.a,
                            this.loading = {
                                type: 'ajustes-buzon',
                                active: !0
                            },
                            this.navigationPanel = {
                                menu: [
                                ],
                                isDashboard: !0,
                                isBuzon: !0,
                                isProducto: !1,
                                seleccionado: null
                            },
                            this.configuracionBack = {
                                copiarDatos: !1,
                                editable: !1,
                                esModal: !1,
                                maxLength: null,
                                titulo: 'Buzón de correspondencia',
                                icono_subtitulo: null,
                                texto_subtitulo: null
                            }
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this.tipos = this._buzonService.obtenerTipos(),
                            this.productosSeccionesBuzon = this._buzonService.getProductos,
                            this.productosSeccionesBuzon.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (e) {
                                e.loaded && !e.error && (n.productosOriginal = e.result, n.cargarPrimeraVezDatos(), n._loadingService.changeStatus({
                                    type: 'ajustes-buzon',
                                    active: !1
                                }))
                            })),
                            this._buzonService.refrescarAjustes.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (e) {
                                e && (n.productosModificados = [
                                ])
                            })),
                            this._loadingService.currentStatus.subscribe((function (e) {
                                e.type == n.loading.type && (n.loading.active = e.active)
                            })),
                            this.cargarPanelNavegacion(),
                            this.cargarSumatorios()
                    },
                        n.prototype.cargarPanelNavegacion = function () {
                            var n = this,
                                e = this._navigationControlService.pathActual;
                            this._navigationPanelService.menuNavegacion.pipe(Object(w.a) (this.unsubscribe)).subscribe((function (t) {
                                n.navigationPanel.menu = t,
                                    n.navigationPanel.seleccionado = t.filter((function (n) {
                                        return n.path === e
                                    })) [0]
                            })),
                                this._navigationPanelService.getSeccionesCorrespondencia(e)
                        },
                        n.prototype.cargarSumatorios = function () {
                            var n = this;
                            this.subscriptionToContadores || (this.subscriptionToContadores = this._contadorCorrespondenciaService.getDatosContador().pipe(Object(w.a) (this.unsubscribe)).subscribe((function (e) {
                                var t = 0,
                                    o = 0;
                                e.loaded && !e.error && (t = e.result.totalNoLeidos, o = e.result.destacadosNoLeidos),
                                    n.itemsSumatorios = [
                                        {
                                            titulo: s.a.Titulos.Pendientes,
                                            valor: t,
                                            moneda: null,
                                            esMoneda: !1,
                                            class : 'blue',
                                            tieneTooltip: !1,
                                            tieneClick: !0
                                        },
                                        {
                                            titulo: s.a.Titulos.Destacados,
                                            valor: o,
                                            moneda: null,
                                            esMoneda: !1,
                                            class : null,
                                            tieneTooltip: !1,
                                            tieneClick: !0
                                        }
                                    ]
                            })))
                        },
                        n.prototype.cargarPrimeraVezDatos = function () {
                            this.productosSinModificar = JSON.parse(JSON.stringify(this.productosOriginal)),
                                null != this.tipoSeleccionado ? this.actualizarSeccion() : (this.tipoSeleccionado = this.tipos[0], this.productosSeleccionado = this.productosSinModificar[0].productosSeccion)
                        },
                        n.prototype.seleccionar = function (n) {
                            n.item != this.tipoSeleccionado && (this.tipoSeleccionado = n.item, this.actualizarSeccion())
                        },
                        n.prototype.actualizarSeccion = function () {
                            var n = this;
                            this.productosSeleccionado = null,
                                this.productosSinModificar = JSON.parse(JSON.stringify(this.productosOriginal));
                            var e = this.productosSinModificar.filter((function (e) {
                                return e.id == n.tipoSeleccionado.id
                            })) [0];
                            e ? (this.productosSeleccionado = e.productosSeccion, this.productosModificados = [
                            ]) : this.productosSeleccionado = null
                        },
                        n.prototype.guardarCambios = function () {
                            this._buzonService.guardarProductos(this.productosModificados)
                        },
                        n.prototype.checkCambios = function () {
                            return this.productosModificados.length > 0 ? (this.positionBotonDescarga(), !1) : (this.positionBotonDescarga(), !0)
                        },
                        n.prototype.obtenerItems = function (n, e) {
                            var t = e.items.filter((function (e) {
                                return e.id == n.item.id
                            })) [0];
                            if (this.productosModificados.length > 0) {
                                var o = this.productosModificados.indexOf(this.productosModificados.find((function (e) {
                                    return e.producto == t && e.item.id == n.itemId
                                })));
                                o > - 1 ? this.productosModificados.splice(o, 1) : this.productosModificados.push({
                                    tipoProducto: n.claseCuenta,
                                    producto: t,
                                    item: {
                                        id: n.itemId,
                                        estado: t.visibilidad
                                    }
                                })
                            } else this.productosModificados.push({
                                tipoProducto: n.claseCuenta,
                                producto: t,
                                item: {
                                    id: n.itemId,
                                    estado: t.visibilidad
                                }
                            })
                        },
                        n.prototype.ngOnDestroy = function () {
                            this.unsubscribe.next(),
                                this.unsubscribe.complete(),
                                this._contadorCorrespondenciaService.getDatosContador()
                        },
                        n.prototype.goToPanelNavegacion = function (n) {
                            this._navigationPanelService.navegar(n.item)
                        },
                        n.prototype.positionBotonDescarga = function () {
                            var n = document.getElementById('botones-guardar'),
                                e = document.getElementById('table-contenedor');
                            n && (window.innerHeight - e.getBoundingClientRect().bottom - n.getBoundingClientRect().height < 0 ? n.classList.add('fixed') : n.classList.remove('fixed'), n.getBoundingClientRect().top < e.getBoundingClientRect().top + 140 ? n.classList.add('hide') : n.classList.remove('hide'))
                        },
                        n.prototype.onResize = function (n) {
                            this.positionBotonDescarga()
                        },
                        n.prototype.onWindowScroll = function () {
                            this.positionBotonDescarga()
                        },
                        n
                }(),
                B = function () {
                    return function (n) {
                        this.auth = n
                    }
                }(),
                U = t('pMnS'),
                L = t('YvNp'),
                $ = t('+hqF'),
                K = t('aHHB'),
                G = t('bXK5'),
                H = t('Ip0R'),
                q = t('EEny'),
                W = t('8zQ8'),
                J = t('4GxJ'),
                X = t('HB/b'),
                Z = t('iZGF'),
                Y = t('pjlW'),
                Q = t('omV9'),
                nn = t('GGOM'),
                en = t('vDcr'),
                tn = t('52tO'),
                on = t('mHW+'),
                ln = t('2/BW'),
                an = t('Q/Kr'),
                cn = t('bqDX'),
                rn = t('Rgyd'),
                sn = t('V0EM'),
                un = t('+EBe'),
                dn = t('Wr/j'),
                pn = t('hAVK'),
                gn = t('LnLi'),
                fn = t('2//T'),
                Cn = t('N/Hn'),
                mn = t('Axip'),
                Pn = t('kgSu'),
                Mn = t('kpld'),
                hn = t('eqBE'),
                On = t('TGwn'),
                bn = t('3Ikc'),
                _n = t('z7ld'),
                vn = t('UCBJ'),
                xn = t('P0hM'),
                wn = t('6BXu'),
                Sn = t('JCHN'),
                yn = t('CIIx'),
                In = t('BCuW'),
                kn = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.correspondencia-container[_ngcontent-%COMP%]{padding:59px 54px 152px;position:relative}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]{background-color:#fff;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);border-radius:2px;padding:0 16px 0 24px;margin-top:20px;height:60px;display:flex;align-items:center}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;width:calc(100% - 48px)}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #select-option[_ngcontent-%COMP%]{font-size:7px;text-align:left;height:20px;width:30px;padding-left:6px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]{display:flex;justify-content:space-between;align-items:center;width:calc(100% - 50px);padding:0 1%}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]{padding:16px 0}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#2d5b7f;display:inline-block;vertical-align:middle}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span.ibercaja-icon-Mail[_ngcontent-%COMP%]{font-size:1rem}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span.ibercaja-icon-Buzon[_ngcontent-%COMP%]{font-size:.6875rem}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span.ibercaja-icon-Mail-abierto[_ngcontent-%COMP%]{font-size:1.0625rem}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span.ibercaja-icon-Copiar[_ngcontent-%COMP%]{font-size:1.1875rem}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]   span.label[_ngcontent-%COMP%]{margin-left:8px;font-family:Ibercaja-Medium,sans-serif;font-size:.8125rem}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .separator[_ngcontent-%COMP%]{color:rgba(45,91,127,.2);font-size:15px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .tabs-icon[_ngcontent-%COMP%]{font-size:18px;height:48px;width:48px;border-radius:2px}.correspondencia-container[_ngcontent-%COMP%]   .select-list[_ngcontent-%COMP%]{margin-top:-16px;left:76px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]{width:100%;height:auto;max-height:0;opacity:0;display:flex;flex-wrap:wrap;justify-content:space-between;transition:all .3s ease;visibility:hidden}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]{display:flex;flex-wrap:wrap;justify-content:space-between;width:100%;padding-bottom:31px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > *[_ngcontent-%COMP%]{width:calc((100% - 120px)/ 5)}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .button-container[_ngcontent-%COMP%]{width:100%;text-align:right;margin-top:12px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]{padding-top:29px;width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]{background-color:#2d5b7f;border-radius:10000px;color:#f5f8fa;font-family:Ibercaja-Medium,sans-serif;font-size:.75rem;padding:4px 8px;display:inline-flex;align-items:center;margin-right:16px;margin-bottom:9px;-webkit-animation-name:fadeIn;animation-name:fadeIn;-webkit-animation-duration:.2s;animation-duration:.2s}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{padding:4px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]{padding:4px;vertical-align:middle;margin-left:8px;cursor:pointer}.correspondencia-container[_ngcontent-%COMP%]   .filter-container.show[_ngcontent-%COMP%]{max-height:none;opacity:1;padding-top:40px;visibility:visible}.correspondencia-container[_ngcontent-%COMP%]   .filter-container.show.second[_ngcontent-%COMP%]{padding-top:0;z-index:999}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]{padding-top:29px;width:100%}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]{background-color:#2d5b7f;border-radius:10000px;color:#f5f8fa;font-family:Ibercaja-Medium,sans-serif;font-size:.75rem;padding:4px 8px;display:inline-flex;align-items:center;margin-right:16px;margin-bottom:9px;-webkit-animation-name:fadeIn;animation-name:fadeIn;-webkit-animation-duration:.2s;animation-duration:.2s}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{padding:4px}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]{padding:4px;vertical-align:middle;margin-left:8px;cursor:pointer}.correspondencia-container[_ngcontent-%COMP%]   .result-container[_ngcontent-%COMP%]{position:relative}.correspondencia-container[_ngcontent-%COMP%]   .result-container[_ngcontent-%COMP%]   .section-title[_ngcontent-%COMP%]{color:#0b7ad0;font-size:1rem;text-transform:capitalize;font-family:Ibercaja-Medium,sans-serif}.correspondencia-container[_ngcontent-%COMP%]   .result-container[_ngcontent-%COMP%]   .section[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]{margin-top:16px}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]{box-shadow:none}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]{justify-content:space-between;padding:0 24px}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%] > div[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif;text-transform:uppercase;font-size:.8125rem;color:#33393e}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]{display:flex;align-items:center;justify-content:flex-start;width:calc(54% - 27px);margin-right:27px}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:first-child{width:55%;margin-right:32px;margin-left:109px;white-space:nowrap}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(2){width:auto;min-width:58px}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]{width:46%;display:flex;align-items:center;justify-content:space-between}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(1){width:36%}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(2){min-width:170px;width:46%}.correspondencia-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(3){width:calc(18% - 32px);margin-left:32px;display:block;height:10px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]{display:flex;align-items:center;justify-content:space-between;text-transform:uppercase;font-family:Ibercaja-Regular,sans-serif;font-size:.875rem;color:rgba(51,57,62,.7);border-bottom:1px solid rgba(45,91,127,.2);background-color:transparent;transition:background-color .2s ease;height:60px;padding:0 24px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]{width:calc(54% - 27px);display:flex;align-items:center;margin-right:27px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   input[_ngcontent-%COMP%] + div[_ngcontent-%COMP%]{margin-right:27px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   div.icon.destacado[_ngcontent-%COMP%]{width:12px;margin-right:27px;visibility:hidden;cursor:pointer}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   div.icon.destacado.ibercaja-icon-Destacado-filled[_ngcontent-%COMP%]{color:#6c7176;visibility:visible}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   .mail-indicator[_ngcontent-%COMP%]{height:7px;width:7px;border-radius:7px;margin-right:16px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]{width:55%;margin-right:32px;overflow:hidden;text-overflow:ellipsis}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]{width:46%;display:flex;align-items:center;justify-content:space-between}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%]{width:36%}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .account-number[_ngcontent-%COMP%]{min-width:52px;width:10%}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .type[_ngcontent-%COMP%]{text-align:right;width:calc(54% - 32px);margin-left:32px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item.unread[_ngcontent-%COMP%]{color:#33393e}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item.unread[_ngcontent-%COMP%]   .mail-indicator[_ngcontent-%COMP%]{background-color:#0b7ad0}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item.unread[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item.selected[_ngcontent-%COMP%]{background-color:rgba(45,91,127,.1)}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]{padding:32px;text-align:center;background-color:#f4f7fd}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{display:inline-block;font-size:.75rem;vertical-align:middle;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;font-size:.6875rem;margin-left:24px}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #select-option[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #select-option[_ngcontent-%COMP%]:hover{cursor:pointer}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover{cursor:pointer}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover   span[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover   span[_ngcontent-%COMP%]{color:#0b7ad0}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .tabs-icon[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   .tabs-icon[_ngcontent-%COMP%]:hover{cursor:pointer}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]:hover{cursor:pointer}@-webkit-keyframes fadeIn{0%{opacity:0}100%{opacity:1}}@keyframes fadeIn{0%{opacity:0}100%{opacity:1}}@media screen and (max-width:1023px){.correspondencia-container[_ngcontent-%COMP%]{padding:24px 16px 84px;min-height:calc(100vh - 435px)}.correspondencia-container[_ngcontent-%COMP%]   .top-bar[_ngcontent-%COMP%]{display:flex;justify-content:space-between;align-items:center}.correspondencia-container[_ngcontent-%COMP%]   .top-bar[_ngcontent-%COMP%]   .tabs-icon[_ngcontent-%COMP%]{height:48px;width:48px;font-size:21px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]{background:0 0;box-shadow:none;border-radius:0;border-bottom:2px solid rgba(49,56,64,.3);height:60px;margin-top:0;padding:0}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]{padding-right:17px;position:relative;font-size:.8125rem;font-family:Ibercaja-Medium,sans-serif;color:#33393e;margin-left:8px;text-transform:lowercase}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]:before{position:absolute;right:0;font-size:6px;content:"\\e91c";top:calc((.8125rem - 6px)/ 2);font-family:ibercaja-icon-font,fantasy!important;speak:none;font-style:normal;font-weight:400;font-variant:normal;text-transform:none;line-height:1;-webkit-font-smoothing:antialiased}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]{position:fixed;z-index:4;padding:0 16px;width:100%;bottom:0;left:0;height:60px;background-color:#fff;box-shadow:0 0 4px 0 rgba(0,0,0,.1);display:flex;justify-content:space-between;align-items:center}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]{color:#2d5b7f}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[class^=ibercaja-icon][_ngcontent-%COMP%]{height:28px;width:28px;line-height:28px;text-align:center}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[class^=ibercaja-icon][_ngcontent-%COMP%]   .ibercaja-icon-Copiar[_ngcontent-%COMP%], .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[class^=ibercaja-icon][_ngcontent-%COMP%]   .ibercaja-icon-Mail-abierto[_ngcontent-%COMP%], .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[class^=ibercaja-icon].ibercaja-icon-Mail[_ngcontent-%COMP%]{font-size:19px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span[class^=ibercaja-icon].ibercaja-icon-Buzon[_ngcontent-%COMP%]{font-size:13px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > span.label[_ngcontent-%COMP%]{font-size:.8125rem;font-family:Ibercaja-Medium,sans-serif;margin-left:8px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons.absolute[_ngcontent-%COMP%]{position:absolute;bottom:0}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]{width:100%;height:0;max-height:0;opacity:0;transition:max-height .2s ease-out}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]{padding-bottom:0;display:flex;justify-content:space-between}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > *[_ngcontent-%COMP%]{max-width:calc((100% - 60px)/ 3);width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child{margin-bottom:30px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:last-child, .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-last-child(2){max-width:calc((100% - 30px)/ 2)}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]{padding-top:29px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]{background-color:#2d5b7f;border-radius:10000px;color:#f5f8fa;font-family:Ibercaja-Medium,sans-serif;font-size:.75rem;padding:4px 8px;display:inline-flex;align-items:center;margin-right:16px;margin-bottom:9px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{padding:4px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]{padding:4px;vertical-align:middle;margin-left:8px;cursor:pointer}.correspondencia-container[_ngcontent-%COMP%]   .filter-container.show[_ngcontent-%COMP%]{height:auto;opacity:1;padding-top:40px;max-height:none;padding-bottom:40px;transition:all .2s ease-in}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]{padding-top:29px}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]{background-color:#2d5b7f;border-radius:10000px;color:#f5f8fa;font-family:Ibercaja-Medium,sans-serif;font-size:.75rem;padding:4px 8px;display:inline-flex;align-items:center;margin-right:16px;margin-bottom:9px}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{padding:4px}.correspondencia-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]   .tag[_ngcontent-%COMP%]   .icon[_ngcontent-%COMP%]{padding:4px;vertical-align:middle;margin-left:8px;cursor:pointer}.correspondencia-container[_ngcontent-%COMP%]   .select-list[_ngcontent-%COMP%]{margin-top:-21px;left:16px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]{margin:32px -16px 0}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]{padding:0 16px;height:auto;min-height:89px;border-bottom:0;position:relative}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]:before{content:\' \';display:block;height:1px;width:calc(100% - 32px);background-color:rgba(45,91,127,.2);position:absolute;bottom:0}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]{width:50px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{padding-right:30px;margin-right:0;width:50px;height:50px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .left[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]:before{top:15px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]{width:calc(100% - 50px);flex-wrap:wrap;position:relative;align-items:initial;padding-bottom:8px;padding-top:8px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .mail-indicator[_ngcontent-%COMP%]{position:absolute;height:7px;width:7px;border-radius:7px;left:-19px;top:calc(1.4375rem / 2)}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]{width:90%;font-family:Ibercaja-Regular,sans-serif;font-size:.875rem;color:#33393e;margin-bottom:12px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   div.icon.destacado[_ngcontent-%COMP%]{padding:9px;position:relative;top:-9px;right:-9px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   div.icon.destacado.ibercaja-icon-Destacado-filled[_ngcontent-%COMP%]{color:#6c7176}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .date-tag[_ngcontent-%COMP%]{width:58px;margin-bottom:16px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%]{width:calc(100% - 68px);text-align:left;font-family:Ibercaja-Regular,sans-serif;font-size:.875rem;color:#33393e;line-height:24px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .account-number[_ngcontent-%COMP%]{width:50%;margin-left:0;text-align:left;color:rgba(51,57,62,.5)}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .type[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.875rem;color:#33393e}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item.unread[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .mail-title[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:hover{color:#0b7ad0;cursor:pointer}.click-device[_nghost-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > span[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > span[_ngcontent-%COMP%]{color:#0b7ad0;cursor:pointer}}@media screen and (max-width:767px){.correspondencia-container[_ngcontent-%COMP%], .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]{position:relative}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]{max-height:0;opacity:0;visibility:hidden;position:absolute;top:0;left:calc((100% - 208px)/ 2);background-color:#fff;width:208px;padding:16px 0;text-align:center;z-index:1}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > div[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]{display:block;width:100%;height:40px;color:#2d5b7f;font-family:Ibercaja-Medium,sans-serif;font-size:.8125rem;line-height:40px}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:before{content:" ";height:20px;width:20px;transform:rotate(45deg);background-color:#fff;border-radius:30% 0;position:absolute;bottom:-10px;left:calc((100% - 20px)/ 2)}.correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%] > div.show[_ngcontent-%COMP%]{max-height:150px;opacity:1;visibility:visible;top:-144px;transition:all .15s ease-in}.correspondencia-container[_ngcontent-%COMP%]   .background.show[_ngcontent-%COMP%]{height:100%;width:100%;position:fixed;top:0;left:0;background-color:rgba(49,56,64,.9);-webkit-animation-name:fadeIn;animation-name:fadeIn;-webkit-animation-duration:.2s;animation-duration:.2s;z-index:3}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]{display:flex;justify-content:space-between;flex-wrap:wrap;width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > *[_ngcontent-%COMP%]{padding-bottom:24px;display:block;width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > .filter-dropdown[_ngcontent-%COMP%], .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > .view-more-container[_ngcontent-%COMP%]{padding-bottom:0}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > .filter-dropdown[_ngcontent-%COMP%]:not(.hidden) > *[_ngcontent-%COMP%], .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > .view-more-container[_ngcontent-%COMP%]:not(.hidden) > *[_ngcontent-%COMP%]{padding-bottom:24px;display:block;width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child{width:100%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%]{display:flex;flex-wrap:wrap;justify-content:space-between}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child, .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2){width:47%}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .btn-primary-blue[_ngcontent-%COMP%]{height:37px;padding-bottom:0}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .btn-primary-blue[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-size:.8125rem}.correspondencia-container[_ngcontent-%COMP%]   .filter-container.show[_ngcontent-%COMP%]{padding-top:20px}.correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .seleccionados[_ngcontent-%COMP%]{padding-top:0}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]{padding:32px;text-align:center;background-color:#f4f7fd}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{display:inline-block;font-size:.75rem;vertical-align:middle;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.correspondencia-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;font-size:.6875rem;margin-left:24px}.correspondencia-container[_ngcontent-%COMP%]   .mail-list[_ngcontent-%COMP%]   .mail-item[_ngcontent-%COMP%]   .right[_ngcontent-%COMP%]   .type[_ngcontent-%COMP%]{width:auto;margin-left:0}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > span[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > span[_ngcontent-%COMP%]{color:#0b7ad0;cursor:pointer}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > div[_ngcontent-%COMP%]   button[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > div[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]{color:#2d5b7f}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > div[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .action-bar[_ngcontent-%COMP%]   #action-buttons[_ngcontent-%COMP%]   .action-btn[_ngcontent-%COMP%]:hover > div[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:hover{color:#0b7ad0;background-color:#f0f4f8;cursor:pointer}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]{display:flex;justify-content:space-between;flex-wrap:wrap}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(3), .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(3){width:100%}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%], .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%]{display:flex;justify-content:space-between}.click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child, .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child, .click-device[_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2), .click-device   [_nghost-%COMP%]   .correspondencia-container[_ngcontent-%COMP%]   .filter-container[_ngcontent-%COMP%]   .filter-wrap[_ngcontent-%COMP%]   .filter-dropdown[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2){width:calc((100% - 32px)/ 2)}}']
                    ],
                    data: {
                    }
                });
            function zn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'app-demo-info', [
                    ], null, null, null, L.b, L.a)),
                    o['ɵdid'](1, 114688, null, 0, $.a, [
                        a.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function Rn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'h3', [
                        ['class',
                            'title']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Documentos '
                    ]))
                ], null, null)
            }
            function jn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'top-bar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'h3', [
                        ['class',
                            'title']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Documentos'
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'button', [
                        ['class',
                            'ibercaja-icon-Filtros tabs-icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.mostrarFiltros = !l.mostrarFiltros) && o),
                            o
                    }), null, null))
                ], null, null)
            }
            function Fn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 28, 'div', [
                        ['class',
                            'action-bar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 26, 'div', [
                        ['class',
                            'left']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'id',
                            'checkbox-all'
                        ],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], null, [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, null) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](3, 81920, [
                        [6,
                            4]
                    ], 0, K.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](4, 0, null, null, 0, 'button', [
                        ['class',
                            'ibercaja-icon-Flecha-form-abajo'],
                        [
                            'id',
                            'select-option'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.mostrarSelectores = !l.mostrarSelectores) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 22, 'div', [
                        ['id',
                            'action-buttons']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('abrir') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'span', [
                        ['class',
                            'label'],
                        [
                            'title',
                            'Abrir seleccionados'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Abrir seleccionados'
                    ])),
                    (n() (), o['ɵeld'](10, 0, null, null, 1, 'span', [
                        ['class',
                            'separator']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        '|'
                    ])),
                    (n() (), o['ɵeld'](12, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('leido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](13, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail-abierto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](14, 0, null, null, 1, 'span', [
                        ['class',
                            'label'],
                        [
                            'title',
                            'Mostrar como leído'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Mostrar como leído'
                    ])),
                    (n() (), o['ɵeld'](16, 0, null, null, 1, 'span', [
                        ['class',
                            'separator']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        '|'
                    ])),
                    (n() (), o['ɵeld'](18, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('duplicado') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](19, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Copiar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](20, 0, null, null, 1, 'span', [
                        ['class',
                            'label'],
                        [
                            'title',
                            'Pedir duplicado'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Pedir duplicado'
                    ])),
                    (n() (), o['ɵeld'](22, 0, null, null, 1, 'span', [
                        ['class',
                            'separator']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        '|'
                    ])),
                    (n() (), o['ɵeld'](24, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('noLeido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](25, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Buzon']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](26, 0, null, null, 1, 'span', [
                        ['class',
                            'label'],
                        [
                            'title',
                            'Mostrar como no leído'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Mostrar como no leído'
                    ])),
                    (n() (), o['ɵeld'](28, 0, null, null, 0, 'button', [
                        ['class',
                            'ibercaja-icon-Filtros tabs-icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.mostrarFiltros = !l.mostrarFiltros) && o),
                            o
                    }), null, null))
                ], (function (n, e) {
                    n(e, 3, 0)
                }), (function (n, e) {
                    n(e, 18, 0, e.component.enableSolicitarDuplicado())
                }))
            }
            function Dn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 16, 'div', [
                        ['id',
                            'action-buttons']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('abrir') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Abrir seleccionados'
                    ])),
                    (n() (), o['ɵeld'](5, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('noLeido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Buzon']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Mostrar como no leído'
                    ])),
                    (n() (), o['ɵeld'](9, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('leido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](10, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail-abierto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Mostrar como leído'
                    ])),
                    (n() (), o['ɵeld'](13, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('duplicado') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](14, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Copiar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](15, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Pedir duplicado'
                    ]))
                ], null, (function (n, e) {
                    n(e, 13, 0, e.component.enableSolicitarDuplicado())
                }))
            }
            function Tn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 20, 'div', [
                        ['id',
                            'action-buttons']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('abrir') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Abrir'
                    ])),
                    (n() (), o['ɵeld'](5, 0, null, null, 11, 'button', [
                        ['class',
                            'action-btn']
                    ], null, [
                        [null,
                            'click'],
                        [
                            null,
                            'clickOutside'
                        ],
                        [
                            'document',
                            'click'
                        ],
                        [
                            'document',
                            'touch'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'document:click' === e && (l = !1 !== o['ɵnov'](n, 6).onClick(t.target) && l),
                        'document:touch' === e && (l = !1 !== o['ɵnov'](n, 6).onClick(t.target) && l),
                        'click' === e && (l = 0 != (i.verOpciones = !i.verOpciones) && l),
                        'clickOutside' === e && (l = 0 != (i.verOpciones = !1) && l),
                            l
                    }), null, null)),
                    o['ɵdid'](6, 16384, null, 0, G.a, [
                        o.ElementRef
                    ], null, {
                        clickOutside: 'clickOutside'
                    }),
                    (n() (), o['ɵeld'](7, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Mail-abierto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Marcar'
                    ])),
                    (n() (), o['ɵeld'](10, 0, null, null, 6, 'div', [
                    ], null, null, null, null, null)),
                    o['ɵdid'](11, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](12, {
                        show: 0
                    }),
                    (n() (), o['ɵeld'](13, 0, null, null, 1, 'button', [
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('leido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Como leído'
                    ])),
                    (n() (), o['ɵeld'](15, 0, null, null, 1, 'button', [
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('noLeido') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Como no leído'
                    ])),
                    (n() (), o['ɵeld'](17, 0, null, null, 3, 'button', [
                        ['class',
                            'action-btn']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.accionesMensajes('duplicado') && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](18, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Copiar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](19, 0, null, null, 1, 'span', [
                        ['class',
                            'label']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Duplicado'
                    ]))
                ], (function (n, e) {
                    var t = n(e, 12, 0, e.component.verOpciones);
                    n(e, 11, 0, t)
                }), (function (n, e) {
                    n(e, 17, 0, e.component.enableSolicitarDuplicado())
                }))
            }
            function En(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 8, 'div', [
                        ['class',
                            'action-bar']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'id',
                            'checkbox-all'
                        ],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], null, [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, null) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](2, 81920, [
                        [6,
                            4]
                    ], 0, K.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'button', [
                        ['id',
                            'select-option']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.mostrarSelectores = !l.mostrarSelectores) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted'](4, null, [
                        ' seleccionar ',
                        ' '
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Dn)),
                    o['ɵdid'](6, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Tn)),
                    o['ɵdid'](8, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0),
                        n(e, 6, 0, t.responsive.esTablet && null != t.mensajes && t.mensajes.length),
                        n(e, 8, 0, t.responsive.esMobile && null != t.mensajes && t.mensajes.length)
                }), (function (n, e) {
                    n(e, 4, 0, e.component.opcionSelectorTexto)
                }))
            }
            function Nn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['class',
                            'background']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        show: 0
                    })
                ], (function (n, e) {
                    var t = n(e, 2, 0, e.component.verOpciones);
                    n(e, 1, 0, 'background', t)
                }), null)
            }
            function An(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 4, 'li', [
                        ['class',
                            'list-item']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.seleccionarMensaje(t, n.context.$implicit.valor) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        selected: 0
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'span', [
                    ], [
                        [8,
                            'title',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵted'](4, null, [
                        '',
                        ''
                    ]))
                ], (function (n, e) {
                    var t = n(e, 2, 0, e.context.$implicit.valor == e.component.opcionSelector);
                    n(e, 1, 0, 'list-item', t)
                }), (function (n, e) {
                    n(e, 3, 0, o['ɵinlineInterpolate'](1, '', e.context.$implicit.texto, '')),
                        n(e, 4, 0, e.context.$implicit.texto)
                }))
            }
            function Vn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarEstados(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](1, 49152, [
                        [3,
                            4],
                        [
                            'estadosFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    })
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, t.placeholderEstado, t.estados, 'estados-dropdown')
                }), null)
            }
            function Bn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'datepicker-range', [
                    ], null, [
                        [null,
                            'fSeleccionadas'],
                        [
                            'window',
                            'resize'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 3).onResize(t) && l),
                        'fSeleccionadas' === e && (l = !1 !== i.seleccionarFechas(t) && l),
                            l
                    }), W.b, W.a)),
                    o['ɵprd'](512, null, C.c, C.c, [
                    ]),
                    o['ɵprd'](512, null, J.q, C.a, [
                        C.c
                    ]),
                    o['ɵdid'](3, 8503296, [
                        [1,
                            4],
                        [
                            'datePicker',
                            4
                        ]
                    ], 0, C.b, [
                        J.h,
                        J.q,
                        p.a
                    ], null, {
                        fSeleccionadas: 'fSeleccionadas'
                    })
                ], (function (n, e) {
                    n(e, 3, 0)
                }), null)
            }
            function Un(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarTiposDocuemento(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](1, 49152, [
                        [4,
                            4],
                        [
                            'tiposFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    })
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, t.placeholderTipoDocFiltro, t.tiposDocumento, 'tipos-dropdown')
                }), null)
            }
            function Ln(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'dropdown-importes', [
                    ], null, [
                        [null,
                            'importeSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'importeSeleccionado' === e && (o = !1 !== n.component.seleccionarImportes(t) && o),
                            o
                    }), X.b, X.a)),
                    o['ɵdid'](1, 114688, [
                        [2,
                            4],
                        [
                            'importesFilter',
                            4
                        ]
                    ], 0, Z.a, [
                        Y.a
                    ], {
                        config: [
                            0,
                            'config'
                        ]
                    }, {
                        importeSeleccionado: 'importeSeleccionado'
                    })
                ], (function (n, e) {
                    n(e, 1, 0, e.component.confFiltroImporte)
                }), null)
            }
            function $n(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarCuentas(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](1, 49152, [
                        [5,
                            4],
                        [
                            'ctasFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ],
                        disabled: [
                            3,
                            'disabled'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    })
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, t.placeholderCuenta, t.cuentasFiltro, 'cuentas-dropdown', t.disabledCuentas)
                }), null)
            }
            function Kn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 10, 'div', [
                        ['class',
                            'top']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Vn)),
                    o['ɵdid'](2, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Bn)),
                    o['ɵdid'](4, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Un)),
                    o['ɵdid'](6, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Ln)),
                    o['ɵdid'](8, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, $n)),
                    o['ɵdid'](10, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0, !t.responsive.esMobile),
                        n(e, 4, 0, !t.responsive.esMobile),
                        n(e, 6, 0, !t.responsive.esMobile),
                        n(e, 8, 0, !t.responsive.esMobile),
                        n(e, 10, 0, !t.responsive.esMobile)
                }), null)
            }
            function Gn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver más filtros'
                    ]))
                ], null, null)
            }
            function Hn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver menos filtros'
                    ]))
                ], null, null)
            }
            function qn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 23, 'div', [
                        ['class',
                            'filter-wrap']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarEstados(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](2, 49152, [
                        [3,
                            4],
                        [
                            'estadosFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 3, 'datepicker-range', [
                    ], null, [
                        [null,
                            'fSeleccionadas'],
                        [
                            'window',
                            'resize'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 6).onResize(t) && l),
                        'fSeleccionadas' === e && (l = !1 !== i.seleccionarFechas(t) && l),
                            l
                    }), W.b, W.a)),
                    o['ɵprd'](512, null, C.c, C.c, [
                    ]),
                    o['ɵprd'](512, null, J.q, C.a, [
                        C.c
                    ]),
                    o['ɵdid'](6, 8503296, [
                        [1,
                            4],
                        [
                            'datePicker',
                            4
                        ]
                    ], 0, C.b, [
                        J.h,
                        J.q,
                        p.a
                    ], null, {
                        fSeleccionadas: 'fSeleccionadas'
                    }),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarTiposDocuemento(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](8, 49152, [
                        [4,
                            4],
                        [
                            'tiposFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    }),
                    (n() (), o['ɵeld'](9, 0, null, null, 6, 'div', [
                        ['class',
                            'filter-dropdown']
                    ], null, null, null, null, null)),
                    o['ɵdid'](10, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](11, {
                        show: 0,
                        hidden: 1
                    }),
                    (n() (), o['ɵeld'](12, 0, null, null, 1, 'dropdown-importes', [
                    ], null, [
                        [null,
                            'importeSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'importeSeleccionado' === e && (o = !1 !== n.component.seleccionarImportes(t) && o),
                            o
                    }), X.b, X.a)),
                    o['ɵdid'](13, 114688, [
                        [2,
                            4],
                        [
                            'importesFilter',
                            4
                        ]
                    ], 0, Z.a, [
                        Y.a
                    ], {
                        config: [
                            0,
                            'config'
                        ]
                    }, {
                        importeSeleccionado: 'importeSeleccionado'
                    }),
                    (n() (), o['ɵeld'](14, 0, null, null, 1, 'dropdown-multiselect', [
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarCuentas(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](15, 49152, [
                        [5,
                            4],
                        [
                            'ctasFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ],
                        disabled: [
                            3,
                            'disabled'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    }),
                    (n() (), o['ɵeld'](16, 0, null, null, 7, 'div', [
                        ['class',
                            'view-more-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](17, 0, null, null, 6, 'button', [
                        ['class',
                            'btn-tertiary-black']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.verMasFiltros() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Gn)),
                    o['ɵdid'](19, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Hn)),
                    o['ɵdid'](21, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](22, 0, null, null, 1, 'div', [
                    ], null, null, null, null, null)),
                    o['ɵdid'](23, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0, t.placeholderEstado, t.estados, 'estados-dropdown'),
                        n(e, 6, 0),
                        n(e, 8, 0, t.placeholderTipoDocFiltro, t.tiposDocumento, 'tipos-dropdown');
                    var o = n(e, 11, 0, t.mostrarFiltrosMobile, !t.mostrarFiltrosMobile);
                    n(e, 10, 0, 'filter-dropdown', o),
                        n(e, 13, 0, t.confFiltroImporte),
                        n(e, 15, 0, t.placeholderCuenta, t.cuentasFiltro, 'cuentas-dropdown', t.disabledCuentas),
                        n(e, 19, 0, !t.mostrarFiltrosMobile),
                        n(e, 21, 0, t.mostrarFiltrosMobile),
                        n(e, 23, 0, t.mostrarFiltrosMobile ? 'ibercaja-icon-Chevron-arriba' : 'ibercaja-icon-Chevron-abajo')
                }), null)
            }
            function Wn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](2, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.borrarFiltroFechas() && o),
                            o
                    }), null, null))
                ], null, (function (n, e) {
                    n(e, 2, 0, e.component.fechasSeleccionadas)
                }))
            }
            function Jn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](2, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.borrarFiltroImportes() && o),
                            o
                    }), null, null))
                ], null, (function (n, e) {
                    n(e, 2, 0, e.component.importesSeleccionados)
                }))
            }
            function Xn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](2, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.desseleccionarCheck('estados-dropdown', n.context.$implicit) && o),
                            o
                    }), null, null))
                ], null, (function (n, e) {
                    n(e, 2, 0, e.component.estados[e.context.$implicit].texto)
                }))
            }
            function Zn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](2, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.desseleccionarCheck('tipos-dropdown', n.context.$implicit) && o),
                            o
                    }), null, null))
                ], null, (function (n, e) {
                    n(e, 2, 0, e.component.tiposDocumento[e.context.$implicit].texto)
                }))
            }
            function Yn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 8, 'div', [
                        ['class',
                            'seleccionados']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Wn)),
                    o['ɵdid'](2, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Jn)),
                    o['ɵdid'](4, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Xn)),
                    o['ɵdid'](6, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Zn)),
                    o['ɵdid'](8, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0, t.fechasSeleccionadas.length > 0),
                        n(e, 4, 0, t.importesSeleccionados.length > 0),
                        n(e, 6, 0, t.estadosSeleccionados),
                        n(e, 8, 0, t.tiposSeleccionadosAlias)
                }), null)
            }
            function Qn(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Pendientes de leer'
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (l.filtro.leido = null, l.showPendientesDeLeer = !1, o = !1 !== l.resetSecondFilter() && o),
                            o
                    }), null, null))
                ], null, null)
            }
            function ne(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'div', [
                        ['class',
                            'tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'texto']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Destacados'
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar icon']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (l.filtro.filtroDestacados = !1, l.filtro.leido = null, o = !1 !== l.resetSecondFilter() && o),
                            o
                    }), null, null))
                ], null, null)
            }
            function ee(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 5, 'div', [
                        ['class',
                            'filter-container second show']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 4, 'div', [
                        ['class',
                            'seleccionados']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Qn)),
                    o['ɵdid'](3, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ne)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0, t.showPendientesDeLeer),
                        n(e, 5, 0, t.filtro.filtroDestacados)
                }), null)
            }
            function te(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 11, 'div', [
                        ['class',
                            'table-header']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 4, 'div', [
                        ['class',
                            'left']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'descripción'
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'fecha'
                    ])),
                    (n() (), o['ɵeld'](6, 0, null, null, 5, 'div', [
                        ['class',
                            'right']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'importe'
                    ])),
                    (n() (), o['ɵeld'](9, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'cuenta'
                    ])),
                    (n() (), o['ɵeld'](11, 0, null, null, 0, 'span', [
                    ], null, null, null, null, null))
                ], null, null)
            }
            function oe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'span', [
                        ['class',
                            'account-number']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](1, null, [
                        '*',
                        ''
                    ])),
                    o['ɵpid'](0, H.SlicePipe, [
                    ])
                ], null, (function (n, e) {
                    var t = o['ɵunv'](e, 1, 0, o['ɵnov'](e, 2).transform(e.parent.context.$implicit.cuentaAsociada.trim(), e.parent.context.$implicit.cuentaAsociada.trim().length - 4, e.parent.context.$implicit.cuentaAsociada.trim().length));
                    n(e, 1, 0, t)
                }))
            }
            function le(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 0, 'span', [
                        ['class',
                            'account-number']
                    ], null, null, null, null, null))
                ], null, null)
            }
            function ie(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 27, 'li', [
                        ['class',
                            'mail-item']
                    ], [
                        [8,
                            'id',
                            0]
                    ], null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        selected: 0,
                        unread: 1
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 14, 'div', [
                        ['class',
                            'left']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 3, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, n.context.index, n.context.$implicit) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](5, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](6, {
                        selected: 0
                    }),
                    o['ɵdid'](7, 81920, [
                        [6,
                            4]
                    ], 0, K.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](8, 0, null, null, 2, 'div', [
                        ['class',
                            'icon destacado']
                    ], null, null, null, null, null)),
                    o['ɵdid'](9, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](10, {
                        'ibercaja-icon-Destacado-filled': 0
                    }),
                    (n() (), o['ɵeld'](11, 0, null, null, 0, 'div', [
                        ['class',
                            'mail-indicator']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](12, 0, null, null, 1, 'span', [
                        ['class',
                            'mail-title']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.GetDocumento(n.context.$implicit) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted'](13, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](14, 0, null, null, 3, 'div', [
                        ['class',
                            'date-tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](15, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](16, 2),
                    o['ɵpid'](0, H.SlicePipe, [
                    ]),
                    (n() (), o['ɵeld'](18, 0, null, null, 9, 'div', [
                        ['class',
                            'right']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](19, 0, null, null, 2, 'span', [
                        ['class',
                            'amount']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](20, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](21, 2),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, oe)),
                    o['ɵdid'](23, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, le)),
                    o['ɵdid'](25, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](26, 0, null, null, 1, 'span', [
                        ['class',
                            'type']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](27, null, [
                        '',
                        ''
                    ]))
                ], (function (n, e) {
                    var t = n(e, 2, 0, e.context.$implicit.seleccionado, !e.context.$implicit.leido);
                    n(e, 1, 0, 'mail-item', t);
                    var o = n(e, 6, 0, e.context.$implicit.seleccionado);
                    n(e, 5, 0, o),
                        n(e, 7, 0);
                    var l = n(e, 10, 0, e.context.$implicit.destacado);
                    n(e, 9, 0, 'icon destacado', l);
                    var i = e.context.$implicit.cuentaAsociada.trim();
                    n(e, 23, 0, i);
                    var a = !e.context.$implicit.cuentaAsociada.trim();
                    n(e, 25, 0, a)
                }), (function (n, e) {
                    // VB: corr columns
                    n(e, 0, 0, o['ɵinlineInterpolate'](1, 'mail-item-', e.context.index, '')),
                        n(e, 4, 0, o['ɵinlineInterpolate'](1, 'checkbox-', e.context.index, '')),
                        n(e, 13, 0, e.context.$implicit.descripcion);
                    var t = o['ɵunv'](e, 15, 0, o['ɵnov'](e, 17).transform(o['ɵunv'](e, 15, 0, n(e, 16, 0, o['ɵnov'](e.parent.parent.parent.parent, 0), e.context.$implicit.fecha, 'dd MMM')), 0, - 1));
                    n(e, 15, 0, t);
                    var l = 0 != e.context.$implicit.importe ? o['ɵunv'](e, 20, 0, n(e, 21, 0, o['ɵnov'](e.parent.parent.parent.parent, 1), e.context.$implicit.importe, 'EUR')) : '';
                    n(e, 20, 0, l),
                        // VB: Ahorro, Prestamo
                        n(e, 27, 0, e.context.$implicit.aliasCuentaAsociada)
                }))
            }
            function ae(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'ul', [
                        ['class',
                            'mail-list']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ie)),
                    o['ɵdid'](2, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.parent.context.$implicit.elementos)
                }), null)
            }
            function ce(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'span', [
                        ['class',
                            'account-number']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](1, null, [
                        '*',
                        ''
                    ])),
                    o['ɵpid'](0, H.SlicePipe, [
                    ])
                ], null, (function (n, e) {
                    var t = o['ɵunv'](e, 1, 0, o['ɵnov'](e, 2).transform(e.parent.context.$implicit.cuentaAsociada.trim(), e.parent.context.$implicit.cuentaAsociada.trim().length - 4, e.parent.context.$implicit.cuentaAsociada.trim().length));
                    n(e, 1, 0, t)
                }))
            }
            function re(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 25, 'li', [
                        ['class',
                            'mail-item']
                    ], [
                        [8,
                            'id',
                            0]
                    ], null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        selected: 0,
                        unread: 1
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 4, 'div', [
                        ['class',
                            'left']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 3, 'input', [
                        ['customCheckbox',
                            ''],
                        [
                            'type',
                            'checkbox'
                        ]
                    ], [
                        [8,
                            'id',
                            0]
                    ], [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t, n.context.index, n.context.$implicit) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](5, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](6, {
                        selected: 0
                    }),
                    o['ɵdid'](7, 81920, [
                        [6,
                            4]
                    ], 0, K.a, [
                        o.ElementRef,
                        o.Renderer2
                    ], null, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵeld'](8, 0, null, null, 17, 'div', [
                        ['class',
                            'right']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.GetDocumento(n.context.$implicit) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](9, 0, null, null, 0, 'div', [
                        ['class',
                            'mail-indicator']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](10, 0, null, null, 1, 'span', [
                        ['class',
                            'mail-title']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](11, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](12, 0, null, null, 2, 'div', [
                        ['class',
                            'icon destacado']
                    ], null, null, null, null, null)),
                    o['ɵdid'](13, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](14, {
                        'ibercaja-icon-Destacado-filled': 0
                    }),
                    (n() (), o['ɵeld'](15, 0, null, null, 3, 'div', [
                        ['class',
                            'date-tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](16, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](17, 2),
                    o['ɵpid'](0, H.SlicePipe, [
                    ]),
                    (n() (), o['ɵeld'](19, 0, null, null, 2, 'span', [
                        ['class',
                            'amount']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](20, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](21, 2),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ce)),
                    o['ɵdid'](23, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](24, 0, null, null, 1, 'span', [
                        ['class',
                            'type']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](25, null, [
                        '',
                        ''
                    ]))
                ], (function (n, e) {
                    var t = n(e, 2, 0, e.context.$implicit.seleccionado, !e.context.$implicit.leido);
                    n(e, 1, 0, 'mail-item', t);
                    var o = n(e, 6, 0, e.context.$implicit.seleccionado);
                    n(e, 5, 0, o),
                        n(e, 7, 0);
                    var l = n(e, 14, 0, e.context.$implicit.destacado);
                    n(e, 13, 0, 'icon destacado', l);
                    var i = e.context.$implicit.cuentaAsociada.trim();
                    n(e, 23, 0, i)
                }), (function (n, e) {
                    n(e, 0, 0, o['ɵinlineInterpolate'](1, 'mail-item-', e.context.index, '')),
                        n(e, 4, 0, o['ɵinlineInterpolate'](1, 'checkbox-', e.context.index, '')),
                        n(e, 11, 0, e.context.$implicit.descripcion);
                    var t = o['ɵunv'](e, 16, 0, o['ɵnov'](e, 18).transform(o['ɵunv'](e, 16, 0, n(e, 17, 0, o['ɵnov'](e.parent.parent.parent.parent, 0), e.context.$implicit.fecha, 'dd MMM')), 0, - 1));
                    n(e, 16, 0, t);
                    var l = o['ɵunv'](e, 20, 0, n(e, 21, 0, o['ɵnov'](e.parent.parent.parent.parent, 1), e.context.$implicit.importe, 'EUR'));
                    n(e, 20, 0, l),
                        n(e, 25, 0, e.context.$implicit.aliasCuentaAsociada)
                }))
            }
            function se(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'ul', [
                        ['class',
                            'mail-list']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, re)),
                    o['ɵdid'](2, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.parent.context.$implicit.elementos)
                }), null)
            }
            function ue(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 10, 'div', [
                        ['class',
                            'section table-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['class',
                            'section-title']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](2, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 2, 'div', [
                        ['class',
                            'table-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, te)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](6, 0, null, null, 4, 'div', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ae)),
                    o['ɵdid'](8, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, se)),
                    o['ɵdid'](10, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 5, 0, !t.responsive.esTablet && !t.responsive.esMobile),
                        n(e, 8, 0, !t.responsive.esTablet && !t.responsive.esMobile && null != e.context.$implicit.elementos && e.context.$implicit.elementos.length),
                        n(e, 10, 0, t.responsive.esTablet || t.responsive.esMobile && null != e.context.$implicit.elementos && e.context.$implicit.elementos.length)
                }), (function (n, e) {
                    n(e, 2, 0, e.context.$implicit.titulo)
                }))
            }
            function de(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 15, 'div', [
                        ['class',
                            'result-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ue)),
                    o['ɵdid'](2, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](3, 0, null, null, 12, 'div', [
                        ['class',
                            'view-more-container'],
                        [
                            'ng-cloak',
                            ''
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 5, 'button', [
                        ['class',
                            'btn-tertiary-black']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.verMenosCorrespondencia(t) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](5, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](6, {
                        hideViewMoreLess: 0
                    }),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver menos'
                    ])),
                    (n() (), o['ɵeld'](9, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Chevron-arriba']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](10, 0, null, null, 5, 'button', [
                        ['class',
                            'btn-tertiary-black']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.verMasCorrespondencia(t) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](11, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](12, {
                        hideViewMoreLess: 0
                    }),
                    (n() (), o['ɵeld'](13, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver más'
                    ])),
                    (n() (), o['ɵeld'](15, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Chevron-abajo']
                    ], null, null, null, null, null))
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0, t.movimientosCorrespondencia);
                    var o = n(e, 6, 0, !t.mostrarMenos);
                    n(e, 5, 0, 'btn-tertiary-black', o);
                    var l = n(e, 12, 0, !t.mostrarMas);
                    n(e, 11, 0, 'btn-tertiary-black', l)
                }), null)
            }
            function pe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'loading', [
                        ['class',
                            'seccion']
                    ], null, null, null, Q.b, Q.a)),
                    o['ɵdid'](1, 114688, null, 0, nn.a, [
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function ge(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'notification', [
                    ], null, null, null, en.c, en.b)),
                    o['ɵdid'](1, 114688, null, 0, tn.a, [
                        d.a,
                        a.a,
                        on.a,
                        ln.a
                    ], {
                        notification: [
                            0,
                            'notification'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 1, 0, e.component.infoNotification)
                }), null)
            }
            function fe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'error-load-section', [
                    ], null, [
                        [null,
                            'reload']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'reload' === e && (o = !1 !== n.component.reload(t) && o),
                            o
                    }), an.b, an.a)),
                    o['ɵdid'](1, 114688, null, 0, cn.a, [
                    ], null, {
                        reload: 'reload'
                    })
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function Ce(n) {
                return o['ɵvid'](0, [
                    o['ɵpid'](0, H.DatePipe, [
                        o.LOCALE_ID
                    ]),
                    o['ɵpid'](0, H.CurrencyPipe, [
                        o.LOCALE_ID
                    ]),
                    o['ɵqud'](671088640, 1, {
                        datePicker: 0
                    }),
                    o['ɵqud'](671088640, 2, {
                        importesFilter: 0
                    }),
                    o['ɵqud'](671088640, 3, {
                        estadosFilter: 0
                    }),
                    o['ɵqud'](671088640, 4, {
                        tiposFilter: 0
                    }),
                    o['ɵqud'](671088640, 5, {
                        ctasFilter: 0
                    }),
                    o['ɵqud'](671088640, 6, {
                        customCheckboxDir: 1
                    }),
                    (n() (), o['ɵeld'](8, 0, null, null, 55, 'dashboard-layout', [
                    ], null, [
                        ['window',
                            'resize'],
                        [
                            'window',
                            'scroll'
                        ]
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 10).onResize(t) && l),
                        'window:scroll' === e && (l = !1 !== o['ɵnov'](n, 10).onWindowScroll() && l),
                            l
                    }), rn.b, rn.a)),
                    o['ɵprd'](512, null, O.a, O.a, [
                    ]),
                    o['ɵdid'](10, 8634368, null, 0, sn.a, [
                        o.ChangeDetectorRef,
                        un.a,
                        O.a,
                        p.a,
                        dn.a,
                        pn.f,
                        a.a,
                        gn.a
                    ], null, null),
                    (n() (), o['ɵeld'](11, 0, null, 0, 8, 'div', [
                        ['top',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, zn)),
                    o['ɵdid'](13, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](14, 0, null, null, 1, 'navigation-back', [
                    ], null, [
                        ['window',
                            'resize']
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 15).onResize(t) && l),
                            l
                    }), fn.b, fn.a)),
                    o['ɵdid'](15, 376832, null, 0, Cn.a, [
                        mn.c,
                        p.a,
                        d.a
                    ], {
                        config: [
                            0,
                            'config'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](16, 0, null, null, 1, 'resumen-producto', [
                    ], null, [
                        [null,
                            'recargar'],
                        [
                            null,
                            'elementoSeleccionado'
                        ]
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'recargar' === e && (o = !1 !== l.cargarSumatorios() && o),
                        'elementoSeleccionado' === e && (o = !1 !== l.seleccionarSumatorio(t) && o),
                            o
                    }), Pn.b, Pn.a)),
                    o['ɵdid'](17, 8503296, null, 0, Mn.a, [
                        p.a
                    ], {
                        items: [
                            0,
                            'items'
                        ]
                    }, {
                        elementoSeleccionado: 'elementoSeleccionado',
                        recargar: 'recargar'
                    }),
                    (n() (), o['ɵeld'](18, 0, null, null, 1, 'app-navigation-panel', [
                    ], null, [
                        [null,
                            'navegar'],
                        [
                            'window',
                            'resize'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 19).onResize(t) && l),
                        'navegar' === e && (l = !1 !== i.goToPanelNavegacion(t) && l),
                            l
                    }), hn.b, hn.a)),
                    o['ɵdid'](19, 8437760, null, 0, On.a, [
                        a.a,
                        d.a,
                        p.a
                    ], {
                        configuracionPanel: [
                            0,
                            'configuracionPanel'
                        ]
                    }, {
                        navegar: 'navegar'
                    }),
                    (n() (), o['ɵeld'](20, 0, null, 1, 40, 'div', [
                        ['main',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](21, 0, null, null, 39, 'div', [
                        ['class',
                            'correspondencia-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Rn)),
                    o['ɵdid'](23, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, jn)),
                    o['ɵdid'](25, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Fn)),
                    o['ɵdid'](27, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, En)),
                    o['ɵdid'](29, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Nn)),
                    o['ɵdid'](31, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](32, 0, null, null, 5, 'ul', [
                        ['class',
                            'select-list']
                    ], null, [
                        [null,
                            'clickOutside'],
                        [
                            'document',
                            'click'
                        ],
                        [
                            'document',
                            'touch'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'document:click' === e && (l = !1 !== o['ɵnov'](n, 35).onClick(t.target) && l),
                        'document:touch' === e && (l = !1 !== o['ɵnov'](n, 35).onClick(t.target) && l),
                        'clickOutside' === e && (l = !1 !== i.closeDropdown(t, 'select-option') && l),
                            l
                    }), null, null)),
                    o['ɵdid'](33, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](34, {
                        hidden: 0
                    }),
                    o['ɵdid'](35, 16384, null, 0, G.a, [
                        o.ElementRef
                    ], null, {
                        clickOutside: 'clickOutside'
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, An)),
                    o['ɵdid'](37, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](38, 0, null, null, 10, 'div', [
                        ['class',
                            'filter-container']
                    ], null, null, null, null, null)),
                    o['ɵdid'](39, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](40, {
                        show: 0
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Kn)),
                    o['ɵdid'](42, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, qn)),
                    o['ɵdid'](44, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](45, 0, null, null, 3, 'div', [
                        ['class',
                            'button-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](46, 0, null, null, 2, 'button', [
                        ['class',
                            'btn-primary-blue btn-text-m']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.resetSecondFilter() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](47, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'aplicar filtros'
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Yn)),
                    o['ɵdid'](50, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ee)),
                    o['ɵdid'](52, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, de)),
                    o['ɵdid'](54, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, pe)),
                    o['ɵdid'](56, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ge)),
                    o['ɵdid'](58, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, fe)),
                    o['ɵdid'](60, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](61, 0, null, 2, 2, 'div', [
                        ['sidebar',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](62, 0, null, null, 1, 'app-dashboard-side-bar', [
                    ], null, null, null, bn.b, bn.a)),
                    o['ɵdid'](63, 245760, null, 0, _n.a, [
                        H.DatePipe,
                        vn.a,
                        xn.a,
                        O.a,
                        d.a,
                        a.a,
                        wn.a,
                        Sn.a,
                        yn.a,
                        In.a,
                        dn.a
                    ], null, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 10, 0),
                        n(e, 13, 0, t.utilsComponent.storage.isDemo),
                        n(e, 15, 0, t.configuracionBack),
                        n(e, 17, 0, t.itemsSumatorios),
                        n(e, 19, 0, t.navigationPanel),
                        n(e, 23, 0, !t.responsive.esTablet && !t.responsive.esMobile),
                        n(e, 25, 0, t.responsive.esTablet || t.responsive.esMobile),
                        n(e, 27, 0, !t.responsive.esTablet && !t.responsive.esMobile),
                        n(e, 29, 0, t.responsive.esTablet || t.responsive.esMobile),
                        n(e, 31, 0, t.responsive.esMobile);
                    var o = n(e, 34, 0, !t.mostrarSelectores);
                    n(e, 33, 0, 'select-list', o),
                        n(e, 37, 0, t.selectores);
                    var l = n(e, 40, 0, t.mostrarFiltros);
                    n(e, 39, 0, 'filter-container', l),
                        n(e, 42, 0, !t.responsive.esMobile),
                        n(e, 44, 0, t.responsive.esMobile),
                        n(e, 50, 0, !t.responsive.esMobile),
                        n(e, 52, 0, !t.responsive.esMobile && (t.showPendientesDeLeer || t.filtro.filtroDestacados)),
                        n(e, 54, 0, null != t.movimientosCorrespondencia && t.movimientosCorrespondencia.length),
                        n(e, 56, 0, t.statusMensajes),
                        n(e, 58, 0, !t.statusMensajes && t.sinCorrespondencia),
                        n(e, 60, 0, !t.statusMensajes && t.errorLoad),
                        n(e, 63, 0)
                }), null)
            }
            function me(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'listado-correspondencia', [
                    ], null, [
                        ['window',
                            'scroll']
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:scroll' === e && (l = !1 !== o['ɵnov'](n, 1).onWindowScroll() && l),
                            l
                    }), Ce, kn)),
                    o['ɵdid'](1, 245760, null, 0, F, [
                        y.a,
                        a.a,
                        O.a,
                        M,
                        H.DatePipe,
                        h.a,
                        r.a,
                        b.a,
                        v.a,
                        d.a,
                        p.a,
                        x.a,
                        R.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            var Pe = o['ɵccf']('listado-correspondencia', F, me, {
                }, {
                }, [
                ]),
                Me = t('grRn'),
                he = function () {
                    function n(n) {
                        this._ps = n,
                            this.propiedades = {
                            }
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this._ps.seleccionadoActual.subscribe((function (e) {
                            n.navegacionOperacion = e
                        }))
                    },
                        n.prototype.seleccionarFormaEnvio = function (n) {
                            this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].subsecciones[this.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato = n.item,
                            'solicitud de duplicados' == this.navegacionOperacion.tituloOperativa && 'forma de envío' == this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].tituloSeccion && (1 == n.item.id ? this._ps.modificarOrdenPasos(this.navegacionOperacion, 2, 1, 3, !1) : 2 == n.item.id && this._ps.modificarOrdenPasos(this.navegacionOperacion, 2, 1, 2, !0)),
                                this._ps.enviarElementoSeleccionado(this.navegacionOperacion)
                        },
                        n.prototype.siguiente = function () {
                            this.noSeleccionado() || (this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].subsecciones[this.navegacionOperacion.indiceSubseccion].datosSeleccionados.texto = this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].subsecciones[this.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato.texto, this._ps.enviarElementoSeleccionado(this.navegacionOperacion), this._ps.continuar())
                        },
                        n.prototype.calcularSeleccionado = function () {
                            var n = this;
                            if (null != this.navegacionOperacion.pasos && null != this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].subsecciones[this.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato) {
                                var e = this.propiedades.opciones.findIndex((function (e) {
                                    return e.id == n.navegacionOperacion.pasos[n.navegacionOperacion.indiceSeccion].subsecciones[n.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato.id
                                }));
                                return this.propiedades.opciones[e]
                            }
                        },
                        n.prototype.noSeleccionado = function () {
                            return null == this.navegacionOperacion.pasos[this.navegacionOperacion.indiceSeccion].subsecciones[this.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato
                        },
                        n
                }(),
                Oe = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.titulo-seccion[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;font-size:1.875rem;color:#33393e}.titulo-seccion[_ngcontent-%COMP%]   .numero[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif;color:#0b7ad0;font-size:1.75rem;margin-right:17px}.back[_ngcontent-%COMP%]{padding-top:25px;display:flex;align-items:center}.back[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{cursor:pointer;font-size:.625rem;color:#fff;background-color:#0b7ad0;border-radius:2px;padding:7px 6px}.back[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;font-size:1.25rem;margin-left:12px}.texto-seccion[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;color:#0b7ad0;font-size:2.25rem}.botones[_ngcontent-%COMP%]:not(.fixed-bottom)   button[_ngcontent-%COMP%]{text-align:center;margin:0 auto;padding:16px 31px;border-radius:2px;font-size:.875rem;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.botones[_ngcontent-%COMP%]:not(.fixed-bottom)   button.continuar[_ngcontent-%COMP%]{display:block}.botones[_ngcontent-%COMP%]:not(.fixed-bottom)   button.opcion[_ngcontent-%COMP%]{display:inline-block}.botones[_ngcontent-%COMP%]:not(.fixed-bottom)   button.opcion[_ngcontent-%COMP%]:nth-of-type(2){margin-left:12px}.botones[_ngcontent-%COMP%]:not(.fixed-bottom)   button.sin-margin[_ngcontent-%COMP%]{margin:0!important}.click-device[_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover, .click-device   [_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover{background-color:rgba(38,38,42,.08);color:rgba(0,0,0,.19);cursor:initial}.mobile[_nghost-%COMP%]   .operacion-configuracion-producto-container[_ngcontent-%COMP%]   .operacion-flujo-container.resumen[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-configuracion-producto-container[_ngcontent-%COMP%]   .operacion-flujo-container.resumen[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-destinatario-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-destinatario-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-dropdown-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-dropdown-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-financiar-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-financiar-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-importe-concepto-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-importe-concepto-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-periodicidad-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-periodicidad-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-seleccion-motivos-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-seleccion-motivos-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-seleccion-opciones-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-seleccion-opciones-container[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-seleccion-productos-container[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-seleccion-productos-container[_ngcontent-%COMP%]{padding-bottom:109px!important}.mobile[_nghost-%COMP%]   .operacion-flujo-container.resumen.txt-info[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-flujo-container.resumen.txt-info[_ngcontent-%COMP%]{padding-bottom:0!important}.mobile[_nghost-%COMP%]   .operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]{padding-bottom:109px!important}@media screen and (max-width:1023px){.back[_ngcontent-%COMP%]{padding:17px}.back[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{padding:9px 7px;font-size:.8125rem}.texto-seccion[_ngcontent-%COMP%]{color:#33393e;font-size:1.125rem;font-family:Ibercaja-Regular,sans-serif;padding-bottom:19px;display:block;line-height:28px}.botones.flotante[_ngcontent-%COMP%]{position:fixed;bottom:15px;display:inline-block;width:calc(100% - 34px)}.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   .continuar[_ngcontent-%COMP%]{margin:0 auto;text-align:center;box-shadow:1px 2px 11px 0 rgba(0,0,0,.22);background-color:#0b7ad0;color:#f5f8fa;padding:16px 41px;border:none;z-index:1}.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   .continuar[_ngcontent-%COMP%]:disabled{background-color:#eee;color:rgba(0,0,0,.19)}.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   .opcion[_ngcontent-%COMP%]{display:block;margin:16px auto 0;text-align:center;position:relative;bottom:initial;left:initial;box-shadow:none;padding:16px 41px}.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   .opcion[_ngcontent-%COMP%]:nth-of-type(2){margin-left:auto}}@media screen and (max-width:767px){.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]{display:block;width:100%}.botones[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:nth-of-type(2){margin-left:0;margin-top:8px}}.operacion-dropdown-container[_ngcontent-%COMP%]{margin-top:71px;max-width:705px}.operacion-dropdown-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{margin-bottom:51px}.operacion-dropdown-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]   p[_ngcontent-%COMP%]{color:#0b7ad0;font-family:Ibercaja-Light,sans-serif;line-height:46px;font-size:2.25rem}.operacion-dropdown-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]   p[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.operacion-dropdown-container[_ngcontent-%COMP%]   .label-dropdown[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif;display:block;font-style:normal;font-size:.875rem;margin-bottom:9px}.operacion-dropdown-container[_ngcontent-%COMP%]   .label-dropdown[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.operacion-dropdown-container[_ngcontent-%COMP%]   dropdown-select[_ngcontent-%COMP%]{display:block;max-width:400px}.operacion-dropdown-container[_ngcontent-%COMP%]   .info[_ngcontent-%COMP%]{margin-top:36px;max-width:450px}.operacion-dropdown-container[_ngcontent-%COMP%]   .info[_ngcontent-%COMP%] > p[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.9375rem;line-height:1.25rem;color:rgba(51,57,62,.7)}.operacion-dropdown-container[_ngcontent-%COMP%]   .info[_ngcontent-%COMP%] > p[_ngcontent-%COMP%] > strong[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.operacion-dropdown-container[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%]{margin-top:20px}.operacion-dropdown-container[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%] > div[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{color:#33393e;display:inline-block;vertical-align:middle}.operacion-dropdown-container[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%] > div[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:first-of-type{font-size:.8125rem;font-family:Ibercaja-Regular,sans-serif;margin-right:8px}.operacion-dropdown-container[_ngcontent-%COMP%]   .amount[_ngcontent-%COMP%] > div[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-of-type(2){font-size:1.25rem;font-family:Ibercaja-Medium,sans-serif}.operacion-dropdown-container[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]{margin-top:80px}@media screen and (max-width:1023px){.operacion-dropdown-container[_ngcontent-%COMP%]{margin-top:0;padding:17px;max-width:none}.operacion-dropdown-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{margin-bottom:28px}.operacion-dropdown-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]   p[_ngcontent-%COMP%]{color:#33393e;font-family:Ibercaja-Regular,sans-serif;line-height:28px;font-size:1.125rem}}']
                    ],
                    data: {
                        animation: [
                            {
                                type: 7,
                                name: 'fadeIn',
                                definitions: [
                                    {
                                        type: 1,
                                        expr: ':enter',
                                        animation: [
                                            {
                                                type: 6,
                                                styles: {
                                                    opacity: 0
                                                },
                                                offset: null
                                            },
                                            {
                                                type: 4,
                                                styles: {
                                                    type: 6,
                                                    styles: {
                                                        opacity: 1
                                                    },
                                                    offset: null
                                                },
                                                timings: '0.3s ease-out'
                                            }
                                        ],
                                        options: null
                                    }
                                ],
                                options: {
                                }
                            }
                        ]
                    }
                });
            function be(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 5, 'div', [
                        ['class',
                            'info']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 4, 'p', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Si desea incluir o modificar su dirección de email, por favor diríjase al apartado de '
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'strong', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Datos Personales'
                    ])),
                    (n() (), o['ɵted']( - 1, null, [
                        '.'
                    ]))
                ], null, null)
            }
            function _e(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 4, 'div', [
                        ['class',
                            'info']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'p', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'strong', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Recuerde: '
                    ])),
                    (n() (), o['ɵted']( - 1, null, [
                        'El envío de correo postal repercute el coste de la tarifa oficial.'
                    ]))
                ], null, null)
            }
            function ve(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 6, 'div', [
                        ['class',
                            'amount']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 5, 'div', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Disponible'
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 2, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](5, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](6, 4)
                ], null, (function (n, e) {
                    var t = e.component,
                        l = o['ɵunv'](e, 5, 0, n(e, 6, 0, o['ɵnov'](e.parent, 0), t.navegacionOperacion.pasos[t.navegacionOperacion.indiceSeccion].subsecciones[t.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato.disponible, t.navegacionOperacion.pasos[t.navegacionOperacion.indiceSeccion].subsecciones[t.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato.moneda, 'symbol-narrow', '1.0'));
                    n(e, 5, 0, l)
                }))
            }
            function xe(n) {
                return o['ɵvid'](0, [
                    o['ɵpid'](0, H.CurrencyPipe, [
                        o.LOCALE_ID
                    ]),
                    (n() (), o['ɵeld'](1, 0, null, null, 17, 'div', [
                        ['class',
                            'operacion-dropdown-container']
                    ], [
                        [24,
                            '@fadeIn',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 2, 'div', [
                        ['class',
                            'titulo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'p', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](4, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'p', [
                        ['class',
                            'label-dropdown']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](6, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'dropdown-select', [
                    ], null, [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionarFormaEnvio(t) && o),
                            o
                    }), Me.b, Me.a)),
                    o['ɵdid'](8, 49152, null, 0, D.a, [
                    ], {
                        model: [
                            0,
                            'model'
                        ],
                        id: [
                            1,
                            'id'
                        ],
                        itemSeleccionado: [
                            2,
                            'itemSeleccionado'
                        ],
                        placeholder: [
                            3,
                            'placeholder'
                        ]
                    }, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, be)),
                    o['ɵdid'](10, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, _e)),
                    o['ɵdid'](12, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ve)),
                    o['ɵdid'](14, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](15, 0, null, null, 3, 'div', [
                        ['class',
                            'botones flotante']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](16, 0, null, null, 2, 'button', [
                        ['class',
                            'button continuar btn-primary-blue']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.siguiente() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](17, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Continuar'
                    ]))
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 8, 0, t.propiedades.opciones, 'operativas-dropdown', t.calcularSeleccionado(), t.propiedades.placeholder),
                        n(e, 10, 0, 'email' == t.propiedades.info),
                        n(e, 12, 0, 'tipoEnvio' == t.propiedades.info && null != t.navegacionOperacion.pasos[t.navegacionOperacion.indiceSeccion].subsecciones[t.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato && 2 == t.navegacionOperacion.pasos[t.navegacionOperacion.indiceSeccion].subsecciones[t.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato.id),
                        n(e, 14, 0, 'lineaCredito' == t.propiedades.info && null != t.navegacionOperacion.pasos[t.navegacionOperacion.indiceSeccion].subsecciones[t.navegacionOperacion.indiceSubseccion].datosSeleccionados.dato)
                }), (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, void 0),
                        n(e, 4, 0, t.propiedades.titulo),
                        n(e, 6, 0, t.propiedades.label),
                        n(e, 16, 0, t.noSeleccionado())
                }))
            }
            var we = function () {
                    function n(n, e, t, o, l) {
                        this.resumenDuplicadosService = n,
                            this.utilsComponent = e,
                            this._ps = t,
                            this.responsive = o,
                            this.errorHandler = l,
                            this.statusMensajes = !1,
                            this.deshabilitarBtn = !1
                    }
                    return n.prototype.ngOnInit = function () {
                        var n = this;
                        this._ps.seleccionadoActual.subscribe((function (e) {
                            n.navegacionOperacion = e
                        }))
                    },
                        n.prototype.solicitar = function () {
                            var n = this;
                            this.statusMensajes = !0,
                                this.deshabilitarBtn = !0;
                            var e = 1 == this.navegacionOperacion.pasos[0].subsecciones[0].datosSeleccionados.dato.id,
                                t = new I;
                            t.canal = s.a.Correspondencia.Contadores.Canal,
                                t.ofiAlta = s.a.Correspondencia.Contadores.OfiAlta,
                                t.codRefCifrado = [
                                ],
                                t.isCorreoElectronico = e,
                            e && (t.correoElectronico = this.navegacionOperacion.pasos[1].subsecciones[0].datosSeleccionados.dato.texto),
                                this.datosConfirmacion.elementos.forEach((function (n) {
                                    t.codRefCifrado.push(n.codRefCifrado)
                                })),
                                this.resumenDuplicadosService.postSolicitudDuplicado(t).subscribe((function (e) {
                                    n.statusMensajes = !1,
                                        n.deshabilitarBtn = !1,
                                        n._ps.continuar()
                                }), (function (e) {
                                    n.statusMensajes = !1,
                                        n.deshabilitarBtn = !1,
                                        n.errorHandler.showModal(s.a.TiposModal.Error, s.a.ErrorMessages.ErrorGenerico, null, !0, s.a.Botones.Aceptar)
                                }))
                        },
                        n
                }(),
                Se = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.duplicados-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{margin-bottom:51px;margin-top:104px}.duplicados-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%] > p[_ngcontent-%COMP%]{color:#0b7ad0;font-family:Ibercaja-Light,sans-serif;line-height:46px;font-size:2.25rem}.duplicados-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%] > p[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]{padding-left:28px;padding-right:16px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:first-child{flex-basis:100px;min-width:80px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(2){flex-basis:calc((50% - 100px)/ 2);min-width:200px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-child(3){flex-basis:50%;min-width:250px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .wrap-move[_ngcontent-%COMP%]{height:64px;background-color:#fff;display:flex;align-items:center;border-bottom:1px solid rgba(51,57,62,.1);position:relative}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .wrap-move[_ngcontent-%COMP%]   .row[_ngcontent-%COMP%]{width:100%;display:flex;padding-left:28px;align-items:center;min-width:165px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .wrap-move[_ngcontent-%COMP%]   .row[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:first-of-type{flex-basis:100px;min-width:80px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .wrap-move[_ngcontent-%COMP%]   .row[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:nth-of-type(2){flex-basis:calc((50% - 100px)/ 2);min-width:200px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .wrap-move[_ngcontent-%COMP%]   .row[_ngcontent-%COMP%] > div[_ngcontent-%COMP%]:nth-of-type(3){flex-basis:50%;min-width:250px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .move-item[_ngcontent-%COMP%]   .date-container[_ngcontent-%COMP%]{position:relative;margin-right:0;min-width:80px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .move-item[_ngcontent-%COMP%]   .date-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{display:block;width:58px}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .move-item[_ngcontent-%COMP%]   .contrato-container[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.875rem;padding:20px 0;min-width:200px;overflow:hidden;text-overflow:ellipsis;color:rgba(51,57,62,.7)}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .move-item[_ngcontent-%COMP%]   .description-container[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;text-transform:uppercase;font-size:.875rem;color:#33393e;padding:20px 0;min-width:250px;overflow:hidden;text-overflow:ellipsis}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   ul[_ngcontent-%COMP%]   .move-item[_ngcontent-%COMP%]   .description-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{white-space:pre-line}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]{padding:32px;text-align:center;background-color:#fff}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{display:inline-block;font-size:.75rem;vertical-align:middle;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.duplicados-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .view-more-container[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;font-size:.6875rem;margin-left:24px}.duplicados-container[_ngcontent-%COMP%]   .seccion[_ngcontent-%COMP%]{display:block;text-align:center}.botones[_ngcontent-%COMP%]{margin-top:40px;text-align:center}.botones[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]{text-align:center;margin:0 auto;padding:16px 31px;border-radius:2px;font-size:.875rem;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}@media screen and (max-width:1023px){.duplicados-container[_ngcontent-%COMP%]{padding-bottom:109px!important}.duplicados-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{margin-bottom:28px;margin-top:0}.duplicados-container[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%] > p[_ngcontent-%COMP%]{color:#33393e;font-family:Ibercaja-Regular,sans-serif;line-height:28px;font-size:1.125rem}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]{background-color:#fff;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);padding:28px 0 30px 22px;margin-bottom:30px}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]{display:flex;flex-direction:column}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .date-container[_ngcontent-%COMP%]{margin-bottom:8px}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .date-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{display:block;width:58px}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .description-container[_ngcontent-%COMP%]{margin-bottom:10px;color:#33393e;font-size:.875rem;line-height:20px;font-family:Ibercaja-Regular,sans-serif}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .description-container[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{white-space:pre-line}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .contrato-container[_ngcontent-%COMP%]{margin-bottom:18px;color:#33393e;line-height:16px;font-size:.9375rem;font-family:Ibercaja-Medium,sans-serif}.duplicados-container[_ngcontent-%COMP%]   .list-container[_ngcontent-%COMP%]   .card-container[_ngcontent-%COMP%]   .card-content[_ngcontent-%COMP%]   .pages-container[_ngcontent-%COMP%]{color:#33393e;font-family:Ibercaja-Regular,sans-serif;font-size:.75rem}.duplicados-container[_ngcontent-%COMP%]   .botones.flotante[_ngcontent-%COMP%]{position:sticky;position:-webkit-sticky;bottom:109px!important}}.click-device[_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover, .click-device   [_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover{background-color:rgba(38,38,42,.08);color:rgba(0,0,0,.19);cursor:initial}']
                    ],
                    data: {
                    }
                });
            function ye(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'li', [
                        ['class',
                            'wrap-move']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 11, 'div', [
                        ['class',
                            'move-item row']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 4, 'div', [
                        ['class',
                            'date-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 3, 'span', [
                        ['class',
                            'date-tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](4, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](5, 2),
                    o['ɵpid'](0, H.SlicePipe, [
                    ]),
                    (n() (), o['ɵeld'](7, 0, null, null, 2, 'div', [
                        ['class',
                            'contrato-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'span', [
                    ], [
                        [8,
                            'title',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵted'](9, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](10, 0, null, null, 2, 'div', [
                        ['class',
                            'description-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'span', [
                    ], [
                        [8,
                            'title',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵted'](12, null, [
                        '',
                        ''
                    ]))
                ], null, (function (n, e) {
                    var t = o['ɵunv'](e, 4, 0, o['ɵnov'](e, 6).transform(o['ɵunv'](e, 4, 0, n(e, 5, 0, o['ɵnov'](e.parent.parent, 0), e.context.$implicit.fecha, 'dd MMM')), 0, - 1));
                    n(e, 4, 0, t),
                        n(e, 8, 0, o['ɵinlineInterpolate'](1, '', e.context.$implicit.contrato, '')),
                        n(e, 9, 0, e.context.$implicit.contrato),
                        n(e, 11, 0, o['ɵinlineInterpolate'](1, '', e.context.$implicit.descripcion, '')),
                        n(e, 12, 0, e.context.$implicit.descripcion)
                }))
            }
            function Ie(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 10, 'div', [
                        ['class',
                            'table-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 6, 'div', [
                        ['class',
                            'table-header']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'fecha'
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'contrato'
                    ])),
                    (n() (), o['ɵeld'](6, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'documento'
                    ])),
                    (n() (), o['ɵeld'](8, 0, null, null, 2, 'ul', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ye)),
                    o['ɵdid'](10, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 10, 0, e.component.datosConfirmacion.elementos)
                }), null)
            }
            function ke(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'div', [
                        ['class',
                            'card-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 11, 'div', [
                        ['class',
                            'card-content']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 4, 'div', [
                        ['class',
                            'date-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 3, 'span', [
                        ['class',
                            'date-tag']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](4, null, [
                        '',
                        ''
                    ])),
                    o['ɵppd'](5, 2),
                    o['ɵpid'](0, H.SlicePipe, [
                    ]),
                    (n() (), o['ɵeld'](7, 0, null, null, 2, 'div', [
                        ['class',
                            'description-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'span', [
                    ], [
                        [8,
                            'title',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵted'](9, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](10, 0, null, null, 2, 'div', [
                        ['class',
                            'contrato-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'span', [
                    ], [
                        [8,
                            'title',
                            0]
                    ], null, null, null, null)),
                    (n() (), o['ɵted'](12, null, [
                        '',
                        ''
                    ]))
                ], null, (function (n, e) {
                    var t = o['ɵunv'](e, 4, 0, o['ɵnov'](e, 6).transform(o['ɵunv'](e, 4, 0, n(e, 5, 0, o['ɵnov'](e.parent.parent, 0), e.context.$implicit.fecha, 'dd MMM')), 0, - 1));
                    n(e, 4, 0, t),
                        n(e, 8, 0, o['ɵinlineInterpolate'](1, '', e.context.$implicit.descripcion, '')),
                        n(e, 9, 0, e.context.$implicit.descripcion),
                        n(e, 11, 0, o['ɵinlineInterpolate'](1, '', e.context.$implicit.contrato, '')),
                        n(e, 12, 0, e.context.$implicit.contrato)
                }))
            }
            function ze(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['class',
                            'list-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ke)),
                    o['ɵdid'](2, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.datosConfirmacion.elementos)
                }), null)
            }
            function Re(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'loading', [
                        ['class',
                            'seccion']
                    ], null, null, null, Q.b, Q.a)),
                    o['ɵdid'](1, 114688, null, 0, nn.a, [
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function je(n) {
                return o['ɵvid'](0, [
                    o['ɵpid'](0, H.DatePipe, [
                        o.LOCALE_ID
                    ]),
                    (n() (), o['ɵeld'](1, 0, null, null, 15, 'div', [
                        ['class',
                            'duplicados-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 2, 'div', [
                        ['class',
                            'titulo']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'p', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](4, null, [
                        '',
                        ' '
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Ie)),
                    o['ɵdid'](6, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ze)),
                    o['ɵdid'](8, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](9, 0, null, null, 5, 'div', [
                        ['class',
                            'botones']
                    ], null, null, null, null, null)),
                    o['ɵdid'](10, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](11, {
                        flotante: 0
                    }),
                    (n() (), o['ɵeld'](12, 0, null, null, 2, 'button', [
                        ['class',
                            'button btn-primary-blue']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.solicitar() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](13, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'solicitar'
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Re)),
                    o['ɵdid'](16, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 6, 0, !t.responsive.esMobile && !t.responsive.esTablet),
                        n(e, 8, 0, t.responsive.esTablet);
                    var o = n(e, 11, 0, t.responsive.esTablet);
                    n(e, 10, 0, 'botones', o),
                        n(e, 16, 0, t.statusMensajes)
                }), (function (n, e) {
                    var t = e.component;
                    n(e, 4, 0, t.datosConfirmacion.titulo),
                        n(e, 12, 0, t.deshabilitarBtn)
                }))
            }
            var Fe = t('zbbk'),
                De = t('vxsF'),
                Te = t('ZYCi'),
                Ee = t('OmmO'),
                Ne = t('acAY'),
                Ae = t('kL4H'),
                Ve = t('w09O'),
                Be = t('kuV8'),
                Ue = t('jNeJ'),
                Le = t('OP3m'),
                $e = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.loading-container[_ngcontent-%COMP%]{height:100%;width:100%;position:relative}.loading-container[_ngcontent-%COMP%] > iframe[_ngcontent-%COMP%]{width:100%}loading[_ngcontent-%COMP%]{position:absolute;top:calc((100% - 40px)/ 2);left:calc((100% - 40px)/ 2)}#firmaOperacion[_ngcontent-%COMP%]{visibility:hidden}#firmaOperacion.show[_ngcontent-%COMP%]{visibility:visible}.cabecera-resumen[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;font-size:1.875rem;color:#0b7ad0;margin-top:40px;margin-bottom:60px}.cabecera-resumen.borrar[_ngcontent-%COMP%]{margin-bottom:0}.modal-principal[_ngcontent-%COMP%]{height:calc(100vh - 200px)}.modal-principal.firma-noDemo[_ngcontent-%COMP%]{height:auto}.operacion-resumen[_ngcontent-%COMP%]{height:calc(100vh - 200px)}.operacion-resumen.firma-noDemo[_ngcontent-%COMP%]{height:auto}.operacion-resumen[_ngcontent-%COMP%]   .texto-seccion[_ngcontent-%COMP%]{font-size:2.75rem;line-height:56px;color:#33393e;font-family:Ibercaja-Light,sans-serif}.operacion-correcta[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%], .operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]{max-width:503px}.operacion-correcta[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]   span[_ngcontent-%COMP%], .operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-size:.6875rem;line-height:20px;color:#33393e;font-family:Ibercaja-Regular,sans-serif}.operacion-correcta[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]   span.bold[_ngcontent-%COMP%], .operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]   span.bold[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.operacion-correcta[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]{margin:13px auto 0;text-align:left;width:465px}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]{margin-top:80px;margin-bottom:30px}.operacion-correcta[_ngcontent-%COMP%]   .botones.periodicidad[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-correcta[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-incorrecta[_ngcontent-%COMP%]   .botones.periodicidad[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-incorrecta[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-personalizada[_ngcontent-%COMP%]   .botones.periodicidad[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-personalizada[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type{margin-right:0}.operacion-correcta[_ngcontent-%COMP%]   span[modal-texto-ok][_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   span[modal-texto-ok][_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   span[modal-texto-ok][_ngcontent-%COMP%]{display:block}.operacion-personalizada[_ngcontent-%COMP%]   .titulo[_ngcontent-%COMP%]{font-size:2.25rem;color:#33393e;text-transform:none;line-height:24px}.operacion-personalizada[_ngcontent-%COMP%]   .txt-titulo[_ngcontent-%COMP%]{font-size:2.25rem;line-height:46px;font-family:Ibercaja-Light,sans-serif;display:block;color:#33393e}.operacion-personalizada[_ngcontent-%COMP%]   .txt-texto[_ngcontent-%COMP%]{margin-top:15px;font-family:Ibercaja-Light,sans-serif;font-size:1.25rem;line-height:32px;display:block;color:rgba(51,57,62,.7)}.operacion-personalizada[_ngcontent-%COMP%]   .iconoFirma[_ngcontent-%COMP%]{display:block;text-align:center;margin-bottom:51px}.operacion-personalizada[_ngcontent-%COMP%]   .iconoFirma[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#fff;font-size:2.5rem;background:#dd4c40;padding:28px;border-radius:2px;display:inline-block}.operacion-personalizada[_ngcontent-%COMP%]   .operacion-pendiente-firma[_ngcontent-%COMP%]{padding-top:21px}.texto-seccion[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;color:#0b7ad0;font-size:2.25rem;line-height:2.625rem}.botones.lineal[_ngcontent-%COMP%]{margin-top:51px}.botones.lineal[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]{display:inline-block;margin-left:15px}.botones.lineal[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]:first-of-type{margin-left:0}.botones.bloque[_ngcontent-%COMP%]{padding-bottom:109px!important}.botones.bloque[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]{display:block;margin-top:15px}.botones.bloque[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]:first-of-type{margin-top:0}.botones.unico[_ngcontent-%COMP%]{text-align:center}.botones.unico[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]{min-width:165px}.botones.ok[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]:nth-of-type(2){margin-left:32px}.botones.botones-resumen[_ngcontent-%COMP%]{padding:20px 0;margin-top:38px;text-align:center;width:100%}.botones.botones-resumen[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:nth-of-type(2){margin-left:12px}.button[_ngcontent-%COMP%]{text-align:center;margin:0 auto;padding:16px 31px;border-radius:2px;font-size:.875rem;text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.button.continuar[_ngcontent-%COMP%]{display:block}.button.opcion[_ngcontent-%COMP%]{display:inline-block}.button.opcion[_ngcontent-%COMP%]:first-of-type{margin-right:32px}.button.sin-margin[_ngcontent-%COMP%]{margin:0!important}.selector-tarjeta[_ngcontent-%COMP%]{padding-top:79px}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]{width:171px;border:1px solid #2d5b7f;padding:13px 0;display:inline-block;text-align:center;cursor:pointer}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#2d5b7f;font-size:.75rem;font-family:Ibercaja-Regular,sans-serif}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]:first-of-type{border-top-left-radius:2px;border-bottom-left-radius:2px;border-right:none}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]:last-of-type{border-top-right-radius:2px;border-bottom-right-radius:2px}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector.active[_ngcontent-%COMP%]{background-color:#2d5b7f!important;border-color:#2d5b7f}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector.active[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#fff}.back[_ngcontent-%COMP%]{padding-top:25px;display:flex;align-items:center}.back[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{cursor:pointer;height:24px;width:24px;line-height:24px;text-align:center;font-size:9px;color:#fff;background-color:#0b7ad0;border-radius:2px}.back[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{font-family:Ibercaja-Light,sans-serif;font-size:1.25rem;margin-left:12px;color:rgba(51,57,62,.7)}.back[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.importe-financiar[_ngcontent-%COMP%]{font-size:.9375rem;margin-top:12px;margin-left:30px}.importe-financiar[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#33393e;display:inline-block}.importe-financiar[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:first-of-type{font-family:Ibercaja-Regular,sans-serif;margin-right:6px}.importe-financiar[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:first-of-type:first-letter{text-transform:uppercase}.importe-financiar[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]:nth-of-type(2){font-family:Ibercaja-Medium,sans-serif}.alert-info[_ngcontent-%COMP%]{display:flex;padding:20px;align-items:center;background-color:#e6f1fa;border:1px solid #0b7ad0;border-radius:2px;margin-top:28px;max-width:640px}.alert-info[_ngcontent-%COMP%]   img[_ngcontent-%COMP%]{height:24px;width:24px;margin-right:16px}.alert-info[_ngcontent-%COMP%]   .info[_ngcontent-%COMP%]{color:#0b7ad0;font-size:.875rem;line-height:1.25rem;font-family:Ibercaja-Regular,sans-serif}.alert-info[_ngcontent-%COMP%]   .info[_ngcontent-%COMP%]   .bold[_ngcontent-%COMP%]{font-family:Ibercaja-Medium,sans-serif}.click-device[_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover, .click-device   [_nghost-%COMP%]   .button[_ngcontent-%COMP%]:disabled:hover{background-color:rgba(38,38,42,.08);color:rgba(0,0,0,.19);cursor:initial}.click-device[_nghost-%COMP%]   .selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]:hover, .click-device   [_nghost-%COMP%]   .selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]:hover{background-color:rgba(11,122,208,.3)}.mobile[_nghost-%COMP%]   .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .mobile[_nghost-%COMP%]   .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .mobile   [_nghost-%COMP%]   .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]{padding-bottom:109px!important}.ie[_nghost-%COMP%]   .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .ie   [_nghost-%COMP%]   .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .ie[_nghost-%COMP%]   .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .ie   [_nghost-%COMP%]   .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .ie[_nghost-%COMP%]   .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .ie   [_nghost-%COMP%]   .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]{margin-bottom:80px}@media screen and (max-width:1023px){.close-button[_ngcontent-%COMP%]   .ibercaja-icon-Lightbox[_ngcontent-%COMP%]{color:#f5f8fa;font-size:1rem;padding:5px;position:relative;z-index:2;display:block}.modal-nav[_ngcontent-%COMP%] + .modal-principal[_ngcontent-%COMP%]{height:calc(100vh - 200px)}.modal-nav[_ngcontent-%COMP%] + .modal-principal.firma-noDemo[_ngcontent-%COMP%]{height:auto}.cabecera-mobile[_ngcontent-%COMP%]{display:flex;align-items:center;color:#f5f8fa;padding:0 17px;font-size:.875rem;height:48px;position:relative;background-color:rgba(45,91,127,.5);text-transform:uppercase;font-family:Ibercaja-Medium,sans-serif}.cabecera-mobile[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{width:calc(100% - 40px)}.texto-seccion[_ngcontent-%COMP%]{color:#33393e;font-size:1.125rem;font-family:Ibercaja-Regular,sans-serif;padding-bottom:19px;display:block;line-height:28px}.botones.unico[_ngcontent-%COMP%]   .button[_ngcontent-%COMP%]{min-width:225px}.botones.flotante[_ngcontent-%COMP%]{position:sticky;position:-webkit-sticky;bottom:15px}.botones[_ngcontent-%COMP%]   .button.continuar[_ngcontent-%COMP%]{margin:0 auto;text-align:center;box-shadow:1px 2px 11px 0 rgba(0,0,0,.22);background-color:#0b7ad0;color:#f5f8fa;padding:16px 41px;border:none;z-index:1}.botones[_ngcontent-%COMP%]   .button.continuar[_ngcontent-%COMP%]:disabled{background-color:#eee;color:rgba(0,0,0,.19)}.botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]{display:block;margin:16px auto 0;text-align:center;position:relative;bottom:initial;left:initial;box-shadow:none;padding:16px 41px}.botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type{margin-right:auto}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]{display:inline-block}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type{margin-right:32px}.selector-tarjeta[_ngcontent-%COMP%]{padding:17px}.selector-tarjeta[_ngcontent-%COMP%]   .btn-selector[_ngcontent-%COMP%]{width:50%}.operacion-correcta[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-incorrecta[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-personalizada[_ngcontent-%COMP%]   .botones.unico[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type{margin:0 auto}.operacion-resumen[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]{padding:0 17px;width:100%;max-width:100%}.operacion-resumen[_ngcontent-%COMP%]   operacion-flujo.firma[_ngcontent-%COMP%]{position:fixed;top:48px;width:100%;z-index:1}.operacion-resumen[_ngcontent-%COMP%]   .loading-container[_ngcontent-%COMP%]{height:calc(100% - 57px);margin-top:57px}.back[_ngcontent-%COMP%]{padding:16px 20px 16px 16px}.back[_ngcontent-%COMP%]   .icono[_ngcontent-%COMP%]{height:32px;width:32px;line-height:32px;text-align:center;font-size:12px;box-shadow:1px 2px 11px 0 rgba(0,0,0,.22)}.back[_ngcontent-%COMP%]   .texto[_ngcontent-%COMP%]{font-size:1.125rem}.alert-info[_ngcontent-%COMP%]{margin-left:17px;margin-right:17px;max-width:100%}}@media screen and (max-width:767px){.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]{margin-top:40px}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.cerrar[_ngcontent-%COMP%], .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.firmar[_ngcontent-%COMP%], .operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.periodico[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.cerrar[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.firmar[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.periodico[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.cerrar[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.firmar[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.periodico[_ngcontent-%COMP%]{min-width:220px}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%], .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%], .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]{display:block}.operacion-correcta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-incorrecta[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type, .operacion-personalizada[_ngcontent-%COMP%]   .botones[_ngcontent-%COMP%]   .button.opcion[_ngcontent-%COMP%]:first-of-type{margin-right:auto}.operacion-personalizada[_ngcontent-%COMP%]   .txt-titulo[_ngcontent-%COMP%]{font-size:1rem;line-height:19px;font-family:Ibercaja-Medium,sans-serif}.operacion-personalizada[_ngcontent-%COMP%]   .txt-texto[_ngcontent-%COMP%]{font-size:.8125rem;line-height:20px}.operacion-personalizada[_ngcontent-%COMP%]   .iconoFirma[_ngcontent-%COMP%]{display:block;text-align:center;margin-bottom:51px}.operacion-personalizada[_ngcontent-%COMP%]   .iconoFirma[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{color:#fff;font-size:2.5rem;background:#dd4c40;padding:28px;border-radius:2px;display:inline-block}.operacion-correcta[_ngcontent-%COMP%]   .text-info[_ngcontent-%COMP%]{width:100%}.botones.ok[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]:nth-of-type(2){margin-left:0}.botones.botones-resumen[_ngcontent-%COMP%]{padding:20px 16px}.botones.botones-resumen[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]{width:100%}.botones.botones-resumen[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]:nth-of-type(2){margin-left:0;margin-top:12px}}']
                    ],
                    data: {
                    }
                });
            function Ke(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-left-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'operativas-dropdown', [
                    ], null, null, null, xe, Oe)),
                    o['ɵdid'](2, 114688, null, 0, he, [
                        l.a
                    ], {
                        propiedades: [
                            0,
                            'propiedades'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.propiedadesFormaEnvio)
                }), null)
            }
            function Ge(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-left-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'operativas-dropdown', [
                    ], null, null, null, xe, Oe)),
                    o['ɵdid'](2, 114688, null, 0, he, [
                        l.a
                    ], {
                        propiedades: [
                            0,
                            'propiedades'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.propiedadesEmail)
                }), null)
            }
            function He(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-left-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'resumen-duplicados', [
                    ], null, null, null, je, Se)),
                    o['ɵdid'](2, 114688, null, 0, we, [
                        y.a,
                        a.a,
                        l.a,
                        p.a,
                        r.a
                    ], {
                        datosConfirmacion: [
                            0,
                            'datosConfirmacion'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.datosConfirmacion)
                }), null)
            }
            function qe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 15, 'app-modal-tres-secciones-navegacion', [
                    ], null, [
                        [null,
                            'modalClose']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'modalClose' === e && (o = !1 !== n.component.cancelar() && o),
                            o
                    }), Fe.b, Fe.a)),
                    o['ɵdid'](1, 114688, null, 0, De.a, [
                        Te.m,
                        d.a,
                        a.a,
                        p.a
                    ], null, {
                        modalClose: 'modalClose'
                    }),
                    (n() (), o['ɵeld'](2, 0, null, 0, 2, 'div', [
                        ['modal-left-top',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'operacion-navegacion', [
                    ], null, null, null, Ee.b, Ee.a)),
                    o['ɵdid'](4, 114688, null, 0, Ne.a, [
                        l.a,
                        p.a
                    ], null, null),
                    (n() (), o['ɵand'](16777216, null, 1, 1, null, Ke)),
                    o['ɵdid'](6, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 1, 1, null, Ge)),
                    o['ɵdid'](8, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 1, 1, null, He)),
                    o['ɵdid'](10, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](11, 0, null, 2, 4, 'div', [
                        ['modal-right',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](12, 0, null, null, 3, 'operacion-flujo', [
                    ], null, null, null, Ae.b, Ae.a)),
                    o['ɵprd'](4608, null, Ve.a, Ve.a, [
                    ]),
                    o['ɵprd'](4608, null, H.CurrencyPipe, H.CurrencyPipe, [
                        o.LOCALE_ID
                    ]),
                    o['ɵdid'](15, 8503296, null, 0, Be.a, [
                        l.a,
                        p.a,
                        O.a
                    ], null, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0),
                        n(e, 4, 0),
                        n(e, 6, 0, 0 == t.navegacionDuplicado.indiceSeccion),
                        n(e, 8, 0, 1 == t.navegacionDuplicado.indiceSeccion && 'correo electrónico' == t.navegacionDuplicado.pasos[t.navegacionDuplicado.indiceSeccion].tituloSeccion),
                        n(e, 10, 0, 'confirmación' == t.navegacionDuplicado.pasos[t.navegacionDuplicado.indiceSeccion].tituloSeccion),
                        n(e, 15, 0)
                }), null)
            }
            function We(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'operativas-dropdown', [
                    ], null, null, null, xe, Oe)),
                    o['ɵdid'](2, 114688, null, 0, he, [
                        l.a
                    ], {
                        propiedades: [
                            0,
                            'propiedades'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.propiedadesFormaEnvio)
                }), null)
            }
            function Je(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'operativas-dropdown', [
                    ], null, null, null, xe, Oe)),
                    o['ɵdid'](2, 114688, null, 0, he, [
                        l.a
                    ], {
                        propiedades: [
                            0,
                            'propiedades'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.propiedadesEmail)
                }), null)
            }
            function Xe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['modal-bottom',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'resumen-duplicados', [
                    ], null, null, null, je, Se)),
                    o['ɵdid'](2, 114688, null, 0, we, [
                        y.a,
                        a.a,
                        l.a,
                        p.a,
                        r.a
                    ], {
                        datosConfirmacion: [
                            0,
                            'datosConfirmacion'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.datosConfirmacion)
                }), null)
            }
            function Ze(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 16, 'app-modal-tres-secciones-navegacion', [
                    ], null, [
                        [null,
                            'modalClose']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'modalClose' === e && (o = !1 !== n.component.cancelar() && o),
                            o
                    }), Fe.b, Fe.a)),
                    o['ɵdid'](1, 114688, null, 0, De.a, [
                        Te.m,
                        d.a,
                        a.a,
                        p.a
                    ], null, {
                        modalClose: 'modalClose'
                    }),
                    (n() (), o['ɵeld'](2, 0, null, 3, 3, 'div', [
                        ['modal-top',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](3, 0, null, null, 2, 'div', [
                        ['class',
                            ' cabecera-mobile']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Solictud de duplicados'
                    ])),
                    (n() (), o['ɵeld'](6, 0, null, 4, 4, 'div', [
                        ['modal-nav',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 3, 'operacion-flujo', [
                    ], null, null, null, Ae.b, Ae.a)),
                    o['ɵprd'](4608, null, Ve.a, Ve.a, [
                    ]),
                    o['ɵprd'](4608, null, H.CurrencyPipe, H.CurrencyPipe, [
                        o.LOCALE_ID
                    ]),
                    o['ɵdid'](10, 8503296, null, 0, Be.a, [
                        l.a,
                        p.a,
                        O.a
                    ], null, null),
                    (n() (), o['ɵand'](16777216, null, 6, 1, null, We)),
                    o['ɵdid'](12, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 6, 1, null, Je)),
                    o['ɵdid'](14, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 6, 1, null, Xe)),
                    o['ɵdid'](16, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0),
                        n(e, 10, 0),
                        n(e, 12, 0, 0 == t.navegacionDuplicado.indiceSeccion),
                        n(e, 14, 0, 1 == t.navegacionDuplicado.indiceSeccion && 'correo electrónico' == t.navegacionDuplicado.pasos[t.navegacionDuplicado.indiceSeccion].tituloSeccion),
                        n(e, 16, 0, 'confirmación' == t.navegacionDuplicado.pasos[t.navegacionDuplicado.indiceSeccion].tituloSeccion)
                }), null)
            }
            function Ye(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                        ['class',
                            'texto'],
                        [
                            'modal-texto-ok',
                            ''
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        ' El duplicado que solicitaste llegará en breve a la dirección de correo que nos indicaste. '
                    ]))
                ], null, null)
            }
            function Qe(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                        ['class',
                            'texto'],
                        [
                            'modal-texto-ok',
                            ''
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        ' El duplicado que solicitaste llegará en 2-3 días a tu domicilio. '
                    ]))
                ], null, null)
            }
            function nt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 9, 'app-modal-aviso', [
                        ['class',
                            'operacion-correcta']
                    ], null, null, null, Ue.b, Ue.a)),
                    o['ɵdid'](1, 114688, null, 0, Le.a, [
                        d.a,
                        p.a,
                        a.a
                    ], {
                        confirmacion: [
                            0,
                            'confirmacion'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 0, 1, null, Ye)),
                    o['ɵdid'](3, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, 0, 1, null, Qe)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](6, 0, null, 2, 3, 'div', [
                        ['class',
                            'botones'],
                        [
                            'modal-ok-bottom',
                            ''
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 2, 'button', [
                        ['class',
                            'button btn-primary-blue']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.cancelar() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Cerrar'
                    ]))
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, !0),
                        n(e, 3, 0, 1 == t.navegacionDuplicado.pasos[0].subsecciones[0].datosSeleccionados.dato.id),
                        n(e, 5, 0, 2 == t.navegacionDuplicado.pasos[0].subsecciones[0].datosSeleccionados.dato.id)
                }), null)
            }
            function et(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 10, 'app-modal-aviso', [
                        ['class',
                            'operacion-incorrecta']
                    ], null, null, null, Ue.b, Ue.a)),
                    o['ɵdid'](1, 114688, null, 0, Le.a, [
                        d.a,
                        p.a,
                        a.a
                    ], {
                        error: [
                            0,
                            'error'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](2, 0, null, 3, 1, 'span', [
                        ['modal-titulo-ko',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'La solicitud no se ha podido realizar'
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, 4, 1, 'span', [
                        ['modal-texto-ko',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris sed ullamcorper nibh. Donec a lorem semper dui ultrices elementum in tempus nulla. Nulla facilisi. Aliquam feugiat lacus metus, vel cursus leo fermentum venenatis. '
                    ])),
                    (n() (), o['ɵeld'](6, 0, null, 5, 4, 'div', [
                        ['modal-ko',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 3, 'div', [
                        ['class',
                            'botones']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](8, 0, null, null, 2, 'button', [
                        ['class',
                            'button opcion btn-secondary-black']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.cancelar() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](9, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Cerrar'
                    ]))
                ], (function (n, e) {
                    n(e, 1, 0, !0)
                }), null)
            }
            function tt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵand'](16777216, null, null, 1, null, qe)),
                    o['ɵdid'](1, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Ze)),
                    o['ɵdid'](3, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, nt)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, et)),
                    o['ɵdid'](7, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 1, 0, !t.responsive.esMobile && !t.responsive.esTablet),
                        n(e, 3, 0, t.responsive.esMobile || t.responsive.esTablet),
                        n(e, 5, 0, 0 == t.estadoDuplicado),
                        n(e, 7, 0, 1 == t.estadoDuplicado)
                }), null)
            }
            function ot(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'pedir-duplicado', [
                    ], null, null, null, tt, $e)),
                    o['ɵdid'](1, 114688, null, 0, g, [
                        l.a,
                        d.a,
                        r.a,
                        p.a,
                        a.a,
                        u.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            var lt = o['ɵccf']('pedir-duplicado', g, ot, {
                }, {
                }, [
                ]),
                it = t('gIcY'),
                at = function () {
                    function n(n) {
                        this.responsive = n,
                            this.enviarElementosSeleccionados = new o.EventEmitter,
                            this.mostrarFiltros = !1,
                            this.mostrarTodos = !0,
                            this.valoresFiltros = {
                                alias: '',
                                numero: '',
                                visibilidad: ''
                            },
                            this.placeholderVisibilidadFiltro = '',
                            this.visibilidad = [
                            ],
                            this.visibilidadSeleccionados = [
                            ],
                            this.mostrar = !0
                    }
                    return n.prototype.ngOnInit = function () {
                        this.productoOriginal = Object.assign({
                        }, this.producto),
                            this.SetUpVisibilidadFiltro()
                    },
                        n.prototype.verMasMenosProductos = function (n) {
                            this.mostrarTodos || (this.producto.items = this.producto.items.slice(0, 3))
                        },
                        n.prototype.cambiarVerMasMenos = function (n) {
                            this.mostrarTodos = !this.mostrarTodos
                        },
                        n.prototype.filtroMasMenos = function (n) {
                            this.producto = Object.assign({
                            }, this.productoOriginal),
                                this.filterAction(),
                                this.verMasMenosProductos(n)
                        },
                        n.prototype.filterAction = function () {
                            var n = this;
                            '' != this.valoresFiltros.alias && (this.producto.items = this.producto.items.filter((function (e) {
                                return e.alias.toUpperCase().includes(n.valoresFiltros.alias.toUpperCase())
                            }))),
                            '' != this.valoresFiltros.numero && (this.producto.items = this.producto.items.filter((function (e) {
                                return e.nProducto.toUpperCase().includes(n.valoresFiltros.numero.toUpperCase())
                            }))),
                            this.visibilidadSeleccionados.length > 0 && this.visibilidadSeleccionados.length < 2 && (this.producto.items = this.producto.items.filter(0 == this.visibilidadSeleccionados[0] ? function (n) {
                                    return !0 === n.visibilidad
                                }
                                : function (n) {
                                    return !1 === n.visibilidad
                                })),
                                this.mostrar = '' == this.valoresFiltros.numero && '' == this.valoresFiltros.alias && '' == this.valoresFiltros.visibilidad || !(this.producto.items.length <= 3)
                        },
                        n.prototype.seleccionItems = function (n) {
                            n.visibilidad = !n.visibilidad,
                                this.enviarElementosSeleccionados.emit({
                                    item: n,
                                    claseCuenta: this.productosSeleccionado.id
                                })
                        },
                        n.prototype.seleccionarVisibilidad = function (n) {
                            this.visibilidadSeleccionados = n.elementos
                        },
                        n.prototype.SetUpVisibilidadFiltro = function () {
                            this.visibilidad = [
                                {
                                    id: 0,
                                    texto: 'Visible',
                                    idEstado: 0
                                },
                                {
                                    id: 1,
                                    texto: 'No visible',
                                    idEstado: 1
                                }
                            ],
                                this.placeholderVisibilidadFiltro = 'Visibilidad'
                        },
                        n
                }(),
                ct = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.buzon-container[_ngcontent-%COMP%]{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:bottom}.buzon-container[_ngcontent-%COMP%]   .subtitle[_ngcontent-%COMP%]{width:calc(50% - 19px);margin-bottom:0;margin-top:70px;font-family:Ibercaja-Medium,sans-serif;font-size:1.125rem;color:#33393e;display:block;margin-left:19px;position:relative}.buzon-container[_ngcontent-%COMP%]   .subtitle[_ngcontent-%COMP%]::first-letter{text-transform:uppercase}.buzon-container[_ngcontent-%COMP%]   .subtitle[_ngcontent-%COMP%]:after{content:"|";font-size:1.125rem;color:#2d5b7f;position:absolute;left:-20px;top:0}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]{width:100%;max-height:0;overflow:hidden;padding-top:24px;transition:max-height .15s ease-in-out}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]{display:flex;flex-wrap:wrap;justify-content:flex-start}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]   input[_ngcontent-%COMP%]{width:100%}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:first-child{margin-bottom:30px;width:calc(100% / 3)}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2){margin:0 10px}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2), .buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(3){width:calc((100% / 3) - 10px)}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .button-container[_ngcontent-%COMP%]{width:100%;text-align:right;margin-top:12px}.buzon-container[_ngcontent-%COMP%]   .filters-container.show[_ngcontent-%COMP%]{max-height:200px;padding-bottom:15px;padding-top:24px}.buzon-container[_ngcontent-%COMP%]   .filters__button[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;margin-top:70px}.buzon-container[_ngcontent-%COMP%]   .filters__button[_ngcontent-%COMP%]   span[_ngcontent-%COMP%]{font-family:Ibercaja-Regular,sans-serif;font-size:.75rem;display:inline-block;vertical-align:middle;margin-right:10px}.buzon-container[_ngcontent-%COMP%]   .filters__button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{display:inline-block;vertical-align:middle;font-size:12px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]{box-shadow:0 2px 4px 0 rgba(0,0,0,.1);width:100%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%]{display:flex;align-items:center;padding:0 0 0 24px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:first-of-type{width:24%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-of-type(2){width:50%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]{padding-left:24px;height:64px;background-color:#fff;display:flex;align-items:center;border-bottom:1px solid rgba(51,57,62,.1);position:relative;transition:transform 50ms ease-in;padding-right:24px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]:first-of-type{border-radius:2px 2px 0 0}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%]{display:flex;flex-direction:row;width:76%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{font-size:.875rem;line-height:1rem;color:rgba(51,57,62,.7);padding-right:6px;white-space:pre-wrap;width:32%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-child(2){color:#33393e}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]{display:flex;align-items:center}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .estado-switch[_ngcontent-%COMP%]{color:#c0cdd8;transition:color .4s ease-in;margin-right:16px;font-size:.8125rem;min-width:80px;text-align:right}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .estado-switch.active[_ngcontent-%COMP%]{color:#0b7ad0}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .estado-switch.noVisibleBoton[_ngcontent-%COMP%]{color:#33393e}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .check[_ngcontent-%COMP%]{cursor:pointer;background-color:#c0cdd8;border-radius:10.8px;height:22px;width:41px;position:relative;transition:all .5s ease-in}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .check[_ngcontent-%COMP%]:after{content:\'\';position:absolute;background-color:#fff;height:18px;width:18px;border-radius:11px;top:2px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .check[_ngcontent-%COMP%]:not(.active):after{left:2px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .check.active[_ngcontent-%COMP%]{background-color:#0b7ad0}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .check.active[_ngcontent-%COMP%]:after{right:2px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container.disabled[_ngcontent-%COMP%]{pointer-events:none;width:auto;position:initial}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .disabled[_ngcontent-%COMP%]{position:absolute;height:100%;width:100%;top:0;left:0;opacity:.5;background-color:#fff;z-index:10;pointer-events:none}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .viewMore__container[_ngcontent-%COMP%]{display:flex;justify-content:center;align-items:center;height:68px;background-color:#fff;margin:0 auto}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .viewMore__container[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]{display:flex;padding:20px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .viewMore__container[_ngcontent-%COMP%] > button[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{font-size:.75rem;font-family:Ibercaja-Medium,sans-serif;color:#000;display:inline-block;margin-right:14px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .viewMore__container[_ngcontent-%COMP%] > button[_ngcontent-%COMP%]   [class^=ibercaja-icon][_ngcontent-%COMP%]{font-size:.75rem}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-child(1){width:calc(75% / 3)}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-child(2){width:calc(100% / 2)}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-child(3){padding-right:0;text-align:right}@media screen and (max-width:1023px){.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]{display:flex;flex-direction:column}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > *[_ngcontent-%COMP%]{width:100%}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(1){margin:0;width:100%}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%] > [_ngcontent-%COMP%]:nth-child(2){margin:24px 0;width:100%}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]   .dropdownFilter[_ngcontent-%COMP%]{width:calc(100% - 2px);margin:auto}.buzon-container[_ngcontent-%COMP%]   .filters-container[_ngcontent-%COMP%]   .top[_ngcontent-%COMP%]   .dropdownFilter[_ngcontent-%COMP%]   button[_ngcontent-%COMP%]{margin:0!important}.buzon-container[_ngcontent-%COMP%]   .filters-container.show[_ngcontent-%COMP%]{max-height:330px;height:320px;padding-bottom:15px;padding-top:24px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]{box-shadow:none}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]{height:88px;margin-bottom:16px;border-bottom:none;display:flex;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);padding:22px;justify-content:space-between}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%]{display:flex;flex-direction:column;color:rgba(51,57,62,.5)}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]{width:88%}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .table-item-block[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-child(2){margin-top:8px;color:#33393e}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]{display:flex;flex-direction:column;align-items:flex-end}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .table-item[_ngcontent-%COMP%]   .switch-container[_ngcontent-%COMP%]   .estado-switch[_ngcontent-%COMP%]{text-align:right;margin:0 0 10px}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-content[_ngcontent-%COMP%]   .viewMore__container[_ngcontent-%COMP%]{background-color:transparent}.buzon-container[_ngcontent-%COMP%]   .table-container[_ngcontent-%COMP%]   .table-header[_ngcontent-%COMP%] > span[_ngcontent-%COMP%]:nth-of-type(2){width:44%}}']
                    ],
                    data: {
                    }
                });
            function rt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 4, 'button', [
                        ['class',
                            'filters__button']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.mostrarFiltros = !l.mostrarFiltros) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'span', [
                        ['title',
                            'Filtra resultados']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Filtra resultados'
                    ])),
                    (n() (), o['ɵeld'](3, 0, null, null, 1, 'div', [
                    ], null, null, null, null, null)),
                    o['ɵdid'](4, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 4, 0, e.component.mostrarFiltros ? 'ibercaja-icon-Chevron-arriba' : 'ibercaja-icon-Chevron-abajo')
                }), null)
            }
            function st(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 21, 'div', [
                        ['class',
                            'filters-container']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        show: 0
                    }),
                    (n() (), o['ɵeld'](3, 0, null, null, 14, 'div', [
                        ['class',
                            'top']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](4, 0, null, null, 5, 'input', [
                        ['class',
                            'custom-input'],
                        [
                            'placeholder',
                            'Filtra por alias'
                        ],
                        [
                            'type',
                            'text'
                        ]
                    ], [
                        [2,
                            'ng-untouched',
                            null],
                        [
                            2,
                            'ng-touched',
                            null
                        ],
                        [
                            2,
                            'ng-pristine',
                            null
                        ],
                        [
                            2,
                            'ng-dirty',
                            null
                        ],
                        [
                            2,
                            'ng-valid',
                            null
                        ],
                        [
                            2,
                            'ng-invalid',
                            null
                        ],
                        [
                            2,
                            'ng-pending',
                            null
                        ]
                    ], [
                        [null,
                            'ngModelChange'],
                        [
                            null,
                            'input'
                        ],
                        [
                            null,
                            'blur'
                        ],
                        [
                            null,
                            'compositionstart'
                        ],
                        [
                            null,
                            'compositionend'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'input' === e && (l = !1 !== o['ɵnov'](n, 5)._handleInput(t.target.value) && l),
                        'blur' === e && (l = !1 !== o['ɵnov'](n, 5).onTouched() && l),
                        'compositionstart' === e && (l = !1 !== o['ɵnov'](n, 5)._compositionStart() && l),
                        'compositionend' === e && (l = !1 !== o['ɵnov'](n, 5)._compositionEnd(t.target.value) && l),
                        'ngModelChange' === e && (l = !1 !== (i.valoresFiltros.alias = t) && l),
                            l
                    }), null, null)),
                    o['ɵdid'](5, 16384, null, 0, it.d, [
                        o.Renderer2,
                        o.ElementRef,
                        [
                            2,
                            it.a
                        ]
                    ], null, null),
                    o['ɵprd'](1024, null, it.k, (function (n) {
                        return [n]
                    }), [
                        it.d
                    ]),
                    o['ɵdid'](7, 671744, null, 0, it.p, [
                        [8,
                            null],
                        [
                            8,
                            null
                        ],
                        [
                            8,
                            null
                        ],
                        [
                            6,
                            it.k
                        ]
                    ], {
                        model: [
                            0,
                            'model'
                        ]
                    }, {
                        update: 'ngModelChange'
                    }),
                    o['ɵprd'](2048, null, it.l, null, [
                        it.p
                    ]),
                    o['ɵdid'](9, 16384, null, 0, it.m, [
                        [4,
                            it.l]
                    ], null, null),
                    (n() (), o['ɵeld'](10, 0, null, null, 5, 'input', [
                        ['class',
                            'custom-input'],
                        [
                            'placeholder',
                            'Filtra por nº de producto'
                        ],
                        [
                            'type',
                            'text'
                        ]
                    ], [
                        [2,
                            'ng-untouched',
                            null],
                        [
                            2,
                            'ng-touched',
                            null
                        ],
                        [
                            2,
                            'ng-pristine',
                            null
                        ],
                        [
                            2,
                            'ng-dirty',
                            null
                        ],
                        [
                            2,
                            'ng-valid',
                            null
                        ],
                        [
                            2,
                            'ng-invalid',
                            null
                        ],
                        [
                            2,
                            'ng-pending',
                            null
                        ]
                    ], [
                        [null,
                            'ngModelChange'],
                        [
                            null,
                            'input'
                        ],
                        [
                            null,
                            'blur'
                        ],
                        [
                            null,
                            'compositionstart'
                        ],
                        [
                            null,
                            'compositionend'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'input' === e && (l = !1 !== o['ɵnov'](n, 11)._handleInput(t.target.value) && l),
                        'blur' === e && (l = !1 !== o['ɵnov'](n, 11).onTouched() && l),
                        'compositionstart' === e && (l = !1 !== o['ɵnov'](n, 11)._compositionStart() && l),
                        'compositionend' === e && (l = !1 !== o['ɵnov'](n, 11)._compositionEnd(t.target.value) && l),
                        'ngModelChange' === e && (l = !1 !== (i.valoresFiltros.numero = t) && l),
                            l
                    }), null, null)),
                    o['ɵdid'](11, 16384, null, 0, it.d, [
                        o.Renderer2,
                        o.ElementRef,
                        [
                            2,
                            it.a
                        ]
                    ], null, null),
                    o['ɵprd'](1024, null, it.k, (function (n) {
                        return [n]
                    }), [
                        it.d
                    ]),
                    o['ɵdid'](13, 671744, null, 0, it.p, [
                        [8,
                            null],
                        [
                            8,
                            null
                        ],
                        [
                            8,
                            null
                        ],
                        [
                            6,
                            it.k
                        ]
                    ], {
                        model: [
                            0,
                            'model'
                        ]
                    }, {
                        update: 'ngModelChange'
                    }),
                    o['ɵprd'](2048, null, it.l, null, [
                        it.p
                    ]),
                    o['ɵdid'](15, 16384, null, 0, it.m, [
                        [4,
                            it.l]
                    ], null, null),
                    (n() (), o['ɵeld'](16, 0, null, null, 1, 'dropdown-multiselect', [
                        ['class',
                            'dropdownFilter']
                    ], null, [
                        [null,
                            'elementosParaFiltrar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementosParaFiltrar' === e && (o = !1 !== n.component.seleccionarVisibilidad(t) && o),
                            o
                    }), q.b, q.a)),
                    o['ɵdid'](17, 49152, [
                        [1,
                            4],
                        [
                            'visibilidadFilter',
                            4
                        ]
                    ], 0, m.a, [
                    ], {
                        placeholder: [
                            0,
                            'placeholder'
                        ],
                        model: [
                            1,
                            'model'
                        ],
                        id: [
                            2,
                            'id'
                        ],
                        selectAll: [
                            3,
                            'selectAll'
                        ]
                    }, {
                        elementosParaFiltrar: 'elementosParaFiltrar'
                    }),
                    (n() (), o['ɵeld'](18, 0, null, null, 3, 'div', [
                        ['class',
                            'button-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](19, 0, null, null, 2, 'button', [
                        ['class',
                            'btn-primary-blue btn-text-m']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.filtroMasMenos(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](20, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'aplicar filtros'
                    ]))
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 2, 0, t.mostrarFiltros);
                    n(e, 1, 0, 'filters-container', o),
                        n(e, 7, 0, t.valoresFiltros.alias),
                        n(e, 13, 0, t.valoresFiltros.numero),
                        n(e, 17, 0, t.placeholderVisibilidadFiltro, t.visibilidad, 'visibilidad-dropdown' + t.idxProd, !1)
                }), (function (n, e) {
                    n(e, 4, 0, o['ɵnov'](e, 9).ngClassUntouched, o['ɵnov'](e, 9).ngClassTouched, o['ɵnov'](e, 9).ngClassPristine, o['ɵnov'](e, 9).ngClassDirty, o['ɵnov'](e, 9).ngClassValid, o['ɵnov'](e, 9).ngClassInvalid, o['ɵnov'](e, 9).ngClassPending),
                        n(e, 10, 0, o['ɵnov'](e, 15).ngClassUntouched, o['ɵnov'](e, 15).ngClassTouched, o['ɵnov'](e, 15).ngClassPristine, o['ɵnov'](e, 15).ngClassDirty, o['ɵnov'](e, 15).ngClassValid, o['ɵnov'](e, 15).ngClassInvalid, o['ɵnov'](e, 15).ngClassPending)
                }))
            }
            function ut(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](1, null, [
                        '',
                        ''
                    ]))
                ], null, (function (n, e) {
                    n(e, 1, 0, e.context.$implicit)
                }))
            }
            function dt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'div', [
                        ['class',
                            'table-header']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ut)),
                    o['ɵdid'](2, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null)
                ], (function (n, e) {
                    n(e, 2, 0, e.component.producto.headers)
                }), null)
            }
            function pt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 3, 'span', [
                        ['class',
                            'estado-switch']
                    ], null, null, null, null, null)),
                    o['ɵdid'](1, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](2, {
                        active: 0
                    }),
                    (n() (), o['ɵted']( - 1, null, [
                        'Visible'
                    ]))
                ], (function (n, e) {
                    var t = n(e, 2, 0, e.parent.context.$implicit.visibilidad);
                    n(e, 1, 0, 'estado-switch', t)
                }), null)
            }
            function gt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                        ['class',
                            'estado-switch noVisibleBoton']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'No Visible'
                    ]))
                ], null, null)
            }
            function ft(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 14, 'li', [
                        ['class',
                            'table-item']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 5, 'div', [
                        ['class',
                            'table-item-block']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](3, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 2, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](5, null, [
                        '*',
                        ''
                    ])),
                    o['ɵpid'](0, H.SlicePipe, [
                    ]),
                    (n() (), o['ɵeld'](7, 0, null, null, 7, 'div', [
                        ['class',
                            'switch-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, pt)),
                    o['ɵdid'](9, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, gt)),
                    o['ɵdid'](11, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](12, 0, null, null, 2, 'div', [
                        ['class',
                            'check']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.seleccionItems(n.context.$implicit) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](13, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](14, {
                        active: 0
                    })
                ], (function (n, e) {
                    n(e, 9, 0, e.context.$implicit.visibilidad),
                        n(e, 11, 0, !e.context.$implicit.visibilidad);
                    var t = n(e, 14, 0, e.context.$implicit.visibilidad);
                    n(e, 13, 0, 'check', t)
                }), (function (n, e) {
                    n(e, 3, 0, e.context.$implicit.alias),
                        n(e, 5, 0, o['ɵunv'](e, 5, 0, o['ɵnov'](e, 6).transform(e.context.$implicit.nProducto, - 4)))
                }))
            }
            function Ct(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver más'
                    ]))
                ], null, null)
            }
            function mt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'ver menos'
                    ]))
                ], null, null)
            }
            function Pt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 7, 'li', [
                        ['class',
                            'viewMore__container'],
                        [
                            'ng-cloak',
                            ''
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 6, 'button', [
                        ['class',
                            'btn-tertiary-black']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (l.cambiarVerMasMenos(t), o = !1 !== l.filtroMasMenos(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Ct)),
                    o['ɵdid'](3, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, mt)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](6, 0, null, null, 1, 'div', [
                    ], null, null, null, null, null)),
                    o['ɵdid'](7, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        ngClass: [
                            0,
                            'ngClass'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0, !t.mostrarTodos),
                        n(e, 5, 0, t.mostrarTodos),
                        n(e, 7, 0, t.mostrarTodos ? 'ibercaja-icon-Chevron-arriba' : 'ibercaja-icon-Chevron-abajo')
                }), null)
            }
            function Mt(n) {
                return o['ɵvid'](0, [
                    o['ɵqud'](671088640, 1, {
                        tipoVisibilidad: 0
                    }),
                    (n() (), o['ɵeld'](1, 0, null, null, 14, 'div', [
                        ['class',
                            'buzon-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                        ['class',
                            'subtitle']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted'](3, null, [
                        '',
                        ''
                    ])),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, rt)),
                    o['ɵdid'](5, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, st)),
                    o['ɵdid'](7, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](8, 0, null, null, 7, 'div', [
                        ['class',
                            'table-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, dt)),
                    o['ɵdid'](10, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](11, 0, null, null, 4, 'ul', [
                        ['class',
                            'table-content']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, ft)),
                    o['ɵdid'](13, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, Pt)),
                    o['ɵdid'](15, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 5, 0, t.filtros),
                        n(e, 7, 0, t.filtros),
                        n(e, 10, 0, !t.responsive.esTablet && !t.responsive.esTablet),
                        n(e, 13, 0, t.producto.items),
                        n(e, 15, 0, t.productoOriginal.items.length > 3 && t.mostrar && t.producto.items.length > 0)
                }), (function (n, e) {
                    n(e, 3, 0, e.component.producto.titulo)
                }))
            }
            var ht = t('5+XA'),
                Ot = t('dJ09'),
                bt = o['ɵcrt']({
                    encapsulation: 0,
                    styles: [
                        ['.ajuste-buzon-container[_ngcontent-%COMP%]{padding:59px 54px 152px;position:relative}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]:before{content:\'|\';font-family:Ibercaja-Bold,sans-serif;font-size:1.75rem;margin-right:12px;color:#dd4c40}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   .tooltip[_ngcontent-%COMP%]{position:absolute;visibility:hidden;padding:26px;background-color:#4fc4cf;top:98px;left:140px;z-index:1;max-width:450px;border-radius:2px}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   .tooltip[_ngcontent-%COMP%]   p[_ngcontent-%COMP%]{color:#fff;font-size:.75rem;line-height:16px;font-family:Ibercaja-Regular,sans-serif}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   .tooltip.show[_ngcontent-%COMP%]{visibility:visible}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   em[_ngcontent-%COMP%]{margin-left:8px;cursor:pointer;position:relative;font-size:1rem;padding:8px}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   em[_ngcontent-%COMP%]:after{content:"";width:0;height:0;border-right:10px solid transparent;border-top:10px solid transparent;border-left:10px solid transparent;border-bottom:10px solid #4fc4cf;position:absolute;bottom:-6px;left:5px;visibility:hidden}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   h4[_ngcontent-%COMP%]   em.show[_ngcontent-%COMP%]:after{visibility:visible}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .table-contenedor[_ngcontent-%COMP%]{padding-bottom:20px}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .selector-container[_ngcontent-%COMP%]{padding-top:48px}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .selector-container[_ngcontent-%COMP%]   label[_ngcontent-%COMP%]{font-size:.875rem;margin-bottom:6px;font-family:Ibercaja-Medium,sans-serif;color:#33393e;display:block}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .selector-container[_ngcontent-%COMP%]   [_ngcontent-%COMP%]:not(label){width:40%;display:inline-block;min-width:260px}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .botones-guardar[_ngcontent-%COMP%]{text-align:center;padding:20px 0;background-color:#f4f7fd}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .botones-guardar.fixed[_ngcontent-%COMP%]{position:fixed;bottom:0;left:0;width:calc(100% - 330px);z-index:1}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .botones-guardar.fixed.hide[_ngcontent-%COMP%]{opacity:0}@media screen and (max-width:1279px){.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .botones-guardar.fixed[_ngcontent-%COMP%]{width:calc(100% - 48px)}}@media screen and (max-width:1023px){.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .selector-container[_ngcontent-%COMP%]{padding-top:32px}.ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   .selector-container[_ngcontent-%COMP%]   [_ngcontent-%COMP%]:not(label), .ajuste-buzon-container[_ngcontent-%COMP%]   .content-container[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]   .botones-guardar.fixed[_ngcontent-%COMP%]{width:100%}.ajuste-buzon-container[_ngcontent-%COMP%]{padding:59px 16px 152px}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]{font-size:1.125rem}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]:before{content:" ";margin-right:0}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]   .tooltip[_ngcontent-%COMP%]{left:0;position:relative;width:100%;top:7px;padding:0;height:0}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]   .tooltip[_ngcontent-%COMP%]   .ibercaja-icon-Cerrar[_ngcontent-%COMP%]{position:absolute;right:0;top:0;color:#fff;padding:15px}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]   .ibercaja-icon-Info.show[_ngcontent-%COMP%]:after{visibility:visible}.ajuste-buzon-container[_ngcontent-%COMP%]   .subtitle-container[_ngcontent-%COMP%]   .title[_ngcontent-%COMP%]   .ibercaja-icon-Info.show[_ngcontent-%COMP%] + .tooltip[_ngcontent-%COMP%]{visibility:visible;height:auto;padding:26px}}']
                    ],
                    data: {
                    }
                });
            function _t(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'app-demo-info', [
                    ], null, null, null, L.b, L.a)),
                    o['ɵdid'](1, 114688, null, 0, $.a, [
                        a.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function vt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 0, 'em', [
                        ['class',
                            'ibercaja-icon-Cerrar']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.tooltipAjustes = !l.tooltipAjustes) && o),
                            o
                    }), null, null))
                ], null, null)
            }
            function xt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 2, 'section', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 1, 'app-tabla-ajustes-buzon', [
                    ], null, [
                        [null,
                            'enviarElementosSeleccionados']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'enviarElementosSeleccionados' === e && (o = !1 !== n.component.obtenerItems(t, n.context.$implicit) && o),
                            o
                    }), Mt, ct)),
                    o['ɵdid'](2, 114688, null, 0, at, [
                        p.a
                    ], {
                        producto: [
                            0,
                            'producto'
                        ],
                        idxProd: [
                            1,
                            'idxProd'
                        ],
                        productosSeleccionado: [
                            2,
                            'productosSeleccionado'
                        ],
                        filtros: [
                            3,
                            'filtros'
                        ]
                    }, {
                        enviarElementosSeleccionados: 'enviarElementosSeleccionados'
                    })
                ], (function (n, e) {
                    n(e, 2, 0, e.context.$implicit, e.context.index, e.component.productosSeleccionado[e.context.index], !0)
                }), null)
            }
            function wt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 6, 'div', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 2, 'div', [
                        ['class',
                            'table-contenedor'],
                        [
                            'id',
                            'table-contenedor'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, xt)),
                    o['ɵdid'](3, 278528, null, 0, H.NgForOf, [
                        o.ViewContainerRef,
                        o.TemplateRef,
                        o.IterableDiffers
                    ], {
                        ngForOf: [
                            0,
                            'ngForOf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](4, 0, null, null, 2, 'div', [
                        ['class',
                            'botones-guardar'],
                        [
                            'id',
                            'botones-guardar'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 1, 'button', [
                        ['class',
                            'btn-primary-blue btn-text-s']
                    ], [
                        [8,
                            'disabled',
                            0]
                    ], [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.guardarCambios() && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Guardar Cambios'
                    ]))
                ], (function (n, e) {
                    n(e, 3, 0, e.component.productosSeleccionado)
                }), (function (n, e) {
                    n(e, 5, 0, e.component.checkCambios())
                }))
            }
            function St(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 23, null, null, null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 12, 'div', [
                        ['class',
                            'subtitle-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 11, 'h4', [
                        ['class',
                            'title']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Ocultar cuentas '
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 2, 'em', [
                        ['class',
                            'ibercaja-icon-Info']
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0,
                            l = n.component;
                        return 'click' === e && (o = 0 != (l.tooltipAjustes = !l.tooltipAjustes) && o),
                            o
                    }), null, null)),
                    o['ɵdid'](5, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](6, {
                        show: 0
                    }),
                    (n() (), o['ɵeld'](7, 0, null, null, 6, 'div', [
                        ['class',
                            'tooltip']
                    ], null, null, null, null, null)),
                    o['ɵdid'](8, 278528, null, 0, H.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](9, {
                        show: 0
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, vt)),
                    o['ɵdid'](11, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](12, 0, null, null, 1, 'p', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Al marcar una cuenta/producto como “no visible” en buzón, los documentos asociados no podrán consultarse desde el buzón de correspondencia.'
                    ])),
                    (n() (), o['ɵeld'](14, 0, null, null, 9, 'section', [
                        ['class',
                            'content-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](15, 0, null, null, 4, 'div', [
                        ['class',
                            'selector-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](16, 0, null, null, 1, 'label', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Selección del producto'
                    ])),
                    (n() (), o['ɵeld'](18, 0, null, null, 1, 'dropdown-select', [
                        ['class',
                            'dropdown']
                    ], null, [
                        [null,
                            'elementoSeleccionado']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'elementoSeleccionado' === e && (o = !1 !== n.component.seleccionar(t) && o),
                            o
                    }), Me.b, Me.a)),
                    o['ɵdid'](19, 49152, [
                        [1,
                            4],
                        [
                            'tipoSeccionMenu',
                            4
                        ]
                    ], 0, D.a, [
                    ], {
                        model: [
                            0,
                            'model'
                        ],
                        id: [
                            1,
                            'id'
                        ],
                        itemSeleccionado: [
                            2,
                            'itemSeleccionado'
                        ]
                    }, {
                        elementoSeleccionado: 'elementoSeleccionado'
                    }),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, wt)),
                    o['ɵdid'](21, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](22, 0, null, null, 1, 'alert', [
                    ], null, null, null, ht.c, ht.b)),
                    o['ɵdid'](23, 245760, null, 0, Ot.a, [
                        T.a
                    ], null, null)
                ], (function (n, e) {
                    var t = e.component,
                        o = n(e, 6, 0, t.tooltipAjustes);
                    n(e, 5, 0, 'ibercaja-icon-Info', o);
                    var l = n(e, 9, 0, t.tooltipAjustes);
                    n(e, 8, 0, 'tooltip', l),
                        n(e, 11, 0, t.responsive.esTablet || t.responsive.esMobile),
                        n(e, 19, 0, t.tipos, 'secciones-dropdown', t.tipoSeleccionado),
                        n(e, 21, 0, t.productosSeleccionado),
                        n(e, 23, 0)
                }), null)
            }
            function yt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'loading', [
                    ], null, null, null, Q.b, Q.a)),
                    o['ɵdid'](1, 114688, null, 0, nn.a, [
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            function It(n) {
                return o['ɵvid'](0, [
                    o['ɵqud'](671088640, 1, {
                        tipoSeccionMenu: 0
                    }),
                    (n() (), o['ɵeld'](1, 0, null, null, 20, 'dashboard-layout', [
                    ], null, [
                        ['window',
                            'resize'],
                        [
                            'window',
                            'scroll'
                        ]
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 3).onResize(t) && l),
                        'window:scroll' === e && (l = !1 !== o['ɵnov'](n, 3).onWindowScroll() && l),
                            l
                    }), rn.b, rn.a)),
                    o['ɵprd'](512, null, O.a, O.a, [
                    ]),
                    o['ɵdid'](3, 8634368, null, 0, sn.a, [
                        o.ChangeDetectorRef,
                        un.a,
                        O.a,
                        p.a,
                        dn.a,
                        pn.f,
                        a.a,
                        gn.a
                    ], null, null),
                    (n() (), o['ɵeld'](4, 0, null, 0, 8, 'div', [
                        ['top',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, _t)),
                    o['ɵdid'](6, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'navigation-back', [
                    ], null, [
                        ['window',
                            'resize']
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 8).onResize(t) && l),
                            l
                    }), fn.b, fn.a)),
                    o['ɵdid'](8, 376832, null, 0, Cn.a, [
                        mn.c,
                        p.a,
                        d.a
                    ], {
                        config: [
                            0,
                            'config'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](9, 0, null, null, 1, 'resumen-producto', [
                    ], null, [
                        [null,
                            'recargar']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'recargar' === e && (o = !1 !== n.component.cargarSumatorios() && o),
                            o
                    }), Pn.b, Pn.a)),
                    o['ɵdid'](10, 8503296, null, 0, Mn.a, [
                        p.a
                    ], {
                        items: [
                            0,
                            'items'
                        ]
                    }, {
                        recargar: 'recargar'
                    }),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'app-navigation-panel', [
                    ], null, [
                        [null,
                            'navegar'],
                        [
                            'window',
                            'resize'
                        ]
                    ], (function (n, e, t) {
                        var l = !0,
                            i = n.component;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 12).onResize(t) && l),
                        'navegar' === e && (l = !1 !== i.goToPanelNavegacion(t) && l),
                            l
                    }), hn.b, hn.a)),
                    o['ɵdid'](12, 8437760, null, 0, On.a, [
                        a.a,
                        d.a,
                        p.a
                    ], {
                        configuracionPanel: [
                            0,
                            'configuracionPanel'
                        ]
                    }, {
                        navegar: 'navegar'
                    }),
                    (n() (), o['ɵeld'](13, 0, null, 1, 5, 'div', [
                        ['main',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](14, 0, null, null, 4, 'div', [
                        ['class',
                            'ajuste-buzon-container']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, St)),
                    o['ɵdid'](16, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, yt)),
                    o['ɵdid'](18, 16384, null, 0, H.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵeld'](19, 0, null, 2, 2, 'div', [
                        ['sidebar',
                            '']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](20, 0, null, null, 1, 'app-dashboard-side-bar', [
                    ], null, null, null, bn.b, bn.a)),
                    o['ɵdid'](21, 245760, null, 0, _n.a, [
                        H.DatePipe,
                        vn.a,
                        xn.a,
                        O.a,
                        d.a,
                        a.a,
                        wn.a,
                        Sn.a,
                        yn.a,
                        In.a,
                        dn.a
                    ], null, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 3, 0),
                        n(e, 6, 0, t.utilsComponent.storage.isDemo),
                        n(e, 8, 0, t.configuracionBack),
                        n(e, 10, 0, t.itemsSumatorios),
                        n(e, 12, 0, t.navigationPanel),
                        n(e, 16, 0, !t.loading.active),
                        n(e, 18, 0, t.loading.active),
                        n(e, 21, 0)
                }), null)
            }
            function kt(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 1, 'app-ajustes-buzon', [
                    ], null, [
                        ['window',
                            'resize'],
                        [
                            'window',
                            'scroll'
                        ]
                    ], (function (n, e, t) {
                        var l = !0;
                        return 'window:resize' === e && (l = !1 !== o['ɵnov'](n, 1).onResize(t) && l),
                        'window:scroll' === e && (l = !1 !== o['ɵnov'](n, 1).onWindowScroll() && l),
                            l
                    }), It, bt)),
                    o['ɵdid'](1, 245760, null, 0, V, [
                        A,
                        O.a,
                        v.a,
                        d.a,
                        p.a,
                        R.a,
                        a.a
                    ], null, null)
                ], (function (n, e) {
                    n(e, 1, 0)
                }), null)
            }
            var zt = o['ɵccf']('app-ajustes-buzon', V, kt, {
                }, {
                }, [
                ]),
                Rt = t('y8gV');
            t.d(e, 'CorrespondenciaRoutingModuleNgFactory', (function () {
                return jt
            }));
            var jt = o['ɵcmf'](B, [
            ], (function (n) {
                return o['ɵmod']([o['ɵmpd'](512, o.ComponentFactoryResolver, o['ɵCodegenComponentFactoryResolver'], [
                    [8,
                        [
                            U.a,
                            Pe,
                            lt,
                            zt
                        ]],
                    [
                        3,
                        o.ComponentFactoryResolver
                    ],
                    o.NgModuleRef
                ]),
                    o['ɵmpd'](1073742336, Te.n, Te.n, [
                        [2,
                            Te.t],
                        [
                            2,
                            Te.m
                        ]
                    ]),
                    o['ɵmpd'](512, f.a, f.a, [
                        Rt.a,
                        Te.m,
                        a.a
                    ]),
                    o['ɵmpd'](1073742336, B, B, [
                        f.a
                    ]),
                    o['ɵmpd'](1024, Te.k, (function () {
                        return [[{
                            path: '',
                            component: F,
                            canActivate: [
                                f.a
                            ],
                            runGuardsAndResolvers: 'always',
                            pathMatch: 'full'
                        },
                            {
                                path: 'duplicado',
                                component: g,
                                outlet: 'modal'
                            },
                            {
                                path: 'ajustes-buzon',
                                component: V,
                                canActivate: [
                                    f.a
                                ]
                            }
                        ]]
                    }), [
                    ])])
            }))
        },
        vxsF: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return l
            }));
            var o = t('CcnG'),
                l = (t('3rka'), t('sE38'), t('SKFc'), function () {
                    function n(n, e, t, l) {
                        this._router = n,
                            this._navigationControlService = e,
                            this.utilsComponent = t,
                            this.responsive = l,
                            this.modalClose = new o.EventEmitter,
                            this.tieneNavegacion = !1
                    }
                    return n.prototype.ngOnInit = function () {
                        - 1 == this._router.url.indexOf('modal:agenda') && (this.tieneNavegacion = !0)
                    },
                        n.prototype.closeModal = function (n) {
                            this.utilsComponent.storage.isModalCondiciones || this.utilsComponent.storage.isModalGDPR || this.utilsComponent.storage.isCustomModalClose ? this.modalClose.next(n) : this._navigationControlService.closeOperativas()
                        },
                        n
                }())
        },
        ySnG: function (n, e, t) {
            'use strict';
            t.d(e, 'a', (function () {
                return o
            })),
                t.d(e, 'b', (function () {
                    return l
                }));
            var o = function (n) {
                    return n[n.activo = 0] = 'activo',
                        n[n.inactivo = 1] = 'inactivo',
                        n[n.completado = 2] = 'completado',
                        n[n.oculto = 3] = 'oculto',
                        n
                }({
                }),
                l = function (n) {
                    return n[n.correcto = 0] = 'correcto',
                        n[n.error = 1] = 'error',
                        n[n.pendiente = 2] = 'pendiente',
                        n
                }({
                })
        },
        zbbk: function (n, e, t) {
            'use strict';
            var o = t('CcnG'),
                l = t('Ip0R');
            t('vxsF'),
                t('ZYCi'),
                t('sE38'),
                t('3rka'),
                t('SKFc'),
                t.d(e, 'a', (function () {
                    return i
                })),
                t.d(e, 'b', (function () {
                    return r
                }));
            var i = o['ɵcrt']({
                encapsulation: 0,
                styles: [
                    ['.modal[_ngcontent-%COMP%]{position:fixed;display:block;background-color:rgba(51,57,62,.9);height:100%;width:100vw;top:0;z-index:5}.modal[_ngcontent-%COMP%]   .modal-wrapper[_ngcontent-%COMP%]{display:flex;position:relative;height:100%;justify-content:space-around;align-items:center}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{background-color:#fff;border-radius:2px;box-shadow:0 2px 4px 0 rgba(0,0,0,.1);min-width:10%;overflow:hidden;height:100%;width:100vw;max-height:none;padding:20px;display:flex;justify-content:space-between}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-left[_ngcontent-%COMP%]{width:65%;height:calc(100vh - 40px);overflow-y:auto;padding:78px 73px;background-color:#f4f7fd;position:relative}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-right[_ngcontent-%COMP%]{padding-top:38px;padding-left:41px;width:35%;overflow-y:auto;position:relative}.modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{color:#33393e;z-index:9}.modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{color:#33393e}.modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   div[_ngcontent-%COMP%], .modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]:hover   span[_ngcontent-%COMP%]{color:#0b7ad0}@media screen and (max-width:1279px){.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-left[_ngcontent-%COMP%]{padding:78px 27px}}@media screen and (max-width:1023px){.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]{padding:0;display:block;background-color:#f4f7fd;overflow:hidden}.modal[_ngcontent-%COMP%]   .modal-content[_ngcontent-%COMP%]   .modal-bottom[_ngcontent-%COMP%]{overflow-y:auto;height:calc(100% - 105px)}.modal[_ngcontent-%COMP%]   .modal-content.sinNav[_ngcontent-%COMP%]   .modal-bottom[_ngcontent-%COMP%]{height:calc(100% - 20px)}.modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]{top:0;right:0;color:#fff;z-index:3;cursor:pointer;padding:16px}.modal[_ngcontent-%COMP%]   .close-button[_ngcontent-%COMP%]   div[_ngcontent-%COMP%]{color:#fff;font-size:1rem;padding:5px;position:relative;z-index:2;display:block}}']
                ],
                data: {
                }
            });
            function a(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'div', [
                        ['class',
                            'modal-wrapper']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 3, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](2, 0, null, null, 1, 'span', [
                    ], null, null, null, null, null)),
                    (n() (), o['ɵted']( - 1, null, [
                        'Cerrar'
                    ])),
                    (n() (), o['ɵeld'](4, 0, null, null, 0, 'div', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 7, 'div', [
                        ['class',
                            'modal-content']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 4, 'div', [
                        ['class',
                            'modal-left']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](7, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-left-top']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 0),
                    (n() (), o['ɵeld'](9, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-left-bottom']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 1),
                    (n() (), o['ɵeld'](11, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-right']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 2)
                ], null, null)
            }
            function c(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 12, 'div', [
                        ['class',
                            'modal-wrapper']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](1, 0, null, null, 11, 'div', [
                        ['class',
                            'modal-content']
                    ], null, null, null, null, null)),
                    o['ɵdid'](2, 278528, null, 0, l.NgClass, [
                        o.IterableDiffers,
                        o.KeyValueDiffers,
                        o.ElementRef,
                        o.Renderer2
                    ], {
                        klass: [
                            0,
                            'klass'
                        ],
                        ngClass: [
                            1,
                            'ngClass'
                        ]
                    }, null),
                    o['ɵpod'](3, {
                        sinNav: 0
                    }),
                    (n() (), o['ɵeld'](4, 0, null, null, 1, 'button', [
                        ['class',
                            'close-button'],
                        [
                            'id',
                            'close-modal'
                        ]
                    ], null, [
                        [null,
                            'click']
                    ], (function (n, e, t) {
                        var o = !0;
                        return 'click' === e && (o = !1 !== n.component.closeModal(t) && o),
                            o
                    }), null, null)),
                    (n() (), o['ɵeld'](5, 0, null, null, 0, 'span', [
                        ['class',
                            'ibercaja-icon-Cerrar'],
                        [
                            'id',
                            'close-modal-icon'
                        ]
                    ], null, null, null, null, null)),
                    (n() (), o['ɵeld'](6, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-top']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 3),
                    (n() (), o['ɵeld'](8, 0, null, null, 1, 'div', [
                        ['class',
                            'modal-nav']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 4),
                    (n() (), o['ɵeld'](10, 0, null, null, 2, 'div', [
                        ['class',
                            'modal-bottom']
                    ], null, null, null, null, null)),
                    o['ɵncd'](null, 5),
                    o['ɵncd'](null, 6)
                ], (function (n, e) {
                    var t = n(e, 3, 0, !e.component.tieneNavegacion);
                    n(e, 2, 0, 'modal-content', t)
                }), null)
            }
            function r(n) {
                return o['ɵvid'](0, [
                    (n() (), o['ɵeld'](0, 0, null, null, 4, 'div', [
                        ['class',
                            'modal']
                    ], null, null, null, null, null)),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, a)),
                    o['ɵdid'](2, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null),
                    (n() (), o['ɵand'](16777216, null, null, 1, null, c)),
                    o['ɵdid'](4, 16384, null, 0, l.NgIf, [
                        o.ViewContainerRef,
                        o.TemplateRef
                    ], {
                        ngIf: [
                            0,
                            'ngIf'
                        ]
                    }, null)
                ], (function (n, e) {
                    var t = e.component;
                    n(e, 2, 0, !t.responsive.esTablet),
                        n(e, 4, 0, t.responsive.esTablet)
                }), null)
            }
        }
    }
]);
