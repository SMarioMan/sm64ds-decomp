"""Execute native particle setup against Rainbow Ride's fragmented heap.

The private capture is an isolated ARM fixture, never live game state.
"""
import struct
import unittest
from unicorn.arm_const import UC_ARM_REG_R3
from test_particle_heap import HeapHarness,NativeAllocationFailure


class ParticleSegmentTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_PARTICLE_SEGMENT_FIXTURE'
    default_fixture=('/workspace/runtime/closed-entry-stage25-matrix/cycle-03/'
                     'diagnostic-transition-native-crash-0')

    def setup_native_manager(self,size=0x8c00,systems=40,particles=256):
        pool=self.call('CoopAllocateParticlePool',size)
        self.write(0x0209ee80,pool)
        self.write(0x0209ee78,pool)
        self.write(0x0209ee7c,pool+size)
        self.cpu.reg_write(UC_ARM_REG_R3,0x1a)
        self.write(0x023fc000,0x3e)
        manager=self.call(self.game['func_0204a4c8'],
                          self.runtime['CoopAllocateParticleChunk'],systems,particles)
        self.assertEqual(self.word(manager+0x10),systems)
        self.assertEqual(self.word(manager+0x18),particles)
        self.call(self.game['func_0204a17c'],manager,self.game['data_02075f14'])
        # Native reserve size is also a physical memory budget. Segment tails
        # and protected arrays must not silently multiply that reservation.
        count=self.word(self.runtime['coopParticleSegmentCount'])
        base=self.runtime['coopParticleSegments']
        capacity=sum(self.word(base+i*16+12)-self.word(base+i*16+4)
                     for i in range(count))
        self.assertLessEqual(capacity,size)
        return pool,manager

    def test_original_full_reserve_fails_despite_sufficient_combined_space(self):
        sizes=(self.largest(self.root),self.largest(self.game_heap))
        self.assertTrue(all(size<0x8c00 for size in sizes))
        self.assertGreaterEqual(sum(sizes),0x8c00)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory13operator_new2Ej'],0x8c00)

    def test_native_full_manager_and_resource_parser_fit(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        pool,manager=self.setup_native_manager()
        self.assertGreaterEqual(self.word(self.runtime['coopParticleSegmentCount']),1)
        self.assertEqual(self.word(self.runtime['coopParticleSplitFallbacks']),1)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_native_bowser_counts_and_resource_parser_fit(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        pool,manager=self.setup_native_manager(0xa800,64,320)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_repeated_native_setup_and_cleanup_does_not_leak(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            pool,manager=self.setup_native_manager()
            self.call('CoopFreeParticlePool',pool)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertEqual(self.word(self.runtime['coopParticleSplitFallbacks']),8)

    def test_cleanup_keeps_all_segment_owners_after_policy_shutdown(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        pool,manager=self.setup_native_manager()
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopFreeParticlePool',pool)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_oversized_chunk_fails_before_overwriting_a_segment(self):
        pool=self.call('CoopAllocateParticlePool',0x8c00)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocateParticleChunk',0x8c04)
        self.call('CoopFreeParticlePool',pool)


class ParticleGuestFragmentTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_PARTICLE_GUEST_FRAGMENT_FIXTURE'
    default_fixture=('/workspace/runtime/streamed-narc-rainbow-inspection/'
                     'load-failed-1')
    setup_native_manager=ParticleSegmentTests.setup_native_manager

    def test_two_largest_blocks_underestimate_available_guest_memory(self):
        self.assertLess(self.largest(self.root)+self.largest(self.game_heap),0x8c00)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory13operator_new2Ej'],0x8c00)

    def test_fragmented_guest_rejects_an_array_without_corrupting_heaps(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            # The 10272-byte resource array cannot fit after the 17408-byte
            # particle array, despite enough aggregate free space. Production
            # must reserve its arena earlier; splitting an individual array
            # would break the native manager's contiguous indexing.
            with self.assertRaises(NativeAllocationFailure):
                self.setup_native_manager()
            pool=self.word(self.runtime['coopParticlePool'])
            self.assertTrue(self.intact(self.root))
            self.assertTrue(self.intact(self.game_heap))
            self.call('CoopFreeParticlePool',pool)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)


if __name__=='__main__':unittest.main()
