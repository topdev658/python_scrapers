import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1',
    'Referer': 'https://movil.bbva.es/apps/woody/client',
}


def worker(client, user):
    payload = {
        "authentication": {
            "consumerID": "00000031",
            "authenticationData": [
                {
                    "authenticationData": [
                        user['pass']
                    ],
                    "idAuthenticationData": "password"
                }
            ],
            "authenticationType": "02",
            "userID": "0019-0{}".format(user['id'])
        }
    }
    r = client.post(
        "https://servicios.bbva.es/ASO/TechArchitecture/grantingTickets/V02", json=payload)
    tsec = r.headers.get('tsec')
    acc = r.json()['user']['id']
    params = {
        'customer.id': acc,
        'showSicav': 'false',
        'showPending': 'true'
    }
    client.headers.update({
        'tsec': tsec
    })
    r = client.get(
        'https://servicios.bbva.es/ASO/financial-overview/v1/financial-overview', params=params)
    return acc, r.json()


def main():
    users = [
        {
            'id': '77996629H',
            'pass': 'Jaume1'
        },
        {
            'id': '21482456L',
            'pass': 'K1197k'
        },
        {
            'id': '52811111y',
            'pass': 'Kk1197'
        }
    ]
    with ThreadPoolExecutor() as executor:
        with requests.Session() as client:
            client.headers.update(headers)
            fs = (executor.submit(worker, client, user) for user in users)
            for fut in as_completed(fs):
                fname, content = fut.result()
                with open('{}.json'.format(fname), 'w') as f:
                    json.dump(content, f, indent=4)
                    print('Saved', f.name)


if __name__ == "__main__":
    main()