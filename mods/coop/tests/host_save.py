#!/usr/bin/env python3
"""Save a controller-earned key and reload it from a private cartridge backup.

This single-console persistence check does not establish wireless acceptance.
The ROM must have been built with the selected --save-slot.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from emulators import Emulators, ROOT
from campaign import check_castle_key, snapshot


def check_wireless_save(ds, metadata):
    """Use the real host pause/Save UI and inspect its cartridge backup."""
    slot=metadata.get('experimentalHostSaveSlot')
    if slot not in ('A','B','C'):
        raise RuntimeError('Wireless save check requires an explicit host save slot')
    selected=ord(slot)-ord('A')
    module=metadata['runtimeModule']
    epochs=[]
    for console in range(ds.count):
        base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
        epochs.append(ds.word(console,base+module['diagnosticOffsets']['coopSaveEpoch']))
        if ds.word(console,base+module['diagnosticOffsets']['coopSaveState'])!=1:
            raise RuntimeError(f'Console {console} did not finish sharing the host save')
        if ds.read(console,0x0209cdc8,1)!=bytes([selected]):
            raise RuntimeError(f'Console {console} loaded a different adventure slot')
        if not ds.word(console,0x0209caa4)&0x40:
            raise RuntimeError(f'Console {console} lost the controller-earned castle key')
    if len(set(epochs))!=1:raise RuntimeError('Save transaction counters already differ between consoles')
    before_path=ds.output/'wireless-save-before.sav'
    after_path=ds.output/'wireless-save-after.sav'
    ds.command(f'dumpcart 0 {before_path}')
    ds.command('keys 0 ff7')
    ds.run(24)
    ds.command('keys 0 fff')
    ds.run(120)
    if not all(ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)):
        raise RuntimeError('Host pause did not reach every console before saving')
    ds.touch(0,128,160)
    ds.run(120)
    snapshot(ds,'wireless-save-menu')
    ds.touch(0,128,96) # The pause menu's Save and Quit button.
    for attempt in range(40):
        ds.run(30)
        ds.command(f'dumpcart 0 {after_path}')
        after=after_path.read_bytes()
        offset=selected*128+14
        if int.from_bytes(after[offset:offset+4],'little')&0x40:break
    else:
        snapshot(ds,'wireless-save-failed')
        raise RuntimeError('The host cartridge did not persist the shared castle key')
    before=before_path.read_bytes()
    if len(before)!=len(after):raise RuntimeError('Cartridge backup size changed')
    for bank in (0,len(after)//2):
        for other in range(3):
            offset=bank+other*128
            if other!=selected and before[offset:offset+128]!=after[offset:offset+128]:
                raise RuntimeError('Wireless saving modified another adventure slot')
    for attempt in range(80):
        ids=[]
        states=[]
        initialized=True
        for console in range(ds.count):
            context=ds.word(console,0x0209cddc)
            if 0x02000000<=context<0x023fff80:
                pc=ds.word(console,context+0x40)
                snapshot(ds,'wireless-save-quit-exception')
                raise RuntimeError(f'Console {console} ARM9 exception at {pc:#010x} during Save and Quit')
            base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
            ended=ds.word(console,base+module['diagnosticOffsets']['coopSessionEnded'])
            if console:
                states.append({'guest':console,'sessionEnded':ended,
                               'net':ds.read(console,0x020a0f04,1)[0],
                               'wirelessState':ds.word(console,0x020a0f94)})
                if ended!=1 or states[-1]['net'] or states[-1]['wirelessState']:
                    initialized=False
                continue
            scene=ds.word(console,0x0209f5c0)
            ids.append(int.from_bytes(ds.read(console,scene+0xc,2),'little')
                       if 0x02000000<=scene<0x023ff000 else 0)
            if ids[-1]:
                alive=ds.read(console,scene+0xe,1)[0]
                flags=ds.read(console,scene+0x13,1)[0]
            else:
                alive=flags=0
            states.append({'scene':ids[-1],'alive':alive,'pauseFlags':flags})
            if ids[-1]!=1 or not alive or flags&1:initialized=False
        if initialized:break
        ds.run(30)
    else:
        snapshot(ds,'wireless-save-quit-failed')
        raise RuntimeError(f'Save and Quit did not return the host to title and end its guest sessions: {states}')
    for console in range(ds.count):
        base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
        if ds.word(console,base+module['diagnosticOffsets']['coopEnabled']):
            raise RuntimeError(f'Console {console} retained the co-op policy after title initialization')
        if ds.word(console,base+module['diagnosticOffsets']['coopSaveEpoch'])!=(epochs[0]^1):
            raise RuntimeError(f'Console {console} did not complete this save transaction')
    ds.run(120) # Allow the initialized host menu's fade to complete.
    snapshot(ds,'wireless-save-quit')
    if ds.word(0,0x0209fc68) or ds.read(0,0x020a0f04,1)[0] or ds.word(0,0x020a0f94):
        raise RuntimeError('The host returned to title with wireless still active')
    final_path=ds.output/'wireless-save-after-quit.sav'
    ds.command(f'dumpcart 0 {final_path}')
    final=final_path.read_bytes()
    for bank in (0,len(final)//2):
        for other in range(3):
            offset=bank+other*128
            if other!=selected and before[offset:offset+128]!=final[offset:offset+128]:
                raise RuntimeError('Save and Quit modified another adventure slot')
    print('Host cartridge saved the shared key and returned to title; Download Play guests ended their sessions.',flush=True)


def start(ds):
    for line in (ROOT/'mods/coop/tests/local_story.commands').read_text().splitlines():
        line=line.strip()
        if line.startswith('screen'):
            break
        if line and not line.startswith('#'):
            ds.command(line)
    ds.run(120)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--slot',choices=('A','B','C'),default='A')
    parser.add_argument('--runtime-report',type=Path,default=ROOT/'build/coop/build.json')
    args=parser.parse_args()
    output=args.output.resolve()
    if (output/'cart/console-0.sav').exists():
        parser.error('Use a fresh output directory; existing cartridge backups are never erased')
    output.mkdir(parents=True,exist_ok=True)
    os.environ['COOP_SAVE_DIR']=str(output/'cart')
    selected=ord(args.slot)-ord('A')
    digest=hashlib.sha256(args.image.read_bytes()).hexdigest()
    runtime_report=json.loads(args.runtime_report.read_text())
    if runtime_report.get('outputSha256',runtime_report.get('sha256'))!=digest:
        parser.error('--runtime-report must describe this exact ROM')
    module=runtime_report['runtimeModule']
    report={'status':'running','wirelessAcceptance':False,'wallClockFramePacing':False,
            'slot':args.slot,'romSha256':digest}
    try:
        with Emulators(args.image,0,output/'first-session',real_time=False) as ds:
            start(ds)
            if ds.read(0,0x0209cdc8,1)!=bytes([selected]):
                raise RuntimeError('The ROM did not load the selected adventure slot')
            if ds.word(0,0x0209caa4)&0x40:
                raise RuntimeError('The private test cartridge already has the castle key')
            ds.command(f'dumpcart 0 {output/"before.sav"}')
            check_castle_key(ds)
            ds.command('keys 0 ff7')
            ds.run(24)
            ds.command('keys 0 fff')
            ds.run(120)
            snapshot(ds,'pause-before-save')
            ds.touch(0,128,160)
            ds.run(120)
            snapshot(ds,'save-menu')
            ds.touch(0,128,96)
            ds.run(120)
            for attempt in range(20):
                path=output/'cart/console-0.sav'
                if path.exists():
                    raw=path.read_bytes()
                    offset=selected*128+14
                    if int.from_bytes(raw[offset:offset+4],'little')&0x40:
                        break
                ds.run(60)
            else:
                snapshot(ds,'save-not-written')
                raise RuntimeError('Native Save and Quit did not persist the castle key')
            ds.command(f'dumpcart 0 {output/"after.sav"}')
            for attempt in range(40):
                scene=ds.word(0,0x0209f5c0)
                if (0x02000000<=scene<0x023ff000 and
                    int.from_bytes(ds.read(0,scene+0xc,2),'little')==1 and
                    not ds.read(0,scene+0x13,1)[0]&1):
                    break
                ds.run(30)
            else:
                snapshot(ds,'save-quit-title-failed')
                raise RuntimeError('Save and Quit did not return to the title scene')
            base=ds.word(0,0x02004184)-int(module['entryOffset'],16)
            if ds.word(0,base+module['diagnosticOffsets']['coopEnabled']):
                raise RuntimeError('The title scene retained the old co-op save policy')
        before=(output/'before.sav').read_bytes()
        after=(output/'after.sav').read_bytes()
        if len(before)!=len(after):
            raise RuntimeError('Cartridge backup size changed')
        for base in (0,len(after)//2):
            for slot in range(3):
                if slot==selected:
                    continue
                offset=base+slot*128
                if before[offset:offset+128]!=after[offset:offset+128]:
                    raise RuntimeError('Saving modified another adventure slot')
        with Emulators(args.image,0,output/'second-session',real_time=False) as ds:
            start(ds)
            snapshot(ds,'reloaded-key')
            if not ds.word(0,0x0209caa4)&0x40:
                raise RuntimeError('A fresh launch did not reload the saved castle key')
        report.update(status='passed',saveBytes=len(after),
                      otherAdventureSlotsUnchanged=True,reloadedCastleKey=True,
                      coOpPolicyClearedAtTitle=True)
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
