"""Bound request bodies even when Content-Length is missing or false."""
from starlette.responses import JSONResponse

class BodyLimitMiddleware:
    def __init__(self,app,max_bytes=1000000):
        self.app=app
        self.max_bytes=max_bytes
    async def __call__(self,scope,receive,send):
        if scope['type']!='http':
            return await self.app(scope,receive,send)
        messages=[]
        size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            size+=len(message.get('body',b''))
            if size>self.max_bytes:
                return await JSONResponse({'detail':'Request body exceeds 1,000,000 bytes'},status_code=413)(scope,receive,send)
            messages.append(message)
            if not message.get('more_body',False):break
        index=0
        async def replay():
            nonlocal index
            if index<len(messages):
                result=messages[index];index+=1;return result
            return await receive()
        await self.app(scope,replay,send)
