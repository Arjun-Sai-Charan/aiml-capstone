# Decisions

- Keep modules under `AIML-02/src` and dispatch from root `run.py`; this keeps commands consistent on Windows, Linux, and Colab.
- Use patient ID as the unique sample key and stratified patient-level splits. Collapse box rows using maximum Target.
- Use compressed uint8 arrays to keep transfer artifacts compact; images are resized to 224x224.
- If source datasets are absent, synthetic output is explicitly marked DEMO and never presented as medical evidence.
- Dataset, training, and Docker outcomes are recorded only after actual execution.
