# Decisions

- Keep modules under `AIML-02/src` and dispatch from root `run.py`; this keeps commands consistent on Windows, Linux, and Colab.
- Use patient ID as the unique sample key and stratified patient-level splits. Collapse box rows using maximum Target.
- Use compressed uint8 arrays to keep transfer artifacts compact; images are resized to 224x224.
- If source datasets are absent, synthetic output is explicitly marked DEMO and never presented as medical evidence.
- Dataset, training, and Docker outcomes are recorded only after actual execution.

- Pin NumPy to 1.26.4 because MONAI 1.4 requires NumPy below 2; pin pathspec 0.12.1 because DVC 3.59 failed with pathspec 1.1.1.
- Redirect DVC's site cache into `.dvc-home/` because the default `C:\ProgramData\iterative` location is not writable here; keep the processed-data DVC remote local under the ignored data directory.
- Build the requested balanced 3,000-image subset and commit only ten small sample DICOMs; raw images and processed files remain uncommitted.
- Keep the actual CPU smoke metrics and synthetic segmentation Dice in docs, labeled as limited smoke/demo evidence. Do not present them as generalizable performance.
- Leave full Docker runtime and Vite build marked PENDING: the Docker daemon was absent and Windows could not execute npm's installed esbuild binary.
