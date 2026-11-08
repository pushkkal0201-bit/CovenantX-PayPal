"""Verify a passport digest, optionally replay policy, and export a readable report."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'apps/api'))
from covenantx.domain import digest
from covenantx.replay import replay_record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--replay',action='store_true',help='Reparse artifacts and recompute the historical settlement without external calls')
    parser.add_argument('--report',help='Write a readable Markdown report')
    args=parser.parse_args()
    document=json.loads(Path(args.file).read_text(encoding='utf-8'))
    if digest(document['payload'])!=document['sha256']:
        raise SystemExit('FAIL: integrity digest does not match')
    record=document['payload']['record']
    print('PASS: canonical SHA-256 matches (not a signature)')
    replay=replay_record(record) if args.replay else None
    if replay:
        for check in replay['checks']:
            print(('PASS' if check['passed'] else 'FAIL')+': '+check['check']+' — '+check['detail'])
    if args.report:
        lines=['# CovenantX Evidence Passport','',record['title'],'',f"State: {record['state']}",f"Revision: {record['version']}",f"Contract hash: {record['contract_hash']}",'','## Settlement','','```json',json.dumps(record['proposal'],indent=2),'```','','## Payment','','```json',json.dumps(record['payment'],indent=2),'```']
        if replay:
            lines.extend(['','## Policy replay','',*[(('PASS' if x['passed'] else 'FAIL')+': '+x['check']+' — '+x['detail']) for x in replay['checks']]])
        lines.extend(['','## Assurance limits','',document['payload']['integrity_scope']])
        Path(args.report).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if replay and not replay['passed']:
        raise SystemExit(1)

if __name__=='__main__':main()
