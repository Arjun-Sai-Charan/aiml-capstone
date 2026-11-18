def test_health_upload_review_audit():
    from fastapi.testclient import TestClient
    from src.service.app import app
    from PIL import Image
    import io

    client = TestClient(app)
    assert client.get('/health').json()['education_only'] is True
    assert client.post('/upload', files={'file': ('bad.png', b'not an image', 'image/png')}).status_code == 400
    gif = io.BytesIO()
    Image.new('L', (8, 8), 0).save(gif, format='GIF')
    assert client.post('/upload', files={'file': ('bad.gif', gif.getvalue(), 'image/gif')}).status_code == 415
    image = io.BytesIO()
    Image.new('L', (32, 32), 100).save(image, format='PNG')
    response = client.post('/upload', files={'file': ('x.png', image.getvalue(), 'image/png')})
    assert response.status_code == 200
    study_id = response.json()['id']
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
