import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
import pytest
from fastapi.testclient import TestClient
from covenantx.main import create_app
from covenantx.domain import digest
from conftest import headers,post,prepare

def test_complete_flow_and_duplicate_click(harness,contract,evidence):
    c,p,app=harness;d=prepare(c,contract,evidence)
    assert d['proposal']['amount']=='4500.00'
    d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    assert d['state']=='ORDER_CREATED' and p.creates==1
    d=post(c,d,'order').json();assert p.creates==1
    p.status='APPROVED';d=post(c,d,'capture').json()
    assert d['state']=='COMPLETED' and d['payment']['capture_id']=='TEST-CAPTURE'
    post(c,d,'capture');assert p.captures==1

def test_auth_and_role_boundaries(harness,contract,evidence):
    c,_,_=harness
    assert c.get('/api/milestones').status_code==401
    assert c.post('/api/milestones',headers=headers('vendor'),json=contract).status_code==403
    d=prepare(c,contract,evidence)
    assert post(c,d,'approve-settlement',role='vendor').status_code==403
    assert c.get('/api/milestones/missing',headers=headers()).status_code==404

def test_stale_revision_cannot_approve(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    assert post(c,d,'approve-settlement').status_code==200
    assert post(c,d,'approve-settlement').status_code==409

def test_concurrent_approval_has_one_winner(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    with ThreadPoolExecutor(2) as executor:
        results=list(executor.map(lambda _:post(c,d,'approve-settlement').status_code,range(2)))
    assert sorted(results)==[200,409]

def test_fixture_cannot_authorize(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence,'fixture')
    assert post(c,d,'approve-settlement').status_code==409

def test_demo_evidence_cannot_authorize(harness,contract,evidence):
    c,_,_=harness;evidence['demonstration']=True;d=prepare(c,contract,evidence)
    assert post(c,d,'approve-settlement').status_code==409

def test_dispute_invalidates_approval(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json()
    d=post(c,d,'dispute',{'note':'Measurement is disputed'},'vendor').json()
    assert d['settlement_approval'] is None
    assert post(c,d,'order').status_code==409
    d=post(c,d,'resolve',{'note':'Evidence corrected and accepted'},'vendor').json()
    assert post(c,d,'approve-settlement').status_code==200

def test_new_evidence_invalidates_decision(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json()
    r=c.post(f"/api/milestones/{d['id']}/evidence?version={d['version']}",headers=headers('vendor'),json=evidence)
    assert r.status_code==200
    assert r.json()['proposal'] is None and r.json()['settlement_approval'] is None

def test_order_locks_disputes(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    assert post(c,d,'dispute',{'note':'Late challenge'},'vendor').status_code==409

def test_simulator_does_not_write(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    r=c.post(f"/api/milestones/{d['id']}/simulate",headers=headers(),json={'coverage':90})
    assert r.json()['scenario']['amount']=='5000.00'
    assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()==d

def test_passport_and_graph(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    passport=c.get(f"/api/milestones/{d['id']}/passport",headers=headers()).json()
    assert digest(passport['payload'])==passport['sha256']
    passport['payload']['record']['title']='tampered'
    assert digest(passport['payload'])!=passport['sha256']
    graph=c.get(f"/api/milestones/{d['id']}/graph",headers=headers()).json()
    assert len(graph['edges'])==3

def test_unknown_create_uses_same_key(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();p.fail_create=True
    assert post(c,d,'order').status_code==502
    d=c.get(f"/api/milestones/{d['id']}",headers=headers()).json();key=d['payment']['create_key']
    assert post(c,d,'order').status_code==409
    p.fail_create=False;d=post(c,d,'reconcile').json()
    assert d['state']=='ORDER_CREATED' and d['payment']['create_key']==key

def test_unknown_capture_is_reconciled_without_recapture(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json();p.status='APPROVED';p.fail_capture=True
    assert post(c,d,'capture').status_code==502
    d=c.get(f"/api/milestones/{d['id']}",headers=headers()).json();assert d['state']=='CAPTURE_UNKNOWN'
    assert post(c,d,'capture').status_code==409
    d=post(c,d,'reconcile').json();assert d['state']=='COMPLETED' and p.captures==1

def test_provider_amount_mismatch_fails_closed(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();p.amount_override='0.01'
    assert post(c,d,'order').status_code==502
    d=c.get(f"/api/milestones/{d['id']}",headers=headers()).json();assert d['state']=='CREATE_UNKNOWN'

def test_buyer_approval_required(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    assert post(c,d,'capture').status_code==409 and p.captures==0

def test_webhook_forgery_and_replay(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    event={'id':'event-1','resource':{'supplementary_data':{'related_ids':{'order_id':'TEST-ORDER'}}}}
    p.signature=False;assert c.post('/api/webhooks/paypal',json=event).status_code==400
    p.signature=True;p.status='COMPLETED'
    assert c.post('/api/webhooks/paypal',json=event).json()['duplicate']==False
    assert c.post('/api/webhooks/paypal',json=event).json()['duplicate']==True
    assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()['state']=='COMPLETED'

def test_persistence_across_application_restart(tmp_path,env,contract):
    url='sqlite:///'+str(tmp_path/'restart.db')
    with TestClient(create_app(url)) as c:d=c.post('/api/milestones',headers=headers(),json=contract).json()
    with TestClient(create_app(url)) as c:assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()==d

def test_missing_external_credentials_fail_closed(harness,contract,evidence,monkeypatch):
    c,_,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();monkeypatch.delenv('PAYPAL_CLIENT_SECRET')
    assert post(c,d,'order').status_code==503

@pytest.mark.parametrize('field,value',[('observed_at','2020-01-01T00:00:00+00:00'),('commit_sha','b'*40)])
def test_untrusted_provenance_blocks_attestation(harness,contract,evidence,field,value):
    c,_,_=harness;evidence[field]=value
    d=c.post('/api/milestones',headers=headers(),json=contract).json();d=post(c,d,'approve-contract').json()
    d=c.post(f"/api/milestones/{d['id']}/evidence?version={d['version']}",headers=headers('vendor'),json=evidence).json()
    assert post(c,d,'attest',{'note':'I reviewed this artifact'}).status_code==409

def test_completed_payment_cannot_regress(harness,contract,evidence):
    c,p,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json();p.status='APPROVED';d=post(c,d,'capture').json()
    p.status='APPROVED';assert post(c,d,'reconcile').status_code==502
    current=c.get(f"/api/milestones/{d['id']}",headers=headers()).json()
    assert current['state']=='COMPLETED'
    post(c,current,'capture');assert p.captures==1

def test_expired_unknown_create_is_not_retried(harness,contract,evidence):
    c,p,app=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();p.fail_create=True;post(c,d,'order')
    d=app.state.store.get(d['id']);d['payment']['started_at']=(datetime.now(timezone.utc)-timedelta(hours=7)).isoformat();d=app.state.store.save(d,d['version'],'test','test.expired')
    p.fail_create=False;assert post(c,d,'reconcile').status_code==409 and p.creates==1

def test_ai_failure_is_not_replaced_by_fixture(tmp_path,env,contract,evidence,monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    with TestClient(create_app('sqlite:///'+str(tmp_path/'ai.db'))) as c:
        d=c.post('/api/milestones',headers=headers(),json=contract).json();d=post(c,d,'approve-contract').json()
        d=c.post(f"/api/milestones/{d['id']}/evidence?version={d['version']}",headers=headers('vendor'),json=evidence).json()
        d=post(c,d,'attest',{'note':'Manual provenance inspection'}).json()
        assert post(c,d,'verify',{'mode':'gemini'}).status_code==503
        assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()['verification'] is None
