import copy
import json
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError
from covenantx.artifacts import Bundle,parse_bundle,strict_json

@pytest.fixture
def reports():
    summary={'num_statements':100,'covered_lines':78,'missing_lines':22,'percent_covered':99}
    return {'coverage-py-json':{'meta':{'version':'7.12.0'},'totals':summary,'files':{'app.py':{'summary':summary}}},
    'k6-summary-json':{'metrics':{'http_req_duration':{'type':'trend','contains':'time','values':{'min':100,'max':250,'p(95)':180}},'http_reqs':{'values':{'count':1000}}}},
    'sarif-2.1-json':{'version':'2.1.0','runs':[{'tool':{'driver':{'name':'test-scanner','rules':[{'id':'security-rule','properties':{'security-severity':'9.0'}}]}},'invocations':[{'executionSuccessful':True}],'results':[]}]}}

def bundle_for(reports):
    return Bundle(commit_sha='a'*40,artifact_id='test-bundle',source_url='fixture://tests',observed_at=datetime.now(timezone.utc),demonstration=True,artifacts=[{'name':fmt+'.json','format':fmt,'content':json.dumps(report)} for fmt,report in reports.items()]+[{'name':'delivery.md','format':'documentation-text','content':'Delivery documentation for the fixture.'}])

def test_all_formats_and_correct_statement_ratio(reports):
    b=bundle_for(reports);e,r=parse_bundle(b)
    assert e.metrics=={'coverage':Decimal(78),'p95_ms':Decimal(180),'critical_count':0,'documentation':1}
    assert 'coverage=78' in e.content
    assert len(r['artifacts'])==4
    assert r['source_authenticity'].startswith('unverified')
    # Deliberately wrong percent_covered is not used: branch+line and statement coverage differ.
    assert e.metrics['coverage']!=99

@pytest.mark.parametrize('value',['{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}','[]','{"x":'])
def test_ambiguous_json_rejected(value):
    with pytest.raises(ValueError):strict_json(value)

@pytest.mark.parametrize('field,value',[('covered_lines',101),('num_statements',0),('missing_lines',-1),('covered_lines',True)])
def test_bad_coverage_rejected(reports,field,value):
    reports['coverage-py-json']['totals']=dict(reports['coverage-py-json']['totals'])
    reports['coverage-py-json']['totals'][field]=value
    with pytest.raises(ValueError):parse_bundle(bundle_for(reports))

def test_duplicate_metric_rejected(reports):
    b=bundle_for(reports);a=b.artifacts[0].model_copy(update={'name':'other-coverage.json'});b.artifacts.append(a)
    with pytest.raises(ValueError,match='same metric'):parse_bundle(b)

@pytest.mark.parametrize('kind',['zero','outside','not-time','missing'])
def test_bad_k6_rejected(reports,kind):
    metrics=reports['k6-summary-json']['metrics']
    if kind=='zero':metrics['http_reqs']['values']['count']=0
    if kind=='outside':metrics['http_req_duration']['values']['p(95)']=251
    if kind=='not-time':metrics['http_req_duration']['contains']='default'
    if kind=='missing':del metrics['http_req_duration']['values']['p(95)']
    with pytest.raises(ValueError):parse_bundle(bundle_for(reports))

@pytest.mark.parametrize('score,expected',[('8.9',0),('9.0',1),('10',1)])
def test_sarif_policy_boundary(reports,score,expected):
    run=reports['sarif-2.1-json']['runs'][0]
    run['tool']['driver']['rules'][0]['properties']['security-severity']=score
    run['results']=[{'ruleId':'security-rule'}]
    e,_=parse_bundle(bundle_for(reports));assert e.metrics['critical_count']==expected

@pytest.mark.parametrize('kind',['failed','no-execution','no-rules','unknown-rule','bad-index','unknown-score','external','new-version'])
def test_unsupported_sarif_does_not_silently_pass(reports,kind):
    report=reports['sarif-2.1-json'];run=report['runs'][0]
    if kind=='failed':run['invocations'][0]['executionSuccessful']=False
    if kind=='no-execution':del run['invocations']
    if kind=='no-rules':run['tool']['driver']['rules']=[]
    if kind=='unknown-rule':run['results']=[{'ruleId':'unknown'}]
    if kind=='bad-index':run['results']=[{'ruleId':'security-rule','ruleIndex':3}]
    if kind=='unknown-score':run['tool']['driver']['rules'][0]['properties']['security-severity']='unknown';run['results']=[{'ruleId':'security-rule'}]
    if kind=='external':run['externalPropertyFileReferences']={'results':[]}
    if kind=='new-version':report['version']='2.2.0'
    with pytest.raises(ValueError):parse_bundle(bundle_for(reports))

def test_filename_traversal_and_duplicate_names(reports):
    data=bundle_for(reports).model_dump(mode='json');data['artifacts'][0]['name']='../../etc/passwd'
    with pytest.raises(ValidationError):Bundle.model_validate(data)
    data=bundle_for(reports).model_dump(mode='json');data['artifacts'][1]['name']=data['artifacts'][0]['name']
    with pytest.raises(ValidationError):Bundle.model_validate(data)

def test_zero_statement_report_rejected(reports):
    summary={'num_statements':0,'covered_lines':0,'missing_lines':0}
    reports['coverage-py-json']['totals']=summary;reports['coverage-py-json']['files']={'empty.py':{'summary':summary}}
    with pytest.raises(ValueError):parse_bundle(bundle_for(reports))


def test_explicit_statement_percentage_conflict(reports):
    reports['coverage-py-json']['meta']['branch_coverage']=False
    with pytest.raises(ValueError,match='contradicts'):parse_bundle(bundle_for(reports))

@pytest.mark.parametrize('change',[{'suppressions':[{'kind':'inSource'}]},{'baselineState':'absent'}])
def test_sarif_ambiguous_resolution_rejected(reports,change):
    reports['sarif-2.1-json']['runs'][0]['results']=[{'ruleId':'security-rule',**change}]
    with pytest.raises(ValueError,match='manual interpretation'):parse_bundle(bundle_for(reports))

def test_sarif_contradictory_execution_rejected(reports):
    reports['sarif-2.1-json']['runs'][0]['invocations'][0]['exitCode']=1
    with pytest.raises(ValueError,match='error'):parse_bundle(bundle_for(reports))
