"""Independent structural checks of the generated, local-only co-op cartridge."""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import unittest

import ndspy.rom
from elftools.elf.elffile import ELFFile

REPO = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get('COOP_BASEROM', '/workspace/inputs/sm64ds-eu.nds'))
BUILD = REPO / 'build/coop'


def destination(data, offset, address, link=False):
    word = struct.unpack_from('<I', data, offset)[0]
    if word >> 24 != (0xEB if link else 0xEA):
        raise AssertionError('Expected unconditional ARM branch')
    signed = word & 0xFFFFFF
    if signed & 0x800000:
        signed -= 0x1000000
    return address + 8 + signed * 4


class ImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = BASE.read_bytes()
        cls.modified = (BUILD / 'sm64ds-coop-experimental.nds').read_bytes()
        cls.stock = ndspy.rom.NintendoDSRom(cls.original)
        cls.mod = ndspy.rom.NintendoDSRom(cls.modified)
        cls.overlay = cls.mod.loadArm9Overlays()[75]
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.module = cls.mod.files[cls.report['runtimeModule']['fileID']]
        cls.header = struct.unpack_from('<6I',cls.module)
        cls.module_base = cls.header[1]
        cls.body = cls.module[24:24+cls.header[2]]
        cls.records = struct.unpack_from('<'+'I'*cls.header[4],cls.module,24+cls.header[2])

    def test_native_files_and_unchanged_boot_images(self):
        self.assertEqual(self.stock.arm9,self.mod.arm9)
        self.assertEqual(self.stock.arm7,self.mod.arm7)
        self.assertEqual(self.stock.arm9OverlayTable,self.mod.arm9OverlayTable)
        self.assertEqual(self.stock.arm7OverlayTable,self.mod.arm7OverlayTable)
        self.assertEqual(len(self.mod.files),len(self.stock.files)+1)
        changed=[i for i,data in enumerate(self.stock.files) if self.mod.files[i]!=data]
        self.assertEqual(changed,[self.overlay.fileID])
        old_fat=struct.unpack_from('<I',self.original,0x48)[0]
        new_fat=struct.unpack_from('<I',self.modified,0x48)[0]
        self.assertEqual(self.original[old_fat:old_fat+len(self.stock.files)*8],
                         self.modified[new_fat:new_fat+len(self.stock.files)*8])
        low,high=struct.unpack_from('<II',self.original,old_fat+self.overlay.fileID*8)
        self.assertEqual(self.original[0x4000:low],self.modified[0x4000:low])
        self.assertEqual(self.original[high:],self.modified[high:len(self.original)])
        allowed={0x14,*range(0x48,0x50),*range(0x80,0x84),0x15e,0x15f}
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(self.original[:0x4000],self.modified[:0x4000])) if a!=b))
        self.assertEqual(self.header[0],0x31584248)
        self.assertEqual(hashlib.sha256(self.module).hexdigest(),self.report['runtimeModule']['sha256'])

    def test_decoded_changes_are_confined(self):
        stock = self.stock.loadArm9Overlays()[75]
        mod = self.overlay
        self.assertEqual(len(stock.data), len(mod.data))
        allowed = [(0x021165B0, 0x02116AD4), (0x02116C8C, 0x02116C90),
                   (0x02118BF8, 0x02118BFC)]
        changed = [mod.ramAddress + i for i, (a, b) in enumerate(zip(stock.data, mod.data)) if a != b]
        self.assertGreater(len(changed), 100)
        self.assertTrue(all(any(lo <= address < hi for lo, hi in allowed) for address in changed))

    def test_late_install_hooks_and_untouched_entry(self):
        runtime = ELFFile(io.BytesIO((BUILD / 'runtime.elf').read_bytes()))
        installer = ELFFile(io.BytesIO((BUILD / 'install.elf').read_bytes()))
        rs = {s.name: s['st_value'] for s in runtime.get_section_by_name('.symtab').iter_symbols()}
        ins = {s.name: s['st_value'] for s in installer.get_section_by_name('.symtab').iter_symbols()}
        data, base = self.overlay.data, self.overlay.ramAddress
        for address, expected in [(0x02116C8C, ins['CoopInstallMatch']),
                                  (0x02118BF8, ins['CoopInstallResources'])]:
            self.assertEqual(destination(data, address - base, address), expected)
        stock = self.stock.loadArm9Overlays()[75]
        self.assertEqual(data[0x0211A410-base:0x0211A414-base],
                         stock.data[0x0211A410-base:0x0211A414-base])
        # The compiled runtime's zeroed session flag must be embedded as data;
        # leaving arbitrary secure-area bytes there would disable normal saves.
        flag=rs['coopEnabled']-self.module_base
        self.assertEqual(self.body[flag:flag+4],bytes(4))
        self.assertEqual(self.header[3],rs['CoopRuntimeDispatch']-self.module_base)

    def test_runtime_trampolines_preserve_original_prologues(self):
        elf = ELFFile(io.BytesIO((BUILD / 'runtime.elf').read_bytes()))
        symbols = {s.name: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        for name, original_address, prologue in [
            ('CoopOriginalLoadLevelOverlays', 0x0202DED4, bytes.fromhex('30402de9')),
            ('CoopOriginalEntryCleanup', 0x0211A210, bytes.fromhex('00402de9')),
            ('CoopOriginalStageInit',0x0202CC0C,bytes.fromhex('f04f2de9')),
            ('CoopOriginalSceneBefore',0x0202E3D4,bytes.fromhex('10402de9')),
            ('CoopOriginalActorBefore',0x02010FD4,bytes.fromhex('10402de9')),
            ('CoopOriginalReadFile',0x0205D688,bytes.fromhex('f0402de9')),
            ('CoopOriginalMessageUpdate',0x0201C0B8,bytes.fromhex('70402de9')),
            ('CoopOriginalKillPlayer',0x02029B30,bytes.fromhex('00402de9')),
            ('CoopOriginalHitDeathPlane',0x02029B84,bytes.fromhex('00402de9')),
            ('CoopOriginalLoadEntrances',0x020FE6C8,bytes.fromhex('f04f2de9')),
            ('CoopOriginalStarTutorial',0x020C6E14,bytes.fromhex('30402de9')),
            ('CoopOriginalCourseTutorial',0x020C44C4,bytes.fromhex('30402de9')),
            ('CoopOriginalLevelEnterInit',0x020C7838,bytes.fromhex('f0402de9')),
            ('CoopOriginalGiveCoins',0x0202A7B8,bytes.fromhex('00402de9')),
            ('CoopOriginalTrimModel',0x02017060,bytes.fromhex('30402de9')),
            ('CoopOriginalResolveFile',0x020186C0,bytes.fromhex('70402de9')),
            ('CoopOriginalOpenFile',0x020185C0,bytes.fromhex('f0412de9'))]:
            offset=symbols[name]-self.module_base
            self.assertEqual(self.body[offset:offset+4],prologue)
            self.assertEqual(destination(self.body,offset+4,symbols[name]+4),original_address+4)
            self.assertIn(0x80000000 | (offset+4),self.records)
        self.assertTrue(all((r&0x7fffffff)%4==0 and (r&0x7fffffff)<=len(self.body)-4 for r in self.records))

    def test_control_is_retail(self):
        control = (BUILD / 'baseline.nds').read_bytes()
        self.assertEqual(hashlib.sha256(control).digest(), hashlib.sha256(self.original).digest())

    def test_camera_completion_read_thunk(self):
        elf=ELFFile(io.BytesIO((BUILD/'runtime.elf').read_bytes()))
        symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        address=symbols['CoopCameraFlagsRead']
        offset=address-self.module_base
        # The replaced native LDR changes only r0. Preserve all the other
        # volatile registers across the C helper, then return after the BL.
        self.assertEqual(self.body[offset:offset+4],struct.pack('<I',0xe92d500e))
        self.assertEqual(self.body[offset+8:offset+12],struct.pack('<I',0xe8bd900e))
        self.assertEqual(destination(self.body,offset+4,address+4,link=True),symbols['CoopSharedCameraFlags'])
        player=self.stock.loadArm9Overlays()[2]
        for site in (0x020c4364,0x020c4b34):
            start=site-player.ramAddress
            self.assertEqual(player.data[start:start+8],struct.pack('<2I',0xe5900154,0xe2100902))

    def test_memory_calls_retain_call_semantics(self):
        import ndspy.codeCompression
        arm9=ndspy.codeCompression.decompress(self.stock.arm9)
        calls=self.report['lateRamCalls']
        self.assertEqual([int(call['address'],16) for call in calls],
                         [0x02022f88,0x020231bc,0x02017c98,0x02017cd8,0x02017d40,
                          0x02017da8,0x02017dcc,0x02017c3c,0x02017dc4,0x02017de4,
                          0x020181c4,0x02018204,0x02018378,0x020183c4,0x020183e0,
                          0x020183fc,0x0201815c])
        for call in calls:
            address=int(call['address'],16)
            self.assertEqual(destination(arm9,address-self.stock.arm9RamAddress,address,link=True),
                             int(call['originalTarget'],16))
            offset=int(call['targetOffset'],16)
            self.assertEqual(offset%4,0)
            self.assertLess(offset,len(self.body))
        self.assertTrue(self.report['runtimeModule']['particlePoolFallback'])
        self.assertTrue(self.report['runtimeModule']['sharedResourceFallback'])


if __name__ == '__main__':
    unittest.main()
