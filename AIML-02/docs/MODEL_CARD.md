# Model card

**For education only, not clinical use.**

## Intended use
Learning and demonstration of imaging ML workflows; no diagnosis or care decisions.

## Data
RSNA Pneumonia Challenge: patient-level labels collapsed by maximum Target; balanced subset sampled positive Lung Opacity and negative classes from detailed class info. Images are resized and windowed to uint8 224x224. The current subset has 3,000 studies: 2,100 train, 450 validation, and 450 test, with 50/50 positive/negative labels in each split. The negative set is split evenly between Normal and No Lung Opacity / Not Normal.

## Metrics
A CPU smoke run on an earlier 3,000-row sample variant trained one epoch on 32 rows and evaluated five test cases once: accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.57; confusion matrix [[0, 3], [0, 2]]. It used random initialization because the ImageNet weights cache was not writable. The processed dataset was later rebuilt with an explicit 50/50 negative-class mix; these historical smoke metrics do not describe the current dataset and are not performance estimates. Full 3-5 epoch training/evaluation remains **PENDING - run `python run.py train-cls -- --epochs 3`** with a writable Torch cache.

## Limitations and bias
The rebuilt subset has balanced pneumonia classes and a 50/50 split between the two available negative source classes, unlike clinical prevalence; population and scanner coverage may not represent deployment populations. Labels can be noisy; bounding boxes are not used for localization and pneumonia labels are not equivalent to diagnosis. Artifacts, positioning, acquisition differences, and shortcuts can drive predictions. Segmentation demo data are synthetic if MSD is unavailable. DEMO mode returns neutral placeholder values and does not run a classifier or produce a Grad-CAM explanation. The committed project contains no model weights; a locally generated smoke checkpoint is ignored by Git.

## Interpretability limits

Grad-CAM heatmaps target the model's predicted class and show activation attribution, not a validated explanation. Heatmaps can highlight image edges, markers, devices, or other non-clinical artifacts; a highlighted region is not evidence that the model reasoned correctly. Heatmaps are not a diagnosis.
# Model file placement

A trained classifier checkpoint must be named `classifier.pt` and placed in `AIML-02/models/classifier.pt`, or selected with the `MODEL_PATH` environment variable. The classifier training command writes this checkpoint and `metrics.json` to `AIML-02/models` by default. For Colab/Kaggle, download both files from the training output directory and put them side by side in that folder. Confirm loading with `python run.py check-model`.

When no checkpoint is available, the service runs in DEMO mode and returns placeholder confidence/probability values. Do not interpret those values as predictions.
