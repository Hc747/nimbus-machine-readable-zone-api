from mrz.checker.td3 import TD3CodeChecker, get_country
from flask import Flask, jsonify, render_template, request
from typing import Optional

# Web services
app = Flask(__name__)


# Prediction class
class ParsedResult:
    def __init__(self, fields):
        self.document_number = fields.document_number
        self.name = fields.name
        self.surname = fields.surname
        self.nationality = get_country(fields.nationality)
        self.country = get_country(fields.country)
        self.birth_date = fields.birth_date
        self.sex = fields.sex
        self.expiry_date = fields.expiry_date

    def serialize(self):
        return {
            'document_number': self.document_number,
            'name': self.name,
            'surname': self.surname,
            'nationality': self.nationality,
            'country': self.country,
            'birth_date': self.birth_date,
            'sex': self.sex,
            'expiry_date': self.expiry_date
        }


def process_text(mrz_str):
    corrected_str = mrz_str[:44] + '\n' + mrz_str[44:]
    return corrected_str


alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
separator = "<"
valid = alphanumeric + separator
substitutions = {
    '«': '<',
    'M': 'M',
    'М': 'M'
}


def longest_common_subsection(a: str, b: str) -> Optional[dict]:
    a_len, b_len = len(a), len(b)
    answer = {}

    for x in range(a_len):
        match = {}
        for y in range(b_len):
            idx = x + y
            if (idx < a_len and a[idx] == b[idx]):
                if "start" not in match:
                    match["start"] = idx

                value = match.get("value", None)
                match["value"] = a[idx] if value is None else value + a[idx]
            else:
                previous = answer.get("value", None)
                current = match.get("value", None)

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


def preprocess_mrz(value: str, size: int, types: str) -> str:
    length: int = len(value)
    offset: int = max(length - size, 0)

    output: str = ""
    subset: str = value[offset:]
    identified: bool = False

    for index in range(len(subset)):
        char: str = subset[index]
        value: str = substitutions.get(char, char)

        if not identified:
            if value in types:
                identified = True
            else:
                continue

        if value not in valid:
            continue

        output += value

    return output


# TODO: extend to allow for MRZ's with more or less than 2 lines
def extract_mrz(content: str, mrz_size: int, lines: int, types: str) -> list:
    chunk_size: int = int(mrz_size / lines)
    formatted = ''.join(content.split()).upper()
    preprocessed = preprocess_mrz(formatted, mrz_size, types)
    processed = substitute(preprocessed, mrz_size, separator)

    output: list = []

    for index in range(lines):
        start: int = index * chunk_size
        end: int = start + chunk_size
        chunk = processed[start:end]

        while len(chunk) > 0:
            char: str = chunk[0]
            if char == separator:
                chunk = chunk[1:]
            else:
                break

        if chunk_size - len(chunk) > 0:
            chunk = substitute(chunk, chunk_size, separator)
            difference = chunk_size - len(chunk)
            chunk = (difference * separator) + chunk if difference > 0 else chunk

        output.append(chunk)

    return output


def parse_mrz(mrz_str):
    mrz_str = process_text(mrz_str)
    td3_check = TD3CodeChecker(mrz_str)
    fields = td3_check.fields()
    result = ParsedResult(fields)
    return result


# Allow CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/')
def main():
    return "mrz parser version 0.1"


@app.route('/api/passport', methods=['POST'])
def post_atar():
    content: str = request.json.get('content')
    types: str = request.json.get('types') if 'types' in request.json else "P"
    lines: int = request.json.get('lines') if 'lines' in request.json else 2
    mrz_size: int = request.json.get('mrz_size') if 'mrz_size' in request.json else 88

    mrz_chunks: list = extract_mrz(content, mrz_size=mrz_size, lines=lines, types=types)
    mrz = ''.join(mrz_chunks)

    parsed_result = parse_mrz(mrz)

    return jsonify(parsed_result.serialize())
