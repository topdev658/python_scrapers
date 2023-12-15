import re
from collections import OrderedDict
from typing import List

from custom_libs import convert
from custom_libs import extract
from project.custom_types import AccountParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT, MovementParsed

__version__ = '2.3.0'

__changelog__ = """
2.3.0
req_movs_i_params: upd req params
2.2.0
req_movs_i_params: upd req params
2.1.0
req_movs_i_params: upd req param 
2.0.0
new web
"""

EXTENDED_DESCRIPTION_DETAILS = OrderedDict([
    ('Nº Operação', 'txtNumOperacao'),
    ('Data/Hora', 'txtDataHora'),
    ('Montante', 'txtMontante'),
    ('Banco Ordenante', 'txtBancoTomador'),  # for movs with pos amount
    ('Banco Destinatário', 'txtBancoTomador'),  # for movs with neg amount
    ('Nome do Beneficiário', 'txtNomeBeneficiario'),
    ('Descritivo', 'txtSepaDescTRF'),
    ('Ref. Ordenante', 'txtSepaOrd'),
    ('BIC Swift', 'txtSepaDestBIC'),
    ('IBAN', 'txtSepaDestIBAN'),
    ('Morada', 'txtSepaAddress'),
])


def get_organization_title(resp_text: str) -> str:
    """Parses class="enterprise-profile">Perfil Empresarial - Lcc Trans Sending Limited (75672660)</div>
    to Lcc Trans Sending Limited
    """
    org_title = extract.re_first_or_blank(r'>Perfil Empresarial\s+-\s+(.*?)\(\d+\)<', resp_text)
    return org_title


def get_account_parsed(resp_text: str) -> AccountParsed:
    # 60_resp_account.html
    # PT50007900007567266010153
    account_no = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
        r'(?si)class="account-card__iban">(.*?)</div\s*>',
        resp_text
    ))
    # 6.915,13 EUR
    balance_currency = extract.text_wo_scripts_and_tags(extract.re_first_or_blank(
        r'(?si)Saldo contabilístico</label>(</div\s*>\s*<div.*?</div\s*>)',
        resp_text
    ))
    balance = convert.to_float(balance_currency)
    currency = balance_currency.strip().split(' ')[-1]
    account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
    # '07567266010001' - new val, '7567266010001' - old val
    fin_ent_account_id = extract.re_first_or_blank('data-card-id="(.*?)">', resp_text)

    account_parsed = {
        'account_no': account_no,
        'financial_entity_account_id': fin_ent_account_id,
        'account_type': account_type,
        'balance': balance,
        'currency': currency,
    }

    return account_parsed


def get_viewstategenerator_param(resp_text: str) -> str:
    # DBCE14BC
    viewstategenerator_param = extract.re_first_or_blank(
        'id="__VIEWSTATEGENERATOR" value="(.*?)"',
        resp_text
    )
    return viewstategenerator_param


def get_osvstate_param(resp_text: str) -> str:
    # from movs
    osvs_from_movs_page = re.findall(r'OsJSONUpdate\({"hidden":{"__OSVSTATE":"(.*?)"', resp_text)
    if osvs_from_movs_page:
        return osvs_from_movs_page[-1]
    osv_from_acc_page = extract.re_first_or_blank(
        r"\('input\[name=__OSVSTATE\]'\).val\('(.*?)'",
        resp_text
    )
    return osv_from_acc_page


def req_movs_recent_params(osvstate_param: str, viewstategenerator_param: str) -> OrderedDict:
    req_params = OrderedDict([
        ('__EVENTTARGET',
         'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtRefreshLnk'),
        ('__EVENTARGUMENT', ''),
        ('__OSVSTATE', osvstate_param),
        ('__VIEWSTATE', ''),
        ('__VIEWSTATEGENERATOR', viewstategenerator_param),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn1$EuroBIC_HB_Patterns_wt56$block$wt3',
            ''),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$EuroBIC_HB_Patterns_wtAccountDetail$block$wtTitle$EuroBIC_HB_Patterns_wt41$block$wtContent$AccountsCurrent_eWb_wt21$block$EuroBIC_Base_Patterns_wtIBAN_Email_Modal$block$wtmodal_wrapper$wt30$EuroBIC_Base_Patterns_wt6$block$wtContent$EuroBIC_HB_Patterns_wt16$block$wtValue$wtEmail_Input',
            ''),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wt8',
            '0'),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$SCA_eWB_wtSCAModal$block$EuroBIC_Base_Patterns_wtmodal$block$wtmodal_wrapper$EuroBIC_Base_Patterns_wt26$block$wtContent$EuroBIC_Base_Patterns_wtFormInputPIN$block$wtValue$EuroBIC_Base_Patterns_wt21$block$wtInputPassword$wtPasswordInput',
            ''),
        ('__AJAX',
         '1588,1071,EuroBIC_HB_Theme_wt8_block_wtMainContent_Common_eWb_wt55_block_EuroBIC_Base_Patterns_wt7_block_wtcolumn2_wtMainContent_WebPatterns_wt64_block_wtContent1_EuroBIC_Base_Patterns_wt20_block_wtRefreshLnk,0,0,0,0,0,0,')])
    return req_params


