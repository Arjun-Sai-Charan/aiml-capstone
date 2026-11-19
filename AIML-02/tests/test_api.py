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
