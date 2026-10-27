"""Keep native coin AI while restoring its local visual floor-probe decision.

The captured actors, native coin Behavior and ray queries run privately in ARM.
The reference changes only the isolated flags-load result at the visual gate.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R5,UC_ARM_REG_R12,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_LR)
from test_line_broadphase import LineHardwareHarness


class CoinShadowProbeTests(LineHardwareHarness,unittest.TestCase):
    fixture_variable='COOP_COIN_SHADOW_FIXTURE'

    def setUp(self):
        super().setUp()
        if 'CoopCoinShadowProbeRead' not in self.runtime:
            self.skipTest('requires --experimental-local-coin-shadows')
        self.reference=False
        def flags(cpu,address,size,user):
            if self.reference and address==0x020b10f4:
                actor=cpu.reg_read(UC_ARM_REG_R5)
                value=self.word(actor+0xb0)|(self.word(self.runtime['coopBehaviorVisibility'])&8)
                cpu.reg_write(UC_ARM_REG_R0,value)
        self.cpu.hook_add(UC_HOOK_CODE,flags)
        self.actor=0x023f2000
        self.write(self.actor+0xb0,3)
        self.write(self.runtime['coopBehaviorActor'],self.actor)
        self.write(self.runtime['coopBehaviorVisibility'],8)

    def install(self,address,target):
        self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))
        self.cpu.ctl_remove_cache(address,address+4)

    def test_saved_local_offscreen_bit_and_actor_added_suppression_are_retained(self):
        self.assertEqual(self.call('CoopCoinShadowProbeFlags',self.actor),11)
        self.write(self.runtime['coopBehaviorVisibility'],0)
        self.assertEqual(self.call('CoopCoinShadowProbeFlags',self.actor),3)
        self.write(self.actor+0xb0,11)
        self.assertEqual(self.call('CoopCoinShadowProbeFlags',self.actor),11)
        self.assertEqual(self.word(self.actor+0xb0),11)

    def test_disabled_offline_foreign_context_do_not_add_local_visibility(self):
        for enabled,net,actor in ((0,4,self.actor),(1,0,self.actor),(1,4,self.actor+16)):
            self.write(self.runtime['coopEnabled'],enabled);self.write(0x0209fc68,net)
            self.write(self.runtime['coopBehaviorActor'],actor)
            self.assertEqual(self.call('CoopCoinShadowProbeFlags',self.actor),3)

    def test_read_adapter_preserves_registers_flags_and_stack(self):
        self.cpu.reg_write(UC_ARM_REG_R5,self.actor)
        regs=(UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12)
        values=(0x12345678,0xabcdef01,0x98765432,0xfeedbeef)
        for r,v in zip(regs,values):self.cpu.reg_write(r,v)
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xa80000df)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
        self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime['CoopCoinShadowProbeRead'],self.base+0xff00,count=10000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R0),11)
        self.assertEqual([self.cpu.reg_read(r) for r in regs],list(values))
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R5),self.actor)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_SP),0x023fc000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0xf8000000,0xa8000000)

    def run_coins(self,reference=False,optimized=False,visible=False,then_visible=False):
        node=self.word(0x0209b468);actors=[]
        while node:
            actor=self.word(node+8)
            if int.from_bytes(self.cpu.mem_read(actor+12,2),'little') in (288,289,290):actors.append(actor)
            node=self.word(node+4)
        self.assertGreaterEqual(len(actors),60)
        ram=bytes(self.cpu.mem_read(0x02000000,0x400000));results=[]
        start=self.instructions;reads=self.sqrt_reads
        for actor in actors:
            self.cpu.mem_write(0x02000000,ram)
            if optimized:self.install(0x020b10f0,self.runtime['CoopCoinShadowProbeRead'])
            else:
                self.write(0x020b10f0,0xe59500b0)
                self.cpu.ctl_remove_cache(0x020b10f0,0x020b10f4)
            for address in (0x02010ba4,0x02010bf0):self.install(address,self.runtime['CoopShadowFlagsRead'])
            flags=self.word(actor+0xb0);self.write(actor+0xb0,flags&~0x38)
            self.write(self.runtime['coopBehaviorActor'],actor)
            self.write(self.runtime['coopBehaviorVisibility'],0 if visible else flags&0x38)
            self.reference=reference
            self.call(0x020b2324,actor)
            if then_visible:
                self.write(self.runtime['coopBehaviorVisibility'],0)
                self.call(0x020b2324,actor)
            results.append(bytes(self.cpu.mem_read(actor,0x3b4)))
        self.cpu.mem_write(0x02000000,ram)
        return results,self.instructions-start,self.sqrt_reads-reads

    def test_full_visible_coin_behavior_preserves_all_actor_bytes_and_native_queries(self):
        native=self.run_coins(visible=True)
        optimized=self.run_coins(optimized=True,visible=True)
        self.assertEqual(optimized[0],native[0]);self.assertEqual(optimized[2],native[2])

    def test_captured_offscreen_coins_match_native_local_visual_gate_and_gameplay(self):
        native=self.run_coins()
        reference=self.run_coins(reference=True)
        optimized=self.run_coins(optimized=True)
        self.assertEqual(optimized[0],reference[0])
        # In this captured BoB cohort the redundant far probes all miss. Thus
        # complete actor bytes, including AI, colliders, matrices and floor
        # state, also match the earlier neutralized-visibility implementation.
        self.assertEqual(optimized[0],native[0])
        self.assertLess(optimized[1],native[1]);self.assertLess(optimized[2],native[2])
        print('Coin local shadow probes: instructions/sqrt:',native[1:],optimized[1:])

    def test_becoming_visible_resumes_the_original_probe_and_complete_behavior(self):
        reference=self.run_coins(reference=True,then_visible=True)
        optimized=self.run_coins(optimized=True,then_visible=True)
        self.assertEqual(optimized[0],reference[0]);self.assertEqual(optimized[2],reference[2])
