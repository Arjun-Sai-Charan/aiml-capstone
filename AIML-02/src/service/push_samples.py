"""Push sample DICOM files to Orthanc. Set ORTHANC_USERNAME/PASSWORD if enabled."""
from pathlib import Path
import argparse,base64,os,urllib.request
p=argparse.ArgumentParser();p.add_argument('--samples',default='AIML-02/data/samples');p.add_argument('--url',default='http://localhost:8042/instances');a=p.parse_args();files=list(Path(a.samples).glob('*.dcm'))
if not files:raise SystemExit(f'No sample DICOM files in {a.samples}')
headers={'Content-Type':'application/dicom'}
if os.getenv('ORTHANC_USERNAME'):
 token=base64.b64encode(f"{os.getenv('ORTHANC_USERNAME')}:{os.getenv('ORTHANC_PASSWORD','')}".encode()).decode();headers['Authorization']='Basic '+token
for f in files:
 req=urllib.request.Request(a.url,data=f.read_bytes(),headers=headers);print(f.name,urllib.request.urlopen(req).status)
