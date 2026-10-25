"""Experimental pacing against the actual ARM reset block and VBlank handler.

Private isolated fixture only. These tests do not modify a live console or
replace wireless input, and do not establish physical performance acceptance.
"""
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_CPSR,UC_ARM_REG_SP
from test_particle_heap import HeapHarness


class WirelessFrameClockTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopResetFrameClock' not in self.runtime:
            self.skipTest('requires --experimental-wireless-frame-clock build')
        for start,size in ((0x02019914,0x14),(0x0201a534,0x98)):
            section=next(s for s in self.main.sections if s.ramAddress<=start and
                         start+size<=s.ramAddress+len(s.data))
            self.cpu.mem_write(start,bytes(section.data[start-section.ramAddress:start-section.ramAddress+size]))
        # The original block's PC-relative literals live outside that block.
        self.write(0x02019994,0x0209ee90)
        self.write(0x02019998,0x0209d514)
        self.write(0x02019924,0x0b000000|(((self.runtime['CoopResetFrameClock']-0x02019924-8)>>2)&0xffffff))
        for name in ('coopStageLoading','coopMenuLoading','coopSceneInitializing',
                     'coopTitleLoading','coopSessionEnded'):
            self.write(self.runtime[name],0)
        self.write(0x0209ef98,0)
        self.cpu.mem_write(0x020a104c,b'\0\0')
        self.events=[]
        def native_callbacks(cpu,address,size,data):
            if address in (0x0205807c,0x02019144,0x02019100):
                self.events.append(address)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,native_callbacks)

    def reset_block(self):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xdf)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
        self.cpu.emu_start(0x02019914,0x02019928,count=10000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),0x02019928)

    def test_active_gameplay_keeps_radio_elapsed_time(self):
        self.write(0x0209d514,1)
        self.reset_block()
        self.assertEqual(self.word(0x0209d514),1)
        self.assertEqual(self.word(0x0209fc68),4)

    def test_loading_offline_teardown_and_scene_transitions_keep_original_reset(self):
        for name in ('coopEnabled','coopStageLoading','coopMenuLoading',
                     'coopSceneInitializing','coopTitleLoading','coopSessionEnded','NET','loading'):
            with self.subTest(name=name):
                address=0x0209fc68 if name=='NET' else 0x020a104c if name=='loading' else self.runtime[name]
                original=self.word(address)
                self.write(address,0 if name in ('coopEnabled','NET') else 0x4000 if name=='loading' else 1)
                self.write(0x0209d514,7)
                self.reset_block()
                self.assertEqual(self.word(0x0209d514),0)
                self.write(address,original)

    def test_native_flag_that_skips_reset_still_skips_the_hook(self):
        self.write(self.runtime['coopEnabled'],0)
        self.write(0x0209ef98,0x10)
        self.write(0x0209d514,7)
        self.reset_block()
        self.assertEqual(self.word(0x0209d514),7)

    def test_actual_irq_requires_the_budget_and_only_wakes_when_render_is_ready(self):
        self.write(0x0208ee44,2)
        self.write(0x0209d514,0)
        self.cpu.mem_write(0x0209d4f0,b'\1')
        self.call(0x0201a534)
        self.assertEqual(self.word(0x0209d514),1)
        self.assertNotIn(0x02019144,self.events)
        self.events.clear()
        self.call(0x0201a534)
        self.assertEqual(self.word(0x0209d514),0)
        self.assertEqual(self.events.count(0x02019144),1)
        self.assertEqual(self.events.count(0x0205807c),2)
        self.cpu.mem_write(0x0209d4f0,b'\0')
        self.write(0x0209d514,8)
        self.events.clear()
        self.call(0x0201a534)
        self.assertEqual(self.word(0x0209d514),9)
        self.assertNotIn(0x02019144,self.events)

    def test_long_radio_delay_does_not_generate_catch_up_simulation_ticks(self):
        self.write(0x0209d514,50)
        self.reset_block()
        self.assertEqual(self.word(0x0209d514),50)
        self.write(0x0208ee44,2)
        self.cpu.mem_write(0x0209d4f0,b'\1')
        self.call(0x0201a534)
        self.assertEqual(self.word(0x0209d514),0)
        self.assertEqual(self.events.count(0x02019144),1)


if __name__=='__main__':unittest.main()
