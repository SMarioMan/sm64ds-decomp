"""Actual retail touch initialization in an isolated ARM fixture.

SDK VBlanks can elapse without a game input update during synchronous WFS.
This checks that controller drivers must await the native delay and touch state;
no running emulator or wireless input is modified.
"""
import unittest
from test_particle_heap import HeapHarness
class TouchInitializationTests(HeapHarness,unittest.TestCase):
 def test_initialization_counts_native_updates_not_video_frames(self):
  start=0x0202c2ac;size=0x584
  section=next(s for s in self.main.sections if s.ramAddress<=start and start+size<=s.ramAddress+len(s.data))
  self.cpu.mem_write(start,bytes(section.data[start-section.ramAddress:start-section.ramAddress+size]))
  self.cpu.mem_write(0x0209f2d8,b'\0')
  self.write(0x0209caa8,self.word(0x0209caa8)|0x80)
  self.write(0x0209fc48,0)
  self.cpu.mem_write(0x0209f21c,b'\4')
  self.cpu.mem_write(0x0209f498,bytes(4*24))
  self.cpu.mem_write(0x0209f350,bytes(4))
  self.cpu.mem_write(0x020a0de8,bytes(16))
  self.cpu.mem_write(0x020a0e58,bytes(16))
  self.cpu.mem_write(0x0209d660,b'\0')
  slot=3;touch=0x020a0de8+slot*4;control=0x0209f498+slot*24
  self.cpu.mem_write(touch,bytes((1,1,128,96)))
  self.call(start,0)
  self.assertEqual(bytes(self.cpu.mem_read(control+0x10,5)),bytes((128,96,4,0,1)))
  self.cpu.mem_write(touch,bytes((1,0,128,96)))
  # Advancing the SDK VBlank clock does not execute CheckInput or its delay.
  self.write(0x023ffc3c,self.word(0x023ffc3c)+24)
  self.assertEqual(bytes(self.cpu.mem_read(control+0x12,1)),b'\4')
  for expected in (3,2,1,0):
   self.call(start,0)
   self.assertEqual(bytes(self.cpu.mem_read(control+0x12,1)),bytes((expected,)))
  self.assertEqual(bytes(self.cpu.mem_read(control+0x10,2)),bytes((128,96)))
if __name__=='__main__':unittest.main()
