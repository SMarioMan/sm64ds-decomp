"""Run retail shadow registration with the real synchronization visibility guard.

The isolated ARM fixture demonstrates the original unwanted shadow, then checks
both native drop-shadow helpers, their stack arguments and the read-hook ABI.
No running emulator or wireless packet is altered by these tests.
"""
import struct
import unittest
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
from test_particle_heap import HeapHarness


class ShadowVisibilityTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.cpu.mem_map(0x01200000,0x10000)
        self.actor=0x01200000
        self.shadow=0x01201000
        self.matrix=0x01202000
        self.stack=0x0120f000
        for start,size in ((0x02010b9c,0x94),(0x02015e64,0x58)):
            section=next(s for s in self.main.sections if s.ramAddress<=start and
                         start+size<=s.ramAddress+len(s.data))
            self.cpu.mem_write(start,bytes(section.data[start-section.ramAddress:start-section.ramAddress+size]))
        self.write(0x0209cef4,0)
        self.cpu.mem_write(0x0209ceec,b'\0')
        self.write(self.actor+0xb0,3) # Native visible/behavior flags after neutralization.
        self.write(self.runtime['coopBehaviorActor'],self.actor)
        self.write(self.runtime['coopBehaviorVisibility'],0x10) # Actual local far clip.

    def install_read_hooks(self):
        for address in (0x02010ba4,0x02010bf0):
            target=self.runtime['CoopShadowFlagsRead']
            self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))

    def drop(self,xyz=False):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xdf)
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),
                                   (self.actor,self.shadow,self.matrix,0x51000)):
            self.cpu.reg_write(register,value)
        args=(0x32000,0x73000,19) if xyz else (0x32000,19)
        self.cpu.mem_write(self.stack,struct.pack('<'+'I'*len(args),*args))
        self.cpu.reg_write(UC_ARM_REG_SP,self.stack)
        self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(0x02010b9c if xyz else 0x02010be8,self.base+0xff00,count=10000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_SP),self.stack)

    def test_original_neutralized_flags_register_an_unwanted_far_shadow(self):
        self.drop()
        self.assertEqual(self.word(0x0209cef4),self.shadow)
        self.assertEqual(self.word(self.shadow+0xc),self.matrix)

    def test_both_native_helpers_reject_the_saved_local_far_clip(self):
        self.install_read_hooks()
        for xyz in (False,True):
            with self.subTest(xyz=xyz):
                self.drop(xyz)
                self.assertEqual(self.word(0x0209cef4),0)
                self.assertEqual(self.word(self.actor+0xb0),3) # AI still sees neutral flags.

    def test_visible_native_shadow_preserves_scales_matrix_and_stack_opacity(self):
        self.install_read_hooks()
        self.write(self.runtime['coopBehaviorVisibility'],0)
        for xyz in (False,True):
            with self.subTest(xyz=xyz):
                self.write(0x0209cef4,0)
                self.drop(xyz)
                self.assertEqual(self.word(0x0209cef4),self.shadow)
                self.assertEqual(self.word(self.shadow+0xc),self.matrix)
                self.assertEqual(struct.unpack('<iii',self.cpu.mem_read(self.shadow+0x10,12)),
                                 (0x51000,0x32000,0x73000 if xyz else 0x51000))
                self.assertEqual(bytes(self.cpu.mem_read(self.shadow+0x1c,1)),b'\x13')

    def test_offline_disabled_and_other_actor_context_keep_native_behavior(self):
        self.install_read_hooks()
        for mode in ('offline','disabled','other-actor'):
            with self.subTest(mode=mode):
                self.write(0x0209cef4,0)
                self.write(0x0209fc68,0 if mode=='offline' else 4)
                self.write(self.runtime['coopEnabled'],0 if mode=='disabled' else 1)
                self.write(self.runtime['coopBehaviorActor'],self.actor+0x400 if mode=='other-actor' else self.actor)
                self.drop()
                self.assertEqual(self.word(0x0209cef4),self.shadow)

    def test_actor_added_shadow_suppression_is_retained(self):
        self.install_read_hooks()
        self.write(self.runtime['coopBehaviorVisibility'],0)
        self.write(self.actor+0xb0,0x13)
        self.drop()
        self.assertEqual(self.word(0x0209cef4),0)
        self.assertEqual(self.word(self.actor+0xb0),0x13)

    def test_read_hook_preserves_argument_registers_and_condition_flags(self):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xa80000df)
        registers=(UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12)
        values=(0x12345678,0xabcdef01,0x76543210,0xfeedbeef)
        for register,value in zip(registers,values):self.cpu.reg_write(register,value)
        self.cpu.reg_write(UC_ARM_REG_R0,self.actor)
        self.cpu.reg_write(UC_ARM_REG_SP,self.stack)
        self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime['CoopShadowFlagsRead'],self.base+0xff00,count=10000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R0),0x13)
        self.assertEqual(tuple(self.cpu.reg_read(register) for register in registers),values)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0xf8000000,0xa8000000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_SP),self.stack)


if __name__=='__main__':unittest.main()
