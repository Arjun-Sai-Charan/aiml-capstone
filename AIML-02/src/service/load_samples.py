"""Upload sample DICOM studies to the local FastAPI service."""
from pathlib import Path
import os
import urllib.error
import urllib.request

samples = Path('AIML-02/data/samples')
files = sorted(samples.glob('*.dcm')) if samples.is_dir() else []
if not files:
    raise SystemExit(f'No sample DICOM files found in {samples}')
url = os.getenv('AIML_API_URL', 'http://127.0.0.1:8000').rstrip('/') + '/upload'
for path in files:
    boundary = '----aiml02' + path.stem
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: application/dicom\r\n\r\n').encode() + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    request = urllib.request.Request(url, data=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            print(path.name, response.status, response.read().decode('utf-8'))
    except urllib.error.URLError as exc:
        raise SystemExit(f'Cannot upload {path.name} to {url}. Start the updated service with python run.py serve. {exc}') from exc
