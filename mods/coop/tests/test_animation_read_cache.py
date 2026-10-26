"""Optional raw animation cache against native heaps/copy/seek in isolation.

The physical read adapter supplies bytes from the user's ROM. It is not a
wireless test and never replaces packets or memory in a running emulator.
"""
import struct
import unittest
from pathlib import Path
import ndspy.narc
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC)
from test_particle_heap import HeapHarness


class AnimationReadCacheTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_ANIMATION_CACHE_FIXTURE'
    default_fixture='/workspace/runtime/bob-native-process-steady/steady-bob-0'

    def setUp(self):
        super().setUp()
        if 'CoopAnimationHeapAllocate' not in self.runtime:
            self.skipTest('requires --experimental-animation-cache build')
        self.file=0x023f0000
        self.destination=0x023d0000
        self.cpu.mem_write(self.file,bytes(68))
        self.write(0x020a613c,self.game['data_020a621c'])
        self.cpu.mem_write(0x020a0f1c,b'\0\0')
        self.write(self.word(0x0209d3b4)+16,3)
        self.reads=[]
        self.read_irq=[]
        self.read_limit=None
        original=Path('/workspace/inputs/sm64ds-eu.nds').read_bytes()
        fat=struct.unpack_from('<I',original,0x48)[0]
        archive_id=self.stock.filenames.idOf('ARCHIVE/arc0.narc')
        archive_top=struct.unpack_from('<I',original,fat+archive_id*8)[0]
        archive=ndspy.narc.NARC(self.stock.files[archive_id])
        table=self.runtime['coopNarcIndex']
        offset=self.word(table+12)
        self.members={}
        for i,data in enumerate(archive.files):
            name=archive.filenames.filenameOf(i)
            if name and name.startswith('data/player/') and name.endswith('.bca'):
                top=archive_top+self.word(table+offset+i*8)
                self.members[name]=(top,bytes(data))
        def physical(cpu,address,size,user):
            if address!=self.game['func_0205cdf4']:return
            f,command=(cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1))
            self.write(f+16,command)
            if command==0:
                # Actual FSi_ReadFileCore prepared these arguments. Complete
                # its physical command; native WaitAsync/Seek/Close still run.
                d,n=self.word(f+44),self.word(f+52)
                top=self.word(f+32)
                data=next(data for member,data in self.members.values() if member==top)
                pos=self.word(f+40)-top
                count=min(n,len(data)-pos)
                if self.read_limit is not None:count=min(count,self.read_limit)
                cpu.mem_write(d,data[pos:pos+count])
                self.write(f+40,top+pos+count)
                self.reads.append((top,n))
                self.read_irq.append(cpu.reg_read(UC_ARM_REG_CPSR)&0x80)
            elif command!=8:
                raise AssertionError('Unexpected physical command '+str(command))
            self.write(f+12,self.word(f+12)&~15)
            self.write(f+20,0)
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,physical)

    def invoke(self,symbol,*args):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0x5f) # IRQ initially enabled.
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):
            self.cpu.reg_write(reg,value)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
        self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime[symbol],self.base+0xff00,count=1000000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0x80,0)
        return self.cpu.reg_read(UC_ARM_REG_R0)

    def view(self,name='data/player/Y_run.bca'):
        top,data=self.members[name]
        self.write(self.file+8,self.word(0x0209d3b4))
        self.write(self.file+12,0x10)
        self.write(self.file+20,0)
        self.write(self.file+32,top)
        self.write(self.file+36,top+len(data))
        self.write(self.file+40,top)
        return top,data

    def stats(self):
        return struct.unpack('<8I',self.cpu.mem_read(self.runtime['coopAnimationCacheStats'],32))

    def load(self,name='data/player/Y_run.bca',async_=0,size=None):
        top,data=self.view(name)
        count=len(data) if size is None else size
        result=self.invoke('CoopReadFile',self.file,self.destination,count,async_)
        self.assertEqual(result,count)
        self.assertEqual(bytes(self.cpu.mem_read(self.destination,count)),data[:count])
        self.assertEqual(self.word(self.file+40),top+count) # Actual retail SeekFile on hits.
        return data

    def test_second_exact_read_uses_immutable_bytes_and_native_cursor_without_io(self):
        self.load()
        self.assertEqual(self.stats()[:3],(0,1,1))
        self.cpu.mem_write(self.destination,b'overwritten by caller')
        self.load()
        self.assertEqual(self.stats()[:3],(1,1,1))
        self.assertEqual(len(self.reads),1)
        self.assertEqual(self.word(self.file+12),0x10)
        self.assertEqual(self.word(self.file+16),0)
        self.assertEqual(self.word(self.file+44),self.destination)
        self.assertEqual(self.word(self.file+48),len(self.members['data/player/Y_run.bca'][1]))
        self.assertEqual(self.word(self.file+52),self.word(self.file+48))
        self.assertEqual(self.call(self.game['func_0205d3f4'],self.file),1)
        self.assertEqual(self.call(self.game['FS_CloseFile'],self.file),1)
        self.assertEqual(self.word(self.file+8),0)
        self.assertEqual(self.word(self.file+16),12)
        self.assertEqual(self.read_irq,[0]) # No cache critical section covers physical I/O.

    def test_root_pressure_evicts_optional_storage_before_native_allocation(self):
        before=self.largest(self.root)
        node=self.word(self.word(self.root+20)+0x24)
        free=[]
        while node:
            free.append((node,self.word(node+4)))
            node=self.word(node+12)
        self.load()
        entries=self.runtime['coopAnimationReadEntries']
        cached=next(self.word(entries+i*24+16) for i in range(32)
                    if self.word(entries+i*24+16))
        request=next(size for node,size in free if node<=cached<node+16+size)
        # The cache may occupy a small free block. Consume other blocks first,
        # so the native request really requires reclaiming that cached block.
        reserved=[]
        while self.largest(self.root)>=request:
            size=self.largest(self.root)
            reserved.append(self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,size,4))
        block=self.invoke('CoopAnimationHeapAllocate',self.root,request,4)
        self.assertTrue(block)
        self.assertEqual(self.stats()[5],0)
        for pointer in [block]+reserved:
            self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.largest(self.root),before)
        self.assertTrue(self.intact(self.root))

    def test_flush_uses_recorded_root_owner_with_game_selected(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.load()
        self.write(self.game['_ZN6Memory14defaultHeapPtrE'],self.game_heap)
        self.invoke('CoopFlushAnimationReadCache')
        self.assertEqual(self.stats()[4:6],(0,0))
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))

    def test_partial_and_async_reads_keep_original_io_and_are_not_cached(self):
        self.load(size=16)
        self.load(async_=1)
        self.assertEqual(len(self.reads),2)
        self.assertEqual(self.stats()[:3],(0,0,0))
        self.assertEqual(self.read_irq,[0,0])

    def test_disabled_offline_and_other_thread_keep_original_io(self):
        for address,value in ((self.runtime['coopEnabled'],0),(0x0209fc68,0),(0x020a613c,0)):
            old=self.word(address)
            self.write(address,value)
            self.load()
            self.write(address,old)
        self.assertEqual(len(self.reads),3)
        self.assertEqual(self.stats()[:3],(0,0,0))

    def test_short_physical_read_is_returned_without_caching_partial_bytes(self):
        top,data=self.view()
        self.read_limit=16
        result=self.invoke('CoopReadFile',self.file,self.destination,len(data),0)
        self.assertEqual(result,16)
        self.assertEqual(bytes(self.cpu.mem_read(self.destination,16)),data[:16])
        self.assertEqual(self.stats()[:3],(0,1,0))
        self.read_limit=None
        self.load()
        self.assertEqual(len(self.reads),2)
        self.assertEqual(self.stats()[:3],(0,2,1))

    def test_truncated_view_and_previous_error_do_not_use_an_existing_cache_hit(self):
        self.load()
        top,data=self.view()
        self.write(self.file+36,top+32)
        self.assertEqual(self.invoke('CoopReadFile',self.file,self.destination,32,0),32)
        self.assertEqual(bytes(self.cpu.mem_read(self.destination,32)),data[:32])
        self.view()
        self.write(self.file+20,3)
        self.assertEqual(self.invoke('CoopReadFile',self.file,self.destination,len(data),0),len(data))
        self.assertEqual(len(self.reads),3)
        self.assertEqual(self.stats()[0],0)

    def test_game_heap_allocation_does_not_evict_root_cache(self):
        self.load()
        pointer=self.invoke('CoopAnimationHeapAllocate',self.game_heap,16,4)
        self.assertTrue(pointer)
        self.assertEqual(self.stats()[5],1)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,pointer)
        self.load()
        self.assertEqual(len(self.reads),1)

    def test_stage_cleanup_flushes_before_delegating_and_preserves_result(self):
        self.load()
        calls=[]
        def original(cpu,address,size,user):
            if address!=self.runtime['CoopOriginalStageCleanup']:return
            self.assertEqual(self.stats()[4:6],(0,0))
            calls.append(cpu.reg_read(UC_ARM_REG_R0))
            cpu.reg_write(UC_ARM_REG_R0,17)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,original)
        self.assertEqual(self.invoke('CoopAnimationStageCleanup',0x023f8000),17)
        self.assertEqual(calls,[0x023f8000])

    def test_archive_transition_and_pending_native_errors_bypass_cache(self):
        self.load()
        archive=self.word(0x0209d3b4)
        for flags in (0,3|0x20,3|0x40,3|0x80):
            self.write(archive+16,flags)
            self.load()
        self.write(archive+16,3)
        for error in (1,2,4,8,16,128):
            self.cpu.mem_write(0x020a0f1c,bytes((error,0)))
            self.load()
        self.assertEqual(self.stats()[0],0)
        self.assertEqual(len(self.reads),11)

    def test_download_play_suspended_rom_archive_still_serves_immutable_cache(self):
        # Native WFS guests retain ROM flags0x0a: loaded plus suspended card
        # access. The cached bytes need no physical ROM operation.
        archive=self.word(0x0209d3b4)
        self.write(archive+16,0x0a)
        self.load()
        self.load()
        self.assertEqual(self.stats()[:3],(1,1,1))
        self.assertEqual(len(self.reads),1)
        self.assertEqual(self.word(archive+16),0x0a)

    def test_capacity_queries_reclaim_cache_and_match_native_values(self):
        for wrapper,native in (('CoopAnimationMaxMemory','_ZN5mHeap9ExpHeap_t19VMaxAllocatableSizeEv'),
                               ('CoopAnimationMemoryLeft','_ZN5mHeap9ExpHeap_t11VMemoryLeftEv')):
            before=self.call(self.game[native],self.root)
            game_before=self.call(self.game[native],self.game_heap)
            self.load()
            self.assertEqual(self.invoke(wrapper,self.game_heap),game_before)
            self.assertEqual(self.stats()[5],1)
            self.assertEqual(self.invoke(wrapper,self.root),before)
            self.assertEqual(self.stats()[5],0)
            self.assertTrue(self.intact(self.root))

    def test_native_in_place_growth_flushes_cache_and_preserves_buffer(self):
        before=self.largest(self.root)
        size=before-256
        pointer=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,size,4)
        data=bytes(range(64))
        self.cpu.mem_write(pointer,data)
        self.load()
        self.assertEqual(self.stats()[5],1)
        self.assertGreaterEqual(self.invoke('CoopAnimationHeapReallocate',self.root,pointer,size+32),size+32)
        self.assertEqual(self.stats()[5],0)
        self.assertEqual(bytes(self.cpu.mem_read(pointer,64)),data)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.largest(self.root),before)
        self.assertTrue(self.intact(self.root))

    def test_native_shrink_keeps_cache_and_preserves_buffer(self):
        pointer=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,128,4)
        data=bytes(range(96))
        self.cpu.mem_write(pointer,data)
        self.load()
        self.assertGreaterEqual(self.invoke('CoopAnimationHeapReallocate',self.root,pointer,96),96)
        self.assertEqual(self.stats()[5],1)
        self.assertEqual(bytes(self.cpu.mem_read(pointer,96)),data)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.invoke('CoopFlushAnimationReadCache')
        self.assertTrue(self.intact(self.root))

    def test_larger_members_exercise_the_payload_budget(self):
        names=sorted(self.members,key=lambda n:len(self.members[n][1]),reverse=True)[:40]
        for name in names:
            self.load(name)
            self.assertLessEqual(self.stats()[4],65536)
            self.assertLessEqual(self.stats()[5],32)
        self.assertGreater(self.stats()[6],60000)
        self.assertGreater(self.stats()[3],0)
        self.invoke('CoopFlushAnimationReadCache')
        self.assertTrue(self.intact(self.root))

    def test_small_members_exercise_lru_capacity_without_unbounded_reservation(self):
        names=sorted(self.members,key=lambda n:len(self.members[n][1]))[:40]
        for name in names:self.load(name)
        self.assertLessEqual(self.stats()[4],65536)
        self.assertLessEqual(self.stats()[5],32)
        self.assertGreater(self.stats()[3],0)
        self.assertTrue(self.intact(self.root))
        self.invoke('CoopFlushAnimationReadCache')
        self.assertEqual(self.stats()[4:6],(0,0))


if __name__=='__main__':unittest.main()
