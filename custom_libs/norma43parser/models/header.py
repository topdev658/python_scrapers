from datetime import date
from decimal import Decimal


class Header:
    def __init__(
        self,
        bank_code: str = None,
        branch_code: str = None,
        account_number: str = None,
        start_date: date = None,
        end_date: date = None,
        initial_balance: Decimal = None,
        currency: str = None,
        information_mode_code: str = None,
        account_name: str = None,
    ) -> None:
        self.bank_code = bank_code
        self.branch_code = branch_code
        self.account_number = account_number
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.currency = currency
        self.information_mode_code = information_mode_code
        self.account_name = account_name
