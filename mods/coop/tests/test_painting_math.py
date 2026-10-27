"""Compare compiled painting coefficients with the original ripple arithmetic.

Unicorn privately adapts DS divider result registers; it never edits a live
party, its packets, or its painting geometry.
"""
import math
import random
import struct
import unittest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from test_particle_heap import HeapHarness


class PaintingMathTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopPaintingHeight' not in self.runtime:
            self.skipTest('requires --experimental-painting-math build')
        overlay=self.stock.loadArm9Overlays()[80]
        self.cpu.mem_write(overlay.ramAddress,bytes(overlay.data))
        self.actor=0x023f0000;self.params=0x023f1000
        self.cpu.mem_write(self.actor,bytes(0x1bc))
        self.write(self.actor+8,0x2466)
        self.write(self.actor+0x1ac,self.params)
        self.parameters([65536,3640,1228800,3686400,100])
        self.clock(6800,100)
        self.instructions=0;self.divisions=0
        def hardware(cpu,access,address,size,value,user):
            if address not in (0x040002a0,0x040002a4,0x040002a8,0x040002ac):return
            mode=int.from_bytes(cpu.mem_read(0x04000280,2),'little')&3
            n=int.from_bytes(cpu.mem_read(0x04000290,4 if mode==0 else 8),'little',signed=True)
            d=int.from_bytes(cpu.mem_read(0x04000298,8 if mode==2 else 4),'little',signed=True)
            q=(1 if n<0 else -1) if d==0 else (abs(n)//abs(d))*(-1 if (n<0)!=(d<0) else 1)
            rem=n if d==0 else n-q*d
            cpu.mem_write(0x040002a0,struct.pack('<QQ',q&0xffffffffffffffff,rem&0xffffffffffffffff))
        def count(cpu,address,size,user):
            self.instructions+=1
            if address in (self.game['_ZN4cstd4fdivEii'],0x01ffabe4):self.divisions+=1
        self.cpu.hook_add(UC_HOOK_MEM_READ,hardware)
        self.cpu.hook_add(UC_HOOK_CODE,count)

    def parameters(self,values):self.cpu.mem_write(self.params,struct.pack('<5i',*values))
    def clock(self,phase,timer):self.cpu.mem_write(self.actor+0x1b4,struct.pack('<hH',phase,timer))
    def stats(self):return struct.unpack('<3I',self.cpu.mem_read(self.runtime['coopPaintingMathStats'],12))
    def compare(self,distance):
        expected=self.call(0x02125bb0,self.actor,distance)
        self.assertEqual(self.call('CoopPaintingHeight',self.actor,distance),expected)

    def test_grid_distances_match_native_across_wave_phases_and_clock_changes(self):
        # Native20x20 grid spacing; radial input is sampled on both sides of
        # the wave radius, with all native rounding left in the ARM routines.
        distances=sorted({math.isqrt((x*150000-1425000)**2+(y*150000-1425000)**2)
            for x in range(20) for y in range(20)})
        for phase,timer in ((6800,100),(0,100),(32767,100),(-32768,100),(1550,1),(-2000,0)):
            self.clock(phase,timer)
            for d in distances:self.compare(d)

    def test_each_coefficient_input_is_part_of_the_cache_key(self):
        original=[65536,3640,1228800,3686400,100]
        self.compare(100000)
        for index,value in enumerate((98304,5000,2000000,2500000,150)):
            p=original.copy();p[index]=value;self.parameters(p)
            self.compare(100000);self.compare(200000)
        self.assertEqual(self.stats()[1],6)

    def test_signed_inputs_and_fixed_point_rounding_match_native(self):
        rng=random.Random(307)
        for i in range(120):
            p=[rng.randint(-150000,150000),3640,rng.choice((-1,1))*rng.randint(1,4000000),
               rng.choice((-1,1))*rng.randint(1,5000000),rng.choice((-100,1,100,1000))]
            self.parameters(p);self.clock(rng.randint(-32768,32767),rng.randint(1,65535))
            self.compare(rng.randint(-5000000,5000000))

    def test_other_native_painting_states_and_offline_rules_are_unchanged(self):
        for mode in (0,2,3):
            self.write(self.actor+8,(mode<<13)|0x466)
            for d in (0,1000,2000000):self.compare(d)
        self.write(self.actor+8,0x2466)
        self.write(self.runtime['coopEnabled'],0)
        self.compare(123456)
        self.assertEqual(self.stats()[2],10)

    def test_helpers_do_not_mutate_wave_state_randomness_or_parameters(self):
        before=bytes(self.cpu.mem_read(self.actor,0x1bc))+bytes(self.cpu.mem_read(self.params,20))
        seed=self.word(0x0209e650)
        for d in (0,1,12345,3000000):self.compare(d)
        after=bytes(self.cpu.mem_read(self.actor,0x1bc))+bytes(self.cpu.mem_read(self.params,20))
        self.assertEqual(before,after)
        self.assertEqual(self.word(0x0209e650),seed)

    def test_phase_changes_reuse_coefficients_and_reduce_executed_work(self):
        distances=[math.isqrt((x*150000-1425000)**2+(y*150000-1425000)**2)
            for x in range(20) for y in range(20)]
        self.instructions=self.divisions=0
        expected=[self.call(0x02125bb0,self.actor,d) for d in distances]
        native=self.instructions;native_divisions=self.divisions
        self.instructions=self.divisions=0
        actual=[self.call('CoopPaintingHeight',self.actor,d) for d in distances]
        optimized=self.instructions;optimized_divisions=self.divisions
        self.assertEqual(actual,expected)
        self.assertLess(optimized,native)
        self.assertEqual(optimized_divisions,3)
        self.assertEqual(native_divisions,1200)
        self.clock(12345,100);self.compare(777777)
        self.assertEqual(self.stats()[1],1)
        print('Painting400-cell isolated ARM instructions:',native,optimized,
              'native divisions:',native_divisions,optimized_divisions)


if __name__=='__main__':unittest.main()
