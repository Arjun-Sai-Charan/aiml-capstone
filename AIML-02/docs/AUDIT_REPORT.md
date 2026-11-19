# AIML-02 Audit Report

Audit date: 2026-11-19. Current branch: `master`. The report was prepared without modifying project code, configuration, or data. Docker/Orthanc are **DESCOPED** under the current scope.

## Verification performed

### Test suite

Command: `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_ADDOPTS=-p no:cacheprovider`, then `.\.venv\Scripts\python.exe run.py test`.

Observed result:

```text
collected 4 items
AIML-02\tests\test_api.py .
AIML-02\tests\test_pipeline.py ...
======================= 4 passed, 3 warnings in 10.98s =======================
```

Warnings are upstream Starlette/AnyIO and FastAPI `on_event` lifecycle deprecations. `AIML-02/tests/conftest.py:9-21` sets `DATA_DIR`, `DATABASE_URL`, and `MODEL_PATH` to a fresh `.test-tmp` directory for each test and removes it afterward. Before/after the run, the live dev DB remained at 10 studies and 0 audit rows; tests did not add rows to it. Test suite breadth is small: three pipeline tests and one API test function (which has several assertions).

### Model check and live API

`python run.py check-model` output:

```text
{'sample': '149d826e-7078-4b2c-888a-d8811c72caf8.dcm', 'mode': 'demo', 'model_version': 'DEMO', 'prediction': 'no pneumonia', 'confidence': 0.5, 'pneumonia_probability': 0.5}
```

The configured default `AIML-02/models/classifier.pt` does not exist. This is the DEMO branch, not model inference.

Live HTTP checks against `http://127.0.0.1:8000` returned:

- `GET /health`: HTTP 200, `model_loaded:false`, `model_version:"DEMO"`, `mode:"demo"`, `education_only:true`.
- `GET /studies`: HTTP 200 with 10 studies. All observed rows are DEMO predictions with placeholder confidence/probability 0.5.

An additional temporary-database TestClient check returned health 200, empty studies 200, PNG upload 200, and review 200 with status `approved`. The resulting audit record contained `who:"audit-check"`, `what:"approve"`, a timestamp, model version `DEMO`, confidence 0.5, pneumonia probability 0.5 and the supplied comment. The temporary database and image directory were removed after the check. A multipart parser warning (`Skipping data after last boundary`) was logged, but the request succeeded.

### Data, DVC, model and environment checks

- Read `AIML-02/data/processed/manifest.csv`: 3,000 records, 3,000 unique patient IDs; split sizes train 2,100 / val 450 / test 450; each split is balanced 50/50 by label. Grouping `Target.max()` by `patientId` occurs before splitting in `AIML-02/src/data/build_dataset.py:60-78`.
- `AIML-02/src/classification/train.py:31,41-50` uses the stored split labels, selects model checkpoints by validation loss and traverses the held-out test indices once after training. No patient overlap exists in the processed manifest. A quick `--max-samples` run is not full evaluation evidence.
- `AIML-02/src/data/build_dataset.py:7-16,22-23` applies MONOCHROME1 inversion, rescale slope/intercept, DICOM windowing or 1st/99th percentile clipping, normalization and resize.
- Current classifier metrics file exactly records `test_n:5`, accuracy 0.4, AUC 0.5, precision 0.4, recall 1.0, F1 0.571428..., confusion matrix `[[0,3],[0,2]]`, CPU and random initialization. README/MODEL_CARD call these historical smoke metrics. The figures match the artifact, but the artifact has no dataset fingerprint or run timestamp; they should remain explicitly historical and not be described as full-model performance.
- Current segmentation metrics file says `demo:true`, `epochs:1`, CPU, Dice `0.036684606904662354`, with per-label values and `score_split` explicitly “training batch (illustrative, not held-out)”. MSD Task04 is absent. This is demo evidence, not real-data validation.
- `AIML-02/models/classifier.pt` is absent. `AIML-02/models/best.pt` is an ignored 16,314,334-byte local smoke checkpoint. No `.pt`/`.pth` weights are tracked in Git history.
- `AIML-02/data/processed.dvc` is tracked and `python -m dvc status` returned `Data and pipelines are up to date.` The configured remote is a local path, so this does not establish availability to a clean clone.
- `python -m pip check` returned `No broken requirements found.` Direct entries in `requirements.txt` are pinned. This checks the current venv, not a fresh install from the Internet.
- Git has eight readable implementation/fix commits before this report; `git remote -v` returned no output. Ten intentionally committed sample DICOMs total 1,404,272 bytes (largest 164,688 bytes). No model weights, raw RSNA tree, processed arrays, or oversized artifacts are tracked. `.gitignore` covers raw/processed data, `.pt`, `.pth`, `.env`, local outputs and SQLite data. Targeted scans found no committed absolute user paths or API/cloud secrets.
- Root README and AIML-02 README contain the exact education-only notice; the viewer header is persistent and the API/docs description contains it. `npm`/browser build artifacts were not regenerated during this no-change audit; the live Vite page returned HTTP 200.

