"""Independent structural checks of the generated, local-only co-op cartridge."""
import hashlib
import io
import os
from pathlib import Path
import struct
import unittest

import ndspy.rom
from elftools.elf.elffile import ELFFile

REPO = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get('COOP_BASEROM', '/workspace/inputs/sm64ds-eu.nds'))
BUILD = REPO / 'build/coop'


def destination(data, offset, address):
    word = struct.unpack_from('<I', data, offset)[0]
    if word >> 24 != 0xEA:
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

    def test_fixed_layout_and_unchanged_boot_images(self):
        self.assertEqual(len(self.original), len(self.modified))
        self.assertEqual(self.original[:0x4000], self.modified[:0x4000])
        self.assertEqual(self.stock.arm9, self.mod.arm9)
        self.assertEqual(self.stock.arm7, self.mod.arm7)
        self.assertEqual(self.stock.arm9OverlayTable, self.mod.arm9OverlayTable)
        changed_files = [i for i, (a, b) in enumerate(zip(self.stock.files, self.mod.files)) if a != b]
        self.assertEqual(changed_files, [self.overlay.fileID])
        fat = struct.unpack_from('<I', self.original, 0x48)[0]
        low, high = struct.unpack_from('<II', self.original, fat + self.overlay.fileID * 8)
        self.assertEqual(self.original[:low], self.modified[:low])
        self.assertEqual(self.original[high:], self.modified[high:])

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
        payload_address = ins['CoopPayload']
        flag = payload_address + rs['coopEnabled'] - 0x02004100
        self.assertEqual(data[flag - base:flag - base + 4], bytes(4))

    def test_runtime_trampolines_preserve_original_prologues(self):
        elf = ELFFile(io.BytesIO((BUILD / 'runtime.elf').read_bytes()))
        symbols = {s.name: s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        installer = ELFFile(io.BytesIO((BUILD / 'install.elf').read_bytes()))
        payload = next(s['st_value'] for s in installer.get_section_by_name('.symtab').iter_symbols()
                       if s.name == 'CoopPayload')
        data, base = self.overlay.data, self.overlay.ramAddress
        for name, original_address, prologue in [
            ('CoopOriginalLoadLevelOverlays', 0x0202DED4, bytes.fromhex('30402de9')),
            ('CoopOriginalEntryCleanup', 0x0211A210, bytes.fromhex('00402de9'))]:
            offset = payload - base + symbols[name] - 0x02004100
            self.assertEqual(data[offset:offset+4], prologue)
            self.assertEqual(destination(data, offset+4, symbols[name]+4), original_address+4)

    def test_control_is_retail(self):
        control = (BUILD / 'baseline.nds').read_bytes()
        self.assertEqual(hashlib.sha256(control).digest(), hashlib.sha256(self.original).digest())


if __name__ == '__main__':
    unittest.main()
