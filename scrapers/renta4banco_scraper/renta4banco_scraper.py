import random
import time
from collections import OrderedDict
from typing import List, Tuple

from custom_libs.myrequests import MySession, Response
from project import settings as project_settings
from project.custom_types import (AccountScraped, MOVEMENTS_ORDERING_TYPE_ASC,
                                  ScraperParamsCommon, MainResult, DOUBLE_AUTH_REQUIRED_TYPE_OTP)
from scrapers._basic_scraper.basic_scraper import BasicScraper
from scrapers.renta4banco_scraper import parse_helpers

__version__ = '1.13.0'

__changelog__ = """
1.13.0
upd login()
1.12.1
added a todo
1.12.0
call basic_upload_movements_scraped with date_from_str
1.11.0
login: 2FA detector
1.10.0
login: upd
1.9.0
upg login method
parse_helpers: upg get_organization_title
1.8.1
parse_helpers: fixed typing
1.8.0
login: upd
1.7.0
use basic_new_session
upd type hints
fmt
1.6.0
use basic_get_date_from
1.5.0
parse_helpers: get_movements_parsed_mi_patrimonio: fixed due to changed layout
parse_helpers: regexps for raw string when necessary (suppress linter weak warns) 
process_contract -> process_company
alias requests -> myrequests
more type hints
1.4.0
changed login url
1.3.0
basic_movements_scraped_from_movements_parsed: new format of the result 
1.2.0
process_account_mi_patrimonio
1.1.0
parse_helpers: fixed acc currency
1.0.0
init
"""


