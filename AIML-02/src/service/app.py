"""Local educational inference API with isolated configurable storage."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import io
import json
import os
import threading
import time
import urllib.request
import uuid

import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from PIL import Image
from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE = Path(__file__).resolve().parents[2]
MODEL_IMAGE_SIZE = (224, 224)  # width, height; shared by the classifier input and displayed scan
DATA_DIR = Path(os.getenv('DATA_DIR', BASE / 'data' / 'local')).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{(DATA_DIR / 'studies.db').as_posix()}")
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()
MODEL_PATH = Path(os.getenv('MODEL_PATH', BASE / 'models' / 'classifier.pt')).resolve()


class Study(Base):
    __tablename__ = 'studies'
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    image_path = Column(String, nullable=False)
    heatmap_path = Column(String, nullable=False)
    prediction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    pneumonia_probability = Column(Float, nullable=False)
    status = Column(String, default='pending', nullable=False)
    model_version = Column(String, default='DEMO', nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Audit(Base):
    __tablename__ = 'audit_log'
    id = Column(String, primary_key=True)
    study_id = Column(String, nullable=False)
    who = Column(String, nullable=False)
    what = Column(String, nullable=False)
    when = Column(DateTime(timezone=True), nullable=False)
    model_version = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    pneumonia_probability = Column(Float, nullable=False)
    comment = Column(Text, default='')


Base.metadata.create_all(engine)
app = FastAPI(title='AIML-02 education API', description='For education only, not clinical use.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
_model = None
_model_version = 'DEMO'
_model_lock = threading.Lock()


class Review(BaseModel):
    decision: str
    reviewer: str
    comment: str = ''


def load_model():
    """Load a CPU-safe EfficientNet checkpoint and optional adjacent metrics."""
    global _model, _model_version
    if not MODEL_PATH.is_file():
        _model = None
        _model_version = 'DEMO'
        return None
    from torchvision.models import efficientnet_b0
    model = efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 2)
    checkpoint = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)
    state = checkpoint.get('state_dict', checkpoint) if isinstance(checkpoint, dict) else checkpoint
    model.load_state_dict(state)
    model.eval()
    metrics_path = MODEL_PATH.with_name('metrics.json')
    metrics = json.loads(metrics_path.read_text(encoding='utf-8')) if metrics_path.is_file() else {}
    _model_version = str(metrics.get('model_version') or checkpoint.get('model_version') or MODEL_PATH.stem)
    _model = model
    return model


def model_health():
    with _model_lock:
        if MODEL_PATH.is_file() and _model is None:
            load_model()
        return {'model_loaded': _model is not None, 'model_version': _model_version,
                'mode': 'real' if _model is not None else 'demo', 'education_only': True}


def serialize(study):
    return {'id': study.id, 'filename': study.filename, 'name': study.filename,
            'prediction': study.prediction, 'confidence': study.confidence,
            'pneumonia_probability': study.pneumonia_probability, 'status': study.status,
            'model_version': study.model_version,
            'heatmap_target': study.prediction if study.model_version != 'DEMO' else None,
            'heatmap_available': study.model_version != 'DEMO',
            'created_at': study.created_at.isoformat()}


def gradcam_for_class(model, tensor, predicted_class):
    """Compute Grad-CAM for the predicted class on the classifier's exact input tensor."""
    from pytorch_grad_cam import GradCAM
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    with GradCAM(model=model, target_layers=[model.features[-1]]) as cam:
        return cam(input_tensor=tensor, targets=[ClassifierOutputTarget(predicted_class)])[0]


def classify_image(image_array):
    with _model_lock:
        if MODEL_PATH.is_file() and _model is None:
            load_model()
        model = _model
        version = _model_version
    if model is None:
        # Demo output is intentionally non-informative and marked DEMO.
        return 'no pneumonia', 0.5, 0.5, 'DEMO', np.zeros_like(image_array)
    tensor = torch.from_numpy(np.repeat(image_array[None, None], 3, axis=1)).float()
    mean = torch.tensor([.485, .456, .406])[None, :, None, None]
    std = torch.tensor([.229, .224, .225])[None, :, None, None]
    tensor = (tensor - mean) / std
    with torch.no_grad():
        probabilities = model(tensor).softmax(1)[0].numpy()
    pneumonia_probability = float(probabilities[1])
    predicted_class = int(probabilities.argmax())
    confidence = float(probabilities[predicted_class])
    prediction = 'pneumonia' if predicted_class == 1 else 'no pneumonia'
    heatmap = image_array
    try:
        # Explain the predicted class using the exact normalized 224x224 scan tensor sent to the model.
        heatmap = gradcam_for_class(model, tensor, predicted_class)
    except Exception:
        pass
    return prediction, confidence, pneumonia_probability, version, heatmap


