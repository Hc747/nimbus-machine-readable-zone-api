from app import app
from arguments import args

if __name__ == '__main__':
    print(f'Arguments: {args}')
    options = dict(
        host='0.0.0.0',
        debug=args.debug,
        port=args.port,
        threaded=True
    )

    app.run(**options)
