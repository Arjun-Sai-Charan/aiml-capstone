import shutil
import sys
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def clear_service_module():
    service_module = sys.modules.pop('src.service.app', None)
    service_package = sys.modules.get('src.service')
    if service_package is not None and hasattr(service_package, 'app'):
        delattr(service_package, 'app')
    return service_module

@pytest.fixture(autouse=True)
def isolated_service_storage(monkeypatch):
    temp_root = Path(tempfile.mkdtemp(prefix='aiml02-test-', dir=PROJECT_ROOT / '.test-tmp'))
    data_dir = temp_root / 'data'
    monkeypatch.setenv('DATA_DIR', str(data_dir))
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{(data_dir / 'test.db').as_posix()}")
    monkeypatch.setenv('MODEL_PATH', str(temp_root / 'missing-classifier.pt'))
    clear_service_module()
    yield
    service_module = clear_service_module()
    if service_module is not None:
        service_module.engine.dispose()
    shutil.rmtree(temp_root, ignore_errors=True)
