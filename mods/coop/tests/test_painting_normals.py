"""Compare complete native wave meshes after the verified normal/flatten pair.

Private Unicorn replay supplies hardware divider/SQRT results. No live game,
network packet, vertex, or emulator core is modified.
"""
import math
import random
import struct
import unittest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from test_particle_heap import HeapHarness


class PaintingMeshHarness(HeapHarness):
    def setUp(self):
        super().setUp()
        if 'CoopPaintingNormals' not in self.runtime:
            self.skipTest('requires --experimental-painting-normals build')
        overlay=self.stock.loadArm9Overlays()[80]
        self.cpu.mem_write(overlay.ramAddress,bytes(overlay.data))
        self.actor=0x023f0000;self.vertices=0x023e0000
        self.cpu.mem_write(self.actor,bytes(0x1bc))
        self.write(self.actor+8,0x2466)
        self.write(self.actor+0x1a0,self.vertices)
        self.instructions=0;self.normalizations=0
        def hardware(cpu,access,address,size,value,user):
            if address==0x040002b4:
                mode=int.from_bytes(cpu.mem_read(0x040002b0,2),'little')&1
                n=int.from_bytes(cpu.mem_read(0x040002b8,8 if mode else 4),'little')
                cpu.mem_write(address,struct.pack('<I',math.isqrt(n)))
            if address not in (0x040002a0,0x040002a4,0x040002a8,0x040002ac):return
            mode=int.from_bytes(cpu.mem_read(0x04000280,2),'little')&3
            n=int.from_bytes(cpu.mem_read(0x04000290,4 if mode==0 else 8),'little',signed=True)
            d=int.from_bytes(cpu.mem_read(0x04000298,8 if mode==2 else 4),'little',signed=True)
            q=(1 if n<0 else -1) if d==0 else (abs(n)//abs(d))*(-1 if (n<0)!=(d<0) else 1)
            r=n if d==0 else n-q*d
            cpu.mem_write(0x040002a0,struct.pack('<QQ',q&0xffffffffffffffff,r&0xffffffffffffffff))
        def count(cpu,address,size,user):
            self.instructions+=1
            if address==self.game['NormalizeVec3']:self.normalizations+=1
        self.cpu.hook_add(UC_HOOK_MEM_READ,hardware)
        self.cpu.hook_add(UC_HOOK_CODE,count)

    def grid(self,rows=20,cols=None,flat=False,reverse=False):
        cols=rows if cols is None else cols
        self.cpu.mem_write(self.actor+0x1b8,struct.pack('<HBB',rows*cols,cols,rows))
        width=height=7*0x64000
        data=bytearray()
        for y in range(rows):
            for x in range(cols):
                px=width*x//(cols-1);py=height*y//(rows-1)
                if reverse:px,py=width-px,height-py
                z=0 if flat else (x*x*123+y*543-12500)
                data+=struct.pack('<4iII',px,py,z,100000+x*13+y*17,0xdeadbeef,x+y*32)
        data+=bytes(24*64) # Native rectangular-stride fallback may read padding.
        self.cpu.mem_write(self.vertices,bytes(data))
        return bytes(data)

    def compare(self,raw):
        actor=bytes(self.cpu.mem_read(self.actor,0x1bc));seed=self.word(0x0209e650)
        self.instructions=self.normalizations=0
        self.call(0x02125940,self.actor);self.call(0x02125af0,self.actor)
        expected=bytes(self.cpu.mem_read(self.vertices,len(raw)))
        native=(self.instructions,self.normalizations)
        self.cpu.mem_write(self.vertices,raw)
        self.instructions=self.normalizations=0
        self.call('CoopPaintingNormals',self.actor);self.call(0x02125af0,self.actor)
        actual=bytes(self.cpu.mem_read(self.vertices,len(raw)))
        optimized=(self.instructions,self.normalizations)
        self.assertEqual(actual,expected)
        self.assertEqual(bytes(self.cpu.mem_read(self.actor,0x1bc)),actor)
        self.assertEqual(self.word(0x0209e650),seed)
        return native,optimized

    def stats(self):return struct.unpack('<3I',self.cpu.mem_read(self.runtime['coopPaintingNormalStats'],12))



class PaintingNormalTests(PaintingMeshHarness,unittest.TestCase):
    def test_wave_mesh_matches_native_without_overwriting_neighbour_border_heights(self):
        raw=self.grid();native,optimized=self.compare(raw)
        self.assertEqual(self.stats(),(1,0,76))
        self.assertEqual(native[1],400);self.assertEqual(optimized[1],324)
        self.assertLess(optimized[0],native[0])
        print('Painting400-cell normal/flatten ARM instructions:',native[0],optimized[0],
              'native normalizations:',native[1],optimized[1])

    def test_flat_and_reversed_regular_grids_match_native(self):
        for flat,reverse in ((True,False),(False,True),(True,True)):
            self.compare(self.grid(flat=flat,reverse=reverse))
        self.assertEqual(self.stats(),(3,0,228))

    def test_minimum_and_maximum_supported_grids_match_native(self):
        for rows in (2,32):self.compare(self.grid(rows))
        self.assertEqual(self.stats(),(2,0,128))

    def test_nonregular_grid_falls_back_before_any_mesh_write(self):
        self.grid();self.write(self.vertices+(7*20+8)*24,123456)
        raw=bytes(self.cpu.mem_read(self.vertices,24*(400+64)))
        native,optimized=self.compare(raw)
        self.assertEqual(self.stats(),(0,1,0));self.assertEqual(optimized[1],native[1])

    def test_rectangular_grid_and_inconsistent_count_use_native(self):
        self.compare(self.grid(20,19))
        raw=self.grid();self.cpu.mem_write(self.actor+0x1b8,struct.pack('<H',399))
        self.compare(raw)
        self.assertEqual(self.stats(),(0,2,0))

    def test_signed_coordinate_difference_and_product_wrapping_match_native(self):
        self.grid(3)
        xs=(0,-2147483648,2147483647);ys=(0,2147483647,-2147483648)
        rng=random.Random(307)
        for y in range(3):
            for x in range(3):
                self.cpu.mem_write(self.vertices+(y*3+x)*24,struct.pack('<3i',
                    xs[x],ys[y],rng.randint(-2147483648,2147483647)))
        self.compare(bytes(self.cpu.mem_read(self.vertices,24*(9+64))))
        self.assertEqual(self.stats()[0],1)

    def test_offline_and_disabled_modes_keep_native_normalization(self):
        raw=self.grid();self.write(self.runtime['coopEnabled'],0)
        self.compare(raw)
        self.write(self.runtime['coopEnabled'],1);self.write(0x0209fc68,0)
        self.compare(self.grid())
        self.assertEqual(self.stats(),(0,2,0))


if __name__=='__main__':unittest.main()
