"""Reset the development SQLite database and generated study images."""
from src.service import app as service

service.Base.metadata.drop_all(service.engine)
service.Base.metadata.create_all(service.engine)
for pattern in ('*.png', '*.jpg', '*.jpeg'):
    for path in service.DATA_DIR.glob(pattern):
        if path.is_file():
            path.unlink()
print(f'Reset complete: {service.DATABASE_URL}; storage: {service.DATA_DIR}')
