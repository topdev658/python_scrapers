from typing import List

from . import MovementLine, Header, Footer


class Account:
    def __init__(
        self, header: Header = None, movement_lines: List[MovementLine] = None, footer: Footer = None,
    ):

        self.header = header
        self.movement_lines = movement_lines if movement_lines is not None else []
        self.footer = footer
