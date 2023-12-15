import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote

import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
}

access = {
    'First': '20690683',
    'Second': 'TPFBBVA'.upper(),
    'Last': 'TPFB4788'
}


def sign_in(req):
    auth_data = {
        "authentication": {
            "consumerID": "00000311",
            "userID": "00230001" + access["First"] + access['Second'],
            "authenticationType": "16",
            "authenticationData": [
                {
                    "authenticationData": [access['Last']],
                    "idAuthenticationData": "password"
                }
            ],
        },
        "backendUserRequest": {
            "userId": "",
            "accessCode": "00230001" + access["First"] + access['Second'],
            "dialogId": "",
        },
    }
    r = req.post(
        "https://www.bbvanetcash.com/ASO/TechArchitecture/grantingTickets/V02", json=auth_data)
    if r.status_code == 403:
        return False
    tsec = r.headers['tsec']

    headers = {
        "aso_sso_params": '{{"tsec":"{}","origen":"00000311"}}'.format(tsec)}
    req.get(
        "https://netcash.bbva.es/SESKYOP/kyop_mult_web_pub/resources-new/images/common/loadingNBbva.gif*", headers=headers)

    req.cookies.update({
        'LoginGT': 'true',
    })

    data = {
        'tsec': ''
    }
    r = req.post(
        "https://netcash.bbva.es/SESKYOP/kyop_mult_web_kyoppresentation_01/master/getLiteUfeMasterRequest.json", data=data)

    tsec = r.json()["data"][0]["listaSpainTsec"][0]["lTsecLocal"][1]["tsec"]
    cid = r.json()["data"][0]["listaSpainTsec"][0]["customerId"]

    req.headers.update({
        'tsec': tsec
    })
    return cid


def get_accounts(req):
    params = {
        "paginationKey": 1,
        "pageSize": 50
    }
    r = req.get(
        "https://www.bbvanetcash.com/ASO/netCashAccounts/V01", params=params)
    with open('Accounts.json', 'w', encoding='utf-8-sig') as f:
        json.dump(r.json(), f, indent=4, ensure_ascii=False)
        print(f'Downloaded --> {f.name}')
    return [
        {
            'id': x['id'],
            'currentBalance':x['currentBalance']['amount'],
            'availableBalance':x['availableBalance']['amount']
        }
        for x in r.json()['items']
    ]


def get_trxs(req, cid, account):
    data = {
        "accountContracts": [
            {
                "account": {
                    "currentBalance": {
                        "accountingBalance": {
                            "amount": account['currentBalance'],
                            "currency": {
                                "code": "EUR"
                            },
                        },
                        "availableBalance": {
                            "amount": account['availableBalance'],
                            "currency": {
                                "code": "EUR"
                            },
                        },
                    }
                },
                "contract": {
                    "id": account['id']
                },
            }
        ],
        "customer": {
            "id": cid
        },
        "filter": {
            "dates": {
                "from": "2023-3-1",
                "to": "2023-3-30"
            }
        },
        "orderField": "DATE_FIELD",
        "orderType": "DESC_ORDER",
        "searchType": "SEARCH",
    }
    params = {
        'pageSize': 45
    }
    r = req.post('https://www.bbvanetcash.com/ASO/accountTransactions/V02/accountTransactionsAdvancedSearch',
                 params=params, json=data)

    with open('Transactions.json', 'w', encoding='utf-8-sig') as f:
        json.dump(r.json(), f, indent=4, ensure_ascii=False)
        print(f'Downloaded --> {f.name}')
    return r.json()['accountTransactions']


def check_pdfs(req, pdfs):
    data = {
        "itemsActionsIn": [
            {
                "id": unquote(item),
            } for item in pdfs
        ]
    }
    r = req.post(
        'https://www.bbvanetcash.com/ASO/transactionVirtualMailsActions/V01/listTransactionBankingVirtualMailsActions', json=data)
    # Now we have received a list of the PDF files which can be downloaded!
    return [x['itemsBankingVirtualMail'][0]
            ['bankingVirtualDocument']['href'][1:] for x in r.json()['items']]


def download_pdf(req, pdf):
    return req.get(f"https://www.bbvanetcash.com/ASO/{pdf}").content


def main():
    with requests.Session() as req:
        req.headers.update(headers)
        cid = sign_in(req)
        if cid:
            accounts = get_accounts(req)
            print(f'Found {len(accounts)} Accounts')
            txs = get_trxs(req, cid, accounts[0])
            if txs:
                print(f'Found {len(txs)} Transaction(s)')
                pdfs = [x['document']['href'].split(
                    '/', 4)[3]for x in txs]
                pdfs = check_pdfs(req, pdfs)
                if pdfs:
                    print(f'Found {len(pdfs)} PDF(s)')
                    with ThreadPoolExecutor(max_workers=10) as executor:
                        fs = (executor.submit(download_pdf, req, pdf)
                              for pdf in pdfs)
                        for num, i in enumerate(as_completed(fs), start=1):
                            with open(f'{num}.pdf', 'wb') as f:
                                f.write(i.result())
                                print(f'Downloaded {f.name}')
                else:
                    print('No PDF(s) available for download!')
            else:
                print('No Transactions Found!')
        else:
            print('Unable to login. Check User/Pass')


if __name__ == "__main__":
    main()