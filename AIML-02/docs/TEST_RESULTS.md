# Test and run results

Environment: Windows 11, Python 3.12.10 in the repository `.venv`; CPU execution.

## Automated tests

Command: `python run.py test`

Result: **4 passed, 17 warnings in 15.90s** on the final run after the smoke checkpoint was generated. Warnings were upstream Starlette/AnyIO and FastAPI lifecycle deprecations plus Matplotlib/Pyparsing deprecations.

## Dataset

Command: `python run.py data`

Completed using the local RSNA directory. The NPZ contains 3,000 uint8 images of shape 224x224, compressed size 110,278,764 bytes. Counts: train 1,050 per class; validation 225 per class; test 225 per class. The generated [dataset statistics](DATASET_STATS.md) are from the real build.

## Classification smoke run

Command: `python run.py train-cls -- --epochs 1 --max-samples 32`

The training and one held-out smoke evaluation completed, then plotting initially failed because Matplotlib selected Tk on this headless setup. Metrics were written before that error: 5 test rows; accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.5714; confusion matrix `[[0, 3], [0, 2]]`; CPU; random initialization because the Torch cache was inaccessible. PNG artifacts were subsequently generated from those recorded metrics without another test inference; the ROC PNG shows the observed single threshold only, not a full ROC curve. Full classification: **PENDING - run `python run.py train-cls -- --epochs 3`**.

## Grad-CAM

Command: `python run.py gradcam`

Completed; 10 overlays were saved in the ignored `AIML-02/outputs/gradcam/` directory.

## Segmentation demo

Command: `python run.py train-seg -- --demo --epochs 1`

Completed on synthetic volumes; training loss 0.6252784729003906, illustrative first-training-batch Dice 0.07421724004638577, CPU. This is demo output and not held-out performance. Outputs are ignored under `AIML-02/outputs/segmentation/`.

## Viewer build and Docker

Viewer build: **PENDING - run `npm install` and `npm run build` in `AIML-02/viewer`**. Here the Windows esbuild binary installed by npm was not a valid executable (`EFTYPE`); Vite could not run.

Docker runtime: **PENDING - run `docker compose -f AIML-02/docker/docker-compose.yml up --build`**. Docker Compose configuration validation passed, but the Docker daemon is unavailable in this environment.
