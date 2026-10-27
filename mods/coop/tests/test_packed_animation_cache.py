"""Adopt already-downloaded common animation bytes with native ownership/heap work.

Private captured ARM execution only. Native unmount, in-place copies, shrink,
read-hit cursor updates and eviction execute; no live wireless state is edited.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from test_animation_read_cache import AnimationReadCacheHarness


class PackedAnimationCacheTests(AnimationReadCacheHarness,unittest.TestCase):
    default_fixture='/workspace/runtime/hmc-wireless-load-inspection/hmc-load-0'

    def setUp(self):
        super().setUp()
        if 'coopPackedAnimationStats' not in self.runtime:
            self.skipTest('requires --experimental-packed-animation-cache')
        self.table=self.game['data_0208ecf4'];self.image=self.word(self.table)
        self.assertTrue(self.image)
        self.owner=self.word(self.table+4)
        self.assertEqual(self.owner,self.word(0x020a0e9c))
        self.allocator=self.word(self.owner+0x14)
        self.entries=self.runtime['coopAnimationReadEntries']
        import ndspy.narc
        common=ndspy.narc.NARC(self.stock.files[self.stock.filenames.idOf('ARCHIVE/arc0.narc')])
        index=self.runtime['coopNarcIndex'];extents=index+self.word(index+12);top=self.word(index+8)
        for member,data in enumerate(common.files):
            name=common.filenames.filenameOf(member) or ''
            if name.endswith('.bca'):
                self.members[name]=(top+self.word(extents+member*8),bytes(data))
        self.assertEqual(len(self.members),132)
        self.expected_packed=sum((len(data)+3)&~3 for _,data in self.members.values())

    def packed_stats(self):return struct.unpack('<8I',self.cpu.mem_read(self.runtime['coopPackedAnimationStats'],32))
    def pool(self):
        for slot in range(32):
            address=self.entries+slot*24
            if self.word(address+16) and self.word(address)==0:return address
        return 0
    def release(self):self.invoke('CoopReleaseStageSourceCache')
    def capacity(self):
        return (self.largest(self.owner),self.call(self.game['_ZN22ExpandingHeapAllocator10MemoryLeftEv'],self.allocator))
    def capacity_without_source(self):
        ram=bytes(self.cpu.mem_read(0x02000000,0x400000))
        self.call(self.game['UnloadArchive'],0);expected=self.capacity()
        self.cpu.mem_write(0x02000000,ram);return expected

    def test_every_common_member_keeps_exact_bytes_and_native_cursor_without_physical_reads(self):
        before_game=self.largest(self.game_heap)
        self.release();pool=self.pool();self.assertTrue(pool)
        self.assertEqual(self.word(self.table),0);self.assertEqual(self.word(self.table+4),0)
        self.assertEqual(self.word(pool+4),self.expected_packed)
        self.assertEqual(self.word(pool+16),self.image)
        for name in self.members:self.load(name)
        self.assertEqual(self.reads,[])
        self.assertEqual(self.packed_stats()[1:3],(1,len(self.members)))
        self.assertEqual(self.largest(self.game_heap),before_game)
        self.assertTrue(self.intact(self.owner))

    def test_native_capacity_prediction_and_eviction_restore_original_source_free_space(self):
        expected=self.capacity_without_source();self.release()
        out=0x023f1000
        self.assertEqual(self.invoke('CoopAnimationQueryCapacity',self.owner,out),1)
        self.assertEqual(struct.unpack('<2I',self.cpu.mem_read(out,8)),expected)
        self.invoke('CoopAnimationCacheMakeRoom',self.owner,expected[0],4)
        self.assertEqual(self.pool(),0);self.assertEqual(self.capacity(),expected)
        self.assertTrue(self.intact(self.owner))

    def test_pool_and_full_regular_cache_share_exact_virtual_capacity_and_free_once(self):
        expected=self.capacity_without_source();self.release();pool=self.pool()
        self.cpu.mem_write(self.destination,b'LZ77\x10\x01\0\0')
        for i in range(34):self.invoke('CoopStoreAnimationRead',0x10000000+i*32,self.destination,8)
        self.assertEqual(self.pool(),pool)
        self.assertEqual(self.stats()[5],32)
        self.assertGreater(self.stats()[4],65536)
        out=0x023f1000
        self.assertEqual(self.invoke('CoopAnimationQueryCapacity',self.owner,out),1)
        self.assertEqual(struct.unpack('<2I',self.cpu.mem_read(out,8)),expected)
        self.invoke('CoopFlushAnimationReadCache')
        self.assertEqual(self.capacity(),expected);self.assertEqual(self.stats()[4:6],(0,0))
        self.assertTrue(self.intact(self.owner))

    def test_invalid_source_keeps_native_unmount_and_deallocation(self):
        expected=self.capacity_without_source()
        top,_=next(iter(self.members.values()));index=self.runtime['coopNarcIndex']
        offset=top-self.word(index+8)
        self.cpu.mem_write(self.image+0x60+offset,b'bad!')
        self.release()
        self.assertEqual(self.pool(),0);self.assertEqual(self.word(self.table),0)
        self.assertEqual(self.capacity(),expected)
        self.assertEqual(self.packed_stats()[4],1);self.assertTrue(self.intact(self.owner))

    def test_packing_stops_if_optional_ownership_changes_between_bounded_copies(self):
        expected=self.capacity_without_source();state={'copies':0,'interrupted':False,'image':None}
        def event(cpu,address,size,user):
            packing=next((self.entries+i*24 for i in range(32)
                if self.word(self.entries+i*24)==1 and self.word(self.entries+i*24+16)),None)
            if address==self.game['CpuCopy8'] and packing:state['copies']+=1
            if address!=self.game['_ZN3IRQ7RestoreEj'] or not packing or not state['copies'] or state['interrupted']:return
            # Model the ownership invalidation at an IRQ boundary; native
            # pressure/free semantics themselves are tested independently above.
            state['interrupted']=True;state['image']=self.word(packing+16)
            size=self.word(packing+8);self.write(packing+16,0);self.write(packing+20,0)
            self.write(self.runtime['coopAnimationCacheStats']+16,self.stats()[4]-size)
            self.write(self.runtime['coopAnimationCacheStats']+20,self.stats()[5]-1)
        self.cpu.hook_add(UC_HOOK_CODE,event)
        self.release()
        self.assertTrue(state['interrupted']);self.assertEqual(state['copies'],1)
        self.assertEqual(self.packed_stats()[5],1);self.assertEqual(self.pool(),0)
        self.call(self.game['_ZN5mHeap6Heap_t11_DeallocateEPv'],self.owner,state['image'])
        self.assertEqual(self.capacity(),expected);self.assertTrue(self.intact(self.owner))

    def test_native_unpack_guards_still_reject_foreign_file_views_and_async_reads(self):
        self.release()
        top,data=self.view();self.write(self.file+40,top+1)
        self.assertEqual(self.invoke('CoopReadFileUncached',self.file,self.destination,0,0),0)
        self.assertEqual(self.packed_stats()[2],0)
        # Direct guard checks avoid fabricating an async operation in this
        # captured loading fixture. Existing physical-I/O tests cover delegates.
        self.assertEqual(self.invoke('CoopAnimationReadKey',self.file,len(data),1),0)
        self.write(self.file+40,top);self.write(self.file+8,0)
        self.assertEqual(self.invoke('CoopAnimationReadKey',self.file,len(data),0),0)
        self.assertEqual(self.packed_stats()[2],0)
