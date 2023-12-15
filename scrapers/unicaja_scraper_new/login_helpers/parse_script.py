import re
from typing import NamedTuple
import esprima

from typing import List

ParseResult = NamedTuple('ParseResult', [

    ('fp_script', str),
    ('global_variables', List[str]),
    ('cookie_script', str),
    ('aih', str),
])


def parse_script(code: str) -> ParseResult:
    # Parse fingerprinting script and cookie script.
    # Cookie script is not needed anywhere in the program, but we still parse it
    # to then remove it, so AST parser has fewer nodes to deal with
    fp_script_span = re.search(r'\(function\s?\(\).*}\)\(\);', code, re.DOTALL).span()
    cookie_script_span = re.search(r'!\(function.*}\(\)\);', code, re.DOTALL).span()

    fp_script = code[fp_script_span[0]:fp_script_span[1]]
    cookie_script = code[cookie_script_span[0]:cookie_script_span[1]]

    # Compose a smaller string to parse AST.
    # fp_script always comes BEFORE cookie_script, so we do not need to sort the indexes
    leftover = code[0:fp_script_span[0]] + \
               code[fp_script_span[1]:cookie_script_span[0]] + \
               code[cookie_script_span[1]:]

    # Parse AST.
    # We search for VariableDeclaration & FunctionDeclaration nodes
    # and add their names to the list. This step is necessary as
    # Incapsula everytime puts them in a different order
    global_variables = []
    ast = esprima.parseScript(leftover)
    for node in ast.body:
        if node.type == 'VariableDeclaration':
            global_variables.append(node.declarations[0].id.name)
        elif node.type == 'FunctionDeclaration':
            global_variables.append(node.id.name)

    # Parse 'aih' in cookie_script, it is a string used in encryption
    # return new window.*?'aih':\s?'(.*?)'
    aih = re.search(r"return new window.*?'aih':\s?'(.*?)'", cookie_script, re.DOTALL).group(1)

    return ParseResult(
        fp_script=fp_script,
        global_variables=global_variables,
        cookie_script=cookie_script,
        aih=aih,
    )
