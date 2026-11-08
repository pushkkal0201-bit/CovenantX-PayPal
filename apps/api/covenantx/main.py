import asyncio
import hmac
import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .domain import Contract,Evidence,Revision,Review,Verify,Simulation,Assessment,settlement,trust,now,digest,ContractEdit,Recovery
from .artifacts import Bundle,parse_bundle
from .replay import replay_record
from .middleware import BodyLimitMiddleware
from .store import Store,Webhook
from .ai import assess
from .paypal import PayPal,validate_order,approval_link

LOCKED={'CREATING','CREATE_UNKNOWN','ORDER_CREATED','CAPTURING','CAPTURE_UNKNOWN','COMPLETED','PROVIDER_REVIEW'}
def create_app(database_url=None,provider=None,reviewer=None):
    store=Store(database_url or os.getenv('DATABASE_URL','sqlite:///./covenantx.db'))
    paypal=provider or PayPal(); ai=reviewer or assess
    @asynccontextmanager
    async def lifespan(app):
        ct,vt=os.getenv('CLIENT_TOKEN',''),os.getenv('VENDOR_TOKEN','')
        if len(ct)<32 or len(vt)<32 or ct==vt: raise RuntimeError('Set distinct CLIENT_TOKEN and VENDOR_TOKEN (at least 32 characters each)')
        # PostgreSQL schema is managed by Alembic. SQLite is the explicit local mode.
        if store.engine.url.get_backend_name()=='sqlite': store.initialize()
        yield
        store.engine.dispose()
    app=FastAPI(title='CovenantX',version='0.2.0',lifespan=lifespan)
    app.state.store=store
    app.add_middleware(CORSMiddleware,allow_origins=[os.getenv('PUBLIC_WEB_URL','http://localhost:3000').rstrip('/')],allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type'])
    app.add_middleware(BodyLimitMiddleware)
    rates=defaultdict(deque)
    log=logging.getLogger('covenantx.http')
    @app.middleware('http')
    async def guards(request:Request,call_next):
        response=await call_next(request)
        log.info(json.dumps({'event':'http.response','method':request.method,'path':request.url.path,'status':response.status_code}))
        response.headers['Cache-Control']='no-store'; response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        return response
    def identity(authorization:str=Header(default='')):
        if not authorization.startswith('Bearer '): raise HTTPException(401,'Bearer token required')
        token=authorization[7:]
        for role,name in [('client','CLIENT_TOKEN'),('vendor','VENDOR_TOKEN')]:
            expected=os.getenv(name,'')
            if len(expected)>=32 and hmac.compare_digest(token,expected):
                q=rates[role]; t=time.monotonic()
                while q and q[0]<t-60:q.popleft()
                if len(q)>=120:raise HTTPException(429,'Rate limit: 120 requests per minute per role')
                q.append(t); return role
        raise HTTPException(401,'Invalid token')
    def client(role=Depends(identity)):
        if role!='client': raise HTTPException(403,'Client approval role required')
        return role
    def vendor(role=Depends(identity)):
        if role!='vendor':raise HTTPException(403,'Vendor submission role required')
        return role
    def load(id,version=None):
        d=store.get(id)
        if version is not None and d['version']!=version: raise HTTPException(409,'Stale revision; refresh')
        return d
    def editable(d):
        if d['state'] in LOCKED:raise HTTPException(409,'Payment workflow is locked; reconcile before further changes')
    def persist(d,actor,event):return store.save(d,d['version'],actor,event)
    def fresh(d):
        reasons=trust(Contract.model_validate(d['contract']),Evidence.model_validate(d['evidence']))
        if reasons:raise HTTPException(409,'; '.join(reasons))
    @app.get('/api/health')
    def health():
        return {'status':'ready','mode':'sandbox-only','paypal_configured':bool(os.getenv('PAYPAL_CLIENT_ID') and os.getenv('PAYPAL_CLIENT_SECRET')),'ai_configured':bool(os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_MODEL'))}
    @app.get('/api/me')
    def me(role=Depends(identity)):return {'role':role,'workspace':'single client/vendor pair'}
    @app.get('/api/milestones')
    def milestones(role=Depends(identity)): return store.list()
    @app.post('/api/milestones',status_code=201)
    def create(body:Contract,role=Depends(client)):
        d={'id':str(uuid.uuid4()),'title':body.title,'state':'DRAFT','contract':body.model_dump(mode='json'),'contract_hash':digest(body.model_dump(mode='json')),'created_at':now(),'version':0,'evidence':None,'proposal':None,'verification':None,'payment':None,'disputes':[],'approvals':[]}
        return store.save(d,0,role,'contract.created')
    @app.get('/api/milestones/{id}')
    def get(id:str,role=Depends(identity)):return load(id)
    @app.post('/api/milestones/{id}/contract')
    def edit_contract(id:str,body:ContractEdit,role=Depends(client)):
        d=load(id,body.version)
        if d['state']!='DRAFT':raise HTTPException(409,'Approved contract rules are immutable')
        d.update(contract=body.contract.model_dump(mode='json'),title=body.contract.title)
        d['contract_hash']=digest(d['contract'])
        return persist(d,role,'contract.draft_edited')
    @app.post('/api/milestones/{id}/approve-contract')
    def approve_contract(id:str,body:Revision,role=Depends(client)):
        d=load(id,body.version)
        if d['state']!='DRAFT':raise HTTPException(409,'Contract already frozen')
        d['state']='AWAITING_EVIDENCE';d['approvals'].append({'kind':'contract','actor':role,'at':now(),'hash':d['contract_hash']})
        return persist(d,role,'contract.approved')
    @app.post('/api/milestones/{id}/evidence')
    def evidence(id:str,body:Evidence,version:int,role=Depends(vendor)):
        d=load(id,version);editable(d)
        if d['state']=='DRAFT':raise HTTPException(409,'Approve financial rules first')
        d.update(evidence_import=None,evidence_provenance=None,evidence=body.model_dump(mode='json'),evidence_hash=digest(body.model_dump(mode='json')),evidence_attestation=None,proposal=None,verification=None,state='EVIDENCE_SUBMITTED',settlement_approval=None)
        return persist(d,role,'evidence.submitted')
    @app.post('/api/milestones/{id}/evidence/import')
    def import_evidence(id:str,body:Bundle,version:int,role=Depends(vendor)):
        d=load(id,version);editable(d)
        if d['state']=='DRAFT':raise HTTPException(409,'Approve financial rules first')
        try: evidence,receipt=parse_bundle(body)
        except ValueError as exc:raise HTTPException(422,str(exc))
        d.update(evidence=evidence.model_dump(mode='json'),evidence_hash=digest(evidence.model_dump(mode='json')),evidence_import=body.model_dump(mode='json'),evidence_provenance=receipt,evidence_attestation=None,proposal=None,verification=None,settlement_approval=None,state='EVIDENCE_SUBMITTED')
        return persist(d,role,'evidence.imported_from_reports')
    @app.post('/api/milestones/{id}/attest')
    def attest(id:str,body:Review,role=Depends(client)):
        d=load(id,body.version);editable(d)
        if not d['evidence']:raise HTTPException(409,'Submit evidence first')
        fresh(d)
        d['evidence_attestation']={'actor':role,'at':now(),'note':body.note,'hash':d['evidence_hash'],'assurance':'human-attested; source authenticity not independently verified'}
        d.update(proposal=None,verification=None,settlement_approval=None,state='EVIDENCE_ATTESTED')
        return persist(d,role,'evidence.attested')
    @app.post('/api/milestones/{id}/verify')
    async def verify(id:str,body:Verify,role=Depends(client)):
        d=load(id,body.version);editable(d)
        if not d.get('evidence_attestation'):raise HTTPException(409,'Client must attest artifact and measurements first')
        fresh(d)
        try: assessment,receipt=await ai(Contract.model_validate(d['contract']),Evidence.model_validate(d['evidence']),body.mode)
        except Exception: raise HTTPException(503,'AI verification unavailable or invalid; check server configuration and provider access')
        verified_at=now()
        d['proposal']=settlement(Contract.model_validate(d['contract']),Evidence.model_validate(d['evidence']),assessment,at=datetime.fromisoformat(verified_at))
        d['verification']={'id':str(uuid.uuid4()),'at':verified_at,'assessment':assessment.model_dump(),'receipt':receipt,'evidence_hash':d['evidence_hash'],'contract_hash':d['contract_hash']}
        d['state']='PROPOSED' if d['proposal']['eligible'] else 'HELD'
        d['settlement_approval']=None
        return persist(d,role,'verification.completed')
    @app.post('/api/milestones/{id}/dispute')
    def dispute(id:str,body:Review,role=Depends(identity)):
        d=load(id,body.version);editable(d)
        d['disputes'].append({'id':str(uuid.uuid4()),'at':now(),'actor':role,'note':body.note,'resolved':False})
        d['settlement_approval']=None;d['state']='DISPUTED'
        return persist(d,role,'dispute.opened')
    @app.post('/api/milestones/{id}/resolve')
    def resolve(id:str,body:Review,role=Depends(vendor)):
        d=load(id,body.version);editable(d)
        for x in d['disputes']:
            if not x['resolved']:x.update(resolved=True,resolution=body.note,resolved_at=now(),resolved_by=role)
        d['state']='PROPOSED' if d['proposal'] and d['proposal']['eligible'] else 'EVIDENCE_SUBMITTED'
        return persist(d,role,'dispute.resolved_by_vendor')
    @app.post('/api/milestones/{id}/approve-settlement')
    def approve_settlement(id:str,body:Revision,role=Depends(client)):
        d=load(id,body.version);editable(d)
        if d['state']!='PROPOSED' or any(not x['resolved'] for x in d['disputes']):raise HTTPException(409,'Settlement is not eligible or is disputed')
        if d['verification']['receipt']['mode']!='GEMINI' or d['evidence']['demonstration']:raise HTTPException(409,'Fixture or demonstration evidence cannot authorize payment')
        fresh(d)
        snapshot=digest({'proposal':d['proposal'],'verification':d['verification'],'attestation':d['evidence_attestation']})
        d.update(state='APPROVED',settlement_approval={'actor':role,'at':now(),'hash':snapshot})
        return persist(d,role,'settlement.approved')
    @app.post('/api/milestones/{id}/simulate')
    def simulate(id:str,body:Simulation,role=Depends(identity)):
        d=load(id)
        if not d['evidence'] or not d['verification']:raise HTTPException(409,'Verify evidence first')
        ev=Evidence.model_validate(d['evidence']); ev.metrics['coverage']=body.coverage
        assessment=Assessment.model_validate(d['verification']['assessment'])
        for f in assessment.findings:
            clause=next((c for c in Contract.model_validate(d['contract']).clauses if c.id==f.clause_id),None)
            if clause and clause.metric=='coverage':f.verdict='pass' if (body.coverage>=clause.threshold if clause.operator=='gte' else body.coverage<=clause.threshold) else 'fail'
        return {'hypothetical':True,'persisted':False,'current':d['proposal'],'scenario':settlement(Contract.model_validate(d['contract']),ev,assessment)}
    @app.get('/api/milestones/{id}/graph')
    def graph(id:str,role=Depends(identity)):
        d=load(id);nodes=[{'id':'contract','label':d['title'],'hash':d['contract_hash']}];edges=[]
        for c in d['contract']['clauses']:
            nodes.append({'id':'clause:'+c['id'],'label':c['text']});edges.append({'source':'contract','target':'clause:'+c['id'],'relation':'requires'})
            if d['evidence']:
                eid='evidence:'+c['id'];nodes.append({'id':eid,'label':c['metric'],'hash':d['evidence_hash']});edges.append({'source':'clause:'+c['id'],'target':eid,'relation':'supported by human-attested artifact' if d.get('evidence_attestation') else 'unattested submission'})
                if d['proposal']:
                    r=next(r for r in d['proposal']['rows'] if r['clause_id']==c['id']);fid='finding:'+c['id'];nodes.append({'id':fid,'label':r['verdict']+' / deduction $'+r['deduction']});edges.append({'source':eid,'target':fid,'relation':'evaluated under '+d['proposal']['policy']})
        return {'nodes':nodes,'edges':edges}
    @app.get('/api/milestones/{id}/replay')
    def replay(id:str,role=Depends(identity)):
        return replay_record(load(id))
    @app.get('/api/milestones/{id}/passport')
    def passport(id:str,role=Depends(identity)):
        d=load(id);payload={'schema':'covenantx-passport-v1','record':d,'audit':store.events(id),'integrity_scope':'SHA-256 detects changes relative to a retained trusted digest; not a signature or immutable ledger'}
        return {'payload':payload,'sha256':digest(payload)}
    async def apply_provider(d,result):
        caps=validate_order(d,result)
        if d['state']=='COMPLETED' and result.get('status')!='COMPLETED':
            raise ValueError('Completed transaction cannot regress to a capturable state')
        d['payment'].update(order_id=result['id'],provider_status=result.get('status'),last_reconciled_at=now(),approval_url=approval_link(result))
        if result.get('status')=='COMPLETED':d['state']='COMPLETED';d['payment']['capture_id']=caps[0]['id']
        elif result.get('status') in ('CREATED','APPROVED','PAYER_ACTION_REQUIRED'):
            # A pending capture must never become capture-eligible again.
            if caps or d['payment'].get('capture_submitted') or d['state'] in ('CAPTURE_UNKNOWN','CAPTURING','PROVIDER_REVIEW'):d['state']='CAPTURE_UNKNOWN'
            else:d['state']='ORDER_CREATED'
        else:d['state']='PROVIDER_REVIEW'
        return persist(d,'provider','payment.reconciled')
    @app.post('/api/milestones/{id}/order')
    async def order(id:str,body:Revision,role=Depends(client)):
        d=load(id,body.version)
        if d['state'] in ('ORDER_CREATED','COMPLETED'):return d
        if d['state']!='APPROVED':raise HTTPException(409,'Fresh settlement approval required; uncertain requests require reconciliation')
        if not os.getenv('PAYPAL_CLIENT_ID') or not os.getenv('PAYPAL_CLIENT_SECRET'):raise HTTPException(503,'PayPal Sandbox credentials missing')
        fresh(d)
        if (datetime.now(timezone.utc)-datetime.fromisoformat(d['settlement_approval']['at'])).total_seconds()>1800:raise HTTPException(409,'Approval expired; verify and approve again')
        d['payment']={'create_key':str(uuid.uuid4()),'capture_key':str(uuid.uuid4()),'snapshot_hash':d['settlement_approval']['hash'],'started_at':now()}
        d['payment']['operation_started_at']=now()
        d['state']='CREATING';d=persist(d,role,'payment.create_requested')
        try:return await apply_provider(d,await paypal.create(d))
        except Exception:
            d['state']='CREATE_UNKNOWN';persist(d,'system','payment.create_uncertain')
            raise HTTPException(502,'Order result uncertain. Use reconciliation; do not create another milestone to retry payment.')
    @app.post('/api/milestones/{id}/capture')
    async def capture(id:str,body:Revision,role=Depends(client)):
        d=load(id,body.version)
        if d['state']=='COMPLETED':return d
        if d['state']!='ORDER_CREATED':raise HTTPException(409,'No capture-eligible order; reconcile unknown outcomes')
        fresh(d)
        d['payment']['operation_started_at']=now()
        d['state']='CAPTURING';d=persist(d,role,'payment.capture_requested')
        try:
            remote=await paypal.get(d);validate_order(d,remote)
            if remote.get('status')=='COMPLETED':return await apply_provider(d,remote)
            if remote.get('status')!='APPROVED':
                d['state']='ORDER_CREATED';persist(d,'provider','payment.awaiting_payer')
                raise HTTPException(409,'Payer must approve this order on PayPal first')
            d['payment']['capture_submitted']=True
            d=persist(d,role,'payment.capture_sending')
            await paypal.capture(d)
            # Capture representations may omit purchase-unit metadata. Reconcile the
            # authoritative full order before validating snapshot and amount.
            return await apply_provider(d,await paypal.get(d))
        except HTTPException:raise
        except Exception:
            d['state']='CAPTURE_UNKNOWN';persist(d,'system','payment.capture_uncertain')
            raise HTTPException(502,'Capture result uncertain. Reconcile provider state before any further action.')
    @app.post('/api/milestones/{id}/reconcile')
    async def reconcile(id:str,body:Revision,role=Depends(client)):
        d=load(id,body.version)
        if not d['payment']:raise HTTPException(409,'No payment attempt exists')
        if d['state'] in ('CREATING','CAPTURING'):raise HTTPException(409,'Request in progress or process interrupted; operator must inspect before recovery')
        try:
            if d['payment'].get('order_id'):return await apply_provider(d,await paypal.get(d))
            if d['state']=='CREATE_UNKNOWN':
                age=(datetime.now(timezone.utc)-datetime.fromisoformat(d['payment']['started_at'])).total_seconds()
                if age>5*3600:raise HTTPException(409,'Automatic retry window expired; operator reconciliation required')
                d['payment']['operation_started_at']=now()
                d['state']='CREATING';d=persist(d,role,'payment.create_retry_same_key')
                try:return await apply_provider(d,await paypal.create(d))
                except Exception:
                    d['state']='CREATE_UNKNOWN';persist(d,'system','payment.create_retry_uncertain');raise
            raise HTTPException(409,'Manual provider reconciliation required')
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Provider reconciliation unavailable or response mismatch; status not confirmed')
    @app.post('/api/milestones/{id}/recover')
    async def recover(id:str,body:Recovery,role=Depends(client)):
        d=load(id,body.version)
        if d['state'] not in {'CREATING','CREATE_UNKNOWN','CAPTURING','CAPTURE_UNKNOWN','PROVIDER_REVIEW'} or not d['payment']:
            raise HTTPException(409,'Only an interrupted or uncertain payment can be recovered')
        timestamp=d['payment'].get('operation_started_at',d['payment']['started_at'])
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(timestamp)).total_seconds()
        if age<120:raise HTTPException(409,'Wait at least two minutes after the operation started before recovery')
        known=d['payment'].get('order_id')
        if known and known!=body.order_id:raise HTTPException(409,'Candidate order differs from the stored order')
        # GET only: the submitted ID is a lookup hint, never proof of payment.
        d['payment']['order_id']=body.order_id
        try:
            remote=await paypal.get(d)
            validate_order(d,remote)
        except Exception:raise HTTPException(502,'Candidate order could not be matched to this amount and approval snapshot')
        d.setdefault('recovery_events',[]).append({'actor':role,'at':now(),'note':body.note,'order_id':body.order_id,'previous_state':d['state'],'method':'GET only'})
        try:return await apply_provider(d,remote)
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Recovery could not persist a verified provider state')
    @app.post('/api/webhooks/paypal')
    async def webhook(request:Request):
        raw=await request.body()
        if len(raw)>150000:raise HTTPException(413,'Webhook too large')
        try:
            event=json.loads(raw)
            if not await paypal.verify_webhook(event,request.headers):raise HTTPException(400,'Signature verification failed')
            eid=event['id']
            if not isinstance(eid,str) or len(eid)>100:raise ValueError()
        except HTTPException:raise
        except Exception:raise HTTPException(400,'Webhook validation failed')
        # A verified event is a reconciliation signal only, never proof of payment.
        with Session(store.engine) as s:
            if s.get(Webhook,eid):return {'received':True,'duplicate':True}
        order_id=event.get('resource',{}).get('supplementary_data',{}).get('related_ids',{}).get('order_id')
        for d in store.list():
            if order_id and d.get('payment') and d['payment'].get('order_id')==order_id:
                if d['state'] in ('CREATING','CAPTURING'):raise HTTPException(503,'Payment operation in progress; retry event')
                try:await apply_provider(d,await paypal.get(d))
                except Exception:raise HTTPException(503,'Reconciliation failed; retry event')
        try:
            with Session(store.engine) as s,s.begin():s.add(Webhook(id=eid,received_at=now()))
        except IntegrityError:pass
        return {'received':True,'duplicate':False}
    return app
app=create_app()
