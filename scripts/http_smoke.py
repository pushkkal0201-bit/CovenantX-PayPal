"""Real localhost HTTP smoke; fixture review only; no external calls or payments."""
import os,sys,subprocess,socket,time,tempfile,json,secrets
from pathlib import Path
import httpx
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'apps/api'))
from covenantx.domain import now
with tempfile.TemporaryDirectory() as td:
    env=dict(os.environ,CLIENT_TOKEN=secrets.token_urlsafe(32),VENDOR_TOKEN=secrets.token_urlsafe(32),DATABASE_URL='sqlite:///'+str(Path(td)/'smoke.db'),PYTHONPATH=str(root/'apps/api'))
    # Keep this smoke independent of the caller's provider credentials.
    for key in ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','GEMINI_API_KEY','GEMINI_MODEL']:env.pop(key,None)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','uvicorn','covenantx.main:app','--host','127.0.0.1','--port',str(port)],env=env,cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}',trust_env=False,timeout=5) as client:
            for _ in range(100):
                try:
                    health=client.get('/api/health');health.raise_for_status();break
                except httpx.TransportError:time.sleep(.05)
            else:raise RuntimeError('API did not start')
            def call(path,body,role='CLIENT_TOKEN'):
                response=client.post('/api'+path,json=body,headers={'Authorization':'Bearer '+env[role]});response.raise_for_status();return response.json()
            contract={'title':'HTTP smoke / fixture','source_text':'5000 USD. Minimum coverage 85 percent. Deduction 500 USD.','amount':'5000.00','currency':'USD','commit_sha':'a'*40,'clauses':[{'id':'COVERAGE','metric':'coverage','operator':'gte','threshold':'85','deduction':'500.00','text':'Coverage must reach 85 percent.'}]}
            evidence={'commit_sha':'a'*40,'artifact_id':'fixture-http','source_url':'fixture://http-smoke','observed_at':now(),'content':'DEMONSTRATION: Coverage is 78 percent.','metrics':{'coverage':'78'},'demonstration':True}
            d=call('/milestones',contract);base='/milestones/'+d['id']
            d=call(base+'/approve-contract',{'version':d['version']})
            formats={'coverage.json':'coverage-py-json','k6-summary.json':'k6-summary-json','security.sarif':'sarif-2.1-json','delivery.md':'documentation-text'}
            bundle={k:evidence[k] for k in ['commit_sha','artifact_id','source_url','observed_at','demonstration']}
            bundle['artifacts']=[{'name':name,'format':fmt,'content':(root/'demo'/'reports'/name).read_text()} for name,fmt in formats.items()]
            d=call(base+'/evidence/import?version='+str(d['version']),bundle,'VENDOR_TOKEN')
            d=call(base+'/attest',{'version':d['version'],'note':'Inspected demonstration fixture, not real evidence'})
            d=call(base+'/verify',{'version':d['version'],'mode':'fixture'})
            simulated=call(base+'/simulate',{'coverage':'90'})
            denied=client.post('/api'+base+'/approve-settlement',json={'version':d['version']},headers={'Authorization':'Bearer '+env['CLIENT_TOKEN']})
            replay=client.get('/api'+base+'/replay',headers={'Authorization':'Bearer '+env['CLIENT_TOKEN']});replay.raise_for_status()
            assert replay.json()['passed']
            passport=client.get('/api'+base+'/passport',headers={'Authorization':'Bearer '+env['CLIENT_TOKEN']});passport.raise_for_status()
            passport_file=Path(td)/'passport.json';passport_file.write_text(passport.text)
            checked=subprocess.run([sys.executable,str(root/'scripts/passport.py'),str(passport_file),'--replay','--report',str(Path(td)/'report.md')],check=True,capture_output=True,text=True)
            assert 'PASS: artifact_derivation' in checked.stdout
            assert d['proposal']['amount']=='4500.00' and simulated['scenario']['amount']=='5000.00' and denied.status_code==409
            print(json.dumps({'transport':'real localhost HTTP','health_status':health.status_code,'review_mode':d['verification']['receipt']['mode'],'current':'4500.00','hypothetical':'5000.00','fixture_authorization_status':denied.status_code,'imported_reports':len(bundle['artifacts']),'policy_replay':'PASS','offline_cli_replay':'PASS','external_services_called':False,'result':'PASS'},indent=2))
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
