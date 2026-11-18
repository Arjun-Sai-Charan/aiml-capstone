"""Train a small MONAI 3D U-Net. Use --demo only when MSD data is absent."""
import argparse,json,os
from pathlib import Path
import numpy as np, torch
def main():
 p=argparse.ArgumentParser();p.add_argument('--demo',action='store_true');p.add_argument('--epochs',type=int,default=2);p.add_argument('--msd');p.add_argument('--output',default='AIML-02/outputs/segmentation');a=p.parse_args(); base=Path(a.msd or os.getenv('MSD_DIR',Path('AIML-02/data/raw/msd/Task04_Hippocampus'))); images=base/'imagesTr'; labels=base/'labelsTr'; demo=False
 if not images.exists() or not labels.exists():
  if not a.demo: raise FileNotFoundError(f'MSD Hippocampus missing at {base}; set MSD_DIR or run python run.py train-seg -- --demo')
  demo=True
 from monai.networks.nets import UNet
 from monai.losses import DiceLoss
 from monai.inferers import sliding_window_inference
 from monai.transforms import Compose,EnsureChannelFirstd,ScaleIntensityd,EnsureTyped
 from monai.data import Dataset,DataLoader
 model=UNet(spatial_dims=3,in_channels=1,out_channels=2,channels=(8,16,32,64),strides=(2,2,2),num_res_units=1); device='cuda' if torch.cuda.is_available() else 'cpu';model.to(device);loss_fn=DiceLoss(to_onehot_y=True,softmax=True);opt=torch.optim.Adam(model.parameters(),1e-3)
 if demo:
  rng=np.random.default_rng(9); data=[]
  for _ in range(4):
   x=rng.random((1,32,32,32),dtype=np.float32); y=np.zeros((1,32,32,32),dtype=np.int16);y[:,10:20,10:20,10:20]=1;data.append({'image':x,'label':y})
 else:
  from monai.data import load_decathlon_datalist
  from monai.transforms import LoadImaged,EnsureChannelFirstd,ScaleIntensityd,EnsureTyped
  listing=base/'dataset.json'; files=load_decathlon_datalist(str(listing),True,'training'); data=Dataset(files,Compose([LoadImaged(keys=['image','label']),EnsureChannelFirstd(keys=['image','label']),ScaleIntensityd(keys='image'),EnsureTyped(keys=['image','label'])]))
 dl=DataLoader(data,batch_size=1,shuffle=True);
 for ep in range(a.epochs):
  model.train(); vals=[]
  for batch in dl:
   x=batch['image'].to(device).float();y=batch['label'].to(device).long();opt.zero_grad();pred=model(x);loss=loss_fn(pred,y);loss.backward();opt.step();vals.append(loss.item())
  print('epoch',ep+1,'dice_loss',float(np.mean(vals)))
 model.eval(); batch=next(iter(dl)); vx=batch['image'].to(device).float(); vy=batch['label'].to(device).long()
 with torch.no_grad(): logits=sliding_window_inference(vx,(32,32,32),1,model); pred=logits.argmax(1); target=vy[:,0] if vy.ndim==5 else vy; inter=((pred==1)&(target==1)).sum().item(); denom=(pred==1).sum().item()+(target==1).sum().item(); dice=float(2*inter/max(denom,1))
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True); torch.save(model.state_dict(),out/'unet.pt')
 import matplotlib
 matplotlib.use("Agg")
 import matplotlib.pyplot as plt
 im=vx[0,0].detach().cpu().numpy(); mask=pred[0].detach().cpu().numpy(); z=im.shape[-1]//2; fig,ax=plt.subplots();ax.imshow(im[:,:,z],cmap='gray');ax.imshow(np.ma.masked_where(mask[:,:,z]==0,mask[:,:,z]),alpha=.4,cmap='autumn');fig.savefig(out/'slice_overlay.png');plt.close(fig)
 metrics={'demo':demo,'epochs':a.epochs,'device':device,'dice_score':dice,'score_split':'first training batch (illustrative, not held-out)'};(out/'metrics.json').write_text(json.dumps(metrics,indent=2));print(metrics)
if __name__=='__main__':main()
