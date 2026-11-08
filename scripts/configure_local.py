"""Creates unique local credentials without printing them. Will not overwrite .env."""
from pathlib import Path
import secrets
p=Path(__file__).resolve().parents[1]/'.env'
text=p.with_name('.env.example').read_text()
for name in ['CLIENT_TOKEN','VENDOR_TOKEN','POSTGRES_PASSWORD']:
    text=text.replace(name+'=\n',name+'='+secrets.token_urlsafe(32)+'\n')
with p.open('x') as f:f.write(text)
p.chmod(0o600)
print('Created .env. Open it locally to configure external sandbox credentials.')
