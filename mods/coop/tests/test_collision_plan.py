"""Pressure-reclaimable ordered spatial planning against the native collision walk.

Private RAM/heap replay only. The hardware SQRT result is adapted in isolation;
no live emulator memory, wireless packets or game positions are altered.
"""
import math
import random
import struct
import unittest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from test_particle_heap import HeapHarness


class CollisionPlanTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_COLLISION_PLAN_FIXTURE'
    default_fixture='/workspace/runtime/animation-cache-collision-leaf-cost-profile/before-steady-3'

    def setUp(self):
        super().setUp()
        if 'CoopCollisionProcess' not in self.runtime:
            self.skipTest('requires --experimental-collision-plan build')
        self.write(0x020a613c,self.game['data_020a621c'])
        self.cpu.mem_write(0x020a0f1c,b'\0\0')
        self.sqrt_calls=0
        self.native_notifications=[]
        self.notification_action=None
        self.notification_stub=0
        def hardware(cpu,access,address,size,value,user):
            if address==0x040002b4:
                n=int.from_bytes(cpu.mem_read(0x040002b8,8),'little')
                cpu.mem_write(address,struct.pack('<I',math.isqrt(n)));self.sqrt_calls+=1
        def division(cpu,access,address,size,value,user):
            if address not in (0x040002a0,0x040002a4,0x040002a8,0x040002ac):return
            mode=int.from_bytes(cpu.mem_read(0x04000280,2),'little')&3
            n=int.from_bytes(cpu.mem_read(0x04000290,4 if mode==0 else 8),'little',signed=True)
            d=int.from_bytes(cpu.mem_read(0x04000298,8 if mode==2 else 4),'little',signed=True)
            q=(1 if n<0 else -1) if d==0 else (abs(n)//abs(d))*(-1 if (n<0)!=(d<0) else 1)
            r=n if d==0 else n-q*d
            cpu.mem_write(0x040002a0,struct.pack('<QQ',q&0xffffffffffffffff,r&0xffffffffffffffff))
        def notify(cpu,address,size,user):
            if address!=self.game['func_02014f44']:return
            self.native_notifications.append((cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)))
            if self.notification_action:self.notification_action()
            if self.notification_stub:
                cpu.reg_write(UC_ARM_REG_PC,self.notification_stub);return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_MEM_READ,hardware);self.cpu.hook_add(UC_HOOK_MEM_READ,division)
        self.cpu.hook_add(UC_HOOK_CODE,notify)
        # Restore retail callsites from a fixture containing the old late guard.
        for address in (0x02014b0c,0x02014bb4,0x02014d0c,0x02014dcc):
            section=next(s for s in self.main.sections if s.ramAddress<=address<s.ramAddress+len(s.data))
            self.cpu.mem_write(address,bytes(section.data[address-section.ramAddress:address-section.ramAddress+4]))
        for address,name in ((0x0203c6bc,'CoopCollisionVAllocate'),(0x0203c568,'CoopCollisionVReallocate'),
                             (0x0203c5d0,'CoopAnimationMaxMemory'),(0x0203c5f8,'CoopAnimationMaxMemory'),
                             (0x0203c5ac,'CoopAnimationMemoryLeft')):
            self.branch(address,self.runtime[name])

    def branch(self,address,target,link=False):
        self.write(address,(0xeb000000 if link else 0xea000000)|(((target-address-8)>>2)&0xffffff))
        self.cpu.ctl_remove_cache(address,address+4)

    def install(self):
        self.branch(0x02014b0c,self.runtime['CoopCollisionPairRead'])
        for address in (0x02014d0c,0x02014dcc):self.branch(address,self.runtime['CoopCollisionNotify'],True)

    def workspace(self):return self.word(self.runtime['coopCollisionPlan'])
    def stats(self):return struct.unpack('<8I',self.cpu.mem_read(self.runtime['coopCollisionPlanStats'],32))
    def prepare(self):self.call('CoopPrepareCollisionPlan')
    def native_nodes(self):
        nodes=[];p=self.word(0x0209cee8)
        while p:
            self.assertNotIn(p,nodes);nodes.append(p);p=self.word(p+0x2c)
        return nodes

    def test_captured_native_list_contacts_match_and_far_pairs_are_not_walked(self):
        self.install();nodes=self.native_nodes();self.assertEqual(len(nodes),160)
        before=bytes(self.cpu.mem_read(0x02000000,0x400000))
        section=next(s for s in self.main.sections if s.ramAddress<=0x02014b0c<s.ramAddress+len(s.data))
        original_word=struct.unpack_from('<I',section.data,0x02014b0c-section.ramAddress)[0]
        self.write(0x02014b0c,original_word);self.cpu.ctl_remove_cache(0x02014b0c,0x02014b10)
        self.call(self.game['_ZN5dCc_c7ProcessEv'])
        expected=[bytes(self.cpu.mem_read(p,0x30)) for p in nodes]
        native_sqrts=self.sqrt_calls
        self.cpu.mem_write(0x02000000,before);self.cpu.ctl_remove_cache(0x02014b0c,0x02014b10)
        self.sqrt_calls=0
        self.call('CoopCollisionProcess')
        self.assertEqual([bytes(self.cpu.mem_read(p,0x30)) for p in nodes],expected)
        self.assertEqual(self.word(0x0209cee8),0)
        self.assertTrue(self.workspace())
        self.assertEqual(self.stats()[:2],(1,0))
        self.assertGreaterEqual(self.stats()[2],80);self.assertEqual(self.stats()[2],self.stats()[3])
        self.call('CoopReleaseCollisionPlan',0)
        self.assertEqual(self.workspace(),0)
        self.assertLess(self.sqrt_calls,native_sqrts//10)
        self.assertTrue(self.intact(self.root))

    def test_workspace_is_reclaimable_and_capacity_queries_reclaim_before_deciding(self):
        before=self.largest(self.root);free=self.raw_free()
        self.prepare();self.assertTrue(self.workspace());self.assertLess(self.raw_free(),free)
        self.call('CoopAnimationMaxMemory',self.root)
        self.assertEqual(self.workspace(),0);self.assertEqual(self.largest(self.root),before)
        self.assertEqual(self.stats()[5],1)
        self.assertTrue(self.intact(self.root))

    def test_explicit_root_owner_survives_game_default_heap_and_other_heap_queries(self):
        before=(self.largest(self.root),self.largest(self.game_heap))
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        self.write(self.game['_ZN6Memory14defaultHeapPtrE'],self.game_heap)
        self.call('CoopAnimationMaxMemory',self.game_heap)
        self.assertEqual(self.workspace(),plan)
        self.call('CoopReleaseCollisionPlan',0)
        self.assertEqual((self.largest(self.root),self.largest(self.game_heap)),before)

    def test_pointer_or_order_mismatch_invalidates_and_returns_the_native_next_node(self):
        self.prepare();self.assertTrue(self.workspace())
        nodes=self.native_nodes()
        self.assertEqual(self.call('CoopCollisionCandidate',nodes[0],nodes[2]),nodes[2])
        self.assertEqual(self.workspace(),0)

    def test_unknown_getter_or_unsafe_coordinate_bypasses_without_reordering(self):
        nodes=self.native_nodes();head=nodes[0];old=self.word(head)
        self.write(head,0)
        self.prepare();self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)
        self.write(head,old)
        pos=self.word(head+0x30)+0x5c if self.word(old+8)==0x02014948 else head+(0x34 if self.word(old+8)==0x02014a2c else 0x30)
        old_x=self.word(pos);self.write(pos,0x20000000)
        self.prepare();self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)
        self.write(pos,old_x);self.assertTrue(self.intact(self.root))

    def raw_free(self):
        return self.call(self.game['_ZN22ExpandingHeapAllocator10MemoryLeftEv'],self.word(self.root+0x14))

    def raw_largest(self):
        return self.call(self.game['_ZN22ExpandingHeapAllocator18MaxAllocatableSizeEi'],self.word(self.root+0x14),4)

    def synthetic(self,specs):
        size=len(specs)*0x50+sum(s[8]!=0 for s in specs)*0x100
        arena=self.call(self.game['_ZN5mHeap6Heap_t8AllocateEji'],self.game_heap,size,4)
        self.assertTrue(arena)
        self.cpu.mem_write(arena,bytes(size))
        nodes=[arena+i*0x50 for i in range(len(specs))]
        owners=arena+len(specs)*0x50
        self.synthetic_arena=arena
        self.synthetic_positions=[]
        owner_index=0
        for i,(x,y,z,radius,height,flags,vuln,owner,kind) in enumerate(specs):
            p=nodes[i];actor=owners+owner_index*0x100
            if kind:owner_index+=1
            vt=(0x0208e6bc,0x0208e6d4,0x0208e704)[kind]
            self.write(p,vt);self.write(p+4,radius);self.write(p+8,height)
            self.write(p+0x18,flags);self.write(p+0x1c,vuln)
            self.write(p+0x28,nodes[i-1] if i else 0)
            self.write(p+0x2c,nodes[i+1] if i+1<len(nodes) else 0)
            if kind:self.write(p+0x30,actor)
            if kind:self.write(actor+4,owner)
            position=p+0x30 if kind==0 else actor+0x5c if kind==1 else p+0x34
            self.cpu.mem_write(position,struct.pack('<iii',x,y,z));self.synthetic_positions.append(position)
        self.write(0x0209cee8,nodes[0] if nodes else 0)
        return nodes

    def compare_synthetic(self,specs):
        nodes=self.synthetic(specs);self.install()
        initial=bytes(self.cpu.mem_read(0x02000000,0x400000))
        self.write(0x02014b0c,0xe5940000);self.cpu.ctl_remove_cache(0x02014b0c,0x02014b10)
        for address in (0x02014d0c,0x02014dcc):self.branch(address,self.game['func_02014f44'],True)
        self.native_notifications=[]
        self.call(self.game['_ZN5dCc_c7ProcessEv'])
        expected=[bytes(self.cpu.mem_read(p,0x50)) for p in nodes]
        notifications=list(self.native_notifications)
        self.cpu.mem_write(0x02000000,initial)
        for address in (0x02014b0c,0x02014d0c,0x02014dcc):self.cpu.ctl_remove_cache(address,address+4)
        self.native_notifications=[]
        self.call('CoopCollisionProcess')
        self.assertEqual([bytes(self.cpu.mem_read(p,0x50)) for p in nodes],expected)
        self.assertEqual(self.native_notifications,notifications)
        self.assertEqual(self.word(0x0209cee8),0)
        self.call('CoopReleaseCollisionPlan',0);self.assertEqual(self.workspace(),0)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,self.synthetic_arena)

    def test_randomized_all_three_native_getters_keep_contacts_masks_owners_and_pair_order(self):
        rng=random.Random(0xc0111510)
        for trial in range(8):
            specs=[]
            for i in range(64):
                x=rng.randrange(-12,13)*100*4096;z=rng.randrange(-12,13)*100*4096
                y=rng.choice((0,0,300*4096));radius=rng.randrange(0,200)*4096
                flags=rng.choice((2,0x100002,0x4000002));vuln=rng.choice((2,0x100002,0x4100002))
                specs.append((x,y,z,radius,200*4096,flags,vuln,i//2+1,rng.randrange(3)))
            self.compare_synthetic(specs)

    def test_touching_coincident_zero_radius_and_diagonal_contacts_keep_native_decisions(self):
        specs=[]
        for i in range(64):
            group=i//8;index=i%8
            x=(group*1000+(0,0,100,200,201,0,200,199)[index])*4096
            z=(0,0,0,0,0,100,200,199)[index]*4096
            radius=(0,100,100,100,100,0,100,100)[index]*4096
            specs.append((x,0,z,radius,200*4096,0x4000002,0x4000002,i+1,2))
        self.compare_synthetic(specs)

    def test_nonfatal_workspace_allocation_failure_and_capacity_limits_keep_original_list(self):
        before=self.largest(self.root)
        reserves=[]
        while self.raw_largest()>=1024:
            pointer=self.call('CoopCollisionVAllocate',self.root,self.raw_largest(),4)
            self.assertTrue(pointer);reserves.append(pointer)
        nodes=self.native_nodes();self.prepare()
        self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)
        for pointer in reserves:self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.largest(self.root),before)
        specs=[(i*1000*4096,0,0,10*4096,100*4096,2,2,i+1,0) for i in range(193)]
        nodes=self.synthetic(specs);self.prepare()
        self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)

    def test_real_root_allocation_pressure_reclaims_workspace_and_preserves_heap(self):
        before=self.largest(self.root);reserves=[]
        while self.raw_largest()>=1024:
            size=self.raw_largest();pointer=self.call('CoopCollisionVAllocate',self.root,size,4)
            self.assertTrue(pointer);reserves.append((size,pointer))
        largest=max(reserves);reserves.remove(largest)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,largest[1])
        self.prepare();self.assertTrue(self.workspace())
        request=self.raw_largest()+32
        self.assertLessEqual(request,before)
        pointer=self.call('CoopCollisionVAllocate',self.root,request,4)
        self.assertTrue(pointer);self.assertEqual(self.workspace(),0)
        self.assertEqual(self.stats()[5],1)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        for size,pointer in reserves:self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.largest(self.root),before)

    def test_root_in_place_growth_reclaims_workspace_before_adjacent_native_allocation(self):
        before=self.largest(self.root)
        pointer=self.call('CoopCollisionVAllocate',self.root,65536,4)
        self.assertTrue(pointer);self.cpu.mem_write(pointer,b'unchanged'*32)
        self.prepare();self.assertTrue(self.workspace())
        result=self.call('CoopCollisionVReallocate',self.root,pointer,65664)
        self.assertGreaterEqual(result,65664);self.assertEqual(self.workspace(),0)
        self.assertEqual(bytes(self.cpu.mem_read(pointer,288)),b'unchanged'*32)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.largest(self.root),before)

    def test_offline_disabled_unready_and_short_lists_do_not_allocate_a_plan(self):
        for address,value,width in ((self.runtime['coopEnabled'],0,4),(0x0209fc68,0,4),
                                    (0x020a0f1c,8,2),(0x020a613c,0,4)):
            old=bytes(self.cpu.mem_read(address,width));self.cpu.mem_write(address,value.to_bytes(width,'little'))
            self.prepare();self.assertEqual(self.workspace(),0)
            self.cpu.mem_write(address,old)
        nodes=self.synthetic([(i*100*4096,0,0,40*4096,100*4096,2,2,i+1,2) for i in range(16)])
        self.prepare();self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)

    def test_game_notification_invalidates_before_future_pairs_after_position_changes(self):
        specs=[(i*1000*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)]
        specs[0]=(0,0,0,100*4096,200*4096,0x400000c,0x4000000,1,2)
        specs[1]=(10*4096,0,0,100*4096,200*4096,0x4000000,0x4000000,2,2)
        specs[2]=(5000*4096,0,0,100*4096,200*4096,0x4000000,0x4000000,3,2)
        def move_future_collider():
            if self.workspace():self.assertGreater(self.word(self.runtime['coopCollisionCallbackDepth']),0)
            if len(self.native_notifications)>1:self.assertEqual(self.workspace(),0)
            if len(self.native_notifications)==1:
                self.write(self.synthetic_positions[2],20*4096)
        self.notification_action=move_future_collider
        self.compare_synthetic(specs)
        self.assertGreaterEqual(len(self.native_notifications),2)
        self.assertEqual(self.stats()[4],1)

    def test_pressure_release_between_native_pairs_returns_original_next_pointer(self):
        self.prepare();nodes=self.native_nodes();self.assertTrue(self.workspace())
        self.call('CoopReleaseCollisionPlan',1)
        self.assertEqual(self.call('CoopCollisionCandidate',nodes[0],nodes[1]),nodes[1])
        self.assertEqual(self.workspace(),0)

    def test_dense_preparation_budget_falls_back_and_frees_optional_storage(self):
        before=self.raw_free()
        nodes=self.synthetic([(0,0,0,100*4096,200*4096,2,2,i+1,2) for i in range(64)])
        self.prepare()
        self.assertEqual(self.workspace(),0);self.assertEqual(self.native_nodes(),nodes)
        self.assertEqual(self.stats()[1],1);self.assertEqual(self.stats()[7],1)
        self.assertEqual(self.raw_free(),before);self.assertTrue(self.intact(self.root))

    def test_narrow_z_aligned_layout_uses_the_spread_axis_and_keeps_native_contacts(self):
        specs=[(0,0,i*500*4096,40*4096,200*4096,2,2,i+1,2) for i in range(64)]
        self.compare_synthetic(specs)
        self.assertEqual(self.stats()[0],1);self.assertEqual(self.stats()[7],0)

    def test_root_request_is_atomic_while_plan_is_live_and_restores_enabled_irqs(self):
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        irq_at_allocator=[]
        def allocator_entry(cpu,address,size,user):
            if address==self.game['_ZN22ExpandingHeapAllocator8AllocateEji']:
                irq_at_allocator.append(cpu.reg_read(UC_ARM_REG_CPSR)&0x80)
        self.cpu.hook_add(UC_HOOK_CODE,allocator_entry)
        self.cpu.reg_write(UC_ARM_REG_CPSR,0x5f)
        for reg,value in ((UC_ARM_REG_R0,self.root),(UC_ARM_REG_R1,64),(UC_ARM_REG_R2,4)):
            self.cpu.reg_write(reg,value)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000);self.cpu.reg_write(UC_ARM_REG_LR,self.base+0xff00)
        self.cpu.emu_start(self.runtime['CoopCollisionVAllocate'],self.base+0xff00,count=1000000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),self.base+0xff00)
        pointer=self.cpu.reg_read(UC_ARM_REG_R0);self.assertTrue(pointer)
        self.assertEqual(irq_at_allocator,[0x80]);self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0x80,0)
        self.assertEqual(self.workspace(),plan)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.call('CoopReleaseCollisionPlan',0);self.assertTrue(self.intact(self.root))

    def build_count(self):return self.stats()[0]+self.word(self.runtime['coopCollisionPlanRefreshes'])

    def reuse_count(self):return self.word(self.runtime['coopCollisionPlanReuses'])

    def relink(self,nodes):
        for i,node in enumerate(nodes):
            self.write(node+0x28,nodes[i-1] if i else 0)
            self.write(node+0x2c,nodes[i+1] if i+1<len(nodes) else 0)
        self.write(0x0209cee8,nodes[0] if nodes else 0)

    def position_address(self,node):
        getter=self.word(self.word(node)+8)
        return node+0x30 if getter==0x02014820 else node+0x34 if getter==0x02014a2c else self.word(node+0x30)+0x5c

    def test_fresh_bounds_validate_reuse_and_stage_changes_rebuild(self):
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        self.prepare();self.assertEqual(self.workspace(),plan);self.assertEqual(self.reuse_count(),1)
        head=self.native_nodes()[0];pos=self.position_address(head)
        self.write(pos,self.word(pos)+8*4096);self.write(head+4,self.word(head+4)+4*4096)
        self.prepare();self.assertEqual(self.workspace(),plan);self.assertEqual(self.reuse_count(),2)
        self.assertEqual(self.stats()[0],1)
        self.write(self.runtime['coopStageIdentity'],self.word(self.runtime['coopStageIdentity'])+1)
        self.prepare();self.assertEqual(self.stats()[0],2);self.assertEqual(self.reuse_count(),2)
        self.call('CoopReleaseCollisionPlan',0)

    def test_teleports_and_radius_growth_outside_envelopes_rebuild_immediately(self):
        self.prepare();head=self.native_nodes()[0];pos=self.position_address(head)
        self.write(pos,self.word(pos)+4096*4096)
        self.prepare();self.assertEqual(self.build_count(),2);self.assertEqual(self.reuse_count(),0)
        self.write(head+4,self.word(head+4)+4096*4096)
        self.prepare();self.assertEqual(self.build_count(),3);self.assertEqual(self.reuse_count(),0)
        self.call('CoopReleaseCollisionPlan',0)

    def test_reordered_or_unknown_fresh_nodes_never_reuse_stale_actor_data(self):
        self.prepare();nodes=self.native_nodes();nodes[1],nodes[2]=nodes[2],nodes[1]
        self.relink(nodes);self.prepare();self.assertEqual(self.stats()[0],2)
        self.assertEqual(self.reuse_count(),0)
        self.write(nodes[0],0);self.prepare();self.assertEqual(self.workspace(),0)
        self.assertTrue(self.intact(self.root))

    def test_reused_and_rebuilt_frames_match_native_contacts_after_new_overlap(self):
        specs=[(i*500*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)]
        nodes=self.synthetic(specs);self.install()
        def check_frame():
            initial=bytes(self.cpu.mem_read(0x02000000,0x400000))
            self.write(0x02014b0c,0xe5940000);self.cpu.ctl_remove_cache(0x02014b0c,0x02014b10)
            self.call(self.game['_ZN5dCc_c7ProcessEv'])
            expected=[bytes(self.cpu.mem_read(node,0x50)) for node in nodes]
            self.cpu.mem_write(0x02000000,initial);self.cpu.ctl_remove_cache(0x02014b0c,0x02014b10)
            self.call('CoopCollisionProcess')
            self.assertEqual([bytes(self.cpu.mem_read(node,0x50)) for node in nodes],expected)
        check_frame();self.assertEqual(self.stats()[0],1);self.assertEqual(self.reuse_count(),0)
        self.relink(nodes);self.write(self.synthetic_positions[1],508*4096)
        check_frame();self.assertEqual(self.stats()[0],1);self.assertEqual(self.reuse_count(),1)
        self.relink(nodes);self.write(self.synthetic_positions[1],20*4096)
        check_frame();self.assertEqual(self.build_count(),2);self.assertEqual(self.reuse_count(),1)
        self.assertEqual(self.word(self.runtime['coopCollisionPlanRefreshes']),1)
        self.assertEqual(self.stats()[0],1)
        self.assertEqual(self.word(nodes[0]+0x20),2)
        self.call('CoopReleaseCollisionPlan',0)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.game_heap,self.synthetic_arena)
        self.assertTrue(self.intact(self.root));self.assertTrue(self.intact(self.game_heap))

    def test_cleanup_releases_retained_plan_before_native_stage_resources(self):
        before=self.raw_free();self.prepare();self.assertTrue(self.workspace());calls=[]
        def cleanup(cpu,address,size,user):
            if address!=self.runtime['CoopOriginalStageCleanup']:return
            self.assertEqual(self.workspace(),0)
            calls.append(cpu.reg_read(UC_ARM_REG_R0))
            cpu.reg_write(UC_ARM_REG_R0,17);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,cleanup)
        self.assertEqual(self.call('CoopAnimationStageCleanup',0x023f0000),17)
        self.assertEqual(calls,[0x023f0000]);self.assertEqual(self.raw_free(),before)
        self.assertTrue(self.intact(self.root))

    def test_fast_actor_velocity_expands_only_its_box_without_assuming_future_motion(self):
        specs=[(i*500*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)]
        nodes=self.synthetic(specs)
        owner=self.word(nodes[1]+0x30);self.write(owner+0x98,60*4096)
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        envelopes=self.word(plan+32)
        bounds=struct.unpack('<4i',self.cpu.mem_read(plan+envelopes+16,16))
        self.assertEqual(bounds[1]-(500+40)*4096,60*32*4096)
        self.write(self.synthetic_positions[1],980*4096)
        self.prepare();self.assertEqual(self.workspace(),plan);self.assertEqual(self.reuse_count(),1)
        self.write(self.synthetic_positions[1],5000*4096)
        self.prepare();self.assertEqual(self.build_count(),2);self.assertEqual(self.reuse_count(),1)
        self.call('CoopReleaseCollisionPlan',0);self.assertTrue(self.intact(self.root))

    def test_extreme_signed_velocity_is_clamped_without_overflow_or_game_state_changes(self):
        nodes=self.synthetic([(i*500*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)])
        owner=self.word(nodes[1]+0x30);self.write(owner+0x98,0x80000000)
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        bounds=struct.unpack('<4i',self.cpu.mem_read(plan+self.word(plan+32)+16,16))
        self.assertEqual(bounds[1]-(500+40)*4096,2048*4096)
        self.assertEqual(self.word(owner+0x98),0x80000000)
        self.call('CoopReleaseCollisionPlan',0);self.assertTrue(self.intact(self.root))

    def callback_specs(self,first_kind=2):
        specs=[(i*1000*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)]
        specs[0]=(0,0,0,200*4096,200*4096,0x400000c,0x4000000,1,first_kind)
        specs[1]=(10*4096,0,0,200*4096,200*4096,0x4000000,0x4000000,2,2)
        return specs

    def test_callback_keeps_valid_suffix_and_finds_new_contacts_within_envelopes(self):
        specs=self.callback_specs()
        specs[2]=(410*4096,0,0,200*4096,200*4096,0x4000000,0x4000000,3,2)
        def move_within_envelope():
            if len(self.native_notifications)==1:self.write(self.synthetic_positions[2],390*4096)
        self.notification_action=move_within_envelope
        self.compare_synthetic(specs)
        self.assertGreaterEqual(self.word(self.runtime['coopCollisionValidatedCallbacks']),1)
        self.assertEqual(self.word(self.runtime['coopCollisionCallbackDepth']),0)

    def test_callback_changed_current_position_reference_drops_plan_even_at_same_coordinates(self):
        specs=self.callback_specs(first_kind=1)
        def change_reference():
            if len(self.native_notifications)!=1:return
            first=self.word(0x0209cee8)
            replacement=self.word(self.word(first+0x2c)+0x30)
            self.cpu.mem_write(replacement+0x5c,bytes(12))
            self.write(first+0x30,replacement)
        self.notification_action=change_reference
        self.compare_synthetic(specs)
        self.assertEqual(self.word(self.runtime['coopCollisionValidatedCallbacks']),0)

    def test_callback_removed_future_node_drops_plan_before_remaining_native_pairs(self):
        def remove_future_node():
            if len(self.native_notifications)!=1:return
            head=self.word(0x0209cee8);one=self.word(head+0x2c);two=self.word(one+0x2c);three=self.word(two+0x2c)
            self.write(one+0x2c,three);self.write(three+0x28,one)
            self.write(two+0x28,0);self.write(two+0x2c,0)
        self.notification_action=remove_future_node
        self.compare_synthetic(self.callback_specs())
        self.assertEqual(self.word(self.runtime['coopCollisionValidatedCallbacks']),0)

    def test_callback_root_allocation_reclaims_before_native_allocator_even_with_ample_room(self):
        self.cpu.mem_map(0x01200000,0x2000)
        code=(0xe92d4010,0xe59f4018,0xe59f0018,0xe3a01040,0xe3a02004,
              0xe59fc010,0xe12fff3c,0xe5840000,0xe8bd8010,
              0x01201000,self.root,self.runtime['CoopCollisionVAllocate'])
        self.cpu.mem_write(0x01200000,struct.pack('<12I',*code))
        self.notification_stub=0x01200000
        callback_allocations=[]
        def allocator_entry(cpu,address,size,user):
            if address==self.game['_ZN22ExpandingHeapAllocator8AllocateEji'] and self.word(self.runtime['coopCollisionCallbackDepth']):
                self.assertEqual(self.workspace(),0)
                callback_allocations.append(cpu.reg_read(UC_ARM_REG_R1))
        self.cpu.hook_add(UC_HOOK_CODE,allocator_entry)
        before=self.raw_free()
        self.compare_synthetic(self.callback_specs())
        self.assertTrue(callback_allocations);self.assertTrue(all(size==64 for size in callback_allocations))
        pointer=self.word(0x01201000);self.assertTrue(pointer)
        self.assertEqual(self.word(self.runtime['coopCollisionCallbackAllocations']),1)
        self.assertEqual(self.word(self.runtime['coopCollisionValidatedCallbacks']),0)
        self.call(self.game['_ZN5mHeap6Heap_t10DeallocateEPv'],self.root,pointer)
        self.assertEqual(self.raw_free(),before);self.assertTrue(self.intact(self.root))

    def test_incremental_refresh_updates_in_place_when_a_mover_leaves_its_envelope(self):
        nodes=self.synthetic([(i*500*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)])
        self.prepare();plan=self.workspace();self.assertTrue(plan)
        self.write(self.synthetic_positions[1],20*4096)
        self.prepare();self.assertEqual(self.workspace(),plan)
        self.assertEqual(self.word(self.runtime['coopCollisionPlanRefreshes']),1)
        self.assertEqual(self.stats()[0],1);self.assertEqual(self.native_nodes(),nodes)
        self.call('CoopReleaseCollisionPlan',0);self.assertTrue(self.intact(self.root))

    def test_incremental_sort_budget_falls_back_then_fresh_build_recovers(self):
        nodes=self.synthetic([(i*500*4096,0,0,40*4096,200*4096,2,2,i+1,2) for i in range(64)])
        before=self.raw_free();self.prepare();self.assertTrue(self.workspace())
        for i,pos in enumerate(self.synthetic_positions):self.write(pos,(63-i)*500*4096)
        self.prepare();self.assertEqual(self.workspace(),0)
        self.assertEqual(self.native_nodes(),nodes)
        self.assertEqual(self.stats()[1],1);self.assertEqual(self.stats()[7],1)
        self.assertEqual(self.raw_free(),before);self.assertTrue(self.intact(self.root))
        self.prepare();self.assertTrue(self.workspace());self.assertEqual(self.stats()[0],2)
        self.call('CoopReleaseCollisionPlan',0);self.assertEqual(self.raw_free(),before)
