# Model card

**For education only, not clinical use.**

## Intended use
Learning and demonstration of imaging ML workflows; no diagnosis or care decisions.

## Data
RSNA Pneumonia Challenge: patient-level labels collapsed by maximum Target; balanced subset sampled positive Lung Opacity and negative classes from detailed class info. Images are resized and windowed to uint8 224x224. The current subset has 3,000 studies: 2,100 train, 450 validation, and 450 test, with 50/50 positive/negative labels in each split. The negative set is split evenly between Normal and No Lung Opacity / Not Normal.

## Metrics

The current local `classifier.pt` has an adjacent metrics artifact reporting `demo:false`, ImageNet initialization, and a 450-image held-out test set. Recorded results: accuracy 0.7978, AUC 0.8843, precision 0.8018, recall 0.7911, F1 0.7964; confusion matrix [[181, 44], [47, 178]]. These are results from one balanced RSNA subset split, not external validation or evidence of clinical performance. The artifact records `device: cpu`; although Colab GPU training was reported, that claim is not corroborated by this metrics file and should be reconciled against the checkpoint's matching run before submission.

Historical smoke run on an earlier sample variant: one epoch, 32 rows, five test cases; accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.57; confusion matrix [[0, 3], [0, 2]], random initialization. These historical smoke values do not describe the current checkpoint.

## Limitations and bias
The rebuilt subset has balanced pneumonia classes and a 50/50 split between the two available negative source classes, unlike clinical prevalence; population and scanner coverage may not represent deployment populations. Labels can be noisy; bounding boxes are not used for localization and pneumonia labels are not equivalent to diagnosis. Artifacts, positioning, acquisition differences, and shortcuts can drive predictions. **Segmentation remains demo-only:** `MSD_DIR/Task04_Hippocampus` is not present, so the saved Dice is from one synthetic training batch and is not real-MRI or held-out performance. DEMO mode returns neutral placeholder values and does not run a classifier or produce a Grad-CAM explanation. Model weights are ignored by Git; distribute the trained checkpoint separately from the repository.

## Interpretability limits

Grad-CAM heatmaps target the model's predicted class and show activation attribution, not a validated explanation. Heatmaps can highlight image edges, markers, devices, or other non-clinical artifacts; a highlighted region is not evidence that the model reasoned correctly. Heatmaps are not a diagnosis.
# Model file placement

A trained classifier checkpoint must be named `classifier.pt` and placed in `AIML-02/models/classifier.pt`, or selected with the `MODEL_PATH` environment variable. The classifier training command writes this checkpoint and `metrics.json` to `AIML-02/models` by default. For Colab/Kaggle, download both files from the training output directory and put them side by side in that folder. Confirm loading with `python run.py check-model`.

When no checkpoint is available, the service runs in DEMO mode and returns placeholder confidence/probability values. Do not interpret those values as predictions.