# TODO TEST ON SEVERAL ACCOUNTS
class Renta4BancoScraper(BasicScraper):
    scraper_name = 'Renta4BancoScraper'

    def __init__(self,
                 scraper_params_common: ScraperParamsCommon,
                 proxies=project_settings.DEFAULT_PROXIES) -> None:
        super().__init__(scraper_params_common, proxies)
        random.seed(int(time.time()))
        self.req_proxies = [random.choice(self.req_proxies)]  # one proxy to use

    def login(self) -> Tuple[MySession, Response, bool, bool, str]:
        s = self.basic_new_session()

        resp_init = s.get(
            'https://www.r4.com/login',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        s.cookies.set('at_check', 'true')
        s.cookies.set('s_cc', 'true')
        s.cookies.set('LOGINCOMBO', '0')

        req_json_headers = self.basic_req_headers_updated({
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.r4.com/login'
        })

        # To get new cookies. The resp is empty
        _resp_token_empty = s.get(
            'https://www.r4.com/login/libs/granite/csrf/token.json',
            headers=req_json_headers,
            proxies=self.req_proxies
        )

        # Expect
        # {"value":"ENCAAAAAAWo9iL8H4/m8KXiYXhbWW66IiasU1wFLJvHghtX0Bv7uzpYz+G+p9zh2MfVBTpxStIxul8OoExk6fzyHDA+6M6jwTvgQD7aZaGl59icrGOABA==",
        # "status":"ok"}
        # OR
        # {"value":"","status":"ko"}
        resp_session_cookie = s.get(
            'https://www.r4.com/content/rentabanco/servlet.getCookie.json?cookieName=SESION_LOGADA',
            headers=req_json_headers,
            proxies=self.req_proxies
        )

        session_cookie = resp_session_cookie.json().get('value')
        if session_cookie is None:
            return s, resp_session_cookie, False, False, "Can't get session_cookie"
        if session_cookie:
            s.cookies.set('JSESSIONID', '"{}"'.format(session_cookie))

        req_login_params = OrderedDict([
            ('USUARIO', self.username_second),
            ('PASSWORD', self.userpass),
            ('EF_DNI', self.username),
            ('idSession', ''),
            ('captcha', ''),
            ('pag', '0'),
            ('particula', 'xml_webnolog'),
            ('geo', '0.0;0.0'),
            # ('ip', check_ip.get_current_ip(self.req_proxies))
            ('redirect', "https://www.r4.com/portal?"),
            ('api', 'true')
        ])

        resp_logged_in = s.post(
            'https://www.r4.com/content/rentabanco/servlet/_jcr_content.login.json',
            data=req_login_params,
            headers=req_json_headers,
            proxies=self.req_proxies
        )

        reason = ''
        is_credentials_error = '[10119] Datos incorrectos' in resp_logged_in.text
        is_logged = '"SessionID"' in resp_logged_in.text

        if 'OTP_LOGIN_INI' in resp_logged_in.text:
            reason = DOUBLE_AUTH_REQUIRED_TYPE_OTP
            is_logged = False

        if not is_logged:
            return s, resp_logged_in, is_logged, is_credentials_error, reason

        # Parses [{"response":"ok","errorCode":[1],"uRLTrasLogin":["TX=goto&FWD=FORM_MIFID"],
        # "SessionID":["5i...2r;ENCAAAAAAWS7ku0/xpQ..kqCg==;ENCAAAAAAVY36Uw....4A=="],"errorMsg":["ok"]}]
        session_params = resp_logged_in.json()[0]['SessionID'].split(';')
        s.cookies.set('CTX', session_params[0])
        s.cookies.set('JSESSIONID', '"{}"'.format(session_params[1]))
        s.cookies.set('SESION_LOGADA', session_params[2])

        resp_pos_global = s.get(
            'https://www.r4.com/portal?TX=goto&FWD=MAIN10&PAG=0',
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        return s, resp_pos_global, is_logged, is_credentials_error, ''

    def process_company(self, s: MySession, resp_pos_global: Response) -> bool:
        organization_title = parse_helpers.get_organization_title(resp_pos_global.text)

        accounts_list_url = 'https://www.r4.com/portal?TX=goto&FWD=MWLIMOP&PORTLET=MWH002'
        accounts_list_resp = s.get(
            accounts_list_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        accounts_parsed = parse_helpers.get_accounts_parsed(accounts_list_resp.text)
        self.logger.info('Contract {} has {} account(s): {}'.format(
            organization_title,
            len(accounts_parsed),
            accounts_parsed)
        )

        if not accounts_parsed:
            self.logger.warning('{}: suspicious results: no accounts_parsed. Pls, check the website'.format(
                organization_title
            ))

        accounts_scraped = [
            self.basic_account_scraped_from_account_parsed(organization_title, acc_parsed)
            for acc_parsed in accounts_parsed
        ]

        self.basic_upload_accounts_scraped(accounts_scraped)
        self.basic_log_time_spent('GET BALANCES')

        results = []  # type: List[bool]
        # not tested on several accounts, use serial processing in this case
        for i, account_scraped in enumerate(accounts_scraped):
            res = self.process_account_mi_patrimonio(s, account_scraped, i)
            results.append(res)
        return all(results)

    def process_account_mi_patrimonio(self, s: MySession,
                                      account_scraped: AccountScraped, ix: int) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)
        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # switch to account if several accounts found
        if ix > 0:
            # use 97204043 from iban ES5400830001180097204043
            req_url = 'https://www.r4.com/portal?TX=multicuenta&OPC=3&FAV={}&PAG=14&HOJA=7'.format(
                fin_ent_account_id[-9:]
            )
            # probably, it affects session tracker at server side
            # to get related movements then
            # the response will not be used
            # keep to for debug purposes
            resp_switch_to_acc = s.get(
                req_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        # TODO IMPL
        #  VB:
        #  From 04/10, recent movs (01/10) are available on Mi partimonio -> Inicio -> Resumen -> Saldo en eur -> Liquidado / Disponible
        #  but no date filter available there and there are no movs older than 01/10
        #  Date filter available on Mi partimonio -> Informes y extractos -> Movimientos entre fechas
        #  but max allowed date is 30/09.
        #  So, need to merge recent and filtered movs to get all necessary movements

        # No dates filter (Resumen -> Saldo en eur -> Liquidado / Disponible)
        # just extract all available
        req_mov_url = 'https://www.r4.com/portal?TX=patrimonio&STD=6&ISIN={}&PAG=6&HOJA=1'.format(
            account_scraped.Currency
        )

        resp_mov = s.get(
            req_mov_url,
            headers=self.req_headers,
            proxies=self.req_proxies
        )

        movements_parsed = parse_helpers.get_movements_parsed_mi_patrimonio(resp_mov.text,
                                                                            account_scraped.Currency)
        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    # TODO UNUSED now, but it is more general approach
    #  NOT TESTED ON REAL CASES WITH SEVERAL ACCOUNTS
    def process_account(self, s: MySession,
                        account_scraped: AccountScraped, ix: int) -> bool:

        fin_ent_account_id = account_scraped.FinancialEntityAccountId
        date_from_str = self.basic_get_date_from(fin_ent_account_id)

        self.basic_log_process_account(fin_ent_account_id, date_from_str)

        # switch to account if several accounts found
        if ix > 0:
            # use 97204043 from iban ES5400830001180097204043
            req_url = 'https://www.r4.com/portal?TX=multicuenta&OPC=3&FAV={}&PAG=14&HOJA=7'.format(
                fin_ent_account_id[-9:]
            )
            # probably, it affects session tracker at server side
            # to get related movements then
            # the response will not be used
            # keep to for debug purposes
            resp_switch_to_acc = s.get(
                req_url,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

        date_to_str = self.date_to_str
        resp_mov = Response()
        for _ in range(3):
            d_to, m_to, y_to = date_to_str.split('/')
            d_from, m_from, y_from = date_from_str.split('/')

            req_mov_url = 'https://www.r4.com/portal'
            req_mov_params = {
                'TX': 'extractos',
                'OPC': '2',
                'PAG': '6',
                'HOJA': '3',
                'TK_EXTR': '1',
                'RET_CODE_ANT': 'INFORMES_Y_EXTRACTOS',
                'TX_ANT': 'goto',
                'CB_DIA_D': d_from,
                'CB_MES_D': m_from,
                'CB_ANNO_D': y_from,
                'FECHA_D': date_from_str,
                'CB_DIA_H': d_to,
                'CB_MES_H': m_to,
                'CB_ANNO_H': y_to,
                'FECHA_H': self.date_to_str,
            }

            resp_mov = s.get(
                req_mov_url,
                params=req_mov_params,
                headers=self.req_headers,
                proxies=self.req_proxies
            )

            if '[11528]' not in resp_mov.text:
                break

            # handle '[11528] Le informamos que la fecha hasta no debe ser superior 23 de julio de 2018'
            # when trying to scrape, for example, to 25/07/2018 and restriction is 23/07/2108 (some prev date),
            # it returns err without movs,
            # then get new date_to_str from the page and retry
            date_to_str = parse_helpers.get_date_to_str_from_page(resp_mov.text)
            if date_to_str == '':
                self.logger.error("Can't extract date_to_str from the page. Check the output:"
                                  "\n{}\nSKIP NOW.".format(resp_mov.text))
                return False

            self.logger.info("Got new date_to={} due to date restriction. "
                             "Retry with new params".format(date_to_str))
        else:
            self.logger.error("The website returns errors after several attempts. Check the output:"
                              "\n{}\nSKIP NOW.".format(resp_mov.text))
            return False

        movements_parsed = parse_helpers.get_movements_parsed(resp_mov.text)

        movements_scraped, _ = self.basic_movements_scraped_from_movements_parsed(
            movements_parsed,
            date_from_str,
            current_ordering=MOVEMENTS_ORDERING_TYPE_ASC
        )

        self.basic_log_process_account(fin_ent_account_id, date_from_str, movements_scraped)
        self.basic_upload_movements_scraped(
            account_scraped,
            movements_scraped,
            date_from_str=date_from_str
        )
        return True

    def main(self) -> MainResult:
        s, resp_logged_in, is_logged, is_credentials_error, reason = self.login()

        if is_credentials_error:
            return self.basic_result_credentials_error()

        if not is_logged:
            return self.basic_result_not_logged_in_due_reason(
                resp_logged_in.url,
                resp_logged_in.text,
                reason
            )

        self.process_company(s, resp_logged_in)

        self.basic_log_time_spent('GET MOVEMENTS')
        return self.basic_result_success()
