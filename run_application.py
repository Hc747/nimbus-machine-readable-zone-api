import os

from app import app

port = os.getenv("PORT")
debug = os.getenv("DEBUG")

if __name__ == '__main__':
    _port = 80 if port is None else int(port)
    _debug = False if debug is None else bool(debug)
    options = dict(
        host='0.0.0.0',
        debug=_debug,
        port=_port,
        threaded=True
    )

    app.run(**options)
