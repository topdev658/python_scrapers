import copy
from decimal import Decimal


from .date_format import DateFormat
from .line_parser import LineParser
from .. import Norma43Document, MovementLine


class MovementCurrencyExchangeInformationParser(LineParser):
    @classmethod
    def parse(cls, line: str, norma_43: Norma43Document, date_format: DateFormat) -> Norma43Document:
        ret = copy.deepcopy(norma_43)
        movement_origin_currency = line[4:7]
        amount = Decimal(line[7:21]) / Decimal("100")
        currency_exchange_information = {
            "movement_origin_currency": movement_origin_currency,
            "amount": amount
        }
        setattr(ret.accounts[-1].movement_lines[-1],'currency_exchange_information',currency_exchange_information)
        return ret
