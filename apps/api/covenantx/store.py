import json
from sqlalchemy import create_engine, Column, String, Integer, Text, select, update
from sqlalchemy.orm import DeclarativeBase, Session
from fastapi import HTTPException
from .domain import canonical, digest, now
class Base(DeclarativeBase): pass
class Record(Base):
    __tablename__='milestones'
    id=Column(String(36),primary_key=True)
    version=Column(Integer,nullable=False)
    data=Column(Text,nullable=False)
class Audit(Base):
    __tablename__='audit_events'
    id=Column(String(80),primary_key=True)
    milestone_id=Column(String(36),nullable=False,index=True)
    data=Column(Text,nullable=False)
class Webhook(Base):
    __tablename__='webhook_events'
    id=Column(String(100),primary_key=True)
    received_at=Column(String(40),nullable=False)
class Store:
    def __init__(self,url):
        self.engine=create_engine(url,connect_args={'check_same_thread':False,'timeout':15} if url.startswith('sqlite') else {},pool_pre_ping=True)
    def initialize(self): Base.metadata.create_all(self.engine)
    def get(self,id):
        with Session(self.engine) as s:
            r=s.get(Record,id)
            if not r: raise HTTPException(404,'Milestone not found')
            return json.loads(r.data)
    def list(self):
        with Session(self.engine) as s: return [json.loads(r.data) for r in s.scalars(select(Record).order_by(Record.id))]
    def save(self,d,expected,actor,event):
        d=dict(d); d['version']=expected+1
        audit={'at':now(),'actor':actor,'event':event,'version':d['version'],'record_hash':digest(d)}
        with Session(self.engine) as s,s.begin():
            if expected==0:
                s.add(Record(id=d['id'],version=1,data=canonical(d)))
            else:
                result=s.execute(update(Record).where(Record.id==d['id'],Record.version==expected).values(version=d['version'],data=canonical(d)))
                if result.rowcount != 1: raise HTTPException(409,'Revision changed; refresh before acting')
            s.add(Audit(id=f"{d['id']}:{d['version']}",milestone_id=d['id'],data=canonical(audit)))
        return d
    def events(self,id):
        with Session(self.engine) as s:
            return sorted([json.loads(r.data) for r in s.scalars(select(Audit).where(Audit.milestone_id==id))],key=lambda x:x['version'])