### Honesty review of reported numbers and claims

- The current processed row count, patient uniqueness, split sizes, and NPZ byte size were checked directly and match the documented values.
- Classifier accuracy/AUC/precision/recall/F1/confusion numbers match the on-disk `metrics.json`, which has `test_n:5`, `weights:"random"`, and `demo:false`. The report is labeled historical/smoke in README and MODEL_CARD. The stated prior command and `--max-samples 32` are not recorded in the metrics artifact, so that run-command provenance cannot be independently confirmed from this checkout; this is a traceability gap, not evidence that the metrics were fabricated.
- Segmentation Dice and per-label values match the on-disk metrics file; that file says `demo:true` and `score_split:"training batch (illustrative, not held-out)`. The README/MODEL_CARD do not present this as real MSD or held-out performance.
- The documented ten Grad-CAM overlays exist in the output directory. The documented latest test duration is stale: the fresh run here was 10.98 seconds, not the previously documented 11.70 seconds.
- Docker/Orthanc runtime claims were not rerun because those items are DESCOPED. Their existing “PENDING” text should be changed to “DESCOPED,” not treated as a failed or missing milestone.

## Correctness and security findings

Finding count: **3 High, 6 Medium, 3 Low**.

| Severity | Finding and location | Evidence / suggested fix |
|---|---|---|
| High | No final default classifier. `AIML-02/src/service/app.py:31,75-91`; README model instructions at `README.md:66`. | The health endpoint and `check-model` both report DEMO; only an ignored smoke `best.pt` exists. Train the full 3,000-image split in Colab, then place `classifier.pt` and matching `metrics.json` at the documented path. Re-run check-model and health before presenting predictions. |
| High | Local API is network-exposed with wildcard CORS and no authentication. `AIML-02/src/service/app.py:63,69-72,223-253`; `run.py:16`. | Service binds `0.0.0.0`, accepts any CORS origin, and accepts a caller-supplied reviewer identity. For a local-only demo bind loopback and restrict origins; before any use with sensitive images add authentication/authorization and trusted reviewer identity. |
| High | Clean-clone setup does not create `.venv` or provision ignored datasets. `README.md:37-46,50-63`; `.gitignore:2-3`. | README's Windows pip command fails if `.venv` is absent; `python run.py data` fails without the ignored RSNA data; generic `python` may select an unintended interpreter. Document `py -3.12 -m venv .venv`, use `\.venv\Scripts\python.exe` for Windows tasks, and explain RSNA/MSD/processed-data provisioning. |
| Medium | Upload reads arbitrary request bodies fully into memory, with no byte limit. `AIML-02/src/service/app.py:256-277`. | A large PNG/JPEG/DICOM can exhaust service memory. Enforce a request/file size limit while streaming and reject oversized uploads before decoding. |
| Medium | DVC remote is machine-local. `.dvc/config:1-3`, `AIML-02/data/processed.dvc`. | Current DVC status is clean locally, but the configured path `../AIML-02/data/dvc_storage` is ignored/local and cannot support a fresh clone. Configure a shared remote and verify pull from a separate checkout. |
| Medium | Grad-CAM errors silently produce a non-CAM image. `AIML-02/src/service/app.py:130-139`. | `heatmap` starts as the input image and exceptions are swallowed; the route/viewer can then present intensity from the scan as though it were Grad-CAM. Return an explicit unavailable/error state instead of a fallback masquerading as a heatmap. |
| Medium | Audit is append-only through current HTTP routes, not immutable at the database layer. `AIML-02/src/service/app.py:48-58,223-253`. | Code inserts audit events and exposes no update/delete route, but SQLite rows can be updated/deleted directly and no immutable trigger/WORM storage exists. If “truly append-only” is required, enforce immutability at the database/storage layer. |
| Medium | Existing docs still present Docker/Orthanc work as in-scope or PENDING. `README.md:13,25,64,78`; `AIML-02/docs/architecture.md:7,28`; `AIML-02/docs/PRESENTATION.md:8`; `AIML-02/docs/TEST_RESULTS.md:35,39`. | These references contradict the current scope. Mark them DESCOPED or remove them in a later documentation-only cleanup; do not run Docker/Orthanc. |
| Medium | There is no GitHub remote configured. `git remote -v` produced no output. | Local history is readable, but a GitHub repository/push is not evidenced. Configure and push to the submission repository if required. |
| Low | Latest documented test timing is stale. `README.md:76`; `AIML-02/docs/TEST_RESULTS.md:9`. | Existing docs record 11.70s; this audit's fresh run was 10.98s. Both are real runs, but the “final run” wording should be updated to the latest result. |
| Low | Automated tests do not exercise the model-file loader or segmentation training/inference path. `AIML-02/tests/test_api.py:1`; `AIML-02/tests/test_pipeline.py:3,8,11`. | The current suite covers preprocessing, a model forward pass, Grad-CAM utility shape, and API review flow. Add targeted model checkpoint and segmentation tests when implementation work is allowed. |
| Low | Presentation separators are visibly corrupted. `AIML-02/docs/PRESENTATION.md:3-11`. | Time ranges and separators render as `?`; replace them with ASCII `-`/`|` and use the same readable form in the submitted slides. |

