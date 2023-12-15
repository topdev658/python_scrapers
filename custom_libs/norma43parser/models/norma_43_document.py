from typing import List

from .account import Account


class Norma43Document:
    def __init__(
        self, accounts: List[Account] = None, reported_entries: int = 0,
    ):

        self.accounts = accounts if accounts is not None else []
        self.reported_entries = reported_entries