def create_study(data, name, is_dicom=False):
    from src.data.build_dataset import process_array
    if is_dicom:
        import pydicom
        dataset = pydicom.dcmread(io.BytesIO(data))
        patient_id = str(getattr(dataset, 'PatientID', '')).strip()
        name = patient_id or Path(name).stem or 'DICOM study'
        array = process_array(dataset.pixel_array,
            getattr(dataset, 'PhotometricInterpretation', '') == 'MONOCHROME1',
            getattr(dataset, 'RescaleSlope', 1), getattr(dataset, 'RescaleIntercept', 0),
            getattr(dataset, 'WindowCenter', None), getattr(dataset, 'WindowWidth', None))
        image = Image.fromarray(array)
    else:
        image = Image.open(io.BytesIO(data)).convert('L').resize(MODEL_IMAGE_SIZE)
        array = np.asarray(image, dtype=np.uint8)
    if (array.shape[1], array.shape[0]) != MODEL_IMAGE_SIZE:
        image = Image.fromarray(array).resize(MODEL_IMAGE_SIZE, Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.uint8)
    normalized = array.astype(np.float32) / 255
    prediction, confidence, pneumonia_probability, version, heat = classify_image(normalized)
    heat = np.asarray(heat, dtype=np.float32)
    heat = (heat - heat.min()) / max(float(heat.max() - heat.min()), 1e-6)
    # Resize the CAM map to the model/display source pixels, then apply identical square framing in the viewer.
    if heat.shape != array.shape:
        heat = np.asarray(Image.fromarray(np.uint8(np.clip(heat, 0, 1) * 255)).resize(
            (array.shape[1], array.shape[0]), Image.Resampling.BILINEAR), dtype=np.float32) / 255
    color = np.zeros((*array.shape, 3), dtype=np.uint8)
    color[:, :, 0] = np.uint8(heat * 255)
    color[:, :, 1] = np.uint8(np.clip(1 - np.abs(heat - .5) * 2, 0, 1) * 80)
    sid = str(uuid.uuid4())
    image_path = DATA_DIR / f'{sid}.png'
    heatmap_path = DATA_DIR / f'{sid}-heatmap.png'
    image.save(image_path, format='PNG')
    Image.fromarray(color).save(heatmap_path)
    study = Study(id=sid, filename=name, image_path=str(image_path), heatmap_path=str(heatmap_path),
        prediction=prediction, confidence=confidence, pneumonia_probability=pneumonia_probability,
        status='pending', model_version=version)
    db = Session()
    db.add(study)
    db.commit()
    db.close()
    return study


@app.get('/health')
def health():
    return model_health()


@app.get('/studies')
def studies():
    db = Session()
    rows = db.query(Study).order_by(Study.created_at.desc()).all()
    result = [serialize(row) for row in rows]
    db.close()
    return result


@app.get('/studies/{sid}')
def study(sid):
    db = Session()
    row = db.get(Study, sid)
    db.close()
    if row is None:
        raise HTTPException(404, 'Study not found')
    return serialize(row)


def file_response(sid, attr):
    db = Session()
    row = db.get(Study, sid)
    db.close()
    if row is None:
        raise HTTPException(404, 'Study not found')
    path = Path(getattr(row, attr))
    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
    return Response(path.read_bytes(), media_type=mime)


@app.get('/studies/{sid}/image')
def image(sid):
    return file_response(sid, 'image_path')


@app.get('/studies/{sid}/heatmap')
def heatmap(sid):
    return file_response(sid, 'heatmap_path')


@app.post('/studies/{sid}/review')
def review(sid, request: Review):
    if request.decision not in ('approve', 'reject'):
        raise HTTPException(400, 'decision must be approve or reject')
    db = Session()
    row = db.get(Study, sid)
    if row is None:
        db.close()
        raise HTTPException(404, 'Study not found')
    if row.status != 'pending':
        db.close()
        raise HTTPException(409, 'Study has already been reviewed')
    row.status = 'approved' if request.decision == 'approve' else 'rejected'
    db.add(Audit(id=str(uuid.uuid4()), study_id=sid, who=request.reviewer, what=request.decision,
        when=datetime.now(timezone.utc), model_version=row.model_version,
        confidence=row.confidence, pneumonia_probability=row.pneumonia_probability, comment=request.comment))
    db.commit()
    result = serialize(row)
    db.close()
    return result


@app.get('/audit-log')
def audit():
    db = Session()
    rows = db.query(Audit).order_by(Audit.when.desc()).all()
    result = [{'id': row.id, 'study_id': row.study_id, 'who': row.who, 'what': row.what,
        'when': row.when.isoformat(), 'model_version': row.model_version, 'confidence': row.confidence,
        'pneumonia_probability': row.pneumonia_probability, 'comment': row.comment} for row in rows]
    db.close()
    return result


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, 'Empty upload')
    filename = Path(file.filename or 'upload').name
    if filename.lower().endswith('.dcm') or file.content_type == 'application/dicom':
        try:
            return serialize(create_study(data, filename, is_dicom=True))
        except Exception as exc:
            raise HTTPException(400, f'Unable to read DICOM upload: {exc}') from exc
    try:
        source = Image.open(io.BytesIO(data))
        image_format = source.format
        if image_format not in ('PNG', 'JPEG'):
            raise HTTPException(415, 'Upload must be DICOM, PNG, or JPEG')
        source.verify()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, 'Upload must be a readable PNG or JPEG') from exc
    return serialize(create_study(data, filename))


def _poll_orthanc():
    url = os.getenv('ORTHANC_URL')
    if not url:
        return
    auth = ''
    if os.getenv('ORTHANC_USERNAME'):
        token = base64.b64encode(f"{os.getenv('ORTHANC_USERNAME')}:{os.getenv('ORTHANC_PASSWORD', '')}".encode()).decode()
        auth = 'Basic ' + token
    def fetch(path):
        headers = {'Authorization': auth} if auth else {}
        return urllib.request.urlopen(urllib.request.Request(url.rstrip('/') + path, headers=headers), timeout=10).read()
    seen = set()
    while True:
        try:
            for oid in json.loads(fetch('/instances')):
                if oid in seen:
                    continue
                raw = fetch(f'/instances/{oid}/file')
                import pydicom
                ds = pydicom.dcmread(io.BytesIO(raw))
                create_study(raw, str(getattr(ds, 'PatientID', oid)), is_dicom=True)
                seen.add(oid)
        except Exception as exc:
            print(f'Orthanc polling unavailable: {exc}')
        time.sleep(15)


@app.on_event('startup')
def startup():
    if MODEL_PATH.is_file():
        load_model()
    if os.getenv('ORTHANC_URL'):
        threading.Thread(target=_poll_orthanc, daemon=True).start()
