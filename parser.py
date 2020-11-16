from typing import List, Optional

from mrz.base.countries_ops import get_country, is_code

from constants import alpha_to_numeric_substitutions, transliteration_substitutions, alphanumeric
from utils import format_iso_date, replace_all, substitute


# Prediction class
class ParsedResult:
    def __init__(self, fields):
        self.document_number = fields.document_number
        self.name = fields.name
        self.surname = fields.surname
        self.nationality = get_country(fields.nationality)
        self.nationality_code = fields.nationality
        self.country = get_country(fields.country)
        self.country_code = fields.country
        self.birth_date = fields.birth_date
        self.sex = fields.sex
        self.expiry_date = fields.expiry_date

    def serialize(self):
        return {
            'document_number': self.document_number,
            'name': self.name,
            'surname': self.surname,
            'nationality': self.nationality,
            'nationality_code': self.nationality_code,
            'country': self.country,
            'country_code': self.country_code,
            'birth_date': format_iso_date(self.birth_date, alpha_to_numeric_substitutions),
            'sex': self.sex,
            'expiry_date': format_iso_date(self.expiry_date, alpha_to_numeric_substitutions)
        }


_default_separator = "<"
_valid = alphanumeric + _default_separator


# MRZ Definition class
class MRZParser:
    def __init__(self, line_size: int, lines: int, types: List[str], checker):
        self.line_size = line_size
        self.lines = lines
        self.types = types
        self.checker = checker

    def size(self) -> int:
        return self.line_size * self.lines

    def __identify_mrz(self, value: str, offset: int, types: List[str], max_attempts: int) -> Optional[str]:
        return self.__identify_mrz_by_type_and_country_code(value, offset, types, max_attempts)

    @staticmethod
    def __identify_mrz_by_type_and_country_code(value: str, offset: int, types: List[str], max_attempts: int) -> Optional[str]:
        identified: bool = False

        for attempt in range(max_attempts):
            if identified:
                break

            index: int = offset - (max_attempts - attempt)

            if index < 0:
                index = offset - attempt

            if index < 0:
                break

            subset: str = value[index:]

            for i in range(len(subset)):
                if identified:
                    break

                chars: str = replace_all(subset[i:], transliteration_substitutions)

                for _type in types:
                    if identified:
                        break

                    if not chars.startswith(_type):
                        continue

                    type_length = len(_type)
                    country_length = 3
                    country_code = chars[type_length:type_length + country_length]

                    if is_code(country_code):
                        identified = True
                        offset = max(index + i, 0)

        return value[offset:] if identified else None

    def __preprocess_mrz(self, value: str) -> str:
        max_attempts: int = 8
        length: int = len(value)
        offset: int = max(length - self.size(), 0)

        subset = self.__identify_mrz(value, offset, self.types, max_attempts)

        if subset is None:
            return ""

        output: str = ""

        for index in range(len(subset)):
            char: str = subset[index]
            element: str = transliteration_substitutions.get(char, char)

            if element not in _valid:
                continue

            output += element

        return output

    def __extract_mrz(self, content: str) -> List[str]:
        mrz_size: int = self.size()
        formatted: str = ''.join(content.split()).upper()
        preprocessed: str = self.__preprocess_mrz(formatted)
        processed: str = substitute(preprocessed, mrz_size, _default_separator)

        output: list = []

        for index in range(self.lines):
            start: int = index * self.line_size
            end: int = start + self.line_size
            chunk: str = processed[start:end]

            while len(chunk) > 0:
                char: str = chunk[0]
                if char == _default_separator:
                    chunk = chunk[1:]
                else:
                    break

            if self.line_size - len(chunk) > 0:
                chunk: str = substitute(chunk, self.line_size, _default_separator)
                difference: int = self.line_size - len(chunk)
                chunk: str = chunk + (difference * _default_separator) if difference > 0 else chunk

            output.append(chunk)

        return output

    @staticmethod
    def __format(chunks: List[str]) -> str:
        return '\n'.join(chunks)

    def parse(self, content: str) -> ParsedResult:
        chunks: List[str] = self.__extract_mrz(content)
        zone: str = self.__format(chunks)
        return ParsedResult(self.checker(zone).fields())
