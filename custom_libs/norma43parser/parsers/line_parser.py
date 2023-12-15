from datetime import date, datetime

from ..models import Norma43Document
from .date_format import DateFormat


class LineParser:
    @classmethod
    def parse(cls, line: str, norma_43: Norma43Document, date_format: DateFormat) -> Norma43Document:
        pass

    @staticmethod
    def _retrieve_date(encoded_date: str, date_format: DateFormat) -> date:
        year = ""
        month = ""
        day = ""

        i = 0

        for _ in range(len(date_format.value)):
            symbol = date_format.value[i]
            encoded_date_part = encoded_date[i * 2 : i * 2 + 2]
            if symbol == "Y":
                year = "20" + encoded_date_part
            elif symbol == "D":
                day = encoded_date_part
            elif symbol == "M":
                month = encoded_date_part
            i += 1
        return datetime(int(year), int(month), int(day)).date()
