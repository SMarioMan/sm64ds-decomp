"""Diagnostic reads must not kill a live wireless party on an oversized field."""
import os
import unittest
from unittest.mock import patch
from emulators import Emulators


class ObservationReadTests(unittest.TestCase):
    def setUp(self):
        self.ds=object.__new__(Emulators);self.ds.count=4;self.commands=[]
        def command(text):
            self.commands.append(text);tokens=text.split();result=[]
            for i in range(2,len(tokens),2):
                address=int(tokens[i],16);size=int(tokens[i+1]);self.assertLessEqual(size,1024)
                result.append(f'RAM 0 {address:08x}:'+''.join(f' {(address+j)&255:x}' for j in range(size)))
            return result
        self.ds.command=command

    def test_large_profile_field_and_adjacent_counter_share_one_valid_request(self):
        with patch.dict(os.environ,{'COOP_BATCH_INPUT':'1'}):
            values=self.ds.readv(0,((0x02000123,1792),(0x02001000,4)))
        self.assertEqual(len(self.commands),1)
        self.assertEqual(values,[bytes((0x123+j)&255 for j in range(1792)),bytes(range(4))])

    def test_bad_ranges_and_aggregate_limit_fail_before_any_frontend_command(self):
        for index,fields in ((4,[(0x02000000,4)]),(0,[(0x02000000,-1)]),
            (0,[(0x02000000,4097)]),(0,[(0x01ffffff,4)]),(0,[(0x023fffff,2)]),
            (0,[(0x02000000,3000),(0x02010000,1097)])):
            with self.subTest(index=index,fields=fields),self.assertRaises(ValueError):
                self.ds.readv(index,fields)
        self.assertEqual(self.commands,[])

    def test_empty_fields_and_full_size_snapshot_reassemble_without_extra_requests(self):
        with patch.dict(os.environ,{'COOP_BATCH_INPUT':'1'}):
            self.assertEqual(self.ds.readv(0,[(0x02000000,0)]),[b''])
            values=self.ds.readv(0,[(0x023ff000,4096)])
        self.assertEqual(len(self.commands),1);self.assertEqual(values,[bytes(range(256))*16])

    def test_nonbatch_path_splits_reads_and_truncated_responses_are_rejected(self):
        reads=[]
        def read(index,address,size):
            reads.append((index,address,size));return bytes((address+j)&255 for j in range(size))
        self.ds.read=read
        with patch.dict(os.environ,{},clear=True):values=self.ds.readv(2,[(0x02000000,1792)])
        self.assertEqual(values,[bytes(range(256))*7]);self.assertEqual(len(reads),2)
        self.ds.command=lambda text:['RAM 0 02000000: 0']
        with patch.dict(os.environ,{'COOP_BATCH_INPUT':'1'}),self.assertRaises(RuntimeError):
            self.ds.readv(0,[(0x02000000,4)])
