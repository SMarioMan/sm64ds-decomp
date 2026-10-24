#!/usr/bin/env python3
"""Build a HaxxStation-only unsigned SM64DS boot probe (no gameplay claim)."""
import hashlib
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

import ndspy.fnt
import ndspy.rom

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'mods/coop'))
from build import branch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--station',type=Path,default=Path('/workspace/inputs/download-station.nds'))
    args=parser.parse_args()
    root = ROOT / 'build/coop/bootstrap'
    root.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'build/coop/sm64ds-coop-experimental.nds'
    rom = ndspy.rom.NintendoDSRom(source.read_bytes())
    # Execute before crt0 decompression/init. This modifies the normally signed
    # ARM9, so firmware must not launch it directly. HaxxStation is the loader.
    marker_address = 0x02004100
    marker = struct.pack('<10I', 0xe59f0014, 0xe59f1014, 0xe5801000,
                         0xe59f1010, 0xe1d110b0, 0xe5801004, 0xeafffffe,
                         0x02000000, 0x504f4f43, 0x027ffc40)
    arm9 = bytearray(rom.arm9)
    start = marker_address - rom.arm9RamAddress
    arm9[start:start + len(marker)] = marker
    entry = rom.arm9EntryAddress - rom.arm9RamAddress
    arm9[entry:entry + 4] = branch(rom.arm9EntryAddress, marker_address)
    rom.arm9 = arm9
    # A Download Station payload needs the executable images only. Story assets
    # will eventually be streamed by the game host after a separate handoff.
    rom.files = []
    rom.filenames = ndspy.fnt.Folder()
    rom.sortedFileIds = []
    rom.arm9OverlayTable = b''
    rom.arm7OverlayTable = b''
    rom.name = b'SM64 COOP DP'
    probe = root / 'boot-probe.nds'
    rom.saveToFile(probe)
    output = root / 'haxxstation-boot-probe.nds'
    subprocess.run(['dspatch', '-s', str(args.station),
                    '-i', str(probe), '-o', str(output)], check=True)
    checked = ndspy.rom.NintendoDSRom(output.read_bytes())
    original = ndspy.rom.NintendoDSRom.fromFile(args.station)
    for name in ('mb/ds_demo_client.srl', 'mb/ds_demo_client.sgn'):
        assert checked.files[checked.filenames.idOf(name)] == original.files[original.filenames.idOf(name)]
    report = {'purpose': 'Unsigned ARM9 execution through real HaxxStation, not gameplay',
              'rom': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'probeBytes': probe.stat().st_size, 'signedDownloadStationClientUnchanged': True,
              'markerAddress': hex(marker_address), 'expectedRam02000000': '434f4f50',
              'bootKindAddress': '0x02000004'}
    (root / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
