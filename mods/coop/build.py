#!/usr/bin/env python3
"""Compile co-op hooks into the EU lobby overlay, retaining signed boot images.

All physical cartridge layout and metadata, ARM9 and ARM7 are retained. The
lobby installs the runtime into RAM. Campaign/Download Play remain experimental.
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

REPO = Path(__file__).resolve().parents[2]
ROM_SHA256 = 'ce5829aaa79f06c67140ed1f45cbca738b0a9d0180538c8c1498472d859db032'
COMPILER_SHA256 = 'c6aafc210c78e91b123e8e949b8e26faa76849225b9f639780fcc9db6cdff0b7'
LINKER_SHA256 = 'eada466d4f0c309fbcf061ff5791a2c98a92d8b0e2364c53a0a9d0fe42100a7f'
PAYLOAD_ADDRESS, PAYLOAD_END = 0x02004100, 0x02004800
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
    args = parser.parse_args()
    original = args.rom.read_bytes()
    if hashlib.sha256(original).hexdigest() != ROM_SHA256:
        parser.error('Expected verified Europe revision-0 ROM; other revisions are unsupported')
    root = REPO / 'build/coop'
    root.mkdir(parents=True, exist_ok=True)
    output_data, patches, ram_hooks = bytearray(original), [], []
    if not args.baseline:
        launcher = shlex.split(os.environ.get('MWCCARM_LAUNCHER', ''))
        if os.name != 'nt' and not launcher:
            parser.error('Set MWCCARM_LAUNCHER (source /workspace/setup/activate.sh)')
        cc = REPO / 'tools/mwccarm/2004/b56/mwccarm.exe'
        ld = REPO / 'tools/mwccarm/1.2/sp2p3/mwldarm.exe'
        for tool, digest in [(cc, COMPILER_SHA256), (ld, LINKER_SHA256)]:
            if hashlib.sha256(tool.read_bytes()).hexdigest() != digest:
                raise RuntimeError(f'Pinned tool checksum mismatch: {tool}')
        main_symbols = symbols(REPO / 'config/arm9/symbols.txt')
        ov_symbols = symbols(REPO / 'config/arm9/overlays/ov075/symbols.txt')
        runtime_symbols = dict(main_symbols, CoopOriginalLoadLevelOverlays=PAYLOAD_ADDRESS + 0x600,
                               CoopOriginalEntryCleanup=PAYLOAD_ADDRESS + 0x680)
        runtime, emitted = link(REPO / 'mods/coop/runtime.cpp', root / 'runtime', PAYLOAD_ADDRESS,
                                runtime_symbols, launcher, cc, ld)
        trampoline = PAYLOAD_ADDRESS + len(runtime)
        runtime_symbols['CoopOriginalLoadLevelOverlays'] = trampoline
        runtime_symbols['CoopOriginalEntryCleanup'] = trampoline + 8
        runtime, emitted = link(REPO / 'mods/coop/runtime.cpp', root / 'runtime', PAYLOAD_ADDRESS,
                                runtime_symbols, launcher, cc, ld)
        rom = ndspy.rom.NintendoDSRom(original)
        stock_arm9 = ndspy.codeCompression.decompress(rom.arm9)
        level_address = main_symbols['_Z17LoadLevelOverlaysi']
        prologue = stock_arm9[level_address-rom.arm9RamAddress:level_address-rom.arm9RamAddress+4]
        if prologue != bytes.fromhex('30402de9') or len(runtime) + PAYLOAD_ADDRESS != trampoline:
            raise RuntimeError('Unexpected level-loader prologue or unstable runtime size')
        runtime += prologue + branch(trampoline + 4, level_address + 4)
        cleanup_address = ov_symbols['_ZN10dScEntry_c16CleanupResourcesEv']
        stock_overlay = rom.loadArm9Overlays()[75]
        cleanup_start = cleanup_address - stock_overlay.ramAddress
        cleanup_prologue = bytes(stock_overlay.data[cleanup_start:cleanup_start+4])
        if cleanup_prologue != bytes.fromhex('00402de9'):
            raise RuntimeError('Unexpected ENTRY cleanup prologue')
        runtime += cleanup_prologue + branch(trampoline + 12, cleanup_address + 4)
        ram_hooks = [
            {'address': hex(main_symbols[SAVE_CURRENT]), 'target': hex(emitted['CoopSaveCurrentFile'])},
            {'address': hex(level_address), 'target': hex(emitted['CoopLoadLevelOverlays'])},
            {'address': hex(cleanup_address), 'target': hex(emitted['CoopEntryCleanup'])}]
        if PAYLOAD_ADDRESS + len(runtime) > PAYLOAD_END or len(runtime) % 4:
            raise RuntimeError('Resident code exceeds secure-area padding or is not word aligned')
        payload_limit = CAVE_END
        rom = ndspy.rom.NintendoDSRom(original)
        overlay = rom.loadArm9Overlays()[75]
        data, base = bytearray(overlay.data), overlay.ramAddress
        define = [f'COOP_PAYLOAD_SIZE={len(runtime)}',
                  f"COOP_SAVE_BRANCH=0x{int.from_bytes(branch(main_symbols[SAVE_CURRENT], emitted['CoopSaveCurrentFile']), 'little'):08x}",
                  f"COOP_LEVEL_BRANCH=0x{int.from_bytes(branch(level_address, emitted['CoopLoadLevelOverlays']), 'little'):08x}",
                  f'COOP_CLEANUP_ADDRESS=0x{cleanup_address:08x}',
                  f"COOP_CLEANUP_BRANCH=0x{int.from_bytes(branch(cleanup_address, emitted['CoopEntryCleanup']), 'little'):08x}"]
        installer_symbols = dict(main_symbols, CoopPayload=CAVE_START,
                                 CoopLoadCourseResources=emitted['CoopLoadCourseResources'],
                                 CoopStartMatch=emitted['CoopStartMatch'])
        installer, _ = link(REPO / 'mods/coop/install.cpp', root / 'install', CAVE_START,
                            installer_symbols, launcher, cc, ld, define)
        runtime_location = CAVE_START + ((len(installer) + 3) & ~3)
        installer_symbols['CoopPayload'] = runtime_location
        installed, install_symbols = link(REPO / 'mods/coop/install.cpp', root / 'install', CAVE_START,
                                           installer_symbols, launcher, cc, ld, define)
        if len(installed) != len(installer) or runtime_location + len(runtime) > payload_limit:
            raise RuntimeError('Installer/runtime exceed reserved result-code span')
        data[CAVE_START - base:CAVE_END - base] = bytes(CAVE_END - CAVE_START)
        data[CAVE_START - base:CAVE_START - base + len(installed)] = installed
        data[runtime_location - base:runtime_location - base + len(runtime)] = runtime
        for symbol, target in HOOKS:
            address = ov_symbols[symbol]
            destination = install_symbols[{'CoopLoadCourseResources': 'CoopInstallResources',
                                           'CoopStartMatch': 'CoopInstallMatch'}[target]]
            data[address - base:address - base + 4] = branch(address, destination)
            patches.append({'symbol': symbol, 'address': hex(address), 'target': hex(destination)})
        # BLZ supports an uncompressed prefix (also used by the stock ARM9).
        # Select its length so the remaining difference fits the <=255-byte BLZ
        # header. This preserves all decoded bytes and the original FAT extent.
        expected = bytes(data)
        file_size = len(rom.files[overlay.fileID])
        replacement = None
        for prefix in range(0, min(len(data), 0x4000), 64):
            compressed = expected[:prefix] + ndspy.codeCompression.compress(expected[prefix:])
            delta = file_size - len(compressed)
            if 0 <= delta <= 247:
                replacement = pad_blz(compressed, file_size, expected)
                break
        if replacement is None:
            raise RuntimeError('No BLZ encoding fits the original overlay extent')
        fat = struct.unpack_from('<I', original, 0x48)[0]
        start, end = struct.unpack_from('<II', original, fat + overlay.fileID * 8)
        if end - start != len(replacement):
            raise RuntimeError('Overlay FAT extent changed')
        output_data[start:end] = replacement
        patches.append({'purpose': 'installer in unused VS result routines', 'address': hex(CAVE_START),
                        'size': CAVE_END - CAVE_START, 'runtimeBytes': len(runtime), 'installerBytes': len(installed)})
        checked = ndspy.rom.NintendoDSRom(output_data)
        if checked.arm9 != rom.arm9 or checked.arm7 != rom.arm7 or output_data[:0x4000] != original[:0x4000]:
            raise RuntimeError('Signed boot images or cartridge header changed')
        if checked.arm9OverlayTable != rom.arm9OverlayTable:
            raise RuntimeError('Overlay table changed')
        if any(a != b for i, (a, b) in enumerate(zip(checked.files, rom.files)) if i != overlay.fileID):
            raise RuntimeError('An unrelated filesystem file changed')
    output = root / ('baseline.nds' if args.baseline else 'sm64ds-coop-experimental.nds')
    output.write_bytes(output_data)
    report = {'inputSha256': ROM_SHA256, 'baseline': args.baseline,
              'output': str(output.relative_to(REPO)), 'outputSha256': hashlib.sha256(output_data).hexdigest(),
              'romSize': len(output_data), 'bootImagesAndHeaderUnchanged': True, 'patches': patches,
              'lateRamHooks': ram_hooks,
              'downloadPlayOverlayAuthentication': audit(output_data),
              'limitations': ['Native Download Play rejects modified overlay 75: HMAC mismatch',
                              'HaxxStation boot and game-session handoff are not implemented',
                              'Campaign gameplay acceptance not established',
                              'Co-op saves remain in RAM', 'VS results replaced by runtime installer']}
    (root / ('baseline.json' if args.baseline else 'build.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
