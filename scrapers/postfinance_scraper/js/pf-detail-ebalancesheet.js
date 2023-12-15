/* Copyright 2012 - 2019 by PostFinance Ltd - All rights reserved */
!function () {
    'use strict';
    define('pf-detail-efbalancesheet-service', function (require) {
        function EfBalancesheetService() {
            DetailPageAbstractService.call(this);
            this.loadData = function loadData() {
                var urlObj = pfWidgetFunctions.getDataUrlForDetailPage(this.name);
                this.restConfig.showSpinner = true;
                this.restConfig.showLoader = false;
                return restngDetailpages.getJson(this.restConfig, urlObj.url, urlObj.params)
            }
        }
        var _ = require('lodash'),
            restngDetailpages = require('pf-shared-modules-rest_ng_detailpages'),
            DetailPageAbstractService = require('pf-shared-modules-detail_page_abstract_service'),
            pfWidgetFunctions = require('pf-widget-functions');
        EfBalancesheetService.prototype = _.create(DetailPageAbstractService.prototype);
        EfBalancesheetService.constructor = DetailPageAbstractService;
        return EfBalancesheetService
    })
}();
!function () {
    'use strict';
    var directives = [
    ];
    define('pf-detail-efbalancesheet', function (require) {
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
        var OverviewController = require('pf-detail-efbalancesheet-overview'),
            EfBalancesheetService = require('pf-detail-efbalancesheet-service'),
            DetailPageHelper = require('pf-shared-modules-detail_page_helper'),
            detailPageName = 'efbalancesheet',
            helper = new DetailPageHelper(detailPageName),
            efBalancesheetService = new EfBalancesheetService,
            states = {
                OVERVIEW: helper.createModuleName('overview')
            },
            shared = {
                helper: helper,
                functions: {
                },
                data: {
                }
            },
            controller = function controller($scope, $state) {
                helper.init({
                    scope: $scope,
                    state: $state,
                    service: efBalancesheetService
                });
                var readyFunction = function readyFunction(urlObj) {
                    shared.data = urlObj;
                    helper.goToState(states.OVERVIEW)
                };
                helper.signalReady(readyFunction)
            };
        controller.$inject = [
            '$scope',
            '$state'
        ];
        return {
            name: 'EfBalanceSheetController',
            detailPageName: detailPageName,
            ctrl: controller,
            init: init,
            template: '/static/fipo/detailpages/efbalancesheet/efbalancesheet.html'
        }
    })
}();
!function () {
    'use strict';
    var directives = [
        'directive-widget-dropdown',
        'directive-widget-more_actions',
        'directive-table-table_filter',
        'directive-table-multi_table',
        'directive-balance_pie_chart',
        'directive-csv_export_button'
    ];
    define('pf-detail-efbalancesheet-overview', function (require) {
        var _ = require('lodash'),
            actions = require('pf-shared-modules-actions'),
            moment = require('moment'),
            platform = require('pf-shared-modules-platform'),
            detect = require('pf-app-detect'),
            webtrendsTracker = require('pf-shared-modules-webtrendstracker'),
            translator = require('pf-shared-modules-translator'),
            pfWidgetFunctions = require('pf-widget-functions'),
            productService = require('pf-shared-modules-productservice'),
            accountsModule = require('pf-shared-modules-accounts'),
            numbers = require('pf-shared-modules-numbers'),
            formatter = require('pf-shared-modules-formatter'),
            scrolling = require('pf-shared-modules-scrolling'),
            products = require('pf-shared-modules-products'),
            historyService = require('pf-shared-modules-historyservice'),
            userData = require('pf-sessiondata-userdata'),
            detailStateService = require('pf-shared-modules-detailstateservice'),
            controller = function controller($scope, shared) {
                function prepareExportTableData() {
                    function createTable(titleKey, footerKey, table, total, columns) {
                        if (tablesInitiated) data.push([]);
                        else tablesInitiated = true;
                        var tableRow = [
                            translatorFn(titleKey)
                        ];
                        _.forEach(table.rows, function (dataRow) {
                            tableRow.push(dataRow[columns[0]]);
                            tableRow.push(dataRow[columns[1]]);
                            tableRow.push(dataRow[columns[2]]);
                            if (hasForeignCurrency) tableRow.push(formatAmount(dataRow[columns[3]], dataRow[columns[4]]));
                            tableRow.push(formatAmount(dataRow[columns[5]]));
                            data.push(tableRow);
                            tableRow = [
                                null
                            ]
                        });
                        var footer = [
                            translatorFn(footerKey),
                            null,
                            null,
                            null
                        ];
                        if (hasForeignCurrency) footer.push('');
                        footer.push(formatAmount(total));
                        data.push(footer)
                    }
                    var data = [
                        ],
                        hasForeignCurrency,
                        tablesInitiated = false;
                    _.forEach(vm.data.view.groups, function (item) {
                        hasForeignCurrency = hasForeignCurrency || item.tableData.hasForeignCurrency
                    });
                    if (!!vm.data.selectedAccountName) data.push([translatorFn('export.Customer'),
                        vm.data.selectedAccountName]);
                    var totalAmountLabel;
                    if (vm.data.view.hasCreditCards || vm.data.view.hasCreditCardsBusiness) if (vm.data.view.hasMortgages) totalAmountLabel = translatorFn('WithoutMortgagesCreditCards');
                    else totalAmountLabel = translatorFn('WithoutCreditCards');
                    else if (vm.data.view.hasMortgages) totalAmountLabel = translatorFn('WithoutMortgages');
                    var totalAmountCol = [
                        translatorFn('TotalAmountChf'),
                        totalAmountLabel,
                        null,
                        null
                    ];
                    if (hasForeignCurrency) totalAmountCol.push('');
                    totalAmountCol.push(formatAmount(vm.data.view.totalAmount));
                    data.push(totalAmountCol);
                    data.push([]);
                    var tableHeader = [
                        null,
                        translatorFn('Account'),
                        translatorFn('export.AccountDescription'),
                        translatorFn('AccountType')
                    ];
                    if (hasForeignCurrency) tableHeader.push(translatorFn('SaldoForeign'));
                    tableHeader.push(translatorFn('SaldoChf'));
                    data.push(tableHeader);
                    _.forEach(vm.data.view.groups, function (group) {
                        createTable(group.title, group.tableData.key, group.tableData, group.tableData.groupTotal, [
                            'description',
                            'title',
                            'productName',
                            'foreignAmount',
                            'currency',
                            'amount'
                        ])
                    });
                    _.forEach(vm.data.view.others, function (group) {
                        createTable(group.title, group.tableData.key, group.tableData, group.tableData.groupTotal, [
                            'description',
                            'title',
                            '',
                            '',
                            '',
                            'amount'
                        ])
                    });
                    data.push('');
                    data.push(translate('DisclaimerTitle', {
                        textKey: 'global'
                    }));
                    data.push(translate('Disclaimer', {
                        textKey: 'global'
                    }));
                    return data
                }
                function formatAmount(amount, currency) {
                    var formatted = '';
                    if (_.isNumber(amount)) {
                        formatted = amount.toFixed(2);
                        if (!!currency) formatted = currency + ' ' + formatted
                    }
                    return formatted
                }
                function createChartData() {
                    vm.data.chartData = {
                        type: vm.helpers.showTypeChart() ? 'TYPE' : 'CURRENCY',
                        chartColors: chartColors,
                        currencyTotals: vm.data.view.currencyTotals,
                        typeTotals: vm.data.view.typeTotals
                    }
                }
                function calculateGroupTables(data) {
                    vm.data.view = vm.data.view || {
                    };
                    vm.data.view.groups = [
                    ];
                    vm.data.view.others = [
                    ];
                    vm.data.view.currencyTotals = {
                    };
                    vm.data.view.typeTotals = {
                    };
                    vm.data.view.totalAmount = 0;
                    vm.data.view.hasCreditCards = false;
                    vm.data.view.hasPartnerCards = false;
                    vm.data.view.hasCreditCardsBusiness = false;
                    vm.data.view.hasMortgages = false;
                    _.forEach(tables, function (tableName) {
                        pushAccountTable(data, tableName)
                    });
                    vm.data.view.totalAmountTable = [
                        {
                            label: translatorFn('TotalAmount'),
                            hasValue: _.isNumber(vm.data.view.totalAmount),
                            value: numbers.formatNumber(vm.data.view.totalAmount, numbers.indicator.plusAndMinus, null, decimalsInTable) || translatorFn('NoContent'),
                            spanClass: vm.data.view.totalAmount < 0 ? 'negative_val' : ''
                        }
                    ]
                }
                function filterTablesByAccount(accountNr) {
                    var accountFilter;
                    if (accountNr) accountFilter = function (account) {
                        return account.nr === accountNr || account.kundenstammOid === accountNr
                    };
                    else accountFilter = _.constant(true);
                    return {
                        paymentAccounts: _.filter(vm.data.rawData.paymentAccounts, accountFilter),
                        savingsAccounts: _.filter(vm.data.rawData.savingsAccounts, accountFilter),
                        investmentAccounts: _.filter(vm.data.rawData.investmentAccounts, accountFilter),
                        retirementAccounts: _.filter(vm.data.rawData.retirementAccounts, accountFilter),
                        creditCards: _.filter(vm.data.rawData.creditCards, accountFilter),
                        partnerCards: _.filter(vm.data.rawData.partnerCards, accountFilter),
                        creditCardsBusiness: _.filter(vm.data.rawData.creditCardsBusiness, accountFilter),
                        mortgages: _.filter(vm.data.rawData.mortgages, accountFilter),
                        lifeInsurances: _.filter(vm.data.rawData.lifeInsurances, accountFilter)
                    }
                }
                function pushAccountTable(data, tableName) {
                    if (data[tableName] && !_.isEmpty(data[tableName])) {
                        var tableData,
                            mainTable = 'groups';
                        switch (tableName) {
                            case tables.CREDIT_CARDS:
                                vm.data.view.hasCreditCards = true;
                                tableData = generateTable(data[tableName], tableName, false, false);
                                mainTable = 'others';
                                break;
                            case tables.PARTNER_CARDS:
                                vm.data.view.hasPartnerCards = true;
                                tableData = generateTable(data[tableName], tableName, false, false);
                                mainTable = 'others';
                                break;
                            case tables.CREDIT_CARDS_BUSINESS:
                                vm.data.view.hasCreditCardsBusiness = true;
                                tableData = generateTable(data[tableName], tableName, false, false);
                                mainTable = 'others';
                                break;
                            case tables.MORTGAGES:
                                vm.data.view.hasMortgages = true;
                                tableData = generateTable(data[tableName], tableName, false, false);
                                mainTable = 'others';
                                break;
                            case tables.LIFE_INSURANCES:
                                tableData = generateTable(data[tableName], tableName, false, true);
                                break;
                            default:
                                tableData = generateTable(data[tableName], tableName, true, false)
                        }
                        vm.data.view[mainTable].push({
                            tableData: tableData,
                            tableName: tableName,
                            title: tablesKeys[tableName]
                        })
                    }
                }
                function generateTable(accounts, tableName, addToSum, lifeInsurance) {
                    var hasForeignCurrencyAccount = containsForeignCurrencyAccount(accounts),
                        groupTotal = 0,
                        table = {
                        },
                        errorInGroup = false;
                    table.rows = _.map(accounts, function (account) {
                        var hasAmountError = !!account.errorInService;
                        errorInGroup = errorInGroup || hasAmountError;
                        var hasForeignAmount = _.exists(account.balance),
                            visibleAmount = hasAmountError ? null : account.balance || account.amount;
                        groupTotal = hasAmountError ? null : addToTotal(groupTotal, visibleAmount);
                        var allowedActions = _.filter(account.actions, function (action) {
                                return pfWidgetFunctions.hasActionUrlForDetailPage(helper.detailPageName, action)
                            }),
                            filteredAllowedActions = _.intersection(allowedActions, products.getActions(account, b$.portal.device, 'balancesheet'));
                        if (addToSum) {
                            var currencyTotals = vm.data.view.currencyTotals;
                            currencyTotals[account.currency] = currencyTotals[account.currency] ? currencyTotals[account.currency] + account.amount : account.amount
                        }
                        var row = {
                            title: getAccountTitle(account, tableName),
                            description: getAccountDescription(account, tableName),
                            productName: !_.isUndefined(account.productName) ? account.productName : translatorFn(account.productTypeKey),
                            isForeign: hasForeignAmount,
                            foreignAmount: hasForeignAmount ? account.amount : null,
                            amountAvailable: account.amountAvailable,
                            currency: account.currency,
                            amount: visibleAmount,
                            actions: actions.buildActionEntries(filteredAllowedActions, $scope),
                            actionUrlReplacementObj: account,
                            errorInService: account.errorInService
                        };
                        if (lifeInsurance && !account.errorInService) _.assign(row, account.additionalInfo);
                        return row
                    });
                    if (addToSum) {
                        vm.data.view.totalAmount = errorInGroup ? null : addToTotal(vm.data.view.totalAmount, groupTotal);
                        switch (tableName) {
                            case tables.PAYMENT:
                                vm.data.view.typeTotals[translatorFn('PaymentAccounts')] = groupTotal;
                                break;
                            case tables.SAVINGS:
                                vm.data.view.typeTotals[translatorFn('SavingsAccounts')] = groupTotal;
                                break;
                            case tables.INVESTMENT:
                                vm.data.view.typeTotals[translatorFn('InvestmentAccounts')] = groupTotal;
                                break;
                            case tables.RETIREMENT:
                                vm.data.view.typeTotals[translatorFn('RetirementAccounts')] = groupTotal
                        }
                    }
                    table.groupTotal = groupTotal;
                    table.currency = pf.globals.types.currency.CHF;
                    table.key = 'Total' + tablesKeys[tableName];
                    table.hasForeignCurrency = hasForeignCurrencyAccount;
                    table.entries = accounts;
                    table.name = tableName;
                    return table
                }
                function addToTotal(total, addition) {
                    var result = total;
                    if (_.isNumber(total)) {
                        if (_.isNumber(addition)) result += addition
                    } else result = null;
                    return result
                }
                function containsForeignCurrencyAccount(accounts) {
                    return !_.isEmpty(accounts) && !_.every(accounts, [
                        'currency',
                        'CHF'
                    ])
                }
                function getAccountDescription(account, tableName) {
                    if (tableName === tables.PARTNER_CARDS) return account.additionalInfo.pan;
                    else return accountsModule.formatAccountNumber(account.nr || account.iban, account.type)
                }
                function getAccountTitle(account, tableName) {
                    if (account.alias) return account.alias;
                    else if (account.name) return account.name;
                    else if (tableName === tables.MORTGAGES) {
                        var additionalInfo = account.additionalInfo;
                        return translatorFn('MortgageTitle', {
                            interestRate: formatter.percentRaw(additionalInfo.interestRate),
                            term: formatter.localizedDateRangeSimple(additionalInfo.startDate, additionalInfo.endDate)
                        })
                    } else if (account.kundenstammOid) return vm.data.accounts[account.kundenstammOid].name;
                    return translatorFn('NoContent')
                }
                function extendAccounts(rawAccounts) {
                    extendIfExists(rawAccounts.paymentAccounts);
                    extendIfExists(rawAccounts.savingsAccounts);
                    extendIfExists(rawAccounts.investmentAccounts);
                    extendIfExists(rawAccounts.retirementAccounts);
                    extendIfExists(rawAccounts.creditCards);
                    extendIfExists(rawAccounts.partnerCards);
                    extendIfExists(rawAccounts.creditCardsBusiness);
                    extendIfExists(rawAccounts.mortgages);
                    extendIfExists(rawAccounts.lifeInsurances)
                }
                function extendIfExists(rawAccounts) {
                    if (rawAccounts) productService.extendAccounts(rawAccounts)
                }
                function generateAccounts(masterAccounts) {
                    var accounts = {
                    };
                    _.forEach(masterAccounts, function (account) {
                        accounts[account.oid] = account
                    });
                    return accounts
                }
                function getAccountDropdown(masterAccounts) {
                    var accounts = [
                            {
                                name: translatorFn('All'),
                                value: null
                            }
                        ],
                        unknownAccountIndex = 1;
                    _.forEach(masterAccounts, function (account) {
                        if (account.name) accounts.push({
                            name: account.name,
                            description: account.plusAccount ? translatorFn('PlusAccount')  : void 0,
                            value: account.oid
                        });
                        else accounts.push({
                            name: translatorFn('CustomerContract') + ' ' + unknownAccountIndex++,
                            description: translatorFn('DescriptionNotAvailable'),
                            value: account.oid
                        })
                    });
                    return accounts
                }
                var helper = shared.helper,
                    service = helper.service,
                    translate = helper.translate,
                    translatorFn = translator.createTranslator($scope);
                helper.addAsChildPage({
                    scope: $scope,
                    name: 'overview'
                });
                helper.setPageTexts({
                    pageTitle: translatorFn('DetailPageTitle'),
                    pageTitlePrintOnly: translatorFn('DetailPageTitlePrintOnly', {
                        date: moment().format(pf.globals.formats.moment.LOCALIZED_DATE_TIME)
                    })
                });
                var tables = {
                        PAYMENT: 'paymentAccounts',
                        SAVINGS: 'savingsAccounts',
                        INVESTMENT: 'investmentAccounts',
                        RETIREMENT: 'retirementAccounts',
                        CREDIT_CARDS: 'creditCards',
                        PARTNER_CARDS: 'partnerCards',
                        CREDIT_CARDS_BUSINESS: 'creditCardsBusiness',
                        MORTGAGES: 'mortgages',
                        LIFE_INSURANCES: 'lifeInsurances'
                    },
                    tablesKeys = {
                        paymentAccounts: 'PaymentAccounts',
                        savingsAccounts: 'SavingsAccounts',
                        investmentAccounts: 'InvestmentAccounts',
                        retirementAccounts: 'RetirementAccounts',
                        creditCards: 'CreditCards',
                        partnerCards: 'CreditCards',
                        creditCardsBusiness: 'CreditCardsBusiness',
                        mortgages: 'Mortgages',
                        lifeInsurances: 'LifeInsurances'
                    },
                    decimalsInTable = 2,
                    chartColors = [
                        '#eaa922',
                        '#AB6516',
                        '#beaf17',
                        '#584125',
                        '#3e2e1a',
                        '#806f60',
                        '#c3a600',
                        '#f9c100',
                        '#e6b900',
                        '#ffcc00'
                    ],
                    vm = {
                        data: {
                            view: {
                                chartType: 'TYPE',
                                chartTypeButtons: [
                                ]
                            },
                            csvData: {
                            },
                            csvButtonDisabled: false
                        },
                        actions: {
                        },
                        helpers: {
                        }
                    };
                vm.actions.exportToCsv = function exportToCsv(event) {
                    webtrendsTracker.trackWebtrends('WT.ac', '_li_ef_page-efbalancesheet_export');
                    var data = prepareExportTableData();
                    document.getElementsByName('data') [0].value = JSON.stringify(data);
                    document.getElementsByName('filename') [0].value = 'export_' + translatorFn('DetailPageTitle') + '_' + moment().format('YYYYMMDD') + '.csv';
                    service.exportToCsv(event.target.form)
                };
                vm.helpers.prepareCsvExportData = function prepareCsvExportData() {
                    vm.data.csvData.model = JSON.stringify(prepareExportTableData());
                    vm.data.csvData.filename = 'export_' + translatorFn('DetailPageTitle') + '_' + moment().format('YYYYMMDD') + '.csv'
                };
                vm.helpers.showButtons = function showButtons() {
                    return !platform.isMobile() && !detect.isApp()
                };
                vm.helpers.showCharts = function showCharts() {
                    return vm.data.view.totalAmount > 0 && (vm.helpers.showTypeChart() || vm.helpers.showCurrencyChart())
                };
                vm.helpers.showTypeChart = function showTypeChart() {
                    if (vm.data.view && vm.data.view.typeTotals && _.keys(vm.data.view.typeTotals).length > 1) return !_.some(vm.data.view.typeTotals, function (total) {
                        return total < 0
                    });
                    else return false
                };
                vm.helpers.showCurrencyChart = function showCurrencyChart() {
                    if (vm.data.view && vm.data.view.currencyTotals && _.keys(vm.data.view.currencyTotals).length > 1) return !_.some(vm.data.view.currencyTotals, function (total) {
                        return total < 0
                    });
                    else return false
                };
                vm.helpers.updateViewTables = function updateViewTables(item) {
                    var accountNr = item ? item.value : null;
                    vm.data.selectedAccountName = item ? item.name : null;
                    var data = filterTablesByAccount(accountNr);
                    calculateGroupTables(data);
                    createChartData()
                };
                var unbindGoToDetailpageFn = $scope.$on(pf.globals.events.GO_TO_DETAIL_PAGE, function (event, data) {
                    var urlObj = pfWidgetFunctions.getActionUrlForDetailPage(helper.detailPageName, data.actionType, data.actionUrlReplacementObj);
                    event.stopPropagation();
                    if ('overlay' !== _.get(urlObj, 'target', '') && 0 === userData.uiAssetsView && detailStateService.isPopupOpen()) {
                        var historyUrlObj = pfWidgetFunctions.buildJsonUrlObject('efbalancesheet', 'overview', {
                        }, {
                            scrollPos: scrolling.getScrollPosition()
                        });
                        historyService.pushDetailPage(historyUrlObj)
                    }
                    urlObj.data = {
                        object: data.actionUrlReplacementObj
                    };
                    pfWidgetFunctions.processUrlObject(urlObj)
                });
                $scope.$on('$destroy', function () {
                    unbindGoToDetailpageFn()
                });
                var doCall = function doCall() {
                    return service.loadData().then(function (response) {
                        if (response.result) {
                            vm.data.rawData = response.result;
                            extendAccounts(vm.data.rawData);
                            vm.data.accounts = generateAccounts(response.result.kundenstamm);
                            vm.helpers.updateViewTables(null);
                            vm.data.accountsDropdown = getAccountDropdown(response.result.kundenstamm)
                        }
                        if (response.messages) helper.applyMessages(response.messages);
                        if (shared.data.data && shared.data.data.scrollPos) {
                            scrolling.scrollToPosition(shared.data.data.scrollPos);
                            shared.data.data.scrollPos = null
                        }
                        if (vm.helpers.showTypeChart()) vm.data.view.chartTypeButtons.push({
                            name: translatorFn('ChartByType'),
                            value: 'TYPE'
                        });
                        if (vm.helpers.showCurrencyChart()) vm.data.view.chartTypeButtons.push({
                            name: translatorFn('ChartByCurrency'),
                            value: 'CURRENCY'
                        })
                    })
                };
                vm.data.config = vm.data.config || {
                };
                if (_.has(shared.data, 'config')) vm.data.config = shared.data.config;
                _.assignIn(this, vm);
                helper.showSpinnerWhile(productService.getWrapperFunction(doCall, helper.goToErrorState) ())
            };
        controller.$inject = [
            '$scope',
            'shared',
            'deps'
        ];
        return {
            controller: controller,
            directives: directives,
            templateUrl: platform.getResourceRoot() + '/static/fipo/detailpages/efbalancesheet/states/overview.html'
        }
    })
}();
