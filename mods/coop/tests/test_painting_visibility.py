"""Native continuous-wave behavior with private render-rejection adapters.

Only the isolated Unicorn copy installs the production count/normal branches.
HitTest is recorded (there are no real players in this unit mapping). Shared
sliding, phase, matrix and save-flag code otherwise executes natively.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
    UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
from test_painting_normals import PaintingMeshHarness


class PaintingVisibilityTests(PaintingMeshHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        if 'CoopPaintingVisibleCells' not in self.runtime:
            self.skipTest('requires --experimental-painting-visibility build')
        self.params=0x023f1000
        self.cpu.mem_write(self.params,struct.pack('<5i',65536,3640,1228800,3686400,100))
        self.write(self.actor+0x1ac,self.params)
        self.cpu.mem_write(self.actor+0x1b4,struct.pack('<hH',6800,100))
        self.grid()
        self.write(self.runtime['coopBehaviorActor'],0)
        self.write(self.runtime['coopBehaviorVisibility'],0)
        self.hit_tests=0;self.height_calls=0;self.force_star=False;self.restart_at=None
        def dependencies(cpu,address,size,user):
            if address==0x02125bb0:self.height_calls+=1
            if address==0x021256f8:
                self.hit_tests+=1
            elif address==self.game['_ZN7fBase_c12BeforeRenderEv']:
                cpu.reg_write(UC_ARM_REG_R0,1)
            elif address==0x020136f8 and self.force_star:
                cpu.reg_write(UC_ARM_REG_R0,1)
            else:return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,dependencies)

    def branch(self,site,target,link=False):
        self.write(site,(0xeb000000 if link else 0xea000000)|(((target-site-8)>>2)&0xffffff))
        self.cpu.ctl_remove_cache(site,site+4)

    def install(self):
        self.branch(0x02125bb0,self.runtime['CoopPaintingHeight'])
        self.branch(0x02126570,self.runtime['CoopPaintingCellCountRead'])
        for site in (0x021265b4,0x02126a24):
            self.branch(site,self.runtime['CoopPaintingNormals'],True)

    def sequence(self,flags,behavior=0x021264ec):
        records=[]
        for frame,flag in enumerate(flags):
            self.write(self.actor+0xb0,flag)
            if frame==self.restart_at:
                self.cpu.reg_write(UC_ARM_REG_R3,1)
                self.call(0x02125de0,self.actor,200000,100000)
            self.call(behavior,self.actor)
            records.append((bytes(self.cpu.mem_read(self.actor,0x1bc)),
                self.word(0x0209caa8),bytes(self.cpu.mem_read(self.vertices,400*24))))
        return records

    def comparison(self,flags,behavior=0x021264ec):
        actor=bytes(self.cpu.mem_read(self.actor,0x1bc))
        mesh=bytes(self.cpu.mem_read(self.vertices,24*(400+64)))
        save=self.word(0x0209caa8);seed=self.word(0x0209e650)
        self.instructions=self.normalizations=self.hit_tests=self.height_calls=0
        baseline=self.sequence(flags,behavior)
        native=(self.instructions,self.normalizations,self.hit_tests,self.height_calls)
        self.cpu.mem_write(self.actor,actor);self.cpu.mem_write(self.vertices,mesh)
        self.write(0x0209caa8,save);self.write(0x0209e650,seed)
        self.install();self.instructions=self.normalizations=self.hit_tests=self.height_calls=0
        actual=self.sequence(flags,behavior)
        optimized=(self.instructions,self.normalizations,self.hit_tests,self.height_calls)
        for flag,expected,result in zip(flags,baseline,actual):
            self.assertEqual(result[:2],expected[:2]) # Every shared actor/save field.
            if behavior!=0x021264ec or not (flag&0x20 or (flag&8 and flag&2)):
                self.assertEqual(result[2],expected[2]) # Every visible vertex byte.
        return native,optimized,baseline,actual

    def test_hidden_to_visible_frames_refresh_the_exact_native_mesh_and_phase(self):
        native,optimized,_,_=self.comparison((0x20,0x28,0x38,0,0x20,0))
        self.assertEqual(native[2],6);self.assertEqual(optimized[2],6)
        self.assertEqual(native[3],2400);self.assertEqual(optimized[3],800)
        self.assertEqual(struct.unpack('<2I',self.cpu.mem_read(
            self.runtime['coopPaintingVisibilityStats'],8)),(4,2))

    def test_native_wave_restart_uses_planar_positions_despite_old_hidden_heights(self):
        self.restart_at=2
        self.comparison((0x38,0x38,0x38,0,0))
        self.assertEqual(self.word(self.actor+0x134),200000)
        self.assertEqual(self.word(self.actor+0x138),100000)

    def test_hidden_mesh_keeps_hit_tests_phase_and_shared_fields_without_vector_work(self):
        native,optimized,_,_=self.comparison((0x38,)*3)
        self.assertEqual(optimized[2],native[2])
        self.assertEqual(optimized[1],0);self.assertEqual(optimized[3],0)
        self.assertLess(optimized[0],native[0])
        print('Hidden painting3-frame ARM instructions:',native[0],optimized[0],
              'height calls:',native[3],optimized[3])

    def test_count_gate_matches_the_actual_native_actor_render_bit_rejection(self):
        for flags in (0,2,8,10,16,32,40,56,0x10003):
            self.write(self.actor+0xb0,flags)
            drawn=self.call(self.game['_ZN8dActor_c12BeforeRenderEv'],self.actor)
            count=self.call('CoopPaintingVisibleCells',self.actor)
            self.assertEqual(count==0,drawn==0,(flags,drawn,count))

    def test_saved_local_visibility_matches_the_flags_restored_after_behavior(self):
        self.write(self.actor+0xb0,0)
        self.write(self.runtime['coopBehaviorActor'],self.actor)
        self.write(self.runtime['coopBehaviorVisibility'],0x38)
        self.assertEqual(self.call('CoopPaintingVisibleCells',self.actor),0)
        self.write(self.runtime['coopBehaviorActor'],self.actor+0x1000)
        self.assertEqual(self.call('CoopPaintingVisibleCells',self.actor),400)

    def test_state_zero_final_wave_frames_are_never_skipped(self):
        self.write(self.actor+8,0x466)
        self.cpu.mem_write(self.actor+0x1b6,struct.pack('<H',2))
        self.comparison((0x38,0x38,0),behavior=0x021269b8)
        self.assertEqual(struct.unpack('<2I',self.cpu.mem_read(
            self.runtime['coopPaintingVisibilityStats'],8)),(0,0))

    def test_hidden_sliding_gate_keeps_native_position_matrix_and_open_flag(self):
        self.write(self.actor+8,0x2766);self.force_star=True
        self.write(self.actor+0x5c,0x802000-0x13e72)
        self.write(self.actor+0x1b0,0)
        self.write(0x0209caa8,self.word(0x0209caa8)&~0x40000)
        _,_,_,actual=self.comparison((0x38,))
        self.assertEqual(self.word(self.actor+0x5c),0x802000)
        self.assertTrue(actual[0][1]&0x40000)

    def test_unsupported_geometry_offline_and_disabled_modes_keep_native_count(self):
        self.write(self.actor+0xb0,0x38)
        self.cpu.mem_write(self.actor+0x1b8,struct.pack('<H',399))
        self.assertEqual(self.call('CoopPaintingVisibleCells',self.actor),399)
        self.grid();self.write(self.runtime['coopEnabled'],0)
        self.assertEqual(self.call('CoopPaintingVisibleCells',self.actor),400)
        self.write(self.runtime['coopEnabled'],1);self.write(0x0209fc68,0)
        self.assertEqual(self.call('CoopPaintingVisibleCells',self.actor),400)

    def test_count_read_bridge_preserves_registers_flags_stack_and_native_lr(self):
        registers=(UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,
            UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,
            UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_LR)
        for hidden in (False,True):
            self.write(self.actor+0xb0,0x38 if hidden else 0)
            self.cpu.reg_write(UC_ARM_REG_CPSR,0xa00000df)
            for i,r in enumerate(registers):self.cpu.reg_write(r,0x12340000+i)
            self.cpu.reg_write(UC_ARM_REG_R5,self.actor)
            self.cpu.reg_write(UC_ARM_REG_R6,self.actor+0x100)
            self.cpu.reg_write(UC_ARM_REG_SP,0x023fc000)
            expected={r:self.cpu.reg_read(r) for r in registers}
            self.cpu.emu_start(self.runtime['CoopPaintingCellCountRead'],0x02126574,count=10000)
            self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),0x02126574)
            self.assertEqual({r:self.cpu.reg_read(r) for r in registers},expected)
            self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R0),0 if hidden else 400)
            self.assertEqual(self.cpu.reg_read(UC_ARM_REG_SP),0x023fc000)
            self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR),0xa00000df)


if __name__=='__main__':unittest.main()
