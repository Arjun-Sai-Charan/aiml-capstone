# Test and run results

Environment: Windows 11, Python 3.12.10 in the repository `.venv`; CPU execution.

## Automated tests

Command: `python run.py test`

Result: **6 passed, 7 warnings in 19.79s** on the current run. Warnings are upstream Starlette/AnyIO and FastAPI lifecycle deprecations. API checks cover isolated temporary storage, raster and DICOM upload, both probability fields, review audit values, and duplicate-review rejection.

## Dataset

Command: `python run.py data`

Completed using the local RSNA directory. The NPZ contains 3,000 uint8 images of shape 224x224, compressed size 110,357,019 bytes. The negative classes are explicitly balanced 50/50 within the negative subset; exact per-split mix is in the generated stats file. Counts: train 1,050 per class; validation 225 per class; test 225 per class. The generated [dataset statistics](DATASET_STATS.md) are from the real build.

## Classification smoke run

Command: `python run.py train-cls -- --epochs 1 --max-samples 32`

The training and one held-out smoke evaluation ran on an earlier dataset sample variant: 5 test rows; accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.5714; confusion matrix `[[0, 3], [0, 2]]`; CPU; random initialization because the Torch cache was inaccessible. Plotting initially failed when Matplotlib selected Tk; PNGs were later generated from recorded metrics without another test inference. The ROC PNG shows one observed threshold only, not a full curve. The processed dataset has since been rebuilt with explicit negative-class balance; these metrics do not describe the current dataset. Full classification: **PENDING - run `python run.py train-cls -- --epochs 3`**.

## Grad-CAM

Command: `python run.py gradcam`

Completed; 10 overlays were saved in the ignored `AIML-02/outputs/gradcam/` directory.

Alignment verification: service preprocessing stores the exact 224x224 grayscale image array passed to classification; CAM output is resized to those pixel dimensions if needed; the viewer uses a shared square frame with no independent object-fit: contain padding. API study JSON identifies the target as the predicted class (heatmap_target), and the viewer captions Heatmap for: <class>. Tests use controlled classifier/CAM doubles to verify identical source pixels, 224x224 output dimensions, and argmax-class target selection; no trained checkpoint is installed, so this does not claim a real-model CAM evaluation. Viewer production build also passed with Vite 8.3.8.

## Segmentation demo

Command: `python run.py train-seg -- --demo --epochs 1`

Completed on synthetic volumes; training loss 0.969166, illustrative first-training-batch Dice 0.036684606904662354 (label 1: 0.040146622447198466; label 2: 0.03322259136212625), CPU. This is demo output and not held-out performance. Outputs are ignored under `AIML-02/outputs/segmentation/`.

## Viewer build and Docker

Viewer install/build and dev server: **passed** using Node 24.13.0, Vite 8.3.8, and the official React plugin. `npm install` completed with 0 reported vulnerabilities; `npm run build` succeeded; the dev server served `/` and transformed `/src/main.jsx` with HTTP 200. Vite 8 removed the esbuild install path that was failing in the pasted log.

Docker runtime: **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`**. Docker Compose configuration validation passed, but the Docker daemon is unavailable in this environment.

## Service helper commands

- `python run.py reset-db`: completed. The database was queried afterward and contained 0 studies and 0 audit rows; generated study images were cleared.
- `python run.py check-model`: completed in DEMO mode because `AIML-02/models/classifier.pt` is not present. It read one bundled DICOM and returned the explicitly marked DEMO values of confidence 0.5 and pneumonia probability 0.5. These are placeholders, not model results.
- `python run.py load-samples`: completed against the updated API on a temporary port. All 10 bundled DICOMs returned HTTP 200 and were named using DICOM PatientID. The validation server used a temporary database, so these records were not added to the development database. For normal use, start the service with `python run.py serve` before running this helper.

The existing ignored `AIML-02/models/best.pt` smoke checkpoint was also loaded on CPU by running `MODEL_PATH=AIML-02/models/best.pt python run.py check-model` (PowerShell equivalent: `$env:MODEL_PATH="AIML-02/models/best.pt"; python run.py check-model`). It produced a forward-pass result with model version `best`, confidence 0.5037637948989868, and pneumonia probability 0.5037637948989868. This only verifies checkpoint loading and inference plumbing; it is not an evaluation metric or a clinically meaningful result. The default `classifier.pt` is absent, so ordinary startup remains in DEMO mode.
