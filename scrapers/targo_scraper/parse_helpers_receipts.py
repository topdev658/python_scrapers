import re
from datetime import datetime
from typing import List, Optional

from custom_libs import convert
from custom_libs import extract
from project.custom_types import CorrespondenceDocParsed, AccountScraped
from .custom_types import AccountForCorrespondence


def get_accounts_for_corr(resp_text: str,
                          accounts_scraped: List[AccountScraped]) -> List[AccountForCorrespondence]:
    """
    Uses account_scraped to set correct account_no and fin_ent_account_id
    Parses
        <option id="F_0.D" value="02160585600620000397">
            0620000397 CUENTA CORRIENTE DE USO PRO EN USD I GAMBASTAR SL
        </option>
    """
    accs_for_corr = []  # type: List[AccountForCorrespondence]
    form_html = extract.re_first_or_blank('(?si)<form id="P1:F".*?</form>', resp_text)
    options = re.findall("""(?si)<option id="F_0.D" value="([^"]+)">(.*?)</option>""", form_html)
    for opt in options:
        req_param = opt[0]
        accounts_scraped_filtered = [a for a in accounts_scraped if req_param in a.FinancialEntityAccountId]

        # not found yet... will use default '02160585600620000397'
        fin_ent_account_id = req_param
        if accounts_scraped_filtered:
            # found, set '02160585600620000397USD', need for corr ProductId
            fin_ent_account_id = accounts_scraped_filtered[0].FinancialEntityAccountId

        account_for_corr = AccountForCorrespondence(
            account_title=opt[1].strip(),
            req_param=req_param,
            fin_ent_account_id=fin_ent_account_id,
        )
        accs_for_corr.append(account_for_corr)
    return accs_for_corr


def get_correspondence_from_list(resp_text: str, account_for_corr: AccountForCorrespondence) -> List[
    CorrespondenceDocParsed]:
    corrs_desc = []  # type: List[CorrespondenceDocParsed]
    # Contains nested correspondence table
    corr_table = extract.re_first_or_blank(
        r'(?si)<div id="F2:expContent" class="a_blocfctl">\s*(<table.*?</table>)',
        resp_text
    )
    trs = re.findall('(?si)<tr.*?</tr>', corr_table)
    for tr in trs:
        cells = re.findall('(?si)<td.*?</td>', tr)
        if not cells:
            # header
            continue

        corr_type = extract.text_wo_scripts_and_tags(cells[1])  # file link text, Transferencia emitida
        pdf_link = extract.re_first_or_blank('href="(.*?)"', cells[1])
        corr_date_str = extract.text_wo_scripts_and_tags(cells[0])  # '07/10/2021'
        corr_date = datetime.strptime(corr_date_str, '%d/%m/%Y')

        # '<td class="p _c1 g _c1">INVERSIONES MARINAS DEL LAGO SA<br />PAGO FRA 402331,402334,402335 Y</td>'
        # -> 'INVERSIONES MARINAS DEL LAGO SA  PAGO FRA 402331,402334,402335 Y'
        descr = extract.text_wo_scripts_and_tags(cells[2].replace('<br />', '  '))

        amount = None  # type: Optional[float]
        amount_str = extract.text_wo_scripts_and_tags(cells[3]).strip()  # '-255.192,00 USD'
        if amount_str:
            amount = convert.to_float(amount_str)
        # trailing upper letters
        currency = extract.re_first_or_blank(r'[-+,.\d\s]+([A-Z]+)$', amount_str)

        corr = CorrespondenceDocParsed(
            type=corr_type,
            account_no=account_for_corr.fin_ent_account_id,
            operation_date=corr_date,
            value_date=None,
            amount=amount,
            currency=currency,
            descr=descr,
            extra={
                'pdf_link': pdf_link
            }
        )
        corrs_desc.append(corr)

    return corrs_desc
