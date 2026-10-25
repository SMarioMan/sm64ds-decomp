"""Native camera guards under a guest's shared host-actor context."""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R9,UC_ARM_REG_R12,UC_ARM_REG_CPSR,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness


class CameraControlTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.camera=0x023f0000
        self.write(self.camera+0x140,0x023f1000)
        self.write(self.camera+0x110,0x023f2000)
        self.write(self.camera+0x154,0)
        self.write(0x0209f318,self.camera)
        self.cpu.mem_write(0x020a0f10,b'\x02')
        self.cpu.mem_write(0x0209f250,b'\0')
        self.cpu.mem_write(0x02092110,b'\xff')
        self.transitions=[]
        def presentation(cpu,address,size,user):
            if address in (self.game['func_02012790'],self.game['func_0200cb58']):pass
            elif address==self.game['func_0200c66c']:
                self.write(cpu.reg_read(UC_ARM_REG_R3),0x0208715c)
            elif address==self.game['_ZN9dCamera_c11ChangeStateEPNS_5StateE']:
                self.transitions.append(cpu.reg_read(UC_ARM_REG_R1))
            else:return
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,presentation)

    def flags(self):return self.word(self.camera+0x154)

    def test_host_zoom_does_not_change_a_guest_camera(self):
        self.call('CoopCameraFar',self.camera,0)
        self.assertEqual(self.flags(),0)

    def test_guest_zoom_uses_its_local_slot_and_restores_shared_context(self):
        self.call('CoopCameraFar',self.camera,2)
        self.assertEqual(self.flags()&2,2)
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')
        self.call('CoopCameraNear',self.camera,2)
        self.assertEqual(self.flags()&2,0)
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')

    def test_other_guest_zoom_is_ignored(self):
        self.call('CoopCameraFar',self.camera,1)
        self.assertEqual(self.flags(),0)

    def test_host_near_zoom_does_not_reset_guest_choice(self):
        self.write(self.camera+0x154,2)
        self.call('CoopCameraNear',self.camera,0)
        self.assertEqual(self.flags()&2,2)

    def test_recenter_only_accepts_the_local_controller(self):
        self.call('CoopCameraBehind',self.camera,0)
        self.assertEqual(self.transitions,[])
        self.call('CoopCameraBehind',self.camera,2)
        self.assertEqual(len(self.transitions),1)
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')

    def test_fov_only_accepts_the_local_controller(self):
        self.call('CoopCameraFov',self.camera,0,0)
        self.assertEqual(self.flags(),0)
        self.call('CoopCameraFov',self.camera,2,0)
        self.assertEqual(self.flags(),0x20000)

    def test_offline_fov_matches_the_native_selected_player(self):
        self.write(self.runtime['coopEnabled'],0)
        self.cpu.mem_write(0x0209f250,b'\x01')
        for player in range(4):
            for mode in (0,1):
                self.write(self.camera+0x154,0)
                self.call(self.game['func_0200ca14'],self.camera,player,mode)
                expected=self.flags()
                self.write(self.camera+0x154,0)
                self.call('CoopCameraFov',self.camera,player,mode)
                self.assertEqual(self.flags(),expected)

    def test_first_person_mode_is_local(self):
        self.call('CoopCameraFirstPerson',self.camera,0)
        self.assertEqual(self.transitions,[])
        self.call('CoopCameraFirstPerson',self.camera,2)
        self.assertEqual(len(self.transitions),1)
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')

    def test_normal_camera_return_is_local(self):
        self.call('CoopCameraNormal',self.camera,0)
        self.assertEqual(self.transitions,[])
        self.call('CoopCameraNormal',self.camera,2)
        self.assertEqual(len(self.transitions),1)

    def test_head_look_uses_echoed_pitch_and_restores_the_local_camera(self):
        player=0x023f3000
        self.cpu.mem_write(player+0x6d8,b'\x03')
        self.cpu.mem_write(0x020a1166+3*36+7,struct.pack('<h',0x2345))
        self.cpu.mem_write(self.camera+0x17e,struct.pack('<h',0x2345))
        self.cpu.mem_write(0x0209f250,b'\x03')
        self.call(self.runtime['CoopOriginalPlayerHeadLook'],player)
        expected=bytes(self.cpu.mem_read(player+0x764,4))
        self.cpu.mem_write(0x0209f250,b'\0')
        for local_pitch in (-0x2000,0,0x3000):
            self.cpu.mem_write(self.camera+0x17e,struct.pack('<h',local_pitch))
            self.call('CoopPlayerHeadLook',player)
            self.assertEqual(bytes(self.cpu.mem_read(player+0x764,4)),expected)
            self.assertEqual(bytes(self.cpu.mem_read(self.camera+0x17e,2)),struct.pack('<h',local_pitch))
            self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')

    def test_pitch_publication_preserves_initial_save_transfer_bytes(self):
        scene=0x023f3000
        self.write(scene+12,3)
        self.cpu.mem_write(self.camera+0x17e,struct.pack('<h',-0x1234))
        self.cpu.mem_write(0x020a1052+7,b'AB')
        self.write(self.runtime['coopSaveState'],0)
        self.call('CoopSceneBefore',scene)
        self.assertEqual(bytes(self.cpu.mem_read(0x020a1052+7,2)),b'AB')
        self.write(self.runtime['coopSaveState'],1)
        self.call('CoopSceneBefore',scene)
        self.assertEqual(bytes(self.cpu.mem_read(0x020a1052+7,2)),struct.pack('<h',-0x1234))


    def test_all_native_movement_modes_select_only_the_local_camera(self):
        for suffix in ('D10c','D148','D438','D474','D508','D544','D580','D5c0','D5fc','D63c','D678','D6b4','D6f0','D72c','D768','D7a4'):
            with self.subTest(mode=suffix):
                self.transitions.clear()
                self.call('CoopCameraMode'+suffix,self.camera,0)
                self.call('CoopCameraMode'+suffix,self.camera,1)
                self.call('CoopCameraMode'+suffix,self.camera,3)
                self.assertEqual(self.transitions,[])
                self.call('CoopCameraMode'+suffix,self.camera,2)
                self.assertEqual(len(self.transitions),1)
                self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')

    def test_offline_movement_modes_preserve_native_player_guards(self):
        self.write(self.runtime['coopEnabled'],0)
        self.cpu.mem_write(0x0209f250,b'\x01')
        for suffix in ('D10c','D148','D438','D474','D508','D544','D580','D5c0','D5fc','D63c','D678','D6b4','D6f0','D72c','D768','D7a4'):
            for slot in range(4):
                with self.subTest(mode=suffix,slot=slot):
                    self.transitions.clear()
                    self.call(self.game['func_0200'+suffix.lower()],self.camera,slot)
                    expected=list(self.transitions)
                    self.transitions.clear()
                    self.call('CoopCameraMode'+suffix,self.camera,slot)
                    self.assertEqual(self.transitions,expected)
                    self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\x01')

    def test_zoom_rejection_is_identical_for_local_and_foreign_replicas(self):
        self.cpu.mem_write(0x020a1166+2*36+5,b'\x04')
        for local in range(4):
            with self.subTest(local=local):
                self.cpu.mem_write(0x020a0f10,bytes([local]))
                self.assertEqual(self.call('CoopCameraFar',self.camera,2),0)
                self.assertEqual(self.flags()&2,0)

    def test_local_zoom_uses_echoed_eligibility_even_at_an_area_boundary(self):
        self.cpu.mem_write(0x023f1000+0x26,b'\x01\0')
        self.cpu.mem_write(0x020a1166+2*36+5,b'\0')
        self.assertEqual(self.call('CoopCameraFar',self.camera,2),1)
        self.assertEqual(self.flags()&2,2)

    def test_offline_zoom_keeps_the_native_area_restriction(self):
        self.write(self.runtime['coopEnabled'],0)
        self.cpu.mem_write(0x0209f250,b'\x02')
        self.cpu.mem_write(0x023f1000+0x26,b'\x01\0')
        self.assertEqual(self.call('CoopCameraFar',self.camera,2),0)
        self.assertEqual(self.flags()&2,0)

    def test_each_camera_input_uses_its_owners_echoed_availability(self):
        self.write(self.camera+0x154,0x80000000)
        for slot in range(4):
            self.cpu.mem_write(0x020a1166+slot*36+5,bytes([2 if slot%2==0 else 0]))
            expected=0x80001000 if slot%2==0 else 0x80000000
            self.assertEqual(self.call('CoopInputCameraFlags',self.camera,slot),expected)
        self.write(self.runtime['coopEnabled'],0)
        self.assertEqual(self.call('CoopInputCameraFlags',self.camera,0),0x80000000)

    def test_owl_completion_uses_the_active_players_echoed_camera(self):
        self.cpu.mem_write(self.game['gActivePlayerSlot'],b'\x03')
        self.cpu.mem_write(0x020a1166+3*36+5,b'\x01')
        self.cpu.mem_write(0x020a1166+5,b'\0')
        self.assertEqual(self.call('CoopPersonalCameraFlags',self.camera)&0x8000,0x8000)
        self.cpu.mem_write(0x020a1166+3*36+5,b'\0')
        self.write(self.camera+0x154,0x8000)
        self.assertEqual(self.call('CoopPersonalCameraFlags',self.camera)&0x8000,0)

    def test_camera_info_publishes_completion_controls_and_zoom_limits(self):
        scene=0x023f3000
        self.write(scene+12,3)
        self.write(self.camera+0x154,0x9000)
        self.cpu.mem_write(0x023f1000+0x26,b'\x01\0')
        self.write(self.runtime['coopSaveState'],1)
        self.call('CoopSceneBefore',scene)
        self.assertEqual(bytes(self.cpu.mem_read(0x020a1052+5,1)),b'\x07')

    def test_native_camera_input_parses_two_players_with_different_camera_states(self):
        # Install the compiled call in this isolated native-code fixture only.
        address=0x02024d40
        target=self.runtime['CoopCameraInputFlagsRead']
        self.write(address,0xeb000000|(((target-address-8)>>2)&0xffffff))
        for flag in (0x0209f294,0x0209f2c4,0x0209f20c,0x0209d660):
            self.cpu.mem_write(flag,b'\0')
        self.cpu.mem_write(0x0209f21c,b'\x04')
        self.cpu.mem_write(0x0209f498,bytes(24*4))
        self.cpu.mem_write(0x0209f350,bytes(4))
        self.cpu.mem_write(self.game['gTouchHeld'],bytes([1,1,235,160])*2+bytes(8))
        self.cpu.mem_write(0x020a1166+5,b'\x02')
        self.cpu.mem_write(0x020a1166+36+5,b'\0')
        self.call(self.game['_ZN10dScStage_c16CheckCameraInputEv'],0)
        held0=int.from_bytes(self.cpu.mem_read(0x0209f498+4,2),'little')
        held1=int.from_bytes(self.cpu.mem_read(0x0209f498+24+4,2),'little')
        self.assertEqual(held0,0x100)
        self.assertEqual(held1,0)

    def test_camera_input_load_preserves_native_registers_and_condition_flags(self):
        self.write(self.camera+0x154,0x80000000)
        self.cpu.mem_write(0x020a1166+5,b'\x02')
        self.cpu.reg_write(UC_ARM_REG_R9,self.camera)
        self.cpu.reg_write(UC_ARM_REG_R3,0x33333333)
        self.cpu.reg_write(UC_ARM_REG_R12,0xcccccccc)
        def flags(cpu,address,size,user):
            if address==self.runtime['CoopCameraInputFlagsRead']:
                cpu.reg_write(UC_ARM_REG_CPSR,0xf00000df)
        self.cpu.hook_add(UC_HOOK_CODE,flags)
        result=self.call('CoopCameraInputFlagsRead',0xcafe,0,0x22222222)
        self.assertEqual(result,0xcafe)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R1),0)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R2),0x22222222)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R3),0x33333333)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R12),0xcccccccc)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_R9),0x80001000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_CPSR)&0xf0000000,0xf0000000)

    def test_look_target_changes_only_for_the_local_player(self):
        self.write(self.camera+0x11c,0x11111111)
        self.call('CoopCameraLookTarget',self.camera,0,0x22222222)
        self.assertEqual(self.word(self.camera+0x11c),0x11111111)
        self.assertEqual(self.transitions,[])
        self.call('CoopCameraLookTarget',self.camera,2,0x33333333)
        self.assertEqual(self.word(self.camera+0x11c),0x33333333)
        self.assertEqual(len(self.transitions),1)
        self.assertEqual(bytes(self.cpu.mem_read(0x0209f250,1)),b'\0')


if __name__=='__main__':unittest.main()
