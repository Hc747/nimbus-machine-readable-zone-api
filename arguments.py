import argparse
import os

p = argparse.ArgumentParser()
p.add_argument('-p', '--port', default=os.getenv('PORT', 80), type=int, help='The port to bind the HTTP service to.')
p.add_argument('-d', '--debug', default=os.getenv('DEBUG', False), type=bool, help='Whether or not to run the application in debug mode.')
args = p.parse_args()
