"""Native model-work pressure from the normal four-Yoshi12→13 failure.

Private captured RAM only. Native archive teardown, heap allocation, BMD
processing and model cleanup execute; no running emulator is modified.
"""
import unittest
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R6
from test_particle_heap import HeapHarness,NativeAllocationFailure


class ModelWorkHeapTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_MODEL_WORK_FIXTURE'
    default_fixture=('/workspace/runtime/lz-window-yoshi-performance/06-level-12/'
                     'diagnostic-transition-native-crash-1')

    def setUp(self):
        super().setUp()
        if 'CoopAllocateModelWork' not in self.runtime:
            self.skipTest('requires model-work pressure release')
        self.archive=self.word(0x0208ecf4)
        self.assertTrue(self.archive)
        self.model=0x0232bdfc # Owned ten-bone BMD saved by the native failing frame.
        self.assertLess(self.largest(self.root),1048)
        self.write(self.runtime['coopFileWaiting'],0)
        # Captured RAM contains0c52 hooks into its old runtime allocation.
        # Restore native heap entry instructions in this private mapping so
        # every allocation/cleanup below exercises retail heap code directly.
        for address in (self.game['_ZN5mHeap6Heap_t8AllocateEji'],0x0203c6bc,0x0203c568):
            section=next(s for s in self.main.sections
                         if s.ramAddress<=address< s.ramAddress+len(s.data))
            offset=address-section.ramAddress
            self.cpu.mem_write(address,bytes(section.data[offset:offset+8]))
        site=0x02016c20;target=self.runtime['CoopModelWorkRead']
        self.write(site,0xeb000000|(((target-site-8)>>2)&0xffffff))


    def test_captured_native_allocation_still_reproduces_original_failure(self):
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory13operator_new2Ej'],1048)

    def test_release_preserves_owned_bmd_and_native_heap_cleanup(self):
        before_game=self.largest(self.game_heap)
        before=bytes(self.cpu.mem_read(self.model,128))
        result=self.call('CoopAllocateModelWork',1048,self.model)
        self.assertTrue(result)
        self.assertEqual(self.word(0x0208ecf4),0)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),1)
        self.assertEqual(bytes(self.cpu.mem_read(self.model,128)),before)
        self.assertEqual(self.largest(self.game_heap),before_game)
        self.call(self.game['_ZN6Memory10DeallocateEPv'],result)
        if 'coopPackedAnimationStats' in self.runtime:
            self.assertEqual(self.word(self.runtime['coopPackedAnimationStats']+4),1)
        if 'coopAnimationPrewarmStats' in self.runtime or 'coopPackedAnimationStats' in self.runtime:
            self.call('CoopFlushAnimationReadCache')
        self.assertGreaterEqual(self.largest(self.root),321000)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_borrowed_narc_model_never_releases_its_source(self):
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateModelWork',1048,self.archive+0x100)
        self.assertEqual(self.word(0x0208ecf4),self.archive)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),0)

    def test_active_file_read_never_releases_its_source(self):
        self.write(self.runtime['coopFileWaiting'],1)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateModelWork',1048,self.model)
        self.assertEqual(self.word(0x0208ecf4),self.archive)

    def test_offline_pressure_keeps_original_failure_and_archive(self):
        self.write(self.runtime['coopEnabled'],0)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateModelWork',1048,self.model)
        self.assertEqual(self.word(0x0208ecf4),self.archive)

    def test_small_fitting_allocation_keeps_original_archive(self):
        available=self.largest(self.root);self.assertGreaterEqual(available,4)
        result=self.call('CoopAllocateModelWork',4,self.model)
        self.assertEqual(self.word(0x0208ecf4),self.archive)
        self.call(self.game['_ZN6Memory10DeallocateEPv'],result)
        self.assertEqual(self.largest(self.root),available)

    def test_game_heap_selection_is_preserved_without_source_release(self):
        before=self.largest(self.game_heap)
        self.write(self.game['_ZN6Memory14defaultHeapPtrE'],self.game_heap)
        result=self.call('CoopAllocateModelWork',1048,self.model)
        self.assertEqual(self.word(0x0208ecf4),self.archive)
        self.call(self.game['_ZN6Memory10DeallocateEPv'],result)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def test_bridge_passes_saved_bmd_and_preserves_argument_registers(self):
        self.cpu.reg_write(UC_ARM_REG_R6,self.model)
        self.cpu.reg_write(UC_ARM_REG_R3,0x12345678)
        result=self.call('CoopModelWorkRead',1048,0x23456789,0x3456789a)
        self.assertTrue(result)
        self.assertEqual(self.word(0x0208ecf4),0)
        for reg,value in ((UC_ARM_REG_R1,0x23456789),(UC_ARM_REG_R2,0x3456789a),
                          (UC_ARM_REG_R3,0x12345678),(UC_ARM_REG_R6,self.model)):
            self.assertEqual(self.cpu.reg_read(reg),value)

    def test_full_native_model_setup_and_cleanup_after_release(self):
        obj=0x023f0000
        self.cpu.mem_write(obj,bytes(0x80))
        self.call(self.game['_ZN17dExtSimpleModel_cC1Ev'],obj)
        self.cpu.reg_write(UC_ARM_REG_R3,0xffffffff)
        self.assertEqual(self.call(self.game['_ZN17dExtSimpleModel_c9DoSetFileEPcii'],obj,self.model,0),1)
        self.assertTrue(self.word(obj+0x4c))
        self.assertEqual(self.word(0x0208ecf4),0)
        self.call(self.game['_ZN17dExtSimpleModel_cD1Ev'],obj)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))


if __name__=='__main__':unittest.main()
