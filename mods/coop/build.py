#!/usr/bin/env python3
"""Compile co-op hooks into the EU lobby overlay, retaining signed boot images.

ARM9, ARM7 and native file extents are retained. A small lobby loader installs
a relocatable runtime from an appended file into ROOT. Campaign acceptance
remains experimental.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess

import ndspy.codeCompression
import ndspy.rom
from elftools.elf.elffile import ELFFile

from audit_download_play import audit
from bootstrap.relocatable import pack, relocations
from ndspy import _common

REPO = Path(__file__).resolve().parents[2]
ROM_SHA256 = 'ce5829aaa79f06c67140ed1f45cbca738b0a9d0180538c8c1498472d859db032'
COMPILER_SHA256 = 'c6aafc210c78e91b123e8e949b8e26faa76849225b9f639780fcc9db6cdff0b7'
LINKER_SHA256 = 'eada466d4f0c309fbcf061ff5791a2c98a92d8b0e2364c53a0a9d0fe42100a7f'
PAYLOAD_ADDRESS = 0x02200000
# Result score calculation and result UI initialization; never ENTRY startup.
CAVE_START, CAVE_END = 0x021165B0, 0x02116AD4
SAVE_CURRENT = '_ZN8SaveData15SaveCurrentFileEv'
HOOKS = [('_ZN10dScEntry_c10StartMatchEv', 'CoopStartMatch'),
         ('_ZN10dScEntry_c19LoadCourseResourcesEi', 'CoopLoadCourseResources')]


def symbols(path):
    return {m[1]: int(m[2], 16) for line in path.read_text().splitlines()
            if (m := re.match(r'(\S+)\s+.*\baddr:(0x[0-9a-fA-F]+)', line))}


def branch(source, target):
    offset = target - source - 8
    if offset % 4 or not -(1 << 25) <= offset < (1 << 25):
        raise ValueError('ARM hook target is not reachable')
    return struct.pack('<I', 0xEA000000 | ((offset >> 2) & 0xFFFFFF))


def run(command):
    subprocess.run([str(x) for x in command], cwd=REPO, check=True)


def link(source, prefix, address, game_symbols, launcher, cc, ld, defines=()):
    obj, elf_path = prefix.with_suffix('.o'), prefix.with_suffix('.elf')
    run([*launcher, cc, '-O4,p', '-enum', 'int', '-lang', 'c++', '-Cpp_exceptions', 'off',
         '-char', 'signed', '-interworking', '-proc', 'arm946e', '-gccext,on', '-msgstyle', 'gcc',
         *['-D' + d for d in defines], '-i', REPO / 'include', '-c', source, '-o', obj])
    with obj.open('rb') as f:
        elf = ELFFile(f)
        unresolved = sorted({s.name for s in elf.get_section_by_name('.symtab').iter_symbols()
                             if s.name and s['st_shndx'] == 'SHN_UNDEF'})
        defined = {s.name for s in elf.get_section_by_name('.symtab').iter_symbols()
                   if s.name and isinstance(s['st_shndx'], int)
                   and s['st_info']['type'] in ('STT_FUNC', 'STT_OBJECT')}
    missing = [name for name in unresolved if name not in game_symbols]
    if missing:
        raise RuntimeError(f'Unresolved game symbols: {missing}')
    lcf = prefix.with_suffix('.lcf')
    text = f'MEMORY {{ CODE : ORIGIN = 0x{address:08x} > {prefix.name}.bin }}\nSECTIONS {{\n'
    text += '\n'.join(f'{name} = 0x{game_symbols[name]:08x};' for name in unresolved) + '\n'
    text += ' .payload : { ALIGNALL(4); '
    text += ' '.join(f'{obj.name}({s})' for s in ('.text', '.init', '.rodata', '.data', '.bss'))
    text += ' } > CODE }\n'
    lcf.write_text(text)
    run([*launcher, ld, '-proc', 'arm946e', '-nostdlib', '-interworking', '-nodead', '-m',
         next(n for n in sorted(defined) if n.startswith('Coop')), '-msgstyle', 'gcc', obj, lcf, '-o', elf_path])
    elf = ELFFile(io.BytesIO(elf_path.read_bytes()))
    emitted = {s.name: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    sizes = {s.name: s['st_size'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    # mwldarm's MEMORY regions are external files, not SHF_ALLOC ELF sections.
    payload = bytearray(prefix.with_suffix('.bin').read_bytes())
    end = max([address + len(payload)] + [emitted[n] + sizes[n] for n in defined])
    payload.extend(bytes(end - address - len(payload)))
    if not payload or end > address + 0x2000:
        raise RuntimeError('Invalid linked payload span')
    return payload, emitted


def pad_blz(compressed, size, expected):
    """Pad the BLZ header to preserve the FAT extent and compressed-size field."""
    delta = size - len(compressed)
    packed, extra = struct.unpack_from('<II', compressed, len(compressed) - 8)
    header_len, encoded_len = packed >> 24, packed & 0xFFFFFF
    if delta < 0 or header_len + delta > 255 or extra < delta:
        raise RuntimeError(f'Cannot retain overlay size: compressed={len(compressed)}, original={size}, padding={delta}')
    result = compressed[:-8] + b'\xff' * delta
    result += struct.pack('<II', (header_len + delta) << 24 | (encoded_len + delta), extra - delta)
    if ndspy.codeCompression.decompress(result) != expected:
        raise RuntimeError('Padded overlay failed decompression round trip')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--baseline', action='store_true', help='Copy the verified retail control')
    parser.add_argument('--save-slot',choices=('A','B','C'),
                        help='Experimental: load and save this host adventure slot; default keeps progress in RAM')
    args = parser.parse_args()
    original = args.rom.read_bytes()
    if hashlib.sha256(original).hexdigest() != ROM_SHA256:
        parser.error('Expected verified Europe revision-0 ROM; other revisions are unsupported')
    root = REPO / 'build/coop'
    root.mkdir(parents=True, exist_ok=True)
    output_data, patches, ram_hooks = bytearray(original), [], []
    module_report = None
    if not args.baseline:
        launcher = shlex.split(os.environ.get('MWCCARM_LAUNCHER', ''))
        if os.name != 'nt' and not launcher:
            parser.error('Set MWCCARM_LAUNCHER (source /workspace/setup/activate.sh)')
        cc = REPO / 'tools/mwccarm/2004/b56/mwccarm.exe'
        ld = REPO / 'tools/mwccarm/1.2/sp2p3/mwldarm.exe'
        for tool, digest in [(cc, COMPILER_SHA256), (ld, LINKER_SHA256)]:
            if hashlib.sha256(tool.read_bytes()).hexdigest() != digest:
                raise RuntimeError(f'Pinned tool checksum mismatch: {tool}')
        game = symbols(REPO / 'config/arm9/symbols.txt')
        ov_symbols = symbols(REPO / 'config/arm9/overlays/ov075/symbols.txt')
        rom = ndspy.rom.NintendoDSRom(original)
        arm9 = ndspy.codeCompression.decompress(rom.arm9)
        overlay = rom.loadArm9Overlays()[75]
        player_overlay = rom.loadArm9Overlays()[2]
        for address in (0x020c4364, 0x020c4b34):
            offset = address-player_overlay.ramAddress
            if player_overlay.data[offset:offset+8] != struct.pack('<2I',0xe5900154,0xe2100902):
                raise RuntimeError('Unexpected native camera-completion read')
        for address in (0x020e3ae8, 0x020e3c88):
            offset = address-player_overlay.ramAddress
            if player_overlay.data[offset:offset+8] != struct.pack('<2I',0xe5d00000,0xe3500001):
                raise RuntimeError('Unexpected native Yoshi palette gate')
        if struct.unpack_from('<I', arm9, 0x02004180-rom.arm9RamAddress)[0] == 0x31504f43:
            raise RuntimeError('Retail prefix overlaps the runtime-cache marker')
        trampolines = [
            ('CoopOriginalLoadLevelOverlays', game['_Z17LoadLevelOverlaysi'], bytes.fromhex('30402de9')),
            ('CoopOriginalEntryCleanup', ov_symbols['_ZN10dScEntry_c16CleanupResourcesEv'], bytes.fromhex('00402de9')),
            ('CoopOriginalStageInit', game['_ZN10dScStage_c13InitResourcesEv'], bytes.fromhex('f04f2de9')),
            ('CoopOriginalSceneBefore', game['_ZN8dScene_c14BeforeBehaviorEv'], bytes.fromhex('10402de9')),
            ('CoopOriginalActorBefore', game['_ZN8dActor_c14BeforeBehaviorEv'], bytes.fromhex('10402de9')),
            ('CoopOriginalReadFile', game['func_0205d688'], bytes.fromhex('f0402de9')),
            ('CoopOriginalMessageUpdate', game['_ZN7Message6UpdateEv'], bytes.fromhex('70402de9')),
            ('CoopOriginalKillPlayer', game['KillPlayer'], bytes.fromhex('00402de9')),
            ('CoopOriginalHitDeathPlane', game['HitDeathPlane'], bytes.fromhex('00402de9')),
            ('CoopOriginalLoadEntrances', 0x020fe6c8, bytes.fromhex('f04f2de9'))]
        imports = dict(game, **{name:PAYLOAD_ADDRESS+0x1800+i*8
                               for i,(name,_,_) in enumerate(trampolines)})
        defines=[f'COOP_SAVE_SLOT={ord(args.save_slot)-ord("A") if args.save_slot else -1}']
        runtime, emitted = link(REPO/'mods/coop/runtime.cpp',root/'runtime',PAYLOAD_ADDRESS,imports,launcher,cc,ld,defines)
        body_size = len(runtime)
        imports.update({name:PAYLOAD_ADDRESS+body_size+i*8 for i,(name,_,_) in enumerate(trampolines)})
        runtime, emitted = link(REPO/'mods/coop/runtime.cpp',root/'runtime',PAYLOAD_ADDRESS,imports,launcher,cc,ld,defines)
        if len(runtime)!=body_size:
            raise RuntimeError('Unstable runtime module size')
        for name,address,prologue in trampolines:
            if address == 0x020fe6c8:
                image,base = player_overlay.data,player_overlay.ramAddress
            else:
                image,base = (overlay.data,overlay.ramAddress) if address>=overlay.ramAddress else (arm9,rom.arm9RamAddress)
            if bytes(image[address-base:address-base+4])!=prologue:
                raise RuntimeError('Unexpected prologue for '+name)
            source=PAYLOAD_ADDRESS+len(runtime)
            runtime+=prologue+branch(source+4,address+4)
        after = game['_ZN8dScene_c13AfterBehaviorEj']-rom.arm9RamAddress
        if arm9[after:after+12]!=struct.pack('<3I',0xe59fc000,0xe12fff1c,game['_ZN7fBase_c13AfterBehaviorEj']):
            raise RuntimeError('Unexpected scene behavior completion wrapper')
        after = game['_ZN8dActor_c13AfterBehaviorEj']-rom.arm9RamAddress
        if arm9[after:after+12]!=struct.pack('<3I',0xe59fc000,0xe12fff1c,game['_ZN7fBase_c13AfterBehaviorEj']):
            raise RuntimeError('Unexpected actor behavior completion wrapper')
        before = game['_ZN8dScene_c19BeforeInitResourcesEv']-rom.arm9RamAddress
        if arm9[before:before+0x34] != struct.pack('<13I',
                0xe92d4000,0xe24dd004,0xeb000009,0xe3500000,0x028dd004,
                0x03a00000,0x08bd4000,0x012fff1e,0xeb00001a,0xe3a00001,
                0xe28dd004,0xe8bd4000,0xe12fff1e):
            raise RuntimeError('Unexpected scene initialization setup')
        after = game['_ZN8dScene_c18AfterInitResourcesEj']-rom.arm9RamAddress
        if arm9[after:after+12]!=struct.pack('<3I',0xe59fc000,0xe12fff1c,game['_ZN7dBase_c18AfterInitResourcesEj']):
            raise RuntimeError('Unexpected scene initialization completion wrapper')
        read = game['FS_ReadFile']-rom.arm9RamAddress
        if arm9[read:read+16]!=struct.pack('<4I',0xe59fc004,0xe3a03000,0xe12fff1c,game['func_0205d688']):
            raise RuntimeError('Unexpected synchronous file-reader wrapper')
        records=relocations(root/'runtime.o',root/'runtime.elf',PAYLOAD_ADDRESS,runtime)
        records.extend(0x80000000 | (body_size+i*8+4) for i in range(len(trampolines)))
        blob=pack(PAYLOAD_ADDRESS,runtime,emitted['CoopRuntimeDispatch'],sorted(records))
        (root/'runtime-relocatable.bin').write_bytes(blob)
        module_id=len(rom.files)
        installer,install_symbols=link(REPO/'mods/coop/install.cpp',root/'install',CAVE_START,game,launcher,cc,ld,
                                       [f'COOP_RUNTIME_FILE={module_id}'])
        if CAVE_START+len(installer)>CAVE_END-8:
            raise RuntimeError('Runtime loader exceeds reserved result-code span')
        data,base=bytearray(overlay.data),overlay.ramAddress
        data[CAVE_START-base:CAVE_END-base]=bytes(CAVE_END-CAVE_START)
        data[CAVE_START-base:CAVE_START-base+len(installer)]=installer
        for symbol,target in HOOKS:
            destination=install_symbols[{'CoopLoadCourseResources':'CoopInstallResources',
                                         'CoopStartMatch':'CoopInstallMatch'}[target]]
            address=ov_symbols[symbol]
            data[address-base:address-base+4]=branch(address,destination)
            patches.append({'symbol':symbol,'address':hex(address),'target':hex(destination)})
        expected=bytes(data)
        replacement=None
        for prefix in range(0,min(len(data),0x4000),64):
            compressed=expected[:prefix]+ndspy.codeCompression.compress(expected[prefix:])
            if 0<=len(rom.files[overlay.fileID])-len(compressed)<=247:
                replacement=pad_blz(compressed,len(rom.files[overlay.fileID]),expected)
                break
        if replacement is None:
            raise RuntimeError('No BLZ encoding fits the original overlay extent')
        old_fat,old_fat_size=struct.unpack_from('<II',original,0x48)
        if old_fat_size!=len(rom.files)*8:
            raise RuntimeError('Unexpected native FAT size')
        start,end=struct.unpack_from('<II',original,old_fat+overlay.fileID*8)
        output_data[start:end]=replacement
        fat=(len(output_data)+511)&~511
        output_data+=b'\xff'*(fat-len(output_data))
        output_data+=original[old_fat:old_fat+old_fat_size]+bytes(8)
        struct.pack_into('<II',output_data,0x48,fat,old_fat_size+8)
        output_data+=b'\xff'*((-len(output_data))%512)
        start=len(output_data)
        output_data+=blob
        struct.pack_into('<II',output_data,fat+module_id*8,start,len(output_data))
        used=len(output_data)
        capacity=max(0x20000,1<<(used-1).bit_length())
        output_data[0x14]=capacity.bit_length()-18
        struct.pack_into('<I',output_data,0x80,used)
        struct.pack_into('<H',output_data,0x15e,_common.crc16(output_data[:0x15e]))
        output_data+=b'\xff'*(capacity-len(output_data))
        checked=ndspy.rom.NintendoDSRom(output_data)
        if checked.arm9!=rom.arm9 or checked.arm7!=rom.arm7 or checked.arm9OverlayTable!=rom.arm9OverlayTable:
            raise RuntimeError('Native boot code or overlay table changed')
        if len(checked.files)!=len(rom.files)+1 or any(checked.files[i]!=f for i,f in enumerate(rom.files) if i!=overlay.fileID):
            raise RuntimeError('An unrelated native file changed')
        pairs=[(game[SAVE_CURRENT],'CoopSaveCurrentFile'),(game['_Z17LoadLevelOverlaysi'],'CoopLoadLevelOverlays'),
               (game['_ZN7Message6UpdateEv'],'CoopMessageUpdate'),
               (game['KillPlayer'],'CoopKillPlayer'),(game['HitDeathPlane'],'CoopHitDeathPlane'),
               (ov_symbols['_ZN10dScEntry_c16CleanupResourcesEv'],'CoopEntryCleanup'),
               (game['_ZN10dScStage_c13InitResourcesEv'],'CoopStageInit'),(game['func_0205d688'],'CoopReadFile'),
               (game['_ZN8dScene_c19BeforeInitResourcesEv'],'CoopSceneBeforeInit'),
               (game['_ZN8dScene_c18AfterInitResourcesEj'],'CoopSceneAfterInit'),
               (game['_ZN8dScene_c14BeforeBehaviorEv'],'CoopSceneBefore'),(game['_ZN8dScene_c13AfterBehaviorEj'],'CoopSceneAfter'),
               (game['_ZN8dActor_c14BeforeBehaviorEv'],'CoopActorBefore'),(game['_ZN8dActor_c13AfterBehaviorEj'],'CoopActorAfter')]
        ram_hooks=[{'address':hex(a),'targetOffset':hex(emitted[n]-PAYLOAD_ADDRESS),'symbol':n}for a,n in pairs]
        module_report={'fileID':module_id,'linkBase':hex(PAYLOAD_ADDRESS),'bodyBytes':len(runtime),
                       'entryOffset':hex(emitted['CoopRuntimeDispatch']-PAYLOAD_ADDRESS),'fixups':len(records),
                       'sha256':hashlib.sha256(blob).hexdigest(),'cacheAddress':'0x02004180'}
        module_report['diagnosticOffsets']={name:emitted[name]-PAYLOAD_ADDRESS
                                           for name in ('coopEnabled','coopSaveState','coopSavePage',
                                                        'coopSaveEpoch','coopStageLoading','coopMenuLoading',
                                                        'coopSceneInitializing','coopTitleLoading','coopFileWaiting',
                                                        'coopSessionEnded','coopDeathTriggered')}
        patches.append({'purpose':'ROOT module loader in unused VS result routines','address':hex(CAVE_START),
                        'size':CAVE_END-CAVE_START,'installerBytes':len(installer)})
    output=root/('baseline.nds' if args.baseline else 'sm64ds-coop-experimental.nds')
    output.write_bytes(output_data)
    report={'inputSha256':ROM_SHA256,'baseline':args.baseline,'output':str(output.relative_to(REPO)),
            'outputSha256':hashlib.sha256(output_data).hexdigest(),'romSize':len(output_data),
            'experimentalHostSaveSlot':args.save_slot,
            'bootImagesUnchanged':True,'nativeFileExtentsUnchanged':True,'patches':patches,
            'runtimeModule':module_report,'lateRamHooks':ram_hooks,
            'downloadPlayOverlayAuthentication':audit(output_data),
            'limitations':['Native Download Play rejects modified overlay 75: HMAC mismatch',
                           'Base image requires the separate HaxxStation bootstrap build for unsigned clients',
                           'Campaign completion not established',
                           'Host save protocol is experimental' if args.save_slot else 'Co-op saves remain in RAM',
                           'VS results replaced by the module loader']}
    (root/('baseline.json' if args.baseline else 'build.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
