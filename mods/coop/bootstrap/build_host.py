#!/usr/bin/env python3
"""Experimental native SM64DS parent with a signed Download Station first stage.

The original hook prototype remains a separate build. This variant appends its
bootstrap assets under new raw file IDs, preserving every native archive.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import struct
import sys

import ndspy.codeCompression
import ndspy.rom
from ndspy import _common

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'mods/coop'))
from build import branch, link, symbols, pad_blz, CAVE_START, CAVE_END
from relocatable import pack, relocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--station',type=Path,default=Path('/workspace/inputs/download-station.nds'))
    parser.add_argument('--package', type=Path,
                        help='HaxxStation package containing demomenu and rom0000d; defaults to the boot probe')
    parser.add_argument('--output', type=Path,
                        help='Output ROM path; defaults to the experimental native host')
    parser.add_argument('--clients', type=int, choices=(1,2,3), default=3,
                        help='Number of Download Play clients to bootstrap before changing sessions')
    parser.add_argument('--handoff', action='store_true',
                        help='Return to the native game lobby after every payload finishes')
    parser.add_argument('--rearm-mp-after-boot', action='store_true',
                        help='Experiment: restart MP after firmware clients depart; retain the parent BSS')
    parser.add_argument('--serial-boot',action='store_true',
                        help='Experiment: boot each signed client after the previous client receives its menu')
    parser.add_argument('--restart-station-parent',action='store_true',
                        help='Experiment: recreate the native MB parent after firmware departure, retaining its TGID')
    parser.add_argument('--close-entry-before-boot',action='store_true',
                        help='Experiment: acknowledge closed association/beacon entry before firmware BOOT')
    parser.add_argument('--channel',type=int,choices=(1,7,13),
                        help='Use a fixed radio channel instead of the native channel measurement')
    parser.add_argument('--beacon-period',type=int,
                        help='Experiment: override the parent beacon interval in 802.11 time units (10..1000)')
    args = parser.parse_args()
    if args.beacon_period is not None and not 10<=args.beacon_period<=1000:
        parser.error('--beacon-period must be between 10 and 1000')
    if args.close_entry_before_boot and (not args.restart_station_parent or args.serial_boot or args.rearm_mp_after_boot):
        parser.error('--close-entry-before-boot requires only --restart-station-parent')
    root = ROOT/'build/coop/bootstrap'
    root.mkdir(parents=True, exist_ok=True)
    original = (ROOT/'build/coop/sm64ds-coop-experimental.nds').read_bytes()
    rom = ndspy.rom.NintendoDSRom(original)
    station = ndspy.rom.NintendoDSRom.fromFile(args.station)
    signed = station.files[station.filenames.idOf('mb/ds_demo_client.srl')]
    package_path = args.package or root/'haxxstation-boot-probe.nds'
    package = ndspy.rom.NintendoDSRom.fromFile(package_path)
    menu = package.files[package.filenames.idOf('ds_demo/demomenu')]
    probe = package.files[package.filenames.idOf('ds_demo/rom0000d')]
    cc = ROOT/'tools/mwccarm/2004/b56/mwccarm.exe'
    ld = ROOT/'tools/mwccarm/1.2/sp2p3/mwldarm.exe'
    launcher = shlex.split(os.environ['MWCCARM_LAUNCHER'])
    game = symbols(ROOT/'config/arm9/symbols.txt')
    overlay_symbols = symbols(ROOT/'config/arm9/overlays/ov075/symbols.txt')
    game.update(overlay_symbols)
    # Bootstrap readers open raw NitroFS IDs, so no filename entries are needed.
    # Keep the native archives: STAGE can request them even with story rules.
    ids = list(range(len(rom.files),len(rom.files)+4))
    old_fat,old_fat_size=struct.unpack_from('<II',original,0x48)
    if old_fat_size!=len(rom.files)*8:
        raise ValueError('Unexpected native FAT size')
    # Fixed position across probe/handoff builds, irrespective of body size.
    fat=(len(original)+511)&~511
    fat_size=old_fat_size+len(ids)*8
    filesystem_header=bytearray(original[0x40:0x60])
    struct.pack_into('<II',filesystem_header,8,fat,fat_size)
    base = 0x02200000
    game['CoopOriginalMBTick'] = base+0x1800
    game['CoopOriginalMBReceive'] = base+0x1808
    game['CoopOriginalParentEvent'] = base+0x1810
    game['CoopOriginalMBSend'] = base+0x1818
    boot_size = sum(struct.unpack_from('<I',signed,p)[0] for p in (0x2c,0x3c))+0x1e8
    define = [f'COOP_EXPECTED_CLIENTS={args.clients}', f'COOP_GAME_HANDOFF={int(args.handoff)}',
              f'COOP_REARM_MP_AFTER_BOOT={int(args.rearm_mp_after_boot)}',
              f'COOP_SERIAL_BOOT={int(args.serial_boot)}',
              f'COOP_RESTART_STATION_PARENT={int(args.restart_station_parent)}',
              f'COOP_CLOSE_ENTRY_BEFORE_BOOT={int(args.close_entry_before_boot)}',
              f'COOP_BOOT_CHANNEL={args.channel or 0}',
              f'COOP_BOOT_BEACON_PERIOD={args.beacon_period or 0}',
              f'COOP_SIGNED_BOOT_FILE={ids[1]}', f'COOP_SIGNED_BOOT_SIZE={boot_size}',
              f'COOP_MENU_FILE={ids[2]}', f'COOP_MENU_SIZE={len(menu)}',
              f'COOP_PAYLOAD_FILE={ids[3]}', f'COOP_PAYLOAD_SIZE={len(probe)}']
    body, exports = link(ROOT/'mods/coop/bootstrap/host.cpp', root/'host', base, game, launcher, cc, ld, define)
    game['CoopOriginalMBTick'] = base+len(body)
    game['CoopOriginalMBReceive'] = base+len(body)+8
    game['CoopOriginalParentEvent'] = base+len(body)+16
    game['CoopOriginalMBSend'] = base+len(body)+24
    body, exports = link(ROOT/'mods/coop/bootstrap/host.cpp', root/'host', base, game, launcher, cc, ld, define)
    arm9 = ndspy.codeCompression.decompress(rom.arm9)
    old_tick = game['func_0203e20c']
    prologue = arm9[old_tick-rom.arm9RamAddress:old_tick-rom.arm9RamAddress+4]
    if prologue != bytes.fromhex('f04f2de9') or game['CoopOriginalMBTick'] != base+len(body):
        raise ValueError('Unexpected native MB tick prologue or unstable payload')
    body += prologue + branch(base+len(body)+4, old_tick+4)
    receive = game['func_0206655c']
    receive_prologue = arm9[receive-rom.arm9RamAddress:receive-rom.arm9RamAddress+4]
    if receive_prologue != bytes.fromhex('f0412de9'):
        raise ValueError('Unexpected MB receive prologue: '+receive_prologue.hex())
    body += receive_prologue + branch(base+len(body)+4,receive+4)
    parent_event=game['func_02066a94']
    event_prologue=arm9[parent_event-rom.arm9RamAddress:parent_event-rom.arm9RamAddress+4]
    if event_prologue!=bytes.fromhex('f0472de9'):
        raise ValueError('Unexpected MB parent event prologue')
    body+=event_prologue+branch(base+len(body)+4,parent_event+4)
    mb_send=game['func_02065f78']
    send_prologue=arm9[mb_send-rom.arm9RamAddress:mb_send-rom.arm9RamAddress+4]
    if send_prologue!=bytes.fromhex('30402de9'):
        raise ValueError('Unexpected MB sender prologue: '+send_prologue.hex())
    body+=send_prologue+branch(base+len(body)+4,mb_send+4)
    fixups = relocations(root/'host.o',root/'host.elf',base,body)
    fixups.extend([0x80000000 | (len(body)-28),0x80000000 | (len(body)-20),0x80000000 | (len(body)-12),
                   0x80000000 | (len(body)-4)])
    blob = pack(base,body,exports['CoopBootstrapInit'],sorted(fixups))
    (root/'host-relocatable.bin').write_bytes(blob)
    # This variant offers the station's signed SRL, so the parent's unused
    # secure-area padding need not retain the stock SM64DS boot signature.
    # ENTRY uses this loader only before the resident story runtime installs.
    # Keep 0x02004100 free for the downloaded client's pre-crt0 descriptor stub.
    loader_address = 0x02004200
    trampoline = CAVE_END-8
    game['CoopOriginalEntryInit'] = trampoline
    loader, _ = link(ROOT/'mods/coop/bootstrap/heap_loader.cpp',root/'heap-loader',loader_address,
                     game,launcher,cc,ld,[f'COOP_BOOTSTRAP_FILE={ids[0]}'])
    if loader_address+len(loader)>0x02004800:
        raise ValueError('Heap loader exceeds the pre-crt0 padding')
    overlay = rom.loadArm9Overlays()[75]
    data = bytearray(overlay.data)
    entry = overlay_symbols['_ZN10dScEntry_c13InitResourcesEv']
    first = data[entry-overlay.ramAddress:entry-overlay.ramAddress+4]
    if first != bytes.fromhex('30402de9'):
        raise ValueError('Unexpected ENTRY prologue')
    data[trampoline-overlay.ramAddress:trampoline-overlay.ramAddress+8] = first+branch(trampoline+4,entry+4)
    data[entry-overlay.ramAddress:entry-overlay.ramAddress+4] = branch(entry,loader_address)
    replacement = None
    for prefix in range(0, min(len(data),0x4000),64):
        compressed = bytes(data[:prefix])+ndspy.codeCompression.compress(data[prefix:])
        if 0<=len(rom.files[overlay.fileID])-len(compressed)<=247:
            replacement=pad_blz(compressed,len(rom.files[overlay.fileID]),bytes(data));break
    if replacement is None:
        raise ValueError('Modified overlay cannot fit fixed extent')
    if args.handoff:
        client_report=json.loads((root/'game-client.json').read_text())
        if hashlib.sha256(package_path.read_bytes()).hexdigest()!=client_report['packageSha256']:
            raise ValueError('Handoff requires the verified game-client package')
        if hashlib.sha256(replacement).hexdigest()!=client_report['hostOverlay75Sha256']:
            raise ValueError('Parent overlay 75 differs from the client authentication table')
        if client_report['wirelessFilesystemHeader']!=filesystem_header.hex():
            raise ValueError('Client wireless filesystem extents differ from the parent header')
    output = bytearray(original)
    output+=b'\xff'*(fat-len(output))
    output+=original[old_fat:old_fat+old_fat_size]+bytes(len(ids)*8)
    struct.pack_into('<II',output,0x48,fat,fat_size)
    arm9_offset=struct.unpack_from('<I',original,0x20)[0]
    loader_offset=loader_address-rom.arm9RamAddress
    if ndspy.codeCompression.decompress(rom.arm9)[loader_offset:loader_offset+len(loader)]!=rom.arm9[loader_offset:loader_offset+len(loader)]:
        raise ValueError('Parent loader storage is not in the uncompressed ARM9 prefix')
    output[arm9_offset+loader_offset:arm9_offset+loader_offset+len(loader)]=loader
    struct.pack_into('<H',output,0x6c,_common.crc16(output[arm9_offset:arm9_offset+0x4000]))
    start,end = struct.unpack_from('<II',output,fat+overlay.fileID*8)
    output[start:end]=replacement
    assets = [blob,signed,menu,probe]
    for file_id,asset in zip(ids,assets):
        while len(output)%512:output.append(0xff)
        start=len(output)
        output+=asset
        struct.pack_into('<II',output,fat+file_id*8,start,len(output))
    used=len(output)
    capacity=max(0x20000,1<<(used-1).bit_length())
    output[0x14]=capacity.bit_length()-18
    struct.pack_into('<I',output,0x80,used)
    struct.pack_into('<H',output,0x15e,_common.crc16(output[:0x15e]))
    output+=b'\xff'*(capacity-len(output))
    checked=ndspy.rom.NintendoDSRom(output)
    changed_native=[i for i,data in enumerate(rom.files) if checked.files[i]!=data]
    if changed_native!=[overlay.fileID] or len(checked.files)!=len(rom.files)+len(ids):
        raise ValueError('Unexpected native file changes: '+str(changed_native))
    if output[0x40:0x60]!=filesystem_header:
        raise ValueError('Unexpected wireless filesystem extents')
    result=args.output or root/'sm64ds-haxxstation-host-experimental.nds'
    result.write_bytes(output)
    report={'purpose':'Signed Download Station first stage inside the SM64DS parent; second-stage service in progress',
            'output':str(result),'sha256':hashlib.sha256(output).hexdigest(),
            'package':str(package_path),
            'clients':args.clients,'nativeGameHandoff':args.handoff,
            'rearmMPAfterBoot':args.rearm_mp_after_boot,
            'serialSignedBoot':args.serial_boot,
            'restartStationParent':args.restart_station_parent,
            'closeEntryBeforeBoot':args.close_entry_before_boot,
            'fixedRadioChannel':args.channel,
            'fixedBeaconPeriodTu':args.beacon_period,
            'originalFileCount':len(rom.files),'preservedNativeArchives':True,
            'wirelessFilesystemHeader':filesystem_header.hex(),
            'files':dict(zip(('bootstrap','signedClient','menu','unsignedPayload'),ids)),
            'loaderAddress':hex(loader_address),'loaderBytes':len(loader),'bodyBytes':len(body),'fixups':len(fixups),
            'bodyLinkBase':hex(base),'bootstrapEntryOffset':exports['CoopBootstrapInit']-base,
            'bootstrapDiagnostics':{
                'tickOffset':exports['CoopBootstrapMBTick']-base,
                'stationAssociationsOffset':exports['stationAssociations']-base,
                'bootAcceptedOffset':exports['bootAccepted']-base,
                'bootControlsOffset':exports['bootControls']-base},
            'signedClientSha256':hashlib.sha256(signed).hexdigest()}
    if args.restart_station_parent:
        report['bootstrapDiagnostics']['stationRestartedOffset']=exports['stationRestarted']-base
    story_report=json.loads((ROOT/'build/coop/build.json').read_text())
    report['experimentalHostSaveSlot']=story_report.get('experimentalHostSaveSlot')
    report['runtimeModule']=story_report['runtimeModule']
    report_path = result.with_suffix('.json') if args.output else root/'host.json'
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
