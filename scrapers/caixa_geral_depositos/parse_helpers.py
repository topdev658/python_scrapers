import re
from typing import Dict, List, Tuple

from custom_libs import convert
from custom_libs import extract
from custom_libs.scrape_logger import ScrapeLogger
from project.custom_types import (
    ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
)

# Descrição 	27123
# Montante 	9.042,68 EUR
# Data valor 	10-08-2019
# Data do movimento 	10-08-2019 16:48
# Tipo de movimento 	Crédito
# Operação efectuada em 	Caixadirecta On-line
# Nº de Transferência 	135107252
# Montante da transferência 	9.042,68 EUR
# Montante original 	9.042,68 EUR
# Nome Ordenante 	DEEPAK BAHADUR KC
# Finalidade 	Outras
# Saldo contabilístico após movimento 	56.191,10 EUR
# Saldo disponível após movimento 	56.191,10 EUR

# Descrição 	Agents LCC to Refunds
# Montante 	20.000,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019 16:41
# Tipo de movimento 	Débito
# Operação efectuada em 	Caixadirecta Empresas
# Conta destino 	0127058574130
# Nº de Transferência 	135052944
# Montante da transferência 	20.000,00 EUR
# Montante original 	20.000,00 EUR
# Finalidade 	Outras
# Comentário 	Agents LCC to Refunds
# Descritivo conta destino 	Agents LCC Refunds
# Saldo contabilístico após movimento 	19.414,76 EUR
# Saldo disponível após movimento 	19.414,76 EUR

# Descrição 	DEPOSITO
# Montante 	3.530,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019
# Tipo de movimento 	Crédito
# Nome do interveniente 	SUSANA MARIA ARANTES LOUREIRO
# Operação efectuada em 	Agência
# Saldo contabilístico após movimento 	39.414,76 EUR
# Saldo disponível após movimento 	39.414,76 EUR

# Descrição 	Agents LCC to Refunds
# Montante 	20.000,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019 16:41
# Tipo de movimento 	Débito
# Operação efectuada em 	Caixadirecta Empresas
# Conta destino 	0127058574130
# Nº de Transferência 	135052944
# Montante da transferência 	20.000,00 EUR
# Montante original 	20.000,00 EUR
# Finalidade 	Outras
# Comentário 	Agents LCC to Refunds
# Descritivo conta destino 	Agents LCC Refunds
# Saldo contabilístico após movimento 	19.414,76 EUR
# Saldo disponível após movimento 	19.414,76 EUR

# Descrição 	TRF MARIA LURDES SANT
# Montante 	300,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019 14:30
# Tipo de movimento 	Crédito
# Local 	R Constituicao Republica
# Nome Ordenante 	MARIA LURDES SANTOS
# N.º Identificação SIBS 	22922185312544
# Saldo contabilístico após movimento 	17.582,13 EUR
# Saldo disponível após movimento 	17.582,13 EUR

# Descrição 	TFI LARISSA NAIARE SA
# Montante 	600,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019
# Tipo de movimento 	Crédito
# Nome Ordenante 	LARISSA NAIARE SANTOS
# Banco Ordenante 	BANCO COMERCIAL PORTUGUES
# Swift Ordenante 	BCOMPTPL
# Saldo contabilístico após movimento 	72.250,97 EUR
# Saldo disponível após movimento 	72.250,97 EUR

# Descrição 	TRF WASEEM ASHRAF
# Montante 	2.000,00 EUR
# Data valor 	09-08-2019
# Data do movimento 	09-08-2019
# Tipo de movimento 	Crédito
# Nome Ordenante 	WASEEM ASHRAF
# Banco Ordenante 	BANCO ACTIVOBANK S.A.
# Swift Ordenante 	ACTVPTPL
# Informação Adicional 	27128
# Saldo contabilístico após movimento 	70.200,97 EUR
# Saldo disponível após movimento 	70.200,97 EUR

EXTENDED_DESCRIPTION_DETAILS = [
    # 'Descrição',  # descr
    # 'Montante',   # amount str like '6.097,99\nEUR'
    # 'Data valor',
    # 'Data do movimento',  # sometimes with time
    'Tipo de movimento',
    'Local',
    'Nome do interveniente',
    'Operação efectuada em',
    'Conta destino',
    'Nº de Transferência',
    'Nome Ordenante',
    'Banco Ordenante',
    'Swift Ordenante',
    'N.º Identificação SIBS',
    # 'Montante da transferência',
    # 'Montante original',
    'Finalidade',
    'Comentário',
    'Descritivo conta destino',
    'Informação Adicional',
    # 'Saldo contabilístico após movimento',
    # 'Saldo disponível após movimento',
]


