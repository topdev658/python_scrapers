import unittest

from fingerprints import *
from generate_solution import generate_solution


class TestGenerateSolution(unittest.TestCase):
    def test_generate_solution(self):
        fingerprint = Fingerprint(
            is_linux=True,
            navigator=Navigator(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                brands_header='"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                hardware_concurrency=24,
                device_memory=8,
                languages_navigator=['en-US', 'en'],
                languages_header='en-US,en;q=0.9',
            ),
            screen=Screen(3840, 2160),
            canvas='linux_001',
            web_gl=WebGl(
                vendor='Google Inc. (NVIDIA Corporation)',
                renderer='ANGLE (NVIDIA Corporation, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5.0)',
                preset='linux_nvidia_001',
            ),
        )

        script_code = """
            window.reese84interrogator = function() {
                this.interrogate = function (onSuccess, onError) {
                    onSuccess({"p":"big_string","st":100,"sr":200,"cr":300,"og":1});
                }
            }
        """

        solution = generate_solution(
            script_src='https://univia.unicajabanco.es/nq-vent-man-macd-and-and-macbeth-gayne-i-not-of-',
            aih='cWGPGNo0iG5PXchwZU63i1/tuXyk4UX4IdoHPCnDHa8=',
            history_len=1,
            global_variables=['a1_0x4d5', 'reese84', 'a1_0xcd60'],
            html='<html></html>',
            script_code=script_code,
            fingerprint=fingerprint,
            cwd='../../solution_001',
        )

        print(solution)