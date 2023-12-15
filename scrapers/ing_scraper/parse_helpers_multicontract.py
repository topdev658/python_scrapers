import json
import re
from typing import Dict, List

from custom_libs import extract


def get_contracts_params(resp_text: str) -> List[Dict[str, str]]:
    """
    parse <a id="apoderado_6543297" name="apoderado_6543297"
    onclick="submitForm('roleSelectionForm',1,
    {source:'apoderado_6543297','corpId':'6543297','role':'SME_AGENT','indexTabCorporateHome':'0'})
    ;return false;" class="OraLink" href="#"></a>

    should extract params to call as
    org.apache.myfaces.trinidad.faces.FORM=roleSelectionForm
    &_noJavaScript=false
    &javax.faces.ViewState=%213
    &source=apoderado_6543297
    &corpId=6543297
    &role=SME_AGENT
    &indexTabCorporateHome=0
    """
    contracts_params = []
    contracts_params_htmls = re.findall('<a id="apoderado.*?</a>', resp_text)
    for contract_params_html in contracts_params_htmls:
        contract_params_json_str = extract.re_first_or_blank('{.*?}', contract_params_html)
        if "'source'" not in contract_params_json_str:
            # fix key source without quotes
            contract_params_json_str = contract_params_json_str.replace('source', "'source'")
        contract_params = json.loads(contract_params_json_str.replace("'", '"'))
        contracts_params.append(contract_params)
    return contracts_params