No inconsistency was found between `confidence` and `pneumonia_probability`: backend `AIML-02/src/service/app.py:121-140` returns the predicted-class probability as confidence and class-1 probability separately; the viewer displays both at `AIML-02/viewer/src/main.jsx:103-109`; the review endpoint copies both saved values into the audit event at `AIML-02/src/service/app.py:235-238`.

No patient leakage was found in the processed manifest: patient IDs are unique across its 3,000 rows. Label aggregation occurs before patient-level stratified split. The training script evaluates the test indices only after all epochs; it evaluates validation loss each epoch for model selection.

## Scope and documentation cleanup

Every item below is **DESCOPED**; it is not missing work and must not be run for this submission scope. Existing references to update later:

- `README.md:13,25,64,78` - Orthanc feature, architecture node, Docker task, Docker PENDING result.
- `AIML-02/docs/architecture.md:7,28` - Orthanc diagram and Docker/Orthanc absent language.
- `AIML-02/docs/PRESENTATION.md:8` - Orthanc agenda item.
- `AIML-02/docs/TEST_RESULTS.md:35,39` - Docker heading and Docker PENDING outcome.

## Top five likely mark losses

1. The default service is DEMO because the trained `classifier.pt` is absent; 0.5 values are placeholders.
2. Classifier evidence is only a five-case historical smoke evaluation, not full held-out results for the current dataset.
3. README setup does not create the venv or explain that raw data and the local DVC remote are absent from a clean clone.
4. No GitHub remote is configured; the presentation is only an outline and the personal reflection is still blank.
5. README/docs still describe Docker/Orthanc and Docker PENDING despite the explicit DESCOPED scope; presentation time separators are also corrupted.
