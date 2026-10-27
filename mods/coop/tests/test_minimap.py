"""Run native story minimap drawing with isolated OAM submission adapters.

The original projection/draw code runs from overlay2; only presentation calls
are recorded. No running emulator or wireless state is modified.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_LR,UC_ARM_REG_PC)
from test_particle_heap import HeapHarness


class MinimapTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        overlay=self.stock.loadArm9Overlays()[2]
        self.cpu.mem_write(overlay.ramAddress,bytes(overlay.data))
        self.map=0x023f0000
        self.cpu.mem_write(self.map,bytes(0x258))
        self.cpu.mem_write(self.map+0x21e,bytes([7]*4+[255]*12))
        self.cpu.mem_write(self.map+0x23a,bytes([255]*9))
        self.cpu.mem_write(self.map+0x248,bytes([255]*9))
        self.cpu.mem_write(0x02111148,b'\x07')
        self.cpu.mem_write(0x0209f250,b'\0')
        self.cpu.mem_write(0x020a0e40,b'\x01')
        self.cpu.mem_write(0x020a0f10,b'\x02')
        self.cpu.mem_write(0x0209f2d8,b'\0')
        for address in (0x0209f294,0x0209f2c4,0x0209f20c):
            self.cpu.mem_write(address,b'\0')
        self.cpu.mem_write(0x0209caa0,bytes(40))
        for slot in range(4):
            player=0x023f1000+slot*0x1000
            self.cpu.mem_write(player,bytes(0x1000))
            self.write(0x0209f394+slot*4,player)
            self.write(player+8,3)
            self.cpu.mem_write(player+0x6d9,b'\x03')
            self.write(self.map+0x70+slot*4,40+slot*40)
            self.write(self.map+0x80+slot*4,80)
        self.draws=[]
        self.original_context=[]
        self.behavior_stub=False
        def calls(cpu,address,size,user):
            if address==self.runtime['CoopOriginalMinimapBehavior'] and self.behavior_stub:
                self.original_context.append((bytes(cpu.mem_read(0x0209f250,1))[0],
                    bytes(cpu.mem_read(0x020a0e40,1))[0]))
                cpu.reg_write(UC_ARM_REG_R0,17)
            elif address==self.game['_ZN3OAM9RenderSubEP7OamAttriiii']:
                self.draws.append(tuple(cpu.reg_read(r) for r in
                    (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)))
            elif address in (self.game['_ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi'],
                             self.game['_ZN3OAM6RenderEbP7OamAttriiiiiiii']):pass
            else:return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,calls)
    def expected(self,local,visible=(0,1,2,3)):
        native_head=(self.word(0x0210c174+15*4),40+local*40,80)
        return [native_head]+[(self.word(0x020aba70+4*(s+1)),
            40+s*40+(10 if s==local else -4),72) for s in visible]

    def test_native_story_head_and_numbered_markers_on_each_local_view(self):
        for local in range(4):
            self.cpu.mem_write(0x020a0f10,bytes([local]));self.draws=[]
            self.assertEqual(self.call('CoopMinimapRender',self.map),1)
            self.assertEqual(self.draws,self.expected(local))
            self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')
            self.assertEqual(bytes(self.cpu.mem_read(0x0209f2d8,1)),b'\0')

    def test_native_map_id_and_screen_clipping_remain_active(self):
        self.cpu.mem_write(self.map+0x21e,b'\x06')
        self.write(self.map+0x70+4,400)
        self.call('CoopMinimapRender',self.map)
        self.assertEqual(self.draws,self.expected(2,visible=(2,3)))

    def test_absent_slots_on_other_maps_are_safe_for_two_and_three_players(self):
        for count in (2,3):
            self.cpu.mem_write(0x020a0f10,b'\0')
            for s in range(4):
                self.write(0x0209f394+4*s,0x023f1000+s*0x1000 if s<count else 0)
                self.cpu.mem_write(self.map+0x21e+s,bytes([7 if s<count else 255]))
            self.draws=[];self.call('CoopMinimapRender',self.map)
            self.assertEqual(self.draws,self.expected(0,visible=tuple(range(count))))

    def test_stale_map_id_for_absent_player_does_not_draw_a_marker(self):
        self.write(0x0209f394+12,0)
        self.call('CoopMinimapRender',self.map)
        self.assertEqual(self.draws,self.expected(2,visible=(0,1,2)))

    def test_offline_has_only_the_native_head(self):
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopMinimapRender',self.map)
        self.assertEqual(self.draws,self.expected(0)[:1])

    def test_native_pause_policy_hides_all_markers(self):
        self.cpu.mem_write(0x0209f2c4,b'\x01')
        self.write(0x0209caa8,0x80)
        self.call('CoopMinimapRender',self.map)
        self.assertEqual(self.draws,[])

    def test_unknown_map_does_not_draw_remote_markers(self):
        self.cpu.mem_write(0x02111148,b'\xff')
        self.call('CoopMinimapRender',self.map)
        self.assertEqual(self.draws,self.expected(2)[:1])

    def test_behavior_uses_local_map_and_touch_then_restores_context(self):
        self.behavior_stub=True
        self.assertEqual(self.call('CoopMinimapBehavior',self.map),17)
        self.assertEqual(self.original_context,[(2,2)])
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')
        self.assertEqual(bytes(self.cpu.mem_read(0x020a0e40,1)),b'\x01')
        self.write(self.runtime['coopEnabled'],0)
        self.call('CoopMinimapBehavior',self.map)
        self.assertEqual(self.original_context[-1],(0,1))


if __name__=='__main__':unittest.main()
