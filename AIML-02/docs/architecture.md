# Architecture and API

**For education only, not clinical use.**

```mermaid
flowchart LR
 O[Orthanc] --> S[FastAPI service]
 U[Local upload] --> S
 S --> M[Classifier + Grad-CAM]
 M --> D[(SQLite studies)]
 D --> V[React viewer]
 V --> R[Review API]
 R --> A[(Append-only audit log)]
```

POST `/upload` accepts multipart field `file` containing a PNG/JPEG. GET `/health`, `/studies`, `/studies/{id}`, `/studies/{id}/image`, `/studies/{id}/heatmap`, `/audit-log`; POST `/studies/{id}/review` takes `{decision: approve|reject, reviewer, comment}`. CORS is enabled.

The service polls Orthanc instances when `ORTHANC_URL` is set and remains usable via local upload without Orthanc. Docker runtime: **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`**.
