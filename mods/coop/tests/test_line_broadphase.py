"""Conservative line-query sphere rejection against native rounded ARM distance.

All fixture edits and hardware arithmetic adapters are private Unicorn work.
No live emulator state, collision results or radio packets are injected.
"""
import math
import random
import struct
import unittest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_R6
from test_particle_heap import HeapHarness


class LineHardwareHarness(HeapHarness):
    fixture_variable='COOP_LINE_BROADPHASE_FIXTURE'
    default_fixture='/workspace/runtime/actor-profile-performance/first-course-0'

    def setUp(self):
        super().setUp()
        self.a=0x023f1000;self.b=self.a+12;self.sqrt_reads=0;self.instructions=0
        def hardware(cpu,access,address,size,value,user):
            if address==0x040002b4:
                n=int.from_bytes(cpu.mem_read(0x040002b8,8),'little')
                cpu.mem_write(address,struct.pack('<I',math.isqrt(n)));self.sqrt_reads+=1
            elif address in (0x040002a0,0x040002a4,0x040002a8,0x040002ac):
                mode=int.from_bytes(cpu.mem_read(0x04000280,2),'little')&3
                n=int.from_bytes(cpu.mem_read(0x04000290,4 if mode==0 else 8),'little',signed=True)
                d=int.from_bytes(cpu.mem_read(0x04000298,8 if mode==2 else 4),'little',signed=True)
                q=(1 if n<0 else -1) if d==0 else (abs(n)//abs(d))*(-1 if (n<0)!=(d<0) else 1)
                r=n if d==0 else n-q*d
                cpu.mem_write(0x040002a0,struct.pack('<QQ',q&0xffffffffffffffff,r&0xffffffffffffffff))
        def count(cpu,address,size,user):self.instructions+=1
        self.cpu.hook_add(UC_HOOK_MEM_READ,hardware);self.cpu.hook_add(UC_HOOK_CODE,count)

    def vectors(self,a,b):self.cpu.mem_write(self.a,struct.pack('<6i',*(a+b)))
    def native(self):return self.call(self.game['Vec3_Dist'],self.a,self.b)
    def helper(self,limit):return self.call('CoopLineSphereDistance',self.a,self.b,limit)
    def branch(self,target):
        address=0x020387a4
        self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))
        self.cpu.ctl_remove_cache(address,address+4)

class LineBroadphaseTests(LineHardwareHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopLineSphereDistance' not in self.runtime:
            self.skipTest('requires --experimental-line-broadphase')

    def test_random_safe_domain_preserves_rejects_and_all_candidate_distances(self):
        rng=random.Random(0x11e)
        for _ in range(600):
            a=tuple(rng.randrange(-0x10000000,0x10000000) for _ in range(3))
            b=tuple(rng.randrange(-0x10000000,0x10000000) for _ in range(3))
            limit=rng.randrange(0x1fffffff);self.vectors(a,b)
            native=self.native();before=self.sqrt_reads;value=self.helper(limit)
            self.assertEqual(value>limit,native>limit)
            if any(abs(x-y)>limit for x,y in zip(a,b)):
                self.assertEqual(value,limit+1);self.assertEqual(self.sqrt_reads,before)
            else:
                self.assertEqual(value,native);self.assertEqual(self.sqrt_reads,before+1)

    def test_touching_diagonal_signed_and_rounded_boundaries(self):
        for limit in (0,1,2,4096,0x1ffffffe):
            for xyz in ((0,0,0),(limit,0,0),(limit+1,0,0),(-limit,0,0),
                        (0,limit,0),(0,0,-limit-1),(1,1,1),(2,2,0),(4096,4096,0)):
                # Keep vectors in the guarded domain; large thresholds are
                # still exercised with small and diagonal vectors.
                if max(abs(x) for x in xyz)>=0x10000000:continue
                self.vectors((0,0,0),xyz)
                self.assertEqual(self.helper(limit)>limit,self.native()>limit)
        self.vectors((-0x10000000,0,0),(0x0fffffff,0,0))
        self.assertEqual(self.helper(0x1ffffffe),0x1fffffff)

    def test_unusual_coordinates_thresholds_and_wrap_delegate_exactly(self):
        for a,b,limit in (((0x20000000,0,0),(0,0,0),1),
            ((-0x20000000,0,0),(0,0,0),1),
            ((-0x80000000,0,0),(0x7fffffff,0,0),1),
            ((0x7fffffff,0x7fffffff,0x7fffffff),(0,0,0),1),
            ((1000,0,0),(0,0,0),-1),((1000,0,0),(0,0,0),0x1fffffff)):
            self.vectors(a,b);native=self.native();before=self.sqrt_reads
            self.assertEqual(self.helper(limit),native);self.assertEqual(self.sqrt_reads,before+1)

    def test_offline_disabled_and_nonplaying_modes_retain_native_length(self):
        self.vectors((100000,200000,300000),(0,0,0));native=self.native()
        for enabled,net in ((0,4),(1,0),(1,1),(1,2),(1,3),(1,6)):
            self.write(self.runtime['coopEnabled'],enabled);self.write(0x0209fc68,net)
            before=self.sqrt_reads;self.assertEqual(self.helper(1),native)
            self.assertEqual(self.sqrt_reads,before+1)

    def test_bridge_uses_native_radius_registers_and_preserves_them(self):
        self.vectors((100000,0,0),(0,0,0))
        self.cpu.reg_write(UC_ARM_REG_R4,100);self.cpu.reg_write(UC_ARM_REG_R6,200)
        self.assertEqual(self.call('CoopLineSphereRead',self.a,self.b),301)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R4),100)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R6),200)

    def test_captured_coin_queries_and_complete_actor_bytes_match_with_less_work(self):
        node=self.word(0x0209b468);actors=[]
        while node:
            actor=self.word(node+8)
            if int.from_bytes(self.cpu.mem_read(actor+12,2),'little') in (288,289,290):actors.append(actor)
            node=self.word(node+4)
        self.assertGreaterEqual(len(actors),60)
        ram=bytes(self.cpu.mem_read(0x02000000,0x400000));query_rows=[];active=[]
        def query(cpu,address,size,user):
            if address==0x02038638:
                from unicorn.arm_const import UC_ARM_REG_LR
                active.append((cpu.reg_read(UC_ARM_REG_LR),cpu.reg_read(UC_ARM_REG_R0)))
            elif active and address==active[-1][0]:
                _,pointer=active.pop();query_rows.append(bytes(cpu.mem_read(pointer,0x78)))
        self.cpu.hook_add(UC_HOOK_CODE,query)
        def run(optimized):
            results=[];queries=[];start=self.instructions;reads=self.sqrt_reads
            for actor in actors:
                self.cpu.mem_write(0x02000000,ram)
                self.branch(self.runtime['CoopLineSphereRead'] if optimized else self.game['Vec3_Dist'])
                self.write(actor+0xb0,self.word(actor+0xb0)&~0x38)
                query_rows.clear();active.clear()
                self.call(0x020b2324,actor)
                results.append(bytes(self.cpu.mem_read(actor,0x3b4)))
                queries.append(list(query_rows))
            return results,queries,self.instructions-start,self.sqrt_reads-reads
        native=run(False);optimized=run(True)
        self.assertEqual(optimized[:2],native[:2])
        print('Captured coins: actors/instructions/sqrt reads:',len(actors),native[2:],optimized[2:])
        self.assertLess(optimized[3],native[3]);self.assertLess(optimized[2],native[2])
