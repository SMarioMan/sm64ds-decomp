#!/usr/bin/env python3
"""Replay story interactions on one DS; this is not wireless acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from campaign import check_castle_entry, check_castle_key, check_first_course, check_course_return
from emulators import Emulators, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/coop/sm64ds-coop-experimental.nds')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--first-course',action='store_true')
    parser.add_argument('--course-return',action='store_true')
    parser.add_argument('--course-death',action='store_true')
    parser.add_argument('--course-star',action='store_true')
    parser.add_argument('--fast',action='store_true',help='Run this single-console diagnostic without wall-clock frame pacing')
    args=parser.parse_args()
    if sum((args.course_return,args.course_death,args.course_star))>1:
        parser.error('Choose one course-return, course-death or course-star checkpoint for one run')
    if args.course_return or args.course_death or args.course_star:
        args.first_course=True
    report={
        'romSha256':hashlib.sha256(args.image.read_bytes()).hexdigest(),
        'consoles':1,'wirelessAcceptance':False,
        'wallClockFramePacing':not args.fast,
        'checks':[], 'campaignCompletionVerified':False,
        'status':'running'}
    args.output.mkdir(parents=True,exist_ok=True)
    try:
        with Emulators(args.image,0,args.output,real_time=not args.fast) as ds:
            for line in (Path(__file__).with_name('local_story.commands')).read_text().splitlines():
                line=line.strip()
                if line.startswith('screen'):
                    break
                if line and not line.startswith('#'):
                    ds.command(line)
            check_castle_key(ds)
            report['checks'].extend(['locked-door-and-lakitu','castle-key'])
            check_castle_entry(ds)
            report['checks'].append('castle-interior-entry')
            if args.first_course:
                check_first_course(ds)
                report['checks'].append('first-course-entry-and-inputs')
            if args.course_return:
                check_course_return(ds)
                report['checks'].append('course-return-and-inputs')
            if args.course_death:
                from course_death import check_course_death
                check_course_death(ds)
                report['checks'].append('enemy-death-and-party-recovery')
            if args.course_star:
                from course_star import check_chain_star
                check_chain_star(ds)
                report['checks'].append('star-collection-persistence-and-party-return')
            report['status']='passed'
    except BaseException as error:
        report['status']='failed'
        report['error']=f'{type(error).__name__}: {error}'
        raise
    finally:
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
