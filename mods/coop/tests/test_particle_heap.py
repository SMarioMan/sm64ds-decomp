"""ARM checks against the captured four-console HMC allocation failure.

The private RAM/DTCM fixture is never distributed. Unicorn executes the actual
retail heap allocator and compiled mod helpers in isolation; this is not a
wireless gameplay test and does not modify a running emulator.
"""
import io
import json
import os
from pathlib import Path
import struct
import sys
import unittest

import ndspy.code
import ndspy.rom
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_CPSR, UC_ARM_REG_LR, UC_ARM_REG_PC,
                               UC_ARM_REG_SP)

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'mods/coop'))
from build import symbols


class NativeAllocationFailure(Exception):
    pass


class HeapHarness:
    fixture_variable='COOP_HEAP_FIXTURE'
    default_fixture='/workspace/runtime/hmc-wireless-load-inspection/hmc-load-0'
    @classmethod
    def setUpClass(cls):
        fixture=Path(os.environ.get(cls.fixture_variable,cls.default_fixture))
        cls.ram=fixture.with_suffix('.ram').read_bytes()
        cls.dtcm=fixture.with_suffix('.dtcm').read_bytes()
        cls.stock=ndspy.rom.NintendoDSRom.fromFile('/workspace/inputs/sm64ds-eu.nds')
        cls.main=ndspy.code.MainCodeFile(cls.stock.arm9,cls.stock.arm9RamAddress)
        report=json.loads((ROOT/'build/coop/build.json').read_text())
        image=ndspy.rom.NintendoDSRom.fromFile(ROOT/'build/coop/sm64ds-coop-experimental.nds')
        blob=image.files[report['runtimeModule']['fileID']]
        _,link,size,_,count,_=struct.unpack_from('<6I',blob)
        cls.base=0x01000000 # Isolated unit-test mapping, outside the heap fixture.
        delta=cls.base-link
        cls.body=bytearray(blob[24:24+size])
        for record in struct.unpack_from('<'+str(count)+'I',blob,24+size):
            offset=record&0x7fffffff
            word=struct.unpack_from('<I',cls.body,offset)[0]
            if record&0x80000000:
                word=(word&0xff000000)|((word-(delta>>2))&0xffffff)
            else:
                word=(word+delta)&0xffffffff
            struct.pack_into('<I',cls.body,offset,word)
        elf=ELFFile(io.BytesIO((ROOT/'build/coop/runtime.elf').read_bytes()))
        cls.runtime={s.name:s['st_value']+delta for s in elf.get_section_by_name('.symtab').iter_symbols()
                     if s.name and isinstance(s['st_shndx'],int)}
        cls.game=symbols(ROOT/'config/arm9/symbols.txt')

    def setUp(self):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        self.cpu.mem_map(0x02000000,0x400000)
        self.cpu.mem_map(0x01ff0000,0x10000)
        self.cpu.mem_map(self.base,0x10000)
        self.cpu.mem_map(0x04000000,0x10000)
        self.cpu.mem_write(0x02000000,self.ram)
        self.cpu.mem_write(0x023c0000,self.dtcm)
        for section in self.main.sections:
            if section.ramAddress<0x02000000:
                self.cpu.mem_write(section.ramAddress,bytes(section.data))
        self.cpu.mem_write(self.base,bytes(self.body))
        self.write(self.runtime['coopEnabled'],1)
        self.write(0x0209fc68,4)
        self.root=self.word(0x020a0ea0)
        self.game_heap=self.word(0x020a0eac)
        def trap(cpu,address,size,data):
            if address==self.game['Crash']:
                raise NativeAllocationFailure('The retail allocator entered Crash()')
        self.cpu.hook_add(UC_HOOK_CODE,trap)

    def word(self,address):
        return struct.unpack('<I',self.cpu.mem_read(address,4))[0]

    def write(self,address,value):
        self.cpu.mem_write(address,struct.pack('<I',value&0xffffffff))

    def call(self,address,*arguments):
        if isinstance(address,str):address=self.runtime[address]
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xdf)
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2),arguments):
            self.cpu.reg_write(register,value&0xffffffff)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
        self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(address,self.base+0xff00,count=1000000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        return self.cpu.reg_read(UC_ARM_REG_R0)

    def largest(self,heap):
        return self.call(self.game['_ZN5mHeap6Heap_t21MaxAllocationUnitSizeEv'],heap)

    def intact(self,heap):
        return self.call(self.game['_ZN5mHeap6Heap_t6IntactEv'],heap)


class ParticleHeapTests(HeapHarness,unittest.TestCase):

    def test_original_pool_request_reproduces_captured_failure(self):
        self.assertLess(self.largest(self.root),0x8c00)
        self.assertGreaterEqual(self.largest(self.game_heap),0x8c00)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory13operator_new2Ej'],0x8c00)

    def test_full_native_pool_fits_spare_game_heap_and_frees_cleanly(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        pool=self.call('CoopAllocateParticlePool',0x8c00)
        start=self.word(self.game_heap+4)
        self.assertGreaterEqual(pool,start)
        self.assertLess(pool+0x8c00,start+self.word(self.game_heap+8)+1)
        self.assertEqual(self.largest(self.root),before[0])
        self.assertEqual(self.word(self.runtime['coopParticleFallbacks']),1)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))

    def test_small_pool_preserves_original_root_ownership(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        pool=self.call('CoopAllocateParticlePool',0x400)
        self.assertNotEqual(pool,0)
        self.assertEqual(self.word(self.runtime['coopParticleFallbacks']),0)
        self.assertEqual(self.largest(self.game_heap),before[1])
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_owner_survives_coop_policy_shutdown(self):
        before=self.largest(self.game_heap)
        pool=self.call('CoopAllocateParticlePool',0x8c00)
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def test_repeated_scene_pool_cycles_do_not_leak(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            pool=self.call('CoopAllocateParticlePool',0x8c00)
            self.call('CoopFreeParticlePool',pool)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertEqual(self.word(self.runtime['coopParticleFallbacks']),8)

    def test_offline_allocator_retains_native_failure(self):
        self.write(self.runtime['coopEnabled'],0)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateParticlePool',0x8c00)

    def test_both_heaps_too_small_retains_native_failure(self):
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateParticlePool',0x80000)

    def test_reserved_table_is_used_by_the_native_resource_parser(self):
        from test_particle_segments import ParticleSegmentTests
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.call('CoopReserveParticlePool',13)
        reserved=self.word(self.runtime['coopParticleReservedTable'])
        self.assertEqual(self.word(self.runtime['coopParticleReservedSize']),10272)
        pool,manager=ParticleSegmentTests.setup_native_manager(self)
        self.assertEqual(self.word(manager+0x1c),reserved)
        self.assertEqual(self.word(self.runtime['coopParticleReservedSize']),0)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_bowser_reservation_keeps_the_native_larger_arrays(self):
        from test_particle_segments import ParticleSegmentTests
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.call('CoopReserveParticlePool',36)
        self.assertEqual(self.word(self.runtime['coopParticleReservedArena']),0xa800)
        pool,manager=ParticleSegmentTests.setup_native_manager(self,0xa800,64,320)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_wrong_native_request_cannot_overrun_a_reservation(self):
        self.call('CoopReserveParticlePool',13)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateParticlePool',0xa800)
        pool=self.call('CoopAllocateParticlePool',0x8c00)
        self.call('CoopFreeParticlePool',pool)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))


if __name__=='__main__':unittest.main()
