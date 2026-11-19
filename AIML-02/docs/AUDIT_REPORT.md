# Project audit report

Audit date: 2026-11-19. Checks used current repository files, local artifacts, executed commands, HTTP responses, and the actual pytest run. Docker and Orthanc were left untouched per the current scope. The untracked `aiml_colab.zip` was not read, modified, staged, or committed.

## Verified status

- `python run.py test -- --tb=short`: **6 passed, 7 warnings in 10.85s**. Warnings are FastAPI lifecycle and Starlette/AnyIO deprecations.
- `python run.py check-model`: loaded the local checkpoint in real mode. Output included model version `efficientnet-b0-imagenet`, prediction `pneumonia`, confidence and pneumonia probability both `0.9606103897094727` for the bundled sample.
- Live `GET /health`: `model_loaded:true`, `model_version:"efficientnet-b0-imagenet"`, `mode:"real"`.
- Live `GET /studies`: 10 studies returned. Viewer root at `http://127.0.0.1:5173/` returned HTTP 200.
- Current classifier metrics file reports `demo:false`, ImageNet weights, `test_n:450`, accuracy 0.7977778, AUC 0.8843062, precision 0.8018018, recall 0.7911111, F1 0.7964206, confusion matrix `[[181,44],[47,178]]`, and `device:"cpu"`.
- Segmentation dataset `AIML-02/data/raw/msd/Task04_Hippocampus` is absent. The stored segmentation metrics say `demo:true`; Dice 0.0366846 is a synthetic training-batch score, not real-MRI or held-out performance.
- Pytest uses temporary DB/data directories in its fixtures; the dev DB inspected after tests contained 10 studies and 0 audit rows. Tests did not add test rows to the dev DB.
- `AIML-02/models/classifier.pt` exists locally but is ignored by Git. The user's statement that training used a Colab GPU is not corroborated by the matching metrics artifact, which says CPU; verify provenance before claiming this checkpoint's metrics came from GPU training.

## Findings

| Severity | Finding and location | Suggested fix |
|---|---|---|
| High | README clean-clone setup (`README.md:37-49`) now creates a venv but requires external RSNA files for `python run.py data`; raw data are not part of Git. | Make the first-run path explicit: provide the processed archive/data separately, or explain that the data task requires the local RSNA dataset. |
| High | Service is a local educational demo with permissive CORS and no authentication (`AIML-02/src/service/app.py:64,273-296`). | Keep it bound to localhost for the demo; add authentication and restrict CORS before exposing it to a network. |
| Medium | Classifier provenance mismatch: `AIML-02/models/metrics.json` says `device:"cpu"`, although the user reports Colab GPU training. | Match the checkpoint with its original Colab metrics/logs or rerun training and preserve the paired artifacts. |
| Medium | Segmentation is synthetic-only (`AIML-02/src/segmentation/train_monai.py`; `AIML-02/outputs/segmentation/metrics.json` says `demo:true`). | Keep results labeled demo-only; use MSD Task04 with a held-out split before making real segmentation performance claims. |
| Medium | Upload endpoint accepts user files (`AIML-02/src/service/app.py`, `/upload` route); review size/type handling before any non-local use. | Enforce byte limits, validate decoded formats, and use generated storage names outside the web root. |
| Medium | CORS behavior is permissive for development (`AIML-02/src/service/app.py:64`). | Restrict allowed origins to the local viewer origin for a local run. |
| Medium | Audit append-only behavior is implemented through service routes, not a database-level immutable constraint (`AIML-02/src/service/app.py:49-60,225-260`). | Add database-level protections or document that direct DB access can alter audit rows. |
| Medium | DVC data remote is local and machine-dependent (`.dvc/config`). | Configure a shared remote only if data sharing is authorized; keep sensitive/raw data out of Git. |
| Low | Test coverage does not prove a real checkpoint's metrics provenance or real-data segmentation quality (`AIML-02/tests/`). | Add loader/provenance tests and segmentation tests when real data are available. |
| Low | GitHub publication cannot be confirmed when no Git remote is configured (`git remote -v` was empty at audit time). | Add the intended remote and push only approved source/docs; keep ignored weights and data out. |

The findings above are code/repository observations, not evidence of clinical safety. This audit did not inspect or validate patient-level clinical performance.

## Segmentation: why it remains demo-only

The real MSD Hippocampus directory is missing. The demo path creates synthetic random volumes and artificial segmentation labels so the MONAI pipeline can execute. Its saved one-epoch Dice value is calculated on a training batch. It does not measure segmentation quality on MRI, and it is not a held-out score. To produce a real result, provide the dataset, set `MSD_DIR`, and run `python run.py train-seg -- --epochs 2` with a valid evaluation split.

## Docker/Orthanc

No Docker/Orthanc actions were performed. Existing Docker references were intentionally left as-is at the user's direction.

## Five items most likely to lose marks

1. Segmentation has no real MSD experiment or held-out Dice result.
2. The current checkpoint's metrics say CPU, which conflicts with the reported Colab GPU provenance unless the artifact pairing is verified.
3. Reflection is still the student's responsibility and is not written.
4. A presentation document is not itself proof of a delivered 10-minute presentation.
5. GitHub publication/remote and clean-clone reproducibility are not confirmed; local data and weights are excluded from Git.
