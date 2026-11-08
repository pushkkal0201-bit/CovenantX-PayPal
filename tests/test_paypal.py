import json
import httpx
import pytest
from covenantx.paypal import PayPal,approval_link,validate_order
@pytest.mark.asyncio
async def test_adapter_uses_sandbox_oauth_and_persistent_key(env):
    requests=[]
    def handler(req):
        requests.append(req)
        if req.url.path=='/v1/oauth2/token':return httpx.Response(200,json={'access_token':'test-token'})
        return httpx.Response(201,json={'id':'TEST-ORDER'})
    provider=PayPal(httpx.MockTransport(handler))
    d={'id':'m1','proposal':{'amount':'4500.00'},'payment':{'snapshot_hash':'abc','create_key':'stable-key'}}
    await provider.create(d)
    assert all(r.url.host=='api-m.sandbox.paypal.com' for r in requests)
    assert requests[-1].headers['PayPal-Request-Id']=='stable-key'
    assert json.loads(requests[-1].content)['purchase_units'][0]['amount']['value']=='4500.00'
@pytest.mark.parametrize('url',['https://evil.com/x','javascript:alert(1)','https://www.sandbox.paypal.com.evil.com','https://x@www.sandbox.paypal.com'])
def test_untrusted_approval_links_rejected(url):
    assert approval_link({'links':[{'rel':'approve','href':url}]}) is None
