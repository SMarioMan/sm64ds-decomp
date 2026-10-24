#!/usr/bin/env python3
"""Build and exercise native stage entries on one console (not wireless).

Each image explicitly selects a diagnostic stage at compile time. These checks
do not establish access, earned stars, boss completion, or multiplayer support.
The default list covers the main courses and their separate stage areas.
All artifacts remain separate
from the integrated host cartridge. The shared build lock prevents collisions.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from diagnostic_stage import check_stage
from emulators import Emulators, ROOT
from host_save import start


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('/workspace/inputs/sm64ds-eu.nds'))
    parser.add_argument('--levels',type=int,nargs='+',default=list(range(6,29)))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--fast',action='store_true',help='Unpaced single-console diagnostic; not real-time wireless evidence')
    args=parser.parse_args()
    if any(not 1<=level<52 for level in args.levels):parser.error('Native stage IDs must be 1..51')
    args.output=args.output.resolve()
    if args.output.exists():parser.error('Use a new output directory to preserve existing test evidence')
    args.output.mkdir(parents=True)
    result={'wirelessAcceptance':False,'cartridgeConsoles':1,'firmwareOnlyConsoles':0,
            'campaignProgressionVerified':False,'paced':not args.fast,'stages':[],'status':'running'}
    def report():
        (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    report()
    for level in args.levels:
        directory=args.output/f'level-{level:02d}'
        directory.mkdir()
        entry={'level':level,'status':'running'}
        result['stages'].append(entry)
        report()
        try:
            with Path('/workspace/runtime/coop-bootstrap-build.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                with (directory/'build.log').open('w') as log:
                    subprocess.run([sys.executable,str(ROOT/'mods/coop/build.py'),str(args.rom),
                                    '--diagnostic-start-level',str(level)],cwd=ROOT,
                                   stdout=log,stderr=subprocess.STDOUT,check=True)
                image=directory/'diagnostic.nds'
                shutil.copyfile(ROOT/'build/coop/sm64ds-coop-experimental.nds',image)
                shutil.copyfile(ROOT/'build/coop/build.json',directory/'diagnostic.json')
                entry['romSha256']=hashlib.sha256(image.read_bytes()).hexdigest()
            os.environ['COOP_SAVE_DIR']=str(directory/'cart')
            with Emulators(image,0,directory,real_time=not args.fast) as ds:
                start(ds)
                actual=ds.read(0,0x0209f2f8,1)[0]
                if actual!=level:raise RuntimeError(f'Native stage entry selected {actual}, expected {level}')
                check_stage(ds,level)
            entry['status']='passed'
        except Exception as error:
            entry.update(status='failed',error=f'{type(error).__name__}: {error}')
            print(f'Diagnostic stage {level} FAILED: {error}',flush=True)
        report()
    result['status']='passed' if all(stage['status']=='passed' for stage in result['stages']) else 'failed'
    report()
    if result['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
