"""Apply only the four reviewed prototype masks, preserving all RGB bytes.

Uses the frozen per-file annotation, not a brightness/radius detector. The tests
independently compare source RGBA against protected reference regions and pinned
expected digests. Needs Pillow and NumPy in the dev environment only.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'tests/fixtures/icon_mask_prototype'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',help='Write only PROTOTYPE_READY bundled PNGs')
    args=parser.parse_args()
    manifest=json.loads((FIX/'manifest.json').read_text(encoding='utf-8'))
    out=ROOT/'app/assets/icons/mastixa_menu' if args.apply else ROOT/'diagnostics/phase2/generated'
    out.mkdir(parents=True,exist_ok=True)
    for filename,entry in manifest['icons'].items():
        if entry['status']!='PROTOTYPE_READY':
            continue
        folder=FIX/Path(filename).stem
        original=(folder/'original.png').read_bytes()
        if hashlib.sha256(original).hexdigest()!=entry['original_sha256']:
            raise ValueError(f'Reference digest mismatch: {filename}')
        mask_bytes=(folder/'approved_removal.png').read_bytes()
        if hashlib.sha256(mask_bytes).hexdigest()!=entry['removal_mask_sha256']:
            raise ValueError(f'Unreviewed mask change: {filename}')
        a=np.array(Image.open(folder/'original.png').convert('RGBA'))
        removal=np.array(Image.open(folder/'approved_removal.png').convert('L'))==255
        a[removal,3]=0
        if hashlib.sha256(a.tobytes()).hexdigest()!=entry['expected_rgba_sha256']:
            raise ValueError(f'RGBA contract mismatch: {filename}')
        Image.fromarray(a).save(out/filename)
        print(filename,hashlib.sha256((out/filename).read_bytes()).hexdigest())

if __name__=='__main__':
    main()
