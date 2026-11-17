"""Create Grad-CAM overlays for test images."""
import argparse
from pathlib import Path
import numpy as np, torch
from PIL import Image
def overlay(image, heat):
 image=np.asarray(image,dtype=np.float32); heat=np.asarray(heat,dtype=np.float32); heat=(heat-heat.min())/max(float(heat.max()-heat.min()),1e-6); color=np.zeros((*heat.shape,3),dtype=np.float32);color[...,0]=heat; color[...,1]=np.maximum(0,1-abs(heat-.5)*2)*.4; return Image.fromarray(np.clip(image*.55+color*255*.45,0,255).astype('uint8'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default='AIML-02/data/processed/dataset.npz');p.add_argument('--model',default='AIML-02/models/best.pt');p.add_argument('--output',default='AIML-02/outputs/gradcam');a=p.parse_args(); z=np.load(a.data); ix=np.where(z['split'].astype(str)=='test')[0][:10]; out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 if not Path(a.model).exists(): raise FileNotFoundError(f'Model missing; run python run.py train-cls first: {a.model}')
 try:
  from torchvision.models import efficientnet_b0
  from pytorch_grad_cam import GradCAM
  from pytorch_grad_cam.utils.image import show_cam_on_image
 except ImportError as e: raise RuntimeError('Install requirements for Grad-CAM') from e
 model=efficientnet_b0(weights=None);model.classifier[1]=torch.nn.Linear(model.classifier[1].in_features,2);model.load_state_dict(torch.load(a.model,map_location='cpu',weights_only=False)['state_dict']);model.eval(); target=[model.features[-1]]
 from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
 with GradCAM(model=model,target_layers=target) as cam:
  for i in ix:
   img=z['images'][i]; rgb=np.repeat(img[...,None],3,axis=2).astype(np.float32)/255; tensor=torch.from_numpy(rgb.transpose(2,0,1)[None]); category=int(model(tensor).argmax(1)); mask=cam(input_tensor=tensor,targets=[ClassifierOutputTarget(category)])[0]; Image.fromarray(show_cam_on_image(rgb,mask,use_rgb=True)).save(out/f'{i}.png')
if __name__=='__main__':main()
