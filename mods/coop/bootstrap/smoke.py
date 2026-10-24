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
    parser.add_argument('--first-course',action='store_true',help='Continue through the castle into Bob-omb Battlefield')
    parser.add_argument('--course-return',action='store_true',help='Also exit the course through the host pause menu and check all controllers')
    parser.add_argument('--course-death',action='store_true',help='Take actual enemy damage and require the party to recover in the castle')
    parser.add_argument('--death-controller',type=int,default=0,help='Console whose player takes enemy damage (0 is host)')
    parser.add_argument('--course-star',action='store_true',help='Collect the actual Chain Chomp star, Save and Continue, and check the shared castle return')
    parser.add_argument('--host-save',action='store_true',help='Save a controller-earned key to the explicitly selected host slot and quit on every console')
    parser.add_argument('--quit-loaded-save',action='store_true',help='Isolate save/quit using a private host backup that already contains the castle key; does not test new progress persistence')
    parser.add_argument('--use-key-fixture',action='store_true',help='Use a private backup with a previously earned castle key for a later campaign checkpoint; record that fixture in the report')
    parser.add_argument('--disconnect-client',action='store_true',help='Power off the last guest and require every remaining console to end the session cleanly')
    parser.add_argument('--disconnect-host',action='store_true',help='Power off the host and require all guests to end the session cleanly')
    parser.add_argument('--loader-only',action='store_true',help='Capture the signed loader without selecting a payload')
    parser.add_argument('--image',type=Path,help='Override the parent cartridge image')
    parser.add_argument('--payload-frames',type=int,default=18000)
    parser.add_argument('--menu-frames',type=int,default=3600)
    parser.add_argument('--clients',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--menu-select-delays',type=int,nargs='+',
                        help='Frames before each guest selects the signed menu, in guest order; tests users joining at different times')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 0<=args.death_controller<=args.clients or (args.death_controller and not args.course_death):
        parser.error('--death-controller requires --course-death and a connected console')
    if args.use_key_fixture and not os.environ.get('COOP_SAVE_DIR'):
        parser.error('--use-key-fixture requires an explicit private COOP_SAVE_DIR')
    selection_delays=args.menu_select_delays or [0]*args.clients
    if len(selection_delays)!=args.clients or any(delay<0 for delay in selection_delays):
        parser.error('--menu-select-delays requires one nonnegative frame count per guest')
    if sum((args.course_return,args.course_death,args.course_star))>1:
        parser.error('Choose one course-return, course-death or course-star checkpoint for one run')
    if args.course_return or args.course_death or args.course_star:
        args.first_course=True
    if args.host_save and args.quit_loaded_save:
        parser.error('Choose --host-save for new progress or --quit-loaded-save for an existing private fixture')
    if args.host_save:
        args.castle_key=True
    if args.quit_loaded_save:
        args.host_save=True
    if args.first_course:
        args.castle_entry=True
    if args.shared_menus and not args.story:
        parser.error('--shared-menus requires --story')
    if args.disconnect_client and args.disconnect_host:
        parser.error('Choose a host or guest power-off check for one run')
    if (args.disconnect_client or args.disconnect_host) and (not args.story or args.host_save or args.castle_key or args.castle_entry):
        parser.error('Power-off checks require --story and a separate run from campaign/save checks')
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
    image_metadata=image_path.with_suffix('.json')
    metadata=json.loads(image_metadata.read_text()) if image_metadata.exists() else {}
    firmware_confirmations=0
    boot_timeout=int(os.environ.get('COOP_BOOT_MP_TIMEOUT_MS','25'))
    game_timeout=int(os.environ.get('COOP_MP_TIMEOUT_MS','25'))
    game_timeout_applied=False
    def report(status='running', error=None):
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'result.json').write_text(json.dumps({
            'romSha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
            'cartridgeConsoles':1,'firmwareOnlyConsoles':args.clients,
            'framePeriodUs':int(os.environ.get('COOP_FRAME_US','16667')),
            'maxEmulatedFrameLead':int(os.environ.get('COOP_MAX_FRAME_LEAD','0')),
            'melonDSMPTransport':'local',
            'cpuExecution':'jit' if os.environ.get('COOP_JIT') else 'interpreter',
            'mpReceiveTimeoutMs':game_timeout if game_timeout_applied else boot_timeout,
            'bootMpReceiveTimeoutMs':boot_timeout,
            'gameMpReceiveTimeoutMs':game_timeout,
            'gameMpReceiveTimeoutApplied':game_timeout_applied,
            'expectedWirelessTableBytes':table_size,
            'checks':checks,'status':status,'error':error,
            'firmwareConfirmationRetries':firmware_confirmations,
            'menuSelectionDelaysFrames':selection_delays,
            'persistentCartSaveDirectory':os.environ.get('COOP_SAVE_DIR'),
            'experimentalHostSaveSlot':metadata.get('experimentalHostSaveSlot'),
            'preexistingKeyFixture':args.quit_loaded_save or args.use_key_fixture,
            'campaignCompletionVerified':False},indent=2)+'\n')
    original_exception_hook=sys.excepthook
    def report_failure(kind, error, traceback):
        report('failed',f'{kind.__name__}: {error}')
        original_exception_hook(kind,error,traceback)
    sys.excepthook=report_failure
    report()
    with Emulators(image_path,args.clients,args.output,mp_timeout_ms=boot_timeout) as ds:
        ds.run(300)
        if args.parent=='native':
            ds.touch(0,128,120)
        for i in range(1,ds.count):ds.touch(i,128,140)
        ds.run(300)
        if port:=os.environ.get('COOP_GDB_EARLY_ARM9'):
            ds.command(f'gdb {int(os.environ.get("COOP_GDB_CONSOLE","1"))} {int(port)}')
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
        for attempt in range(10):
            ds.run(120)
            firmware_confirmations+=ds.select_firmware_downloads()
        if args.parent=='native':
            for attempt in range(0,args.menu_frames,60):
                phases=struct.unpack('<3I',ds.read(0,0x02000050,12))
                if all(phase==4 for phase in phases[:args.clients]):
                    break
                ds.run(min(60,args.menu_frames-attempt))
                if attempt%600==0:
                    debug=struct.unpack('<32I',ds.read(0,0x02000000,128))
                    print('Menu transfer diagnostics:',debug,flush=True)
                    retries=ds.select_firmware_downloads()
                    firmware_confirmations+=retries
                    if retries:
                        print('Retried selection on firmware-only clients:',retries,flush=True)
            else:
                ds.screens('menu-not-ready-')
                for i in range(ds.count):
                    ds.command(f'dump {i} {ds.output / ("menu-not-ready-"+str(i)+".ram")}')
                    ds.command(f'dump7 {i} {ds.output / ("menu-not-ready-"+str(i)+".arm7")}')
                    ds.command(f'dumptcm {i} {ds.output / ("menu-not-ready-"+str(i)+".dtcm")}')
                    ds.command(f'dumpwifi {i} {ds.output / ("menu-not-ready-"+str(i)+".wifi")}')
                    ds.command(f'regs {i}')
                ds.command('status')
                print('Menu wait diagnostics:',struct.unpack('<32I',ds.read(0,0x02000000,128)),flush=True)
                context=ds.word(0,0x0209cddc)
                if 0x02000000<=context<0x023fff80:
                    raise RuntimeError(f'Parent ARM9 exception at {ds.word(0,context+0x40):#010x}; see saved context and RAM')
                raise RuntimeError('Signed loader menu did not finish on every client')
        ds.screens('signed-loader-')
        ds.command('status')
        for i in range(ds.count):
            ds.command(f'dump {i} {ds.output / ("signed-loader-"+str(i)+".ram")}')
            ds.command(f'dumptcm {i} {ds.output / ("signed-loader-"+str(i)+".dtcm")}')
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
            report('passed')
            return
        if args.parent=='station' or args.probe or args.game:
            # Each guest can browse and confirm independently. The parent
            # must wait for actual payload requests rather than require the
            # human players to press A together.
            elapsed=0
            for delay,i in sorted((delay,i+1) for i,delay in enumerate(selection_delays)):
                ds.run(max(0,delay-elapsed))
                elapsed=max(elapsed,delay)
                ds.command(f'keys {i} ffe')
                ds.run(12)
                ds.command(f'keys {i} fff')
                ds.run(120)
                ds.touch(i,80,142)
                elapsed+=144
            ds.screens('payload-confirmation-')
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
            for elapsed in range(0,args.payload_frames,60):
                if all(ds.read(i,0x0209fc50,1)==bytes([ds.count]) and
                       ds.word(i,0x020a1fcc)==2 and
                       ds.word(i,0x020a1fe4)==table_size for i in range(ds.count)):
                    break
                ds.run(60)
            for i in range(ds.count):
                ds.command(f'dump {i} {ds.output / ("native-lobby-"+str(i)+".ram")}')
                ds.command(f'regs {i}')
            if not all(ds.read(i,0x0209fc50,1)==bytes([ds.count]) and
                       ds.word(i,0x020a1fcc)==2 and
                       ds.word(i,0x020a1fe4)==table_size for i in range(ds.count)):
                raise RuntimeError('Native party or wireless filesystem is not ready on every console')
            ds.command(f'mptimeout {game_timeout}')
            game_timeout_applied=True
            checks.append('native-party-and-mounted-wireless-filesystem')
            report()
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
            from campaign import check_yoshi_colors
            check_yoshi_colors(ds)
            checks.append('standard-multiplayer-yoshi-palettes')
            if metadata.get('experimentalHostSaveSlot') is not None:
                module=metadata['runtimeModule']
                for console in range(ds.count):
                    if ds.word(console,0x02004180)!=0x31504f43:
                        raise RuntimeError('No installed co-op runtime for host-save validation')
                    base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
                    if ds.word(console,base+module['diagnosticOffsets']['coopSaveState'])!=1:
                        raise RuntimeError(f'Console {console} did not finish loading the host adventure file')
                progress=[ds.read(console,0x0209caa0,0x44) for console in range(ds.count)]
                if len(set(progress))!=1:
                    raise RuntimeError('The full host adventure file differs between consoles')
                checks.append('host-adventure-file-loaded-and-shared')
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
            report()
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
                report()
                print('Client pause requests ignored; host pause and resume synchronized on every console.',flush=True)
            if args.castle_key or args.castle_entry:
                if args.use_key_fixture:
                    if not all(ds.word(i,0x0209caa4)&0x40 for i in range(ds.count)):
                        raise RuntimeError('The private fixture did not supply the previously earned key to every console')
                    checks.append('previously-controller-earned-key-fixture-loaded')
                else:
                    from campaign import check_castle_key
                    check_castle_key(ds)
                    checks.append('controller-driven-shared-castle-key')
                report()
            if args.castle_entry:
                from campaign import check_castle_entry
                check_castle_entry(ds)
                checks.append('controller-driven-shared-castle-entry')
                report()
            if args.first_course:
                from campaign import check_first_course
                check_first_course(ds)
                checks.append('controller-driven-shared-first-course')
                report()
            if args.course_return:
                from campaign import check_course_return
                check_course_return(ds)
                checks.append('controller-driven-shared-course-return')
            if args.course_death:
                from course_death import check_course_death
                check_course_death(ds,args.death_controller)
                checks.append('controller-driven-enemy-death-and-party-recovery')
            if args.course_star:
                from course_star import check_chain_star
                check_chain_star(ds)
                checks.append('controller-driven-star-collection-persistence-and-party-return')
            if args.host_save:
                from host_save import check_wireless_save
                check_wireless_save(ds,metadata)
                if args.course_star:checks.append('consecutive-star-and-quit-saves')
                checks.append('existing-host-file-save-and-shared-quit' if args.quit_loaded_save
                              else 'host-cartridge-save-and-shared-quit')
            if args.disconnect_client or args.disconnect_host:
                from disconnect import check_guest_disconnect
                check_guest_disconnect(ds,metadata,0 if args.disconnect_host else None)
                checks.append(('host' if args.disconnect_host else 'guest')+'-poweroff-and-clean-session-end')
        report('passed')


if __name__=='__main__':main()