def get_view_state_param(resp_text: str) -> str:
    view_state_param = extract.form_param(resp_text, 'javax.faces.ViewState')
    return view_state_param


def get_date_fields(resp_text: str) -> Tuple[str, str]:
    """Parses
    if(!consultaMovimentos_kid_j_idt3012_checkDate(day)) return false;
    -> consultaMovimentos:kid_j_idt3012_inputField
    return (date_from_field, date_to_field)
    """
    ids = re.findall(r'consultaMovimentos_kid_j_idt(\d+)_checkDate\(day\)', resp_text)
    param_pattern = 'consultaMovimentos:kid_j_idt{}_inputField'
    return param_pattern.format(ids[0]), param_pattern.format(ids[1])


def get_accounts_wo_iban_parsed(resp_text: str) -> List[dict]:
    """Parses
    <tr style="cursor: pointer;"
        onmouseover="JavaScript:this.className='row_Over'" onmouseout="JavaScript:this.className='';"
        onclick="clickEvent('PGIdEUR400_0','A');">

        <td class="txt_tableinnertable linhabottom">
        <span title="0127055801930">0127055801930</span> <br />
        <span title="Conta Extracto">Conta Extracto</span></td>

        <td class="txt_tableinnertable linhabottom">
        <span title="AVENIDA DA REPUBLICA - LISBOA">AVENIDA DA REPUBLICA - LISBOA</span></td>

        <td class="alignright linhabottom">
            <p class="text_tab_valor">23.342,79
            </p>
        </td>
        <td class="txt_tableinnertable alignright linhabottom">15,36%
        </td>
        <td id="PGIdEUR400_0" class="txt_tableinnertable alignrighttext linhabottom">
           <a href="/ceb/private/contasaordem/consultaSaldosMovimentos.seam?account=PT+00350127055801930EUR0&...>
        <img src="..." /></a>
        </td>
    </tr>
    """
    accounts_parsed_wo_iban = []  # type: List[dict]

    trs = re.findall(
        '(?si)<tr.*?</tr>',
        extract.re_first_or_blank(
            '(?si)<tr id="detailAEUR0"[^>]+>(.*?)<tr class="footertable_valores">',
            resp_text
        )
    )

    for tr in trs:
        tds = re.findall('(?si)<td.*?</td>', tr)
        fin_ent_account_id = extract.re_first_or_blank(r'\d+', extract.remove_tags(tds[0]))
        if not fin_ent_account_id:
            continue
        balance = convert.to_float(extract.remove_tags(tds[2]))
        account_type = ACCOUNT_TYPE_CREDIT if balance < 0 else ACCOUNT_TYPE_DEBIT
        currency = 'EUR'  # no other examples
        # 'PT+00350127055801930EUR0' -> 'PT 00350127055801930EUR0'
        # important to replace '+' because here it's escaped space
        # and the scraper fails if passes raw val with '+' in requests
        select_account_param = extract.re_first_or_blank('[?]account[=](.*?)&', tds[4]).replace('+', ' ')
        account_parsed = {
            'financial_entity_account_id': fin_ent_account_id,
            'balance': balance,
            'currency': currency,
            'account_type': account_type,
            'country_code': 'PRT',  # Portugal
            'select_account_param': select_account_param
        }
        accounts_parsed_wo_iban.append(account_parsed)

    return accounts_parsed_wo_iban


def get_account_parsed(resp_text: str, acc_parsed_wo_iban: dict) -> AccountParsed:
    acc_parsed = acc_parsed_wo_iban.copy()
    account_no = re.sub(r'\s+', '', extract.re_first_or_blank(
        r'<span class="col2 outputext">(PT[\s\d]+)</span>', resp_text
    ))
    acc_parsed['account_no'] = account_no
    return acc_parsed


def get_total_num_of_movements(resp_text: str) -> int:
    total_str = extract.re_first_or_blank(r'(?si)Número total de registos:\s*(\d+)', resp_text)
    if not total_str:
        return 0
    return int(total_str)


def get_movements_filter_form_params(resp_text: str) -> Tuple[str, dict]:
    link, params = extract.build_req_params_from_form_html_patched(resp_text, 'consultaMovimentos')
    return link, params


def get_next_page_req_param(resp_text: str) -> Dict[str, str]:
    # Parses from ?cid=978025#
    if 'Consultar mais movimentos' not in resp_text:
        return {}
    id_ = extract.re_first_or_blank(
        r"{'(consultaMovimentos:j_idt\d+)':'consultaMovimentos:j_idt\d+'},''\);}"
        'return false" class="linkLar">Consultar mais movimentos',
        resp_text
    )
    return {id_: id_}


