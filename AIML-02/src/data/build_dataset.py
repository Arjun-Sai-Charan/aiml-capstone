"""Build a patient-level RSNA subset or clearly marked synthetic demo."""
from pathlib import Path
import argparse, os, random
import numpy as np, pandas as pd
from PIL import Image

def dicom_image(path):
    try:
        import pydicom
    except ImportError as e: raise RuntimeError("Install requirements: python run.py setup") from e
    d=pydicom.dcmread(str(path)); a=d.pixel_array.astype(np.float32)
    if getattr(d, "PhotometricInterpretation", "") == "MONOCHROME1": a=a.max()-a
    a=a*float(getattr(d,"RescaleSlope",1))+float(getattr(d,"RescaleIntercept",0))
    center=getattr(d,"WindowCenter",None); width=getattr(d,"WindowWidth",None)
    if center is not None and width is not None:
        center=float(np.asarray(center).flat[0]); width=max(1,float(np.asarray(width).flat[0])); a=np.clip(a,center-width/2,center+width/2)
    else: a=np.clip(a,*np.percentile(a,[1,99]))
    a=(a-a.min())/max(float(a.max()-a.min()),1e-6)
    return np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((224,224),Image.Resampling.BILINEAR),dtype=np.uint8)

def build(out=None, demo=False, limit=3000, rsna=None):
    base=Path(rsna or os.getenv('RSNA_DIR',Path(__file__).resolve().parents[2]/'data/raw/rsna')); out=Path(out or Path(__file__).resolve().parents[2]/'data/processed'); out.mkdir(parents=True,exist_ok=True)
    labels=base/'stage_2_train_labels.csv'; details=base/'stage_2_detailed_class_info.csv'; imgs=base/'stage_2_train_images'
    if not (labels.is_file() and details.is_file() and imgs.is_dir()):
        if not demo: raise FileNotFoundError(f"RSNA dataset missing under {base}; set RSNA_DIR or run python run.py data --demo")
        rng=np.random.default_rng(2); n=min(limit,80); x=rng.integers(0,256,(n,224,224),dtype=np.uint8); y=np.tile([0,1],(n+1)//2)[:n].astype(np.uint8)
        ids=[f'demo-{i:04d}' for i in range(n)]; split=np.array(['train']*int(n*.7)+['val']*int(n*.15)+['test']*(n-int(n*.7)-int(n*.15)))
        np.savez_compressed(out/'dataset.npz',images=x,labels=y,split=split); pd.DataFrame({'patientId':ids,'label':y,'split':split,'demo':True}).to_csv(out/'manifest.csv',index=False); print('DEMO dataset:',n); return
    lab=pd.read_csv(labels).groupby('patientId',as_index=False).Target.max(); info=pd.read_csv(details).drop_duplicates('patientId')
    df=lab.merge(info,on='patientId',how='left'); df['label']=(df.Target>0).astype(int); df['kind']=df['class'].fillna('').astype(str)
    pos=df[df.label==1].sample(n=min(limit//2,int(df.label.sum())),random_state=42); neg=df[df.label==0].sample(n=min(limit-len(pos),int((df.label==0).sum())),random_state=42); df=pd.concat([pos,neg]).sample(frac=1,random_state=42).reset_index(drop=True)
    from sklearn.model_selection import train_test_split
    tr,rest=train_test_split(df,test_size=.30,random_state=42,stratify=df.label); va,te=train_test_split(rest,test_size=.5,random_state=42,stratify=rest.label); df['split']=''; df.loc[tr.index,'split']='train'; df.loc[va.index,'split']='val'; df.loc[te.index,'split']='test'
    xs=[]; ys=[]
    for _,row in df.iterrows():
        p=imgs/(str(row.patientId)+'.dcm')
        if p.is_file(): xs.append(dicom_image(p)); ys.append((row.patientId,int(row.label),row.split))
    if not xs: raise FileNotFoundError(f"No DICOMs found in {imgs}")
    meta=pd.DataFrame(ys,columns=['patientId','label','split']); np.savez_compressed(out/'dataset.npz',images=np.stack(xs),labels=meta.label.to_numpy(np.uint8),split=meta.split.to_numpy(dtype='U5')); meta.to_csv(out/'manifest.csv',index=False); print(meta.groupby(['split','label']).size().to_string())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--max-samples',type=int,default=3000);p.add_argument('--rsna');p.add_argument('--output');a=p.parse_args();build(a.output,a.demo,a.max_samples,a.rsna)
