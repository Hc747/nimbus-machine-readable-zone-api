import datetime
from typing import Optional, Union, List

from flask import Flask, jsonify, request
from mrz.base.countries_ops import is_code, get_country
from mrz.checker.mrva import MRVACodeChecker
from mrz.checker.mrvb import MRVBCodeChecker
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td3 import TD3CodeChecker

# Web services
app_name: str = "MRZ Parser"
app_version: str = "2.0"
app = Flask(app_name)


def version() -> str:
    return '%s version: %s' % (app_name, app_version)


@app.route('/')
def main():
    return version()


alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
numeric = "1234567890"
alphanumeric = alpha + numeric
default_separator = "<"
valid = alphanumeric + default_separator
transliteration_substitutions = {
    '«': '<',
    'く': '<',
    'M': 'M',
    'М': 'M'
}
alpha_to_numeric_substitutions = {
    'o': '0',
    'O': '0',
}


def replace_all(string: str, dictionary: dict) -> str:
    for key, value in dictionary.items():
        string = string.replace(key, value)
    return string


def century_from_year(year: int) -> int:
    return (year - 1) // 100


def format_iso_date(date: str) -> str:
    current_year: int = int(datetime.datetime.now().year)
    current_century: int = century_from_year(current_year)
    avg_lifespan: int = 80

    #  TODO: determine if closer to upper or lower bound of century / correctly determine offset value

    offset = 1 if current_year - (current_century * 100) < avg_lifespan else 0

    year: Union[str, int]
    sanitised_date = replace_all(date, alpha_to_numeric_substitutions)

    try:
        year = int(sanitised_date[:2])
        century: int = current_century - offset if abs(100 - year) < year else current_century
        year = str(century) + sanitised_date[:2]
    except:
        year = sanitised_date[:2]

    month: str = sanitised_date[2:4]
    day: str = sanitised_date[4:]

    return '-'.join([year, month, day])


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
            'birth_date': format_iso_date(self.birth_date),
            'sex': self.sex,
            'expiry_date': format_iso_date(self.expiry_date)
        }


def process_text(mrz_str):
    corrected_str = mrz_str[:44] + '\n' + mrz_str[44:]
    return corrected_str


def longest_common_subsection(a: str, b: str) -> Optional[dict]:
    a_len, b_len = len(a), len(b)
    answer: dict = {}

    for x in range(a_len):
        match: dict = {}
        for y in range(b_len):
            idx: int = x + y
            if (idx < a_len and a[idx] == b[idx]):
                if "start" not in match:
                    match["start"] = idx

                value: Optional[str] = match.get("value", None)
                match["value"] = a[idx] if value is None else value + a[idx]
            else:
                previous: Optional[str] = answer.get("value", None)
                current: Optional[str] = match.get("value", None)

                if (previous is None and current is not None) or (current is not None and len(current) > len(previous)):
                    match["end"] = idx
                    answer = match

                break

    if len(answer) == 0:
        return None

    if "start" in answer and "end" not in answer:
        answer["end"] = a_len

    return answer


def substitute(value: str, size: int, substitution: str) -> str:
    if size - len(value) <= 0:
        return value

    indices: Optional[dict] = longest_common_subsection(value, substitution * size)

    if indices is None:
        return value  # TODO: return none?

    start: str = value[:indices["start"]]
    end: str = value[indices["end"]:]
    difference: int = size - (len(start) + len(end))
    padding: str = substitution * difference if difference > 0 else ""

    return start + padding + end


def identify_mrz(value: str, offset: int, types: List[str], max_attempts: int) -> Optional[str]:
    return identify_mrz_by_type_and_country_code(value, offset, types, max_attempts)


def identify_mrz_by_type_and_country_code(value: str, offset: int, types: List[str], max_attempts: int) -> Optional[str]:
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


def preprocess_mrz(value: str, size: int, types: List[str]) -> str:
    max_attempts: int = 8
    length: int = len(value)
    offset: int = max(length - size, 0)

    subset = identify_mrz(value, offset, types, max_attempts)

    if subset is None:
        return ""

    output: str = ""

    for index in range(len(subset)):
        char: str = subset[index]
        element: str = transliteration_substitutions.get(char, char)

        if element not in valid:
            continue

        output += element

    return output


# TODO: extend to allow for MRZ's with more or less than 2 lines
def extract_mrz(content: str, mrz_size: int, lines: int, types: List[str]) -> list:
    chunk_size: int = int(mrz_size / lines)
    formatted: str = ''.join(content.split()).upper()
    preprocessed: str = preprocess_mrz(formatted, mrz_size, types)
    processed: str = substitute(preprocessed, mrz_size, default_separator)

    output: list = []

    for index in range(lines):
        start: int = index * chunk_size
        end: int = start + chunk_size
        chunk: str = processed[start:end]

        while len(chunk) > 0:
            char: str = chunk[0]
            if char == default_separator:
                chunk = chunk[1:]
            else:
                break

        if chunk_size - len(chunk) > 0:
            chunk: str = substitute(chunk, chunk_size, default_separator)
            difference: int = chunk_size - len(chunk)
            chunk: str = chunk + (difference * default_separator) if difference > 0 else chunk

        output.append(chunk)

    return output


# Allow CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


class MRZDefinition:
    def __init__(self, size: int, lines: int, types: List[str], checker):
        self.size = size
        self.lines = lines
        self.types = types
        self.checker = checker


default_implementation: str = 'TD3'
empty_types: List[str] = []  # determine document types
mrz_definitions: map = {
    'TD1': MRZDefinition(90, 3, empty_types, TD1CodeChecker),
    'TD2': MRZDefinition(72, 2, empty_types, TD2CodeChecker),
    'TD3': MRZDefinition(88, 2, ['P<', 'P0'] + ['P' + char for char in alpha], TD3CodeChecker),
    'MRVA': MRZDefinition(88, 2, empty_types, MRVACodeChecker),
    'MRVB': MRZDefinition(72, 2, empty_types, MRVBCodeChecker)
}


def parse(implementation: MRZDefinition, machine_readable_zone: str) -> ParsedResult:
    machine_readable_zone = process_text(machine_readable_zone)
    checker = implementation.checker(machine_readable_zone)
    fields = checker.fields()
    return ParsedResult(fields)


@app.route('/api/passport', methods=['POST'])
def post_mrz():
    identifier: str = request.json.get('implementation') if 'implementation' in request.json else default_implementation
    identifier = identifier if identifier in mrz_definitions.keys() else default_implementation

    content: str = request.json.get('content')
    impl: MRZDefinition = mrz_definitions.get(identifier)
    mrz: str = ''.join(extract_mrz(content, mrz_size=impl.size, lines=impl.lines, types=impl.types))
    result = parse(impl, mrz)

    return jsonify(result.serialize())
