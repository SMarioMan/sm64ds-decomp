"""Native cylinder pair processing parity with an optional axis broadphase.

Unicorn executes the retail list walk, virtual calls, native horizontal length
and SDK sqrt wrapper. The isolated adapter supplies only the hardware SQRT
result. No live emulator, collision list or wireless packet is modified.
"""
import math
import random
import struct
import unittest
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R8,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC)
from test_particle_heap import HeapHarness


class CollisionBroadphaseTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_COLLISION_FIXTURE'
    default_fixture='/workspace/runtime/bob-native-process-steady/steady-bob-0'

    def setUp(self):
        super().setUp()
        if 'CoopCollisionHorizontalRead' not in self.runtime:
            self.skipTest('requires --experimental-collision-broadphase build')
        self.cpu.mem_map(0x01200000,0x10000)
        self.first=0x01200000;self.other=0x01200040;self.vector=0x01200200
        self.sqrt_reads=0
        def hardware(cpu,access,address,size,value,user):
            if address!=0x040002b4:return
            value=int.from_bytes(cpu.mem_read(0x040002b8,8),'little')
            cpu.mem_write(0x040002b4,struct.pack('<I',math.isqrt(value)))
            self.sqrt_reads+=1
        self.cpu.hook_add(UC_HOOK_MEM_READ,hardware)
        # The original signed-result SDK sqrt wrapper and vector multiply run
        # unchanged. Hardware control is not busy in this isolated adapter.
        self.original_pair_word=self.word(0x02014bb4)

    def vector_value(self,x,z):
        self.cpu.mem_write(self.vector,struct.pack('<iii',x,0,z))

    def helper(self,x,z,a,b):
        self.vector_value(x,z)
        self.write(self.first+4,a);self.write(self.other+4,b)
        self.write(0x01200300,self.first)
        self.cpu.reg_write(UC_ARM_REG_R4,0x01200300)
        self.cpu.reg_write(UC_ARM_REG_R8,self.other)
        return self.call('CoopCollisionHorizontalRead',self.vector)

    def native_length(self,x,z):
        self.vector_value(x,z)
        return self.call(self.game['Vec3_HorzLen'],self.vector)

    def test_axis_rejection_only_removes_pairs_native_distance_already_rejects(self):
        rng=random.Random(0xc0111510)
        for _ in range(600):
            a=rng.randrange(1,400*4096);b=rng.randrange(1,400*4096)
            x=rng.randrange(-8000*4096,8000*4096);z=rng.randrange(-8000*4096,8000*4096)
            native=self.native_length(x,z);before=self.sqrt_reads
            value=self.helper(x,z,a,b)
            if abs(x)>=a+b or abs(z)>=a+b:
                self.assertGreaterEqual(native,a+b)
                self.assertEqual(value,a+b)
                self.assertEqual(self.sqrt_reads,before)
            else:
                self.assertEqual(value,native)
                self.assertEqual(self.sqrt_reads,before+1)

    def test_touching_near_coincident_and_diagonal_cases_keep_native_collision_decision(self):
        radius=100*4096
        for x,z in ((0,0),(1,0),(radius-1,0),(radius,0),(radius+1,0),
                    (-radius,0),(0,-radius),(radius-1,radius-1),(radius//2,radius//2)):
            with self.subTest(x=x,z=z):
                native=self.native_length(x,z)
                value=self.helper(x,z,radius//2,radius//2)
                self.assertEqual(native<radius,value<radius)
                if value<radius:self.assertEqual(value,native)
                self.assertEqual(bytes(self.cpu.mem_read(self.vector,12)),struct.pack('<iii',x,0,z))

    def test_unusual_radius_and_native_overflow_domain_delegate_exactly(self):
        for x,z,a,b in ((0x20000000,1,1,1),(-0x80000000,0,1,1),
                         (1,0,-1,4),(1,0,0,0),(100,0,0x20000000,1),
                         (0x7fffffff,0x7fffffff,1,1)):
            with self.subTest(x=x,z=z,a=a,b=b):
                native=self.native_length(x,z);before=self.sqrt_reads
                self.assertEqual(self.helper(x,z,a,b),native)
                self.assertEqual(self.sqrt_reads,before+1)

    def test_offline_disabled_and_nonplaying_network_states_preserve_native_length(self):
        expected=self.native_length(100000,200000)
        for enabled,net in ((0,4),(1,0),(1,1),(1,2),(1,3),(1,6)):
            self.write(self.runtime['coopEnabled'],enabled);self.write(0x0209fc68,net)
            before=self.sqrt_reads
            self.assertEqual(self.helper(100000,200000,1,1),expected)
            self.assertEqual(self.sqrt_reads,before+1)

    def test_exact_native_callsite_adapter_preserves_stack_arguments_and_saved_registers(self):
        head=0x01200300;self.write(head,self.first)
        self.write(self.first+4,10);self.write(self.other+4,20);self.vector_value(100,200)
        regs=((UC_ARM_REG_R1,0x11111111),(UC_ARM_REG_R2,0x22222222),
              (UC_ARM_REG_R3,0x33333333),(UC_ARM_REG_R4,head),
              (UC_ARM_REG_R8,self.other),(UC_ARM_REG_R12,0xcccccccc))
        for reg,value in regs:self.cpu.reg_write(reg,value)
        self.cpu.reg_write(UC_ARM_REG_R0,self.vector)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000);self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime['CoopCollisionHorizontalRead'],self.base+0xff00,count=10000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R0),30)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_SP),0x023fc000)
        # r0-r3/r12 are native caller-saved scratch, just as with the norm.
        for reg,value in regs:
            if reg in (UC_ARM_REG_R4,UC_ARM_REG_R8):self.assertEqual(self.cpu.reg_read(reg),value)

    def native_process(self,colliders,patched):
        nodes=0x01201000;vtable=0x01200400;get_pos=0x01200500;get_owner=0x01200510
        self.cpu.mem_write(get_pos,bytes.fromhex('300080e21eff2fe1')) # add r0,r0,#0x30; bx lr
        self.cpu.mem_write(get_owner,bytes.fromhex('3c0090e51eff2fe1')) # ldr r0,[r0,#0x3c]; bx lr
        self.write(vtable+8,get_pos);self.write(vtable+12,get_owner)
        self.cpu.mem_write(nodes,bytes(len(colliders)*0x40))
        for i,(x,y,z,radius,height,flags,vuln,owner) in enumerate(colliders):
            p=nodes+i*0x40
            for offset,value in ((0,vtable),(4,radius),(8,height),(0x18,flags),(0x1c,vuln),
                                  (0x28,p-0x40 if i else 0),
                                  (0x2c,p+0x40 if i+1<len(colliders) else 0),(0x3c,owner)):
                self.write(p+offset,value)
            self.cpu.mem_write(p+0x30,struct.pack('<iii',x,y,z))
        self.write(0x0209cee8,nodes)
        target=self.runtime['CoopCollisionHorizontalRead']
        self.write(0x02014bb4,0xeb000000|(((target-0x02014bbc)>>2)&0xffffff) if patched else self.original_pair_word)
        self.cpu.ctl_remove_cache(0x02014bb4,0x02014bb8)
        before=self.sqrt_reads
        self.call(self.game['_ZN5dCc_c7ProcessEv'])
        self.assertEqual(self.word(0x0209cee8),0)
        return bytes(self.cpu.mem_read(nodes,len(colliders)*0x40)),self.sqrt_reads-before

    def test_whole_native_list_processing_preserves_contacts_flags_owners_and_unlink_order(self):
        rng=random.Random(191)
        colliders=[]
        for i in range(96):
            # Nearby contacts, separated same-height pairs, disjoint heights,
            # shared owners and masks are all processed by the original walk.
            x=rng.randrange(-10,11)*100*4096;z=rng.randrange(-10,11)*100*4096
            y=rng.choice((0,0,500*4096));radius=rng.randrange(25,200)*4096
            flags=rng.choice((2,2,0x100000,0x4000002));vuln=rng.choice((2,0x100000,0x4100002))
            colliders.append((x,y,z,radius,200*4096,flags,vuln,i//2+1))
        native,native_sqrts=self.native_process(colliders,False)
        optimized,optimized_sqrts=self.native_process(colliders,True)
        self.assertEqual(optimized,native)
        self.assertLess(optimized_sqrts,native_sqrts//3)
        self.assertGreater(native_sqrts,500)
