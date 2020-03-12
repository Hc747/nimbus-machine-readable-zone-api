from mrz.checker.td3 import TD3CodeChecker, get_country
from flask import Flask, jsonify, render_template, request

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


# TODO: more intelligently identify the start of the MRZ
def extract_mrz(content, mrz_size=88):
    formatted = ''.join(content.split()).replace('«', '<')
    length = len(formatted)
    result = formatted[length - mrz_size:].upper() if length >= mrz_size else content  #TODO: raise exception
    return result


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
    content = request.json.get('content')
    mrz = extract_mrz(content)
    parsed_result = parse_mrz(mrz)
    return jsonify(parsed_result.serialize())
