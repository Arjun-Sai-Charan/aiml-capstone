# Model card

**For education only, not clinical use.**

## Intended use
Learning and demonstration of imaging ML workflows; no diagnosis or care decisions.

## Data
RSNA Pneumonia Challenge: patient-level labels collapsed by maximum Target; balanced subset sampled positive Lung Opacity and negative classes from detailed class info. Images are resized and windowed to uint8 224x224. Exact sample size and split counts should be copied from data build output.

## Metrics
A CPU smoke run on an earlier 3,000-row sample variant trained one epoch on 32 rows and evaluated five test cases once: accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.57; confusion matrix [[0, 3], [0, 2]]. It used random initialization because the ImageNet weights cache was not writable. The processed dataset was later rebuilt with an explicit 50/50 negative-class mix; these historical smoke metrics do not describe the current dataset and are not performance estimates. Full 3-5 epoch training/evaluation remains **PENDING - run `python run.py train-cls -- --epochs 3`** with a writable Torch cache.

## Limitations and bias
The rebuilt subset has balanced pneumonia classes and a 50/50 split between the two available negative source classes, unlike clinical prevalence; population and scanner coverage may not represent deployment populations. Labels can be noisy; bounding boxes are not used for localization and pneumonia labels are not equivalent to diagnosis. Artifacts, positioning, acquisition differences, and shortcuts can drive predictions. Segmentation demo data are synthetic if MSD is unavailable. The local fallback DEMO score is a simple image statistic, not the trained classifier. The committed project contains no model weights; a locally generated smoke checkpoint is ignored by Git.
