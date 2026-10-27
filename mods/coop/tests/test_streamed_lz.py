"""Compiled LZ reader and retail allocator against the skybox memory peak.

Physical file reads use an in-memory ROM adapter; this is not WFS evidence.
"""
import struct
import unittest
import ndspy.lz10
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness,NativeAllocationFailure


class StreamedLzTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_STREAM_LZ_FIXTURE'
    default_fixture=('/workspace/runtime/reserved-table-rainbow-matrix/'
                     'story-entry-native-crash-0')

    def setUp(self):
        super().setUp()
        # Release the captured native scratch buffer, then replay that file's
        # complete load against the same heaps and pinned particle table.
        scratch=struct.unpack_from('<I',self.dtcm,0x37cc)[0]
        self.call(self.game['_ZN6Memory10DeallocateEPv'],scratch)
        self.file=0x023f0000
        self.data=bytes(self.stock.files[0x64a])
        self.position=0
        self.read_sizes=[]
        self.closed=False
        self.delegated=0
        self.flushes=[]
        self.input_cache_ranges=[]
        self.write(self.file+32,0)
        self.write(self.file+36,len(self.data))
        def fs(cpu,address,size,user):
            a,b,c=(cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
            result=None
            if address in (self.game['FS_ReadFile'],self.game['func_02018d48']):
                count=min(c,len(self.data)-self.position)
                cpu.mem_write(b,self.data[self.position:self.position+count])
                self.position+=count
                self.read_sizes.append(c)
                result=count
            elif address==self.game['FS_CloseFile']:
                self.closed=True;result=1
            elif address==self.game['func_0205d368']:
                self.position=b;result=1
            elif address==self.game['func_02018770']:
                result=0
            elif address==self.game['_ZN4CP1514FlushDataCacheEjj']:
                self.flushes.append((a,b));result=0
            elif address==self.game['_ZN4CP1527FlushAndInvalidateDataCacheEjj']:
                self.input_cache_ranges.append((a,b));result=0
            elif address==self.runtime['CoopOriginalLoadDiskFile']:
                self.delegated+=1;result=0x1234
            if result is not None:
                cpu.reg_write(UC_ARM_REG_R0,result)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,fs)

    def test_native_scratch_plus_result_reproduces_skybox_failure(self):
        with self.assertRaises(NativeAllocationFailure):
            self.call(self.game['func_0201834c'],self.file,0)

    def test_exact_skybox_output_with_bounded_input_and_native_allocator(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        expected=ndspy.lz10.decompress(self.data[4:])
        self.assertEqual(len(expected),33336)
        result=self.call('CoopLoadDiskFile',self.file,1)
        self.assertEqual(bytes(self.cpu.mem_read(result,len(expected))),expected)
        limit=4096 if 'coopLzWindowStats' in self.runtime else 512
        self.assertLessEqual(max(self.read_sizes),limit)
        self.assertTrue(self.input_cache_ranges)
        self.assertTrue(all(address%32==0 and 0<count<=limit
                            for address,count in self.input_cache_ranges))
        self.assertTrue(self.closed)
        self.assertEqual(self.flushes,[(result,len(expected))])
        self.assertEqual(self.word(self.runtime['coopStreamedLzReads']),1)
        self.call('CoopFreeResource',result)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_repeated_skybox_loads_release_their_owner(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        for _ in range(8):
            self.position=0
            result=self.call('CoopLoadDiskFile',self.file,0)
            self.call('CoopFreeResource',result)
            self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root))
        self.assertTrue(self.intact(self.game_heap))

    def window_stats(self):
        if 'coopLzWindowStats' not in self.runtime:
            self.skipTest('requires --experimental-lz-window build')
        return struct.unpack('<5I',self.cpu.mem_read(self.runtime['coopLzWindowStats'],20))

    def fill_below_window(self,owner,ballast):
        for _ in range(128):
            available=self.largest(owner)
            if available<4096:return
            pointer=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],owner,available-128,4)
            self.assertTrue(pointer);ballast.append((owner,pointer))
        self.fail('Could not construct bounded native heap-pressure fixture')

    def release_ballast(self,ballast):
        for owner,pointer in reversed(ballast):
            self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],owner,pointer)

    def test_large_window_reduces_read_requests_and_restores_both_native_heaps(self):
        self.window_stats()
        before=(self.largest(self.root),self.largest(self.game_heap))
        result=self.call('CoopLoadDiskFile',self.file,0)
        stats=self.window_stats()
        self.assertEqual(stats[0]+stats[1],1)
        self.assertEqual(stats[2],0)
        self.assertEqual(max(self.read_sizes),4096)
        self.assertEqual(len(self.read_sizes),1+(len(self.data)-8+4095)//4096)
        self.assertEqual(stats[3],len(self.read_sizes)-1)
        self.assertEqual(bytes(self.cpu.mem_read(result,33336)),ndspy.lz10.decompress(self.data[4:]))
        self.call('CoopFreeResource',result)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_heap_pressure_keeps_exact_output_with_the_original_stack_window(self):
        self.window_stats()
        before=(self.largest(self.root),self.largest(self.game_heap));ballast=[]
        # Keep one exact output-sized block. After allocating the output,
        # neither heap can provide the optional4KB input window.
        held=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,33336,32)
        self.fill_below_window(self.root,ballast)
        self.fill_below_window(self.game_heap,ballast)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,held)
        result=self.call('CoopLoadDiskFile',self.file,0)
        self.assertEqual(self.window_stats()[:3],(0,0,1))
        self.assertLessEqual(max(self.read_sizes),512)
        self.assertEqual(bytes(self.cpu.mem_read(result,33336)),ndspy.lz10.decompress(self.data[4:]))
        self.call('CoopFreeResource',result);self.release_ballast(ballast)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_game_owned_window_is_released_through_its_explicit_owner(self):
        self.window_stats()
        before=(self.largest(self.root),self.largest(self.game_heap));ballast=[]
        held=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.root,33336,32)
        self.fill_below_window(self.root,ballast)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,held)
        result=self.call('CoopLoadDiskFile',self.file,0)
        self.assertEqual(self.window_stats()[:3],(0,1,0))
        self.assertEqual(bytes(self.cpu.mem_read(result,33336)),ndspy.lz10.decompress(self.data[4:]))
        self.call('CoopFreeResource',result);self.release_ballast(ballast)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_offline_policy_delegates_without_reading(self):
        self.write(self.runtime['coopEnabled'],0)
        self.assertEqual(self.call('CoopLoadDiskFile',self.file,0),0x1234)
        self.assertEqual(self.read_sizes,[])

    def test_uncompressed_file_restores_position_before_native_load(self):
        self.data=b'uncompressed data'+bytes(512)
        self.write(self.file+36,len(self.data))
        self.assertEqual(self.call('CoopLoadDiskFile',self.file,0),0x1234)
        self.assertEqual(self.position,0)
        self.assertEqual(self.delegated,1)


if __name__=='__main__':unittest.main()
