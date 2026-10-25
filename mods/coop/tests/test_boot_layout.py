"""Structural boot checks for the integrated cartridge, not just the base mod."""
import json
import os
from pathlib import Path
import struct
import unittest
import ndspy.rom
from ndspy import _common
from test_particle_heap import ROOT


class BootLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=Path(os.environ.get('COOP_HOST_ROM',ROOT/'build/coop/bootstrap/provisional-host.nds'))
        cls.raw=cls.path.read_bytes()
        cls.host=ndspy.rom.NintendoDSRom(cls.raw)
        cls.original=Path('/workspace/inputs/sm64ds-eu.nds').read_bytes()
        cls.stock=ndspy.rom.NintendoDSRom(cls.original)
        cls.report=json.loads(cls.path.with_suffix('.json').read_text())

    def test_integrated_host_preserves_retail_boot_executables(self):
        self.assertEqual(self.host.arm9,self.stock.arm9)
        self.assertEqual(self.host.arm7,self.stock.arm7)
        self.assertEqual(self.raw[0x20:0x40],self.original[0x20:0x40])

    def test_secure_area_and_its_original_metadata_are_untouched(self):
        arm9=struct.unpack_from('<I',self.raw,0x20)[0]
        original_arm9=struct.unpack_from('<I',self.original,0x20)[0]
        self.assertEqual(self.raw[arm9:arm9+0x4000],
                         self.original[original_arm9:original_arm9+0x4000])
        self.assertEqual(self.raw[0x6c:0x70],self.original[0x6c:0x70])

    def test_parent_bootstrap_loader_is_inside_the_lobby_overlay(self):
        overlay=self.host.loadArm9Overlays()[75]
        address=int(self.report['loaderAddress'],16)
        self.assertEqual(self.report['bootstrapLoaderStorage'],'overlay75')
        self.assertGreaterEqual(address,0x021165b0)
        self.assertLessEqual(address+self.report['loaderBytes'],0x02116acc)
        self.assertGreaterEqual(address,overlay.ramAddress)
        self.assertLess(address,overlay.ramAddress+len(overlay.data))

    def test_header_and_all_file_extents_fit_the_declared_cartridge(self):
        capacity=1<<(17+self.raw[0x14])
        self.assertEqual(len(self.raw),capacity)
        self.assertEqual(struct.unpack_from('<H',self.raw,0x15e)[0],_common.crc16(self.raw[:0x15e]))
        fat,size=struct.unpack_from('<II',self.raw,0x48)
        self.assertLessEqual(fat+size,capacity)
        for start,end in struct.iter_unpack('<II',self.raw[fat:fat+size]):
            self.assertLessEqual(start,end)
            self.assertLessEqual(end,capacity)


if __name__=='__main__':unittest.main()
