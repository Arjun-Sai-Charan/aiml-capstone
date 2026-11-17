"""Local educational inference API with SQLite review audit."""
from pathlib import Path
from datetime import datetime,timezone
import io, os, uuid
import numpy as np
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import create_engine,Column,String,Float,DateTime,Text,ForeignKey
from sqlalchemy.orm import declarative_base,sessionmaker
from PIL import Image
BASE=Path(__file__).resolve().parents[2]; STORE=BASE/'data/local';STORE.mkdir(parents=True,exist_ok=True);engine=create_engine('sqlite:///'+str(STORE/'studies.db'),connect_args={'check_same_thread':False});Session=sessionmaker(bind=engine);Base=declarative_base()
class Study(Base):
 __tablename__='studies';id=Column(String,primary_key=True);filename=Column(String);image_path=Column(String);heatmap_path=Column(String);prediction=Column(String);confidence=Column(Float);status=Column(String,default='pending');model_version=Column(String,default='DEMO')
class Audit(Base):
 __tablename__='audit_log';id=Column(String,primary_key=True);study_id=Column(String);who=Column(String);what=Column(String);when=Column(DateTime);model_version=Column(String);confidence=Column(Float);comment=Column(Text)
Base.metadata.create_all(engine);app=FastAPI(title='AIML-02 education API',description='For education only, not clinical use.');app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
class Review(BaseModel): decision:str; reviewer:str; comment:str=''
def serialize(s):return {'id':s.id,'filename':s.filename,'prediction':s.prediction,'confidence':s.confidence,'status':s.status,'model_version':s.model_version}
def create_study(data,name):
 sid=str(uuid.uuid4());p=STORE/(sid+Path(name).suffix);p.write_bytes(data); img=Image.open(io.BytesIO(data)).convert('L').resize((224,224));a=np.asarray(img,dtype=np.float32)/255; score=float(a.mean()); pred='pneumonia' if score>.5 else 'no pneumonia';hm=Image.fromarray(np.uint8(np.clip(a*255,0,255))).convert('RGB');hp=STORE/(sid+'-heatmap.png');hm.save(hp); s=Study(id=sid,filename=name,image_path=str(p),heatmap_path=str(hp),prediction=pred,confidence=abs(score-.5)*2,status='pending',model_version='DEMO'); db=Session();db.add(s);db.commit();db.close();return s
@app.get('/health')
def health():return {'ok':True,'model_mode':'DEMO','education_only':True}
@app.get('/studies')
def studies():
 d=Session();r=[serialize(s) for s in d.query(Study).all()];d.close();return r
@app.get('/studies/{sid}')
def study(sid):
 d=Session();s=d.get(Study,sid);d.close();
 if not s:raise HTTPException(404,'Study not found')
 return serialize(s)
def file_response(sid,attr):
 d=Session();s=d.get(Study,sid);d.close();
 if not s:raise HTTPException(404,'Study not found')
 p=Path(getattr(s,attr));return Response(p.read_bytes(),media_type='image/png' if p.suffix=='.png' else 'image/jpeg')
@app.get('/studies/{sid}/image')
def image(sid):return file_response(sid,'image_path')
@app.get('/studies/{sid}/heatmap')
def heatmap(sid):return file_response(sid,'heatmap_path')
@app.post('/studies/{sid}/review')
def review(sid,r:Review):
 if r.decision not in ('approve','reject'):raise HTTPException(400,'decision must be approve or reject')
 d=Session();s=d.get(Study,sid)
 if not s:d.close();raise HTTPException(404,'Study not found')
 s.status='approved' if r.decision=='approve' else 'rejected';d.add(Audit(id=str(uuid.uuid4()),study_id=sid,who=r.reviewer,what=r.decision,when=datetime.now(timezone.utc),model_version=s.model_version,confidence=s.confidence,comment=r.comment));d.commit();res=serialize(s);d.close();return res
@app.get('/audit-log')
def audit():
 d=Session();rows=d.query(Audit).order_by(Audit.when.desc()).all();ans=[{'id':x.id,'study_id':x.study_id,'who':x.who,'what':x.what,'when':x.when.isoformat(),'model_version':x.model_version,'confidence':x.confidence,'comment':x.comment} for x in rows];d.close();return ans
@app.post('/upload')
async def upload(file:UploadFile=File(...)):
 data=await file.read()
 if not data:raise HTTPException(400,'Empty upload')
 try:Image.open(io.BytesIO(data)).verify()
 except Exception:raise HTTPException(400,'Upload must be a readable image (PNG/JPEG)')
 return serialize(create_study(data,file.filename or 'upload.png'))
