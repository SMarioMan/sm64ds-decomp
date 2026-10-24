#!/usr/bin/env python3
"""Build the integrated four-player cartridge from two user-supplied ROMs.

Requires the configured CodeWarrior toolchain, ndspy and dspatch on PATH.
Campaign acceptance remains experimental; this builder performs image audits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path,help='Super Mario 64 DS Europe revision 0')
    parser.add_argument('--station',type=Path,required=True,help='Personal Download Station Volume 1 USA dump')
    parser.add_argument('--save-slot',choices=('A','B','C'),default='A',help='Host adventure file, default A')
    parser.add_argument('--clients',type=int,choices=(1,2,3),default=3)
    parser.add_argument('--channel',type=int,choices=(1,7,13),default=1)
    parser.add_argument('--beacon-period',type=int,default=100)
    parser.add_argument('--output',type=Path,default=ROOT/'build/coop/bootstrap/sm64ds-haxxstation-game-handoff.nds')
    args=parser.parse_args()
    args.rom=args.rom.resolve()
    args.station=args.station.resolve()
    args.output=args.output.resolve()
    for path in (args.rom,args.station):
        if not path.is_file():parser.error(f'Input ROM does not exist: {path}')
    if args.output in (args.rom,args.station):parser.error('Output must not replace an input ROM')
    if not 10<=args.beacon_period<=1000:parser.error('Beacon interval must be between 10 and 1000')
    if not shutil.which('dspatch'):parser.error('dspatch is not on PATH; activate the configured toolchain')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    root=ROOT/'build/coop/bootstrap'
    root.mkdir(parents=True,exist_ok=True)
    def run(script,*arguments):
        subprocess.run([sys.executable,str(ROOT/'mods/coop'/script),*map(str,arguments)],cwd=ROOT,check=True)
    radio=('--clients',args.clients,'--restart-station-parent','--channel',args.channel,
           '--beacon-period',args.beacon_period,'--station',args.station)
    run('build.py',args.rom,'--save-slot',args.save_slot)
    run('bootstrap/build_probe.py','--station',args.station)
    # The provisional parent fixes the final WFS table extents before the
    # executable-only client is packaged. Nothing from this stage is played.
    provisional=root/'provisional-host.nds'
    run('bootstrap/build_host.py',*radio,'--package',root/'haxxstation-boot-probe.nds','--output',provisional)
    run('bootstrap/build_client.py','--host',provisional,'--station',args.station)
    run('bootstrap/build_host.py',*radio,'--handoff','--package',root/'haxxstation-game-client.nds','--output',args.output)
    result=json.loads(args.output.with_suffix('.json').read_text())
    result['buildInputs']={
        'gameSha256':hashlib.sha256(args.rom.read_bytes()).hexdigest(),
        'stationSha256':hashlib.sha256(args.station.read_bytes()).hexdigest()}
    result['campaignCompletionVerified']=False
    args.output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Built {args.output}\nSHA256 {result["sha256"]}\nHost adventure file {args.save_slot}')


if __name__=='__main__':main()
