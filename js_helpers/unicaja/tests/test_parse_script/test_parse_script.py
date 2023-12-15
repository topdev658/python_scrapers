import unittest

from parse_script import parse_script


def test_parse_script(test_class, file):
    with open(file, 'r') as f:
        code = f.read()

    result = parse_script(code)

    # print(result.fp_script[-70:])
    # print(result.cookie_script[-70:])

    # Fingerprinting script ends on `window['reese84interrogator'] = someFunction`,
    # of course obfuscated, so we only check for `window[` in it
    test_class.assertTrue('window[' in result.fp_script[-70:])

    # Cookie script ends on `reese84 = someValue`, so we assert it is present
    test_class.assertTrue('reese84' in result.cookie_script[-70:])

    # We cannot check the order of global variables, but know for sure
    # that it contains 'reese84' from the 'var reese84;' statement
    test_class.assertTrue('reese84' in result.global_variables)

    print('Global variables:', result.global_variables)
    print('aih:', result.aih)


class TestParseScript(unittest.TestCase):
    def test_parse_script_001(self):
        test_parse_script(self, 'code_001.js')