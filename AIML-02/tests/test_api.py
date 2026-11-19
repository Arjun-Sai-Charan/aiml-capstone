def test_health_upload_review_audit():
    from fastapi.testclient import TestClient
    from src.service import app as service
    from PIL import Image
    import io
    from pathlib import Path

    client = TestClient(service.app)
    health = client.get('/health').json()
    assert health == {'model_loaded': False, 'model_version': 'DEMO', 'mode': 'demo', 'education_only': True}
    assert service.DATA_DIR != Path(__file__).resolve().parents[1] / 'data' / 'local'
    assert client.post('/upload', files={'file': ('bad.png', b'not an image', 'image/png')}).status_code == 400
    gif = io.BytesIO()
    Image.new('L', (8, 8), 0).save(gif, format='GIF')
    assert client.post('/upload', files={'file': ('bad.gif', gif.getvalue(), 'image/gif')}).status_code == 415
    image = io.BytesIO()
    Image.new('L', (32, 32), 100).save(image, format='PNG')
    response = client.post('/upload', files={'file': ('teaching-image.png', image.getvalue(), 'image/png')})
    assert response.status_code == 200
    study = response.json()
    study_id = study['id']
    assert study['name'] == 'teaching-image.png'
    assert study['confidence'] >= .5
    assert study['pneumonia_probability'] == .5
    assert client.get('/studies').status_code == 200
    assert client.get(f'/studies/{study_id}').status_code == 200
    assert client.get(f'/studies/{study_id}/image').status_code == 200
    assert client.get(f'/studies/{study_id}/heatmap').status_code == 200

    review = client.post(
        f'/studies/{study_id}/review',
        json={'decision': 'approve', 'reviewer': 'test', 'comment': 'ok'},
    )
    assert review.status_code == 200 and review.json()['status'] == 'approved'
    entry = client.get('/audit-log').json()[0]
    assert entry['what'] == 'approve' and entry['who'] == 'test'
    assert entry['confidence'] == study['confidence']
    assert entry['pneumonia_probability'] == study['pneumonia_probability']
    assert client.post(f'/studies/{study_id}/review', json={'decision': 'reject', 'reviewer': 'test'}).status_code == 409

    sample = Path(__file__).resolve().parents[1] / 'data' / 'samples' / '149d826e-7078-4b2c-888a-d8811c72caf8.dcm'
    dicom = client.post('/upload', files={'file': (sample.name, sample.read_bytes(), 'application/dicom')})
    assert dicom.status_code == 200
    assert dicom.json()['name'] == '149d826e-7078-4b2c-888a-d8811c72caf8'


def test_heatmap_pixels_align_and_response_names_predicted_class(monkeypatch):
    from src.service import app as service
    from PIL import Image
    import io
    import numpy as np

    received = {}
    def fake_classifier(image_array):
        received['image'] = image_array.copy()
        # Model output predicts class 0; the low-resolution map is resized to scan pixels by create_study.
        return 'no pneumonia', 0.8, 0.2, 'test-checkpoint', np.arange(112 * 112, dtype=np.float32).reshape(112, 112)

    monkeypatch.setattr(service, 'classify_image', fake_classifier)
    source = Image.fromarray(np.arange(40 * 80, dtype=np.uint8).reshape(40, 80))
    buffer = io.BytesIO()
    source.save(buffer, format='PNG')
    study = service.create_study(buffer.getvalue(), 'alignment.png')

    displayed = np.asarray(Image.open(study.image_path), dtype=np.float32) / 255
    heatmap = Image.open(study.heatmap_path)
    assert received['image'].shape == (224, 224)
    assert np.array_equal(received['image'], displayed / 1.0)
    assert heatmap.size == (224, 224)
    result = service.serialize(study)
    assert result['heatmap_target'] == 'no pneumonia'
    assert result['heatmap_available'] is True


def test_gradcam_targets_model_argmax_class(monkeypatch):
    from src.service import app as service
    import numpy as np
    import torch

    captured = {}
    class FixedLogitModel:
        features = [object()]
        def __call__(self, tensor):
            return torch.tensor([[-1.0, 2.0]])

    def fake_cam(model, tensor, predicted_class):
        captured['class_index'] = predicted_class
        captured['input_shape'] = tuple(tensor.shape[-2:])
        return np.ones((224, 224), dtype=np.float32)

    service._model = FixedLogitModel()
    service._model_version = 'test-checkpoint'
    monkeypatch.setattr(service, 'gradcam_for_class', fake_cam)
    prediction, _, pneumonia_probability, _, _ = service.classify_image(np.zeros((224, 224), dtype=np.float32))
    assert prediction == 'pneumonia'
    assert pneumonia_probability > 0.5
    assert captured == {'class_index': 1, 'input_shape': (224, 224)}
