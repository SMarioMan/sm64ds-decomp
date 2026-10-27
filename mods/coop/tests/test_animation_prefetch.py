"""Optional loading-only pose reads with native read/cursor/close and heaps.

Only the physical file-open/range selection and ROM read backend are adapted;
all mappings are private Unicorn fixtures, never a running wireless console.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_CPSR
from test_animation_read_cache import AnimationReadCacheHarness


class AnimationPrefetchTests(AnimationReadCacheHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopPrefetchAnimationReads' not in self.runtime:
            self.skipTest('requires --experimental-animation-prefetch')
        self.write(self.runtime['coopStageLoading'],2)
        self.write(self.runtime['coopSceneInitializing'],1)
        self.opens=[];self.closes=[];self.flushes=[]
        self.open_failure=False
        table=self.runtime['coopAnimationPrefetchIndex']
        self.expected=[struct.unpack('<3I',self.cpu.mem_read(table+4+i*12,12))
                       for i in range(self.word(table))]
        def adapter(cpu,address,size,user):
            args=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            if address==self.game['func_0205d5e8']:
                f,archive,top,end=args;file_id=self.word(cpu.reg_read(UC_ARM_REG_SP))
                self.opens.append((top,end-top,file_id))
                if not self.open_failure:
                    for offset,value in ((8,archive),(12,0x10),(20,0),(28,file_id),(32,top),(36,end),(40,top)):
                        self.write(f+offset,value)
                result=int(not self.open_failure)
            elif address==self.game['FS_CloseFile']:
                self.closes.append(self.word(args[0]+32));return # Run native close.
            elif address==self.game['_ZN4CP1527FlushAndInvalidateDataCacheEjj']:
                self.assertEqual(cpu.reg_read(UC_ARM_REG_CPSR)&0x80,0)
                self.flushes.append((args[0],args[1]));result=0
            else:return
            cpu.reg_write(UC_ARM_REG_R0,result)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,adapter)

    def prefetch_stats(self):
        return struct.unpack('<8I',self.cpu.mem_read(self.runtime['coopAnimationPrefetchStats'],32))

    def test_every_pose_is_read_once_and_second_loading_pass_reuses_exact_cache(self):
        before_game=self.largest(self.game_heap)
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(len(self.expected),14)
        self.assertEqual(self.opens,self.expected)
        self.assertEqual(self.closes,[x[0] for x in self.expected])
        self.assertEqual(self.prefetch_stats(),(1,0,14,14,0,0,0,0))
        self.assertEqual(len(self.reads),14)
        self.assertEqual([size for address,size in self.flushes],[x[1] for x in self.expected])
        self.assertTrue(all(not address%32 for address,size in self.flushes))
        self.assertEqual(self.read_irq,[0]*14)
        self.assertEqual(self.largest(self.game_heap),before_game)
        for name in ('data/player/Y_wait.bca','data/player/Y_walk.bca',
                     'data/player/Y_sleep_start.bca','data/player/Y_sleep_wait.bca',
                     'data/player/Y_sleep_end.bca','data/player/Y_sleep_to_lie.bca',
                     'data/player/cold_wait_start.bca','data/player/cold_wait.bca',
                     'data/player/cold_wait_end.bca','data/player/swim_in.bca',
                     'data/player/swim_wait.bca','data/player/paddle_1.bca',
                     'data/player/paddle_2.bca','data/player/paddle_end.bca'):
            self.load(name)
        self.assertEqual(len(self.reads),14) # Exact bytes and native cursors, no IO.
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(2,14,14,14,0,0,0,0))
        self.assertEqual(len(self.opens),14)
        self.invoke('CoopFlushAnimationReadCache')
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_gameplay_offline_foreign_thread_or_active_read_never_prefetches(self):
        for address,value in ((self.runtime['coopStageLoading'],0),(self.runtime['coopEnabled'],0),
                              (0x0209fc68,0),(0x020a613c,0),(self.runtime['coopFileWaiting'],1)):
            old=self.word(address);self.write(address,value)
            self.invoke('CoopPrefetchAnimationReads');self.write(address,old)
        self.assertEqual(self.opens,[]);self.assertEqual(self.prefetch_stats(),(0,)*8)

    def test_open_failures_do_not_read_close_or_leak_game_scratch(self):
        before=self.largest(self.game_heap);self.open_failure=True
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(1,0,0,0,14,0,0,0))
        self.assertEqual(self.reads,[]);self.assertEqual(self.closes,[])
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def test_short_reads_are_closed_without_storing_partial_poses(self):
        before=self.largest(self.game_heap);self.read_limit=1
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(1,0,14,0,0,14,0,0))
        self.assertEqual(len(self.closes),14)
        self.assertEqual(self.stats()[2],0)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def test_game_pressure_skips_optional_scratch_and_preserves_all_heap_capacity(self):
        before=self.largest(self.game_heap);ballast=[]
        for _ in range(128):
            available=self.largest(self.game_heap)
            if available<8192:break
            p=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.game_heap,available-128,4)
            self.assertTrue(p);ballast.append(p)
        self.assertLess(self.largest(self.game_heap),8192)
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(1,0,0,0,0,0,1,0));self.assertEqual(self.opens,[])
        for p in reversed(ballast):self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,p)
        self.assertEqual(self.largest(self.game_heap),before)
        self.assertTrue(self.intact(self.game_heap))

    def test_existing_idle_walk_cache_entries_do_not_issue_new_reads(self):
        self.load('data/player/Y_wait.bca');self.load('data/player/Y_walk.bca')
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(1,2,12,12,0,0,0,0))
        self.assertEqual(self.opens,self.expected[2:])
        self.assertEqual(self.stats()[2],14)

    def test_unready_or_error_archive_never_opens_optional_files(self):
        address=self.word(0x0209d3b4)+16;old=self.word(address)
        for flags in (0,0x22,0x42,0x82):
            self.write(address,flags);self.invoke('CoopPrefetchAnimationReads')
        self.write(address,old)
        self.assertEqual(self.opens,[]);self.assertEqual(self.prefetch_stats(),(0,)*8)

    def test_root_pressure_skips_reads_that_cannot_be_stored(self):
        before=(self.largest(self.root),self.largest(self.game_heap));ballast=[]
        for _ in range(128):
            available=self.largest(self.root)
            if available<512:break
            p=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,available-128,4)
            self.assertTrue(p);ballast.append(p)
        self.assertLess(self.largest(self.root),512)
        self.invoke('CoopPrefetchAnimationReads')
        self.assertEqual(self.prefetch_stats(),(1,0,0,0,0,0,0,14));self.assertEqual(self.opens,[])
        for p in reversed(ballast):self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,p)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))


if __name__=='__main__':unittest.main()
