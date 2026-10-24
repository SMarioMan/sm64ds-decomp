#!/usr/bin/env python3
"""Check compiler-generated calls at the relocatable module boundary."""
import os
from pathlib import Path
import shlex
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'mods/coop'), str(ROOT/'mods/coop/bootstrap')]
from build import link
from relocatable import relocations


class RelocationTests(unittest.TestCase):
    def compile_call(self, directory, after):
        directory = Path(directory)
        source = directory/'call.cpp'
        source.write_text('extern "C" {\n'
                          'void CoopOriginal(void);\n'
                          'volatile unsigned CoopCounter;\n'
                          'unsigned char CoopStorage[128];\n'
                          'void CoopCaller(void) { CoopOriginal(); '+after+' }\n}\n')
        prefix = directory/'call'
        base = 0x02200000
        body, _ = link(source, prefix, base, {'CoopOriginal':base+0x40},
                       shlex.split(os.environ['MWCCARM_LAUNCHER']),
                       ROOT/'tools/mwccarm/2004/b56/mwccarm.exe',
                       ROOT/'tools/mwccarm/1.2/sp2p3/mwldarm.exe')
        return prefix, base, body

    def test_tail_call_literal_is_relocated(self):
        with tempfile.TemporaryDirectory(prefix='coop-relocation-') as directory:
            prefix, base, body = self.compile_call(directory, '')
            records = relocations(prefix.with_suffix('.o'), prefix.with_suffix('.elf'), base, body)
            pointers = [record for record in records if not record & 0x80000000
                        and struct.unpack_from('<I', body, record)[0] == base+0x40]
            self.assertTrue(pointers, 'Tail-call trampoline address has no ABS32 fixup')

    def test_non_tail_call_needs_no_external_branch_adjustment(self):
        with tempfile.TemporaryDirectory(prefix='coop-relocation-') as directory:
            prefix, base, body = self.compile_call(directory, '++CoopCounter;')
            records = relocations(prefix.with_suffix('.o'), prefix.with_suffix('.elf'), base, body)
            self.assertFalse(any(record & 0x80000000 for record in records))


if __name__ == '__main__':
    unittest.main()
