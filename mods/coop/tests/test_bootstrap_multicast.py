"""Native ARM bootstrap grouping and completion; SDK submission is isolated.

No running emulator or radio packet is altered. Only the compiled parent module
executes here; private peer records model SDK success, errors and reconnects.
"""
import io
import ndspy.rom
import struct
import unittest
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,
    UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)

ROOT=Path(__file__).resolve().parents[3]


class BootstrapMulticastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=ROOT/'build/coop/bootstrap'
        if not (root/'host.elf').exists() or not (root/'host.bin').exists():
            raise unittest.SkipTest('requires an integrated bootstrap build')
        elf=ELFFile(io.BytesIO((root/'host.elf').read_bytes()))
        cls.symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols() if s.name}
        if 'CoopBootstrapPayloadTargets' not in cls.symbols:
            raise unittest.SkipTest('requires --experimental-bootstrap-multicast integrated build')
        cls.body=(root/'host.bin').read_bytes()
        package=ndspy.rom.NintendoDSRom.fromFile(root/'haxxstation-game-client.nds')
        cls.payload_size=len(package.files[package.filenames.idOf('ds_demo/rom0000d')])

    def setUp(self):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_ARM);self.cpu.mem_map(0x02000000,0x400000)
        self.cpu.mem_write(0x02200000,self.body)
        self.wm=0x020b0000;self.buffer=0x023d0000;self.payload=0x023a0000;self.event=0x023f0000
        self.write('data_020a9db4',self.wm);self.write('transmitBuffer',self.buffer)
        self.write('payloadData',self.payload);self.write('stationChildren',14)
        self.cpu.mem_write(self.wm+0x1411,b'\x01')
        self.cpu.mem_write(self.wm+0x1e28,struct.pack('<HH',1,14))
        self.cpu.mem_write(self.payload,bytes(range(252)))
        for aid in range(1,4):self.peer(aid)
        self.allow_pump=False;self.pumps=0;self.submissions=[];self.submit_result=2
        def sdk(cpu,address,size,user):
            if address==self.symbols['Pump'] and not self.allow_pump:
                self.pumps+=1
            elif address==self.symbols['_ZN3IRQ7DisableEv']:
                cpu.reg_write(UC_ARM_REG_R0,0x5f)
            elif address==self.symbols['_ZN3IRQ7RestoreEj']:
                pass
            elif address==self.symbols['func_02062428']:
                sp=cpu.reg_read(UC_ARM_REG_SP);data=cpu.reg_read(UC_ARM_REG_R2);length=cpu.reg_read(UC_ARM_REG_R3)
                bitmap,port,priority=struct.unpack('<3I',cpu.mem_read(sp,12))
                self.submissions.append({'destinations':bitmap,'port':port,'priority':priority,
                    'data':bytes(cpu.mem_read(data,length))})
                cpu.reg_write(UC_ARM_REG_R0,self.submit_result)
            else:return
            cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
        self.cpu.hook_add(UC_HOOK_CODE,sdk)

    def address(self,value):return self.symbols[value] if isinstance(value,str) else value
    def write(self,address,value):self.cpu.mem_write(self.address(address),struct.pack('<I',value&0xffffffff))
    def word(self,address):return int.from_bytes(self.cpu.mem_read(self.address(address),4),'little')
    def peer(self,aid,phase=8,offset=0,chunk=0,repeats=0,cooldown=0,generation=7):
        self.cpu.mem_write(self.symbols['peers']+aid*24,struct.pack('<6I',phase,offset,chunk,repeats,cooldown,generation))
    def peers(self):return bytes(self.cpu.mem_read(self.symbols['peers'],96))
    def row(self,aid):return struct.unpack('<6I',self.cpu.mem_read(self.symbols['peers']+aid*24,24))
    def stats(self):return struct.unpack('<4I',self.cpu.mem_read(self.symbols['coopBootstrapMulticastStats'],16))
    def call(self,name,*args):
        self.cpu.reg_write(UC_ARM_REG_CPSR,0xdf)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):self.cpu.reg_write(reg,value)
        self.cpu.reg_write(UC_ARM_REG_SP,0x023fe000);self.cpu.reg_write(UC_ARM_REG_LR,0x023ff000)
        self.cpu.emu_start(self.symbols[name],0x023ff000,count=100000)
        self.assertEqual(self.cpu.reg_read(UC_ARM_REG_PC),0x023ff000)
        return self.cpu.reg_read(UC_ARM_REG_R0)
    def pump(self):
        self.allow_pump=True
        try:self.call('Pump')
        finally:self.allow_pump=False
    def complete(self,error=0):
        self.cpu.mem_write(self.event+2,struct.pack('<H',error));self.call('CoopStationSent',self.event)

    def test_matching_payload_blocks_group_only_associated_ready_members(self):
        for count in (1,2,3):
            mask=(1<<(count+1))-2;self.cpu.mem_write(self.wm+0x1e2a,struct.pack('<H',mask))
            before=self.peers()
            for aid in range(1,count+1):self.assertEqual(self.call('CoopBootstrapPayloadTargets',aid),mask)
            self.assertEqual(self.peers(),before)
        for kwargs in ({'phase':7},{'offset':126},{'chunk':1},{'cooldown':1}):
            self.peer(3,**kwargs);self.assertEqual(self.call('CoopBootstrapPayloadTargets',1),6)
        self.assertEqual(self.call('CoopBootstrapPayloadTargets',0),0)
        self.assertEqual(self.call('CoopBootstrapPayloadTargets',4),0)
        self.write('data_020a9db4',0);self.assertEqual(self.call('CoopBootstrapPayloadTargets',1),0)

    def test_menu_start_and_execute_messages_remain_single_recipient(self):
        for phase,offset in ((1,0),(3,0),(5,0),(7,0),(8,self.payload_size)):
            for aid in range(1,4):self.peer(aid,phase=phase,offset=offset)
            self.assertEqual(self.call('CoopBootstrapPayloadTargets',1),2)

    def test_native_pump_submits_one_reliable_group_and_success_advances_each_peer(self):
        self.pump();self.assertEqual(len(self.submissions),1)
        packet=self.submissions[0];self.assertEqual(packet['destinations'],14);self.assertEqual(packet['port'],15)
        self.assertEqual(packet['data'],b'\0\0'+bytes(range(126)))
        self.assertEqual(self.word('transmitBusy'),1)
        self.complete()
        for aid in range(1,4):self.assertEqual(self.row(aid),(8,126,1,0,0,7))
        self.assertEqual(self.stats(),(1,3,252,0));self.assertEqual(self.word('transmitBusy'),0);self.assertEqual(self.pumps,1)
        self.complete() # Duplicate/stale completion cannot advance this block twice.
        for aid in range(1,4):self.assertEqual(self.row(aid)[1:3],(126,1))
        self.assertEqual(self.stats()[3],3)

    def test_lagging_recipients_catch_up_without_rewriting_an_ahead_peer(self):
        self.peer(3,offset=126,chunk=1);ahead=self.row(3)
        self.pump();self.assertEqual(self.submissions[-1]['destinations'],6);self.complete()
        self.assertEqual(self.row(3),ahead)
        self.assertEqual(self.stats(),(1,2,126,0))
        self.pump();self.assertEqual(self.submissions[-1]['destinations'],14)
        self.assertEqual(self.submissions[-1]['data'],b'\x01\0'+bytes(range(126,252)))
        self.complete()
        for aid in range(1,4):self.assertEqual(self.row(aid)[1:3],(252,2))
        self.assertEqual(self.stats(),(2,5,378,0))

    def test_submission_or_sdk_completion_errors_do_not_advance_any_peer(self):
        before=self.peers();self.submit_result=5;self.pump()
        self.assertEqual(self.peers(),before);self.assertEqual(self.word('transmitBusy'),0)
        self.submit_result=2;self.pump();self.complete(error=1)
        self.assertEqual(self.peers(),before);self.assertEqual(self.stats(),(0,0,0,0));self.assertEqual(self.pumps,0)

    def test_generation_phase_offset_and_chunk_changes_reject_stale_acknowledgment(self):
        for kwargs in ({'generation':8},{'phase':0},{'offset':126},{'chunk':2}):
            for aid in range(1,4):self.peer(aid)
            self.write('nextAid',1);self.pump();self.peer(2,**kwargs);expected=self.row(2);self.complete()
            self.assertEqual(self.row(2),expected)
            for aid in (1,3):self.assertEqual(self.row(aid)[1:3],(126,1))
        self.assertEqual(self.stats()[3],4)

    def test_execute_barrier_waits_for_every_body_and_terminators_stay_unicast(self):
        for aid in range(1,4):self.peer(aid,offset=self.payload_size)
        self.peer(3,offset=self.payload_size-126,chunk=99)
        self.write('payloadData',self.payload-self.payload_size+126)
        self.pump();self.assertEqual(self.submissions[-1]['destinations'],8)
        self.assertEqual(self.submissions[-1]['data'][:2],struct.pack('<H',99))
        self.complete();self.assertEqual(self.row(3)[1],self.payload_size)
        self.write('nextAid',1);self.pump();packet=self.submissions[-1]
        self.assertEqual(packet['destinations'],2);self.assertEqual(packet['data'],b'\xff\xff')
        self.assertEqual(self.word('transmitTargets'),0)
        self.complete();self.assertEqual(self.row(1)[0],9)
        self.assertEqual(self.word('payloadDone'),2)
        self.assertEqual([self.row(aid)[0] for aid in (2,3)],[8,8])
