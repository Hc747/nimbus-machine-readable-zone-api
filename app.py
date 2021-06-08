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

http_status_ok: int = 200
http_status_unprocessable_entity: int = 422
http_status_internal_server_error: int = 500

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
        output, status = result.serialize(), http_status_ok
    except FieldError as e:
        output, status = {'success': False, 'message': 'Exception: \'%s\', Cause: \'%s\'' % (e.msg, e.cause)}, http_status_unprocessable_entity
    except:
        output, status = {'success': False, 'message': 'Unable to process request.'}, http_status_internal_server_error
    return jsonify(output), status


# Allow CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
