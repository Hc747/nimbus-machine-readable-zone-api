import os
from app import app

port = os.getenv("PORT")
debug = os.getenv("DEBUG")

if __name__ == '__main__':
    opts = dict(
        host='0.0.0.0',
        debug=False if debug is None else bool(debug),
        port=80 if port is None else int(port),
        threaded=True
    )

    app.run(**opts)
