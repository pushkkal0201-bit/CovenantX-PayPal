"""Parse uploaded reports, never execute them or assume their source is authentic."""
import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal
from pydantic import Field, model_validator
from .domain import Strict, Evidence

PARSER_VERSION = 'covenantx-artifacts-v1'
class Artifact(Strict):
    name: str = Field(min_length=1, max_length=150, pattern=r'^[^/\\\x00]+$')
    format: Literal['coverage-py-json', 'k6-summary-json', 'sarif-2.1-json', 'documentation-text']
    content: str = Field(min_length=1, max_length=180000)
class Bundle(Strict):
    commit_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    artifact_id: str = Field(min_length=1, max_length=200)
    source_url: str = Field(min_length=1, max_length=500)
    observed_at: datetime
    demonstration: bool = False
    artifacts: list[Artifact] = Field(min_length=1, max_length=8)
    @model_validator(mode='after')
    def bound(self):
        if self.observed_at.tzinfo is None:
            raise ValueError('Timestamp needs a timezone')
        if len({a.name for a in self.artifacts}) != len(self.artifacts):
            raise ValueError('Artifact names must be unique')
        if sum(len(a.content.encode('utf-8')) for a in self.artifacts) > 400000:
            raise ValueError('Combined artifact content exceeds 400,000 bytes')
        return self

