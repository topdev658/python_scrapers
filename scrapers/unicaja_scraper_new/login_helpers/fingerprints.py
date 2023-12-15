from typing import NamedTuple
from typing import List


Navigator = NamedTuple('Navigator', [
    ('user_agent', str),
    ('brands_header', str),

    ('hardware_concurrency', int),
    ('device_memory', int),

    ('languages_navigator', List[str]),
    ('languages_header', str),

])

Screen = NamedTuple('Screen', [

    ('width', int),
    ('height', int),

])

WebGl = NamedTuple('WebGl', [
    ('vendor', str),
    ('renderer', str),
    ('preset', str),

])


class Fingerprint:
    is_linux = None # type: bool
    navigator = None # type: Navigator
    screen = None # type: Screen
    canvas = None # type: str
    web_gl = None # type: WebGl

    def __init__(self, is_linux: bool, navigator: Navigator, screen: Screen, canvas: str, web_gl: WebGl):
        self.is_linux = is_linux
        self.navigator = navigator
        self.screen = screen
        self.canvas = canvas
        self.web_gl = web_gl

        if self.is_linux:
            self.platform_header = '"Linux"'
        else:
            self.platform_header = '"Windows"'
