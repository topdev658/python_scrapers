import re
from typing import List

from custom_libs import extract
from project.custom_types import MovementParsed
from .custom_types import SantanderChileCompany


def get_companies(resp_text: str) -> List[SantanderChileCompany]:
    companies = []  # type: List[SantanderChileCompany]
    companies_table_html = extract.re_first_or_blank('(?si)<tbody id="tabla_empresas">.*?</table>', resp_text)
    companies_htmls = re.findall('(?si)<tr.*?</tr>', companies_table_html)
    for company_html in companies_htmls:
        tds = [extract.remove_tags(td) for td in re.findall('(?si)<td.*?</td>', company_html)]
        emp_sel_param = extract.re_first_or_blank(r'name="empSel"\s+value="(.*?)"', company_html).strip()
        org_title = tds[-1].strip()  # UST GLOBAL CHILE S.A
        # Controller / Supervisor, it is possible when several roles for one company
        # but we need only Controller
        user_access_role = tds[3]
        if user_access_role == 'Controller':
            company = SantanderChileCompany(
                empSel_param=emp_sel_param,
                org_title=org_title,
            )
            companies.append(company)

    return companies


def get_companies_one_contract(resp_text: str) -> List[SantanderChileCompany]:
    # 0001000100069002163980007645325700NALANDA SEGURIDAD SPA
    emp_sel_param = extract.re_first_or_blank('name=empSel value="(.*?)"', resp_text).strip()
    org_title = re.sub(r'^\d+', '', emp_sel_param)
    companies = [
        SantanderChileCompany(
            empSel_param=emp_sel_param,
            org_title=org_title,
        )
    ]
    return companies


def get_movements_parsed(resp_json: dict) -> List[MovementParsed]:
    # fpr resp format take a look into the dev/req-resp
    movements_parsed_desc = []  # type: List[MovementParsed]
    # Also covers
    # {'Result': None, 'ErrorCode': None, 'ErrorDescription': None, \
    # 'ErrorSource': None,
    # 'Mensaje': {'Titulo': '', 'Texto': 'No se encontraron datos para la consulta',
    # 'Tipo': 1, 'CodigoEmisorError': None, 'CodigoError': None}, 'Status': 0}
    movs_dicts = (resp_json.get('Result') or {}).get('Detalle', [])
    for mov_dict in movs_dicts:
        operation_date = mov_dict['FechaContable']  # '12/10/2018'
        amount = float(mov_dict['Importe'])
        temp_balance = float(mov_dict['NuevoSaldo'])
        descr = mov_dict['Descripcion'].strip()

        movement_parsed = {
            'operation_date': operation_date,
            # there is no information about value date in the web/excel
            'value_date': operation_date,
            'description': descr,
            'amount': amount,
            'temp_balance': temp_balance
        }

        movements_parsed_desc.append(movement_parsed)

    return movements_parsed_desc
