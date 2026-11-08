import copy
import json
from datetime import datetime,timezone,timedelta
import pytest
from covenantx.domain import digest
from covenantx.replay import replay_record
from conftest import headers,post,prepare
from test_artifacts import reports,bundle_for

def test_edit_draft_and_freeze(harness,contract):
    c,_,_=harness;d=c.post('/api/milestones',headers=headers(),json=contract).json()
    contract['amount']='6000.00'
    d=post(c,d,'contract',{'contract':contract}).json();assert d['contract']['amount']=='6000.00'
    assert d['contract_hash']==digest(d['contract'])
    d=post(c,d,'approve-contract').json()
    assert post(c,d,'contract',{'contract':contract}).status_code==409

def test_parsed_import_then_offline_replay(harness,contract,reports):
    c,_,_=harness;d=c.post('/api/milestones',headers=headers(),json=contract).json();d=post(c,d,'approve-contract').json()
    body=bundle_for(reports).model_dump(mode='json')
    response=c.post(f"/api/milestones/{d['id']}/evidence/import?version={d['version']}",headers=headers('vendor'),json=body)
    assert response.status_code==200,response.text
    d=response.json();assert d['evidence']['metrics']['coverage']=='78'
    assert d['evidence_attestation'] is None
    assert d['evidence_import']['artifacts'][0]['content']==body['artifacts'][0]['content']
    d=post(c,d,'attest',{'note':'Inspected original reports and scope'}).json()
    d=post(c,d,'verify',{'mode':'fixture'}).json()
    result=c.get(f"/api/milestones/{d['id']}/replay",headers=headers()).json()
    assert result['passed'] and not result['external_calls']
    assert any(x['check']=='artifact_derivation' for x in result['checks'])
    changed=copy.deepcopy(d);changed['evidence_import']['artifacts'][0]['content']='{}'
    assert not replay_record(changed)['passed']
    assert post(c,d,'approve-settlement').status_code==409

def test_legacy_record_replay_and_tamper(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    assert replay_record(d)['passed']
    d['proposal']['amount']='1.00'
    assert not replay_record(d)['passed']

def test_replay_uses_historical_time(harness,contract,evidence):
    c,_,_=harness;d=prepare(c,contract,evidence)
    # Shift all evidence/verification timestamps together into the past, then rebind hashes.
    old=(datetime.now(timezone.utc)-timedelta(days=50)).isoformat()
    d['evidence']['observed_at']=old;d['evidence_hash']=digest(d['evidence'])
    d['verification']['at']=old;d['verification']['evidence_hash']=d['evidence_hash']
    d['evidence_attestation']['hash']=d['evidence_hash']
    assert replay_record(d)['passed']

def test_import_failure_preserves_previous_approval(harness,contract,evidence,reports):
    c,_,_=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json()
    body=bundle_for(reports).model_dump(mode='json');body['artifacts'][0]['content']='{}'
    r=c.post(f"/api/milestones/{d['id']}/evidence/import?version={d['version']}",headers=headers('vendor'),json=body)
    assert r.status_code==422
    assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()==d

def interrupted(harness,contract,evidence,state='CREATING'):
    c,p,app=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    d['state']=state;d['payment']['operation_started_at']=(datetime.now(timezone.utc)-timedelta(minutes=3)).isoformat()
    if state=='CREATING':d['payment'].pop('order_id')
    return app.state.store.save(d,d['version'],'test','simulate.process_crash')

def test_recovery_of_interrupted_create_is_get_only(harness,contract,evidence):
    c,p,_=harness;d=interrupted(harness,contract,evidence);before=p.creates
    r=post(c,d,'recover',{'order_id':'TEST-ORDER','note':'Matched order in sandbox dashboard'})
    assert r.status_code==200,r.text
    assert r.json()['state']=='ORDER_CREATED' and p.creates==before and p.captures==0
    assert r.json()['recovery_events'][0]['method']=='GET only'

def test_recovery_of_interrupted_capture_never_recaptures(harness,contract,evidence):
    c,p,_=harness;d=interrupted(harness,contract,evidence,'CAPTURING');p.status='COMPLETED'
    r=post(c,d,'recover',{'order_id':'TEST-ORDER','note':'Inspected provider capture details'})
    assert r.json()['state']=='COMPLETED' and p.captures==0

def test_recovery_refuses_amount_mismatch_and_wrong_role(harness,contract,evidence):
    c,p,_=harness;d=interrupted(harness,contract,evidence);p.amount_override='1.00'
    body={'order_id':'TEST-ORDER','note':'Candidate dashboard order'}
    assert post(c,d,'recover',body,'vendor').status_code==403
    assert post(c,d,'recover',body).status_code==502
    assert c.get(f"/api/milestones/{d['id']}",headers=headers()).json()==d

def test_recovery_grace_and_order_binding(harness,contract,evidence):
    c,p,app=harness;d=interrupted(harness,contract,evidence,'CAPTURE_UNKNOWN')
    assert post(c,d,'recover',{'order_id':'WRONG-ID','note':'Candidate dashboard order'}).status_code==409
    d['payment']['operation_started_at']=datetime.now(timezone.utc).isoformat();d=app.state.store.save(d,d['version'],'test','recent')
    assert post(c,d,'recover',{'order_id':'TEST-ORDER','note':'Candidate dashboard order'}).status_code==409

def test_capture_uncertainty_survives_unusual_provider_status(harness,contract,evidence):
    c,p,app=harness;d=prepare(c,contract,evidence);d=post(c,d,'approve-settlement').json();d=post(c,d,'order').json()
    p.status='APPROVED';p.fail_capture=True;post(c,d,'capture')
    d=app.state.store.get(d['id']);assert d['payment']['capture_submitted']
    p.status='SAVED';d=post(c,d,'reconcile').json();assert d['state']=='PROVIDER_REVIEW'
    p.status='APPROVED';d=post(c,d,'reconcile').json();assert d['state']=='CAPTURE_UNKNOWN'
    assert post(c,d,'capture').status_code==409 and p.captures==1

def test_streaming_body_limit(harness):
    c,_,_=harness
    r=c.post('/api/milestones',headers=headers(),content=(b'x'*500001 for _ in range(2)))
    assert r.status_code==413

def test_graph_ids_cannot_collide_with_contract_node(harness,contract,evidence):
    c,_,_=harness;contract['clauses'][0]['id']='contract';d=prepare(c,contract,evidence)
    graph=c.get(f"/api/milestones/{d['id']}/graph",headers=headers()).json()
    assert len({n['id'] for n in graph['nodes']})==len(graph['nodes'])

def test_legacy_provider_review_cannot_reopen_capture(harness,contract,evidence):
    c,p,app=harness
    d=interrupted(harness,contract,evidence,'PROVIDER_REVIEW')
    d['payment'].pop('capture_submitted',None)
    d=app.state.store.save(d,d['version'],'test','legacy.no_capture_marker')
    p.status='APPROVED'
    d=post(c,d,'reconcile').json()
    assert d['state']=='CAPTURE_UNKNOWN'
    assert post(c,d,'capture').status_code==409
    assert p.captures==0
