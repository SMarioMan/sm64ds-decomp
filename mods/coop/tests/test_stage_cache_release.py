"""Native archive teardown and copied-resource lifetime in a private ARM heap.

Only skybox rendering is stubbed. The native shared loader, decompressor,
archive unmount and heap operations execute; no running emulator is modified.
"""
import unittest
import ndspy.narc
import ndspy.lz10
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_R0
from test_particle_heap import HeapHarness


class StageCacheReleaseTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.table=self.game['data_0208ecf4']
        self.archive=self.word(self.table)
        self.assertNotEqual(self.archive,0)
        self.skybox_calls=0
        self.cache_at_skybox=[]
        def render(cpu,address,size,user):
            if address==self.runtime['CoopOriginalLoadSkybox']:
                self.skybox_calls+=1
                self.cache_at_skybox.append(self.word(self.table))
            elif address!=self.game['_ZN4CP1514FlushDataCacheEjj']:return
            cpu.reg_write(UC_ARM_REG_R0,0)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,render)

    def test_native_cache_is_released_before_skybox_loading(self):
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.cache_at_skybox,[0])
        if 'coopAnimationPrewarmStats' in self.runtime or 'coopPackedAnimationStats' in self.runtime:
            self.call('CoopFlushAnimationReadCache')
        self.assertGreaterEqual(self.largest(self.root),321224)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),1)
        self.assertTrue(self.intact(self.root))

    def test_loaded_member_survives_reuse_of_the_native_archive_allocation(self):
        arc=ndspy.narc.NARC(self.stock.files[self.stock.filenames.idOf('ARCHIVE/arc0.narc')])
        member,expected=next((i,ndspy.lz10.decompress(data[4:]))
            for i,data in enumerate(arc.files)
            if data[:4]==b'LZ77' and 8<int.from_bytes(data[5:8],'little')<=4096
            and not int.from_bytes(data[5:8],'little')%2)
        handle=0x023f0000
        self.write(handle,0x8000+member)
        self.write(handle+4,0)
        result=self.call(self.game['_ZN13SharedFilePtr8LoadFileEv'],handle)
        self.assertEqual(bytes(self.cpu.mem_read(result,len(expected))),expected)
        cache_bytes=self.word(self.archive-12)
        self.assertFalse(self.archive<=result<self.archive+cache_bytes)
        self.call('CoopLoadSkybox',0)
        if 'coopAnimationPrewarmStats' in self.runtime or 'coopPackedAnimationStats' in self.runtime:
            self.call('CoopFlushAnimationReadCache')
        reused=self.call(self.game['_ZN6Memory8AllocateEj'],cache_bytes)
        self.assertEqual(reused,self.archive)
        self.cpu.mem_write(reused,bytes(cache_bytes))
        self.assertEqual(bytes(self.cpu.mem_read(result,len(expected))),expected)
        self.call(self.game['_ZN6Memory10DeallocateEPv'],reused)
        self.call(self.game['_ZN13SharedFilePtr7ReleaseEv'],handle)
        self.assertTrue(self.intact(self.root))

    def test_later_member_resolution_does_not_reload_the_whole_archive(self):
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.call('CoopResolveFile',0x8000),0)
        self.assertEqual(self.word(self.table),0)
        before=self.largest(self.root)
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),1)
        self.assertEqual(self.largest(self.root),before)
        self.assertEqual(self.skybox_calls,2)

    def test_offline_skybox_keeps_the_native_cache(self):
        before=self.largest(self.root)
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.cache_at_skybox,[self.archive])
        self.assertEqual(self.largest(self.root),before)
        self.assertEqual(self.word(self.runtime['coopStageCacheEvictions']),0)


class AnimationPrewarmTests(StageCacheReleaseTests):
    def setUp(self):
        super().setUp()
        if 'coopAnimationPrewarmStats' not in self.runtime:
            self.skipTest('requires --experimental-animation-prewarm')

    def stats(self):
        return tuple(self.word(self.runtime['coopAnimationPrewarmStats']+i*4) for i in range(5))

    def cached(self):
        result={}
        for i in range(32):
            row=self.runtime['coopAnimationReadEntries']+i*24
            data=self.word(row+16)
            if data:
                self.assertEqual(self.word(row+20),self.word(0x020a0e9c))
                result[self.word(row)]=bytes(self.cpu.mem_read(data,self.word(row+4)))
        return result

    def test_exact_original_idle_and_walk_bytes_survive_source_release(self):
        before_game=self.largest(self.game_heap)
        arc=ndspy.narc.NARC(self.stock.files[self.stock.filenames.idOf('ARCHIVE/arc0.narc')])
        index=self.runtime['coopNarcIndex']
        extents=index+self.word(index+12);top=self.word(index+8)
        expected={top+self.word(extents+i*8):bytes(arc.files[i]) for i in (80,81)}
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.cache_at_skybox,[0])
        self.assertEqual(self.stats(),(1,0,sum(map(len,expected.values())),2,0))
        self.assertEqual(self.cached(),expected)
        # The complete original GAME scratch allocation has been returned.
        self.assertEqual(self.largest(self.game_heap),before_game)
        # Repeated boundary calls neither allocate nor recopy an absent source.
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.stats()[0],1)
        self.call('CoopFlushAnimationReadCache')
        self.assertEqual(self.cached(),{})
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_game_pressure_unmounts_without_scratch_or_fatal_allocation(self):
        ballast=[];before=self.largest(self.game_heap)
        for _ in range(128):
            available=self.largest(self.game_heap)
            if available<9652:break
            pointer=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.game_heap,available-128,4)
            self.assertTrue(pointer);ballast.append(pointer)
        self.assertLess(self.largest(self.game_heap),9652)
        self.call('CoopLoadSkybox',0)
        self.assertEqual(self.stats(),(1,1,0,0,0))
        self.assertEqual(self.cached(),{})
        self.assertEqual(self.cache_at_skybox,[0])
        for pointer in reversed(ballast):
            self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,pointer)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_missing_root_cache_owner_releases_scratch_and_native_source(self):
        before=self.largest(self.game_heap);root=self.word(0x020a0e9c)
        self.write(0x020a0e9c,0)
        self.call('CoopLoadSkybox',0)
        self.write(0x020a0e9c,root)
        self.assertEqual(self.stats(),(1,0,9649,0,1))
        self.assertEqual(self.cached(),{})
        self.assertEqual(self.cache_at_skybox,[0])
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))


if __name__=='__main__':unittest.main()
