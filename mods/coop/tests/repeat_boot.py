#!/usr/bin/env python3
"""Repeat real Download Play cold starts; every failed run remains a failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runs',type=int,default=5)
    parser.add_argument('--clients',type=int,choices=(1,2,3),default=3)
    parser.add_argument('--timeout',type=int,default=900,help='Maximum wall-clock seconds per cold start')
    parser.add_argument('--checkpoint',choices=('menu','story','course-return','course-death','course-star','host-save'),default='story')
    args=parser.parse_args()
    if args.runs<2:parser.error('--runs must be at least 2')
    if args.timeout<1:parser.error('--timeout must be positive')
    if args.output.exists():parser.error('Use a fresh output directory; previous evidence is never replaced')
    args.image=args.image.resolve()
    args.output=args.output.resolve()
    args.output.mkdir(parents=True)
    digest=hashlib.sha256(args.image.read_bytes()).hexdigest()
    results=[]
    report={'romSha256':digest,'requestedRuns':args.runs,
            'checkpoint':args.checkpoint,'timeoutSecondsPerRun':args.timeout,
            'status':'running','runs':results}

    def write():
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')

    write()
    for index in range(args.runs):
        if hashlib.sha256(args.image.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('The cartridge image changed during the repeat test')
        output=args.output/f'run-{index+1}'
        command=[sys.executable,str(ROOT/'mods/coop/bootstrap/smoke.py'),
                 '--parent','native','--image',str(args.image),
                 '--clients',str(args.clients),'--output',str(output)]
        if args.checkpoint=='menu':
            command.append('--loader-only')
        else:
            command.extend(['--story','--shared-menus'])
            # Real users can select their menus at different times. Exercise
            # those waits without ever modifying emulated state or packets.
            schedules=([0,0,0],[0,600,1800],[1800,0,600])
            command.extend(['--menu-select-delays',
                            *map(str,schedules[index%3][:args.clients])])
            if args.checkpoint!='story':command.append('--'+args.checkpoint)
        environment=dict(os.environ)
        if environment.get('COOP_PACKET_LOG'):
            environment['COOP_PACKET_LOG']=str(output/'packets.bin')
        if args.checkpoint=='host-save':
            environment['COOP_SAVE_DIR']=str(output/'cart')
        print(f'Cold start {index+1}/{args.runs}: {args.checkpoint}',flush=True)
        timeout_error=None
        with (args.output/f'run-{index+1}.log').open('w') as log:
            process=subprocess.Popen(command,cwd=ROOT,env=environment,
                                     stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                returncode=process.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timeout_error=f'Cold start exceeded {args.timeout} wall-clock seconds'
                # Terminate this run's own process group, including its cores;
                # do not leave an emulator behind after its Python driver exits.
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
                returncode=process.returncode
            except BaseException:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
                report['status']='interrupted'
                write()
                raise
        path=output/'result.json'
        result=json.loads(path.read_text()) if path.exists() else {'status':'failed','error':'No smoke report'}
        passed=returncode==0 and result.get('status')=='passed'
        results.append({'run':index+1,'passed':passed,'returncode':returncode,
                        'report':str(path),'error':timeout_error or result.get('error')})
        write()
        print(f'Cold start {index+1}: '+('passed' if passed else 'FAILED'),flush=True)
    report['status']='passed' if all(result['passed'] for result in results) else 'failed'
    write()
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':sys.exit(main())
