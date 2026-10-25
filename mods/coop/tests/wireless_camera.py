#!/usr/bin/env python3
"""Check independent native zoom with four real wireless emulator controllers.

Use a normal smoke.py --story --control-socket party in an unrestricted camera
area. Reads observe native state; only physical pad/touch input is submitted.
"""
import argparse
import json
from pathlib import Path

from campaign import assert_party_synchronized, snapshot, wait_controller_buttons
from diagnostic_stage import resume_stage
from session_control import RemoteEmulators


def observe(ds):
    result=[]
    for console in range(ds.count):
        camera=ds.word(console,0x0209f318)
        slot=ds.read(console,0x020a0f10,1)[0]
        actors=[ds.word(console,0x0209f394+4*p) for p in range(ds.count)]
        result.append({'console':console,'slot':slot,
            'far':bool(ds.word(console,camera+0x154)&2),
            'state':hex(ds.word(console,camera+0x138)),
            'mode':ds.read(console,0x0209f4ae+24*slot,1)[0],
            'choices':[ds.read(console,actor+0x715,1)[0] for actor in actors]})
    return result


def check_zoom(ds):
    resume_stage(ds)
    baseline=observe(ds)
    events=[]
    report={'status':'running','consoles':ds.count,'baseline':baseline,'events':events}
    path=ds.output/'camera-controls.json'
    def save():path.write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        for console in range(ds.count):
            for step in range(3):
                before=observe(ds)
                mode=before[console]['mode']
                if mode==0:
                    # Standard mode maps the physical X button to native zoom.
                    ds.set_input(console,0xbff)
                    wait_controller_buttons(ds,console,0x400,held=True)
                    ds.run(6)
                    ds.set_input(console,0xfff)
                    wait_controller_buttons(ds,console,0x400)
                elif mode in (1,2):
                    ds.touch(console,235,165 if mode==1 else 130)
                else:raise RuntimeError('Invalid native controller mode')
                ds.run(90)
                after=observe(ds)
                events.append({'console':console,'step':step,'before':before,'after':after})
                save()
                choices=after[0]['choices']
                if any(peer['choices']!=choices for peer in after):
                    raise RuntimeError('Native player zoom choices diverged')
                for peer in range(ds.count):
                    if peer!=console and any(after[peer][key]!=before[peer][key]
                                             for key in ('far','state')):
                        raise RuntimeError('A foreign zoom button changed the local camera')
                if choices[console]==1:
                    if not after[console]['far']:raise RuntimeError('Local far zoom did not engage')
                elif choices[console]==2:
                    if after[console]['state']!='0x209b098':
                        raise RuntimeError('Local first-person camera did not engage')
                elif choices[console]==0:
                    if after[console]['far'] or after[console]['state']!='0x209b008':
                        raise RuntimeError('Local normal camera did not return')
                else:raise RuntimeError('Invalid native zoom choice')
                if choices[console]==before[console]['choices'][console]:
                    raise RuntimeError('Native zoom button did not change its player choice')
                assert_party_synchronized(ds,f'camera-zoom-{console}-{step}')
            if observe(ds)[console]['choices'][console]!=baseline[console]['choices'][console]:
                raise RuntimeError('Complete zoom cycle did not restore the native choice')
        report['status']='passed'
        ds.screens('camera-controls-')
    except Exception as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}')
        save()
        snapshot(ds,'camera-controls-failed')
        raise
    finally:save()
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with RemoteEmulators(args.socket,args.output) as ds:
        check_zoom(ds)


if __name__=='__main__':main()
