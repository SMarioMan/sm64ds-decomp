"""Optional elapsed-time wrappers in isolated ARM; SDK clock/delegate adapters.

No live emulator memory or wireless packets are changed. These checks validate
measurement bookkeeping and ABI, not a claim about real hardware speed.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_LR, UC_ARM_REG_PC
from test_particle_heap import HeapHarness


class PlayerCostTests(HeapHarness,unittest.TestCase):
    fixture_variable='COOP_PLAYER_COST_FIXTURE'
    default_fixture='/workspace/runtime/bob-native-process-steady/steady-bob-0'

    def setUp(self):
        super().setUp()
        if 'coopPlayerCosts' not in self.runtime:
            self.skipTest('requires --diagnostic-player-cost build')
        self.write(self.runtime['coopStageIdentity'],123)
        for name in ('coopStageLoading','coopMenuLoading','coopSceneInitializing','coopTitleLoading'):
            self.write(self.runtime[name],0)
        self.cpu.mem_write(0x020a104c,b'\0\0')
        self.cpu.mem_write(0x020a6430,b'\1\0')
        self.write(0x0209f1ec,3) # Native gameplay menu state is also3.
        self.cpu.mem_write(0x0209f2c4,b'\0')
        self.write(0x020a1154,45)
        self.ticks=iter((100,150))
        self.delegates=[]
        self.change=None
        def adapter(cpu,address,size,user):
            if address==self.game['func_02059650']:
                cpu.reg_write(UC_ARM_REG_R0,next(self.ticks))
                cpu.reg_write(UC_ARM_REG_R1,0)
            elif address in (self.runtime['CoopOriginalStageRender'],self.game['_ZN17dExtSimpleModel_c6RenderEPK7Vector3'],
                self.game['_ZN10dScStage_c11RenderModelEv'],self.game['_ZN10dScStage_c22RenderModelTransparentEv'],
                self.game['_ZN17dExtShadowModel_c9RenderAllEv'],self.game['_ZN5dCc_c7ProcessEv']):
                self.delegates.append((cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)))
                if self.change:self.change()
                cpu.reg_write(UC_ARM_REG_R0,0xabcdef01)
            else:return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,adapter)

    def rows(self):
        return [struct.unpack('<6I',self.cpu.mem_read(self.runtime['coopPlayerCosts']+i*24,24)) for i in range(18)]

    def test_stage_delegate_arguments_return_and_elapsed_ticks(self):
        self.assertEqual(self.call('CoopCostStageRender',0x023f0000),0xabcdef01)
        self.assertEqual(self.delegates[0][0],0x023f0000)
        self.assertEqual(self.rows()[3],(2,1,50,0,50,50))
        self.assertEqual(self.word(self.runtime['coopPlayerCostStage']),123)

    def test_body_head_exact_arguments_and_separate_buckets(self):
        self.call('CoopCostBodyRender',0x023f0000,0x023f1000)
        self.ticks=iter((200,225))
        self.call('CoopCostHeadRender',0x023f2000,0)
        self.assertEqual(self.delegates,[(0x023f0000,0x023f1000),(0x023f2000,0)])
        self.assertEqual(self.rows()[1],(2,1,50,0,50,50))
        self.assertEqual(self.rows()[2],(2,1,25,0,25,25))

    def test_paused_buckets_wrap_and_64_bit_total_carry(self):
        self.cpu.mem_write(0x0209f2c4,b'\1')
        self.ticks=iter((0xfffffff0,0x20))
        self.call('CoopCostStageRender',1)
        self.assertEqual(self.rows()[12],(2,1,48,0,48,48))
        self.write(self.runtime['coopPlayerCosts']+12*24+8,0xfffffff0)
        self.ticks=iter((50,150))
        self.call('CoopCostStageRender',1)
        self.assertEqual(self.rows()[12],(4,2,84,1,100,48))

    def test_changed_stage_resets_and_does_not_mix_costs(self):
        self.call('CoopCostStageRender',1)
        self.write(self.runtime['coopStageIdentity'],124)
        self.ticks=iter((300,320))
        self.call('CoopCostHeadRender',2,0)
        self.assertEqual(self.rows()[3],(0,0,0,0,0,0))
        self.assertEqual(self.rows()[2],(2,1,20,0,20,20))

    def test_unready_offline_and_loading_do_not_read_clock_or_change_delegate(self):
        for address,value,width in ((self.runtime['coopEnabled'],0,4),(0x0209fc68,2,4),
            (self.runtime['coopStageIdentity'],0,4),(self.runtime['coopStageLoading'],1,4),
            (self.runtime['coopSceneInitializing'],1,4),(self.runtime['coopMenuLoading'],1,4),
            (self.runtime['coopTitleLoading'],1,4),(0x020a104c,0x4000,2),(0x020a6430,0,2)):
            with self.subTest(address=hex(address)):
                old=bytes(self.cpu.mem_read(address,width))
                self.cpu.mem_write(address,value.to_bytes(width,'little'))
                self.ticks=iter(()) # A clock access would fail this check.
                self.assertEqual(self.call('CoopCostStageRender',1),0xabcdef01)
                self.assertEqual(self.rows(),[(0,)*6]*18)
                self.cpu.mem_write(address,old)

    def test_spans_crossing_tick_stage_or_loading_are_discarded(self):
        for address,value,width in ((0x020a1154,46,4),(self.runtime['coopStageIdentity'],124,4),
                                    (0x020a104c,0x4000,2)):
            with self.subTest(address=hex(address)):
                old=bytes(self.cpu.mem_read(address,width))
                self.change=lambda:self.cpu.mem_write(address,value.to_bytes(width,'little'))
                self.ticks=iter((100,150))
                self.call('CoopCostStageRender',1)
                self.assertEqual(self.rows(),[(0,)*6]*18)
                self.cpu.mem_write(address,old)

    def test_successful_player_behavior_scope_counts_once_and_restores_context(self):
        actor=self.word(0x0209f394)
        self.assertTrue(actor)
        def before(cpu,address,size,user):
            if address!=self.runtime['CoopOriginalActorBefore']:return
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,before)
        flags=self.word(actor+0xb0)
        self.assertEqual(self.call('CoopActorBefore',actor),1)
        self.call('CoopActorAfter',actor,1)
        self.assertEqual(self.rows()[0],(2,1,50,0,50,50))
        self.assertEqual(self.word(actor+0xb0),flags)
        self.ticks=iter(())
        self.call('CoopActorAfter',actor,1)
        self.assertEqual(self.rows()[0],(2,1,50,0,50,50))

    def test_stage_subspans_delegate_and_keep_independent_elapsed_buckets(self):
        for kind,symbol in enumerate(('CoopCostOpaqueRender','CoopCostShadowRender',
                                      'CoopCostTransparentRender','CoopCostCollisionProcess'),4):
            self.ticks=iter((100,100+kind))
            self.call(symbol,0x023f0000)
            self.assertEqual(self.rows()[kind],(2,1,kind,0,kind,kind))
        self.assertEqual(self.delegates[0][0],0x023f0000)
        self.assertEqual(self.delegates[2][0],0x023f0000)

    def actor_scope(self, actor_id, ticks=(100,150), paused=False, result=1):
        actor=0x023f2000
        self.cpu.mem_write(actor,b'\0'*0x200)
        self.cpu.mem_write(actor+12,struct.pack('<H',actor_id))
        self.cpu.mem_write(0x0209f2c4,bytes((int(paused),)))
        self.ticks=iter(ticks)
        def before(cpu,address,size,user):
            if address!=self.runtime['CoopOriginalActorBefore']:return
            cpu.reg_write(UC_ARM_REG_R0,result)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        hook=self.cpu.hook_add(UC_HOOK_CODE,before)
        self.assertEqual(self.call('CoopActorBefore',actor),result)
        if result:self.call('CoopActorAfter',actor,1)
        self.cpu.hook_del(hook)

    def profiles(self):
        return [struct.unpack('<7I',self.cpu.mem_read(self.runtime['coopActorProfileCosts']+i*28,28))
                for i in range(64)]

    def test_nonplayer_classes_collisions_pause_and_exact_elapsed_totals(self):
        self.actor_scope(7)
        self.actor_scope(71,(200,220)) # Same initial hash slot; preserve both.
        self.actor_scope(7,(300,330))
        self.actor_scope(7,(400,410),paused=True)
        records={r[0]:r[1:] for r in self.profiles() if r[0]}
        self.assertEqual(records,{8:(4,2,80,0,50,30),72:(2,1,20,0,20,20),
                                  65544:(2,1,10,0,10,10)})
        self.assertEqual(self.rows()[8],(6,3,100,0,50,20))
        self.assertEqual(self.rows()[17],(2,1,10,0,10,10))

    def test_full_class_table_preserves_records_and_resets_on_stage(self):
        for actor_id in range(64):self.actor_scope(actor_id)
        before=self.profiles()
        self.actor_scope(1000)
        self.assertEqual(self.profiles(),before)
        self.assertEqual(self.word(self.runtime['coopActorProfileCostOverflows']),1)
        self.assertEqual(self.rows()[8][1],65) # Aggregate never loses the span.
        self.write(self.runtime['coopStageIdentity'],124)
        self.actor_scope(65535) # Encoding must not alias a paused actor0.
        self.assertEqual([r for r in self.profiles() if r[0]],[(65536,2,1,50,0,50,50)])
        self.assertEqual(self.word(self.runtime['coopActorProfileCostOverflows']),0)

    def test_rejected_nonplayer_behavior_does_not_read_clock_or_record(self):
        self.actor_scope(7,ticks=(),result=0)
        self.assertEqual(self.profiles(),[(0,)*7]*64)
        self.assertEqual(self.rows(),[(0,)*6]*18)
