# Model card

**For education only, not clinical use.**

## Intended use
Learning and demonstration of imaging ML workflows; no diagnosis or care decisions.

## Data
RSNA Pneumonia Challenge: patient-level labels collapsed by maximum Target; balanced subset sampled positive Lung Opacity and negative classes from detailed class info. Images are resized and windowed to uint8 224x224. Exact sample size and split counts should be copied from data build output.

## Metrics
A CPU smoke run trained one epoch on 32 selected rows and evaluated its 5-row test subset once: accuracy 0.40, AUC 0.50, precision 0.40, recall 1.00, F1 0.57. The confusion matrix was [[0, 3], [0, 2]]. The run used random initialization because the ImageNet weights cache was not writable. These tiny smoke metrics are only evidence that the pipeline executes; they are not useful performance estimates. A full 3-5 epoch experiment has not been run. **PENDING - run `python run.py train-cls -- --epochs 3`** in an environment with the processed data and a writable Torch cache.

## Limitations and bias
The subset has balanced classes unlike clinical prevalence; population and scanner coverage may not represent deployment populations. Labels can be noisy; bounding boxes are not used for localization and pneumonia labels are not equivalent to diagnosis. Artifacts, positioning, acquisition differences, and shortcuts can drive predictions. Segmentation demo data are synthetic if MSD is unavailable. The local fallback DEMO score is a simple image statistic, not the trained classifier. The committed project contains no model weights; a locally generated smoke checkpoint is ignored by Git.
