"""Cross-platform launcher: loads local .env without a shell or secret output."""
import os,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.chdir(root)
for line in (root/'.env').read_text().splitlines():
    if line and not line.startswith('#') and '=' in line:
        key,value=line.split('=',1);os.environ.setdefault(key,value)
sys.path.insert(0,str(root/'apps/api'))
import uvicorn
uvicorn.run('covenantx.main:app',host='127.0.0.1',port=8000)
