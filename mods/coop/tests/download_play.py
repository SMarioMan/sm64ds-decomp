#!/usr/bin/env python3
"""Real Download Play smoke: one cartridge, three firmware-only melonDS peers.

Requires the native test harness, user-provided DS BIOS/firmware, and EU rev0.
Exit zero establishes four consoles in a stage with the requested rules mode;
it does not establish campaign completion, shared saves, or absence of desyncs.
"""
import argparse
import os
from pathlib import Path
import queue
import re
import subprocess
import threading

REPO = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-mode', type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, COOP_LIVE='1')
    with (output / 'transcript.log').open('w') as log:
        process = subprocess.Popen([os.environ.get('COOP_HARNESS_EXE',str(REPO / 'build/coop/melon-test')), str(args.rom.resolve()), '-', '-', '-'],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, env=env)
        lines = queue.Queue()
        def collect():
            for line in process.stdout:
                log.write(line)
                log.flush()
                lines.put(line.rstrip())
            lines.put(None)
        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        def command(text):
            log.write('> ' + text + '\n')
            process.stdin.write(text + '\n')
            process.stdin.flush()
            result = []
            while True:
                try:
                    line = lines.get(timeout=60)
                except queue.Empty:
                    raise RuntimeError('Emulator command timed out: ' + text)
                if line is None:
                    raise RuntimeError('Emulator exited during: ' + text)
                if line == 'done ' + text:
                    return result
                result.append(line)
        def run(frames):
            command(f'run {frames}')
        def touch(console, x, y):
            command(f'touch {console} {x} {y}')
            run(12)
            command(f'release {console}')
        def accept_clients():
            for i in range(1, 4):
                command(f'keys {i} ffe')
            run(12)
            for i in range(1, 4):
                command(f'keys {i} fff')
        def screens(label):
            for i in range(4):
                command(f'screen {i} {output / (label + str(i) + ".ppm")}')
        def ram(console, address, size=1):
            result = command(f'read {console} {address:08x} {size}')
            match = next((re.search(r': ([0-9a-f ]+)$', line) for line in result if line.startswith('RAM ')), None)
            if match is None:
                raise RuntimeError('No RAM result')
            return int.from_bytes(bytes(int(v, 16) for v in match[1].split()), 'little')
        try:
            run(600)
            touch(0, 128, 120)
            for i in range(1, 4):
                touch(i, 128, 140)
            run(300)
            for attempt in range(4):
                touch(0, 32, 170)
                run(300)
                if ram(0, 0x020A0F04) == 3:
                    break
            else:
                screens('host-lobby-failed-')
                raise RuntimeError('Host did not open its native Download Play lobby')
            # Firmware's DS Download Play launcher.
            for i in range(1, 4):
                touch(i, 180, 75)
            run(600)
            screens('discovery-')
            accept_clients()
            run(120)
            screens('confirmation-')
            accept_clients()
            for attempt in range(30):
                run(120)
                for i in range(1,4):
                    if ram(i,0x023ffc40,2)==2:continue
                    touch(i,180,75)
                    if ram(i,0x023ffc40,2)==2:continue
                    command(f'keys {i} ffe')
                    run(12)
                    command(f'keys {i} fff')
                # The unmodified cartridge requires the host's START touch.
                # Wait for all image headers rather than racing discovery.
                work=ram(0,0x020a9db8,4)
                if 0x02000000<=work<0x023f0000 and all(
                        ram(0,work+0x14e8+4*i,4)==14 for i in range(3)):
                    touch(0,128,170)
                if all(ram(i,0x023ffc40,2)==2 for i in range(1,4)):
                    break
            screens('after-download-')
            reached = False
            for attempt in range(12):
                status = command('status')
                if any(0x02013F4C <= int(pc, 16) < 0x02014150
                       for line in status for pc in re.findall(r'arm9pc=([0-9a-f]+)', line)):
                    screens('fatal-')
                    raise RuntimeError('A client entered the game fatal-error loop; see screenshots and overlay audit')
                # Input is ignored while the game is loading. Repeat until the
                # host's course menu is ready, allowing slower interpreter runs.
                touch(0, 32, 72)
                run(120)
                touch(0, 128, 20)
                run(300)
                reached = all(ram(i, 0x0209F21C) == 4
                              and ram(i, 0x0209F2D8) == args.expect_mode
                              and all(ram(i, 0x0209F394 + 4*j, 4) != 0 for j in range(4))
                              for i in range(4))
                if reached:
                    break
            screens('stage-')
            if not reached:
                raise RuntimeError(f'Four consoles did not reach a four-player stage in mode {args.expect_mode}')
            print('Four-console Download Play stage smoke passed; see ' + str(output))
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            reader.join(timeout=2)


if __name__ == '__main__':
    main()
