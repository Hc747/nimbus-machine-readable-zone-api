from typing import List

from flask import Flask, jsonify, request
from mrz.base.errors import FieldError
from mrz.checker.mrva import MRVACodeChecker
from mrz.checker.mrvb import MRVBCodeChecker
from mrz.checker.td1 import TD1CodeChecker
from mrz.checker.td2 import TD2CodeChecker
from mrz.checker.td3 import TD3CodeChecker

from constants import alpha
from parser import MRZParser

app_name: str = "MRZ Parser"
app_version: str = "2.0"
app = Flask(app_name)

unprocessable_entity = 422
internal_server_error = 500

default_implementation: str = 'TD3'
empty_types: List[str] = []  # determine document types
mrz_definitions: map = {
    'TD1': MRZParser(30, 3, empty_types, TD1CodeChecker),
    'TD2': MRZParser(36, 2, empty_types, TD2CodeChecker),
    'TD3': MRZParser(44, 2, ['P<', 'P0'] + ['P' + char for char in alpha], TD3CodeChecker),
    'MRVA': MRZParser(44, 2, empty_types, MRVACodeChecker),
    'MRVB': MRZParser(36, 2, empty_types, MRVBCodeChecker)
}


@app.route('/')
def version():
    return '%s version: %s' % (app_name, app_version)


@app.route('/api/machine_readable_zone', methods=['POST'])
def parse_machine_readable_zone():
    try:
        identifier: str = request.json.get('implementation') if 'implementation' in request.json else default_implementation
        identifier = identifier if identifier in mrz_definitions.keys() else default_implementation

        content: str = request.json.get('content')
        parser: MRZParser = mrz_definitions.get(identifier)
        result = parser.parse(content)

        return jsonify(result.serialize())
    except FieldError as e:
        result = {'success': False, 'message': 'Exception: \'%s\', Cause: \'%s\'' % (e.msg, e.cause)}
        return jsonify(result), unprocessable_entity
    except:
        result = {'success': False, 'message': 'Unable to process request.'}
        return jsonify(result), internal_server_error


# Allow CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
