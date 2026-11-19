# AIML-02 Progress Report

Audit date: 2026-11-19. This report uses the current working tree, inspected local artifacts, command outputs, and HTTP checks. Docker and Orthanc are **DESCOPED** by the current project scope. No project code, configuration, or data was changed for this audit.

## Milestone status

| Original milestone | Status | Complete | Evidence observed | Remaining work |
|---|---:|---:|---|---|
| 1. Data choice, DICOM handling, preprocessing | DONE | 100% | `AIML-02/src/data/build_dataset.py:7-23,60-84`; processed NPZ is 110,357,019 bytes; manifest has 3,000 rows and 3,000 unique patient IDs; split counts are 2,100/450/450 with 50/50 labels; preprocessing tests pass. RSNA raw labels and image directory exist locally. | Raw RSNA input is intentionally not in Git; provision it separately on a clean machine and set `RSNA_DIR`. |
| 2. DVC versioning | PARTIAL | 75% | `AIML-02/data/processed.dvc` is tracked; `python -m dvc status` returned `Data and pipelines are up to date.`; `.dvc/config` points to `../AIML-02/data/dvc_storage`. | The configured remote is local and ignored, so a clean clone cannot pull this data from the Git repository alone. Configure/publish an accessible DVC remote for portability. |
| 3. Transfer-learning classifier | PARTIAL | 40% | EfficientNet-B0/ImageNet fallback and held-out evaluation code are in `AIML-02/src/classification/train.py:21-51`. `AIML-02/models/metrics.json` records a CPU smoke run with `test_n: 5`, accuracy 0.4, AUC 0.5, random initialization. `AIML-02/models/classifier.pt` is absent. `python run.py check-model` returned DEMO; `/health` returned `model_loaded:false`, `mode:"demo"`. | Train on the full split in Colab/Kaggle, retain real test metrics, and place the resulting `classifier.pt` plus adjacent `metrics.json` in `AIML-02/models/`. |
| 4. MONAI 3D U-Net segmentation | DONE | 100% | `AIML-02/src/segmentation/train_monai.py:27-70,73-103` implements three-label 3D U-Net, MONAI transforms, DiceLoss and sliding-window inference. MSD Task04 is absent. Existing `AIML-02/outputs/segmentation/metrics.json` says `demo:true`, `epochs:1`, and explicitly labels its Dice as training-batch illustrative. | The scope permits a clearly labeled demo when MSD is absent. For a real-data result, provide `MSD_DIR` and train/evaluate on a held-out split. Current Dice is not real-data or held-out performance. |
| 5. Grad-CAM | PARTIAL | 65% | Grad-CAM code is in `AIML-02/src/classification/gradcam.py`; 10 existing overlay PNGs are present under `AIML-02/outputs/gradcam/` from the smoke checkpoint. Viewer/service expose a heatmap route. | Regenerate and inspect overlays from the final full-data classifier. The service silently falls back to the input image if Grad-CAM raises an exception. |
| 6. Inference service and storage | DONE | 100% | `AIML-02/src/service/app.py`; live `GET /health` returned HTTP 200 in DEMO mode; live `GET /studies` returned 10 DEMO sample studies. An isolated TestClient check returned 200 for health, studies, upload, and review; its audit entry stored reviewer, action, time, model version, confidence, and pneumonia probability. | Scope target is met. Restrict network exposure and upload size before accepting sensitive or untrusted files. |
| 7. React viewer, review, audit log | DONE | 90% | `AIML-02/viewer/src/main.jsx` implements study selection, status/confidence badges, scan/overlay controls, reviewer/comment, approve/reject, audit view, and the education notice. `http://127.0.0.1:5173/` returned HTTP 200; API integration tests pass. | No browser-driven end-to-end test is in pytest. Verify the trained-model and review flow manually after loading the final checkpoint. |
| 8. Docker plus model limits/bias docs and education notice | PARTIAL | 90% | Model limits/bias are documented in `AIML-02/docs/MODEL_CARD.md`; root and project READMEs, viewer, API and architecture docs show the education-only notice. Docker/Orthanc are **DESCOPED**, not missing. | Existing README/docs still advertise Docker/Orthanc or call Docker PENDING; see the exact locations below. Update those lines when documentation edits are allowed. |

### Completion calculation

Overall in-scope completion: **82.5% (rounded to 83%)**. I averaged the eight milestone percentages equally: `(100 + 75 + 40 + 100 + 65 + 100 + 90 + 90) / 8`. The Docker part of milestone 8 is excluded from scoring because it is DESCOPED; the percentage there measures the remaining model-limit/bias documentation and education notice. This is implementation completeness, not model performance. The absent default classifier is the largest remaining functional gap.

## Submission deliverables

