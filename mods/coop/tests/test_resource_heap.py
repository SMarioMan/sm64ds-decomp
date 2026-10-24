"""Compiled ARM shared-file allocation checks using the HMC guest failure.

Private captured RAM is an isolated unit fixture. The native allocator runs
unchanged; none of these checks writes to a running multiplayer session.
"""
import unittest

from test_particle_heap import HeapHarness, NativeAllocationFailure


class ResourceHeapTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_RESOURCE_HEAP_FIXTURE'
    default_fixture=('/workspace/runtime/particle-four-player-matrix/cycle-06/'
                     'diagnostic-transition-connection-failed-1')

    def aligned_largest(self,heap,align):
        return self.call(self.game['_ZN22ExpandingHeapAllocator18MaxAllocatableSizeEi'],
                         self.word(heap+0x14),align)

    def test_original_raw_file_request_reproduces_guest_failure(self):
        self.assertLess(self.aligned_largest(self.root,32),6532)
        self.assertGreaterEqual(self.aligned_largest(self.game_heap,32),6532)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory8AllocateEji'],6532,32)

    def test_native_load_allocation_sequence_and_full_particle_pool_fit(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        # The real SharedFilePtr::Load path: raw file, compressed scratch,
        # release raw, decompressed model, release scratch. Counts/sizes are
        # from the unchanged file 0x300 and its native LZ header.
        raw=self.call('CoopAllocateAlignedResource',6532,32)
        self.assertEqual(raw&31,0)
        scratch=self.call('CoopAllocateResource',6528)
        self.call('CoopFreeResource',raw)
        model=self.call('CoopAllocateResource',7556)
        self.call('CoopFreeResource',scratch)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacksLive']),1)
        pool=self.call('CoopAllocateParticlePool',0x8c00)
        self.assertNotEqual(pool,0)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))
        self.call('CoopFreeResource',model)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacksLive']),0)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_native_trim_of_fallback_model_loses_game_heap_space(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        model=self.call('CoopAllocateResource',7556)
        self.write(model+14*4,4096)
        self.assertEqual(self.call(self.game['func_02017060'],model),4096)
        self.call('CoopFreeResource',model)
        # Native trim returns success, but inserts the freed model tail into
        # ROOT rather than GAME. Its apparent success hid a persistent leak.
        self.assertLess(self.largest(self.game_heap),before[1])

    def test_model_trim_uses_owning_game_heap_and_preserves_contents(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        model=self.call('CoopAllocateResource',7556)
        self.write(model+14*4,4096) # Native BMD retained-size field.
        self.write(model,0x12345678)
        self.write(self.runtime['coopEnabled'],0) # Ownership outlives policy.
        self.assertEqual(self.call('CoopTrimResourceModel',model),4096)
        self.assertEqual(self.word(model),0x12345678)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))
        self.call('CoopFreeResource',model)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_model_trim_preserves_native_root_path_and_null(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        model=self.call('CoopAllocateResource',1024)
        self.write(model+14*4,512)
        self.assertEqual(self.call('CoopTrimResourceModel',model),512)
        self.call('CoopFreeResource',model)
        self.assertEqual(self.call('CoopTrimResourceModel',0),0)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_requested_alignment_is_checked_before_allocating(self):
        unaligned=self.largest(self.root)
        aligned=self.aligned_largest(self.root,32)
        self.assertGreater(unaligned,aligned)
        ptr=self.call('CoopAllocateAlignedResource',aligned+4,32)
        self.assertEqual(ptr&31,0)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacks']),1)
        self.call('CoopFreeResource',ptr)
        self.assertEqual(self.largest(self.root),unaligned)

    def test_cleanup_keeps_owner_after_coop_is_disabled(self):
        before=self.largest(self.game_heap)
        ptr=self.call('CoopAllocateAlignedResource',6532,32)
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopFreeResource',ptr)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacksLive']),0)
        self.assertTrue(self.intact(self.game_heap))

    def test_root_allocations_retain_native_cleanup(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        ptr=self.call('CoopAllocateAlignedResource',512,32)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacks']),0)
        self.call('CoopFreeResource',ptr)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_repeated_shared_files_do_not_leak(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            raw=self.call('CoopAllocateAlignedResource',6532,32)
            scratch=self.call('CoopAllocateResource',6528)
            self.call('CoopFreeResource',raw)
            model=self.call('CoopAllocateResource',7556)
            self.call('CoopFreeResource',scratch)
            self.call('CoopFreeResource',model)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
            self.assertEqual(self.word(self.runtime['coopResourceFallbacksLive']),0)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacks']),24)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacksPeak']),2)

    def test_actor_private_heap_behavior_is_unchanged(self):
        before=self.largest(self.game_heap)
        self.write(0x020a0ea0,self.game_heap)
        ptr=self.call('CoopAllocateAlignedResource',512,32)
        self.assertEqual(self.word(self.runtime['coopResourceFallbacks']),0)
        self.call('CoopFreeResource',ptr)
        self.assertEqual(self.largest(self.game_heap),before)

    def test_offline_load_preserves_native_failure(self):
        self.write(self.runtime['coopEnabled'],0)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateAlignedResource',6532,32)

    def test_high_end_module_allocation_can_shrink_without_moving(self):
        before=self.largest(self.game_heap)
        ptr=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.game_heap,0x4000,-32)
        self.assertEqual(ptr&31,0)
        pattern=bytes(range(256))*32
        self.cpu.mem_write(ptr,pattern)
        size=self.call(self.game['_ZN5mHeap6Heap_t10ReallocateEPvj'],self.game_heap,ptr,len(pattern))
        self.assertGreaterEqual(size,len(pattern))
        self.assertEqual(bytes(self.cpu.mem_read(ptr,len(pattern))),pattern)
        self.assertTrue(self.intact(self.game_heap))
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,ptr)
        self.assertEqual(self.largest(self.game_heap),before)


if __name__=='__main__':unittest.main()
