import datetime
import re
from typing import Dict, List

from custom_libs import extract
from project import settings as project_settings
from project.custom_types import ACCOUNT_TYPE_CREDIT, ACCOUNT_TYPE_DEBIT, AccountParsed, MovementParsed
from .custom_types import Tile


def get_gridpass_img_src(resp_text: str) -> str:
    return extract.re_first_or_blank(
        r'img\s+id="gridpass_img"\s+src="(.*?)"',
        resp_text
    )


def get_gridpass_tile_to_code(resp_text: str) -> Dict[Tile, str]:
    """
    Parses
    <map id="gridpass_map" onclick="return(false);" name="gridpass_map_name">
    <area href="#" onclick="vrepo.sendChange('gridpass','15');return false;" shape="rect" coords="..."  />
    <area href="#" onclick="vrepo.sendChange('gridpass','96');return false;" shape="rect" coords="..."  />
    <area href="#" onclick="vrepo.sendChange('gridpass','90');return false;" shape="rect" coords="..."  />
    <area href="#" onclick="vrepo.sendChange('gridpass','77');return false;" shape="rect" coords="..."  />
    <area href="#" onclick="vrepo.sendChange('gridpass','46');return false;" shape="rect" coords="..."  />
    ...

    :returns: dict(tile_pos: gridpass_value==code), i.e. {(0,0): '15', ...}
    """

    vals = re.findall(r"vrepo.sendChange\('gridpass','(\d+)'\)", resp_text)
    assert len(vals) == 24
    tiles_to_codes = {}  # type: Dict[Tile, str]
    i = 0
    for y in range(4):
        for x in range(6):
            tile = Tile((x, y))
            tiles_to_codes[tile] = vals[i]
            i += 1

    assert len(tiles_to_codes) == 24
    return tiles_to_codes


def get_accounts_parsed(resp_json: dict) -> List[AccountParsed]:
    accounts_parsed = []  # type: List[AccountParsed]
    groups = resp_json['tableauSoldes']['listeGroupes']
    for group_dict in groups:
        if group_dict['libelleGroupe'] not in ['Comptes courants', 'Current accounts']:
            continue

        accounts_dicts = group_dict['listeComptes']

        for acc in accounts_dicts:
            balance_cents = acc['soldePrevisionnel']
            balance = round(balance_cents / 100, 2)

            account_no = acc['numeroCompte']  # FR7630004008230001050284503
            currency = acc['deviseTenue']

            account_type = (ACCOUNT_TYPE_CREDIT
                            if (acc['type'] != '101' or balance < 0)
                            else ACCOUNT_TYPE_DEBIT)

            country_code = 'FRA' if account_no.startswith('FR') else 'ESP'

            account_parsed = {
                'account_no': account_no,
                'country_code': country_code,
                'account_type': account_type,
                'currency': currency,
                'balance': balance,
                'financial_entity_account_id': account_no
            }

            accounts_parsed.append(account_parsed)

    return accounts_parsed


def _date_str_from_ts(ts: int) -> str:
    """:returns: formatted date from timestamp (seconds or millis)"""
    if len(str(ts)) == 13:
        ts = int(ts / 1000)
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime(project_settings.SCRAPER_DATE_FMT)


def get_movements_parsed(resp_json: dict, account_balance: float) -> List[MovementParsed]:
    # need to calculate temp_balance manually
    # for this should reorder movements form asc to desc

    movements_parsed_desc = []  # type: List[MovementParsed]

    movs_dicts_desc = resp_json['mouvementsBDDF']
    temp_balance = account_balance
    for mov in movs_dicts_desc:
        descr = mov['libelle']
        amount = round(mov['montant']['montant'] / 100, 2)
        operation_date = _date_str_from_ts(mov['dateOperation'])  # from 1539640800000
        value_date = _date_str_from_ts(mov['dateValeur'])

        movement_parsed = {
            'amount': amount,
            'temp_balance': temp_balance,
            'description': descr,
            'operation_date': operation_date,
            'value_date': value_date
        }

        movements_parsed_desc.append(movement_parsed)
        temp_balance = round(temp_balance - amount, 2)

    return movements_parsed_desc
