# AI-Assisted Medical Imaging and Diagnosis System (AIML-02)

**For education only, not clinical use.**

A cross-platform educational project showing chest X-ray preprocessing and classification, hippocampus segmentation, Grad-CAM overlays, and a reviewable local API and React viewer. It is not a medical device and must not be used for diagnosis or care decisions.

## Features

- Patient-level RSNA Pneumonia subset: DICOM inversion/windowing, 224x224 uint8 preprocessing, balanced class sampling, and 70/15/15 train/validation/test splits.
- EfficientNet-B0 classifier with ImageNet weights when available and random-init fallback; weighted/balanced sampling, train-only augmentations, metrics, and plots.
- MONAI 3D U-Net workflow for MSD Hippocampus, with clearly marked synthetic demo mode.
- Grad-CAM overlays for test images.
- FastAPI local upload and optional Orthanc polling; SQLite study records and append-only review audit log.
- React viewer with newest-first study list, model/demo banner, pneumonia probability and predicted-class confidence, Grad-CAM opacity control, reviewer/comment fields, and audit log.
- DVC tracked processed dataset with a local remote.

## Architecture

```mermaid
flowchart LR
 D[RSNA / MSD] --> P[Preprocessing]
 P --> C[EfficientNet classifier]
 P --> G[MONAI 3D U-Net]
 C --> X[Grad-CAM]
 O[Orthanc] --> API[FastAPI]
 X --> API
 API --> DB[(SQLite studies)]
 DB --> UI[React viewer]
 UI --> R[Review API]
 R --> A[(Append-only audit log)]
```

See [detailed architecture and API](AIML-02/docs/architecture.md).

## Setup

Use Python 3.12 in the repository `.venv`. No data are downloaded. The local RSNA data are under `AIML-02/data/raw/rsna/`; set `RSNA_DIR` if your path differs. Set `MSD_DIR` to the MSD `Task04_Hippocampus` folder for real segmentation training.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py data
```

Linux/Colab: activate the root `.venv` (or use `.venv/bin/python`) and run `python run.py <task>` from the repository root.

## Run tasks

- Setup dependencies: `python run.py setup`
- Build the RSNA processed dataset: `python run.py data`
- Build a synthetic dataset if RSNA is absent: `python run.py data -- --demo`
- Train classification: `python run.py train-cls -- --epochs 3`
- Quick CPU classification smoke run: `python run.py train-cls -- --epochs 1 --max-samples 32`
- Generate Grad-CAM overlays: `python run.py gradcam`
- Train segmentation using MSD: `python run.py train-seg -- --epochs 2`
- Run synthetic segmentation demo if MSD is absent: `python run.py train-seg -- --demo --epochs 1`
- Reset local study database, uploads, and heatmaps: `python run.py reset-db`
- Start local API at port 8000: `python run.py serve`
- Check the classifier on one bundled DICOM sample: `python run.py check-model`
- Load all bundled DICOM samples into the running local service: `python run.py load-samples`
- Run tests: `python run.py test`
- Start the React viewer in a second terminal: `cd AIML-02/viewer; npm install; npm run dev`
- Validate Docker services: `docker compose -f AIML-02/docker/docker-compose.yml up --build`

The classifier loader defaults to `AIML-02/models/classifier.pt`. After GPU training in Colab/Kaggle, download the generated `classifier.pt` from the training output directory and place it at `AIML-02/models/classifier.pt` (create the `models` folder if needed). Place its adjacent `metrics.json` in the same folder so the viewer can show the model version. Alternatively set `MODEL_PATH` to the checkpoint path before starting the service. Check that it loads with `python run.py check-model`. Without it, the UI shows a DEMO warning. To load the bundled DICOM scans, start the API with `python run.py serve`, open another terminal at the repository root, and run `python run.py load-samples`.

## Results

| Work item | Result |
|---|---|
| RSNA data build | Complete: 3,000 images; 2,100 train, 450 validation, 450 test; each split class balanced. Compressed NPZ: 110,357,019 bytes. See [dataset counts](AIML-02/docs/DATASET_STATS.md). |
| Historical classification smoke | Earlier data variant: 1 epoch, 32 rows, 5-row test subset; accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.57; random initialization. It does not describe the current dataset. Full run: **PENDING - run `python run.py train-cls -- --epochs 3`**. |
| Grad-CAM | 10 overlays generated locally from the earlier smoke checkpoint. |
| Segmentation demo | Synthetic one-epoch training; illustrative first-batch Dice 0.0367 on synthetic data, not held-out performance. |
| Automated tests | 4 passed, 3 upstream deprecation warnings in 11.70s. See [test output summary](AIML-02/docs/TEST_RESULTS.md). |
| Viewer production build | Verified with Vite 8.3.8; `npm install`, `npm run build`, and dev server HTTP checks passed. |
| Docker runtime | Compose config validated; **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`** when Docker daemon is available. |

## Screenshots

Placeholder: capture the study list, selected scan with heatmap overlay, review controls, and audit log after running the viewer.

## Limitations

The balanced subset does not represent real-world disease prevalence. Dataset population and scanner coverage may not generalize; labels are noisy proxies, and bounding boxes are not localization ground truth. Image artifacts and acquisition differences can influence output. The historical smoke classification metrics use five test images from the earlier sample variant and do not describe the rebuilt dataset; the segmentation Dice is from synthetic training data. Without a checkpoint, the service runs in DEMO mode with neutral placeholder values and displays a warning; those values are not predictions. No output supports clinical use.

## Project documents

- [Model card](AIML-02/docs/MODEL_CARD.md)
- [Implementation decisions](AIML-02/docs/DECISIONS.md)
- [10-minute presentation outline](AIML-02/docs/PRESENTATION.md)
- [Reflection prompts](AIML-02/docs/REFLECTION_TEMPLATE.md)
- [Test and run results](AIML-02/docs/TEST_RESULTS.md)
