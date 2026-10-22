#!/usr/bin/env python3
"""Exercise actual HaxxStation boot or the native SM64DS signed-loader parent."""
import argparse
import os
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'mods/coop/tests'))
from emulators import Emulators


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',choices=('station','native'),default='station')
    parser.add_argument('--probe',action='store_true',help='Select and execute the unsigned RAM-marker payload from either parent')
    parser.add_argument('--game',action='store_true',help='Check native game-client startup, not story gameplay')
    parser.add_argument('--image',type=Path,help='Override the parent cartridge image')
    parser.add_argument('--payload-frames',type=int,default=6000)
    parser.add_argument('--clients',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    image=('haxxstation-boot-probe.nds' if args.parent=='station'
           else 'sm64ds-haxxstation-host-experimental.nds')
    with Emulators(args.image or ROOT/'build/coop/bootstrap'/image,args.clients,args.output) as ds:
        ds.run(300)
        if args.parent=='native':
            ds.touch(0,128,120)
        for i in range(1,ds.count):ds.touch(i,128,140)
        ds.run(300)
        if args.parent=='native':
            for attempt in range(4):
                ds.touch(0,32,170)
                ds.run(300)
                if ds.word(0,0x02000000)==0x58584148:
                    break
            else:
                ds.screens('host-bootstrap-failed-')
                raise RuntimeError('Parent bootstrap did not initialize')
            print('Native parent heap-loaded bootstrap initialized.',flush=True)
        for i in range(1,ds.count):ds.touch(i,180,75)
        ds.run(600)
        ds.screens('discovery-')
        ds.accept()
        ds.run(120)
        ds.accept()
        ds.run(1200)
        if args.parent=='native':
            for attempt in range(60):
                phases=struct.unpack('<3I',ds.read(0,0x02000050,12))
                if all(phase==4 for phase in phases[:args.clients]):
                    break
                ds.run(60)
            else:
                ds.screens('menu-not-ready-')
                ds.command('status')
                print('Menu wait diagnostics:',struct.unpack('<32I',ds.read(0,0x02000000,128)),flush=True)
                raise RuntimeError('Signed loader menu did not finish on every client')
        ds.screens('signed-loader-')
        ds.command('status')
        for i in range(ds.count):
            ds.command(f'dump {i} {ds.output / ("signed-loader-"+str(i)+".ram")}')
        if args.parent=='native':
            debug=struct.unpack('<32I',ds.read(0,0x02000000,128))
            print('Native bootstrap diagnostics:',debug,flush=True)
            if not debug[2] or not debug[4]:
                raise RuntimeError('No signed-loader read or no Download Station port request')
            print('Native parent launched the signed loader and received a second-stage request.',flush=True)
            if port:=os.environ.get('COOP_GDB_ARM9'):
                ds.command(f'gdb 1 {int(port)}')
                ready=Path(os.environ['COOP_GDB_READY'])
                for attempt in range(100):
                    if ready.exists():break
                    time.sleep(.1)
                else:raise RuntimeError('Debugger did not install its breakpoints')
        if args.parent=='station' or args.probe or args.game:
            ds.accept()
            ds.run(120)
            ds.screens('payload-confirmation-')
            for i in range(1,ds.count):ds.touch(i,80,142)
            for elapsed in range(0,args.payload_frames,120):
                ds.run(min(120,args.payload_frames-elapsed))
                if not args.game and all(ds.read(i,0x02000000,8)==bytes.fromhex('434f4f5002000000')
                                         for i in range(1,ds.count)):
                    break
                if args.parent=='native':
                    current=struct.unpack('<32I',ds.read(0,0x02000000,128))
                    if elapsed%600==0:
                        print('Payload transfer:',current[20:23],current[29],current[28],flush=True)
                    if current[28]==7 and any(phase in (7,8) for phase in current[20:23]):
                        print('Parent reports no connected child during payload transfer.',flush=True)
                        break
            ds.screens('unsigned-probe-')
            ds.command('status')
            for i in range(ds.count):
                ds.command(f'dump {i} {ds.output / ("payload-final-"+str(i)+".ram")}')
                ds.command(f'regs {i}')
            if args.parent=='native':
                print('Final native diagnostics:',struct.unpack('<32I',ds.read(0,0x02000000,128)),flush=True)
            for i in range(1,ds.count):
                if args.game:
                    mode=ds.read(i,0x020a0f04,1)[0]
                    code=ds.read(i,0x0205de9c,8)
                    if mode!=2 or code!=bytes.fromhex('70402de958d04de2'):
                        raise RuntimeError(f'Native game client did not initialize on child {i}: mode={mode}, code={code.hex()}')
                else:
                    marker=ds.read(i,0x02000000,8)
                    if marker!=bytes.fromhex('434f4f5002000000'):
                        raise RuntimeError(f'Unsigned ARM9 probe did not execute on child {i}: {marker.hex()}')
            if args.game:
                print('Unsigned SM64DS clients initialized native child networking with overlay verification intact; gameplay handoff still unverified.',flush=True)
            else:
                print('HaxxStation executed modified SM64DS ARM9 on cartridge-free clients; boot kind 2 retained.',flush=True)


if __name__=='__main__':main()
