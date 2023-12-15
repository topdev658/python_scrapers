'use strict';

myAppControllers.controller('informeController', ['$rootScope', '$scope', 'tableReport', 'informeFactory', 'dialogs', '$exceptionHandler', '$state', '$modal', '$window', '$filter', '$timeout',
    function($rootScope, $scope, tableReport, informeFactory, dialogs, $exceptionHandler, $state, $modal, $window, $filter, $timeout) {
        $scope.diarioMensual = "diario";
        $scope.esNuevaBusqueda=true;

        $scope.fechaactual = $filter('date')(new Date(), 'dd-MM-yyyy');
        $scope.comercioObligatorio = true;
        $scope.entidadObligatoria = true;
        $scope.terminalObligatorio = false;

        var InformesInput = function() {
            this.tipo = null,
                this.csb = null,
                this.page = 0,
                this.order = "fecha",
                this.dateIni = "",
                this.dateEnd = "",

                this.comercio = null,
                this.terminal = null,
                this.navegador = "",
                this.dispositivo = "",
                this.personalizacion = "",
                this.elementByPage = 10,
                this.direction = "ASC",

                this.reset = function() {
                    if ($rootScope.isUserInterno()) {
                        this.csb = null;
                        this.tipo = null;
                    } else {
                        this.csb = $rootScope.user.csb;
                        this.tipo = $rootScope.user.tipoEntidad;
                    }

                    this.page = 0;
                    this.order = "fecha";

                    this.dateIni = "";
                    this.dateEnd = "";
                    this.comercio = null;
                    this.terminal = null;
                    this.navegador = null,
                        this.dispositivo = null,
                        this.personalizacion = null,
                        this.elementByPage = 10;
                    this.direction = "ASC";
                },

                this.formatToServer = function() {
                    //Se modifica el formato de las fechas
                    var dateIni = moment(unescape(this.dateIni), 'DD/MM/YYYY');
                    var dateEnd = moment(unescape(this.dateEnd), 'DD/MM/YYYY');
                    this.dateIni = $filter('date')(new Date(dateIni), 'yyyy-MM-dd');
                    this.dateEnd = $filter('date')(new Date(dateEnd), 'yyyy-MM-dd');
                    if (this.csb != null && this.csb == '')
                        this.csb = null;
                    if (this.comercio != null && this.comercio == '')
                        this.comercio = null;
                    if (this.terminal != null && this.terminal == '')
                        this.terminal = null;
                    if (this.navegador != null && (this.navegador == '' || this.navegador == 'x'))
                        this.navegador = null;
                    if (this.dispositivo != null && (this.dispositivo == '' || this.dispositivo == 'x'))
                        this.dispositivo = null;
                    if (this.personalizacion != null && (this.personalizacion == '' || this.personalizacion == 'x'))
                        this.personalizacion = null;
                }
        };

        /*
	 * informe.th.tipoEntidad = Tipo entidad
informe.th.csb = Entidad
informe.th.fecha = Fecha
informe.th.comercio = NÃƒâ€šÃ‚Âº comercio
informe.th.terminal = Terminal
informe.th.numeroOperaciones = NÃƒâ€šÃ‚Âº Operaciones
informe.th.numeroOperacionesOk = NÃƒâ€šÃ‚Âº Operaciones OK
informe.th.numeroOperacionesError = NÃƒâ€šÃ‚Âº Operaciones KO
informe.th.importeTotal = Importe Total
informe.th.importeTotalOk = Importe OK
informe.th.importeTotalError = Importe KO
informe.th.numeroOperacionesKo9998 = NÃƒâ€šÃ‚Âº Oper. Sin Finalizar
informe.th.numeroOperacionesKo9999 = NÃƒâ€šÃ‚Âº Autenticaciones sin Finalizar
informe.th.numeroOperacionesEci7 = NÃƒâ€šÃ‚Âº Oper. Comer. No Seguro
informe.th.numeroOperacionesEci6 = NÃƒâ€šÃ‚Âº Oper. Comer. Seguro-Tit. No Seg
informe.th.numeroOperacionesEci5 = NÃƒâ€šÃ‚Âº Oper. Comer. Seguro-Tit. Seg
	 */

        var metaColumn = function(obj) {
            var result = new tableReport.metaColumn(obj);
            result.fn_i18n_header = function(value) { return $filter('translate')("informe.th." + this.nombre); };
            return result;
        };

        /* var columnasComercio = function() {
             this.columnas = [
                 new metaColumn({ nombre: "tipoEntidad", visible: false, align: "center" }),
                 new metaColumn({ nombre: "csb", visible: false, align: "center" }),
                 new metaColumn({ nombre: "comercio", visible: true, disabled: true, align: "center" }),
                 new metaColumn({ nombre: "terminal", visible: true, disabled: true, align: "center" }),
                 new metaColumn({ nombre: "fecha", visible: true, disabled: true, align: "center" }),
                 new metaColumn({ nombre: "numeroOperaciones", visible: true, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesOk", visible: true, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesError", visible: true, align: "center" }),
                 new metaColumn({ nombre: "importeTotal", visible: true, align: "center" }),
                 new metaColumn({ nombre: "importeTotalOk", visible: true, align: "center" }),
                 new metaColumn({ nombre: "importeTotalError", visible: true, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesKo9998", visible: false, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesKo9999", visible: false, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesEci7", visible: false, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesEci6", visible: false, align: "center" }),
                 new metaColumn({ nombre: "numeroOperacionesEci5", visible: false, align: "center" })
             ];
             this.name = "informeComercio";
         };*/

        $scope.columnasComercio = {
            columnas: [
                new metaColumn({ nombre: "tipoEntidad", visible: false, align: "center" }),
                new metaColumn({ nombre: "csb", visible: false, align: "center" }),
                new metaColumn({ nombre: "comercio", visible: true, disabled: true, align: "center" }),
                new metaColumn({ nombre: "terminal", visible: true, disabled: true, align: "center" }),
                new metaColumn({ nombre: "fecha", visible: true, disabled: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperaciones", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesOk", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesError", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotal", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotalOk", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotalError", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesKo9998", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesKo9999", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci7", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci6", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci5", visible: false, align: "center" })
            ],
            name: "informeComercio"
        };

        $scope.configVersionComercio = JSON.stringify($scope.columnasComercio).hashCode();
        $scope.columnasComercio.columnas = tableReport.restoreConf($scope.columnasComercio.name, $scope.configVersionComercio, $scope.columnasComercio.columnas);


        /*   var columnasEntidad = function() {
               this.columnas = [
                   new metaColumn({ nombre: "tipoEntidad", visible: false, align: "center" }),
                   new metaColumn({ nombre: "csb", visible: true, disabled: true, align: "center" }),
                   new metaColumn({ nombre: "fecha", visible: true, disabled: true, align: "center" }),
                   new metaColumn({ nombre: "numeroOperaciones", visible: true, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesOk", visible: true, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesError", visible: true, align: "center" }),
                   new metaColumn({ nombre: "importeTotal", visible: true, align: "center" }),
                   new metaColumn({ nombre: "importeTotalOk", visible: true, align: "center" }),
                   new metaColumn({ nombre: "importeTotalError", visible: true, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesKo9998", visible: false, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesKo9999", visible: false, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesEci7", visible: false, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesEci6", visible: false, align: "center" }),
                   new metaColumn({ nombre: "numeroOperacionesEci5", visible: false, align: "center" })
               ]
           };*/


        $scope.columnasEntidad = {
            columnas: [
                new metaColumn({ nombre: "tipoEntidad", visible: false, align: "center" }),
                new metaColumn({ nombre: "csb", visible: true, disabled: true, align: "center" }),
                new metaColumn({ nombre: "fecha", visible: true, disabled: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperaciones", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesOk", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesError", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotal", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotalOk", visible: true, align: "center" }),
                new metaColumn({ nombre: "importeTotalError", visible: true, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesKo9998", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesKo9999", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci7", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci6", visible: false, align: "center" }),
                new metaColumn({ nombre: "numeroOperacionesEci5", visible: false, align: "center" })
            ],
            name: "informeEntidad"
        };

        $scope.configVersionEntidad = JSON.stringify($scope.columnasEntidad).hashCode();
        $scope.columnasEntidad.columnas = tableReport.restoreConf($scope.columnasEntidad.name, $scope.configVersionEntidad, $scope.columnasEntidad.columnas);



        /* var columnasPersonalizacion = function() {
             this.columnas = [
                 new metaColumn({ nombre: "comercio", visible: true, align: "center" }),
                 new metaColumn({ nombre: "terminal", visible: true, align: "center" }),
                 new metaColumn({ nombre: "fecha", visible: true, align: "center" }),
                 new metaColumn({ nombre: "personalizacion", visible: true, align: "center" }),
                 new metaColumn({ nombre: "dispositivo", visible: true, align: "center" }),
                 new metaColumn({ nombre: "navegador", visible: true, align: "center" }),
                 new metaColumn({ nombre: "operacionesTotales", visible: true, align: "center" }),
                 new metaColumn({ nombre: "operaciones9998", visible: true, align: "center" }),
                 new metaColumn({ nombre: "operaciones9999", visible: true, align: "center" })
             ]
         };*/

        $scope.columnasPersonalizacion = {
            columnas: [
                new metaColumn({ nombre: "comercio", visible: true, align: "center" }),
                new metaColumn({ nombre: "terminal", visible: true, align: "center" }),
                new metaColumn({ nombre: "fecha", visible: true, align: "center" }),
                new metaColumn({ nombre: "personalizacion", visible: true, align: "center" }),
                new metaColumn({ nombre: "dispositivo", visible: true, align: "center" }),
                new metaColumn({ nombre: "navegador", visible: true, align: "center" }),
                new metaColumn({ nombre: "operacionesTotales", visible: true, align: "center" }),
                new metaColumn({ nombre: "operaciones9998", visible: true, align: "center" }),
                new metaColumn({ nombre: "operaciones9999", visible: true, align: "center" })
            ],
            name: "informePersonalizacion"

        }

        $scope.configVersionPersonalizacion = JSON.stringify($scope.columnasPersonalizacion).hashCode();
        $scope.columnasPersonalizacion.columnas = tableReport.restoreConf($scope.columnasPersonalizacion.name, $scope.configVersionPersonalizacion, $scope.columnasPersonalizacion.columnas);



        $scope.tiposEntidad = [
            { "value": 0, "label": "comercios.tipoEntidad.0" },
            { "value": 10, "label": "comercios.tipoEntidad.10" },
            { "value": 20, "label": "comercios.tipoEntidad.20" }
        ];

        $scope.listItemsByPage = [
            { "value": 10, "label": "10" },
            { "value": 20, "label": "20" },
            { "value": 50, "label": "50" }
        ];

        $scope.tiposDispositivo = [
            { "value": "0", "label": "dispositivo.tipo.0" },
            { "value": "1", "label": "dispositivo.tipo.1" },
            { "value": "2", "label": "dispositivo.tipo.2" },
            { "value": "3", "label": "dispositivo.tipo.3" },
            { "value": "4", "label": "dispositivo.tipo.4" },
            { "value": "5", "label": "dispositivo.tipo.5" }
        ];

        $scope.tiposNavegador = [
            { "value": "0", "label": "navegador.tipo.0" },
            { "value": "1", "label": "navegador.tipo.1" },
            { "value": "2", "label": "navegador.tipo.2" },
            { "value": "3", "label": "navegador.tipo.3" },
            { "value": "4", "label": "navegador.tipo.4" },
            { "value": "5", "label": "navegador.tipo.5" },
            { "value": "6", "label": "navegador.tipo.6" }
        ];
        $scope.tiposPersonalizacion = [
            { "value": "1", "label": "personalizacion.sis.1" },
            { "value": "2", "label": "personalizacion.sis.2" },
        ];

        $scope.informesInput = new InformesInput();

        $scope.informesInput.dispositivo = $scope.tiposDispositivo[0].value;

        $scope.informesInput.navegador = $scope.tiposNavegador[0].value;

        $scope.informesInput.personalizacion = $scope.tiposPersonalizacion[0].value;

        $scope.tipoEntidad={};
        $scope.tipoEntidad.tipo = "0";

        $scope.informesInputBusqueda = new InformesInput();

        $scope.tipoInforme = "comercio";
        $scope.tab="comercio";

        $scope.mes = "";

        $scope.dia = "";

        $scope.informeList = [];

        $scope.columnas = [];

        $scope.isLoading = false;

        $scope.itemsByPage = 10;

        $scope.parent = {
            dateIni: '',
            dateEnd: ''
        };

        //Datos para las grÃƒÆ’Ã‚Â¡ficas
        $scope.triggerGrafico = true;
        $scope.tipoGrafico = "";
        $scope.dataGrafico = [];
        $scope.datosCompletosGrafico = [];
        $scope.informeGrafico = [];
        $scope.hdata = "0";
        $scope.optionGrafico = {};
        $scope.formatoGrafico = {
            "x": "fecha",
            "y": "entero" // texto, entero, decimal (2 decimales), moneda
        };

        $scope.tooltipPersonalizacion=function (e) {
            var series = e.data;

            var rows =
                "<tr>" +
                "<td class='legend-color-guide'><div style='background-color: " + e.color + ";'></div></td>" +
                "<td class='key'>" + series.key + "</td>";


            if (series.value === null || isNaN(series.value) || series.value=="")
                rows=rows+"<td class='x-value'><b>"+$filter("translate")("sin.datos")+"</b></td>";
            else
                rows=rows+"<td class='x-value'><b>" + d3.format(",d")(Number(series.value)) + " " + $filter("translate")("DE").toLowerCase() + " " + series.total + " " + $filter("translate")("informe.operaciones").toLowerCase() +"</b></td>";


            "</tr>";

            var header =
                "<thead>" +
                "<tr>" +
                "<td class='key' colspan='3'><strong>" + series.label + "</strong></td>" +
                "</tr>" +
                "</thead>";

            return "<table>" +
                header +
                "<tbody>" +
                rows +
                "</tbody>" +
                "</table>";
        };
        //Setea el terminal con el select activado
        /* $scope.$watch("informesInput.comercio", function(comercio, oldValue) {
             if (angular.isDefined($rootScope.user.comercio_terminal[comercio])) {
                 $scope.informesInput.terminal = $rootScope.user.comercio_terminal[comercio][0]+"";
             }

         }, false);*/

        $scope.procesaGrafico=function(newValue) {
            if (newValue > 0 && newValue <= $scope.dataGrafico.length) {
                $scope.informeGrafico = $scope.dataGrafico[newValue - 1];

                if ($scope.tipoInforme == "personalizacion") {
                    //operaciones por navegador, por dispositivos y navegador y dispositivo
                    if (newValue == "4" || newValue == "5" || newValue=="8") {
                        if (newValue == "4")
                            $scope.dataGrafico = informeFactory.formatFromServerDataGraficosPersonalizacion($scope.datosCompletosGrafico, "D");
                        if (newValue == "5")
                            $scope.dataGrafico = informeFactory.formatFromServerDataGraficosPersonalizacion($scope.datosCompletosGrafico, "N");
                        if (newValue == "8"){
                            $scope.dataGrafico = informeFactory.formatFromServerDataGraficosPersonalizacion($scope.datosCompletosGrafico, "NULL");
                            $scope.formatoGrafico.x="texto";
                            $scope.formatoGrafico.y="entero";
                            $scope.formatoGrafico.y2="entero";
                            $scope.optionGrafico = {
                                chart: {
                                    stacked: true,
                                    showControls: false,
                                    reduceXTicks: false,
                                    margin: {
                                        left: 110,
                                        bottom: 210
                                    },
                                    yAxis: {
                                        axisLabel: $filter('translate')('informe.radio.operaciones.dispositivo.navegador'),
                                        axisLabelDistance: 20
                                    },
                                    xAxis: {

                                        rotateLabels: -85
                                    }

                                }
                            };
                        }else{
                            $scope.formatoGrafico.x=($scope.diarioMensual=="diario"?"fecha":"meses");
                            $scope.formatoGrafico.y="porcentajeDecimal";
                            $scope.formatoGrafico.y2="porcentajeDecimal";
                            $scope.optionGrafico = {
                                chart: {
                                    stacked: true,
                                    showControls: false,
                                    forceY: [0, 100],
                                    margin: {
                                        left: 110
                                    },
                                    yAxis: {
                                        axisLabel: $filter('translate')('informe.th.operacionesTotales.entrantes'),
                                        axisLabelDistance: 20
                                    }

                                }
                            };

                        }
                        $scope.tipoGrafico = 'Columnas';




                    } else
                    if (newValue == "6" || newValue == "7") {
                        $scope.tipoGrafico = 'Columnas';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fecha":"meses"),
                            "y": "porcentajeDecimal"

                        };
                        $scope.optionGrafico = {
                            chart: {
                                stacked: true,
                                showControls: false,
                                forceY: [0, 100],
                                margin: {
                                    left: 110
                                },
                                yAxis: {
                                    axisLabel: $filter('translate')('informe.th.operacionesTotales'),
                                    axisLabelDistance: 20
                                }

                            }
                        };



                    } else if (newValue == "3") {
                        $scope.tipoGrafico = 'LineasConFocus';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fecha":"meses"),
                            "y": "porcentajeEntero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                forceY: [0, 100],
                                yAxis: {
                                    axisLabel: $filter('translate')('informe.tasa.abandonos'),
                                }
                            }
                        };
                    } else {
                        $scope.tipoGrafico = 'BarrasHorizontales';
                        $scope.formatoGrafico = {
                            "x": "entero",
                            "y": "entero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                margin:{
                                    left: 200
                                },
                                showControls: false,
                                stacked: true,
                                forceY: [0, 100],
                                yAxis: {
                                    axisLabel: (newValue=="2")?
                                        $filter('translate')('informe.operaciones.nav'):
                                        $filter('translate')('informe.operaciones.dis'),
                                }
                            }
                        };

                        if($scope.tab=='personalizacion'){
                            $scope.optionGrafico.chart.tooltip={
                                contentGenerator: $scope.tooltipPersonalizacion
                            };
                        }
                    }
                } else {
                    /*if(newValue=="4"){
					$scope.tipoGrafico = 'MultiTabla';
					$scope.formatoGrafico={
						"x": "translate;dias.",
						"y": "moneda",
						"y2": "entero"
					};
					$scope.optionGrafico = {
						chart: {
							margin: {
								left: 110
							},
							yAxis1: {
	                            axisLabel: $filter('translate')('informe.th.importeTotalOk'),
	                            axisLabelDistance: 50
							},
							yAxis2: {
	                            axisLabel: $filter('translate')('informe.th.numeroOperacionesOk'),
	                            axisLabelDistance: 20
							}
						}
					};
				}
				else*/
                    if (newValue == "3") {
                        $scope.tipoGrafico = 'MultiTabla';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fechaFromSerie":"mesesFromSerie"),
                            "y": "entero",
                            "y2": "entero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                margin: {
                                    left: 110,
                                    bottom: 60
                                },
                                yAxis1: {
                                    axisLabel: $filter('translate')('informe.th.importeTotalOk'),
                                    axisLabelDistance: 50
                                },
                                yAxis2: {
                                    axisLabel: $filter('translate')('informe.th.numeroOperacionesOk'),
                                    axisLabelDistance: 20
                                }
                            }
                        };
                    } else if (newValue == "2") {
                        var tics=[];
                        if($scope.informeGrafico.length>0){
                            for(var i=0; i<$scope.informeGrafico[0]["values"].length; i++){
                                tics.push($scope.informeGrafico[0]["values"][i]["x"]);
                            }
                        }

                        $scope.tipoGrafico = 'LineasConFocus';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fecha":"meses"),
                            "y": "entero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                yAxis: {
                                    axisLabel: $filter('translate')('informe.operaciones'),
                                    axisLabelDistance: 20
                                },
                                xAxis: {
                                    tickValues: tics
                                },
                                margin:{
                                    bottom: 60
                                }
                            }
                        };
                    } else if (newValue == "4") {
                        $scope.tipoGrafico = 'MultiTabla';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fecha":"meses"),
                            "y": "entero",
                            "y2": "entero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                margin: {
                                    left: 110,
                                    bottom: 60
                                },
                                yAxis1: {
                                    axisLabel: $filter('translate')('informe.th.importeTotalOk'),
                                    axisLabelDistance: 50
                                },
                                yAxis2: {
                                    axisLabel: $filter('translate')('informe.th.numeroOperacionesOk'),
                                    axisLabelDistance: 20
                                }
                            }
                        };

                    } else {
                        var tics=[];
                        if($scope.informeGrafico.length>0){
                            for(var i=0; i<$scope.informeGrafico[0]["values"].length; i++){
                                tics.push($scope.informeGrafico[0]["values"][i]["x"]);
                            }
                        }

                        $scope.tipoGrafico = 'LineasConFocus';
                        $scope.formatoGrafico = {
                            "x": ($scope.diarioMensual=="diario"?"fecha":"meses"),
                            "y": "entero"
                        };
                        $scope.optionGrafico = {
                            chart: {
                                yAxis: {
                                    axisLabel: $filter('translate')('informe.importe'),
                                    axisLabelDistance: 20
                                },
                                xAxis: {
                                    tickValues: tics
                                },
                                margin:{
                                    bottom: 60
                                }
                            }
                        };
                    }
                }

                $scope.mostrarGrafico = true;
                $scope.triggerGrafico = !$scope.triggerGrafico;
            } else {
                $scope.informeGrafico = [];
                $scope.optionGrafico = [];
            }
        };

        $scope.$watch("hdata", $scope.procesaGrafico, true);

        $scope.$watch("parent.dateIni", function(newValue) {
            $scope.informesInput.dateIni = newValue;
        }, true);

        $scope.$watch("parent.dateEnd", function(newValue) {
            $scope.informesInput.dateEnd = newValue;
        }, true);


        $scope.$watch("informesInput.terminal", function(newValue) {
            if (!angular.isUndefined(newValue) && newValue != null && newValue != '') {
                $scope.comercioObligatorio = true;
            } else {
                if ($rootScope.isUserInterno() || $rootScope.isUserEntidad()) {
                    $scope.comercioObligatorio = false;
                } else {
                    $scope.comercioObligatorio = true;
                }
            }
        }, true);



        $scope.$watch("selectEntidad",function(newValue){
            $scope.informesInput.csb=newValue.entidad;
            $scope.tipoEntidad.tipo=newValue.tipoEntidad;


        },true);

        $scope.$watch("tipoEntidad.tipo", function(newValue) {

            if (angular.isUndefined(newValue) || newValue == null || newValue == '')
                $scope.informesInput.tipo = null;
            else
                $scope.informesInput.tipo = parseInt(newValue);

            if (!angular.isUndefined(newValue) && newValue != null && newValue != '') {
                $scope.entidadObligatoria = true;
            } else {
                if ($scope.tipoInforme == 'entidad') {
                    if ($rootScope.isUserInterno()) {
                        $scope.entidadObligatoria = false;
                    } else {
                        $scope.entidadObligatoria = true;
                    }
                } else {
                    if ($rootScope.isUserInterno()) {
                        $scope.entidadObligatoria = false;
                    }
                    if ($rootScope.isUserComercio()) {
                        $scope.entidadObligatoria = false;
                    }
                }
            }
        }, true);


        $scope.$watchGroup(["tipoInforme", "diarioMensual"], function(newValues, oldValues) {
            $scope.informeList.content = undefined;
            //Datos para las grÃƒÆ’Ã‚Â¡ficas y exportacion
            $scope.informeGrafico = [];
            //$scope.limpiarGrafico();
            $scope.mostrarGrafico = false
        }, true);

        $scope.$watch("tipoInforme", function(newValue, oldValue) {
            if ($scope.tipoInforme == 'comercio') {
                //$scope.columnas = new $scope.columnasComercio();
                $scope.columnas.columnas = tableReport.restoreConf($scope.columnasComercio.name, $scope.configVersionComercio, $scope.columnasComercio.columnas);
                $scope.entidadObligatoria = true;

                if ($rootScope.isUserInterno()) {
                    $scope.entidadObligatoria = false;
                }
                if ($rootScope.isUserInterno() || $rootScope.isUserEntidad()) {
                    $scope.comercioObligatorio = false;
                } else {
                    $scope.comercioObligatorio = true;
                }
                $scope.terminalObligatorio = false;
            }
            if ($scope.tipoInforme == 'entidad') {
                //$scope.columnas = new columnasEntidad();
                $scope.columnas.columnas = tableReport.restoreConf($scope.columnasEntidad.name, $scope.configVersionEntidad, $scope.columnasEntidad.columnas);
                if ($rootScope.isUserInterno()) {
                    $scope.entidadObligatoria = false;
                } else {
                    $scope.entidadObligatoria = true;
                }
                $scope.terminalObligatorio = false;
            }
            if ($scope.tipoInforme == 'personalizacion') {
                //$scope.columnas = new columnasPersonalizacion();
                $scope.columnas.columnas = tableReport.restoreConf($scope.columnasPersonalizacion.name, $scope.configVersionPersonalizacion, $scope.columnasPersonalizacion.columnas);
                $scope.entidadObligatoria = false;
                $scope.comercioObligatorio = true;
                $scope.terminalObligatorio = true;
            }
        });

        $scope.$watch("diarioMensual", function(newValue, oldValue) {
            if (newValue == "diario") {
                $scope.parent.dateIni = $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000 * 15)), 'dd-MM-yyyy');
                $scope.parent.dateEnd = $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000)), 'dd-MM-yyyy');

                angular.element("#fechaIniDiario").datepicker('clearDates');
                angular.element("#fechaFinDiario").datepicker('clearDates');

                angular.element("#fechaIniDiario").datepicker('update', $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000 * 15)), 'dd-MM-yyyy'));
                angular.element("#fechaFinDiario").datepicker('update', $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000)), 'dd-MM-yyyy'));
            } else {
                $scope.parent.dateIni = "";
                $scope.parent.dateEnd = "";

                angular.element("#fechaIniMensual").datepicker('clearDates');
                angular.element("#fechaFinMensual").datepicker('clearDates');

                angular.element("#fechaIniMensual").datepicker('update', "");
                angular.element("#fechaFinMensual").datepicker('update', "");
            }
        }, true);

        //Cambiar el numero de filas por pÃƒÆ’Ã‚Â¡gina
        $scope.$watch("itemsByPage", function(newValue, oldValue) {
            $scope.informeListClear();
        });

        $scope.initInforme = function() {

            $scope.informesInput = new InformesInput();
            $scope.informesInput.reset();

            $scope.comercioObligatorio = true;
            $scope.entidadObligatoria = true;
            $scope.tipoInforme = "comercio";

            $scope.diarioMensual = "diario";

            $scope.parent.dateIni = $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000 * 15)), 'dd-MM-yyyy');
            $scope.parent.dateEnd = $filter('date')(new Date(new Date() - (24 * 60 * 60 * 1000)), 'dd-MM-yyyy');

            if ($rootScope.isUserInterno() || $rootScope.isUserEntidad()) {
                $scope.comercioObligatorio = false;
            }

            $scope.columnas.columnas = tableReport.restoreConf($scope.columnasComercio.name, $scope.configVersionComercio, $scope.columnasComercio.columnas);

            $scope.informesInputBusqueda = null;

            $scope.itemsByPage = 10;

            //$scope.limpiarGrafico();
            $scope.mostrarGrafico = false;


            if ($rootScope.isUserMultiComercio() || $rootScope.isUserComercio()) {
                $scope.informesInput.comercio = $rootScope.user.comercios[0];

            }

            /*if ($rootScope.isUserMultiComercio() || $rootScope.isUserComercio() || $rootScope.isUserTerminal())
                $scope.informesInput.terminal = $rootScope.user.comercio_terminal[$rootScope.user.comercios[0]][0];*/
            $scope.informesInput.terminal=undefined;
            if($rootScope.isUserEntidad()){
                $scope.selectEntidad=$rootScope.user.entidades[0];
                $scope.informesInput.tipo=$rootScope.user.entidades[0].tipoEntidad;
            } else if ($rootScope.isUserComercio()) {
                $scope.informesInput.csb=$rootScope.user.csb;
                $scope.informesInput.tipo=$rootScope.user.tipoEntidad;

                $scope.informesInput.comercio = $rootScope.user.comercios[0];
            }else if($rootScope.isUserTerminal()){
                $scope.informesInput.csb=$rootScope.user.csb;
                $scope.informesInput.tipo=$rootScope.user.tipoEntidad;
                for(var i in $rootScope.user.comercio_terminal){
                    $scope.informesInput.comercio = i;
                    if( $rootScope.user.comercio_terminal[i].length>0)
                        $scope.informesInput.terminal = $rootScope.user.comercio_terminal[i][0];
                    else
                        $scope.informesInput.terminal = undefined;
                    break;
                }



            }
            if(!angular.isUndefined($scope.informesInput.terminal)){
                $scope.informesInput.dateIni = $scope.parent.dateIni;
                $scope.informesInput.dateEnd = $scope.parent.dateEnd;
                $scope.submitFiltro();
            }
        };

        $scope.inicializarNumber = function(inicial, option) {
            if (inicial != null && !angular.isUndefined(inicial))
                return inicial;
            if (option.length > 0)
                return option[0].value;
        };

        $scope.submitFiltro = function() {
            if ($rootScope.triggerValidation($scope.formInforme)) {
                $scope.esNuevaBusqueda=true;
                $scope.informesInputBusqueda = angular.copy($scope.informesInput);
                $scope.informesInputBusqueda.formatToServer();

                $scope.informeListClear();
                //$scope.limpiarGrafico();
            }
        };

        $scope.informeListAsignData = function(tableState) {

            var totalPagesDefault = 0;
            var pagesDefault = 0;

            var page;
            var pageSize;

            if (angular.isUndefined($scope.informeList) || angular.isUndefined($scope.informeList.content)) {
                page = pagesDefault;
                pageSize = $scope.itemsByPage;

                tableState.pagination.start = pagesDefault;
                tableState.pagination.number = $scope.itemsByPage;
                tableState.pagination.itemsByPage = $scope.itemsByPage;
            } else {
                page = tableState.pagination.start / tableState.pagination.number;

                pageSize = tableState.pagination.itemsByPage || $scope.itemsByPage;
            }

            if ($scope.informesInputBusqueda != null) {
                $scope.isLoading = true;
                $scope.informesInputBusqueda.page = page;
                $scope.informesInputBusqueda.elementByPage = pageSize;

                //deja el listado recargando
                $scope.informeList.content = undefined;

                //seleciona el tipo de busqueda en funciÃƒÆ’Ã‚Â³n del filtro
                var promise = null;

                if ($scope.tipoInforme == 'comercio') {
                    if ($scope.informesInput.csb == null && $scope.informesInput.comercio == null) {
                        dialogs.error("ERROR.FIND", "ERROR.EMPTY_FIELDS");
                    } else {
                        if ($scope.diarioMensual == 'diario')
                            promise = informeFactory.informeDiarioComercio($scope.informesInputBusqueda);
                        else
                            promise = informeFactory.informeMensualComercio($scope.informesInputBusqueda);
                    }
                }

                if ($scope.tipoInforme == 'entidad') {
                    if ($scope.diarioMensual == 'diario')
                        promise = informeFactory.informeDiarioEntidad($scope.informesInputBusqueda);
                    else
                        promise = informeFactory.informeMensualEntidad($scope.informesInputBusqueda);
                }

                if ($scope.tipoInforme == 'personalizacion') {
                    $scope.informesInputBusqueda.tab=$scope.tab;
                    if ($scope.diarioMensual == 'diario')
                        promise = informeFactory.informeDiarioPersonalizacion($scope.informesInputBusqueda);
                    else
                        promise = informeFactory.informeMensualPersonalizacion($scope.informesInputBusqueda);
                }

                if (promise != null) {
                    promise.success(function(data) {
                        $scope.informeList = data;

                        tableState.pagination.itemsByPage = $scope.itemsByPage;
                        tableState.pagination.numberOfPages = $scope.informeList.totalPages;
                        //tableState.pagination.page = $scope.operacionesList.page;

                        if ($scope.tipoInforme != 'personalizacion') {
                            for (var i in $scope.informeList.content) {
                                $scope.informeList.content[i] = informeFactory.formatFromServerLineaInforme($scope.informeList.content[i]);
                            }
                        } else {
                            for (var i in $scope.informeList.content) {
                                $scope.informeList.content[i] = informeFactory.formatFromServerLineaInformePersonalizacion($scope.informeList.content[i]);
                            }
                        }

                        //Se carga el grafico

                        if($scope.esNuevaBusqueda){
                            $scope.mostrarGrafico = false;
                            $scope.cargarGrafico();
                        }
                        $scope.esNuevaBusqueda=false;

                        $scope.isLoading = false;
                    })
                        .error(function(data) {
                            $scope.isLoading = false;
                            $exceptionHandler(data, 'ERROR.FIND');
                        });
                }
            }

        };

        //limpiar el listado
        $scope.informeListClear = function() {
            $scope.informeList.content = undefined;
            //Datos para las grÃƒÆ’Ã‚Â¡ficas y exportacion
            $scope.informeGrafico = [];


            if ($scope.tableStateInformeList) {
                $scope.informeListReload();
            }
        };

        //forzar recarga del listado en la pagina actual
        $scope.informeListReload = function() {
            if ($scope.tableStateInformeList) {
                $scope.informeListAsignData($scope.tableStateInformeList);
            }
        };

        $scope.tipoColumna = function(nombre, tipo) {
            if (nombre.indexOf('fecha') >= 0 || nombre.indexOf('importe') >= 0 || nombre.indexOf('Operaciones') >= 0) {
                return "formated" == tipo;
            } else if (nombre.indexOf('tipoEntidad') >= 0) {
                return "tentidad" == tipo;
            } else if (nombre.indexOf('dispositivo') >= 0) {
                return "dispositivo" == tipo;
            } else if (nombre.indexOf('navegador') >= 0) {
                return "navegador" == tipo;
            } else
                return "normal" == tipo;
        };

        //ordenar columnas
        $scope.ordenar = function(order) {
            if ($scope.informesInputBusqueda.order == order) {
                if ($scope.informesInputBusqueda.direction == 'ASC')
                    $scope.informesInputBusqueda.direction = 'DESC';
                else
                    $scope.informesInputBusqueda.direction = 'ASC';
            } else {
                $scope.informesInputBusqueda.order = order;
                $scope.informesInputBusqueda.direction = 'ASC';
            }

            $scope.informeListClear();
        };

        //lanzar pop-up seleccionar th
        $scope.lanzarPopupSelectTh = function() {
            $modal.open({
                controller: 'informeControllerSelectTh',
                templateUrl: 'static/partials/informe/informe-select-th.html',
                scope: $scope
            });
        };

        //Limpiar grafico
        $scope.limpiarGrafico = function() {
            $scope.informeGrafico = [];
            $scope.hdata = "0";
        };



        $scope.exportar = function(nuevoExportar) {
            $rootScope.compruebaTimeSesion();

            if ($rootScope.triggerValidation($rootScope.getObjectOutScope("formInforme"))) {
                //Creamos fecha y hora actual para concatenar al nombre fichero
                var date = $filter('date')(new Date(), 'yyyyMMddTHHmmss');

                var objetoExportar = $scope.informesInputBusqueda;
                var totalElementosExportar = $scope.informeList.totalElements;
                var tipoObjetoExportar = $scope.tipoInforme;
                var tipoAgrupacionExportar = $scope.diarioMensual; //solo para informes
                var cabecerasExportar = $rootScope.recuperaCabecerasVisiblesNuevo($scope.columnas.columnas);
                var nombreFicheroExportar = "InformesExportados_" + date;

                $rootScope.donwloadCSV(objetoExportar, totalElementosExportar, tipoObjetoExportar, tipoAgrupacionExportar, cabecerasExportar, nombreFicheroExportar);
            } else {
                dialogs.error('ERROR.DESCARGA', 'campos.incorrectos');
                $window.scrollTo(0, 0);
            }
        };

        var buildFiltroBusquedaDescarga = function(informesInput) {

            $rootScope.encodeParameters(arguments);

            //var input= new InformesInput();
            /*
             *
            this.tipo = null,
            this.csb = null,
            this.page = 0,
            this.order = "fecha",
            this.dateIni = "",
            this.dateEnd = "",

            this.comercio = null,
            this.terminal = null,
            this.elementByPage = 10,
            this.direction = "ASC",
             */

            //input.tipo=inf.tipo;
            //input.dateIni=inf.dateIni;

            informesInput.tab=$scope.tab;

            return informesInput;
        };





        //Cargar el grafico
        $scope.cargarGrafico = function() {

            if ($scope.tipoInforme == 'comercio' && (
                angular.isUndefined($scope.informesInput.comercio) ||
                angular.isUndefined($scope.informesInput.csb) ||
                angular.isUndefined($scope.informesInput.tipo) ||
                $scope.informesInput.comercio == null ||
                $scope.informesInput.csb == null ||
                $scope.informesInput.tipo == null ||
                $scope.informesInput.csb == '' ||
                $scope.informesInput.comercio == '')) {
                //dialogs.error('informes.grafico.error.comercio');
            } else if ($scope.tipoInforme == 'entidad' && (
                angular.isUndefined($scope.informesInput.csb) ||
                angular.isUndefined($scope.informesInput.tipo) ||
                $scope.informesInput.csb == null ||
                $scope.informesInput.tipo == null ||
                $scope.informesInput.csb == '')) {
                //dialogs.error('informes.grafico.error.entidad');
            } else if ($scope.tipoInforme == 'personalizacion' && (
                angular.isUndefined($scope.informesInput.comercio) ||
                angular.isUndefined($scope.informesInput.terminal) ||
                $scope.informesInput.comercio == null ||
                $scope.informesInput.terminal == null ||
                $scope.informesInput.comercio == '' ||
                $scope.informesInput.terminal == '')) {
                //dialogs.error('informes.grafico.error.personalizacion');
            } else {
                if (!angular.isUndefined($scope.informeList.content) &&
                    $scope.informeList.content != null &&
                    $scope.informeList.content.length > 0) {

                    var promise = null; //para resultado de las llamadas
                    if ($scope.tipoInforme == 'comercio') {
                        if ($scope.diarioMensual == 'diario')
                            promise = informeFactory.informeDiarioComercioGrafico($scope.informesInputBusqueda);
                        else
                            promise = informeFactory.informeMensualComercioGrafico($scope.informesInputBusqueda);
                    }

                    if ($scope.tipoInforme == 'entidad') {
                        if ($scope.diarioMensual == 'diario')
                            promise = informeFactory.informeDiarioEntidadGrafico($scope.informesInputBusqueda);
                        else
                            promise = informeFactory.informeMensualEntidadGrafico($scope.informesInputBusqueda);
                    }

                    if ($scope.tipoInforme == 'personalizacion') {
                        $scope.informesInputBusqueda.tab=$scope.tab;
                        if ($scope.diarioMensual == 'diario')
                            promise = informeFactory.informeDiarioPersonalizacionGrafico($scope.informesInputBusqueda);
                        else
                            promise = informeFactory.informeMensualPersonalizacionGrafico($scope.informesInputBusqueda);
                    }

                    if (promise != null) {
                        promise.success(function(data) {
                            $rootScope.isLoading = true;

                            $timeout(function() {
                                $rootScope.isLoading = false;

                                if ($scope.tipoInforme == "personalizacion") {
                                    $scope.datosCompletosGrafico = informeFactory.rellenaInformePersonalizacion(data, $scope.informesInputBusqueda.dateIni, $scope.informesInputBusqueda.dateEnd, $scope.diarioMensual == 'diario');
                                    $scope.dataGrafico = informeFactory.formatFromServerDataGraficosPersonalizacion($scope.datosCompletosGrafico, "D");
                                    if($scope.tab=="dispositivoNavegador")
                                        $scope.hdata = "4";
                                    else
                                        $scope.hdata = "1";
                                } else {
                                    $scope.datosCompletosGrafico = informeFactory.rellenaInformeComercioEntidad(data, $scope.informesInputBusqueda.dateIni, $scope.informesInputBusqueda.dateEnd, $scope.diarioMensual == 'diario');
                                    $scope.dataGrafico = informeFactory.formatFromServerDataGraficosEntidadComercio($scope.datosCompletosGrafico, $scope.columnas);
                                    $scope.hdata = "2";
                                }
                                $scope.procesaGrafico($scope.hdata);

                                $timeout(function() {
                                    $scope.mostrarGrafico = true;
                                }, 500);
                            }, 1500);
                        })
                            .error(function(data) {
                                $scope.limpiarGrafico();
                                $scope.mostrarGrafico = false;
                                $exceptionHandler(data, 'ERROR.FIND');
                            });
                    }
                }
            }
        };

        //contar las columnas seleccionadas
        $scope.countActive = function() {
            var count = 0;
            angular.forEach($scope.columnas.columnas, function(value, key) {
                if (value.visible)
                    count = count + 1;
            });

            return count;
        };

    }


]).controller('informeControllerSelectTh', ['$scope', 'tableReport', 'dialogs', 'informeFactory', '$modalInstance', '$exceptionHandler', '$timeout',
    function($scope, tableReport, dialogs, informeFactory, $modalInstance, $exceptionHandler, $timeout) {
        $scope.close = function() {
            $modalInstance.close();
        };

        $scope.thClick = function(th) {
            if (!th.disabled) {
                th.visible = !th.visible;


                //Se guarda en almacenamiento local la configuraciÃƒÆ’Ã‚Â³n
                tableReport.saveConf($scope.columnasComercio.name, $scope.configVersionComercio, $scope.columnasComercio.columnas);
                tableReport.saveConf($scope.columnasEntidad.name, $scope.configVersionEntidad, $scope.columnasEntidad.columnas);
                tableReport.saveConf($scope.columnasPersonalizacion.name, $scope.configVersionPersonalizacion, $scope.columnasPersonalizacion.columnas);

                if ($scope.tipoInforme == "personalizacion") {
                    //$scope.datosCompletosGrafico = informeFactory.rellenaInformePersonalizacion(data, $scope.informesInputBusqueda.dateIni, $scope.informesInputBusqueda.dateEnd, $scope.diarioMensual == 'diario');
                    $scope.$parent.dataGrafico = informeFactory.formatFromServerDataGraficosPersonalizacion($scope.$parent.datosCompletosGrafico, "D");
                } else {
                    //$scope.datosCompletosGrafico = informeFactory.rellenaInformeComercioEntidad(data, $scope.informesInputBusqueda.dateIni, $scope.informesInputBusqueda.dateEnd, $scope.diarioMensual == 'diario');
                    $scope.$parent.dataGrafico = informeFactory.formatFromServerDataGraficosEntidadComercio($scope.$parent.datosCompletosGrafico, $scope.columnas);
                }

                $scope.$parent.mostrarGrafico = true;
                //Cambiar el valor a esta varable hace que repinte grafico
                $scope.$parent.triggerGrafico = !$scope.$parent.triggerGrafico;
                $scope.$parent.aux = $scope.$parent.hdata;
                $scope.$parent.hdata = null;
                $timeout(function() {
                    $scope.$parent.hdata = $scope.$parent.aux;
                }, 200);



                //$scope.dataGrafico = informeFactory.formatFromServerDataGraficosEntidadComercio($scope.datosCompletosGrafico, $scope.columnas);
            }

        };
    }
]);
