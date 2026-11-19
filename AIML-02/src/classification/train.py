"""EfficientNet-B0 transfer learning on processed NPZ."""
import argparse,json,random
from pathlib import Path
import numpy as np, torch
from torch import nn
from torch.utils.data import Dataset,DataLoader

class Chest(Dataset):
 def __init__(self,x,y,augment=False): self.x=x; self.y=y; self.augment=augment
 def __len__(self): return len(self.y)
 def __getitem__(self,i):
  from PIL import Image,ImageEnhance
  im=Image.fromarray(self.x[i]);
  if self.augment:
   import random
   if random.random()<.5: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   im=im.rotate(random.uniform(-7,7)); im=ImageEnhance.Brightness(im).enhance(random.uniform(.9,1.1)); im=ImageEnhance.Contrast(im).enhance(random.uniform(.9,1.1))
  a=np.asarray(im,dtype=np.float32)[None]/255
  tensor=torch.from_numpy(a).repeat(3,1,1); mean=torch.tensor([.485,.456,.406])[:,None,None]; std=torch.tensor([.229,.224,.225])[:,None,None]
  return (tensor-mean)/std,torch.tensor(self.y[i],dtype=torch.long)
def main():
 p=argparse.ArgumentParser();p.add_argument('--epochs',type=int,default=3);p.add_argument('--max-samples',type=int);p.add_argument('--data',default='AIML-02/data/processed/dataset.npz');p.add_argument('--output',default='AIML-02/models');a=p.parse_args(); z=np.load(a.data); x=z['images']; y=z['labels']; s=z['split'].astype(str);
 if a.max_samples: x=x[:a.max_samples];y=y[:a.max_samples];s=s[:a.max_samples]
 device='cuda' if torch.cuda.is_available() else 'cpu'
 try:
  from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
  try: model=efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT); init='ImageNet'
  except Exception as e: print('ImageNet unavailable, using random init:',e); model=efficientnet_b0(weights=None); init='random'
  model.classifier[1]=nn.Linear(model.classifier[1].in_features,2)
 except Exception as e: raise RuntimeError('Torchvision EfficientNet unavailable; install pinned requirements') from e
 model.to(device); train=np.where(s=='train')[0]; val=np.where(s=='val')[0]; test=np.where(s=='test')[0]
 dl=lambda ix,aug=False:DataLoader(Chest(x[ix],y[ix],aug),batch_size=16,shuffle=aug)
 opt=torch.optim.AdamW(model.parameters(),lr=1e-4); lossfn=nn.CrossEntropyLoss(); scaler=torch.amp.GradScaler('cuda',enabled=device=='cuda')
 best=1e9; out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for epoch in range(a.epochs):
  model.train();
  for bx,by in dl(train,True):
   opt.zero_grad()
   with torch.autocast(device_type='cuda',enabled=device=='cuda'): loss=lossfn(model(bx.to(device)),by.to(device))
   scaler.scale(loss).backward();scaler.step(opt);scaler.update()
  model.eval(); losses=[]
  with torch.no_grad():
   for bx,by in dl(val): losses.append(lossfn(model(bx.to(device)),by.to(device)).item())
  v=float(np.mean(losses)) if losses else 0;print(f'epoch {epoch+1}: val_loss={v:.4f}')
  if v<best: best=v;checkpoint={'state_dict':model.state_dict(),'init':init,'model_version':'efficientnet-b0-' + init.lower()}; torch.save(checkpoint,out/'classifier.pt'); torch.save(checkpoint,out/'best.pt')
 # held-out test evaluated once after selecting best epoch
 from sklearn.metrics import accuracy_score,roc_auc_score,precision_recall_fscore_support,confusion_matrix,roc_curve
 ck=torch.load(out/'classifier.pt',map_location=device,weights_only=False);model.load_state_dict(ck['state_dict']);model.eval(); ys=[];ps=[]
 with torch.no_grad():
  for bx,by in dl(test): ys.extend(by.tolist());ps.extend(model(bx.to(device)).softmax(1)[:,1].cpu().tolist())
 pred=np.asarray(ps)>=.5; precision,recall,f1,_=precision_recall_fscore_support(ys,pred,average='binary',zero_division=0) if ys else (0,0,0,0); metrics={'accuracy':float(accuracy_score(ys,pred)) if ys else None,'auc':float(roc_auc_score(ys,ps)) if len(set(ys))>1 else None,'precision':float(precision),'recall':float(recall),'f1':float(f1),'confusion_matrix':confusion_matrix(ys,pred).tolist() if ys else [],'test_n':len(ys),'device':device,'weights':ck['init'],'model_version':ck['model_version'],'demo':bool(np.load(a.data).get('demo',False))}; (out/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8');
 import matplotlib
 matplotlib.use("Agg")
 import matplotlib.pyplot as plt
 cm=np.asarray(metrics['confusion_matrix']); fig,ax=plt.subplots();ax.imshow(cm,cmap='Blues');ax.set(xlabel='Predicted',ylabel='Actual',title='Confusion matrix');fig.savefig(out/'confusion_matrix.png');plt.close(fig)
 if len(set(ys))>1:
  fpr,tpr,_=roc_curve(ys,ps);fig,ax=plt.subplots();ax.plot(fpr,tpr);ax.plot([0,1],[0,1],':');ax.set(xlabel='False positive rate',ylabel='True positive rate',title='ROC');fig.savefig(out/'roc.png');plt.close(fig)
 print(metrics)
if __name__=='__main__':main()
