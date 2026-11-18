# Test and run results

Environment: Windows 11, Python 3.12.10 in the repository `.venv`; CPU execution.

## Automated tests

Command: `python run.py test`

Result: **4 passed, 17 warnings in 10.18s** on the final run after the smoke checkpoint was generated. Warnings were upstream Starlette/AnyIO and FastAPI lifecycle deprecations plus Matplotlib/Pyparsing deprecations.

## Dataset

Command: `python run.py data`

Completed using the local RSNA directory. The NPZ contains 3,000 uint8 images of shape 224x224, compressed size 110,357,019 bytes. The negative classes are explicitly balanced 50/50 within the negative subset; exact per-split mix is in the generated stats file. Counts: train 1,050 per class; validation 225 per class; test 225 per class. The generated [dataset statistics](DATASET_STATS.md) are from the real build.

## Classification smoke run

Command: `python run.py train-cls -- --epochs 1 --max-samples 32`

The training and one held-out smoke evaluation ran on an earlier dataset sample variant: 5 test rows; accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.5714; confusion matrix `[[0, 3], [0, 2]]`; CPU; random initialization because the Torch cache was inaccessible. Plotting initially failed when Matplotlib selected Tk; PNGs were later generated from recorded metrics without another test inference. The ROC PNG shows one observed threshold only, not a full curve. The processed dataset has since been rebuilt with explicit negative-class balance; these metrics do not describe the current dataset. Full classification: **PENDING - run `python run.py train-cls -- --epochs 3`**.

## Grad-CAM

Command: `python run.py gradcam`

Completed; 10 overlays were saved in the ignored `AIML-02/outputs/gradcam/` directory.

## Segmentation demo

Command: `python run.py train-seg -- --demo --epochs 1`

Completed on synthetic volumes; training loss 0.969166, illustrative first-training-batch Dice 0.036684606904662354 (label 1: 0.040146622447198466; label 2: 0.03322259136212625), CPU. This is demo output and not held-out performance. Outputs are ignored under `AIML-02/outputs/segmentation/`.

## Viewer build and Docker

Viewer install/build and dev server: **passed** using Node 24.13.0, Vite 8.3.8, and the official React plugin. `npm install` completed with 0 reported vulnerabilities; `npm run build` succeeded; the dev server served `/` and transformed `/src/main.jsx` with HTTP 200. Vite 8 removed the esbuild install path that was failing in the pasted log.

Docker runtime: **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`**. Docker Compose configuration validation passed, but the Docker daemon is unavailable in this environment.
