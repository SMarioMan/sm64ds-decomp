"""Run the retail cannon launch arithmetic with independently aimed views.

Private Unicorn mappings adapt the final return before presentation/animation;
no live emulator state or wireless packet is written.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R12,UC_ARM_REG_CPSR,UC_ARM_REG_PC)
from test_particle_heap import HeapHarness


class CannonCameraTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        overlay=self.stock.loadArm9Overlays()[2]
        self.cpu.mem_write(overlay.ramAddress,bytes(overlay.data))
        self.actor=0x023f0000
        self.camera=0x023f1000
        self.cpu.mem_write(self.actor,bytes(0x800))
        self.write(0x0209f318,self.camera)
        self.cpu.mem_write(self.game['gActivePlayerSlot'],b'\x02')
        self.cpu.mem_write(self.actor+0x6d8,b'\x02')
        self.cpu.mem_write(0x0209f49e+24*2,b'\x01\0')
        self.cpu.mem_write(0x020a1164+36*2,struct.pack('<h',0x1234))
        def finish(cpu,address,size,user):
            if address==0x020df008:
                cpu.reg_write(UC_ARM_REG_PC,self.base+0xff00)
        self.cpu.hook_add(UC_HOOK_CODE,finish)

    def patch_pitch(self):
        address=0x020def88
        target=self.runtime['CoopCannonPitchRead']
        self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))
        self.cpu.ctl_remove_cache(0x020def14,0x020df208)

    def launch(self,pitch):
        self.cpu.mem_write(self.actor+0x6e3,b'\x01')
        self.cpu.mem_write(self.camera+0x17e,struct.pack('<h',pitch))
        self.call(0x020def14,self.actor)
        return (self.word(self.actor+0x98),self.word(self.actor+0xa8),
                bytes(self.cpu.mem_read(self.actor+0x94,2)))

    def test_original_cannon_launch_diverges_with_different_local_views(self):
        self.assertNotEqual(self.launch(0),self.launch(0x2000))

    def test_native_launch_uses_the_firing_players_pitch_on_every_console(self):
        expected=self.launch(0x2000)
        self.cpu.mem_write(0x020a1166+36*2+7,struct.pack('<h',0x2000))
        self.patch_pitch()
        for console,pitch in enumerate((-0x2000,0,0x1000,0x3000)):
            with self.subTest(console=console):
                self.cpu.mem_write(0x020a0f10,bytes([console]))
                self.assertEqual(self.launch(pitch),expected)
                self.assertEqual(bytes(self.cpu.mem_read(self.camera+0x17e,2)),struct.pack('<h',pitch))

    def test_distinct_players_retain_distinct_native_aim(self):
        expected=[self.launch(pitch) for pitch in (0,0x1000,0x2000,0x3000)]
        self.patch_pitch()
        for slot,pitch in enumerate((0,0x1000,0x2000,0x3000)):
            self.cpu.mem_write(self.game['gActivePlayerSlot'],bytes([slot]))
            self.cpu.mem_write(self.actor+0x6d8,bytes([slot]))
            self.cpu.mem_write(0x0209f49e+24*slot,b'\x01\0')
            self.cpu.mem_write(0x020a1164+36*slot,struct.pack('<h',0x1234))
            self.cpu.mem_write(0x020a1166+36*slot+7,struct.pack('<h',pitch))
            self.assertEqual(self.launch(-0x1000),expected[slot])

    def test_offline_and_disabled_coop_preserve_native_launch(self):
        expected=self.launch(-0x1000)
        self.patch_pitch()
        for enabled,net in ((0,4),(1,0)):
            self.write(self.runtime['coopEnabled'],enabled)
            self.write(0x0209fc68,net)
            self.assertEqual(self.launch(-0x1000),expected)

    def test_pitch_load_preserves_registers_and_condition_flags(self):
        self.patch_pitch()
        self.cpu.mem_write(0x020a1166+36*2+7,struct.pack('<H',0xe000))
        registers=((UC_ARM_REG_R1,0x11111111),(UC_ARM_REG_R2,0x22222222),
                   (UC_ARM_REG_R3,0x33333333),(UC_ARM_REG_R4,self.camera),
                   (UC_ARM_REG_R12,0xcccccccc))
        for register,value in registers:self.cpu.reg_write(register,value)
        def flags(cpu,address,size,user):
            if address==self.runtime['CoopCannonPitchRead']:
                cpu.reg_write(UC_ARM_REG_CPSR,0xf00000df)
        self.cpu.hook_add(UC_HOOK_CODE,flags)
        self.assertEqual(self.call('CoopCannonPitchRead',self.camera+0x100),0xe000)
        for register,value in registers:self.assertEqual(self.cpu.reg_read(register),value)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0xf0000000,0xf0000000)


if __name__=='__main__':unittest.main()