def strict_json(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate JSON key: ' + k[:80])
            result[k] = v
        return result
    def bad_constant(value):
        raise ValueError('Nonfinite JSON numbers are not accepted')
    try:
        data = json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('Invalid or excessively nested JSON report') from exc
    if not isinstance(data, dict):
        raise ValueError('Report must be a JSON object')
    return data

def number(value, label, maximum=1000000):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(label + ' must be numeric')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(label + ' must be numeric') from exc
    if not result.is_finite() or result < 0 or result > maximum:
        raise ValueError(label + ' outside supported range')
    return result

def count(value, label):
    result = number(value, label, 100000000)
    if result != result.to_integral_value():
        raise ValueError(label + ' must be an integer')
    return int(result)

def coverage(data):
    totals = data['totals']
    files = data['files']
    if not isinstance(files, dict) or not files or len(files)>10000:
        raise ValueError('Coverage report needs a nonempty file map (maximum 10,000 files)')
    statements = covered = 0
    for filename, file in files.items():
        summary = file['summary']
        n = count(summary['num_statements'], 'num_statements')
        c = count(summary['covered_lines'], 'covered_lines')
        missing = count(summary['missing_lines'], 'missing_lines')
        if c + missing != n:
            raise ValueError('Coverage counts disagree for ' + filename[:100])
        statements += n
        covered += c
    if statements == 0:
        raise ValueError('Cannot calculate coverage for zero statements')
    if count(totals['num_statements'], 'totals.num_statements') != statements or count(totals['covered_lines'], 'totals.covered_lines') != covered or count(totals['missing_lines'], 'totals.missing_lines') != statements-covered:
        raise ValueError('Coverage totals disagree with file summaries')
    # Use statement coverage; combined branch+statement percent_covered is not interchangeable.
    value = Decimal(covered)*100/Decimal(statements)
    stated=totals.get('percent_statements_covered')
    if stated is None and data.get('meta',{}).get('branch_coverage') is False:
        stated=totals.get('percent_covered')
    if stated is not None and abs(number(stated,'stated coverage',100)-value)>Decimal('0.01'):
        raise ValueError('Stated statement coverage contradicts uploaded counts')
    return {'coverage':value}, {'basis':'statement coverage; uploaded counts', 'covered':covered, 'statements':statements}

def k6(data):
    metric = data['metrics']['http_req_duration']
    if metric.get('type') != 'trend' or metric.get('contains') != 'time':
        raise ValueError('Expected a k6 time trend for http_req_duration')
    values = metric['values']
    p95 = number(values['p(95)'], 'p95_ms')
    low, high = number(values['min'], 'min'), number(values['max'], 'max')
    if not low <= p95 <= high:
        raise ValueError('P95 lies outside observed min/max')
    requests = count(data['metrics']['http_reqs']['values']['count'], 'request count')
    if requests == 0:
        raise ValueError('A latency report needs at least one request')
    return {'p95_ms':p95}, {'basis':'uploaded k6 aggregate, milliseconds; percentile not recalculated from samples', 'requests':requests}

def sarif(data):
    if data.get('version') != '2.1.0':
        raise ValueError('Only the supported SARIF 2.1.0 subset is accepted')
    runs = data['runs']
    if not isinstance(runs,list) or not runs or len(runs)>20:
        raise ValueError('SARIF requires 1–20 runs')
    critical = results_seen = 0
    for run in runs:
        if run.get('externalPropertyFileReferences'):
            raise ValueError('External SARIF properties are not supported')
        invocations = run.get('invocations')
        if not isinstance(invocations,list) or not invocations or any(x.get('executionSuccessful') is not True for x in invocations):
            raise ValueError('Every SARIF invocation must report successful execution')
        driver = run['tool']['driver']
        if not isinstance(driver.get('name'),str) or not driver['name'].strip():
            raise ValueError('SARIF tool name is required')
        rules = driver.get('rules', [])
        if not any('security-severity' in r.get('properties',{}) for r in rules):
            raise ValueError('SARIF needs declared security rules, even for an empty result set')
        for rule in rules:
            if 'security-severity' in rule.get('properties',{}):
                number(rule['properties']['security-severity'],'security-severity',10)
        for invocation in invocations:
            if invocation.get('exitCode',0)!=0 or any(n.get('level')=='error' for n in invocation.get('toolExecutionNotifications',[])):
                raise ValueError('SARIF invocation reports an error despite successful flag')
        ids = [r['id'] for r in rules]
        if len(set(ids))!=len(ids):
            raise ValueError('Duplicate SARIF rule IDs')
        by_id = dict(zip(ids, rules))
        results = run['results']
        if not isinstance(results,list) or len(results)>10000:
            raise ValueError('Invalid SARIF result list')
        for result in results:
            if result.get('suppressions') or result.get('baselineState')=='absent':
                raise ValueError('Suppressed or baseline-absent findings require manual interpretation')
            if result.get('kind','fail') != 'fail':
                raise ValueError('Non-failure SARIF result kinds need manual interpretation')
            rid = result.get('ruleId')
            if 'ruleIndex' in result:
                index = count(result['ruleIndex'],'ruleIndex')
                if index>=len(rules) or (rid is not None and rules[index]['id']!=rid):
                    raise ValueError('SARIF rule index/ID mismatch')
                rid = rules[index]['id']
            if rid not in by_id:
                raise ValueError('SARIF result references unknown rule')
            score = number(by_id[rid]['properties']['security-severity'], 'security-severity',10)
            critical += int(score >= Decimal('9.0'))
            results_seen += 1
    return {'critical_count':Decimal(critical)}, {'basis':'policy: active unsuppressed rule security-severity >= 9.0; ambiguous suppression/resolution rejected', 'results_examined':results_seen}

def parse_bundle(bundle: Bundle):
    metrics, receipts, lines = {}, [], []
    for artifact in bundle.artifacts:
        sha = hashlib.sha256(artifact.content.encode('utf-8')).hexdigest()
        try:
            if artifact.format == 'documentation-text':
                if not artifact.content.strip():
                    raise ValueError('Documentation is empty')
                derived, details = {'documentation':Decimal(1)}, {'basis':'nonempty document presence only; completeness still requires review'}
            else:
                data = strict_json(artifact.content)
                derived, details = {'coverage-py-json':coverage,'k6-summary-json':k6,'sarif-2.1-json':sarif}[artifact.format](data)
        except (KeyError, TypeError, IndexError, AttributeError) as exc:
            raise ValueError(f'{artifact.name}: unsupported or incomplete report schema') from exc
        duplicate = metrics.keys() & derived.keys()
        if duplicate:
            raise ValueError('Multiple artifacts supply the same metric: '+', '.join(sorted(duplicate)))
        metrics.update(derived)
        receipts.append({'name':artifact.name,'format':artifact.format,'sha256':sha,'bytes':len(artifact.content.encode('utf-8')),'derived_metrics':{k:str(v) for k,v in derived.items()},'details':details})
        lines.append(f'Artifact {artifact.name}; SHA-256 {sha}. '+ '; '.join(f'{k}={v}' for k,v in derived.items())+'. '+details['basis'])
        if artifact.format=='documentation-text':
            lines.append('Document excerpt (untrusted data, at most 12,000 characters):\n'+artifact.content[:12000])
    evidence = Evidence(commit_sha=bundle.commit_sha,artifact_id=bundle.artifact_id,source_url=bundle.source_url,observed_at=bundle.observed_at,content='\n'.join(lines),metrics=metrics,demonstration=bundle.demonstration)
    return evidence, {'parser':PARSER_VERSION,'source_authenticity':'unverified upload; human inspection required','artifacts':receipts}
