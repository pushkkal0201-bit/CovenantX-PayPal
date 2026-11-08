"""Typed inputs and pure settlement policy. Models never compute or authorize money."""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

POLICY = 'covenantx-usd-v1'
def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()
def now():
    return datetime.now(timezone.utc).isoformat()
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class Clause(Strict):
    id: str = Field(pattern=r'^[A-Za-z0-9_-]{1,40}$')
    metric: Literal['coverage', 'p95_ms', 'critical_count', 'documentation']
    operator: Literal['gte', 'lte']
    threshold: Decimal = Field(ge=0, le=1000000)
    deduction: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    text: str = Field(min_length=5, max_length=2000)
class Contract(Strict):
    title: str = Field(min_length=3, max_length=150)
    source_text: str = Field(min_length=10, max_length=40000)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Literal['USD'] = 'USD'
    commit_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    clauses: list[Clause] = Field(min_length=1, max_length=20)
    @model_validator(mode='after')
    def unique_clauses(self):
        if len({c.id for c in self.clauses}) != len(self.clauses):
            raise ValueError('Clause IDs must be unique')
        if sum(c.deduction for c in self.clauses) > self.amount:
            raise ValueError('Combined deductions cannot exceed milestone value')
        return self
class Evidence(Strict):
    commit_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    artifact_id: str = Field(min_length=1, max_length=200)
    source_url: str = Field(min_length=1, max_length=500)
    observed_at: datetime
    content: str = Field(min_length=1, max_length=40000)
    metrics: dict[Literal['coverage','p95_ms','critical_count','documentation'], Decimal]
    demonstration: bool = False
    @model_validator(mode='after')
    def validate_metrics(self):
        if self.observed_at.tzinfo is None:
            raise ValueError('Evidence timestamp needs a timezone')
        for k,v in self.metrics.items():
            if not v.is_finite() or v < 0 or v > 1000000:
                raise ValueError('Invalid metric')
            if k == 'coverage' and v > 100: raise ValueError('Coverage exceeds 100')
            if k == 'documentation' and v not in (0,1): raise ValueError('Documentation must be 0 or 1')
            if k == 'critical_count' and v != v.to_integral_value(): raise ValueError('Count must be integral')
        return self
class Finding(Strict):
    clause_id: str
    verdict: Literal['pass','fail','unknown']
    evidence_quote: str = Field(max_length=2000)
    explanation: str = Field(min_length=1, max_length=2000)
class Assessment(Strict):
    findings: list[Finding] = Field(max_length=20)
    concern: str = Field(max_length=2000)
class Revision(Strict):
    version: int = Field(ge=1)
class Review(Revision):
    note: str = Field(min_length=5, max_length=2000)
class Verify(Revision):
    mode: Literal['gemini','fixture'] = 'gemini'
class Simulation(Strict):
    coverage: Decimal = Field(ge=0, le=100)
def trust(contract, evidence, at=None):
    at = at or datetime.now(timezone.utc)
    reasons = []
    age = (at - evidence.observed_at).total_seconds()
    if evidence.commit_sha != contract.commit_sha: reasons.append('Evidence commit differs from approved contract')
    if age < -300 or age > 7*86400: reasons.append('Evidence outside the seven-day freshness window')
    missing = sorted({c.metric for c in contract.clauses} - evidence.metrics.keys())
    if missing: reasons.append('Missing measurements: '+', '.join(missing))
    return reasons

def settlement(contract, evidence, assessment, at=None):
    findings = {f.clause_id:f for f in assessment.findings}
    reasons = trust(contract,evidence,at=at)
    if len(findings) != len(assessment.findings) or set(findings) != {c.id for c in contract.clauses}:
        reasons.append('AI must return each approved clause exactly once')
    if assessment.concern.strip(): reasons.append('Adversarial review: '+assessment.concern)
    rows=[]
    for clause in contract.clauses:
        f=findings.get(clause.id)
        val=evidence.metrics.get(clause.metric)
        expected='unknown' if val is None else ('pass' if (val>=clause.threshold if clause.operator=='gte' else val<=clause.threshold) else 'fail')
        if not f or f.verdict == 'unknown': reasons.append(f'{clause.id}: insufficient interpretation')
        elif f.verdict != expected: reasons.append(f'{clause.id}: AI contradicts supplied measurement')
        if f and (not f.evidence_quote.strip() or f.evidence_quote not in evidence.content):
            reasons.append(f'{clause.id}: missing exact evidence citation')
        deduction=clause.deduction if expected=='fail' else Decimal('0')
        rows.append({'clause_id':clause.id,'metric':clause.metric,'observed':str(val) if val is not None else None,'threshold':str(clause.threshold),'verdict':expected,'deduction':f'{deduction:.2f}','finding':f.model_dump() if f else None})
    amount=contract.amount-sum(Decimal(r['deduction']) for r in rows)
    if amount<=0: reasons.append('Zero-value settlement cannot create a PayPal order')
    return {'policy':POLICY,'currency':'USD','base':f'{contract.amount:.2f}','amount':f'{amount:.2f}','rows':rows,'holds':reasons,'eligible':not reasons}

class ContractEdit(Revision):
    contract: Contract
class Recovery(Review):
    order_id: str = Field(pattern=r'^[A-Za-z0-9_-]{5,64}$')
