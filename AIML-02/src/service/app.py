"""Local educational inference API with SQLite review audit."""
from pathlib import Path
from datetime import datetime,timezone
import io, os, uuid, threading, time, urllib.request, json, base64
import numpy as np
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import create_engine,Column,String,Float,DateTime,Text,ForeignKey
from sqlalchemy.orm import declarative_base,sessionmaker
from PIL import Image
BASE=Path(__file__).resolve().parents[2]; STORE=BASE/'data/local';STORE.mkdir(parents=True,exist_ok=True);engine=create_engine('sqlite:///'+str(STORE/'studies.db'),connect_args={'check_same_thread':False});Session=sessionmaker(bind=engine,expire_on_commit=False);Base=declarative_base()
class Study(Base):
 __tablename__='studies';id=Column(String,primary_key=True);filename=Column(String);image_path=Column(String);heatmap_path=Column(String);prediction=Column(String);confidence=Column(Float);status=Column(String,default='pending');model_version=Column(String,default='DEMO')
class Audit(Base):
 __tablename__='audit_log';id=Column(String,primary_key=True);study_id=Column(String);who=Column(String);what=Column(String);when=Column(DateTime);model_version=Column(String);confidence=Column(Float);comment=Column(Text)
Base.metadata.create_all(engine);app=FastAPI(title='AIML-02 education API',description='For education only, not clinical use.');app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
class Review(BaseModel): decision:str; reviewer:str; comment:str=''
def serialize(s):return {'id':s.id,'filename':s.filename,'prediction':s.prediction,'confidence':s.confidence,'status':s.status,'model_version':s.model_version}
def classify_image(a):
 model_file=BASE/'models'/'best.pt'
 if model_file.exists():
  import torch
  from torchvision.models import efficientnet_b0
  model=efficientnet_b0(weights=None);model.classifier[1]=torch.nn.Linear(model.classifier[1].in_features,2);ck=torch.load(model_file,map_location='cpu',weights_only=False);model.load_state_dict(ck['state_dict']);model.eval();tensor=torch.from_numpy(np.repeat(a[None,None],3,axis=1)).float(); tensor=(tensor-torch.tensor([.485,.456,.406])[None,:,None,None])/torch.tensor([.229,.224,.225])[None,:,None,None]
  with torch.no_grad(): probs=model(tensor).softmax(1)[0].numpy()
  pred='pneumonia' if int(probs.argmax())==1 else 'no pneumonia'; confidence=float(probs.max()); version='efficientnet-b0-trained'
  try:
   from pytorch_grad_cam import GradCAM
   from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
   with GradCAM(model=model,target_layers=[model.features[-1]]) as cam: heat=cam(input_tensor=tensor,targets=[ClassifierOutputTarget(int(probs.argmax()))])[0]
  except Exception: heat=a
  return pred,confidence,version,heat
 score=float(a.mean());return ('pneumonia' if score>.5 else 'no pneumonia'),float(abs(score-.5)*2),'DEMO',a

def create_study(data,name):
 sid=str(uuid.uuid4());p=STORE/(sid+Path(name).suffix);p.write_bytes(data); img=Image.open(io.BytesIO(data)).convert('L').resize((224,224));a=np.asarray(img,dtype=np.float32)/255;pred,confidence,version,heat=classify_image(a); heat=np.asarray(heat,dtype=np.float32);heat=(heat-heat.min())/max(float(heat.max()-heat.min()),1e-6); color=np.zeros((224,224,3),dtype=np.uint8);color[:,:,0]=np.uint8(heat*255);color[:,:,1]=np.uint8(np.clip(1-np.abs(heat-.5)*2,0,1)*80);hp=STORE/(sid+'-heatmap.png');Image.fromarray(color).save(hp); s=Study(id=sid,filename=name,image_path=str(p),heatmap_path=str(hp),prediction=pred,confidence=confidence,status='pending',model_version=version); db=Session();db.add(s);db.commit();db.close();return s
@app.get('/health')
def health():return {'ok':True,'model_mode':'trained' if (BASE/'models'/'best.pt').is_file() else 'DEMO','education_only':True}
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

# Optional Orthanc polling. Local upload remains fully independent of Orthanc.
def _poll_orthanc():
 url=os.getenv('ORTHANC_URL')
 if not url:return
 auth=''
 if os.getenv('ORTHANC_USERNAME'):
  token=base64.b64encode(f"{os.getenv('ORTHANC_USERNAME')}:{os.getenv('ORTHANC_PASSWORD','')}".encode()).decode();auth='Basic '+token
 def fetch(path):
  headers={'Authorization':auth} if auth else {};return urllib.request.urlopen(urllib.request.Request(url.rstrip('/')+path,headers=headers),timeout=10).read()
 seen=set()
 while True:
  try:
   for oid in json.loads(fetch('/instances')):
    if oid in seen:continue
    raw=fetch(f'/instances/{oid}/file')
    import pydicom
    ds=pydicom.dcmread(io.BytesIO(raw)); arr=ds.pixel_array.astype(np.float32)
    if getattr(ds,'PhotometricInterpretation','')=='MONOCHROME1':arr=arr.max()-arr
    arr=(arr-arr.min())/max(float(arr.max()-arr.min()),1e-6); buf=io.BytesIO();Image.fromarray(np.uint8(arr*255)).save(buf,format='PNG'); create_study(buf.getvalue(),f'orthanc-{oid}.png');seen.add(oid)
  except Exception as e: print(f'Orthanc polling unavailable: {e}')
  time.sleep(15)
@app.on_event('startup')
def start_orthanc_polling():
 if os.getenv('ORTHANC_URL'):threading.Thread(target=_poll_orthanc,daemon=True).start()
