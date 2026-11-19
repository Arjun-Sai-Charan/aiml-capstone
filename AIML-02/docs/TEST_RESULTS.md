# Test and run results

Environment: Windows, Python 3.12.10 in the repository `.venv`; CPU execution for the recorded test run.

## Automated tests

Command: `python run.py test`

Current observed result: **6 passed, 7 warnings in 10.85s**. Warnings are upstream Starlette/AnyIO and FastAPI lifecycle deprecations. Tests cover temporary API storage, raster and DICOM upload, review/audit values, preprocessing, model forward pass, Grad-CAM utility shape, heatmap alignment, and predicted-class target selection.

## Dataset

Command: `python run.py data`

The processed NPZ currently contains 3,000 uint8 images of shape 224x224, compressed size 110,357,019 bytes. The manifest has 3,000 unique patient IDs: train 2,100, validation 450, test 450; each split has 1,050/225/225 samples per class. Negative-class mix is recorded in [dataset statistics](DATASET_STATS.md). These artifacts were inspected during the latest audit; the data build was not rerun in this documentation update.

## Current classifier

The local `AIML-02/models/classifier.pt` exists. Running `python run.py check-model` loaded it and returned:

```text
{'sample': '149d826e-7078-4b2c-888a-d8811c72caf8.dcm', 'mode': 'real', 'model_version': 'efficientnet-b0-imagenet', 'prediction': 'pneumonia', 'confidence': 0.9606103897094727, 'pneumonia_probability': 0.9606103897094727}
```

The current metrics artifact records `AIML-02/models/metrics.json`: `demo:false`, `weights:"ImageNet"`, `device:"cpu"`, `test_n:450`, accuracy 0.7977777777777778, AUC 0.8843061728395062, precision 0.8018018018018018, recall 0.7911111111111111, F1 0.796420581655481, and confusion matrix `[[181, 44], [47, 178]]`.

The user reports training with a Colab GPU, but this metrics artifact reports CPU. The repository does not record the training invocation or a checkpoint-to-metrics hash. Verify that the metrics file belongs to the submitted checkpoint before claiming GPU training. The checkpoint is ignored by Git and must be transferred separately to another checkout.

## Historical classifier smoke run

An earlier data variant smoke run evaluated 5 test rows: accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.5714; confusion matrix `[[0, 3], [0, 2]]`; CPU and random initialization. These historical values do not describe the current classifier.

## Grad-CAM

The service computes Grad-CAM for the classifier's predicted class from the same normalized 224x224 scan input shown in the viewer. If a map has another size, it is resized to the scan pixel dimensions; the viewer displays both layers in the same square frame. Study JSON identifies `heatmap_target`, and the viewer captions `Heatmap for: <class>`. Tests use controlled classifier/CAM doubles to verify pixel equality, 224x224 dimensions, and argmax-class selection. The current live API reports 10 studies with `heatmap_available:true`; maps were not visually reviewed during this documentation update.

## Segmentation demo

MSD Task04_Hippocampus is absent, so segmentation remains demo-only. `python run.py train-seg -- --demo --epochs 1` uses generated random volumes and artificial labels to verify the MONAI pipeline, not real MRI data. The saved metrics file says `demo:true`; its one-epoch Dice 0.036684606904662354 (label 1: 0.040146622447198466; label 2: 0.03322259136212625) is an illustrative training-batch score, not held-out performance.

## Viewer build and Docker

Viewer install/build and dev server: **passed** using Node 24.13.0, Vite 8.3.8, and the official React plugin. `npm install` completed with 0 reported vulnerabilities; `npm run build` succeeded; the dev server served `/` and transformed `/src/main.jsx` with HTTP 200. Vite 8 removed the esbuild install path that was failing in the pasted log.

Docker runtime: **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`**. Docker Compose configuration validation passed, but the Docker daemon is unavailable in this environment.

## Service helper commands

- `python run.py reset-db` previously completed and produced an empty dev database at that time. The current dev database has 10 studies and 0 audit rows.
- `python run.py check-model` currently loads the local classifier in real mode; output is shown above.
- `python run.py load-samples` was tested against a temporary API database; all 10 bundled DICOMs returned HTTP 200. The current local service also lists 10 studies.
