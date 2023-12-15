import re
import time
from typing import List, Dict

from custom_libs import extract


def get_n43_url(resp_text: str) -> str:
    url = extract.re_first_or_blank(
        r'(?s)<a id="C:R3.R22:link" href="(.*?)" class="_c1 ei_richlink _c1"',
        resp_text
    )
    return 'https://www.targobank.es' + url


def get_n43_archive_url(resp_text: str) -> str:
    url = extract.re_first_or_blank(
        r'(?s)<a id="C:R3.R1.R24:link" href="(.*?)" class="_c1 ei_richlink _c1"',
        resp_text
    )
    return 'https://www.targobank.es' + url


def get_n43_filter_params(resp_text: str) -> Dict:
    filter_params = dict()
    filter_params["$CPT"] = extract.re_first_or_blank(
        r'(?s)<input name="\$CPT" type="hidden" value="(.*?)"',
        resp_text
    )
    filter_params["_wxf2_cc"] = extract.re_first_or_blank(
        r'(?s)<input name="_wxf2_cc" type="hidden" value="(.*?)"',
        resp_text
    )
    form_params = re.findall(
        r'(?s)<input id="C:P:F:([\w]{,2})" name="([\w_%/]*?)" type="hidden" value="([\w_%/:.]*?)" />',
        resp_text
    )
    form_dict = {tup[1]: tup[2] for tup in form_params}
    filter_params.update(form_dict)
    return filter_params


def get_n43_files_download_info(resp_text: str, date_from: str, date_to: str) -> List[Dict[str, str]]:
    n43_files_download_info = []
    links_by_data = re.findall(
        r'(?s)<td class="([\w]{1}) _c1 c _c1">([\d]{2}\/[\d]{2}\/[\d]{4}[\s]{1}[\d]?[\d]\:[\d]{2}\:[\d]{2})'
        r'</td><td class="([\w]{1}) _c1 g _c1">(.*?)<a href="([\w._&/?;=%]*)" target="_self" id="([\w._:]*)" '
        r'title="Descargar el fichero en su ordenador">',
        resp_text
    )

    from_date = time.strptime(date_from, "%d/%m/%Y")
    to_date = time.strptime(date_to, "%d/%m/%Y")

    # additional check in case if some params for files filtering were not uploaded in response html
    for link_by_data in links_by_data:
        date = extract.re_first_or_blank(
            r'\d{2}/\d{2}/\d{4}',
            link_by_data[1]
        )
        link_date = time.strptime(date, "%d/%m/%Y")
        link_id = extract.re_first_or_blank(
            r'.*id=(.*?)&amp;',
            link_by_data[4]
        )

        # check if file's date is in range of date_from and date_to
        if from_date <= link_date <= to_date:
            file_donwload_info = {}  # type: Dict[str, str]
            file_donwload_info['link'] = 'https://www.targobank.es' + link_by_data[4]
            file_donwload_info['id'] = link_id

            n43_files_download_info.append(file_donwload_info)

    return n43_files_download_info


def get_n43_files_reactivate_info(resp_text: str, date_from: str, date_to: str) -> List[Dict[str,str]]:
    n43_files_reactivate_info_unfiltered = re.findall(
        r'(?s)<input type="submit" value="Reactivar" name="(.*?)" class="hideifscript" title="Reactivar el fichero para descargar"',
        resp_text
    )

    n43_files_reactivate_info = []

    from_date = time.strptime(date_from, "%d/%m/%Y")
    to_date = time.strptime(date_to, "%d/%m/%Y")

    # additional check in case if some params for files filtering were not uploaded in response html
    for n43_file_reactivate_info_unfiltered in n43_files_reactivate_info_unfiltered:
        file_date_reverse = extract.re_first_or_blank(
            r'(?s)dateFichier:([\d]*?)_',
            n43_file_reactivate_info_unfiltered + '_'
        )

        file_id = extract.re_first_or_blank(
            r'(?s)dateFichier:([\d]*?)_',
            n43_file_reactivate_info_unfiltered + '_'
        )

        file_date = time.strptime(file_date_reverse[0:8], "%Y%m%d")

        if from_date <= file_date <= to_date:
            n43_file_reactivate_info = {}  # type: Dict[str, str]
            n43_file_reactivate_info['reactivate_param'] = n43_file_reactivate_info_unfiltered
            n43_file_reactivate_info['id'] = file_id
            n43_files_reactivate_info.append(n43_file_reactivate_info)

    return n43_files_reactivate_info


def get_n43_reactivate_form(resp_text: str) -> Dict:
    reactivate_params = dict()
    reactivate_params["$CPT"] = extract.re_first_or_blank(
        r'(?s)<input name="\$CPT" type="hidden" value="(.*?)"',
        resp_text
    )
    reactivate_params["_wxf2_cc"] = extract.re_first_or_blank(
        r'(?s)<input name="_wxf2_cc" type="hidden" value="(.*?)"',
        resp_text
    )

    form_params = re.findall(
        r'(?s)<input id="C:P:F:([\w]{,2})" name="([\w_%/]*?)" type="hidden" value="([\w_%/:.]*?)" />',
        resp_text
    )
    form_dict = {tup[1]: tup[2] for tup in form_params}
    reactivate_params.update(form_dict)

    return reactivate_params


def get_form_action_url(resp_text: str) -> str:
    form_action = extract.re_first_or_blank(
        r'(?s)<form id="C:P:F" action="(.*?)" method="post" novalidate="novalidate" class="_devb_act ___Form"',
        resp_text
    )
    return 'https://www.targobank.es' + form_action