def _get_movs_details_param_ids(resp_text: str) -> List[str]:
    """Returns ids of req params to open all details of the movements at the page"""
    ids = re.findall(
        r"""id="callDetail\d+"><a[^>]+'(consultaMovimentos:j_idt\d+)':'consultaMovimentos:j_idt\d+'""",
        resp_text
    )
    return ids


def get_movs_details_params(resp_text: str) -> Dict[str, str]:
    """Returns req params to open all details of the movements at the page"""
    return {id_: id_ for id_ in _get_movs_details_param_ids(resp_text)}


def _get_description_extended(descr_short: str, descr_ext_table_html: str) -> str:
    # {'Descrição': '01089788 POS VENDAS',
    #  'Montante': '6.097,99\nEUR',
    #  'Data valor': '11-08-2019',
    #  'Data do movimento': '11-08-2019',
    #  'Tipo de movimento': 'Crédito',
    #  'Saldo contabilístico após movimento': '74.697,66\nEUR',
    #  'Saldo disponível após movimento': '74.697,66\nEUR'}
    descr_ext_dict = {}  # type: Dict[str, str]
    for row in re.findall('(?si)<tr.*?</tr>', descr_ext_table_html):
        cells = re.findall('(?si)<td.*?</td>', row)
        descr_ext_dict[extract.remove_tags(cells[0]).strip()] = extract.remove_tags(cells[1].strip())

    description_extended = descr_short

    for det_title in EXTENDED_DESCRIPTION_DETAILS:
        detail = descr_ext_dict.get(det_title, '')
        msg = '{}: {}'.format(det_title, detail).strip()
        description_extended += ' || {}'.format(msg)

    return description_extended.strip()


def get_movements_parsed_w_details(logger: ScrapeLogger, fin_ent_account_id: str,
                                   movements_parsed_batch: List[MovementParsed],
                                   resp_text: str) -> List[MovementParsed]:
    """Allows to get extended descriptions for provided batch of movements_parsed.
    Expects resp_text were len(det_tables) == len(movements_parsed)
    """
    # details for each movement
    det_tables = re.findall('(?si)<table class="fltl".*?</table>', resp_text)
    if len(det_tables) != len(movements_parsed_batch):
        logger.error(
            "{}: can't get movements_parsed: no details for movements ({} of {}). Skip. RESPONSE:\n{}".format(
                fin_ent_account_id,
                len(det_tables),
                len(movements_parsed_batch),
                resp_text
            )
        )
        return []
    movements_parsed_w_details = []  # type: List[MovementParsed]
    for i, mov in enumerate(movements_parsed_batch):
        descr_extended = _get_description_extended(mov['description'], det_tables[i])
        mov_upd = mov.copy()
        mov_upd['description_extended'] = descr_extended
        movements_parsed_w_details.append(mov_upd)

    return movements_parsed_w_details


def get_movements_parsed(resp_text: str) -> List[MovementParsed]:
    """Parses dev/resp_movs_details.html"""

    movements_parsed_desc = []  # type: List[MovementParsed]
    # tr with basic + tr with extended descriptions
    mov_htmls = re.findall(r'(?si)<tr id="element.*?</tr>\s*<tr style="display: none;">.*?</tr>',
                           resp_text)  # max 65 movs per page

    for mov_html in mov_htmls:
        cells = re.findall('(?si)<td[^>]*>(.*?)</td>', mov_html)

        operation_date = extract.remove_tags(cells[0])  # '14-08-2019'
        value_date = extract.remove_tags(cells[1])  # '14-08-2019'
        description = extract.remove_tags(cells[2])
        amount = convert.to_float(cells[3])
        temp_balance = convert.to_float(cells[4])
        req_details_param_id = _get_movs_details_param_ids(mov_html)[0]  # type: str

        mov_parsed = {
            'value_date': value_date.replace('-', '/'),
            'operation_date': operation_date.replace('-', '/'),
            'description': description,
            'amount': amount,
            'temp_balance': temp_balance,
            'req_details_param_id': req_details_param_id
        }

        movements_parsed_desc.append(mov_parsed)

    return movements_parsed_desc


def get_movements_parsed_from_tsv(resp_text: str) -> List[MovementParsed]:
    movements_parsed_desc = []  # type: List[MovementParsed]
    rows = resp_text.split('\n')  # max 3000 movs
    for row in rows:
        cells = row.strip().split('\t')
        # skip title and non-mov rows
        if len(cells) != 5:
            continue
        if cells[0].strip() == 'Data mov.':
            continue

        amount = convert.to_float(cells[3])
        temp_balance = convert.to_float(cells[4])

        mov_parsed = {
            'value_date': cells[0].replace('-', '/'),  # '14-08-2019' -> '14/08/2019'
            'operation_date': cells[1].replace('-', '/'),
            'description': cells[2],
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(mov_parsed)

    return movements_parsed_desc
