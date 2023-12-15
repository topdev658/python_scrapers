from datetime import date
from decimal import Decimal
from typing import List


class MovementLine:
    def __init__(
        self,
        branch_code: str = None,
        transaction_date: date = None,
        value_date: date = None,
        amount: Decimal = None,
        balance: Decimal = None,
        description: str = None,
        extra_information: List[str] = None,
    ) -> None:
        self.branch_code = branch_code
        self.transaction_date = transaction_date
        self.value_date = value_date
        self.amount = amount
        self.balance = balance
        self.description = description
        self.extra_information = extra_information if extra_information is not None else []
