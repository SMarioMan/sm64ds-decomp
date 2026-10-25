"""Native ARM shutdown callbacks in an isolated failed-quit fixture.

SDK command submission is stubbed; callbacks run explicitly as private unit
fixtures. This is not packet injection or live wireless acceptance.
"""
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness


class NativeErrorScreen(Exception):
    pass


class WirelessTeardownTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_WIRELESS_TEARDOWN_FIXTURE'
    default_fixture=('/workspace/runtime/streamed-narc-normal-guest-star/'
                     'wireless-save-quit-failed-1')

    def setUp(self):
        super().setUp()
        self.scene=0x023f0000
        self.event=self.scene+0x100
        self.write(self.scene+12,1)
        self.write(self.runtime['coopTitleLoading'],1)
        self.write(self.runtime['coopMenuLoading'],5)
        self.write(0x020a0f94,4)
        self.submissions=[]
        self.result=2
        def sdk(cpu,address,size,user):
            if address==self.game['func_02062200']:
                # Mirror the installed branch at the SDK Reset entry point.
                cpu.reg_write(UC_ARM_REG_PC,self.runtime['CoopWirelessReset'])
                return
            commands={self.runtime['CoopOriginalWirelessReset']:'Reset',
                      self.game['func_020622a8']:'Disable',
                      self.game['func_02062338']:'End'}
            if address in commands:
                self.submissions.append((commands[address],cpu.reg_read(UC_ARM_REG_R0)))
                cpu.reg_write(UC_ARM_REG_R0,self.result)
            elif address in (self.game['func_02040aa4'],self.game['func_0201ffcc']):
                cpu.reg_write(UC_ARM_REG_R0,0)
            elif address==self.game['func_02030500']:
                raise NativeErrorScreen()
            else:return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,sdk)

    def test_native_reset_disable_end_chain_is_submitted_once(self):
        self.assertEqual(self.call('CoopSceneBeforeInit',self.scene),0)
        self.assertEqual([name for name,cb in self.submissions],['Reset'])
        # Keep calling the real scene hook before each asynchronous completion.
        # It must not enqueue another Reset during any native teardown phase.
        for phase in ('Reset','Disable','End'):
            for _ in range(4):self.call('CoopSceneBeforeInit',self.scene)
            self.assertEqual(self.submissions[-1][0],phase)
            callback=self.submissions[-1][1]
            self.write(self.event,0)
            self.call(callback,self.event)
        self.assertEqual([name for name,cb in self.submissions],['Reset','Disable','End'])
        self.assertEqual(self.word(0x020a0f94),0)
        self.assertEqual(self.word(0x020a0f5c),0)

    def test_sdk_submission_error_does_not_claim_an_async_reset(self):
        self.result=3
        self.call('CoopSceneBeforeInit',self.scene)
        self.assertEqual(self.word(self.runtime['coopTitleRadioResetPending']),0)
        self.assertEqual(self.word(0x020a0f94),1) # Native failure state.

    def test_non_coop_reset_retains_the_native_callback(self):
        self.write(self.runtime['coopEnabled'],0)
        callback=self.game['func_020402a0']
        self.assertEqual(self.call('CoopWirelessReset',callback),2)
        self.assertEqual(self.submissions,[('Reset',callback)])
        self.assertEqual(self.word(self.runtime['coopTitleRadioResetPending']),0)

    def test_native_reset_failure_ends_the_wait_in_the_error_screen(self):
        self.result=3
        self.call('CoopSceneBeforeInit',self.scene)
        with self.assertRaises(NativeErrorScreen):
            self.call('CoopSceneBeforeInit',self.scene)
        self.assertEqual(self.word(self.runtime['coopEnabled']),0)
        self.assertEqual(self.word(self.runtime['coopSessionEnded']),3)


if __name__=='__main__':unittest.main()
