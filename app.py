from flask import Flask

server = Flask(__name__)

@server.route('/')
def hello_world():
    return 'Hello Joe & Harrison!'
