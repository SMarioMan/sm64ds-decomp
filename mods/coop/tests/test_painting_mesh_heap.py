"""Execute the native painting allocation and cleanup from the stage13 crash.

The captured RAM is a private Unicorn mapping. The native allocator, archive
unmount and mesh cleanup execute without replacing those callees.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness,NativeAllocationFailure


class PaintingMeshHeapTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_PAINTING_HEAP_FIXTURE'
    default_fixture=('/workspace/runtime/castle-owner-stage1-through40-wireless/'
                     'cycle-12/diagnostic-transition-native-crash-1')

    def test_original_native_mesh_allocation_reproduces_the_failure(self):
        self.assertLess(self.largest(self.root),9600)
        self.assertGreaterEqual(self.largest(self.game_heap),9600)
        self.assertNotEqual(self.word(0x0208ecf4),0)
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['_ZN6Memory13operator_new2Ej'],9600)

    def test_native_mesh_cells_and_cleanup_keep_their_original_root_owner(self):
        actor=0x0215ec00 # Captured daPicGate_c, 20x20 native cells.
        self.assertEqual(bytes(self.cpu.mem_read(actor+0x1b8,4)),b'\x90\x01\x14\x14')
        address=0x02126e10
        target=self.runtime['CoopAllocatePaintingMesh']
        self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))
        def finish(cpu,address,size,user):
            if address==0x02126e18:
                cpu.reg_write(UC_ARM_REG_PC,self.base+0xff00)
        self.cpu.hook_add(UC_HOOK_CODE,finish)
        self.cpu.reg_write(UC_ARM_REG_R4,actor)
        game_before=self.largest(self.game_heap)
        self.call(0x02126e00) # Retail size calculation, allocation, mCells store.
        cells=self.word(actor+0x1a0)
        self.assertNotEqual(cells,0)
        self.assertEqual(self.word(0x0208ecf4),0)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),1)
        self.assertEqual(self.largest(self.game_heap),game_before)
        pattern=bytes(range(256))*37+bytes(range(128)) # Exactly 9600 bytes.
        self.cpu.mem_write(cells,pattern)
        self.assertEqual(bytes(self.cpu.mem_read(cells,9600)),pattern)
        self.call(0x02126bfc,actor) # Original daPicGate_c::CleanupResources.
        if 'coopAnimationPrewarmStats' in self.runtime:
            # Optional owned poses may remain after native mesh cleanup.
            # Their explicit cache teardown must restore the original block.
            self.assertEqual(self.word(self.runtime['coopAnimationPrewarmStats']+12),2)
            self.call('CoopFlushAnimationReadCache')
        if 'coopPackedAnimationStats' in self.runtime:
            self.assertEqual(self.word(self.runtime['coopPackedAnimationStats']+4),1)
            self.call('CoopFlushAnimationReadCache')
        self.assertEqual(self.largest(self.root),321328)
        self.assertEqual(self.largest(self.game_heap),game_before)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))

    def test_cache_is_retained_when_the_mesh_already_fits(self):
        archive=self.word(0x0208ecf4)
        before=self.largest(self.root)
        mesh=self.call('CoopAllocatePaintingMesh',24)
        self.assertEqual(self.word(0x0208ecf4),archive)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),0)
        self.call(self.game['func_0203cbc0'],mesh)
        self.assertEqual(self.largest(self.root),before)

    def test_offline_failure_does_not_change_native_cache_lifetime(self):
        self.write(0x0209fc68,0)
        archive=self.word(0x0208ecf4)
        with self.assertRaises(NativeAllocationFailure):
            self.call('CoopAllocatePaintingMesh',9600)
        self.assertEqual(self.word(0x0208ecf4),archive)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),0)

    def test_non_root_allocations_keep_their_native_heap_and_the_cache(self):
        archive=self.word(0x0208ecf4)
        before=self.largest(self.game_heap)
        self.write(0x020a0ea0,self.game_heap)
        mesh=self.call('CoopAllocatePaintingMesh',9600)
        self.assertEqual(self.word(0x0208ecf4),archive)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),0)
        self.call(self.game['func_0203cbc0'],mesh)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def patch_resident_overlays(self):
        self.write(self.runtime['coopEntryRetired'],1)
        ignored={self.runtime['CoopOriginalLoadLevelOverlays'],
                 self.game['_ZN4CP1514FlushDataCacheEv'],
                 self.game['_ZN4CP1514FlushDataCacheEjj'],
                 self.game['_ZN4CP1526InvalidateInstructionCacheEjj']}
        def dependencies(cpu,address,size,user):
            if address in ignored:
                cpu.reg_write(UC_ARM_REG_R0,0)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,dependencies)
        self.call('CoopLoadLevelOverlays',13)

    def test_patch_matches_only_the_loaded_native_painting_code(self):
        self.patch_resident_overlays()
        address=0x02126e10
        expected=0xeb000000|(((self.runtime['CoopAllocatePaintingMesh']-address-8)>>2)&0xffffff)
        self.assertEqual(self.word(address),expected)

    def test_another_overlay_at_the_same_address_is_not_patched(self):
        self.write(0x02126e08,0xe3a00000)
        before=bytes(self.cpu.mem_read(0x02126e08,16))
        self.patch_resident_overlays()
        self.assertEqual(bytes(self.cpu.mem_read(0x02126e08,16)),before)


if __name__=='__main__':unittest.main()
