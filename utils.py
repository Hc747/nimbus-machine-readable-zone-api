import datetime
from typing import Optional, Union


class LCSResult:
    def __init__(self, start: Optional[int], end: Optional[int], value: Optional[str]):
        self.start = start
        self.end = end
        self.value = value

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, start):
        self.__start = start

    @property
    def end(self):
        return self.__end

    @end.setter
    def end(self, end):
        self.__end = end

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    def size(self) -> Optional[int]:
        start, end = self.start, self.end
        return None if (start is None or end is None) else end - start

    def valid(self) -> bool:
        return self.value is not None and self.size() is not None


def longest_common_subsection(first: str, second: str) -> Optional[LCSResult]:
    a, b = len(first), len(second)
    answer: Optional[LCSResult] = None

    for x in range(a):
        candidate: LCSResult = LCSResult(None, None, None)
        for y in range(b):
            index: int = x + y
            if index < a and first[index] == second[index]:
                candidate.start = index if candidate.start is None else candidate.start
                candidate.value = first[index] if candidate.value is None else candidate.value + first[index]
            else:
                candidate.end = index

                if candidate.valid():
                    answer = candidate if answer is None else max(candidate, answer, key=lambda v: v.size())

                break

    if answer is not None and answer.end is None:
        answer.end = a

    return answer


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
