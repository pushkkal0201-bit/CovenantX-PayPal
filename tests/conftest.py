import pytest
from fastapi.testclient import TestClient
from covenantx.main import create_app
from covenantx.ai import assess
from covenantx.domain import now

CLIENT='c'*40;VENDOR='v'*40
@pytest.fixture
def contract():
    return {'title':'Atlas milestone','source_text':'USD 5000. Coverage >=85%, deduction 500 USD.','amount':'5000.00','currency':'USD','commit_sha':'a'*40,'clauses':[{'id':'SLA-01','metric':'coverage','operator':'gte','threshold':'85','deduction':'500.00','text':'Coverage must reach 85 percent.'}]}
@pytest.fixture
def evidence():
    return {'commit_sha':'a'*40,'artifact_id':'ci-104','source_url':'https://github.com/example/repo/actions/runs/104','observed_at':now(),'content':'Coverage is 78 percent.','metrics':{'coverage':'78'},'demonstration':False}
class FakeProvider:
    """Test double only. Never installed in the runtime application."""
    def __init__(self):self.creates=0;self.captures=0;self.status='CREATED';self.fail_create=False;self.fail_capture=False;self.signature=True;self.amount_override=None
    def response(self,d):
        amount={'currency_code':'USD','value':self.amount_override or d['proposal']['amount']}
        unit={'reference_id':d['id'],'custom_id':d['payment']['snapshot_hash'],'amount':amount}
        if self.status=='COMPLETED':unit['payments']={'captures':[{'id':'TEST-CAPTURE','status':'COMPLETED','amount':amount}]}
        return {'id':'TEST-ORDER','status':self.status,'purchase_units':[unit],'links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=TEST-ORDER'}]}
    async def create(self,d):
        self.creates+=1
        if self.fail_create:raise TimeoutError()
        return self.response(d)
    async def get(self,d):return self.response(d)
    async def capture(self,d):
        self.captures+=1;self.status='COMPLETED'
        if self.fail_capture:raise TimeoutError()
        return self.response(d)
    async def verify_webhook(self,event,headers):return self.signature
async def test_reviewer(c,e,mode):
    a,r=await assess(c,e,'fixture')
    # The integration test injects a provider double; this is NOT proof of Gemini execution.
    if mode=='gemini':r={'mode':'GEMINI','model':'TEST-DOUBLE','stages':[]}
    return a,r
@pytest.fixture
def env(monkeypatch):
    for k,v in {'CLIENT_TOKEN':CLIENT,'VENDOR_TOKEN':VENDOR,'PAYPAL_CLIENT_ID':'test','PAYPAL_CLIENT_SECRET':'test'}.items():monkeypatch.setenv(k,v)
@pytest.fixture
def harness(tmp_path,env):
    p=FakeProvider();app=create_app('sqlite:///'+str(tmp_path/'test.db'),p,test_reviewer)
    with TestClient(app) as client:yield client,p,app

def headers(role='client'):return {'Authorization':'Bearer '+(CLIENT if role=='client' else VENDOR)}
def post(client,d,action,body=None,role='client'):
    return client.post(f"/api/milestones/{d['id']}/{action}",headers=headers(role),json={'version':d['version'],**(body or {})})
def prepare(client,contract,evidence,mode='gemini'):
    r=client.post('/api/milestones',headers=headers(),json=contract);assert r.status_code==201,r.text
    d=post(client,r.json(),'approve-contract').json()
    r=client.post(f"/api/milestones/{d['id']}/evidence?version={d['version']}",headers=headers('vendor'),json=evidence);assert r.status_code==200,r.text
    d=post(client,r.json(),'attest',{'note':'Inspected source and measurement'}).json()
    r=post(client,d,'verify',{'mode':mode});assert r.status_code==200,r.text
    return r.json()
