# todo in progress, the request was blocked
# extracted from func 'process_account'
# not working...
def _get_movements_excel(self):
    req_headers['Referer'] = req1_url
    req_headers['Connection'] = 'keep-alive'
    req_headers['Upgrade-Insecure-Requests'] = '1'

    action_url = extract.re_first_or_blank(
        'name="FORM_RVIA_0" action="(.*?)"',
        resp1_process_acc.text
    )

    if not action_url:
        msg = "Error opening excel req of account {}".format(account_no)
        self.logger.error(msg)
        raise Exception(msg)

    req_xls_url = urllib.request.urljoin(
        resp1_process_acc.url,
        action_url
    )

    pan_param = extract.re_first_or_blank(
        "var toPrinterCuerpo = '(.*)' \+",
        resp1_process_acc.text
    ) + '<div id=DATOSPIE><table border="0" cellspacing="0" cellpadding="0" align=right><tr><td class="datocodeD"></td><td class="datocodeD"></td><td class="datocodeD"></td><td class="datocodeD"></td><td class="datocodeD"></td><td class="datocodeD"></td></tr></table><br><br></div>'

    req_xls_params = {
        'ISUM_OLD_METHOD': 'post',
        'ISUM_ISFORM': 'true',
        'FILENAME': 'movimientos.xls',
        'formato': 'htm',
        'PAN': ''  # pan_param
    }

    resp_xls = s.post(
        req_xls_url,
        params=req_xls_params,
        headers=req_headers,
        proxies=self.req_proxies,
        stream=True
    )

    movements_parsed = parse_helpers.parse_movements_from_resp_excel(resp_xls)
