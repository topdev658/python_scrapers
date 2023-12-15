import hashlib
import json
from typing import Tuple, List
from collections import OrderedDict

from custom_libs import date_funcs
from project.custom_types import LeasingContractParsed, LeasingFeeParsed
from .custom_types import LeasingCompany


def get_leasing_companies_from_json(resp_text: str) -> Tuple [bool, List[LeasingCompany], str]:
    try:
        subsidiaries = []  # List[subsidiaries]
        next_subsidiaries_url = ''
        # 11_resp_subsidiaries.json
        # {"subsidiaries":[{"personType":"J","personCode":789925,"tipDoc":"S","cif":"A08072415","companyName":"FERROCARRILES Y TRANSPORTES SA"},{"personType":"J","personCode":2966947,"tipDoc":"S","cif":"A43000348","companyName":"COMPAÑIA REUSENSE DE AUTOMOVILES HISPANI"},{"personType":"J","personCode":802275,"tipDoc":"S","cif":"A08552770","companyName":"17 BAGES BUS S.A.U."},{"personType":"J","personCode":257216,"tipDoc":"S","cif":"A07284375","companyName":"32 EIVISSA BUS S.A."},{"personType":"J","personCode":4981649,"tipDoc":"S","cif":"B17834839","companyName":"MAYPE TAXIS Y MICROBUSES SL"}],"_links":{"self":{"href":"https://empresas3.gruposantander.es/paas/api/nwe-subsidiary-api/v1/subsidiary?otherSubsidiary=true&pagination.codperss=2951219&pagination.tipdoc=S&pagination.apellnom=25%20OSONA%20BUS%20S.A.U.&pagination.tipopel=J&pagination.coddocud=A08290538"}}}
        resp_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_text)
        subsidiaries_from_json = resp_json['subsidiaries']
        for sub in subsidiaries_from_json:
            subsidiary = LeasingCompany(
                personCode=sub['personCode'],
                cif=sub['cif'],
                companyName=sub['companyName'])
            subsidiaries.append(subsidiary)

        links = resp_json['_links']
        if 'next' in links:
            next_subsidiaries_url = links['next']['href']

    except Exception as _e:
        return False, [], ''

    return True, subsidiaries, next_subsidiaries_url

