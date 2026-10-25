"""Execute retail connection checks around asymmetric native loading phases."""
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness


class LoadingConnectionTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.cpu.mem_write(0x0209fc50,b'\x04')
        self.cpu.mem_write(0x0209fc54,b'\0')
        self.cpu.mem_write(0x0209fc58,b'\0')
        self.cpu.mem_write(0x020a0f1c,b'\x08\0')
        self.cpu.mem_write(0x020a104c,b'\0\x80')
        self.cpu.mem_write(0x020927ec,bytes(7*4))
        for slot in range(4):self.peer(slot,0x8000)
        self.failures=0
        def error(cpu,address,size,user):
            if address!=self.game['func_02030790']:return
            self.failures+=1
            self.write(0x0209fc68,6)
            cpu.reg_write(UC_ARM_REG_R0,0)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,error)

    def peer(self,slot,flags):
        self.cpu.mem_write(0x020a1160+slot*36,flags.to_bytes(2,'little'))

    def test_peer_loading_allows_only_the_transient_wing_checksum_mismatch(self):
        self.peer(0,0xc000)
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,0)
        self.assertEqual(self.word(0x0209fc68),4)
        self.assertEqual(self.word(self.runtime['coopLoadingChecksumGraceClears']),1)
        self.assertEqual(bytes(self.cpu.mem_read(0x020a0f1c,2)),b'\0\0')

    def test_local_loading_has_the_same_transition_grace(self):
        self.cpu.mem_write(0x020a104c,b'\0\xc0')
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,0)

    def test_checksum_mismatch_remains_fatal_during_normal_gameplay(self):
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,1)
        self.assertEqual(self.word(self.runtime['coopLoadingChecksumGraceClears']),0)

    def test_inactive_peer_loading_bits_do_not_suppress_a_gameplay_failure(self):
        self.peer(1,0x4000)
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,1)

    def test_radio_and_timeout_errors_remain_fatal_while_loading(self):
        self.peer(0,0xc000)
        for flags in (1,4,0x80,9,0x88):
            with self.subTest(flags=flags):
                self.failures=0
                self.write(0x0209fc68,4)
                self.cpu.mem_write(0x020a0f1c,flags.to_bytes(2,'little'))
                self.call('CoopConnectionUpdate')
                self.assertEqual(self.failures,1)

    def test_membership_loss_remains_fatal_while_loading(self):
        self.peer(0,0xc000)
        self.cpu.mem_write(0x0209fc54,b'\x01')
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,1)

    def test_disabled_coop_preserves_the_original_checksum_failure(self):
        self.write(self.runtime['coopEnabled'],0)
        self.peer(0,0xc000)
        self.call('CoopConnectionUpdate')
        self.assertEqual(self.failures,1)

    def test_stage_loading_disconnect_starts_the_existing_error_cleanup(self):
        self.write(0x0209fc68,6)
        reached=[]
        def stop(cpu,address,size,user):
            if address==self.game['func_02030a78']:
                reached.append(address)
                cpu.reg_write(UC_ARM_REG_PC,self.base+0xff00)
        self.cpu.hook_add(UC_HOOK_CODE,stop)
        self.call('CoopStageInit',0x023f0000)
        self.assertEqual(reached,[self.game['func_02030a78']])
        self.assertEqual(self.word(self.runtime['coopEnabled']),0)


if __name__=='__main__':unittest.main()
