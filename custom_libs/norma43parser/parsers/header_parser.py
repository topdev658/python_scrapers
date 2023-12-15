import copy
from decimal import Decimal

from .date_format import DateFormat
from .line_parser import LineParser
from .. import Norma43Document, Header, Account


class HeaderParser(LineParser):
    @classmethod
    def parse(cls, line: str, norma_43: Norma43Document, date_format: DateFormat) -> Norma43Document:
        ret = copy.deepcopy(norma_43)
        bank_code = line[2:6]
        branch_code = line[6:10]
        account_number = line[10:20]
        start_date = cls._retrieve_date(line[20:26], date_format)
        end_date = cls._retrieve_date(line[26:32], date_format)

        initial_balance_sign = 1 if line[32:33] == "2" else -1
        initial_balance_str = line[33:47]
        initial_balance = initial_balance_sign * Decimal(initial_balance_str) / Decimal("100")
        currency = line[47:50]
        information_mode_code = line[50:51]
        account_name = line[51:]
        ret.accounts.append(
            Account(
                header=Header(
                    bank_code=bank_code,
                    branch_code=branch_code,
                    account_number=account_number,
                    start_date=start_date,
                    end_date=end_date,
                    initial_balance=initial_balance,
                    currency=currency,
                    information_mode_code=information_mode_code,
                    account_name=account_name,
                )
            )
        )

        # TODO replace currency
        return ret
