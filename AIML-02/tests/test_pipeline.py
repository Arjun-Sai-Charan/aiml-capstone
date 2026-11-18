import numpy as np
from src.data.build_dataset import process_array
def test_preprocessing_shape_range_and_monochrome1():
 source=np.arange(64*64,dtype=np.uint16).reshape(64,64)
 out=process_array(source,monochrome1=True)
 assert out.shape==(224,224) and out.dtype==np.uint8
 assert int(out.min())==0 and int(out.max())==255
def test_model_forward_when_torch_available():
 import pytest
 torch=pytest.importorskip('torch'); torchvision=pytest.importorskip('torchvision'); model=torchvision.models.efficientnet_b0(weights=None);model.classifier[1]=torch.nn.Linear(model.classifier[1].in_features,2);assert model(torch.zeros(1,3,224,224)).shape==(1,2)
def test_gradcam_overlay_shape():
 from src.classification.gradcam import overlay
 im=overlay(np.zeros((16,16),dtype=np.uint8),np.ones((16,16),dtype=np.float32));assert im.size==(16,16)
