import datetime
import re
import traceback
import urllib.parse
from typing import List, Tuple, Optional, Dict

from custom_libs import convert
from custom_libs import extract
from custom_libs import iban_builder
from project import settings as project_settings
from project.custom_types import AccountParsed, MovementParsed, ACCOUNT_TYPE_DEBIT, ACCOUNT_TYPE_CREDIT


def get_page_content_req_link(resp_text: str) -> str:
    # /portal/site/SogecashWeb/template.ASYNC/globalcash/?javax.portlet.tpst=c1c03cab4385048d34d08610c841240c&javax.portlet.begCacheTok=com.vignette.cachetoken&javax.portlet.endCacheTok=com.vignette.cachetoken&vgnextoid=ccb834f30a531210VgnVCM1000008c1442c0RCRD&service=Navigation&vgnextfmt=default&sgniUrl=%2Fsgw%2FNavigationServlet%3F_GOTO%3DListeComptables%26_NumeroPage%3D1&selectedSgniMenu=ccb834f30a531210VgnVCM1000008c1442c0RCRD&service=Navigation&sgniUrl="+encodeURIComponent('/sgw/NavigationServlet?_GOTO=ListeComptables&_NumeroPage=1')+"&selectedSgniMenu=ccb834f30a531210VgnVCM1000008c1442c0RCRD&portlet-name=PortletSGNI2

    link_raw = extract.re_first_or_blank(
        r'load\("(/portal/site/SogecashWeb/template.ASYNC/globalcash/.*?)",',
        resp_text
    )

    # replace encodeURIComponent
    to_quote = extract.re_first_or_blank(r'encodeURIComponent\((.*?)\)', link_raw)
    quoted = urllib.parse.quote_plus(to_quote)
    re.sub(r'''"+encodeURIComponent\(.*?\)+"''', '', link_raw)
    link_quoted = link_raw.replace('''"+encodeURIComponent({})+"'''.format(to_quote), quoted)
    return link_quoted


def get_movements_filtered_link(resp_text: str) -> Tuple[str, Optional[str]]:
    """
    :returns link and optional error str

    $.ajax({
          type: "POST",
          url: '/portal/site/SogecashWeb/template.RAW/action.process/globalcash/
          ?javax.portlet.action=true&javax.portlet.sync=fd62089716a8e3a136e1d0216032140c
          &javax.portlet.tpst=c1c03cab4385048d34d08610c841240c_ws_RW
          &javax.portlet.prp_c1c03cab4385048d34d08610c841240c=
          service%3DNavigation%26sgniUrl%3D%252Fsgw%252FNavigationServlet
          &javax.portlet.begCacheTok=com.vignette.cachetoken
          &javax.portlet.endCacheTok=com.vignette.cachetoken',
          data: objForm.serialize(),
          dataType: "html",
          success: function(data) {
        if (isSessionExpired()){
          document.location.reload();
        } else {
          var $currentTabs = $("#tabsContainerReleves
    """

    re_exp = r"""(?si)url:\s*'(.*?)'"""
    link = extract.re_first_or_blank(re_exp, resp_text)
    unique_links = set(re.findall(re_exp, resp_text))
    if len(unique_links) > 1:
        return '', 'get_movements_filtered_link: wrong parsing. Unable to continue'
    return link, None


def get_organization_title(resp_text: str) -> str:
    return ""


