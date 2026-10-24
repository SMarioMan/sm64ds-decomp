"""ARM unit checks of compiled coin hooks and the retail hundred-coin trigger.

Uses private ROM/build inputs and Unicorn, not a running multiplayer session.
Actor allocation is observed and returns null; no wireless acceptance is claimed.
"""
import io
from pathlib import Path
import struct
import sys
import unittest

import ndspy.code
import ndspy.codeCompression
import ndspy.rom
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'mods/coop'))
from build import symbols


class CounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock=ndspy.rom.NintendoDSRom.fromFile('/workspace/inputs/sm64ds-eu.nds')
        cls.main=ndspy.code.MainCodeFile(cls.stock.arm9,cls.stock.arm9RamAddress)
        cls.player=cls.stock.loadArm9Overlays()[2]
        rom=ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/coop/sm64ds-coop-experimental.nds')
        import json
        report=json.loads((ROOT/'build/coop/build.json').read_text())
        blob=rom.files[report['runtimeModule']['fileID']]
        _,cls.base,size,*_=struct.unpack_from('<6I',blob)
        cls.body=bytes(blob[24:24+size])
        elf=ELFFile(io.BytesIO((ROOT/'build/coop/runtime.elf').read_bytes()))
        cls.runtime={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        cls.game=symbols(ROOT/'config/arm9/symbols.txt')

    def setUp(self):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        self.cpu.mem_map(0x02000000,0x400000)
        self.cpu.mem_map(0x01ff0000,0x10000)
        # Reproduce CRT0 autoload placement. Copying the whole expanded file
        # would incorrectly put its ITCM source bytes over ARM9 BSS globals.
        for section in self.main.sections:
            self.cpu.mem_write(section.ramAddress,bytes(section.data))
        self.cpu.mem_write(self.player.ramAddress,bytes(self.player.data))
        self.cpu.mem_write(self.base,self.body)
        self.spawns=[]
        spawn=self.game['_ZN8dActor_c5SpawnEjjRK7Vector3PK10Vector3_16as']
        def observe(cpu,address,size,data):
            if address==spawn:
                position=struct.unpack('<iii',cpu.mem_read(cpu.reg_read(UC_ARM_REG_R2),12))
                self.spawns.append((cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1),position))
                cpu.reg_write(UC_ARM_REG_R0,0) # Native allocation failure path.
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,observe)
        self.write(self.runtime['coopEnabled'],1,4)
        self.write(0x0209fc68,4,4)
        self.write(0x0209f2d8,0,1)
        self.write(0x0209f21c,4,1)
        self.write(0x0209f2f8,6,1)
        for slot in range(4):
            actor=0x02380000+slot*0x1000
            self.write(0x0209f394+slot*4,actor,4)
            self.write(actor+0x6d8,slot,1)
            self.cpu.mem_write(actor+0x5c,struct.pack('<iii',slot*1000*4096,200*4096,(50+slot*10)*4096))

    def write(self,address,value,size):
        self.cpu.mem_write(address,int(value&((1<<(size*8))-1)).to_bytes(size,'little'))

    def counts(self,values=None):
        if values is not None:self.cpu.mem_write(0x0209f358,struct.pack('<4h',*values))
        return struct.unpack('<4h',self.cpu.mem_read(0x0209f358,8))

    def call(self,address,*arguments):
        if isinstance(address,str):address=self.runtime[address]
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1),arguments):self.cpu.reg_write(register,value&0xffffffff)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
        self.cpu.reg_write(UC_ARM_REG_LR,0x023fff00)
        self.cpu.emu_start(address,0x023fff00,count=100000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),0x023fff00,'ARM routine did not return')
        return self.cpu.reg_read(UC_ARM_REG_R0)

    def test_split_retail_coins_do_not_spawn_a_hundred_coin_star(self):
        self.counts((40,30,29,0))
        self.call(self.game['GiveCoins'],3,1)
        self.assertEqual(self.call(self.game['NumCoins']),100)
        self.assertEqual(self.spawns,[])

    def test_guest_team_pickup_triggers_native_star_at_collector(self):
        self.counts((99,99,99,99))
        self.call('CoopGiveCoins',3,1)
        self.assertEqual(self.counts(),(100,100,100,100))
        self.assertEqual(self.call('CoopNumCoins'),100)
        self.assertEqual(self.spawns,[(0xb2,0x20,(3000*4096,500*4096,80*4096))])

    def test_shared_total_clamps_and_stays_single_in_hud(self):
        self.counts((250,250,250,250))
        self.call('CoopGiveCoins',2,10)
        self.assertEqual(self.counts(),(255,255,255,255))
        self.assertEqual(self.call('CoopNumCoins'),255)
        self.call('CoopGiveCoins',1,-300)
        self.assertEqual(self.counts(),(0,0,0,0))
        self.assertEqual(self.call('CoopNumCoins'),0)

    def test_tally_reset_is_authoritative_before_next_guest_pickup(self):
        self.counts((0,100,100,100))
        self.call('CoopGiveCoins',1,1)
        self.assertEqual(self.counts(),(1,1,1,1))
        self.assertEqual(self.spawns,[])

    def test_disabled_hook_preserves_retail_individual_counts(self):
        self.write(self.runtime['coopEnabled'],0,4)
        self.counts((5,7,9,11))
        self.call('CoopGiveCoins',2,5)
        self.assertEqual(self.counts(),(5,7,14,11))
        self.assertEqual(self.call('CoopNumCoins'),self.call(self.game['NumCoins']))

    def test_vs_rules_preserve_individual_counts(self):
        self.write(0x0209f2d8,1,1)
        self.counts((5,7,9,11))
        self.call('CoopGiveCoins',1,5)
        self.assertEqual(self.counts(),(5,12,9,11))
        self.assertEqual(self.call('CoopNumCoins'),37)

    def test_offline_coin_accessor_matches_retail(self):
        self.write(0x0209fc68,0,4)
        self.counts((255,128,17,99))
        for count in range(5):
            self.write(0x0209f21c,count,1)
            self.assertEqual(self.call('CoopNumCoins'),self.call(self.game['NumCoins']))


if __name__=='__main__':unittest.main()
