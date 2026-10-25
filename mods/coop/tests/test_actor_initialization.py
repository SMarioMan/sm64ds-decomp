"""Native Snufit initial state must not depend on local rendering or IO timing."""
import struct
import unittest
import ndspy.rom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness


class ActorInitializationTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        overlay=ndspy.rom.NintendoDSRom.fromFile('/workspace/inputs/sm64ds-eu.nds').loadArm9Overlays()[65]
        self.cpu.mem_write(overlay.ramAddress,bytes(overlay.data))
        self.actor=0x023f0000
        self.cpu.mem_write(self.actor,bytes(0x400))
        self.write(self.actor+4,1100)
        self.write(self.actor+0xb0,0x08000000) # Native spawn-even-if-killed profile flag.
        self.write(self.runtime['coopStageIdentity'],1000)
        self.cpu.mem_write(0x0209f2f8,b'\x21')
        def presentation(cpu,address,size,user):
            if address!=self.game['_ZN14dExtAnmModel_c7SetAnimEP8BCA_Fileiit']:return
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,presentation)

    def native_initial_state(self):
        self.call(0x021168a8,self.actor) # Original Snufit wait-state initializer.
        return bytes(self.cpu.mem_read(self.actor+0x3e0,2))+bytes(self.cpu.mem_read(self.actor+0x100,2))

    def test_unseeded_native_initial_ai_depends_on_unrelated_random_draws(self):
        states=set()
        for seed in (1,12345,0x12345678,0xdeadbeef):
            self.write(0x0209e650,seed)
            states.add(self.native_initial_state())
        self.assertGreater(len(states),1)

    def test_native_initial_heading_and_timer_match_despite_render_rng_and_packet_skew(self):
        states=[]
        for seed,tick in ((1,100),(12345,103),(0x12345678,109),(0xdeadbeef,120)):
            self.write(0x0209e650,seed)
            self.write(0x020a1154,tick)
            self.assertEqual(self.call('CoopActorBeforeInit',self.actor),1)
            states.append(self.native_initial_state())
        self.assertEqual(len(set(states)),1)
        self.assertEqual(self.word(self.runtime['coopActorInitializationsSeeded']),4)

    def test_stage_relative_creation_identity_survives_pre_session_actor_count_differences(self):
        states=[]
        for stage in (1000,1001,2000):
            self.write(self.runtime['coopStageIdentity'],stage)
            self.write(self.actor+4,stage+100)
            self.call('CoopActorBeforeInit',self.actor)
            states.append(self.native_initial_state())
        self.assertEqual(len(set(states)),1)

    def test_different_actors_get_independent_initial_streams(self):
        states=set()
        for identity in range(1100,1108):
            self.write(self.actor+4,identity)
            self.call('CoopActorBeforeInit',self.actor)
            states.add(self.native_initial_state())
        self.assertGreater(len(states),1)

    def test_offline_initialization_preserves_the_native_random_stream(self):
        self.write(0x0209fc68,0)
        self.write(0x0209e650,0x12345678)
        self.call('CoopActorBeforeInit',self.actor)
        self.assertEqual(self.word(0x0209e650),0x12345678)
        self.assertEqual(self.word(self.runtime['coopActorInitializationsSeeded']),0)


if __name__=='__main__':unittest.main()
