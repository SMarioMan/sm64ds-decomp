"""ARM checks of the plain LoadFile failure captured on HMC entry.

This private RAM/DTCM fixture is isolated from every live wireless test.
"""
import unittest
from test_particle_heap import HeapHarness, NativeAllocationFailure


class RawResourceHeapTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_RAW_RESOURCE_HEAP_FIXTURE'
    default_fixture=('/workspace/runtime/resource-owner-hmc-matrix/'
                     'story-entry-failed-0')

    def test_original_map_result_allocation_reproduces_failure(self):
        self.assertLess(self.largest(self.root),17396)
        self.assertGreaterEqual(self.largest(self.game_heap),17396)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory8AllocateEj'],17396)

    def test_map_result_copy_and_owner_release(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        result=self.call('CoopAllocateResource',17396)
        scratch=0x02355ddc # Captured LoadFile scratch pointer on this stack.
        expected=self.stock.files[0x55b]
        self.assertEqual(bytes(self.cpu.mem_read(scratch,len(expected))),expected)
        self.call(self.game['CpuCopy8'],scratch,result,len(expected))
        self.assertEqual(bytes(self.cpu.mem_read(result,len(expected))),expected)
        self.call('CoopFreeResource',result)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))

    def test_scratch_fallback_preserves_negative_alignment_and_free(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        scratch=self.call('CoopAllocateAlignedResource',17396,-4)
        self.assertEqual(scratch&3,0)
        self.call('CoopFreeResource',scratch)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_repeated_map_buffers_do_not_leak(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            result=self.call('CoopAllocateResource',17396)
            self.call('CoopFreeResource',result)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacksLive']),0)


if __name__=='__main__':unittest.main()
