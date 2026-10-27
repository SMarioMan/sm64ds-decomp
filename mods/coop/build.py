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
import ndspy.narc
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
    # The runtime is dynamically allocated in ROOT; the loader accepts 64 KiB.
    # Keep code/data below 37 KiB; the final module (including tables) is
    # checked separately against the loader's 64 KiB limit.
    if not payload or end > address + 0x9400:
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


def narc_member_index(rom, arm9, original):
    """Index immutable member extents without runtime metadata reads over WFS."""
    rows,extents=bytearray(),bytearray()
    fat=struct.unpack_from('<I',original,0x48)[0]
    for archive in range(13):
        record=0x0208ecf4-rom.arm9RamAddress+archive*20
        first,limit=struct.unpack_from('<HH',arm9,record+8)
        path=struct.unpack_from('<I',arm9,record+16)[0]-rom.arm9RamAddress
        name=bytes(arm9[path:arm9.index(0,path)]).decode().lstrip('/')
        file_id=rom.filenames.idOf(name)
        top,bottom=struct.unpack_from('<II',original,fat+file_id*8)
        data=bytes(rom.files[file_id])
        if len(data)!=bottom-top or data[:4]!=b'NARC':raise ValueError('Unexpected NARC extent')
        position,blocks=struct.unpack_from('<HH',data,12)
        members=None;image=None
        for _ in range(blocks):
            kind,size=struct.unpack_from('<4sI',data,position)
            if size<8 or position+size>len(data):raise ValueError('Invalid NARC block')
            if kind==b'BTAF':
                count=struct.unpack_from('<H',data,position+8)[0]
                members=[struct.unpack_from('<II',data,position+12+i*8) for i in range(count)]
            elif kind==b'GMIF':image=position+8
            position+=size
        if members is None or image is None or len(members)!=limit-first:
            raise ValueError('NARC table differs from native virtual file range')
        expected=ndspy.narc.NARC(data).files
        rows+=struct.pack('<HHIII',first,limit,file_id,top,13*16+len(extents))
        for i,(start,end) in enumerate(members):
            if data[image+start:image+end]!=expected[i]:raise ValueError('NARC member index mismatch')
            extents+=struct.pack('<II',image+start,image+end)
    return bytes(rows+extents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--baseline', action='store_true', help='Copy the verified retail control')
    parser.add_argument('--runtime-placement',choices=('root','prefix'),default='root',
                        help='Experimental prefix placement uses free RAM below retail ARM9')
    parser.add_argument('--save-slot',choices=('A','B','C'),
                        help='Experimental: load and save this host adventure slot; default keeps progress in RAM')
    parser.add_argument('--diagnostic-start-level',type=int,choices=range(1,52),
                        help='TEST ONLY: start in this native stage; does not validate campaign progression')
    parser.add_argument('--diagnostic-stage-cycle',action='store_true',
                        help='TEST ONLY: synchronized L+R+X requests the next native stage')
    parser.add_argument('--diagnostic-render-cost',action='store_true',
                        help='TEST ONLY: drain geometry to measure terrain/body/head polygon costs; changes timing')
    parser.add_argument('--diagnostic-player-cost',action='store_true',
                        help='TEST ONLY: elapsed SDK ticks for player behavior/models and stage rendering')
    parser.add_argument('--experimental-painting-math',action='store_true',
                        help='EXPERIMENTAL: reuse exact ripple-wave coefficients across mesh cells')
    parser.add_argument('--experimental-collision-plan',action='store_true',
                        help='EXPERIMENTAL: ordered spatial candidates with pressure/callback fallback')
    parser.add_argument('--experimental-collision-broadphase',action='store_true',
                        help='EXPERIMENTAL: conservative axis rejection before native cylinder distance')
    parser.add_argument('--experimental-persistent-animation-cache',action='store_true',
                        help='EXPERIMENTAL: retain immutable animation bytes across stage transitions')
    parser.add_argument('--experimental-lazy-animation-eviction',action='store_true',
                        help='EXPERIMENTAL: preserve cached bytes during exact virtual capacity queries')
    parser.add_argument('--experimental-animation-cache',action='store_true',
                        help='EXPERIMENTAL: expendable ROOT cache for compressed animation reads')
    args = parser.parse_args()
    if args.baseline and args.diagnostic_start_level is not None:
        parser.error('--baseline cannot select a diagnostic stage')
    if args.diagnostic_stage_cycle and args.diagnostic_start_level is None:
        parser.error('--diagnostic-stage-cycle requires --diagnostic-start-level')
    if args.baseline and (args.diagnostic_render_cost or args.diagnostic_player_cost or args.experimental_animation_cache or args.experimental_collision_broadphase or args.experimental_collision_plan or args.experimental_painting_math):
        parser.error('--baseline cannot enable render diagnostics')
    if args.experimental_persistent_animation_cache and not args.experimental_animation_cache:
        parser.error('Persistent animation caching requires --experimental-animation-cache')
    if args.experimental_lazy_animation_eviction and not args.experimental_animation_cache:
        parser.error('Lazy animation eviction requires --experimental-animation-cache')
    if args.experimental_collision_plan and (not args.experimental_animation_cache or args.experimental_collision_broadphase):
        parser.error('Collision plans require --experimental-animation-cache and exclude --experimental-collision-broadphase')
    if args.diagnostic_player_cost and args.diagnostic_render_cost:
        parser.error('Elapsed timing cannot be combined with FIFO-draining geometry diagnostics')
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
        for address in (0x02010ba4,0x02010bf0):
            offset=address-rom.arm9RamAddress
            if arm9[offset:offset+8]!=struct.pack('<II',0xe59000b0,0xe2100010):
                raise RuntimeError(f'Unexpected native drop-shadow flags read at {address:#x}')
        overlay = rom.loadArm9Overlays()[75]
        player_overlay = rom.loadArm9Overlays()[2]
        painting_signature=bytes.fromhex('1800a0e3910000e07057fceba00184e5')
        painting_matches=[]
        for overlay_id,candidate in rom.loadArm9Overlays().items():
            offset=0x02126e08-candidate.ramAddress
            if offset>=0 and candidate.data[offset:offset+16]==painting_signature:
                painting_matches.append(overlay_id)
        if painting_matches!=[80]:
            raise RuntimeError('Painting mesh hook is not unique to native overlay80')

        for address in (0x020c4364, 0x020c4b34):
            offset = address-player_overlay.ramAddress
            if player_overlay.data[offset:offset+8] != struct.pack('<2I',0xe5900154,0xe2100902):
                raise RuntimeError('Unexpected native camera-completion read')
        if arm9[0x02024d40-rom.arm9RamAddress:0x02024d4c-rom.arm9RamAddress]!=bytes.fromhex('549199e5019a19e26b00000a'):
            raise RuntimeError('Unexpected native per-player camera-input guard')
        cannon=0x020def88-player_overlay.ramAddress
        if player_overlay.data[cannon:cannon+12]!=bytes.fromhex('be07d0e10060a0e31919a0e3'):
            raise RuntimeError('Unexpected native cannon pitch read')
        owl=0x020df6a0-player_overlay.ramAddress
        if player_overlay.data[owl:owl+8]!=bytes.fromhex('540190e5020910e2'):
            raise RuntimeError('Unexpected native owl camera-completion read')
        for address in (0x020e3ae8, 0x020e3c88):
            offset = address-player_overlay.ramAddress
            if player_overlay.data[offset:offset+8] != struct.pack('<2I',0xe5d00000,0xe3500001):
                raise RuntimeError('Unexpected native Yoshi palette gate')
        if struct.unpack_from('<I', arm9, 0x02004180-rom.arm9RamAddress)[0] == 0x31504f43:
            raise RuntimeError('Retail prefix overlaps the runtime-cache marker')
        trampolines = [
            ('CoopOriginalMinimapBehavior',0x020fa690,bytes.fromhex('f04f2de9')),
            ('CoopOriginalMinimapRender',0x020f9e98,bytes.fromhex('f04f2de9')),
            ('CoopOriginalLoadLevelOverlays', game['_Z17LoadLevelOverlaysi'], bytes.fromhex('30402de9')),
            ('CoopOriginalEntryCleanup', ov_symbols['_ZN10dScEntry_c16CleanupResourcesEv'], bytes.fromhex('00402de9')),
            ('CoopOriginalStageInit', game['_ZN10dScStage_c13InitResourcesEv'], bytes.fromhex('f04f2de9')),
            ('CoopOriginalSceneBefore', game['_ZN8dScene_c14BeforeBehaviorEv'], bytes.fromhex('10402de9')),
            ('CoopOriginalActorBefore', game['_ZN8dActor_c14BeforeBehaviorEv'], bytes.fromhex('10402de9')),
            ('CoopOriginalActorBeforeInit',game['_ZN8dActor_c19BeforeInitResourcesEv'],bytes.fromhex('10402de9')),
            ('CoopOriginalReadFile', game['func_0205d688'], bytes.fromhex('f0402de9')),
            ('CoopOriginalMessageUpdate', game['_ZN7Message6UpdateEv'], bytes.fromhex('70402de9')),
            ('CoopOriginalKillPlayer', game['KillPlayer'], bytes.fromhex('00402de9')),
            ('CoopOriginalHitDeathPlane', game['HitDeathPlane'], bytes.fromhex('00402de9')),
            ('CoopOriginalLoadEntrances', 0x020fe6c8, bytes.fromhex('f04f2de9')),
            ('CoopOriginalStarTutorial',0x020c6e14,bytes.fromhex('30402de9')),
            ('CoopOriginalCourseTutorial',0x020c44c4,bytes.fromhex('30402de9')),
            ('CoopOriginalLevelEnterInit',0x020c7838,bytes.fromhex('f0402de9')),
            ('CoopOriginalGiveCoins',game['GiveCoins'],bytes.fromhex('00402de9')),
            ('CoopOriginalTrimModel',game['func_02017060'],bytes.fromhex('30402de9')),
            ('CoopOriginalResolveFile',game['func_020186c0'],bytes.fromhex('70402de9')),
            ('CoopOriginalOpenFile',game['func_020185c0'],bytes.fromhex('f0412de9')),
            ('CoopOriginalLoadDiskFile',game['func_0201834c'],bytes.fromhex('f0412de9')),
            ('CoopOriginalWirelessReset',game['func_02062200'],bytes.fromhex('10402de9')),
            ('CoopOriginalConnectionUpdate',game['func_02030e4c'],bytes.fromhex('00402de9')),
            ('CoopOriginalLoadSkybox',game['_ZN10dScStage_c10LoadSkyboxEv'],bytes.fromhex('30402de9')),
            ('CoopOriginalCameraFar',game['func_0200d0ac'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraNear',game['func_0200d064'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraBehind',game['_ZN9dCamera_c14GoBehindPlayerEj'],bytes.fromhex('10402de9')),
            ('CoopOriginalCameraFirstPerson',game['func_0200d7e0'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraNormal',game['func_0200d81c'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraLookTarget',game['func_0200d3f8'],bytes.fromhex('00402de9')),
            ('CoopOriginalPlayerHeadLook',0x020cae10,bytes.fromhex('f0412de9'))]
        trampolines += [
            ('CoopOriginalCameraModeD10c',game['func_0200d10c'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD148',game['func_0200d148'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD438',game['func_0200d438'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD474',game['func_0200d474'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD508',game['func_0200d508'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD544',game['func_0200d544'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD580',game['func_0200d580'],bytes.fromhex('10402de9')),
            ('CoopOriginalCameraModeD5c0',game['func_0200d5c0'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD5fc',game['func_0200d5fc'],bytes.fromhex('10402de9')),
            ('CoopOriginalCameraModeD63c',game['func_0200d63c'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD678',game['func_0200d678'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD6b4',game['func_0200d6b4'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD6f0',game['func_0200d6f0'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD72c',game['func_0200d72c'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD768',game['func_0200d768'],bytes.fromhex('00402de9')),
            ('CoopOriginalCameraModeD7a4',game['func_0200d7a4'],bytes.fromhex('00402de9')),
        ]
        fov=game['func_0200ca14']-rom.arm9RamAddress
        if arm9[fov:fov+60]!=bytes.fromhex('30309fe50030d3e5030051e11eff2f11000052e3551f8002000091050208800300008105551f80120000911501088013000081151eff2fe150f20902'):
            raise RuntimeError('Unexpected native player camera FOV helper')
        if args.experimental_painting_math:
            trampolines += [('CoopOriginalPaintingHeight',0x02125bb0,bytes.fromhex('f0402de9'))]
        if args.experimental_animation_cache:
            trampolines += [('CoopOriginalHeapAllocate',game['_ZN5mHeap6Heap_t8AllocateEji'],bytes.fromhex('30402de9')),
                            ('CoopOriginalStageCleanup',game['_ZN10dScStage_c16CleanupResourcesEv'],bytes.fromhex('f0412de9')),
                            ('CoopOriginalHeapReallocate',game['_ZN5mHeap6Heap_t10ReallocateEPvj'],bytes.fromhex('00402de9'))]
            for address,expected in ((0x0203c5d0,'08c09fe5140090e50410a0e31cff2fe1f8e00402'),
                                     (0x0203c5f8,'08c09fe5140090e50410a0e31cff2fe1f8e00402'),
                                     (0x0203c5ac,'04c09fe5140090e51cff2fe180e10402')):
                offset=address-rom.arm9RamAddress
                if arm9[offset:offset+len(bytes.fromhex(expected))]!=bytes.fromhex(expected):
                    raise RuntimeError('Unexpected expanding-heap capacity query')
        if args.diagnostic_player_cost:
            trampolines += [('CoopOriginalStageRender',game['_ZN10dScStage_c6RenderEv'],bytes.fromhex('f0402de9'))]
        if args.experimental_collision_broadphase:
            # Pin the working-register/collider layout, original vector call,
            # coincident case and radius-overlap comparison as one block.
            begin=0x02014b90-rom.arm9RamAddress
            expected=bytes.fromhex('002090e5001099e5011042e008108de5082090e5081099e508008de2011042e010108de5')
            expected+=branch(0x02014bb4,game['Vec3_HorzLen'])[:3]+b'\xeb'
            expected+=bytes.fromhex('0070b0e104709d05001094e50700a00108008d05040098e5042091e5000082e0076040e0000056e3c80000da')
            if arm9[begin:begin+len(expected)]!=expected:
                raise RuntimeError('Unexpected native cylinder pair distance/overlap block')
        if args.experimental_collision_plan:
            for address,expected in ((0x0203c6bc,'04c09fe5140090e51cff2fe170e30402'),
                                     (0x0203c568,'04c09fe5140090e51cff2fe1e8e10402'),
                                     (0x02014b0c,'000094e51c2098e5183090e51c1090e5180098e5'),
                                     (0x02014f14,'000094e52c1090e5285080e5000094e5000051e3')):
                offset=address-rom.arm9RamAddress
                if arm9[offset:offset+len(bytes.fromhex(expected))]!=bytes.fromhex(expected):
                    raise RuntimeError('Unexpected native collision/heap plan site')
            for address,target in ((0x0202ba14,game['_ZN5dCc_c7ProcessEv']),
                                   (0x02014d0c,game['func_02014f44']),(0x02014dcc,game['func_02014f44'])):
                offset=address-rom.arm9RamAddress
                if arm9[offset:offset+4]!=branch(address,target)[:3]+b'\xeb':
                    raise RuntimeError('Unexpected native collision plan callback')
        imports = dict(game, **{name:PAYLOAD_ADDRESS+0x1800+i*8
                               for i,(name,_,_) in enumerate(trampolines)})
        if args.experimental_painting_math:
            painting_image=rom.loadArm9Overlays()[80]
            address=0x02125cf0;offset=address-painting_image.ramAddress
            if painting_image.data[offset:offset+4]!=branch(address,0x01ffabe4)[:3]+b'\xeb':
                raise RuntimeError('Unexpected native painting signed divider call')
            imports['CoopPaintingDivide']=0x01ffabe4
        if args.experimental_collision_plan:
            imports.update(CoopCollisionPairContinue=0x02014b10,CoopCollisionPairDone=0x02014f14)
        imports['coopNarcIndex']=PAYLOAD_ADDRESS+0x1800
        narc_index=narc_member_index(rom,arm9,original)
        animation_mask=b'';animation_direct_index=b'';direct_animations=[]
        if args.experimental_animation_cache:
            common=ndspy.narc.NARC(rom.files[rom.filenames.idOf('ARCHIVE/arc0.narc')])
            if struct.unpack_from('<HH',narc_index)!=(0x8000,0x8000+len(common.files)):
                raise RuntimeError('Unexpected common archive virtual range')
            mask=bytearray((len(common.files)+7)//8)
            for member in range(len(common.files)):
                name=common.filenames.filenameOf(member)
                if name and name.startswith('data/player/') and name.endswith('.bca'):
                    mask[member//8]|=1<<(member%8)
            if not any(mask):raise RuntimeError('No verified player animations')
            animation_mask=bytes(mask)+bytes((-len(mask))%4)
            fat=struct.unpack_from('<I',original,0x48)[0]
            for file_id,data in enumerate(rom.files):
                name=rom.filenames.filenameOf(file_id)
                if not (name and name.startswith('data/player/') and name.endswith('.bca') and
                        8<=len(data)<=16384 and data[:5]==b'LZ77\x10'):continue
                top,bottom=struct.unpack_from('<II',original,fat+file_id*8)
                if bottom-top!=len(data) or original[top:bottom]!=data:
                    raise RuntimeError('Unexpected direct player animation extent')
                direct_animations.append((top,len(data)))
            direct_animations.sort()
            if not direct_animations:raise RuntimeError('No verified direct player animations')
            animation_direct_index=struct.pack('<I',len(direct_animations))+b''.join(
                struct.pack('<II',top,size) for top,size in direct_animations)
            imports['coopAnimationCacheMask']=imports['coopNarcIndex']+len(narc_index)
            imports['coopAnimationDirectIndex']=imports['coopAnimationCacheMask']+len(animation_mask)
        defines=[f'COOP_SAVE_SLOT={ord(args.save_slot)-ord("A") if args.save_slot else -1}']
        if args.experimental_painting_math:defines.append('COOP_EXPERIMENTAL_PAINTING_MATH=1')
        if args.experimental_animation_cache:
            defines.append('COOP_EXPERIMENTAL_ANIMATION_CACHE=1')
        if args.experimental_persistent_animation_cache:
            defines.append('COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE=1')
        if args.experimental_lazy_animation_eviction:
            defines.append('COOP_EXPERIMENTAL_LAZY_ANIMATION_EVICTION=1')
        if args.diagnostic_start_level is not None:
            defines.append(f'COOP_DIAGNOSTIC_START_LEVEL={args.diagnostic_start_level}')
        if args.diagnostic_stage_cycle:
            defines.append('COOP_DIAGNOSTIC_STAGE_CYCLE=1')
        if args.experimental_collision_plan:
            defines.append('COOP_EXPERIMENTAL_COLLISION_PLAN=1')
        if args.experimental_collision_broadphase:
            defines.append('COOP_EXPERIMENTAL_COLLISION_BROADPHASE=1')
        if args.diagnostic_player_cost:
            defines.append('COOP_DIAGNOSTIC_PLAYER_COST=1')
        if args.diagnostic_player_cost:
            for address,target in ((0x0202b99c,game['_ZN17dExtShadowModel_c9RenderAllEv']),
                                   (0x0202ba14,game['_ZN5dCc_c7ProcessEv'])):
                offset=address-rom.arm9RamAddress
                if arm9[offset:offset+4]!=branch(address,target)[:3]+b'\xeb':
                    raise RuntimeError('Unexpected native stage-cost callsite')
        if args.diagnostic_render_cost or args.diagnostic_player_cost:
            if args.diagnostic_render_cost:defines.append('COOP_DIAGNOSTIC_RENDER_COST=1')
            for address,target,data,base in (
                    (0x0202b998,game['_ZN10dScStage_c11RenderModelEv'],arm9,rom.arm9RamAddress),
                    (0x0202b9a4,game['_ZN10dScStage_c22RenderModelTransparentEv'],arm9,rom.arm9RamAddress),
                    (0x020e3b4c,game['_ZN17dExtSimpleModel_c6RenderEPK7Vector3'],player_overlay.data,player_overlay.ramAddress),
                    (0x020e3cfc,game['_ZN17dExtSimpleModel_c6RenderEPK7Vector3'],player_overlay.data,player_overlay.ramAddress)):
                if data[address-base:address-base+4]!=branch(address,target)[:3]+b'\xeb':
                    raise RuntimeError(f'Unexpected native render diagnostic call at {address:#x}')
        runtime, emitted = link(REPO/'mods/coop/runtime.cpp',root/'runtime',PAYLOAD_ADDRESS,imports,launcher,cc,ld,defines)
        body_size = len(runtime)
        imports.update({name:PAYLOAD_ADDRESS+body_size+i*8 for i,(name,_,_) in enumerate(trampolines)})
        imports['coopNarcIndex']=PAYLOAD_ADDRESS+body_size+len(trampolines)*8
        if args.experimental_animation_cache:
            imports['coopAnimationCacheMask']=imports['coopNarcIndex']+len(narc_index)
            imports['coopAnimationDirectIndex']=imports['coopAnimationCacheMask']+len(animation_mask)
        runtime, emitted = link(REPO/'mods/coop/runtime.cpp',root/'runtime',PAYLOAD_ADDRESS,imports,launcher,cc,ld,defines)
        if len(runtime)!=body_size:
            raise RuntimeError('Unstable runtime module size')
        for name,address,prologue in trampolines:
            if name=='CoopOriginalPaintingHeight':
                image,base=rom.loadArm9Overlays()[80].data,rom.loadArm9Overlays()[80].ramAddress
            elif player_overlay.ramAddress<=address<player_overlay.ramAddress+len(player_overlay.data):
                image,base = player_overlay.data,player_overlay.ramAddress
            else:
                image,base = (overlay.data,overlay.ramAddress) if address>=overlay.ramAddress else (arm9,rom.arm9RamAddress)
            if bytes(image[address-base:address-base+4])!=prologue:
                raise RuntimeError('Unexpected prologue for '+name)
            source=PAYLOAD_ADDRESS+len(runtime)
            runtime+=prologue+branch(source+4,address+4)
        runtime+=narc_index+animation_mask+animation_direct_index
        if len(runtime)>0x10000:
            raise RuntimeError('Runtime module exceeds the 64 KiB loader limit')
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
        if len(runtime)%4:raise RuntimeError('Runtime fixup table must be word aligned')
        blob=pack(PAYLOAD_ADDRESS,runtime,emitted['CoopRuntimeDispatch'],sorted(records))
        (root/'runtime-relocatable.bin').write_bytes(blob)
        module_id=len(rom.files)
        if args.runtime_placement=='prefix' and (rom.arm9RamAddress!=0x02004000 or len(runtime)>0x3f00):
            raise RuntimeError('Runtime cannot fit the verified free ARM9 prefix')
        installer,install_symbols=link(REPO/'mods/coop/install.cpp',root/'install',CAVE_START,game,launcher,cc,ld,
                                       [f'COOP_RUNTIME_FILE={module_id}',*(['COOP_RUNTIME_PREFIX=1'] if args.runtime_placement=='prefix' else [])])
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
        if arm9[game['NumCoins']-rom.arm9RamAddress:game['NumCoins']-rom.arm9RamAddress+8]!=bytes.fromhex('38009fe538209fe5'):
            raise RuntimeError('Unexpected native coin accessor')
        if arm9[0x02023178-rom.arm9RamAddress:0x02023194-rom.arm9RamAddress]!=bytes.fromhex('10109fe5003091e5002083e00300a0e1002081e51eff2fe178ee0902'):
            raise RuntimeError('Unexpected native particle arena allocator')
        memory_calls=[(0x02022f88,game['_ZN6Memory13operator_new2Ej'],'CoopAllocateParticlePool'),
                        (0x020231bc,game['func_0203cbc0'],'CoopFreeParticlePool'),
                        (0x02017c98,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x02017cd8,game['_ZN6Memory8AllocateEji'],'CoopAllocateAlignedResource'),
                        (0x02017d40,game['_ZN6Memory8AllocateEji'],'CoopAllocateAlignedResource'),
                        (0x02017da8,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x02017dcc,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x02017c3c,game['_ZN6Memory10DeallocateEPv'],'CoopFreeResource'),
                        (0x02017dc4,game['_ZN6Memory10DeallocateEPv'],'CoopFreeResource'),
                        (0x02017de4,game['_ZN6Memory10DeallocateEPv'],'CoopFreeResource'),
                        (0x020181c4,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x02018204,game['_ZN6Memory8AllocateEji'],'CoopAllocateAlignedResource'),
                        (0x02018378,game['_ZN6Memory8AllocateEji'],'CoopAllocateAlignedResource'),
                        (0x020183c4,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x020183e0,game['_ZN6Memory8AllocateEj'],'CoopAllocateResource'),
                        (0x020183fc,game['_ZN6Memory10DeallocateEPv'],'CoopFreeResource'),
                        (0x0201815c,game['_ZN6Memory10DeallocateEPv'],'CoopFreeResource')]
        for address,target,_ in memory_calls:
            offset=address-rom.arm9RamAddress
            if arm9[offset:offset+4]!=branch(address,target)[:3]+b'\xeb':
                raise RuntimeError(f'Unexpected native memory allocation/free call at {address:#x}')
        pairs=[(game['func_02030e4c'],'CoopConnectionUpdate'),(game['_ZN10dScStage_c10LoadSkyboxEv'],'CoopLoadSkybox'),(game['func_02062200'],'CoopWirelessReset'),(game['func_0201834c'],'CoopLoadDiskFile'),(game['func_020186c0'],'CoopResolveFile'),(game['func_020185c0'],'CoopOpenFile'),(game['func_02023178'],'CoopAllocateParticleChunk'),(game['func_02017060'],'CoopTrimResourceModel'),(game['NumCoins'],'CoopNumCoins'),(game['GiveCoins'],'CoopGiveCoins'),(game[SAVE_CURRENT],'CoopSaveCurrentFile'),(game['_Z17LoadLevelOverlaysi'],'CoopLoadLevelOverlays'),
               (game['func_0200d0ac'],'CoopCameraFar'),(game['func_0200d064'],'CoopCameraNear'),
               (game['_ZN9dCamera_c14GoBehindPlayerEj'],'CoopCameraBehind'),(game['func_0200ca14'],'CoopCameraFov'),
               (game['func_0200d3f8'],'CoopCameraLookTarget'),(game['func_0200d7e0'],'CoopCameraFirstPerson'),(game['func_0200d81c'],'CoopCameraNormal'),
               (0x020cae10,'CoopPlayerHeadLook'),(0x02024d40,'CoopCameraInputFlagsRead'),(0x020df6a0,'CoopPersonalCameraFlagsRead'),(0x020def88,'CoopCannonPitchRead'),(0x02126e10,'CoopAllocatePaintingMesh'),
               (game['_ZN7Message6UpdateEv'],'CoopMessageUpdate'),
               (game['KillPlayer'],'CoopKillPlayer'),(game['HitDeathPlane'],'CoopHitDeathPlane'),
               (ov_symbols['_ZN10dScEntry_c16CleanupResourcesEv'],'CoopEntryCleanup'),
               (game['_ZN10dScStage_c13InitResourcesEv'],'CoopStageInit'),(game['func_0205d688'],'CoopReadFile'),
               (game['_ZN8dScene_c19BeforeInitResourcesEv'],'CoopSceneBeforeInit'),
               (game['_ZN8dScene_c18AfterInitResourcesEj'],'CoopSceneAfterInit'),
               (game['_ZN8dScene_c14BeforeBehaviorEv'],'CoopSceneBefore'),(game['_ZN8dScene_c13AfterBehaviorEj'],'CoopSceneAfter'),
               (game['_ZN8dActor_c19BeforeInitResourcesEv'],'CoopActorBeforeInit'),(game['_ZN8dActor_c14BeforeBehaviorEv'],'CoopActorBefore'),(game['_ZN8dActor_c13AfterBehaviorEj'],'CoopActorAfter')]
        if args.diagnostic_player_cost:
            pairs += [(game['_ZN10dScStage_c6RenderEv'],'CoopCostStageRender')]
        if args.experimental_animation_cache:
            pairs += [(game['_ZN5mHeap6Heap_t8AllocateEji'],'CoopAnimationHeapAllocate'),
                      (game['_ZN10dScStage_c16CleanupResourcesEv'],'CoopAnimationStageCleanup'),
                      (game['_ZN5mHeap6Heap_t10ReallocateEPvj'],'CoopAnimationHeapReallocate'),
                      (0x0203c5d0,'CoopAnimationMaxMemory'),(0x0203c5f8,'CoopAnimationMaxMemory'),
                      (0x0203c5ac,'CoopAnimationMemoryLeft')]
        ram_hooks=[{'address':hex(a),'targetOffset':hex(emitted[n]-PAYLOAD_ADDRESS),'symbol':n}for a,n in pairs]
        module_report={'fileID':module_id,'linkBase':hex(PAYLOAD_ADDRESS),'bodyBytes':len(runtime),
                       'entryOffset':hex(emitted['CoopRuntimeDispatch']-PAYLOAD_ADDRESS),'fixups':len(records),
                       'sha256':hashlib.sha256(blob).hexdigest(),'cacheAddress':'0x02004180'}
        if args.experimental_animation_cache:
            module_report['experimentalAnimationReadCache']={'entries':32,'payloadBudget':65536,'maxMemberBytes':16384,
                'preserveAcrossStageTransitions':args.experimental_persistent_animation_cache,
                'statsOffset':emitted['coopAnimationCacheStats']-PAYLOAD_ADDRESS,
                'entriesOffset':emitted['coopAnimationReadEntries']-PAYLOAD_ADDRESS,'entryWords':6,
                'fields':['hits','misses','stores','evictions','payloadBytes','entries','peakBytes','flushes'],
                'eligibleMaskSha256':hashlib.sha256(animation_mask).hexdigest(),
                'directMembers':len(direct_animations),
                'directIndexSha256':hashlib.sha256(animation_direct_index).hexdigest()}
            if args.experimental_lazy_animation_eviction:
                module_report['experimentalAnimationReadCache']['virtualCapacityQueries']={
                    'successesOffset':emitted['coopAnimationVirtualQueries']-PAYLOAD_ADDRESS,
                    'fallbacksOffset':emitted['coopAnimationVirtualFallbacks']-PAYLOAD_ADDRESS,
                    'usedNodeLimit':1024,'freeNodeLimit':256}
        if args.experimental_animation_cache and args.diagnostic_stage_cycle:
            module_report['diagnosticAnimationFlushes']={
                'countOffset':emitted['coopDiagnosticAnimationFlushCount']-PAYLOAD_ADDRESS,
                'rowsOffset':emitted['coopDiagnosticAnimationFlushes']-PAYLOAD_ADDRESS,
                'capacity':16,'fields':['sequence','reason','level','net','payloadBytes','entries','vblank','loopPhase'],
                'reasons':['unknown','entry-cleanup','ended-scene','root-growth','root-capacity-query',
                           'root-total-memory-query','connection-loss','new-match','planned-session-end','stage-cleanup']}
        module_report['sharedCourseCoins']=True
        module_report['runtimePlacement']=args.runtime_placement
        if args.runtime_placement=='prefix':module_report['residentAddress']='0x02000100'
        module_report['particlePoolFallback']=True
        module_report['particleSplitFallback']=True
        module_report['particleTableReserveBeforeStageResources']=True
        module_report['sharedResourceFallback']=True
        module_report['streamUncachedNarcMembers']=True
        module_report['streamCompressedDiskFiles']=True
        module_report['nativeTeardownResetDeduplicated']=True
        module_report['evictCommonStageSourceCache']=True
        module_report['evictStageCacheForPaintingMesh']=True
        module_report['localCameraControls']=True
        if args.experimental_painting_math:
            module_report['experimentalPaintingMath']={'defaultEnabled':False,'statsOffset':emitted['coopPaintingMathStats']-PAYLOAD_ADDRESS,
                'fields':['coefficientHits','coefficientFills','nativeFallbacks'],'nativeStateZeroPreserved':True}
        module_report['cooperativeMinimapMarkers']={'nativeProjection':True,'localMapControls':True,
            'markerStyle':'native-common-HUD-slot-numbers','storyItemRulesPreserved':True}
        module_report['nativeFlightEntranceMarioCaps']=True
        module_report['loadingChecksumTransitionGrace']=True
        module_report['localMovementCameraModes']=[33607948, 33608008, 33608760, 33608820, 33608968, 33609028, 33609088, 33609152, 33609212, 33609276, 33609336, 33609396, 33609456, 33609516, 33609576, 33609636]
        module_report['cameraPitchUserBytes']=[7,8]
        module_report['cameraInfoUserByte']=5
        module_report['perPlayerCameraInputGuards']=True
        module_report['perPlayerCannonPitch']=True
        module_report['deterministicActorInitialization']=True
        module_report['localShadowVisibility']=True
        module_report['shadowVisibilityReads']=[{'address':hex(address),
            'originalWord':'0xe59000b0','targetOffset':hex(emitted['CoopShadowFlagsRead']-PAYLOAD_ADDRESS)}
            for address in (0x02010ba4,0x02010bf0)]
        module_report['narcIndexBytes']=len(narc_index)
        module_report['narcIndexSha256']=hashlib.sha256(narc_index).hexdigest()
        if args.diagnostic_start_level is not None:
            module_report['diagnosticStartLevel']=args.diagnostic_start_level
            module_report['diagnosticStageCycle']=args.diagnostic_stage_cycle
            if args.diagnostic_stage_cycle:module_report['diagnosticStageChord']=0x700
        module_report['diagnosticOffsets']={name:emitted[name]-PAYLOAD_ADDRESS
                                           for name in ('coopActorInitializationsSeeded','coopStageIdentity','coopLoadingChecksumGraceClears','coopEnabled','coopSaveState','coopSavePage',
                                                        'coopSaveEpoch','coopStageLoading','coopMenuLoading',
                                                        'coopSceneInitializing','coopTitleLoading','coopTitleRadioResetPending','coopFileWaiting',
                                                        'coopSessionEnded','coopDeathTriggered','coopGuestTutorialSkips',
                                                        'coopNarcOpenDiagnostic','coopStageCacheEvictions','coopStreamedLzReads','coopStreamedNarcReads','coopParticleFallbacks','coopParticleSplitFallbacks','coopParticleSegmentCount','coopResourceFallbacks',
                                                        'coopResourceFallbacksLive','coopResourceFallbacksPeak')}
        if args.diagnostic_stage_cycle:
            module_report['diagnosticOffsets']['coopDiagnosticConnectionFailure']=emitted['coopDiagnosticConnectionFailure']-PAYLOAD_ADDRESS
            module_report['connectionFailureFields']=['errors','radio','net','tick','level','pause','loopPhase','fileWaiting']
            for name in ('coopDiagnosticGameplayRead','coopDiagnosticSlowGameplayRead'):
                module_report['diagnosticOffsets'][name]=emitted[name]-PAYLOAD_ADDRESS
            module_report['gameplayReadFields']=['count','size','romTop','position','pause','vblankBegin','vblankEnd','active','tickBegin','tickEnd','result','ownFlags','loopPhase','sceneEvent','burstTick','burstVblankBegin','burstVblankEnd','burstReads','burstBytes','burstLongestRead']
        if args.diagnostic_render_cost:
            for name in ('coopDiagnosticRenderCount','coopDiagnosticRenderCosts'):
                module_report['diagnosticOffsets'][name]=emitted[name]-PAYLOAD_ADDRESS
            module_report['diagnosticRenderCost']={'changesScheduling':True,'capacity':64,
                'kinds':['terrain-opaque','terrain-transparent','player-body','yoshi-head'],
                'fields':['tick','kind','slot','polygonsBefore','polygonsAfter','verticesBefore',
                          'verticesAfter','overflowBefore','overflowAfter','vblankBegin','vblankEnd','localSlot']}
        if args.diagnostic_player_cost:
            module_report['diagnosticPlayerCost']={
                'clockHz':33513982/64,'exclusiveCpuCycles':False,'drainsGeometry':False,
                'costsOffset':emitted['coopPlayerCosts']-PAYLOAD_ADDRESS,
                'stageOffset':emitted['coopPlayerCostStage']-PAYLOAD_ADDRESS,
                'kinds':['player-behavior','player-body','yoshi-head','stage-render',
                         'terrain-opaque','shadows','terrain-transparent','actor-collision'],
                'fields':['sequence','count','totalTicksLow','totalTicksHigh','maxTicks','minTicks'],
                'buckets':16,'resetOnStageIdentity':True}
        if args.experimental_collision_broadphase:
            module_report['experimentalCollisionBroadphase']={
                'callsite':'0x02014bb4','preservesPairOrder':True,
                'coordinateLimit':0x1fffffff,'defaultEnabled':False}
        if args.experimental_collision_plan:
            module_report['experimentalCollisionPlan']={
                'capacity':256,'minimumNodes':48,'pairCheckBudget':1024,'windowCheckBudget':2048,'axisPolicy':'bounded-alternate-if-primary-window-exceeds-budget','envelopeMargin':32*4096,'maximumEnvelopeMargin':2048*4096,'velocityEnvelopeFactor':32,'defaultEnabled':False,
                'reusesOffset':emitted['coopCollisionPlanReuses']-PAYLOAD_ADDRESS,
                'refreshesOffset':emitted['coopCollisionPlanRefreshes']-PAYLOAD_ADDRESS,'refreshShiftBudget':256,
                'edgeRefreshesOffset':emitted['coopCollisionPlanEdgeRefreshes']-PAYLOAD_ADDRESS,
                'edgeRefreshNodeBudget':8,'edgeRefreshPairBudget':1024,
                'validatedCallbacksOffset':emitted['coopCollisionValidatedCallbacks']-PAYLOAD_ADDRESS,
                'callbackAllocationsOffset':emitted['coopCollisionCallbackAllocations']-PAYLOAD_ADDRESS,
                'statsOffset':emitted['coopCollisionPlanStats']-PAYLOAD_ADDRESS,
                'workspaceOffset':emitted['coopCollisionPlan']-PAYLOAD_ADDRESS,
                'fields':['preparedFrames','fallbackFrames','plannedPairs','dispatchedPairs',
                          'notifications','pressureReleases','peakNodes','abortedFrames']}
        patches.append({'purpose':'ROOT module loader in unused VS result routines','address':hex(CAVE_START),
                        'size':CAVE_END-CAVE_START,'installerBytes':len(installer)})
    output=root/('baseline.nds' if args.baseline else 'sm64ds-coop-experimental.nds')
    output.write_bytes(output_data)
    report={'inputSha256':ROM_SHA256,'baseline':args.baseline,'output':str(output.relative_to(REPO)),
            'outputSha256':hashlib.sha256(output_data).hexdigest(),'romSize':len(output_data),
            'experimentalHostSaveSlot':args.save_slot,
            'bootImagesUnchanged':True,'nativeFileExtentsUnchanged':True,'patches':patches,
            'runtimeModule':module_report,'lateRamHooks':ram_hooks,
            'lateRamCalls':([] if args.baseline else [
                {'address':hex(a),'originalTarget':hex(t),'targetOffset':hex(emitted[n]-PAYLOAD_ADDRESS),'symbol':n}
                for a,t,n in memory_calls]),
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
