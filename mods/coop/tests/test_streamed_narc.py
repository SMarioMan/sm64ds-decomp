"""Compiled ARM NARC views checked against ndspy and private failure heaps.

Only the physical FS API is replaced by an in-memory ROM adapter. Parser,
policy and original allocator execute as ARM; this is not wireless evidence.
"""
import struct
import unittest

import ndspy.narc
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
                              UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC)
from test_particle_heap import HeapHarness,NativeAllocationFailure


class StreamedNarcTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_STREAM_NARC_FIXTURE'
    default_fixture=('/workspace/runtime/split-particle-rainbow-matrix/'
                     'story-entry-native-crash-1')

    def setUp(self):
        super().setUp()
        self.file=0x023f0000
        self.buffer=0x023d0000
        self.handles={}
        self.original_calls=[]
        self.physical_opens=0
        self.arc_table=self.game['data_0208ecf4']
        fat=struct.unpack_from('<I',self.stock.save(),0x48)[0]
        original=self.stock.save()
        self.archives={}
        for i in range(13):
            row=self.arc_table+i*20
            path=self.string(self.word(row+16))
            file_id=self.stock.filenames.idOf(path.lstrip('/'))
            top,bottom=struct.unpack_from('<II',original,fat+file_id*8)
            data=self.stock.files[file_id]
            self.archives[path]=(file_id,top,bottom,data)
        def fs(cpu,address,size,user):
            args=[cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            result=None
            if address==self.game['FS_InitFile']:
                self.cpu.mem_write(args[0],bytes(68));result=0
            elif address==self.game['func_02018d98']:
                name=self.string(args[1]);entry=self.archives[name]
                self.handles[args[0]]=entry
                file_id,top,bottom,data=entry
                self.write(args[0]+8,0x020a8074)
                self.write(args[0]+28,file_id)
                for offset,value in ((32,top),(36,bottom),(40,top)):
                    self.write(args[0]+offset,value)
                self.physical_opens+=1;result=1
            elif address==self.game['FS_ReadFile']:
                file_id,top,bottom,data=self.handles[args[0]]
                position=self.word(args[0]+40)
                count=min(args[2],self.word(args[0]+36)-position)
                self.cpu.mem_write(args[1],bytes(data[position-top:position-top+count]))
                self.write(args[0]+40,position+count);result=count
            elif address==self.game['func_0205d368']:
                base=(self.word(args[0]+32),self.word(args[0]+40),self.word(args[0]+36))[args[2]]
                self.write(args[0]+40,base+args[1]);result=1
            elif address==self.game['FS_CloseFile']:
                self.handles.pop(args[0],None);result=1
            elif address==self.game['func_0205d5e8']:
                file_id= self.word(cpu.reg_read(UC_ARM_REG_SP))
                entry=next(e for e in self.archives.values() if e[0]==file_id)
                self.handles[args[0]]=entry
                for offset,value in ((8,args[1]),(28,file_id),(32,args[2]),(36,args[3]),(40,args[2])):
                    self.write(args[0]+offset,value)
                result=1
            elif address in (self.runtime['CoopOriginalOpenFile'],self.runtime['CoopOriginalResolveFile']):
                self.original_calls.append((address,args));result=0x1234
            if result is not None:
                cpu.reg_write(UC_ARM_REG_R0,result)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,fs)

    def string(self,address):
        out=bytearray()
        while True:
            b=self.cpu.mem_read(address+len(out),1)[0]
            if not b:return out.decode()
            out.append(b)

    def test_original_whole_archive_reproduces_rainbow_guest_failure(self):
        self.assertLess(self.largest(self.root),42992)
        with self.assertRaises(NativeAllocationFailure):self.call(self.game['LoadArchive'],7)

    def test_uncached_resolver_avoids_loading_the_container(self):
        self.write(self.arc_table+7*20,0)
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.assertEqual(self.call('CoopResolveFile',0x9c06),0)
        self.assertEqual(self.physical_opens,0)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_actual_failing_member_reads_exact_bytes_without_heap_reserve(self):
        row=self.arc_table+7*20;self.write(row,0)
        expected=ndspy.narc.NARC(self.archives['/ARCHIVE/ar1.narc'][3]).files[6]
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.assertEqual(self.call('CoopOpenFile',self.file,0x9c06),1)
        self.assertEqual(self.word(self.file+36)-self.word(self.file+32),len(expected))
        self.assertEqual(self.call(self.game['FS_ReadFile'],self.file,self.buffer,len(expected)),len(expected))
        self.assertEqual(bytes(self.cpu.mem_read(self.buffer,len(expected))),expected)
        self.call(self.game['FS_CloseFile'],self.file)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertEqual(self.word(self.runtime['coopStreamedNarcReads']),1)

    def test_every_member_matches_independent_narc_parser(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        members=0
        for i in range(13):
            row=self.arc_table+i*20;self.write(row,0)
            first=self.word(row+8)&0xffff
            name=self.string(self.word(row+16))
            for index,expected in enumerate(ndspy.narc.NARC(self.archives[name][3]).files):
                # Both native copy loaders support these streamed disk files.
                self.assertGreater(len(expected),8)
                self.assertEqual(self.call('CoopOpenFile',self.file,first+index),1)
                self.assertEqual(self.call(self.game['FS_ReadFile'],self.file,self.buffer,len(expected)),len(expected))
                self.assertEqual(bytes(self.cpu.mem_read(self.buffer,len(expected))),expected)
                self.call(self.game['FS_CloseFile'],self.file);members+=1
        self.assertEqual(self.word(self.runtime['coopStreamedNarcReads']),members)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)
        self.assertFalse(self.handles)

    def test_cached_archive_retains_native_resolver_and_open(self):
        self.write(self.arc_table+7*20,0x02300000)
        self.assertEqual(self.call('CoopResolveFile',0x9c06),0x1234)
        self.assertEqual(self.call('CoopOpenFile',self.file,0x9c06),0x1234)
        self.assertEqual(len(self.original_calls),2)
        self.assertEqual(self.physical_opens,0)

    def test_offline_paths_retain_native_policy(self):
        self.write(self.runtime['coopEnabled'],0)
        self.assertEqual(self.call('CoopResolveFile',0x9c06),0x1234)
        self.assertEqual(self.call('CoopOpenFile',self.file,0x9c06),0x1234)
        self.assertEqual(len(self.original_calls),2)
        self.assertEqual(self.physical_opens,0)


if __name__=='__main__':unittest.main()
