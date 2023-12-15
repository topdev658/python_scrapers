import hashlib
import re
from typing import Tuple, Dict, List
from collections import OrderedDict

from custom_libs import date_funcs, convert
from project.custom_types import LeasingContractParsed, LeasingFeeParsed
from .custom_types import LeasingCompany


def get_leasing_companies_from_json(resp_text: str) -> Tuple [bool, List[LeasingCompany]]:
    try:
        businesses = []  # List[LeasingBusiness]
        # 11_resp_financial_management_businesses.json
        # {"businesses":[{"id":"201ES0182001236615","businessDocuments":[{"businessDocumentType":{"id":"NIF"},"documentNumber":"B08405268","country":{"id":"ES"},"isPreferential":false,"name":"BARCELONA BUS S.L."
        businesses_from_json = re.findall('(?si){"id":"201(.*?)".*?"documentNumber":"(.*?)",.*?name":"(.*?)".*?"product":{"id":"201"}', resp_text)
        for b in businesses_from_json:
            business = LeasingCompany(
                id=b[0],
                cif=b[1],
                name=b[2])
            businesses.append(business)

    except Exception as _e:
        return False, []

    return True, businesses

def get_leasing_contracts_from_json_resp(resp_text: str) -> List[LeasingContractParsed]:
    # arrayDatos[0]=["LEASING MOBILIARIO","182","90","501","1635164","2017-03-28","2020-03-28","68465,00","0",""];

    # "data":{"leasings":[{"id":"ES0182050100000000000000000376971103XXXXXXXXX","numberType":{"id":"BOCF"},"number":"018254255011637971","isAgreementContract":true,"product":{"id":"2200","subproduct":{"id":"0"},"description":"LEASING MOBILIARIO"},"signatureDate":"2017-05-12","dueDate":"2024-05-12","amount":{"currency":"EUR","amount":215975.00},"isInsured":false,"isSettlementPeriodApplied":false},
    fields = re.findall(
        '(?si)"id":"(.*?)","numberType.*?"number":"(\d+?)".*?description":"(.*?)"'
        '.*?signatureDate":"(.*?)".*?dueDate":"(.*?)".*?currency":"(.*?)".*?amount":(.*?)}',
        resp_text)

    leasing_contracts_parsed = []
    for f in fields:
        #post_data = {'idx': f[0], 'bank': f[2], 'office': f[3], 'control': f[4], 'folio': f[5], 'depcode': f[9]}
        office = f[1][4:8]
        contract_id = f[0]
        # '018254255011637971' -> '0182-5425-0501-00000001637971'
        contract_reference = '{}{}{}{}-{}{}{}{}-0{}{}{}-0000000{}{}{}{}{}{}{}'.format(*list(f[1]))
        contract_date = date_funcs.convert_date_to_db_format(f[3])
        expiration_date = date_funcs.convert_date_to_db_format(f[4])
        amount = convert.to_float(f[6])

        hashbase = 'BBVA{}{}{}'.format(
            contract_reference,
            contract_date,
            amount  # capital
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        contract_parsed = {
            'office': office,
            'contract_id': contract_id,
            'contract_reference': contract_reference,
            'amount': amount,
            'contract_date': contract_date,
            'expiration_date': expiration_date,
            'keyvalue': keyvalue,
            'has_details': True,
            #'post_data': ''
        }
        leasing_contracts_parsed.append(contract_parsed)

    return leasing_contracts_parsed


def get_leasing_contract_details_from_json_resps(
        resp_text: str,
        resp_interest_text: str,
        contract_parsed: LeasingContractParsed) -> LeasingContractParsed:

    # {"data":{"id":"1","installmentsPlan":{"quotaType":{"id":"CONSTANT_NET_FEE"},"installmentsNumber":84,"quotaBase":"N","periodicity":"MONTHLY","totalQuota":{"currency":"EUR","amount":2664.45,"number":84},"payment":{"paymentPeriodType":"PREPAID"},"gracePeriod":{"installmentsNumber":0},"isFinancedInsurance":false},"conditions":[{"id":"0","paymentMethod":"POSTPONED","unit":{"unitType":"PERCENTAGE","percentage":1.35000000,"percentageName":"FIJO"}},{"id":"1","paymentMethod":"POSTPONED","unit":{"unitType":"PERCENTAGE","percentage":21.00000000,"percentageName":"I.V.A. MEDIO"}},{"id":"2","paymentMethod":"POSTPONED","unit":{"unitType":"PERCENTAGE","percentage":1.37568500}},{"id":"3","paymentMethod":"POSTPONED","unit":{"unitType":"AMOUNTUNIT","amount":2664.45,"currency":"EUR"}},{"id":"4","paymentMethod":"POSTPONED","unit":{"unitType":"AMOUNTUNIT","amount":3223.98}}],"balances":[{"balanceType":"NET","amount":215975.00,"currency":"EUR"},{"balanceType":"FINANCED_EXPENSES","amount":0.00,"currency":"EUR"},{"balanceType":"CASH_ADVANCED","amount":0.00,"currency":"EUR","grossAmount":{"currency":"EUR","amount":0.00}},{"balanceType":"FLOOR_PRICE","amount":0.00,"currency":"EUR"},{"balanceType":"FINANCED_AMOUNT","amount":215975.00,"currency":"EUR"}]}}
    percentages = re.findall(
       '(?si)"percentage":(.*?)[,}].*?',
        resp_text)

    financed_amount = re.findall(
        '(?si)"balanceType":.*?FINANCED_AMOUNT.*?"amount":(.*?),.*?currency',
        resp_text)

    quotas = re.findall(
       '(?si)installmentsNumber":(.*?),.*?amount":(.*),"number.*?',
        resp_text)

    interests = re.findall(
        '(?si)"interestRate":(.*?),".*?',
        resp_interest_text)

    """
    JFM: all the contract data extracted from the page:
    percentages = ['1.35000000', '21.00000000', '1.37568500']
    financed_amount = ['215975.00']
    quotas = [('84', '2664.45')]
    interests = ['1.800000', '1.872000', '3.258000', '4.134000']
    """

    contract_parsed['fees_quantity'] = int(quotas[0][0])
    contract_parsed['amount'] = convert.to_float(financed_amount[0])
    contract_parsed['taxes'] = convert.to_float(percentages[1])
    contract_parsed['residual_value'] = None
    contract_parsed['initial_interest'] = interests[0]  # Get last element of interests
    contract_parsed['current_interest'] = interests[-1]  # Get last element of interests
    # contract_parsed['tae'] = convert.to_float(n_data[10])  #T.A.E

    return contract_parsed


def get_leasing_fees_parsed_with_bill_details_from_bills_details_json_resps(
        resp_bills_json: OrderedDict,
        leasing_fees_parsed: List[LeasingFeeParsed],
        ) -> List[LeasingFeeParsed]:


    for idx, fee_parsed in enumerate(leasing_fees_parsed):
        try:
            bills = [x for i, x in enumerate(resp_bills_json)
                     if date_funcs.convert_date_to_db_format(x['maturity']) == fee_parsed['operational_date']
                     and x['grossAmount']['amount'] == fee_parsed['fee_amount']]
            if bills:
                invoice_number = bills[0]['id'] # '182_F_17_0791_A_00192340' -> 17/A/00192340
                invoice_number_splited = invoice_number.split('_')  # '182_F_17_0791_A_00192340' -> 17/A/00192340 shown at bank
                invoice_number = '{}/{}/{}'.format(
                    invoice_number_splited[2],
                    invoice_number_splited[4],
                    invoice_number_splited[5])
                fee_parsed['invoice_number'] = invoice_number
                account_number = bills[0]['bill_detail']['participants'][1]['account']['number']

                fee_parsed['account_number'] = account_number

                fee_parsed['state'] = 'LIQUIDADO' if bills[0]['status'] == 'COLLECTED' else 'PENDIENTE'
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


def get_leasing_fees_parsed_from_installments_and_bills_json_resps(
        resp_installments_json: OrderedDict,
        resp_bills_json: OrderedDict,
        contract_parsed: LeasingContractParsed
        ) -> List[LeasingFeeParsed]:

    leasing_fees_parsed = []  # type: List[LeasingFeeParsed]

    for installment in resp_installments_json:

        # installment = OrderedDict([('id', '1'), ('maturity', '2017-05-12'), ('fiscalAmortization', OrderedDict([('currency', 'EUR'), ('amount', 2421.14)])), ('amortization', OrderedDict([('currency', 'EUR'), ('amount', 2421.14)])), ('interest', OrderedDict([('currency', 'EUR'), ('amount', 243.31)])), ('installmentPlan', OrderedDict([('netAmount', OrderedDict([('currency', 'EUR'), ('amount', 2664.45)])), ('grossAmount', OrderedDict([('currency', 'EUR'), ('amount', 3223.98)]))])), ('rate', OrderedDict([('currency', 'EUR'), ('amount', 559.53)])), ('pendingAmount', OrderedDict([('currency', 'EUR'), ('amount', 213553.86)])), ('installmentType', 'INSTALLMENT'), ('totalInsurancesAmount', [OrderedDict([('currency', 'EUR'), ('amount', 0.0)])])])
        # bills =
        fee_parsed = {}  # type: LeasingFeeParsed

        installment_id = installment['id']
        installment_pending_amount = installment['pendingAmount']['amount']
        installment_amount = installment['installmentPlan']['grossAmount']['amount']

        installment_maturity = installment['maturity']
        operational_date = date_funcs.convert_date_to_db_format(installment_maturity) # '2017-05-12'
        hashbase = 'BBVA{}/{}-{}-{}-{}'.format(
            contract_parsed['contract_reference'],
            installment_id,  # fee_number
            operational_date,  # operational_date
            installment_amount,  # fee_amount
            installment_pending_amount,  # pending_repayment
        )
        keyvalue = hashlib.sha256(hashbase.encode()).hexdigest().strip()

        fee_parsed['fee_reference'] = "{}/{}".format(contract_parsed['contract_reference'], installment_id)
        fee_parsed['fee_number'] = installment['id']
        fee_parsed['operational_date'] = operational_date
        fee_parsed['currency'] = installment['pendingAmount']['currency']
        fee_parsed['financial_repayment'] = installment['amortization']['amount']
        fee_parsed['financial_performance'] = installment['interest']['amount']
        fee_parsed['insurance_amount'] = installment['totalInsurancesAmount'][0]['amount'] # seguro, always 0.00
        fee_parsed['fee_type'] = 'CUOTA' if installment['installmentType'] == 'INSTALLMENT' else None
        fee_parsed['amount'] = installment['installmentPlan']['netAmount']['amount']  # cuota neta
        fee_parsed['taxes_amount'] = installment['rate']['amount']  # impuesto
        fee_parsed['fee_amount'] = installment_amount  # cuota bruta
        fee_parsed['pending_repayment'] = installment_pending_amount  # capital vivo
        fee_parsed['keyvalue'] = keyvalue

        fee_parsed['statement_id'] = None
        fee_parsed['contract_id'] = None

        bills = [x for i, x in enumerate(resp_bills_json) if
                 x['maturity'] == installment['maturity'] and
                 x['grossAmount']['amount'] == installment_amount]
        if bills:
            fee_parsed['bill_id'] = bills[0]['id']

        leasing_fees_parsed.append(fee_parsed)

    return leasing_fees_parsed