| Deliverable | Status | Evidence / gap |
|---|---|---|
| Working demo | PARTIAL | Viewer and API respond; ten local DICOM sample studies are in DEMO mode. A trained model is not installed, so predictions/0.5 values are placeholders. |
| GitHub repository with clean commits, README and setup | PARTIAL | Eight phase/fix commits are readable and the working tree was clean before these reports. `git remote -v` returned no remotes, so GitHub publication is not evidenced. Clean-clone setup also lacks venv creation and required data provisioning steps. |
| Architecture diagram | DONE | Mermaid diagram in `AIML-02/docs/architecture.md`. |
| Data and API documentation | PARTIAL | Dataset stats and API descriptions exist. DVC remote is local; a few scope and run-result references are stale. |
| Test results with accuracy numbers | PARTIAL | Four tests pass. A real historical smoke metrics file contains accuracy/AUC values, but it evaluates only five test examples and is not full-model evidence. |
| 10-minute presentation | PARTIAL | `AIML-02/docs/PRESENTATION.md` is an outline only; it is not slides or a recording and its separators render as question marks. |
| Individual reflection | NOT STARTED | `AIML-02/docs/REFLECTION_TEMPLATE.md` contains prompts; the reflection must be written by the student. |

## Model and data state

- `AIML-02/models/classifier.pt`: **absent**. An ignored `best.pt` smoke checkpoint exists locally, but it is not the configured default model and must not be treated as the final trained model.
- Service `GET /health`: **DEMO**, observed response `{"model_loaded":false,"model_version":"DEMO","mode":"demo","education_only":true}`.
- Classification `AIML-02/models/metrics.json`: present, real smoke-run artifact (`demo:false`) with `test_n:5`; it is not a full-run result.
- Segmentation `AIML-02/outputs/segmentation/metrics.json`: present and explicitly **demo:true**; it reports a one-epoch synthetic training-batch Dice, not held-out performance.
- MSD `Task04_Hippocampus`: **absent** at `AIML-02/data/raw/msd/Task04_Hippocampus`.
- RSNA raw labels/images and processed dataset/manifest: present locally. The current processed manifest contains 3,000 unique patients, train 2,100 / validation 450 / test 450.
- The dev SQLite database currently contains 10 studies and 0 audit rows. These are bundled sample uploads, not test-created rows.

## Remaining work

Estimates assume the provided RSNA processed NPZ can be uploaded to Colab/Kaggle and a usable GPU is available.

### Must do before submission

1. **Train the classifier and capture full held-out metrics (1.5-3 hours).** Upload `AIML-02/data/processed/dataset.npz` to Colab, install the pinned requirements as appropriate, then run `python run.py train-cls -- --epochs 3`. Do not use `--max-samples`. Download the actual `classifier.pt` and `metrics.json` produced in `AIML-02/models/`.
2. **Install and verify that artifact locally (0.5 hour).** Put both downloaded files in `AIML-02/models/`, run `python run.py check-model`, restart the API with `python run.py serve`, and confirm `/health` reports `mode:"real"`. Keep confidence and metrics claims tied to that run.
3. **Walk through the demo and capture evidence (0.5-1 hour).** In a second terminal run `python run.py load-samples`, start the viewer with `cd AIML-02/viewer; npm ci; npm run dev`, and verify scan display, review, and audit log. Capture the actual screens/results for submission.
4. **Fix the startup instructions for a clean Windows clone and reconcile docs with the DESCOPED scope (0.5-1 hour).** Add Python 3.12 venv creation, explicitly use `\.venv\Scripts\python.exe`, explain provisioning `RSNA_DIR`/processed NPZ, remove/label the Docker/Orthanc instructions and stale test timing, then run `python run.py test`.
5. **Prepare and deliver the presentation (1-1.5 hours).** Correct the broken separators in `AIML-02/docs/PRESENTATION.md`, replace the placeholder results section with verified results, and prepare the actual 10-minute slides/talk.
6. **Write the individual reflection (1 hour).** Use the prompts in `AIML-02/docs/REFLECTION_TEMPLATE.md`; do not present the template as a completed reflection.
7. **Publish if GitHub is required (0.5-1 hour).** Create/configure the intended remote, then push the audited commits and reports. No remote is currently configured.

Estimated must-do total: **5.5-9 hours**.

### Nice to have

- Provide MSD and run a real-data segmentation experiment with a held-out split (3-6 hours after data is available). Current scope accepts the clearly marked synthetic demo if the dataset is unavailable.
- Configure a shared/portable DVC remote and verify `dvc pull` from another clone (1-2 hours plus remote setup).
- Restrict CORS to the local viewer, bind the dev API to loopback, add reviewer authentication, and enforce a maximum upload size (1-2 hours).
- Enforce audit immutability at the database layer and add model-loader/segmentation regression tests (1-2 hours).

Estimated nice-to-have total: **6-11 hours**. Total remaining including nice-to-have work: **11.5-20 hours**; the must-do list fits approximately one workday if GPU training is available and dataset transfer is smooth.

## Docker/Orthanc references to correct later

These references remain in existing docs and are **DESCOPED**, not pending or missing:

- `README.md:13,25,64,78` - optional Orthanc feature, Orthanc architecture node, Docker startup task, Docker runtime PENDING row.
- `AIML-02/docs/architecture.md:7,28` - Orthanc architecture node and Docker/Orthanc absent wording.
- `AIML-02/docs/PRESENTATION.md:8` - Orthanc in the API presentation segment.
- `AIML-02/docs/TEST_RESULTS.md:35,39` - Docker heading and Docker runtime PENDING result.
