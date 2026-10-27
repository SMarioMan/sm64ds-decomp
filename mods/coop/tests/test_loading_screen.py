"""Stage loading display leases in isolated ARM hardware-memory mappings.

Native IRQ registration and VRAM-bank SDK functions execute. VBlank work and
asset-producing routines have deterministic adapters; no live DS is modified.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_SP,UC_ARM_REG_CPSR
from test_particle_heap import HeapHarness


class LoadingScreenTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopLoadingAllow' not in self.runtime:
            self.skipTest('requires --experimental-loading-screen')
        for base,size in ((0x05000000,0x1000),(0x06600000,0x4000),(0x07000000,0x1000)):
            self.cpu.mem_map(base,size)
        self.tiles=bytes((i*13+7)&255 for i in range(0x4000))
        self.palette=bytes((i*7+19)&255 for i in range(512))
        self.oam=bytes((i*3+11)&255 for i in range(1024))
        self.cpu.mem_write(0x06600000,self.tiles)
        self.cpu.mem_write(0x05000600,self.palette)
        self.cpu.mem_write(0x07000400,self.oam)
        self.display=0x40000303
        self.write(0x04001000,self.display)
        self.half(0x04000304,0x200);self.half(0x0400106c,0x8010)
        self.cpu.mem_write(0x04000249,b'\x82')
        self.cpu.mem_write(0x020a6088,bytes(26));self.half(0x020a609c,0x100)
        self.native_irq=self.game['_ZN3IRQ13VBlankHandlerEv']
        self.write(0x02099fe4,self.native_irq)
        self.native_calls=0;self.delegates=[];self.writer=None
        def adapter(cpu,address,size,user):
            if address==self.native_irq:
                self.native_calls+=1;result=0
            elif address in tuple(self.runtime[n] for n in
                    ('CoopLoadingOriginalDecompress','CoopLoadingOriginalObjPalette','CoopLoadingOriginalReadAt')):
                args=tuple(cpu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
                self.delegates.append((address,args,self.word(self.runtime['coopLoadingActive'])))
                if self.writer:self.writer(args)
                result=321
            else:return
            cpu.reg_write(UC_ARM_REG_R0,result)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,adapter)

    def half(self,address,value):self.cpu.mem_write(address,struct.pack('<H',value))
    def readhalf(self,address):return struct.unpack('<H',self.cpu.mem_read(address,2))[0]
    def invoke(self,name,*args):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0x5f)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):
            self.cpu.reg_write(reg,value)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000);self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime[name],self.base+0xff00,count=1000000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0x80,0)
        return self.cpu.reg_read(UC_ARM_REG_R0)
    def stats(self):return struct.unpack('<7I',self.cpu.mem_read(self.runtime['coopLoadingScreenStats'],28))
    def active(self):return self.word(self.runtime['coopLoadingActive'])

    def test_loading_text_animates_and_restores_exact_native_tiles_palette_oam_and_irq(self):
        self.invoke('CoopLoadingAllow');self.assertEqual(self.active(),1)
        self.assertEqual(self.word(0x02099fe4),self.runtime['CoopLoadingVBlank'])
        self.assertEqual(self.readhalf(0x0400106c),0)
        self.write(0x027ffc3c,0);self.invoke('CoopLoadingVBlank')
        first=bytes(self.cpu.mem_read(0x06603fe0,32))
        self.write(0x027ffc3c,8);self.invoke('CoopLoadingVBlank')
        self.assertNotEqual(bytes(self.cpu.mem_read(0x06603fe0,32)),first)
        self.assertEqual(self.native_calls,2)
        self.assertEqual(self.readhalf(0x07000400),88)
        self.assertEqual(self.readhalf(0x07000404),0xf1f8)
        # Preserve unrelated native display changes made during the lease.
        self.write(0x04001000,self.word(0x04001000)|0x400)
        self.invoke('CoopLoadingEnd')
        self.assertEqual(self.word(0x04001000),self.display|0x400)
        self.assertEqual(self.readhalf(0x0400106c),0x8010)
        self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),self.tiles)
        self.assertEqual(bytes(self.cpu.mem_read(0x05000600,512)),self.palette)
        self.assertEqual(bytes(self.cpu.mem_read(0x07000400,1024)),self.oam)
        self.assertEqual(self.word(0x02099fe4),self.native_irq)
        self.assertEqual(self.stats()[:4],(1,1,2,0))
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_decompress_yields_owned_bytes_then_restores_new_asset_not_stale_backup(self):
        self.invoke('CoopLoadingAllow')
        def writer(args):
            self.assertEqual(args[:2],(0x023d0000,0x06600000))
            self.assertEqual(self.active(),0)
            self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),self.tiles)
            self.cpu.mem_write(0x06600000,b'\x55'*0x4000)
        self.writer=writer;self.invoke('CoopLoadingDecompress',0x023d0000,0x06600000)
        self.assertEqual(self.active(),1)
        self.invoke('CoopLoadingEnd')
        self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),b'\x55'*0x4000)
        self.assertEqual(self.stats()[3],1)

    def test_palette_writer_preserves_exact_native_arguments_and_releases_new_colors(self):
        self.invoke('CoopLoadingAllow')
        def writer(args):
            self.assertEqual(args,(0x023d0000,0x120,0xe0));self.assertEqual(self.active(),0)
            self.cpu.mem_write(0x05000720,b'\x63'*0xe0)
        self.writer=writer;self.invoke('CoopLoadingObjPalette',0x023d0000,0x120,0xe0)
        self.invoke('CoopLoadingEnd')
        self.assertEqual(bytes(self.cpu.mem_read(0x05000720,0xe0)),b'\x63'*0xe0)

    def test_direct_file_writer_blocks_reacquisition_and_preserves_native_return(self):
        self.invoke('CoopLoadingAllow')
        def writer(args):
            self.assertEqual(args,(0x023e0000,0x05000600,512));self.assertEqual(self.active(),0)
            self.assertEqual(self.word(self.runtime['coopLoadingWriting']),1)
            self.cpu.mem_write(0x05000600,b'\x49'*512)
        self.writer=writer
        self.assertEqual(self.invoke('CoopLoadingReadAt',0x023e0000,0x05000600,512),321)
        self.assertEqual(self.active(),1);self.invoke('CoopLoadingEnd')
        self.assertEqual(bytes(self.cpu.mem_read(0x05000600,512)),b'\x49'*512)

    def test_unrelated_heap_decompression_does_not_suspend_feedback(self):
        self.invoke('CoopLoadingAllow');self.invoke('CoopLoadingDecompress',0x023d0000,0x023e0000)
        self.assertEqual(self.delegates[0][2],1);self.assertEqual(self.active(),1)
        self.assertEqual(self.stats()[3],0)

    def test_native_disable_banks_restores_before_reassignment_and_allows_later_restart(self):
        self.invoke('CoopLoadingAllow');self.invoke('CoopLoadingDisableBanks')
        self.assertEqual(self.active(),0);self.assertEqual(self.word(0x02099fe4),self.native_irq)
        self.assertEqual(self.cpu.mem_read(0x04000249,1),b'\0')
        self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),self.tiles)
        self.call(self.game['_ZN2GX16SetBankForSubOBJEt'],0x100)
        self.invoke('CoopLoadingBegin');self.assertEqual(self.active(),1)
        self.invoke('CoopLoadingEnd');self.assertEqual(self.stats()[6],0)

    def test_borrow_only_free_bank_and_return_exact_sdk_ownership_and_mapping(self):
        for bank,lcdc in ((0,0),(0x80,0x100)):
            self.cpu.mem_write(0x020a6088,bytes(26));self.half(0x020a6088,lcdc)
            self.cpu.mem_write(0x04000249,bytes((bank,)))
            self.invoke('CoopLoadingAllow');self.assertEqual(self.active(),1)
            self.assertEqual(self.readhalf(0x020a609c),0x100)
            self.invoke('CoopLoadingEnd')
            self.assertEqual(self.cpu.mem_read(0x04000249,1),bytes((bank,)))
            self.assertEqual(self.readhalf(0x020a609c),0)
            self.assertEqual(self.readhalf(0x020a6088),lcdc)

    def test_foreign_bank_ownership_is_never_reassigned(self):
        self.half(0x020a609c,0);self.half(0x020a609a,0x100)
        self.cpu.mem_write(0x04000249,b'\x81')
        self.invoke('CoopLoadingAllow');self.assertEqual(self.active(),0)
        self.assertEqual(self.cpu.mem_read(0x04000249,1),b'\x81')
        self.assertEqual(self.stats()[4],1)
        self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),self.tiles)

    def test_unknown_irq_disabled_engine_and_unsupported_obj_layout_are_untouched(self):
        for address,value in ((0x02099fe4,0x02000000),(0x04000304,0),
                              (0x04001000,self.display|0x10),
                              (0x04001000,self.display|0x100000),
                              (0x04001000,self.display|0x80000000)):
            old=self.word(address);self.write(address,value)
            self.invoke('CoopLoadingAllow');self.assertEqual(self.active(),0)
            self.write(address,old)
        self.assertEqual(self.stats()[5],5)
        self.assertEqual(bytes(self.cpu.mem_read(0x06600000,0x4000)),self.tiles)

    def test_offline_or_not_requested_never_changes_hardware(self):
        self.invoke('CoopLoadingBegin');self.assertEqual(self.active(),0)
        self.write(self.runtime['coopEnabled'],0)
        self.invoke('CoopLoadingAllow');self.assertEqual(self.active(),0)
        self.assertEqual(self.stats(),(0,)*7)
        self.assertEqual(self.word(0x04001000),self.display)
        self.assertEqual(self.word(0x02099fe4),self.native_irq)


if __name__=='__main__':unittest.main()
