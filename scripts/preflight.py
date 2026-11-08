"""Check configuration locally; never contact providers or print secret values."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


def load_config(path, environ):
    values = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                values[key] = value
    values.update(environ)  # Same precedence as run_api.py.
    return values


def inspect_config(values, mode='fixture', webhook=False):
    checks = []
    def check(name, passed, remedy):
        checks.append({'check': name, 'passed': bool(passed),
                       'detail': 'Configured' if passed else remedy})
    client, vendor = (values.get(k, '') for k in ('CLIENT_TOKEN', 'VENDOR_TOKEN'))
    check('role_tokens', len(client) >= 32 and len(vendor) >= 32 and client != vendor,
          'Set distinct CLIENT_TOKEN and VENDOR_TOKEN values of at least 32 characters.')
    try:
        url = urlsplit(values.get('PUBLIC_WEB_URL', 'http://localhost:3000'))
        port = url.port
        origin_ok = (url.scheme in ('http', 'https') and bool(url.hostname)
                     and not url.username and not url.password
                     and url.path in ('', '/') and not url.query and not url.fragment
                     and not any(c.isspace() for c in url.netloc))
    except ValueError:
        origin_ok = False
    check('web_origin', origin_ok, 'Set PUBLIC_WEB_URL to an HTTP(S) origin without credentials, path, query or fragment.')
    db = values.get('DATABASE_URL', 'sqlite:///./covenantx.db')
    check('database_driver', db.startswith(('sqlite:///', 'postgresql+psycopg://')),
          'Use a SQLite or postgresql+psycopg SQLAlchemy URL.')
    if mode == 'sandbox':
        for name in ('GEMINI_API_KEY', 'GEMINI_MODEL', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET'):
            check(name.lower(), bool(values.get(name, '').strip()), 'Configure ' + name + ' locally.')
    if webhook:
        check('paypal_webhook_id', bool(values.get('PAYPAL_WEBHOOK_ID', '').strip()),
              'Configure the registered sandbox PAYPAL_WEBHOOK_ID.')
    return {'mode': mode, 'passed': all(c['passed'] for c in checks), 'checks': checks,
            'external_calls': False,
            'scope': 'Configuration only. Does not verify credential validity, model access, database connectivity, webhook delivery or payments.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=Path(__file__).resolve().parents[1] / '.env')
    parser.add_argument('--mode', choices=('fixture', 'sandbox'), default='fixture')
    parser.add_argument('--webhook', action='store_true', help='Also require a registered webhook ID')
    parser.add_argument('--json', action='store_true', help='Emit a report without configuration values')
    args = parser.parse_args()
    try:
        result = inspect_config(load_config(args.env_file, os.environ), args.mode, args.webhook)
    except (OSError, UnicodeError):
        parser.exit(2, 'Unable to read the configuration file. Check its path, permissions and UTF-8 encoding.\n')
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result['checks']:
            print(f"{'PASS' if item['passed'] else 'FAIL'} {item['check']}: {item['detail']}")
        print(result['scope'])
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
