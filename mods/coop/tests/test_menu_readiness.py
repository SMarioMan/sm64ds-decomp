"""Retail pause-menu input gating in an isolated ARM fixture.

Only presentation callbacks are replaced; the actual PS_Update branch reads
native touch/cooldown fields. This never writes to a running wireless session.
"""
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_R0
from test_particle_heap import HeapHarness


class MenuReadinessTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        start=0x0202635c
        size=0x30ac
        section=next(s for s in self.main.sections if s.ramAddress<=start and
                     start+size<=s.ramAddress+len(s.data))
        self.cpu.mem_write(start,bytes(section.data[start-section.ramAddress:start-section.ramAddress+size]))
        for address in (0x0209f210,0x0209f2e4,0x0209f244,0x0209f2cc,
                        0x0209f23c,0x0209f22c,0x0209f300,0x0209f2e0):
            self.write(address,0)
        self.cpu.mem_write(0x0209f1ec,b'\3')
        self.cpu.mem_write(0x0209f248,b'\3')
        self.cpu.mem_write(self.game['gActivePlayerSlot'],b'\0')
        self.write(0x0208ee44,2)
        self.calls=[]
        def presentation(cpu,address,size,data):
            if address in (self.game['_ZN10dScStage_c17UpdateMenuButtonsEb'],
                           self.game['func_02012790'],
                           self.game['IsButtonInputValid']):
                self.calls.append(address)
                cpu.reg_write(UC_ARM_REG_R0,0)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,presentation)

    def touch(self,held):
        self.cpu.mem_write(self.game['gTouchHeld'],bytes((held,1,128,160)))

    def update(self):
        self.call(self.game['_ZN10dScStage_c9PS_UpdateEv'],0)

    def test_exit_touch_is_ignored_during_opening_cooldown(self):
        self.write(0x0209f300,10)
        self.touch(1)
        self.update()
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f1ec,1)),b'\3')
        self.assertEqual(self.calls,[])

    def test_fresh_exit_touch_after_readiness_enters_the_native_exit_action(self):
        self.touch(1)
        self.update()
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f1ec,1)),b'\x13')
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f22c,1)),b'\x10')
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f2e0,1)),b'\3')
        self.assertIn(self.game['func_02012790'],self.calls)


if __name__=='__main__':unittest.main()