def get_accounts_dropdown_option_values(resp_text: str) -> Dict[str, str]:
    """
    :returns dict {fin_ent_account_id: dropdown_option_value}

    Parses:

    <table class="sgw_form_table"><tr>
      <td class="sgw_align_left">
        <div class="sgw_input_bloc sgw_position_top sgw_input_align_left "><label>Cuenta</label>
        <select    id="lstCompte" onChange="validComptePourEdition(
        document.frmReleves_V_c1c03cab4385048d34d08610c841240c.lstCompte.selectedIndex,
        document.frmReleves_V_c1c03cab4385048d34d08610c841240c, 'V_c1c03cab4385048d34d08610c841240c');"
        name="lstCompte"  class="sgw_input_select"><option value="1157203" selected >
            01080030200030059490 28 RIBERA DEL LOIRA SA
            </option><

            option value="1157209">
            01080030270030066222 330 AVDA DE ARAGON
            </option>

            <option value="1157204">
            01080030290030061254 330 AVENIDA DE ARAGON  S
            </option><option value="1157205">
            01080030230030061236 330 AVENIDA DE ARAGON SL
            </option><option value="1157206">
            01080030220030064910 BARDOL INVERSIONES SL
            </option><option value="1157212">
            01080030220030070903 GREF ALAMEDA PARK SL
            </option><option value="1157211">
            01080030250030070912 GREF ALAMEDA PARK SL
            </option><option value="1157200">
            01080030230030061806 RAMIREZ  EPGF  SL
            </option><option value="1157201">
            01080030260030061931 RAMIREZ EPGF SL SERVICE
            </option></select></div>
      </td>
    </tr></table>
    """

    dropdownids_to_finentids = re.findall(
        r'(?si)<option value="(\d{7})"[^>]*>\s*(\d{20})[^<]*</option>',
        resp_text
    )
    acc_to_drop_id = {fid: did for (did, fid) in dropdownids_to_finentids}
    return acc_to_drop_id


def get_accounts_parsed(resp_text: str, current_url: str) -> List[AccountParsed]:
    accounts_parsed = []
    accounts_htmls = re.findall('(?si)<tr.*?>(.*?)</tr>', resp_text)
    for acc_html in accounts_htmls:
        # ['01080030200030059490 - 28 RIBERA DEL LOIRA SA', 'EUR', '132 302,32', '25/09/2018']
        cells = [extract.remove_tags(c) for c in re.findall('(?si)<td.*?>(.*?)</td>', acc_html)]
        details_link = extract.re_first_or_blank('href="(.*?)"', acc_html)
        if len(cells) < 4 or not details_link:
            continue

        details_url = urllib.parse.urljoin(current_url, details_link)

        fin_ent_account_id = cells[0].split('-')[0].strip()
        balance = convert.to_float(cells[2])
        currency = cells[1]

        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT

        account_iban = iban_builder.build_iban('ES', fin_ent_account_id)
        account_parsed = {
            'account_no': account_iban,
            'financial_entity_account_id': fin_ent_account_id,
            'balance': balance,
            'account_type': account_type,
            'currency': currency,
            'details_url': details_url
        }
        accounts_parsed.append(account_parsed)

    return accounts_parsed


def _get_mov_date_obj(date_part_str, prev_date_obj, fin_ent_account_id, logger) -> datetime.datetime:
    """
    similar to caixa, but more strict - it expects prev_date explicitly

    '16/07' and modify to '16/07/2017'
    handle case if mov from previous year:
    if calculated date > current date then calc.year = curr.year - 1

    even using calculated year, possible case when 2016 (or less) will be calculated as 2017
    if date (day/mo) of prev year less than current date (day/mo)
    use additional checkups (direct extractions) in main code

    each next date should be <= prev date (descending ordering)
    """

    date_for_year_obj = prev_date_obj

    # first, try with current year
    # then do step back on exception
    # loop over 10 years to avoid infinite loop
    # on unexpected situation
    year = date_for_year_obj.year  # type: int
    for _ in range(10):
        date_str = date_part_str + "/" + str(year)
        try:
            date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y')
            if date_obj <= prev_date_obj:
                break
            year -= 1
            continue
        # wrong year, most probable reason: 29/02
        # move to one previous year to find leap year
        except ValueError as exc:
            if 'day is out of range for month' in str(exc):
                year -= 1
                logger.info(
                    'Handled exception: "{}" for predicted date {}. '
                    'Set previous year to get (probably) correctly predictied date: {}'.format(
                        exc,
                        date_str,
                        year
                    )
                )
                continue
        except:
            raise Exception(
                "{}: can't get_mov_date_obj from date_str={} and year={}. "
                "NEED TO HANDLE THIS CASE IN THE CODE.\n{}".format(
                    fin_ent_account_id,
                    date_str,
                    date_for_year_obj.year,
                    traceback.format_exc()
                )
            )
    else:
        raise Exception(
            "{}: calculate correct year. from date_part_str={} and prev_date_obj={}. "
            "NEED TO HANDLE THIS CASE IN THE CODE".format(
                fin_ent_account_id,
                date_part_str,
                prev_date_obj
            ))

    return date_obj


