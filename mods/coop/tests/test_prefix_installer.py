"""Run the compiled opt-in prefix loader, with physical FS calls stubbed."""
import io
from pathlib import Path
import struct
import unittest
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR,UC_ARM_REG_PC
from test_particle_heap import HeapHarness,ROOT


class PrefixInstallerTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        import json
        report=json.loads((ROOT/'build/coop/build.json').read_text())
        if report['runtimeModule'].get('runtimePlacement')!='prefix':
            self.skipTest('Build --runtime-placement prefix to exercise this installer')
        elf=ELFFile(io.BytesIO((ROOT/'build/coop/install.elf').read_bytes()))
        self.loader=next(s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()
                         if s.name=='LoadRuntime')
        self.cpu.mem_write(0x021165b0,(ROOT/'build/coop/install.bin').read_bytes())
        self.blob=bytearray((ROOT/'build/coop/runtime-relocatable.bin').read_bytes())
        self.position=0
        self.reads=[]
        self.closed=False
        self.input_cache_ranges=[]
        self.write(0x02004180,0)
        self.cpu.mem_write(0x02000000,bytes([0xa5])*256)
        self.retail_prefix=bytes(self.cpu.mem_read(0x02004000,256))
        def fs(cpu,address,size,user):
            a,b,c=(cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
            result=None
            if address==self.game['func_020185c0']:result=1
            elif address==self.game['FS_ReadFile']:
                data=bytes(self.blob[self.position:self.position+c])
                cpu.mem_write(b,data);self.position+=len(data)
                self.reads.append(c);result=len(data)
            elif address==self.game['FS_CloseFile']:
                self.closed=True;result=1
            elif address in (self.game['_ZN4CP1514FlushDataCacheEjj'],
                             self.game['_ZN4CP1526InvalidateInstructionCacheEjj']):result=0
            elif address==self.game['_ZN4CP1527FlushAndInvalidateDataCacheEjj']:
                self.input_cache_ranges.append((a,b));result=0
            elif address==self.game['_ZN5mHeap6Heap_t8AllocateEji']:
                raise AssertionError('Prefix installation allocated from a heap')
            if result is not None:
                cpu.reg_write(UC_ARM_REG_R0,result)
                cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,fs)

    def test_native_loader_relocates_body_without_a_heap_or_fixup_tail(self):
        _,link,size,entry,count,_=struct.unpack_from('<6I',self.blob)
        expected=bytearray(self.blob[24:24+size]);delta=0x02000100-link
        for record in struct.unpack_from('<'+'I'*count,self.blob,24+size):
            offset=record&0x7fffffff
            value=struct.unpack_from('<I',expected,offset)[0]
            if record&0x80000000:value=(value&0xff000000)|((value-(delta>>2))&0xffffff)
            else:value=(value+delta)&0xffffffff
            struct.pack_into('<I',expected,offset,value)
        result=self.call(self.loader)
        self.assertEqual(result,0x02000100+entry)
        self.assertEqual(bytes(self.cpu.mem_read(0x02000100,size)),expected)
        self.assertEqual(bytes(self.cpu.mem_read(0x02000000,256)),bytes([0xa5])*256)
        self.assertEqual(bytes(self.cpu.mem_read(0x02004000,256)),self.retail_prefix)
        self.assertTrue(self.closed)
        self.assertEqual(self.reads[:2],[24,size])
        self.assertTrue(all(n<=256 for n in self.reads[2:]))
        self.assertEqual(self.input_cache_ranges[0],(0x02000100,size))
        self.assertTrue(all(address%32==0 and count<=256
                            for address,count in self.input_cache_ranges[1:]))

    def test_second_install_uses_the_cached_entry(self):
        entry=self.call(self.loader);reads=list(self.reads)
        self.assertEqual(self.call(self.loader),entry)
        self.assertEqual(self.reads,reads)

    def test_oversized_body_is_rejected_before_copy(self):
        struct.pack_into('<I',self.blob,8,0x4000)
        self.assertEqual(self.call(self.loader),0)
        self.assertEqual(self.reads,[24])
        self.assertEqual(self.word(0x02004180),0)
        self.assertTrue(self.closed)

    def test_invalid_fixup_never_publishes_an_entry(self):
        size=struct.unpack_from('<I',self.blob,8)[0]
        struct.pack_into('<I',self.blob,24+size,size)
        self.assertEqual(self.call(self.loader),0)
        self.assertEqual(self.word(0x02004180),0)
        self.assertTrue(self.closed)


if __name__=='__main__':unittest.main()
