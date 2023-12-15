import re
from custom_libs import extract


def get_form_inputs(resp_text: str, form_name: str) -> dict:
    """Similar to extract.build_form_params, but for special layout"""

    form_html = extract.re_first_or_blank(
        r'(?si)<form[^>]*name\s*=\s*"{}".*?</form>'.format(form_name),
        resp_text
    )
    # [(value, name), ...]
    fields_tuples_with_values = re.findall(
        r"""(?si)<input[^>]*value\s*=\s*"([^>]*?)"[^>]*name\s*=\s*"([^>]*?)"[^>]*>""",
        form_html
    )
    params = {name: value for (value, name) in fields_tuples_with_values}
    return params
