#!/usr/bin/env python3
"""Build an unsigned Download Station game payload with host overlay hashes.

This is a boot/handoff experiment, not a complete co-op release. HaxxStation
loads the modified executable; the game's overlay verification stays enabled.
The parent must subsequently provide its native wireless filesystem session.
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import struct
import subprocess

import ndspy.code
import ndspy.codeCompression
import ndspy.fnt
import ndspy.rom

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, default=ROOT/'build/coop/bootstrap/sm64ds-haxxstation-host-experimental.nds')
    args = parser.parse_args()
    root = ROOT/'build/coop/bootstrap'
    rom = ndspy.rom.NintendoDSRom(args.host.read_bytes())
    if rom.idCode != b'ASMP' or rom.version != 0:
        raise ValueError('Only Europe revision 0 is supported')
    arm9 = bytearray(ndspy.codeCompression.decompress(rom.arm9))
    base = rom.arm9RamAddress
    key_address, key_size = struct.unpack_from('<II', arm9, 0x0209a04c-base)
    if key_size != 64:
        raise ValueError('Unexpected overlay HMAC key')
    key = arm9[key_address-base:key_address-base+key_size]
    changes = []
    for index, overlay in rom.loadArm9Overlays().items():
        if not overlay.flags & 2:
            raise ValueError(f'Overlay {index} is not authenticated')
        size = overlay.compressedSize if overlay.flags & 1 else overlay.ramSize
        digest = hmac.new(key, rom.files[overlay.fileID][:size], hashlib.sha1).digest()
        offset = 0x0209a7ec + 20*index-base
        if arm9[offset:offset+20] != digest:
            changes.append(index)
            arm9[offset:offset+20] = digest
    if changes != [75]:
        raise ValueError(f'Unexpected changed overlay hashes: {changes}')
    # Keep the original autoload layout, and compress to fit the DS parent's
    # heap alongside the signed loader. Module parameters lie in the ARM9
    # compression format's uncompressed prefix, so patch the final end there.
    settings = ndspy.code.MainCodeFile(arm9, base).codeSettingsOffs
    if settings is None:
        raise ValueError('ARM9 module parameters not found')
    struct.pack_into('<I', arm9, settings+0x14, 0)
    encoded = bytearray(ndspy.codeCompression.compress(arm9, isArm9=True))
    compressed_end = base+len(encoded)
    struct.pack_into('<I', encoded, settings+0x14, compressed_end)
    struct.pack_into('<I', arm9, settings+0x14, compressed_end)
    if ndspy.codeCompression.decompress(encoded) != arm9:
        raise ValueError('ARM9 compression round trip failed')
    rom.arm9 = encoded
    # Verify all overlay digests against the updated executable before stripping
    # the assets. Native WFS will fetch those exact files from the game parent.
    import sys
    sys.path.insert(0, str(ROOT/'mods/coop'))
    from audit_download_play import audit
    checked = audit(rom.save())
    if not checked['valid']:
        raise ValueError('Updated overlay audit failed: '+str(checked))
    host_overlay_digest = hashlib.sha256(rom.files[rom.loadArm9Overlays()[75].fileID]).hexdigest()
    rom.files = []
    rom.filenames = ndspy.fnt.Folder()
    rom.sortedFileIds = []
    rom.arm9OverlayTable = b''
    rom.arm7OverlayTable = b''
    rom.name = b'SM64 COOP DP'
    client = root/'game-client.nds'
    rom.saveToFile(client)
    output = root/'haxxstation-game-client.nds'
    subprocess.run(['dspatch', '-s', '/workspace/inputs/download-station.nds',
                    '-i', str(client), '-o', str(output)], check=True)
    report = {'purpose': 'Unsigned game executable; native parent handoff still required',
              'hostSha256': hashlib.sha256(args.host.read_bytes()).hexdigest(),
              'clientSha256': hashlib.sha256(client.read_bytes()).hexdigest(),
              'changedOverlayHashes': changes, 'overlayHmacAudit': checked,
              'hostOverlay75Sha256': host_overlay_digest,
              'overlayVerificationEnabled': True, 'arm9Bytes': len(encoded),
              'decodedArm9Bytes': len(arm9),
              'output': str(output)}
    (root/'game-client.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
