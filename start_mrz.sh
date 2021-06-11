#!/usr/bin/env sh

port=80

python3 -m pip install -r requirements.txt
python3 run_application.py -p $port
