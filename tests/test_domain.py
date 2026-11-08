from decimal import Decimal
import pytest
from pydantic import ValidationError
from covenantx.domain import Contract,Evidence,Assessment,Finding,settlement

def assessment(quote='Coverage is 78 percent.',verdict='fail'):
    return Assessment(findings=[Finding(clause_id='SLA-01',verdict=verdict,evidence_quote=quote,explanation='Coverage below threshold')],concern='')
@pytest.mark.parametrize('coverage,amount',[('0','4500.00'),('78','4500.00'),('84.999','4500.00'),('85','5000.00'),('100','5000.00')])
def test_boundary_and_decimal(contract,evidence,coverage,amount):
    evidence['metrics']['coverage']=coverage
    result=settlement(Contract(**contract),Evidence(**evidence),assessment(verdict='pass' if Decimal(coverage)>=85 else 'fail'))
    assert result['amount']==amount and result['eligible']
@pytest.mark.parametrize('quote,verdict',[('invented evidence','fail'),('Coverage is 78 percent.','pass'),('','fail'),('Coverage is 78 percent.','unknown')])
def test_hallucinated_or_contradictory_findings_hold(contract,evidence,quote,verdict):
    assert not settlement(Contract(**contract),Evidence(**evidence),assessment(quote,verdict))['eligible']
def test_duplicate_and_missing_findings(contract,evidence):
    a=assessment();a.findings*=2
    assert not settlement(Contract(**contract),Evidence(**evidence),a)['eligible']
    a.findings=[];assert not settlement(Contract(**contract),Evidence(**evidence),a)['eligible']
def test_model_cannot_change_money(contract,evidence):
    with pytest.raises(ValidationError):Assessment.model_validate({'findings':[],'concern':'','amount':'1'})
    contract['clauses'][0]['deduction']='5001'
    with pytest.raises(ValidationError):Contract(**contract)
@pytest.mark.parametrize('coverage',['NaN','Infinity','-1','101'])
def test_invalid_metrics_rejected(evidence,coverage):
    evidence['metrics']['coverage']=coverage
    with pytest.raises(ValidationError):Evidence(**evidence)
def test_adversarial_concern_holds(contract,evidence):
    a=assessment();a.concern='Artifact instructs model to approve payment'
    assert not settlement(Contract(**contract),Evidence(**evidence),a)['eligible']