def get_movements_parsed(fin_ent_account_id: str,
                         resp_text: str,
                         init_temp_balance: float,
                         prev_date_obj: datetime.datetime,
                         logger) -> Tuple[List[MovementParsed], float, datetime.datetime]:
    """
    Returns tuple(list of movements_parsed, last temp balance (for pagination), last_mov_date_obj)
    Descending ordering
    """
    movements_parsed = []
    movements_htmls = re.findall('(?si)<tr.*?>(.*?)</tr>', resp_text)

    prev_op_date_obj = prev_date_obj
    prev_val_date_obj = prev_op_date_obj

    temp_balance = init_temp_balance

    # oredering desc (most recent is the first)
    for ix, mov_html in enumerate(movements_htmls):
        # ['01080030200030059490 - 28 RIBERA DEL LOIRA SA', 'EUR', '132 302,32', '25/09/2018']
        cells = [extract.remove_tags(c) for c in re.findall('(?si)<td.*?>(.*?)</td>', mov_html)]
        if len(cells) < 4:
            continue

        try:
            operation_date_dm = cells[1]  # 07/09, year will be calculated
            value_date_dm = cells[2]  # 07/09, year will be calculated

            description = cells[3]  # CHG A152/016/Com. Trans.
            if cells[4]:
                amount = -convert.to_float(cells[4])  # type: Optional[float]   # DEBE
            elif cells[5]:
                amount = +convert.to_float(cells[5])  # 0,60, HABER
            else:
                amount = None  # will be handled below
            if amount is None:
                continue
            if not all([operation_date_dm, value_date_dm, description]):
                continue

            op_date_obj = _get_mov_date_obj(operation_date_dm, prev_op_date_obj, fin_ent_account_id, logger)
            val_date_obj = _get_mov_date_obj(value_date_dm, prev_val_date_obj, fin_ent_account_id, logger)

            prev_op_date_obj = op_date_obj
            prev_val_date_obj = val_date_obj

        except Exception as e:
            logger.error("{}: {}: {}".format(fin_ent_account_id, cells, e))
            continue

        # temp_balance unknown, should be calculated
        mov_parsed = {
            'operation_date': op_date_obj.strftime(project_settings.SCRAPER_DATE_FMT),
            'value_date': val_date_obj.strftime(project_settings.SCRAPER_DATE_FMT),
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance
        }

        temp_balance = round(temp_balance - amount, 2)
        movements_parsed.append(mov_parsed)

    return movements_parsed, temp_balance, prev_op_date_obj


def reorder_movements_and_recalculate_temp_balances(
        movements_parsed: List[MovementParsed]) -> List[MovementParsed]:
    """
    >>> wrong_ordered = [{'temp_balance': 3, 'amount': 2}, {'temp_balance': 1, 'amount': 1}]
    >>> reordered = reorder_movements_and_recalculate_temp_balances(wrong_ordered)
    >>> reordered == [{'temp_balance': 3, 'amount': 1}, {'temp_balance': 2, 'amount': 2}]
    True
    """
    # we expect temp_balance calculated for DESC ordering
    temp_balance = movements_parsed[0]['temp_balance']
    movements_parsed_reordered = []
    for mov in movements_parsed[::-1]:
        m = mov.copy()  # avoid unexpected behavior
        m['temp_balance'] = temp_balance
        temp_balance = round(temp_balance - m['amount'], 2)
        movements_parsed_reordered.append(m)
    return movements_parsed_reordered
