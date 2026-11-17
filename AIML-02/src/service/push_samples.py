"""Push sample DICOM files to an Orthanc REST endpoint."""
from pathlib import Path
import argparse,urllib.request
p=argparse.ArgumentParser();p.add_argument('--samples',default='AIML-02/data/samples');p.add_argument('--url',default='http://localhost:8042/instances');a=p.parse_args();files=list(Path(a.samples).glob('*.dcm'))
if not files:raise SystemExit(f'No sample DICOM files in {a.samples}')
for f in files:
 req=urllib.request.Request(a.url,data=f.read_bytes(),headers={'Content-Type':'application/dicom'});print(f.name,urllib.request.urlopen(req).status)
