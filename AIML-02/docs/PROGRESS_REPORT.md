# Progress report

Audit date: 2026-11-19. This report reflects inspected files and real command/API runs. Docker and Orthanc are intentionally left as existing project material and are not part of this local-only work plan. The untracked `aiml_colab.zip` was left untouched and is not included in Git changes.

## Milestones

| Milestone | Status | Complete | Evidence | Remaining |
|---|---:|---:|---|---|
| 1. Data choice, DICOM and preprocessing | DONE | 100% | `AIML-02/src/data/build_dataset.py`; processed archive has 3,000 images and a 3,000-row, unique-patient manifest, split 2,100/450/450. | Dataset/raw files must be provisioned separately on another machine. |
| 2. DVC versioning | PARTIAL | 75% | DVC metadata and local remote configuration exist. | Local remote is machine-specific; processed data is not portable from Git alone. |
| 3. Classifier with transfer learning | DONE | 90% | `AIML-02/models/classifier.pt` exists; adjacent metrics report ImageNet initialization, `demo:false`, and 450 held-out cases. `python run.py check-model` loaded it successfully. | Metrics record `device: cpu`, while the user reports Colab GPU training. Reconcile the metrics/checkpoint provenance before claiming GPU training. |
| 4. MONAI 3D U-Net segmentation | PARTIAL | 50% | MONAI pipeline and synthetic demo run exist; `AIML-02/outputs/segmentation/metrics.json` has `demo:true`. | Segmentation is demo-only: `AIML-02/data/raw/msd/Task04_Hippocampus` is absent. The reported Dice is from a synthetic training batch, not MSD MRI or held-out evaluation. |
| 5. Grad-CAM | PARTIAL | 80% | Code and tests target the predicted class and same 224x224 preprocessed image; live API listed 10 studies with heatmaps available. | The maps were not visually inspected in this audit; fallback behavior should be reviewed if Grad-CAM errors. |
| 6. Inference service, SQLite and audit log | DONE | 100% | Live `/health` returned real mode; `/studies` returned 10 rows; API tests cover temporary storage and review/audit writes. | Audit immutability is enforced by route behavior, not a database-level append-only constraint. |
| 7. React viewer and review flow | DONE | 90% | Viewer returned HTTP 200; code includes study selection, scan/heatmap controls, approve/reject and audit page. | No automated browser end-to-end check. |
| 8. Model limits/bias documentation and education notice | DONE | 90% | README, model card, viewer and API disclose educational-only use; model card documents dataset bias and interpretability limits. | Continue to keep result/provenance statements tied to actual artifacts. Docker/Orthanc are left untouched. |

Overall in-scope completion: **84%**. Method: equal-weight average of the eight percentages above: `(100 + 75 + 90 + 50 + 80 + 100 + 90 + 90) / 8 = 84.375%`, rounded to the nearest whole percent. This is implementation completeness, not model quality. Segmentation is partial because real MSD data and a real held-out segmentation result are unavailable.

## Submission checklist

| Deliverable | Status | Evidence / next step |
|---|---|---|
| Working local demo | PARTIAL | API and viewer run; classifier is in real mode and 10 studies are listed. Start with `python run.py serve` and `cd AIML-02/viewer; npm run dev`. |
| GitHub repository with clean commits, README and setup | PARTIAL | Local commit history exists; no remote was configured at audit time. Add/publish a remote if required. |
| Architecture diagram | DONE | `AIML-02/docs/architecture.md`. |
| Data and API documentation | DONE | Dataset statistics, README and API/OpenAPI docs exist. |
| Test results and classifier metrics | DONE | `AIML-02/docs/TEST_RESULTS.md`; current pytest run: 6 passed, 7 warnings. Classifier metrics are reported in `AIML-02/models/metrics.json`. |
| 10-minute presentation | PARTIAL | `AIML-02/docs/PRESENTATION.md` exists; review/finalize the slides/timing. |
| Individual reflection | NOT STARTED | Fill `AIML-02/docs/REFLECTION_TEMPLATE.md` yourself. |

## Current model and data state

- `AIML-02/models/classifier.pt`: present locally (16,334,630 bytes); ignored by Git.
- Service `/health`: `model_loaded:true`, `model_version:"efficientnet-b0-imagenet"`, `mode:"real"`.
- Classification metrics: real artifact (`demo:false`, `test_n:450`); recorded accuracy 0.7978 and AUC 0.8843. Its metadata says CPU, so GPU provenance is not established by this artifact.
- Segmentation metrics: present but `demo:true`; Dice 0.0366846069 is illustrative synthetic training-batch output only.
- MSD Task04 Hippocampus: not present at the configured local path.
- Processed classification dataset: present locally; raw data/model checkpoint are not tracked in Git.

## Remaining work

### Must do before submission

1. **Resolve classifier run provenance (0.5-1 hour).** Compare the Colab training output/checkpoint to `AIML-02/models/metrics.json`; retain matching evidence. Do not describe the current metrics as GPU-produced unless confirmed. Command to recheck: `python run.py check-model`.
2. **Do a clean local demo pass (0.5-1 hour).** Start API with `python run.py serve`, then in another terminal run `python run.py load-samples`; verify viewer study selection and a review action. Keep Docker/Orthanc out of this flow.
3. **Finish submission artifacts (1-2 hours).** Prepare the presentation from `AIML-02/docs/PRESENTATION.md` and complete your reflection from `AIML-02/docs/REFLECTION_TEMPLATE.md`.

### Nice to have

1. **Run classifier training from the Colab GPU checkpoint/artifacts if provenance cannot be matched (1.5-3 hours, GPU time varies).** Upload processed data and run `python run.py train-cls -- --epochs 3`; save the produced checkpoint and matching metrics together.
2. **Run real segmentation if MSD data becomes available (3-6 hours).** Set `MSD_DIR` to the Task04_Hippocampus directory and run `python run.py train-seg -- --epochs 2`. Until then the synthetic demo is the only segmentation result.
3. **Visually inspect representative Grad-CAM overlays (0.5-1 hour).** Open the studies in the viewer and confirm overlays align; do not interpret them as diagnostic evidence.
