#!/usr/bin/env python3
"""Replay story interactions on one DS; this is not wireless acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from campaign import check_castle_entry, check_castle_key
from emulators import Emulators, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/coop/sm64ds-coop-experimental.nds')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with Emulators(args.image,0,args.output) as ds:
        for line in (Path(__file__).with_name('local_story.commands')).read_text().splitlines():
            line=line.strip()
            if line.startswith('screen'):
                break
            if line and not line.startswith('#'):
                ds.command(line)
        check_castle_key(ds)
        check_castle_entry(ds)
        (ds.output/'result.json').write_text(json.dumps({
            'romSha256':hashlib.sha256(args.image.read_bytes()).hexdigest(),
            'consoles':1,'wirelessAcceptance':False,
            'checks':['locked-door-and-lakitu','castle-key','castle-interior-entry'],
            'campaignCompletionVerified':False},indent=2)+'\n')


if __name__=='__main__':
    main()
