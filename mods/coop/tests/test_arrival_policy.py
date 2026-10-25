"""Guest result-pose ownership must not erase native movement entrances."""
import unittest
import struct
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R2,UC_ARM_REG_PC,UC_ARM_REG_LR
from test_particle_heap import HeapHarness


class ArrivalPolicyTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.player=0x023f0000
        self.cpu.mem_write(self.player+0x6d8,b'\x02')
        self.cpu.mem_write(0x0209f2fc,b'\x01')
        self.arrivals=[]
        self.heals=0
        def native(cpu,address,size,user):
            if address==self.runtime['CoopOriginalLevelEnterInit']:
                self.arrivals.append(self.cpu.mem_read(self.player+0x6e3,1)[0])
            elif address==self.game['GiveHealth']:self.heals+=1
            else:return
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,native)

    def enter(self,kind):
        self.cpu.mem_write(self.player+0x6e3,bytes([kind]))
        self.call('CoopLevelEnterInit',self.player)
        return self.arrivals[-1]

    def test_water_and_wing_cap_arrivals_reach_the_native_initializer(self):
        for kind in (1,2):
            with self.subTest(kind=kind):self.assertEqual(self.enter(kind),kind)
        self.assertEqual(self.heals,0)

    def test_other_movement_entrances_are_preserved(self):
        for kind in (0,3,5,6,7,9,10,12,13,14,17):
            with self.subTest(kind=kind):self.assertEqual(self.enter(kind),kind)
        self.assertEqual(self.heals,0)

    def test_shared_star_and_key_return_poses_use_one_leader(self):
        for kind in (4,8,11,15,16,18):
            with self.subTest(kind=kind):self.assertEqual(self.enter(kind),0)
        self.assertEqual(self.heals,6)

    def test_host_keeps_all_native_arrival_types(self):
        self.cpu.mem_write(self.player+0x6d8,b'\0')
        for kind in range(19):self.assertEqual(self.enter(kind),kind)
        self.assertEqual(self.heals,0)

    def test_non_result_transition_keeps_guest_arrivals(self):
        for reason in (0,2):
            self.cpu.mem_write(0x0209f2fc,bytes([reason]))
            for kind in range(19):self.assertEqual(self.enter(kind),kind)
        self.assertEqual(self.heals,0)

    def test_offline_arrivals_are_unchanged(self):
        self.write(self.runtime['coopEnabled'],0)
        for kind in range(19):self.assertEqual(self.enter(kind),kind)
        self.assertEqual(self.heals,0)


class FlightPartyTests(HeapHarness,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.table=0x023f0000
        self.entries=0x023f0100
        self.cpu.mem_write(self.table,struct.pack('<BBHI',0,1,0,self.entries))
        self.cpu.mem_write(0x02092128,bytes([3,1,2,0]))
        self.cpu.mem_write(0x02092114,b'\x02')
        self.selections=[]
        self.spawn_rows=[]
        def spawn(cpu,address,size,user):
            if address!=self.runtime['CoopOriginalLoadEntrances']:return
            table=cpu.reg_read(UC_ARM_REG_R0)
            count=self.cpu.mem_read(table+1,1)[0]
            entries=self.word(table+4)
            index=cpu.reg_read(UC_ARM_REG_R2)
            self.selections.append((bytes(self.cpu.mem_read(0x02092128,4)),
                                    bytes(self.cpu.mem_read(0x02092114,1))))
            self.spawn_rows.append(bytes(self.cpu.mem_read(entries+index*16,count*16)))
            cpu.reg_write(UC_ARM_REG_R0,1)
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,spawn)

    def enter(self,kind):
        row=struct.pack('<H6hH',0,-4000,2866,0,0,16384,0,kind<<7)
        self.cpu.mem_write(self.entries,row)
        self.call('CoopLoadEntrances',self.table,0,0)
        self.assertEqual(bytes(self.cpu.mem_read(0x02092128,4)),bytes([3,1,2,0]))
        self.assertEqual(bytes(self.cpu.mem_read(0x02092114,1)),b'\x02')
        return row

    def test_flight_uses_mario_caps_for_all_four_native_actor_constructions(self):
        row=self.enter(2)
        self.assertEqual(self.selections,[(bytes(4),b'\xff')])
        self.assertEqual(self.spawn_rows,[row*4])
        self.assertEqual(self.word(0x0209f328),self.entries)
        self.assertEqual(self.word(0x0209f214),1)

    def test_other_entrances_keep_native_character_choices(self):
        for kind in (0,1,3,4,8,11,13,15,17):
            self.enter(kind)
            self.assertEqual(self.selections[-1],(bytes([3,1,2,0]),b'\x02'))

    def test_offline_flight_keeps_native_character_choices(self):
        self.write(0x0209fc68,0)
        self.enter(2)
        self.assertEqual(self.selections,[(bytes([3,1,2,0]),b'\x02')])

    def test_unmodified_mode_keeps_the_original_entrance_table(self):
        self.write(self.runtime['coopEnabled'],0)
        row=self.enter(2)
        self.assertEqual(self.selections,[(bytes([3,1,2,0]),b'\x02')])
        self.assertEqual(self.spawn_rows,[row])


if __name__=='__main__':unittest.main()
