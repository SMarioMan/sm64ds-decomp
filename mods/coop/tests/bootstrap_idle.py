#!/usr/bin/env python3
"""Initialize the native parent with no guests; check for startup exceptions.

This uses a real melonDS console. It is not a wireless acceptance test.
"""
import argparse
import hashlib
import json
from pathlib import Path

from emulators import Emulators


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report={'status':'running','wirelessAcceptance':False,
            'romSha256':hashlib.sha256(args.image.read_bytes()).hexdigest()}
    try:
        with Emulators(args.image,0,args.output,real_time=False) as ds:
            ds.run(300)
            ds.touch(0,128,120)
            ds.run(300)
            for attempt in range(4):
                ds.touch(0,32,170)
                ds.run(300)
                if ds.word(0,0x02000000)==0x58584148:break
            else:
                raise RuntimeError('Native bootstrap did not initialize')
            for attempt in range(20):
                context=ds.word(0,0x0209cddc)
                if context:
                    pc=ds.word(0,context+0x40)
                    raise RuntimeError(f'Parent ARM9 exception at {pc:#010x}')
                if ds.word(0,0x020a0f50)==3:break
                ds.run(60)
            else:
                raise RuntimeError('Parent radio initialization did not complete')
            ds.run(600)
            if ds.word(0,0x0209cddc):
                raise RuntimeError('Idle parent entered an exception')
            work=ds.word(0,0x020a9db4)
            if not 0x02000000<=work<0x023f0000:
                raise RuntimeError('Parent has no wireless work buffer')
            if ds.read(0,work+0x1e2a,2)!=b'\0\0':
                raise RuntimeError('Idle parent unexpectedly has associated guests')
            if ds.read(0,0x020a0f08,1)!=b'\1':
                raise RuntimeError('Idle parent has an incorrect party count')
            ds.screens('idle-parent-')
            report.update(status='passed',idleFramesAfterInitialization=600,
                          noGuests=True,noARM9Exception=True)
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
