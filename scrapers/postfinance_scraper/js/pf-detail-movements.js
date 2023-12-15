/* Copyright 2012 - 2019 by PostFinance Ltd - All rights reserved */
!function () {
    'use strict';
    define('pf-detail-efmovements-service', function (require) {
        function EfmovementsService() {
            DetailPageAbstractService.call(this);
            this.getTransactions = function getTransactions(params) {
                var url = pfWidgetFunctions.getActionUrlForDetailPage(this.name, actionKeys.GET_POSTINGS, params);
                this.restConfig.showSpinner = true;
                this.restConfig.showLoader = false;
                return restngDetailpages.postFormData2Json(this.restConfig, url.url, url.params)
            };
            this.exportToCsv = function exportToCsv(form) {
                var urlObj = pfWidgetFunctions.getActionUrlForDetailPage(this.name, actionKeys.CSV);
                form.action = urlObj.url;
                form.submit()
            }
        }
        var _ = require('lodash'),
            DetailPageAbstractService = require('pf-shared-modules-detail_page_abstract_service'),
            restngDetailpages = require('pf-shared-modules-rest_ng_detailpages'),
            pfWidgetFunctions = require('pf-widget-functions'),
            actionKeys = {
                GET_POSTINGS: 'SearchMovements',
                MOVEMENT_DETAIL: 'MovementDetail',
                OTHER_DETAIL: 'MovementOtherDetail',
                DD_DETAIL: 'DDDetail',
                CSV: 'ExportCSV'
            };
        EfmovementsService.prototype = _.create(DetailPageAbstractService.prototype);
        EfmovementsService.constructor = DetailPageAbstractService;
        return EfmovementsService
    })
}();
!function () {
    'use strict';
    var directives = [
    ];
    define('pf-detail-efmovements', function (require) {
        function init(module) {
            if (!helper.isInitialized()) {
                module._stateProvider.state(states.OVERVIEW, {
                    controller: OverviewController.controller,
                    controllerAs: 'overview',
                    templateUrl: OverviewController.templateUrl,
                    resolve: {
                        shared: function () {
                            return shared
                        },
                        deps: function () {
                            return module.registerDependencies({
                                directives: OverviewController.directives
                            })
                        }
                    }
                });
                helper.setInitialized(true)
            }
            return module.registerDependencies({
                directives: directives
            }).then(function success() {
                module.controller(this.name, this.ctrl)
            }.bind(this))
        }
        var _ = require('lodash'),
            DetailPageHelper = require('pf-shared-modules-detail_page_helper'),
            OverviewController = require('pf-detail-efmovements-overview'),
            EfmovementsService = require('pf-detail-efmovements-service'),
            detailPageName = 'efmovements',
            helper = new DetailPageHelper(detailPageName),
            efmovementsService = new EfmovementsService,
            states = {
                OVERVIEW: helper.createModuleName('overview')
            },
            shared = {
                helper: helper,
                data: {
                }
            },
            controller = function controller($scope, $state) {
                helper.init({
                    scope: $scope,
                    state: $state,
                    service: efmovementsService
                });
                var readyFunction = function readyFunction(urlObj) {
                    shared.data.productUniqueKey = _.get(urlObj, 'params.productUniqueKey');
                    helper.goToState(states.OVERVIEW)
                };
                helper.signalReady(readyFunction)
            };
        controller.$inject = [
            '$scope',
            '$state'
        ];
        return {
            name: 'EfmovementsController',
            detailPageName: detailPageName,
            ctrl: controller,
            init: init,
            template: '/static/fipo/detailpages/efmovements/efmovements.html'
        }
    })
}();
!function () {
    'use strict';
    var directives = [
        'directive-account_label',
        'directive-csv_export_button',
        'directive-currency_input',
        'directive-form-input_errors',
        'directive-form-toggle_buttons',
        'directive-form_validation-lower_bigger',
        'directive-form_validation-period_validation',
        'directive-table-table_filter',
        'directive-tooltips',
        'directive-widget-amount_input',
        'directive-widget-content_pane_collapsible',
        'directive-widget-datepicker',
        'directive-widget-dropdown',
        'directive-widget-toggle'
    ];
    define('pf-detail-efmovements-overview', function (require) {
        var _ = require('lodash'),
            angular = require('angular'),
            moment = require('moment'),
            numbers = require('pf-shared-modules-numbers'),
            wcmsEnumGenerator = require('pf-shared-modules-wcms_enum_generator'),
            dropdowns = require('pf-shared-modules-dropdowns'),
            userData = require('pf-sessiondata-userdata'),
            productService = require('pf-shared-modules-productservice'),
            util = require('pf-shared-modules-util'),
            platform = require('pf-shared-modules-platform'),
            focus = require('pf-shared-modules-focus'),
            formatter = require('pf-shared-modules-formatter'),
            pfWidgetFunctions = require('pf-widget-functions'),
            movements = require('pf-shared-modules-movements'),
            historyService = require('pf-shared-modules-historyservice'),
            currencies = require('pf-shared-modules-currencies'),
            controller = function controller($scope, $timeout, shared) {
                function applyForwardId(result) {
                    vm.data.tempId = result.forwardId;
                    if (vm.data.tempId) vm.data.total = null;
                    else vm.data.total = getTotalCreditDebit()
                }
                function isDefaultTransactionType() {
                    return vm.data.config.transactionType === pf.globals.detailpages.efmovements.transactionType.ALL
                }
                function getAvailableMovementMonths() {
                    for (var selectionList = [
                    ], i = 0; i <= pf.globals.detailpages.efmovements.NUM_MONTHS; i++) {
                        var date = moment().subtract(i, 'month');
                        selectionList.push({
                            name: _.get(monthsEnum[date.month() + 1], 'text') + ' ' + date.year(),
                            value: date.format('YYYY-MM')
                        })
                    }
                    return selectionList
                }
                function updateBalanceColumnFlag() {
                    vm.data.showBalanceColumn = showBalanceColumn()
                }
                function showBalanceColumn() {
                    var rangeManualOrMonth = 0 === vm.data.search.config.rangeSelect || 1 === vm.data.search.config.rangeSelect,
                        noAmountSpecified = !(vm.data.search.config.amountFrom || vm.data.search.config.amountTo);
                    return rangeManualOrMonth && noAmountSpecified && isDefaultTransactionType()
                }
                function prepareExportSearchOptionsData() {
                    var data = [
                    ];
                    if (vm.data.config.transactionDateFrom) data[data.length] = formatSearchConfig(translate('DueDateFrom', $scope), vm.data.config.transactionDateFrom);
                    if (vm.data.config.transactionDateTo) data[data.length] = formatSearchConfig(translate('DueDateTo', $scope), vm.data.config.transactionDateTo);
                    if (vm.data.config.amountFrom) data[data.length] = formatSearchConfig(translate('AmountFromLabel', $scope), numbers.filterAmount(vm.data.config.amountFrom, numbers.indicator.prefixOnlyMinus));
                    if (vm.data.config.amountTo) data[data.length] = formatSearchConfig(translate('AmountToLabel', $scope), numbers.filterAmount(vm.data.config.amountTo, numbers.indicator.prefixOnlyMinus));
                    if (isRangeTypeCurrentDay()) data[data.length] = formatSearchConfig(translate('ValueDate', $scope), formatter.isoDateToLocalized(vm.data.search.rangeToday));
                    else data[data.length] = formatSearchConfig(translate('TransactionType', $scope), _.get(vm.data.search.transactionTypesObject[vm.data.config.transactionType], 'text'));
                    data[data.length] = formatSearchConfig(translate('Account', $scope), vm.data.config.account.iban);
                    data[data.length] = formatSearchConfig(translate('Currency', $scope), currencies.getLiteral(vm.data.config.account.currency));
                    if (vm.data.config.showDetails) data[data.length] = formatSearchConfig(translate('TransactionDetails', $scope), translate('Yes', $scope));
                    return data
                }
                function formatSearchConfig(title, value) {
                    return [title + ':',
                        value]
                }
                function valueOrEmptyString(value) {
                    return value || ''
                }
                function formattedValueOrEmptyString(value, negate) {
                    if (_.isNil(value)) return '';
                    else return (negate ? - value : value).toFixed(2)
                }
                function prepareExportTableData() {
                    var data = [
                        ],
                        showBalance = showBalanceColumn(),
                        headers = [
                            translate('TransactionDate', $scope),
                            translate('AvisText', $scope),
                            translate('GutschriftIn', $scope, vm.data.search.criteria.account),
                            translate('LastschriftIn', $scope, vm.data.search.criteria.account),
                            translate('Valuta', $scope)
                        ];
                    if (showBalance) headers.push(translate('BalanceIn', $scope, vm.data.search.criteria.account));
                    data[0] = headers;
                    _.forEach(vm.data.movements, function (obj, index) {
                        var text = vm.data.search.config.showDetails ? obj.text : obj.shorttext,
                            arrayIndex = index + 1;
                        data[arrayIndex] = [
                        ];
                        data[arrayIndex].push(valueOrEmptyString(obj.date));
                        data[arrayIndex].push('"' + valueOrEmptyString(text).replace(/(?:\r\n|\r|\n|\\n)/g, ' ').replace(/"/g, '""') + '"');
                        data[arrayIndex].push(formattedValueOrEmptyString(obj.credit));
                        data[arrayIndex].push(formattedValueOrEmptyString(obj.debit, true));
                        data[arrayIndex].push(valueOrEmptyString(obj.valueDate));
                        if (showBalance) data[arrayIndex].push(formattedValueOrEmptyString(obj.balance))
                    });
                    return data
                }
                function getTotalCreditDebit() {
                    var total = {
                        credit: 0,
                        debit: 0
                    };
                    _.forEach(vm.data.movements, function (element) {
                        total.credit += element.credit || 0;
                        total.debit -= element.debit || 0
                    });
                    return total
                }
                function initSearchConfig(efInitResponse) {
                    resetSearchConfig(efInitResponse);
                    vm.data.search.config.transactionType = efInitResponse.bookingType;
                    vm.data.search.criteria = _.cloneDeep(vm.data.search.config);
                    vm.data.search.criteria.account = productService.getByIban(vm.data.search.config.account.model) [0];
                    vm.data.config.account = vm.data.search.criteria.account
                }
                function resetSearchConfig(efInitResponse) {
                    productService.extendAccounts(efInitResponse.accounts);
                    vm.data.search.accounts = dropdowns.buildAccountOptions(efInitResponse.accounts);
                    var initialAccount,
                        initialValue = productService.extendAccount(efInitResponse.selectedAccount).iban;
                    if (_.isNil(initialValue) && !_.isNil(shared.data.productUniqueKey)) {
                        initialAccount = productService.getByUniqueKey(shared.data.productUniqueKey);
                        if (initialAccount) initialValue = initialAccount.iban
                    }
                    if (_.isNil(initialValue)) {
                        initialAccount = productService.getByUniqueKey(userData.standardAccount.productUniqueKey);
                        if (initialAccount) initialValue = initialAccount.iban;
                        else initialValue = _.get(_.head(vm.data.search.accounts), 'value', null)
                    }
                    vm.data.search.config = {
                        account: {
                            model: initialValue
                        },
                        currency: _.get(initialAccount, 'account.currency', null),
                        transactionType: pf.globals.detailpages.efmovements.transactionType.ALL,
                        selectedMonth: vm.data.search.availableMonths[0].value,
                        rangeSelect: 0,
                        transactionDateFrom: {
                            model: ''
                        },
                        transactionDateTo: {
                            model: ''
                        },
                        amountFrom: '',
                        amountTo: '',
                        showDetails: 9 === userData.movementsBuchArt,
                        numberOfMovements: efInitResponse.numberOfMovements
                    }
                }
                function getMinDate() {
                    var today = moment(),
                        endOfThisMonth = moment().endOf('month').format(pf.globals.formats.moment.ISO_DATE),
                        isEndOfMonth = today.isSame(endOfThisMonth, 'day'),
                        minDate = moment().subtract(15, 'month');
                    if (isEndOfMonth) minDate = minDate.endOf('month');
                    return minDate.format(pf.globals.formats.moment.ISO_DATE)
                }
                function isRangeTypeCurrentDay() {
                    return 2 === vm.data.search.config.rangeSelect
                }
                function init(response) {
                    helper.clearMessages();
                    initSearchConfig(response.result);
                    vm.actions.handleResponse(response, false);
                    vm.data.search.config.currency = vm.data.config.account.currency;
                    var unwatch = $scope.$watch('vm.data.filterArg', function () {
                        $scope.$applyAsync()
                    });
                    $scope.$on('$destroy', unwatch)
                }
                var helper = shared.helper,
                    service = helper.service,
                    translate = helper.translate,
                    detailPageId = helper.addAsChildPage({
                        scope: $scope,
                        name: 'overview'
                    }),
                    monthsEnum = wcmsEnumGenerator.getEnumObject('monthfull', $scope),
                    tableFocusser = new focus.GrowingTableFocusser(detailPageId + '-last-movements-table'),
                    vm = {
                        actions: {
                        },
                        data: {
                            search: {
                                transactionTypesObject: wcmsEnumGenerator.getEnumObject('transactionTypes', $scope),
                                availableMonths: getAvailableMovementMonths(),
                                accounts: [
                                ],
                                rangeToday: moment(),
                                config: {
                                },
                                criteria: {
                                }
                            },
                            config: {
                                transactionType: pf.globals.detailpages.efmovements.transactionType.ALL
                            },
                            uiAssetsView: userData.uiAssetsView,
                            showBalanceColumn: true,
                            collapsibleOpen: true,
                            showTimeRangeTooltip: pfWidgetFunctions.hasActionUrlForDetailPage(helper.detailPageName, 'TimeRangeTooltip'),
                            dateFrom: {
                                minDate: getMinDate(),
                                maxDate: moment().format(pf.globals.formats.moment.ISO_DATE)
                            },
                            dateTo: {
                                minDate: getMinDate(),
                                maxDate: moment().format(pf.globals.formats.moment.ISO_DATE)
                            }
                        },
                        helpers: {
                        }
                    };
                vm.data.showBackToAssets = historyService.hasHistory();
                vm.helpers.accountChanged = function accountChanged(entry) {
                    vm.data.search.config.currency = entry.account.currency;
                    vm.actions.searchBtn()
                };
                vm.actions.searchBtn = function searchBtn() {
                    vm.data.collapsibleOpen = false;
                    return vm.actions.search(true)
                };
                vm.actions.search = function search(doFocus) {
                    vm.data.movements = [
                    ];
                    var config = vm.data.search.config,
                        selectedAccount = productService.getByIban(config.account.model) [0],
                        params = {
                            account: selectedAccount,
                            accountIban: config.account.model,
                            amountFrom: config.amountFrom,
                            amountTo: config.amountTo,
                            numPostings: config.numberOfMovements,
                            transactionType: config.transactionType,
                            text: config.text
                        };
                    vm.data.search.criteria = _.cloneDeep(config);
                    vm.data.search.criteria.account = params.account;
                    if (_.has(vm.data, 'config')) params.listId = vm.data.config.listId;
                    switch (config.rangeSelect) {
                        case 0:
                            if (!_.isEmpty(config.transactionDateFrom) && !_.isEmpty(config.transactionDateFrom.model)) params.transactionDateFrom = moment(config.transactionDateFrom.model, pf.globals.formats.moment.LOCALIZED_DATE).format(pf.globals.formats.moment.ISO_DATE);
                            if (!_.isEmpty(config.transactionDateTo) && !_.isEmpty(config.transactionDateTo.model)) params.transactionDateTo = moment(config.transactionDateTo.model, pf.globals.formats.moment.LOCALIZED_DATE).format(pf.globals.formats.moment.ISO_DATE);
                            break;
                        case 1:
                            var month = moment(config.selectedMonth);
                            params.transactionDateFrom = moment.max(month.startOf('month'), moment(vm.data.dateFrom.minDate)).format(pf.globals.formats.moment.ISO_DATE);
                            params.transactionDateTo = moment.min(month.endOf('month'), moment(vm.data.dateTo.maxDate)).format(pf.globals.formats.moment.ISO_DATE);
                            break;
                        case 2:
                            params.transactionDateFrom = moment().format(pf.globals.formats.moment.ISO_DATE);
                            params.transactionDateTo = params.transactionDateFrom
                    }
                    params = util.removeEmptyProperties(params);
                    vm.data.config = angular.copy(params);
                    vm.data.filterArg = '';
                    return service.getTransactions(params).then(function success(response) {
                        vm.actions.handleResponse(response, doFocus)
                    })
                };
                vm.actions.reset = function reset() {
                    $timeout(resetSearchConfig(vm.data))
                };
                vm.actions.handleResponse = function handleResponse(response, doFocus) {
                    helper.applyMessages(response.messages);
                    var result = response.result;
                    _.assign(vm.data, result);
                    if (!_.isEmpty(result)) {
                        if (_.isEmpty(result.movements)) vm.data.movements = [
                        ];
                        if (!_.isNil(result.buchDatVon)) {
                            config.transactionDateFrom.model = moment(result.buchDatVon).format(pf.globals.formats.moment.LOCALIZED_DATE);
                            vm.data.search.criteria.transactionDateFrom.model = config.transactionDateFrom.model
                        }
                        if (!_.isNil(result.buchDatBis)) {
                            config.transactionDateTo.model = moment(result.buchDatBis).format(pf.globals.formats.moment.LOCALIZED_DATE);
                            vm.data.search.criteria.transactionDateTo.model = config.transactionDateTo.model
                        }
                        applyForwardId(result);
                        if (doFocus) focus.detailpageFocus();
                        updateBalanceColumnFlag()
                    }
                };
                vm.actions.loadMore = function loadMore() {
                    var params = vm.data.config;
                    params.tempId = vm.data.tempId;
                    tableFocusser.saveCurrentState();
                    service.getTransactions(params).then(function success(response) {
                        helper.applyMessages(response.messages);
                        var result = response.result;
                        if (!_.isEmpty(result)) {
                            vm.data.movements = vm.data.movements.concat(result.movements);
                            applyForwardId(result)
                        }
                        $timeout(function () {
                            tableFocusser.focusAfterUpdate()
                        })
                    })
                };
                vm.actions.openDetail = function openDetail(event, movement) {
                    movement.accountIban = vm.data.config.account.iban;
                    historyService.setPreventClearOnClose(true);
                    movements.showDetail(service.name, movement, event.target)
                };
                vm.actions.exportToCsv = function exportToCsv() {
                    var searchOptions = prepareExportSearchOptionsData(),
                        data = searchOptions.concat(prepareExportTableData());
                    data.push('');
                    data.push(translate('DisclaimerTitle', {
                        textKey: 'global'
                    }));
                    data.push(translate('Disclaimer', {
                        textKey: 'global'
                    }));
                    vm.data.csvData = {
                        model: JSON.stringify(data),
                        filename: 'export_' + translate('Transactions', $scope) + '_' + moment().format('YYYYMMDD') + '.csv'
                    }
                };
                vm.helpers.isBcNumberVisible = function isBcNumberVisible(entry) {
                    return entry.bkClearNr && vm.data.config.showDetails
                };
                vm.helpers.isTableFilterActive = function isTableFilterActive() {
                    return !_.isEmpty(vm.data.filterArg)
                };
                vm.helpers.notDefaultTransactionType = function notDefaultTransactionType() {
                    return !isDefaultTransactionType()
                };
                vm.helpers.getMonthNameByValue = function getMonthNameByValue() {
                    var month = _.find(vm.data.search.availableMonths, [
                        'value',
                        vm.data.search.criteria.selectedMonth
                    ]);
                    return _.get(month, 'name', '')
                };
                var doCall = function doCall() {
                    var params = {
                    };
                    if (shared.data.productUniqueKey) {
                        var selectedAccount = productService.getByUniqueKey(shared.data.productUniqueKey);
                        params.accountIban = selectedAccount.iban;
                        vm.data.collapsibleOpen = false
                    }
                    service.getTransactions(params).then(function (response) {
                        $timeout(function () {
                            init(response)
                        })
                    })
                };
                _.assignIn(this, vm);
                var wrappedDataLoaded = productService.getWrapperFunction(doCall, helper.goToErrorState);
                wrappedDataLoaded()
            };
        controller.$inject = [
            '$scope',
            '$timeout',
            'shared',
            'deps'
        ];
        return {
            controller: controller,
            directives: directives,
            templateUrl: platform.getResourceRoot() + '/static/fipo/detailpages/efmovements/states/overview.html'
        }
    })
}();
