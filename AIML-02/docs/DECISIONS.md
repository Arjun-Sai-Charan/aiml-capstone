# Decisions

- Keep modules under `AIML-02/src` and dispatch from root `run.py`; commands work on Windows, Linux, and Colab.
- Keep the patient ID as the unique dataset key, collapse RSNA box rows by maximum Target, and split at patient level.
- Store processed images as compressed uint8 arrays; synthetic output is always labeled DEMO.
- Run API tests against temporary SQLite and image directories so test uploads cannot pollute the development database.
- Use `AIML-02/models/classifier.pt` as the default CPU-loadable classifier path; accept `MODEL_PATH` for another location and adjacent `metrics.json` for version metadata.
- Return both predicted-class confidence and pneumonia probability. Record both in review audit events to preserve the decision context.
- Accept DICOM directly in `/upload`; show DICOM PatientID as the study name, and preserve the provided filename for PNG/JPEG uploads.
- Treat absent weights as DEMO mode with neutral placeholder probabilities and a persistent warning in the viewer.
- Keep DEMO and historical metrics distinct from model evaluation results; never infer accuracy from a smoke run.
