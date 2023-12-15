import copy
from decimal import Decimal

from .date_format import DateFormat
from .line_parser import LineParser
from .. import Norma43Document, Footer


class FooterParser(LineParser):
    @classmethod
    def parse(cls, line: str, norma_43: Norma43Document, date_format: DateFormat) -> Norma43Document:
        ret = copy.deepcopy(norma_43)
        bank_code = line[2:6]
        branch_code = line[6:10]
        account_number = line[10:20]
        debit_entries = int(line[20:25])
        debit_amount = Decimal(line[25:39]) / Decimal("100")
        credit_entries = int(line[39:44])
        credit_amount = Decimal(line[44:58]) / Decimal("100")
        final_balance_sign = 1 if line[58:59] == "2" else -1
        final_balance_str = line[59:73]
        final_balance = final_balance_sign * Decimal(final_balance_str) / Decimal("100")
        currency = line[73:76]
        # TODO: convert currency
        ret.accounts[-1].footer = Footer(
            bank_code=bank_code,
            branch_code=branch_code,
            account_number=account_number,
            debit_entries=debit_entries,
            debit_amount=debit_amount,
            credit_entries=credit_entries,
            credit_amount=credit_amount,
            final_balance=final_balance,
            currency=currency,
        )
        return ret
