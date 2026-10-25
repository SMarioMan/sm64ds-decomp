"""Native camera guards under a guest's shared host-actor context."""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R3,UC_ARM_REG_PC,UC_ARM_REG_LR
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
            if address==self.game['func_02012790']:pass
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


if __name__=='__main__':unittest.main()
