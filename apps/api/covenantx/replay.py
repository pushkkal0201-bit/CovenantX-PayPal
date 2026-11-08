"""Offline policy replay. This checks internal consistency, not document authenticity."""
from datetime import datetime
from .domain import Contract, Evidence, Assessment, POLICY, digest, settlement
from .artifacts import Bundle, parse_bundle

def replay_record(record):
    checks = []
    def add(name,ok,detail):checks.append({'check':name,'passed':bool(ok),'detail':detail})
    try:
        contract=Contract.model_validate(record['contract'])
        evidence=Evidence.model_validate(record['evidence'])
        verification=record['verification']
        if not verification:raise ValueError('No verification is recorded')
        assessment=Assessment.model_validate(verification['assessment'])
        at=datetime.fromisoformat(verification['at'])
        if at.tzinfo is None:raise ValueError('Verification timestamp has no timezone')
        add('contract_hash',digest(record['contract'])==record['contract_hash'],'Original structured contract')
        add('evidence_hash',digest(record['evidence'])==record['evidence_hash'],'Original evidence serialization')
        add('verification_inputs',verification['contract_hash']==record['contract_hash'] and verification['evidence_hash']==record['evidence_hash'],'Review is bound to current inputs')
        add('attestation',record.get('evidence_attestation',{}).get('hash')==record['evidence_hash'],'Human attestation bound to evidence')
        if record.get('evidence_import'):
            parsed,receipt=parse_bundle(Bundle.model_validate(record['evidence_import']))
            add('artifact_derivation',digest(parsed.model_dump(mode='json'))==digest(evidence.model_dump(mode='json')),'Reparse original uploaded files')
            add('parser_receipt',digest(receipt)==digest(record.get('evidence_provenance')),'Artifact bytes, hashes and parser interpretation')
        add('policy_version',record['proposal']['policy']==POLICY,'Only this installed policy is replayed')
        proposal=settlement(contract,evidence,assessment,at=at)
        add('settlement_replay',digest(proposal)==digest(record['proposal']),'Recomputed at recorded verification time; no model or provider call')
        if record.get('settlement_approval'):
            snapshot=digest({'proposal':record['proposal'],'verification':verification,'attestation':record['evidence_attestation']})
            add('approval_snapshot',snapshot==record['settlement_approval']['hash'],'Client approved this exact decision')
            if record.get('payment'):
                add('payment_binding',snapshot==record['payment']['snapshot_hash'],'Provider intent tied to approved decision')
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        add('record_structure',False,str(exc)[:300])
    return {'passed':bool(checks) and all(x['passed'] for x in checks),'checks':checks,'external_calls':False,'limitations':'Consistency only; a valid digest and replay do not prove authentic evidence, model execution or provider success.'}
