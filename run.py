"""Cross-platform task runner. Invoke with python run.py <task>."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TASKS = {
    'setup': ['-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')],
    'data': ['-m', 'src.data.build_dataset'],
    'train-cls': ['-m', 'src.classification.train'],
    'train-seg': ['-m', 'src.segmentation.train_monai'],
    'gradcam': ['-m', 'src.classification.gradcam'],
    'serve': ['-m', 'uvicorn', 'src.service.app:app', '--host', '0.0.0.0', '--port', '8000'],
    'test': ['-m', 'pytest', 'AIML-02/tests'],
    'reset-db': ['-m', 'src.service.reset_db'],
    'load-samples': ['-m', 'src.service.load_samples'],
    'check-model': ['-m', 'src.service.check_model'],
}
parser = argparse.ArgumentParser()
parser.add_argument('task', choices=TASKS)
args, extra = parser.parse_known_args()
if extra[:1] == ['--']:
    extra = extra[1:]
env = os.environ.copy()
env['PYTHONPATH'] = str(ROOT / 'AIML-02') + os.pathsep + env.get('PYTHONPATH', '')
raise SystemExit(subprocess.call([sys.executable, *TASKS[args.task], *extra], cwd=ROOT, env=env))
