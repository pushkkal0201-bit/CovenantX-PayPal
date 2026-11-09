from conftest import headers, post


def test_audit_summaries_and_rejected_write(harness, contract):
    c, _, _ = harness
    d = c.post('/api/milestones', headers=headers(), json=contract).json()
    approved = post(c, d, 'approve-contract').json()
    assert post(c, d, 'approve-contract').status_code == 409
    url = f"/api/milestones/{d['id']}/passport"
    assert c.get(url).status_code == 401
    audit = c.get(url, headers=headers('vendor')).json()['payload']['audit']
    assert len(audit) == 2
    assert audit[0]['state_before'] is None
    assert audit[0]['state_after'] == 'DRAFT'
    assert audit[1]['state_before'] == 'DRAFT'
    assert audit[1]['state_after'] == 'AWAITING_EVIDENCE'
    assert audit[1]['changed_fields'] == ['approvals', 'state']
    assert audit[1]['version'] == approved['version']
    assert audit[1]['actor'] == 'client'
    assert 'source_text' not in str(audit)
