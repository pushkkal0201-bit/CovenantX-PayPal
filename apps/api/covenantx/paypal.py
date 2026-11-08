"""Sandbox-only HTTP adapter. No production URL override or simulated success."""
import os
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import httpx
BASE='https://api-m.sandbox.paypal.com'
class PayPal:
    def __init__(self,transport=None): self.transport=transport
    async def request(self,method,path,payload=None,key=None):
        cid,secret=os.getenv('PAYPAL_CLIENT_ID'),os.getenv('PAYPAL_CLIENT_SECRET')
        if not cid or not secret: raise RuntimeError('PayPal Sandbox credentials are not configured')
        async with httpx.AsyncClient(base_url=BASE,timeout=25,transport=self.transport,follow_redirects=False) as client:
            token=await client.post('/v1/oauth2/token',auth=(cid,secret),data={'grant_type':'client_credentials'})
            token.raise_for_status()
            headers={'Authorization':'Bearer '+token.json()['access_token'],'Content-Type':'application/json'}
            if key: headers.update({'PayPal-Request-Id':key,'Prefer':'return=representation'})
            response=await client.request(method,path,headers=headers,json=payload)
            response.raise_for_status()
            return response.json()
    async def create(self,d):
        return_url=os.getenv('PUBLIC_WEB_URL','http://localhost:3000').rstrip('/')
        return await self.request('POST','/v2/checkout/orders',{'intent':'CAPTURE','purchase_units':[{'reference_id':d['id'],'custom_id':d['payment']['snapshot_hash'],'amount':{'currency_code':'USD','value':d['proposal']['amount']}}],'payment_source':{'paypal':{'experience_context':{'user_action':'PAY_NOW','return_url':return_url+'/?payment=approved','cancel_url':return_url+'/?payment=cancelled'}}}},d['payment']['create_key'])
    async def capture(self,d):
        return await self.request('POST','/v2/checkout/orders/'+d['payment']['order_id']+'/capture',{},d['payment']['capture_key'])
    async def get(self,d): return await self.request('GET','/v2/checkout/orders/'+d['payment']['order_id'])
    async def verify_webhook(self,event,headers):
        wid=os.getenv('PAYPAL_WEBHOOK_ID')
        if not wid: raise RuntimeError('Webhook ID is not configured')
        keys={'auth_algo':'paypal-auth-algo','cert_url':'paypal-cert-url','transmission_id':'paypal-transmission-id','transmission_sig':'paypal-transmission-sig','transmission_time':'paypal-transmission-time'}
        data={k:headers[v] for k,v in keys.items()}
        data.update(webhook_id=wid,webhook_event=event)
        result=await self.request('POST','/v1/notifications/verify-webhook-signature',data)
        return result.get('verification_status')=='SUCCESS'

def validate_order(d,result):
    units=result.get('purchase_units',[])
    if not isinstance(result.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{5,64}',result['id']) or len(units)!=1: raise ValueError('Unexpected order identity or purchase units')
    if d['payment'].get('order_id') and result['id']!=d['payment']['order_id']: raise ValueError('Order ID mismatch')
    unit=units[0]
    if unit.get('reference_id')!=d['id'] or unit.get('custom_id')!=d['payment']['snapshot_hash']: raise ValueError('Order does not match approved snapshot')
    amount=unit.get('amount',{})
    if amount.get('currency_code')!='USD' or Decimal(amount.get('value','-1'))!=Decimal(d['proposal']['amount']): raise ValueError('Provider amount mismatch')
    captures=unit.get('payments',{}).get('captures',[])
    if result.get('status')=='COMPLETED':
        if len(captures)!=1: raise ValueError('Expected exactly one completed capture')
        cap=captures[0]; money=cap.get('amount',{})
        if not cap.get('id') or cap.get('status')!='COMPLETED' or money.get('currency_code')!='USD' or Decimal(money.get('value','-1'))!=Decimal(d['proposal']['amount']):
            raise ValueError('Capture mismatch or incomplete capture')
    return captures

def approval_link(result):
    for link in result.get('links',[]):
        if link.get('rel') in ('approve','payer-action'):
            url=urlparse(link.get('href',''))
            if url.scheme=='https' and url.hostname in ('www.sandbox.paypal.com','sandbox.paypal.com') and not url.username:
                return link['href']
    return None
