import copy
from decimal import Decimal

from .date_format import DateFormat
from .line_parser import LineParser
from .. import Norma43Document, MovementLine


class MovementLineParser(LineParser):
    @classmethod
    def parse(cls, line: str, norma_43: Norma43Document, date_format: DateFormat) -> Norma43Document:
        ret = copy.deepcopy(norma_43)
        branch_code = line[6:10]
        transaction_date = cls._retrieve_date(line[10:16], date_format)
        value_date = cls._retrieve_date(line[16:22], date_format)
        amount_sign = 1 if line[27:28] == "2" else -1
        amount_str = line[28:42]
        amount = amount_sign * Decimal(amount_str) / Decimal("100")
        description = line[52:]
        balance = (
            (
                norma_43.accounts[-1].header.initial_balance
                if norma_43.accounts[-1].header is not None and norma_43.accounts[-1].header.initial_balance is not None
                else Decimal("0")
            )
            if len(norma_43.accounts[-1].movement_lines) == 0
            else norma_43.accounts[-1].movement_lines[-1].balance or Decimal("0")
        ) + amount
        ret.accounts[-1].movement_lines.append(
            MovementLine(
                branch_code=branch_code,
                transaction_date=transaction_date,
                value_date=value_date,
                amount=amount,
                balance=balance,
                description=description,
            )
        )
        return ret
