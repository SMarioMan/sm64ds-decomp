#!/usr/bin/env python3
"""Check EU revision-0 NitroSDK overlay HMACs, not the Nintendo RSA signature.

The stock child calls func_0205dd9c before decompressing each overlay. It
requires flag bit 1 and compares HMAC-SHA1 with the table embedded in ARM9.
Changing an overlay without updating that table causes Crash(), even when the
initial signed Download Play image has booted successfully.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import struct

import ndspy.codeCompression
import ndspy.rom


def audit(data):
    rom = ndspy.rom.NintendoDSRom(data)
    if rom.idCode != b'ASMP' or rom.version != 0:
        raise ValueError('Only Europe revision 0 is supported')
    arm9 = ndspy.codeCompression.decompress(rom.arm9)
    def offset(address):
        result = address - rom.arm9RamAddress
        if not 0 <= result < len(arm9):
            raise ValueError('Authentication data is outside ARM9')
        return result
    key_address, key_size = struct.unpack_from('<II', arm9, offset(0x0209A04C))
    if key_size != 64:
        raise ValueError('Unexpected overlay HMAC key size')
    key = arm9[offset(key_address):offset(key_address) + key_size]
    checks = []
    for index, overlay in rom.loadArm9Overlays().items():
        entry = offset(0x0209A7EC + 20 * index)
        expected = arm9[entry:entry + 20]
        encoded = rom.files[overlay.fileID]
        size = overlay.compressedSize if overlay.flags & 1 else overlay.ramSize
        actual = hmac.new(key, encoded[:size], hashlib.sha1).digest()
        checks.append({'overlay': index, 'authenticatedFlag': bool(overlay.flags & 2),
                       'valid': bool(overlay.flags & 2) and hmac.compare_digest(expected, actual),
                       'expected': expected.hex(), 'actual': actual.hex()})
    return {'scope': 'EU rev0 overlay HMAC only; RSA and session handoff are separate',
            'overlays': len(checks), 'valid': all(c['valid'] for c in checks),
            'failures': [c for c in checks if not c['valid']]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    result = audit(args.rom.read_bytes())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['valid'] else 2)


if __name__ == '__main__':
    main()
