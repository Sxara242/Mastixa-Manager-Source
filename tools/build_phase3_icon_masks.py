"""Dev-only reproduction of the eight validated Phase 3 source masks.

Reads frozen masks and independent references, never creates test expectations.
Default output is diagnostic; --apply writes only successfully validated files.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/icon_mask_phase3'
ALLOWED={'cultivation.png','expenses.png','income.png','invoice_documents.png',
         'plant_protection.png','sales.png','suppliers_buyers.png','warehouse.png'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 manifest=json.loads((FIX/'manifest.json').read_text())
 ready={n for n,e in manifest['icons'].items() if e['status']=='VALIDATED_SOURCE'}
 if ready!=ALLOWED: raise ValueError('Unreviewed scope change')
 out=ROOT/('app/assets/icons/mastixa_menu' if args.apply else 'diagnostics/phase3/generated')
 out.mkdir(parents=True,exist_ok=True)
 for name in sorted(ready):
  folder=FIX/Path(name).stem;e=manifest['icons'][name]
  for file,key in [('original.png','original_sha256'),('approved_removal.png','removal_sha256'),('independent_protected.png','protected_sha256')]:
   if hashlib.sha256((folder/file).read_bytes()).hexdigest()!=e[key]: raise ValueError(f'Unreviewed fixture: {name}/{file}')
  a=np.array(Image.open(folder/'original.png').convert('RGBA'));b=a.copy()
  removal=np.array(Image.open(folder/'approved_removal.png'))>0
  protected=np.array(Image.open(folder/'independent_protected.png'))>0
  if np.any(removal&protected): raise ValueError(f'Protected region overlap: {name}')
  b[removal,3]=0
  if not np.array_equal(a[protected],b[protected]): raise ValueError(f'Protected RGBA changed: {name}')
  if hashlib.sha256(b.tobytes()).hexdigest()!=e['expected_rgba_sha256']: raise ValueError(f'Output mismatch: {name}')
  Image.fromarray(b).save(out/name)
  print(name,hashlib.sha256((out/name).read_bytes()).hexdigest())

if __name__=='__main__': main()