def get_leasing_contracts_from_json_resp(resp_text: str) -> List[LeasingContractParsed]:
    # {"_embedded":{"contractList":[{"contractNumber":"0473156","contractSignatureDate":"2021-07-28","expirationDate":"2026-06-28","durationMonth":"60","propertyType":"Mobiliario","leasingEntity":"BANCO SANTANDER S.A.","propertyCost":216117.10,"pendingCapital":139167.23,"currency":"EUR","purchaseOptionDate":"2026-07-28","purchaseAmountOption":3865.97,"interestType":"INT. FIJO","prescriptorCif":"A39427547","prescriptorName":"EVOBUS IBERICA S.A.","mocDescrip":"AUTOCARES","regularity":"MENSUAL","clientCif":"B60917051","clientName":"DISBUS 21 SL.","contractType":"3","share":4677.82,"partenonContract":"0049 1895 153 0473156"},{"contractNumber":"0473160","contractSignatureDate":"2021-07-28","expirationDate":"2026-06-28","durationMonth":"60","propertyType":"Mobiliario","leasingEntity":"BANCO SANTANDER S.A.","propertyCost":216117.10,"pendingCapital":139167.23,"currency":"EUR","purchaseOptionDate":"2026-07-28","purchaseAmountOption":3865.97,"interestType":"INT. FIJO","prescriptorCif":"A17030529","prescriptorName":"BEULAS S.A.","mocDescrip":"AUTOCARES","regularity":"MENSUAL","clientCif":"B60917051","clientName":"DISBUS 21 SL.","contractType":"3","share":4677.82,"partenonContract":"0049 1895 153 0473160"},{"contractNumber":"0473165","contractSignatureDate":"2021-07-28","expirationDate":"2026-06-28","durationMonth":"60","propertyType":"Mobiliario","leasingEntity":"BANCO SANTANDER S.A.","propertyCost":216117.10,"pendingCapital":139167.23,"currency":"EUR","purchaseOptionDate":"2026-07-28","purchaseAmountOption":3865.97,"interestType":"INT. FIJO","prescriptorCif":"A17030529","prescriptorName":"BEULAS S.A.","mocDescrip":"AUTOCARES","regularity":"MENSUAL","clientCif":"B60917051","clientName":"DISBUS 21 SL.","contractType":"3","share":4677.82,"partenonContract":"0049 1895 153 0473165"},{"contractNumber":"0323011","contractSignatureDate":"2020-03-06","expirationDate":"2025-02-06","durationMonth":"60","propertyType":"Mobiliario","leasingEntity":"BANCO SANTANDER S.A.","propertyCost":100000.00,"pendingCapital":37094.46,"currency":"EUR","purchaseOptionDate":"2025-03-06","purchaseAmountOption":1712.04,"interestType":"INT. FIJO","prescriptorCif":"A78498193","prescriptorName":"COCENTRO S.A.","mocDescrip":"AUTOCARES","regularity":"MENSUAL","clientCif":"B60917051","clientName":"DISBUS 21 SL.","contractType":"3","share":2071.57,"partenonContract":"0049 1895 153 0323011"}]},"_links":{"self":{"href":"https://empresas3.gruposantander.es/paas/api/nwe-leasingrenting-api/leasing/v1/contract?clientCif=B60917051&personCode=1588307&personType=J&contractType=3&expDateFrom=1984-01-01&expDateTo=2063-12-31&dateSignedFrom=1984-01-01&dateSignedTo=2023-06-06&page=0&size=10&sort=contractSignatureDate,desc"}},"page":{"size":10,"totalElements":4,"number":0}}
    resp_json = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(resp_text)
    contracts_list = resp_json['_embedded']['contractList']
    leasing_contracts_parsed = []
    for contract in contracts_list:
        office = ''
        contract_number = contract['contractNumber']
        contract_date = contract['contractSignatureDate']
        expiration_date = contract['expirationDate']
        property_cost = contract['propertyCost']
        partenon_contract = contract['partenonContract']

        hashbase = 'SANTANDER{}{}{}'.format(
            contract_number,
            contract_date,
            property_cost  # capital
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        contract_parsed = {
            'office': office,
            'partenon_contract': partenon_contract,
            'contract_number': contract_number,
            'property_cost': property_cost,
            'contract_date': contract_date,
            'expiration_date': expiration_date,
            'keyvalue': keyvalue,
            'has_details': True,
        }
        leasing_contracts_parsed.append(contract_parsed)

    return leasing_contracts_parsed


def get_leasing_contract_details_from_json_resp(
        resp_contract_details_json: str,
        contract_parsed: LeasingContractParsed) -> LeasingContractParsed:

    # {"productSubType":"013","pendingCapital":135701.53,"clientCif":"B60917051","clientName":"DISBUS 21 SL.","commission":1307.51,"partenonContract":"0049 1895 153 0473156","propertyCost":216117.10,"leasingEntity":"BANCO SANTANDER S.A.","signatureDate":"2021-07-28","purchaseDateOption":"2026-07-28","purchaseAmountOption":3865.97,"currency":"EUR","office":"O.E. MOLLET, ONZE DE SETEMBRE, 3","regularity":"MENSUAL","durationMonth":"60","propertyType":"AUTOCARES","interestType":"INT. FIJO","taxType":"IVA","prescriptor":"EVOBUS IBERICA S.A.","subsidized":"AVANZA","grossCost":4677.82,"descProduct":"LEASING ICO INVERSION","productType":"153"}
    contract_parsed['office'] = resp_contract_details_json['partenonContract'][4:8]
    contract_parsed['contract_reference'] = resp_contract_details_json['partenonContract']
    contract_parsed['pending_repayment'] = resp_contract_details_json['pendingCapital']
    contract_parsed['contract_date'] = resp_contract_details_json['signatureDate']
    contract_parsed['expiration_date'] = resp_contract_details_json['purchaseDateOption']
    contract_parsed['amount'] = resp_contract_details_json['propertyCost']
    contract_parsed['residual_value'] = resp_contract_details_json['purchaseAmountOption']
    contract_parsed['fees_quantity'] = resp_contract_details_json['durationMonth']

    return contract_parsed


def get_leasing_fees_parsed_with_invoice_details_from_invoices_details_json_resps(
        resp_invoices_json: OrderedDict,
        leasing_fees_parsed: List[LeasingFeeParsed],
        ) -> List[LeasingFeeParsed]:

    for idx, fee_parsed in enumerate(leasing_fees_parsed):
        try:
            invoices = [x for i, x in enumerate(resp_invoices_json)
                     if date_funcs.convert_date_to_db_format(x['invoiceDate']) == fee_parsed['operational_date']
                     and x['invoiceAmount'] == fee_parsed['fee_amount']]
            if invoices:
                fee_parsed['invoice_number'] = invoices[0]['invoiceNumber'] # '23013541'
                account_number = invoices[0]['invoice_detail']['clientCCC'] # '0049/1895/00/2010279174' -> '00491895002010279174'
                account_number = account_number.replace('/', '')
                fee_parsed['account_number'] = account_number
                fee_parsed['interest_nominal'] = invoices[0]['invoice_detail']['interestNominal']

                fee_parsed['state'] = 'LIQUIDADO' if invoices[0]['invoiceStatus'] == 'Pagada' else 'PENDIENTE'
            else:
                fee_parsed['state'] = 'PENDIENTE'
                fee_parsed['invoice_number'] = ''
                fee_parsed['account_number'] = ''
        except:
            print("{}: can't get leasing_fee_parsed with details: EXCEPTION\n{}".format(
                fee_parsed,
            ))

        leasing_fees_parsed[idx] = fee_parsed
    return leasing_fees_parsed


def get_leasing_fees_parsed_from_maturities_and_invoices_json_resps(
        resp_maturities_json: OrderedDict,
        resp_invoices_json: OrderedDict,
        contract_parsed: LeasingContractParsed
        ) -> List[LeasingFeeParsed]:

    leasing_fees_parsed = []  # type: List[LeasingFeeParsed]

    for idx, maturity in enumerate(resp_maturities_json):

        # maturity = OrderedDict([('clientCif', 'B60917051'), ('clientName', 'DISBUS 21 SL.'), ('amortization', 3238.06), ('contractNumber', '0473156'), ('currency', 'EUR'), ('expirationNumber', ''), ('expirationDate', '2021-07-30'), ('grossFee', 4627.25), ('interest', 586.11), ('interestPercentage', 3.55), ('invoiceNumber', '23013540'), ('netShare', 3824.17), ('pendingCapital', 212879.04), ('taxAmount', 803.08), ('taxPercentage', 21.0), ('invoiceStatus', 'Pagada')])
        # invoice = OrderedDict([('clientCif', 'B60917051'), ('clientName', 'DISBUS 21 SL.'), ('contractNumber', '0473156'), ('invoiceConcept', 'CUOTA DE ARRENDAMIENTO FINANCIERO'), ('amortization', 3238.06), ('commissionClaims', 0.0), ('expirationDate', '2021-07-30'), ('expirationNumber', 1), ('interestDelay', 0.0), ('interestImp', 586.11), ('invoiceStatus', 'Pagada'), ('invoiceDate', '2021-08-03'), ('invoiceNumber', '23013540'), ('invoiceTax', 0), ('invoiceType', 1), ('issuer', 'BANCO SANTANDER S.A'), ('issuerCif', 'A39000013'), ('leasingEntity', 'BANCO SANTANDER S.A.'), ('leasingEntityCode', '01'), ('netShare', '3824.17'), ('taxBase', 3824.17), ('taxPercentage', 21.0), ('taxTax', 803.08), ('taxType', 'IVA'), ('currency', 'EUR'), ('invoiceAmount', 4627.25)])
        fee_parsed = {}  # type: LeasingFeeParsed

        maturity_pending_amount = maturity['pendingCapital']
        maturity_amount = maturity['grossFee']

        maturity_expiration_date = maturity['expirationDate']
        expiration_date = date_funcs.convert_date_to_db_format(maturity_expiration_date) # '2021-07-30'

        fee_parsed['fee_number'] = idx + 1
        fee_parsed['operational_date'] = expiration_date
        fee_parsed['currency'] = maturity['currency']
        fee_parsed['financial_repayment'] = maturity['amortization']
        fee_parsed['financial_performance'] = maturity['interest']
        #fee_parsed['insurance_amount'] = installment['totalInsurancesAmount'][0]['amount'] # seguro, always 0.00
        #fee_parsed['fee_type'] = 'CUOTA' if installment['installmentType'] == 'INSTALLMENT' else None
        fee_parsed['amount'] = maturity['netShare']  # cuota neta
        fee_parsed['taxes_amount'] = maturity['taxAmount']  # impuesto
        fee_parsed['fee_amount'] = maturity_amount  # cuota bruta
        fee_parsed['pending_repayment'] = maturity_pending_amount  # capital vivo
        fee_parsed['insurance_amount'] = None
        fee_parsed['tax_percentage'] = maturity['taxPercentage']


        fee_parsed['statement_id'] = None
        fee_parsed['contract_id'] = None

        invoices = [x for i, x in enumerate(resp_invoices_json) if
                 x['expirationDate'] == maturity_expiration_date and
                 x['invoiceAmount'] == maturity_amount]
        if invoices:
            fee_parsed['invoice_id'] = invoices[0]['invoiceNumber']
            fee_parsed['fee_number'] = invoices[0]['expirationNumber']
            fee_parsed['delay_interest'] = invoices[0]['interestDelay']

            invoice_operational_date = invoices[0]['invoiceDate']
            operational_date = date_funcs.convert_date_to_db_format(invoice_operational_date)
            fee_parsed['operational_date'] = operational_date
            fee_parsed['amount'] = invoices[0]['netShare']
            fee_parsed['tax_percentage'] = invoices[0]['taxPercentage']

        fee_parsed['fee_reference'] = "{}/{}".format(contract_parsed['contract_number'], fee_parsed['fee_number'])
        hashbase = 'SANTANDER{}-{}-{}-{}'.format(
            contract_parsed['contract_number'],
            fee_parsed['fee_number'], # fee_number
            expiration_date,  # expiration_date
            maturity_amount,  # fee_amount
            maturity_pending_amount,  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()
        fee_parsed['keyvalue'] = keyvalue

        leasing_fees_parsed.append(fee_parsed)

    for invoice in [x for x in resp_invoices_json if x['expirationNumber'] == 0]:

        fee_parsed = {}  # type: LeasingFeeParsed

        maturity_pending_amount = None
        invoice_amount = invoice['invoiceAmount']

        fee_parsed['fee_number'] = 0
        fee_parsed['currency'] = invoice['currency']
        fee_parsed['financial_repayment'] = invoice['amortization']
        fee_parsed['financial_performance'] = invoice['interestImp']
        fee_parsed['amount'] = invoice['taxBase']  # cuota neta
        fee_parsed['taxes_amount'] = invoice['taxTax']  # impuesto
        fee_parsed['fee_amount'] = invoice_amount  # cuota bruta
        fee_parsed['pending_repayment'] = maturity_pending_amount  # capital vivo
        fee_parsed['insurance_amount'] = None
        fee_parsed['tax_percentage'] = invoice['taxPercentage']

        fee_parsed['statement_id'] = None
        fee_parsed['contract_id'] = None

        fee_parsed['invoice_id'] = invoice['invoiceNumber']
        fee_parsed['fee_number'] = invoice['expirationNumber']
        fee_parsed['delay_interest'] = invoice['interestDelay']

        invoice_operational_date = invoice['invoiceDate']
        operational_date = date_funcs.convert_date_to_db_format(invoice_operational_date)
        fee_parsed['operational_date'] = operational_date
        fee_parsed['amount'] = invoice['taxBase']
        fee_parsed['tax_percentage'] = invoice['taxPercentage']

        fee_parsed['fee_reference'] = "{}/{}".format(contract_parsed['contract_number'], fee_parsed['fee_number'])
        hashbase = 'SANTANDER{}-{}-{}-{}'.format(
            contract_parsed['contract_number'],
            fee_parsed['fee_number'], # fee_number
            expiration_date,  # expiration_date
            invoice_amount,  # fee_amount
            maturity_pending_amount,  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()
        fee_parsed['keyvalue'] = keyvalue
        leasing_fees_parsed.append(fee_parsed)

    return leasing_fees_parsed
