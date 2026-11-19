"""Run one classifier pass on the first sample DICOM or image."""
from pathlib import Path
import io
import numpy as np
from PIL import Image
from src.service import app as service

samples = Path('AIML-02/data/samples')
files = sorted(path for path in samples.iterdir() if path.suffix.lower() in ('.dcm', '.png', '.jpg', '.jpeg')) if samples.is_dir() else []
if not files:
    raise SystemExit(f'No sample images found in {samples}')
path = files[0]
if path.suffix.lower() == '.dcm':
    import pydicom
    ds = pydicom.dcmread(str(path))
    from src.data.build_dataset import process_array
    array = process_array(ds.pixel_array, getattr(ds, 'PhotometricInterpretation', '') == 'MONOCHROME1',
        getattr(ds, 'RescaleSlope', 1), getattr(ds, 'RescaleIntercept', 0),
        getattr(ds, 'WindowCenter', None), getattr(ds, 'WindowWidth', None))
else:
    array = np.asarray(Image.open(path).convert('L').resize((224, 224)), dtype=np.uint8)
result = service.classify_image(array.astype(np.float32) / 255)
prediction, confidence, probability, version, _ = result
print({'sample': path.name, 'mode': 'real' if service.MODEL_PATH.is_file() else 'demo',
       'model_version': version, 'prediction': prediction, 'confidence': confidence,
       'pneumonia_probability': probability})
