import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('preflight', Path(__file__).resolve().parents[1] / 'scripts/preflight.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def config():
    return {'CLIENT_TOKEN': 'c' * 32, 'VENDOR_TOKEN': 'v' * 32}


def test_fixture_needs_no_provider_credentials():
    assert p.inspect_config(config())['passed']
    assert not p.inspect_config(config(), 'sandbox')['passed']


def test_sandbox_report_never_contains_credentials():
    values = config()
    values.update({k: 'secret-value-' + k for k in ('GEMINI_API_KEY', 'GEMINI_MODEL', 'PAYPAL_CLIENT_ID', 'PAYPAL_CLIENT_SECRET')})
    report = p.inspect_config(values, 'sandbox')
    assert report['passed'] and not report['external_calls']
    assert all(value not in json.dumps(report) for value in values.values())
    assert not p.inspect_config(values, 'sandbox', webhook=True)['passed']


def test_invalid_origins_and_duplicate_tokens_fail():
    for origin in ('https://user:pass@example.com', 'https://example.com/path', 'https://example.com?x=y', 'https://example.com:invalid', 'javascript:alert(1)'):
        assert not p.inspect_config(dict(config(), PUBLIC_WEB_URL=origin))['passed']
    assert not p.inspect_config(dict(config(), VENDOR_TOKEN='c' * 32))['passed']


def test_environment_takes_precedence_without_modifying_file(tmp_path):
    env = tmp_path / '.env'
    env.write_text('CLIENT_TOKEN=file\n# comment\nVENDOR_TOKEN=vendor\n')
    before = env.read_bytes()
    assert p.load_config(env, {'CLIENT_TOKEN': 'environment'})['CLIENT_TOKEN'] == 'environment'
    assert env.read_bytes() == before
    assert p.load_config(tmp_path / 'absent', {}) == {}
