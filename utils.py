import datetime
from typing import Optional, Union


class LCSResult:
    def __init__(self, start: int, end: int, value: str):
        self.start = start
        self.end = end
        self.value = value


_value = 'value'
_start = 'start'
_end = 'end'


def longest_common_subsection(a: str, b: str) -> Optional[LCSResult]:
    a_len, b_len = len(a), len(b)
    answer: dict = {}

    for x in range(a_len):
        match: dict = {}
        for y in range(b_len):
            idx: int = x + y
            if idx < a_len and a[idx] == b[idx]:
                if _start not in match:
                    match[_start] = idx

                value: Optional[str] = match.get(_value, None)
                match[_value] = a[idx] if value is None else value + a[idx]
            else:
                previous: Optional[str] = answer.get(_value, None)
                current: Optional[str] = match.get(_value, None)

                if (previous is None and current is not None) or (current is not None and len(current) > len(previous)):
                    match[_end] = idx
                    answer = match

                break

    if len(answer) == 0:
        return None

    if _start in answer and _end not in answer:
        answer[_end] = a_len

    return LCSResult(answer[_start], answer[_end], answer[_value])


def replace_all(string: str, dictionary: dict) -> str:
    for key, value in dictionary.items():
        string = string.replace(key, value)
    return string


def century_from_year(year: int) -> int:
    return (year - 1) // 100


def substitute(value: str, size: int, substitution: str) -> str:
    if size - len(value) <= 0:
        return value

    indices: Optional[LCSResult] = longest_common_subsection(value, substitution * size)

    if indices is None:
        return value  # TODO: return none?

    start: str = value[:indices.start]
    end: str = value[indices.end:]
    difference: int = size - (len(start) + len(end))
    padding: str = substitution * difference if difference > 0 else ""

    return start + padding + end


def format_iso_date(date: str, substitutions: Optional[dict] = None) -> str:
    current_year: int = int(datetime.datetime.now().year)
    current_century: int = century_from_year(current_year)
    avg_lifespan: int = 80

    #  TODO: determine if closer to upper or lower bound of century / correctly determine offset value

    offset = 1 if current_year - (current_century * 100) < avg_lifespan else 0

    year: Union[str, int]
    sanitised_date = date if substitutions is None else replace_all(date, substitutions)

    try:
        year = int(sanitised_date[:2])
        century: int = current_century - offset if abs(100 - year) < year else current_century
        year = str(century) + sanitised_date[:2]
    except:
        year = sanitised_date[:2]

    month: str = sanitised_date[2:4]
    day: str = sanitised_date[4:]

    return '-'.join([year, month, day])
