#!/usr/bin/env python3
"""Exercise actual HaxxStation boot or the native SM64DS signed-loader parent."""
import argparse
import hashlib
import json
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
    parser.add_argument('--story',action='store_true',help='Require multiplayer castle-grounds gameplay and independent inputs')
    parser.add_argument('--shared-menus',action='store_true',help='Check host-controlled synchronized pause and resume')
    parser.add_argument('--castle-key',action='store_true',help='Catch the actual castle-key rabbit using controller input')
    parser.add_argument('--castle-entry',action='store_true',help='Collect the castle key and enter the castle together')
    parser.add_argument('--loader-only',action='store_true',help='Capture the signed loader without selecting a payload')
    parser.add_argument('--image',type=Path,help='Override the parent cartridge image')
    parser.add_argument('--payload-frames',type=int,default=18000)
    parser.add_argument('--menu-frames',type=int,default=3600)
    parser.add_argument('--clients',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.shared_menus and not args.story:
        parser.error('--shared-menus requires --story')
    if (args.castle_key or args.castle_entry) and not args.story:
        parser.error('--castle-key and --castle-entry require --story')
    if args.story:
        if args.parent!='native':parser.error('--story requires --parent native')
        args.game=True
    image=('haxxstation-boot-probe.nds' if args.parent=='station'
           else 'sm64ds-haxxstation-host-experimental.nds')
    image_path=args.image or ROOT/'build/coop/bootstrap'/image
    header=image_path.read_bytes()[:0x60]
    table_size=0x14+sum((struct.unpack_from('<I',header,offset)[0]+31)&~31
                       for offset in (0x44,0x4c,0x54,0x5c))
    checks=[]
    def report():
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'result.json').write_text(json.dumps({
            'romSha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
            'cartridgeConsoles':1,'firmwareOnlyConsoles':args.clients,
            'framePeriodUs':int(os.environ.get('COOP_FRAME_US','16667')),
            'mpReceiveTimeoutMs':int(os.environ.get('COOP_MP_TIMEOUT_MS','25')),
            'expectedWirelessTableBytes':table_size,
            'checks':checks,'campaignCompletionVerified':False},indent=2)+'\n')
    with Emulators(image_path,args.clients,args.output) as ds:
        ds.run(300)
        if args.parent=='native':
            ds.touch(0,128,120)
        for i in range(1,ds.count):ds.touch(i,128,140)
        ds.run(300)
        if port:=os.environ.get('COOP_GDB_EARLY_ARM9'):
            ds.command(f'gdb 1 {int(port)}')
            ready=Path(os.environ['COOP_GDB_READY'])
            for attempt in range(100):
                if ready.exists():break
                time.sleep(.1)
            else:raise RuntimeError('Debugger did not install its breakpoints')
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
            for attempt in range(0,args.menu_frames,60):
                phases=struct.unpack('<3I',ds.read(0,0x02000050,12))
                if all(phase==4 for phase in phases[:args.clients]):
                    break
                ds.run(min(60,args.menu_frames-attempt))
                if attempt%600==0:
                    print('Menu transfer diagnostics:',struct.unpack('<32I',ds.read(0,0x02000000,128)),flush=True)
            else:
                ds.screens('menu-not-ready-')
                for i in range(ds.count):
                    ds.command(f'dump {i} {ds.output / ("menu-not-ready-"+str(i)+".ram")}')
                    ds.command(f'dump7 {i} {ds.output / ("menu-not-ready-"+str(i)+".arm7")}')
                    ds.command(f'regs {i}')
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
        if args.loader_only:
            checks.append('signed-loader-menu')
            report()
            return
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
                    if args.game and current[14]==5 and all(
                            ds.read(i,0x020a0f04,1)==b'\x02' for i in range(1,ds.count)):
                        break
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
                checks.append('unsigned-game-client-startup')
                print('Unsigned SM64DS clients initialized native child networking with overlay verification intact; gameplay handoff still unverified.',flush=True)
            else:
                checks.append('unsigned-arm9-probe-on-every-client')
                print('HaxxStation executed modified SM64DS ARM9 on cartridge-free clients; boot kind 2 retained.',flush=True)
        if args.story:
            ds.run(1200)
            for i in range(ds.count):
                ds.command(f'dump {i} {ds.output / ("native-lobby-"+str(i)+".ram")}')
                ds.command(f'regs {i}')
            if not all(ds.read(i,0x0209fc50,1)==bytes([ds.count]) and
                       ds.word(i,0x020a1fcc)==2 and
                       ds.word(i,0x020a1fe4)==table_size for i in range(ds.count)):
                raise RuntimeError('Native party or wireless filesystem is not ready on every console')
            checks.append('native-party-and-mounted-wireless-filesystem')
            entered=False
            for attempt in range(30):
                if attempt%5==0:
                    print('Story progress:',[{
                        'console':i,'net':ds.read(i,0x020a0f04,1)[0],
                        'session':ds.word(i,0x0209fc68),
                        'level':ds.read(i,0x0209f2f8,1)[0],
                        'loading':ds.read(i,0x02092778,1)[0],
                        'players':sum(bool(ds.word(i,0x0209f394+4*j)) for j in range(ds.count)),
                        'wfsRead':hex(ds.word(i,0x020a1fdc))}
                        for i in range(ds.count)],flush=True)
                    for i in range(ds.count):
                        ds.command(f'dump {i} {ds.output / ("story-progress-"+str(i)+".ram")}')
                ds.touch(0,32,72)
                ds.run(120)
                ds.touch(0,128,20)
                ds.run(300)
                if all(ds.read(i,0x0209f21c,1)==bytes([ds.count]) and
                       ds.read(i,0x0209f2d8,1)==b'\0' and
                       ds.read(i,0x0209f2f8,1)==b'\x01' and
                       ds.read(i,0x02092778,1)==b'\0' and
                       all(ds.word(i,0x0209f394+4*j) for j in range(ds.count))
                       for i in range(ds.count)):
                    entered=True
                    break
                if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
                    print('Native session reported a connection error during story entry.',flush=True)
                    break
            if not entered:
                ds.screens('story-entry-failed-')
                for i in range(ds.count):
                    ds.command(f'dump {i} {ds.output / ("story-entry-failed-"+str(i)+".ram")}')
                    ds.command(f'dumptcm {i} {ds.output / ("story-entry-failed-"+str(i)+".dtcm")}')
                    ds.command(f'regs {i}')
                raise RuntimeError('The Download Play party did not enter multiplayer castle grounds')
            ds.run(180)
            def positions():
                return [tuple(struct.unpack('<iii',ds.read(i,ds.word(i,0x0209f394+4*j)+0x5c,12)))
                        for i in range(ds.count) for j in range(ds.count)]
            controlled=set()
            for controller in range(ds.count):
                before=positions()
                ds.command(f'keys {controller} fef')
                ds.run(60)
                ds.command(f'keys {controller} fff')
                ds.run(180)
                after=positions()
                moved={j for j in range(ds.count) if before[j]!=after[j]}
                if len(moved)!=1 or moved&controlled:
                    raise RuntimeError(f'Console {controller} did not control a distinct player: {moved}')
                controlled|=moved
                if any(after[i*ds.count:(i+1)*ds.count]!=after[:ds.count] for i in range(1,ds.count)):
                    raise RuntimeError(f'Player positions diverged after console {controller} input')
                print(f'Independent console {controller} input synchronized: {after[:ds.count]}',flush=True)
            ds.screens('story-movement-')
            for i in range(ds.count):
                ds.command(f'dump {i} {ds.output / ("story-movement-"+str(i)+".ram")}')
            print(f'{ds.count}-player Download Play castle-grounds entry and independent movement passed.',flush=True)
            checks.extend(['multiplayer-castle-grounds','distinct-inputs-and-synchronized-player-positions'])
            if args.shared_menus:
                def press(console, mask):
                    ds.command(f'keys {console} {mask}')
                    ds.run(12)
                    ds.command(f'keys {console} fff')
                    ds.run(120)
                def pause_states():
                    return [ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)]
                def menu_failure(message):
                    ds.screens('shared-menu-failed-')
                    for i in range(ds.count):
                        ds.command(f'dump {i} {ds.output / ("shared-menu-failed-"+str(i)+".ram")}')
                        ds.command(f'regs {i}')
                    raise RuntimeError(message)
                for console in range(1,ds.count):
                    press(console,'ff7')
                    if any(pause_states()):
                        menu_failure(f'Client {console} changed the shared pause state: {pause_states()}')
                press(0,'ff7')
                paused=pause_states()
                if not all(paused) or len(set(paused))!=1:
                    menu_failure(f'Host pause did not synchronize: {paused}')
                ds.screens('shared-pause-')
                before=positions()
                ds.run(120)
                if before!=positions():
                    menu_failure('Player positions changed while the shared game was paused')
                press(0,'ff7')
                if any(pause_states()):
                    menu_failure(f'Host resume did not synchronize: {pause_states()}')
                checks.append('host-controlled-synchronized-pause-and-resume')
                print('Client pause requests ignored; host pause and resume synchronized on every console.',flush=True)
            if args.castle_key or args.castle_entry:
                from campaign import check_castle_key
                check_castle_key(ds)
                checks.append('controller-driven-shared-castle-key')
                report()
            if args.castle_entry:
                from campaign import check_castle_entry
                check_castle_entry(ds)
                checks.append('controller-driven-shared-castle-entry')
        report()


if __name__=='__main__':main()
