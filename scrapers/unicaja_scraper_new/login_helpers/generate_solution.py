import json
import subprocess
from typing import List

from .fingerprints import Fingerprint


def generate_solution(
    script_src: str,
    aih: str,
    history_len: int,
    global_variables: List[str],
    html: str,
    script_code: str,
    fingerprint: Fingerprint,
    cwd: str,
):
    # Generate JSON that the script needs
    json_obj = {
        'isLinux': fingerprint.is_linux,
        'navigator': {
            'userAgent': fingerprint.navigator.user_agent,
            'hardwareConcurrency': fingerprint.navigator.hardware_concurrency,
            'deviceMemory': fingerprint.navigator.device_memory,
            'languages': fingerprint.navigator.languages_navigator,
        },
        'screen': {
            'width': fingerprint.screen.width,
            'height': fingerprint.screen.height,
        },
        'canvas': fingerprint.canvas,
        'webGl': {
            'vendor': fingerprint.web_gl.vendor,
            'renderer': fingerprint.web_gl.renderer,
            'preset': fingerprint.web_gl.preset,
        }
    }

    json_str = json.dumps(json_obj)
    proc = subprocess.run(
        [
            'node',
            'unicaja.js',
            script_src,
            aih,
            str(history_len),
            json_str,
            ','.join(global_variables),
        ],
        input=bytes(html + script_code, encoding='utf-8'),
        stdout=subprocess.PIPE,
        cwd=cwd,
    )

    if proc.returncode != 0:
        print('Process return non zero exit-code: {}'.format(proc.returncode))
        print(proc.stderr.decode())

    output = proc.stdout.decode(encoding='utf-8')
    try:
        solution = json.loads(output)
    except Exception as e:
        print(output)
        raise e
    return solution
