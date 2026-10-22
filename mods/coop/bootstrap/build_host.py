#!/usr/bin/env python3
"""Experimental native SM64DS parent with a signed Download Station first stage.

The original hook prototype remains a separate build. This variant appends its
bootstrap assets into the four replaced VS archives; all story assets remain.
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
    parser.add_argument('--package', type=Path,
                        help='HaxxStation package containing demomenu and rom0000d; defaults to the boot probe')
    parser.add_argument('--output', type=Path,
                        help='Output ROM path; defaults to the experimental native host')
    args = parser.parse_args()
    root = ROOT/'build/coop/bootstrap'
    root.mkdir(parents=True, exist_ok=True)
    original = (ROOT/'build/coop/sm64ds-coop-experimental.nds').read_bytes()
    rom = ndspy.rom.NintendoDSRom(original)
    station = ndspy.rom.NintendoDSRom.fromFile('/workspace/inputs/download-station.nds')
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
    # Raw NitroFS file IDs of the four VS-only NARCs, now unused by story mode.
    ids = [rom.filenames.idOf('ARCHIVE/vs'+str(i)+'.narc') for i in range(1,5)]
    base = 0x02200000
    game['CoopOriginalMBTick'] = base+0x1800
    game['CoopOriginalMBReceive'] = base+0x1808
    boot_size = sum(struct.unpack_from('<I',signed,p)[0] for p in (0x2c,0x3c))+0x1e8
    define = [f'COOP_SIGNED_BOOT_FILE={ids[1]}', f'COOP_SIGNED_BOOT_SIZE={boot_size}',
              f'COOP_MENU_FILE={ids[2]}', f'COOP_MENU_SIZE={len(menu)}',
              f'COOP_PAYLOAD_FILE={ids[3]}', f'COOP_PAYLOAD_SIZE={len(probe)}']
    body, exports = link(ROOT/'mods/coop/bootstrap/host.cpp', root/'host', base, game, launcher, cc, ld, define)
    game['CoopOriginalMBTick'] = base+len(body)
    game['CoopOriginalMBReceive'] = base+len(body)+8
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
    fixups = relocations(root/'host.o',root/'host.elf',base,body)
    fixups.extend([0x80000000 | (len(body)-12),0x80000000 | (len(body)-4)])
    blob = pack(base,body,exports['CoopBootstrapInit'],sorted(fixups))
    (root/'host-relocatable.bin').write_bytes(blob)
    old_report = json.loads((ROOT/'build/coop/build.json').read_text())
    cave = next(p for p in old_report['patches'] if 'installerBytes' in p)
    loader_address = CAVE_START+((cave['installerBytes']+3)&~3)+cave['runtimeBytes']
    trampoline = CAVE_END-8
    game['CoopOriginalEntryInit'] = trampoline
    loader, _ = link(ROOT/'mods/coop/bootstrap/heap_loader.cpp',root/'heap-loader',loader_address,
                     game,launcher,cc,ld,[f'COOP_BOOTSTRAP_FILE={ids[0]}'])
    if loader_address+len(loader)>trampoline:
        raise ValueError(f'Heap loader exceeds cave: {len(loader)} bytes, {trampoline-loader_address} available')
    overlay = rom.loadArm9Overlays()[75]
    data = bytearray(overlay.data)
    off = loader_address-overlay.ramAddress
    data[off:off+len(loader)] = loader
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
    output = bytearray(original)
    fat = struct.unpack_from('<I',output,0x48)[0]
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
    result=args.output or root/'sm64ds-haxxstation-host-experimental.nds'
    result.write_bytes(output)
    report={'purpose':'Signed Download Station first stage inside the SM64DS parent; second-stage service in progress',
            'output':str(result),'sha256':hashlib.sha256(output).hexdigest(),
            'package':str(package_path),
            'files':dict(zip(('bootstrap','signedClient','menu','unsignedPayload'),ids)),
            'loaderAddress':hex(loader_address),'loaderBytes':len(loader),'bodyBytes':len(body),'fixups':len(fixups),
            'bodyLinkBase':hex(base),'bootstrapEntryOffset':exports['CoopBootstrapInit']-base,
            'signedClientSha256':hashlib.sha256(signed).hexdigest()}
    report_path = result.with_suffix('.json') if args.output else root/'host.json'
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
