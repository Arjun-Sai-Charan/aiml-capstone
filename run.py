"""Cross-platform task runner. Invoke with python run.py <task>."""
from pathlib import Path
import argparse, subprocess, sys
ROOT=Path(__file__).resolve().parent
TASKS={'setup':['-m','pip','install','-r',str(ROOT/'requirements.txt')], 'data':['-m','src.data.build_dataset'], 'train-cls':['-m','src.classification.train'], 'train-seg':['-m','src.segmentation.train_monai'], 'gradcam':['-m','src.classification.gradcam'], 'serve':['-m','uvicorn','src.service.app:app','--host','0.0.0.0','--port','8000'], 'test':['-m','pytest','AIML-02/tests']}
p=argparse.ArgumentParser();p.add_argument('task',choices=TASKS);a,extra=p.parse_known_args(); extra=extra[1:] if extra[:1]==['--'] else extra; raise SystemExit(subprocess.call([sys.executable,*TASKS[a.task],*extra],cwd=ROOT))