def req_movs_i_params(
        osvstate_param: str,
        viewstategenerator_param: str,
        date_from_str,
        date_to_str: str,
        page_ix: int) -> OrderedDict:
    eventtarget_param = (
        # FILTERED
        'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtDateFilter$block$wtActionRight$wt103'
        if page_ix == 1  # 1st page
        else 'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_Base_Patterns_wt51$block$wtItems$EuroBIC_HB_Patterns_wt131$block$wtNavigationNext$wt149'
    )

    ajax_param = (
        # Filter applied
        '1588,1196,EuroBIC_HB_Theme_wt8_block_wtMainContent_Common_eWb_wt55_block_EuroBIC_Base_Patterns_wt7_block_wtcolumn2_wtMainContent_WebPatterns_wt64_block_wtContent1_EuroBIC_Base_Patterns_wt20_block_wtLateLoadContent_AccountsCurrent_eWb_wt54_block_EuroBIC_HB_Patterns_wt1_block_wtFilter_EuroBIC_HB_Patterns_wtDateFilter_block_wtActionRight_wt103,465,1015,519,0,0,0,'
        if page_ix == 1
        else '1440,1196,EuroBIC_HB_Theme_wt8_block_wtMainContent_Common_eWb_wt55_block_EuroBIC_Base_Patterns_wt7_block_wtcolumn2_wtMainContent_WebPatterns_wt64_block_wtContent1_EuroBIC_Base_Patterns_wt20_block_wtLateLoadContent_AccountsCurrent_eWb_wt54_block_EuroBIC_Base_Patterns_wt51_block_wtItems_EuroBIC_HB_Patterns_wt131_block_wtNavigationNext_wt149,1040,1321,551,0,1328,1055,'
    )

    dates_from_to_param = '{} - {}'.format(date_from_str, date_to_str)

    req_params = OrderedDict([
        ('__EVENTTARGET', eventtarget_param),
        ('__EVENTARGUMENT', ''),
        ('__OSVSTATE', osvstate_param),
        ('__VIEWSTATE', ''),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtDateFilter$block$wt8',
            'off'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtOrderTypeFilter_Others$block$wt8',
            'off'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtAmountFilter$block$wt8',
            'off'),
        ('__VIEWSTATEGENERATOR', viewstategenerator_param),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn1$EuroBIC_HB_Patterns_wt56$block$wt3',
            ''
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$EuroBIC_HB_Patterns_wtAccountDetail$block$wtTitle$EuroBIC_HB_Patterns_wt41$block$wtContent$AccountsCurrent_eWb_wt21$block$EuroBIC_Base_Patterns_wtIBAN_Email_Modal$block$wtmodal_wrapper$wt30$EuroBIC_Base_Patterns_wt6$block$wtContent$EuroBIC_HB_Patterns_wt16$block$wtValue$wtEmail_Input',
            ''
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtDateFilter$block$wtContent$EuroBIC_HB_Patterns_wt54$block$wtInputCalendar$wt138',
            dates_from_to_param
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtOrderTypeFilter_Others$block$wtContent$wtComboOthersGroup',
            '__ossli_0'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtAmountFilter$block$wtContent$EuroBIC_Base_Patterns_wt167$block$wtInputToMask$wtMinAmountInput',
            '0.00'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_HB_Patterns_wt1$block$wtFilter$EuroBIC_HB_Patterns_wtAmountFilter$block$wtContent$EuroBIC_Base_Patterns_wt50$block$wtInputToMask$wtMaxAmountInput',
            '0.00'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wtContent1$EuroBIC_Base_Patterns_wt20$block$wtLateLoadContent$AccountsCurrent_eWb_wt54$block$EuroBIC_Base_Patterns_wtEmailModal$block$wtmodal_wrapper$Email_eWB_wt166$block$RichWidgets_wt6$block$wtMainContent$wtEmail_Input',
            ''
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$Common_eWb_wt55$block$EuroBIC_Base_Patterns_wt7$block$wtcolumn2$wtMainContent$WebPatterns_wt64$block$wt8',
            '0'
        ),
        (
            'EuroBIC_HB_Theme_wt8$block$wtMainContent$SCA_eWB_wtSCAModal$block$EuroBIC_Base_Patterns_wtmodal$block$wtmodal_wrapper$EuroBIC_Base_Patterns_wt26$block$wtContent$EuroBIC_Base_Patterns_wtFormInputPIN$block$wtValue$EuroBIC_Base_Patterns_wt21$block$wtInputPassword$wtPasswordInput',
            ''
        ),
        ('__AJAX', ajax_param),

    ])
    return req_params


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    """
    Parses
    <tr onclick="onclick">
        <td class="TableRecords_OddLine">26-11-2021</td>
        <td class="TableRecords_OddLine"><div  id="EuroBIC_HB_Theme_wt8_block_wtMainContent_Common_eWb_wt55_block_EuroBIC_Base_Patterns_wt7_block_wtcolumn2_wtMainContent_WebPatterns_wt64_block_wtContent1_EuroBIC_Base_Patterns_wt20_block_wtLateLoadContent_AccountsCurrent_eWb_wt54_block_wtTransactionsTable_ctl05_wtTooltip">Dep. Numer&#225;rio RE...</div ><script>$('#EuroBIC_HB_Theme_wt8_block_wtMainContent_Common_eWb_wt55_block_EuroBIC_Base_Patterns_wt7_block_wtcolumn2_wtMainContent_WebPatterns_wt64_block_wtContent1_EuroBIC_Base_Patterns_wt20_block_wtLateLoadContent_AccountsCurrent_eWb_wt54_block_wtTransactionsTable_ctl05_wtTooltip').tooltipster({
            content: $('<span>Dep. Numerário REF 27147</span>' ),
            trigger: 'hover',
            position: 'top',
            maxWidth: '',
            theme: 'tooltip_style'
            });</script>
        </td>
        <td class="TableRecords_OddLine"><div  class="Text_right">9.050,00EUR</div ></td>
        <td class="TableRecords_OddLine"><div  class="Text_right">51.986,64EUR</div ></td>
        <td class="TableRecords_OddLine"></td>
    </tr>

    see 70_resp_movs.html
    """
    movements_parsed_desc = []  # type: List[MovementParsed]
    trs = re.findall(r'(?si)<tr onclick=\\"onclick\\">.*?<\\/tr>', resp_text)
    for tr in trs:
        cells = [extract.remove_tags(td) for td in re.findall(r'(?si)<td.*?<\\/td>', tr)]
        operation_date = cells[0]  # 26-11-2021
        value_date = operation_date  # no info
        # simple detector for incorrect dates
        if '-' not in operation_date:
            continue

        # Unescapes 'Com TRF créd SEPA+ net\\/app\\\\x3e=100.000'
        # to 'Com TRF créd SEPA+ net/app>=100.000'
        descr = extract.unescape_html_from_json(extract.re_first_or_blank(r"(?si)content: \$\('<span>(.*?)<", tr))

        amount = convert.to_float(cells[2])
        temp_balance = convert.to_float(cells[3])

        movement = {
            'operation_date': operation_date,
            'value_date': value_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance,
            # Not implemented for the new web (2021)
            # 'details_params_list': details_params_list,
            # 'id': '{}--{}'.format(extract.by_index_or_blank(details_params_list, 3), uuid.uuid4()),
            # 'has_extra_details': bool(details_params_list)
        }
        movements_parsed_desc.append(movement)

    return movements_parsed_desc


# Not used for the new web (2021)
def get_description_extended(resp_text: str, mov_parsed: MovementParsed) -> str:
    # Similar to AlphaBank
    description_extended = mov_parsed['description']

    for det_title, det_key in EXTENDED_DESCRIPTION_DETAILS.items():
        detail = extract.form_param(resp_text, det_key).strip()
        # overwrite one of shared details, depends of movement's sign
        if det_title == 'Banco Ordenante' and mov_parsed['amount'] < 0:
            detail = ''
        if det_title == 'Banco Destinatário' and mov_parsed['amount'] >= 0:
            detail = ''
        msg = '{}: {}'.format(det_title, detail).strip()

        description_extended += ' || {}'.format(msg)

    return description_extended.strip()
