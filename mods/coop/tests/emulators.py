"""Command driver for real melonDS cores; no emulated memory writes or protocol substitutes."""
import os
from pathlib import Path
import queue
import re
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[3]


class Emulators:
    def __init__(self, rom, clients, output):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.log = (self.output/'transcript.log').open('w')
        self.process = subprocess.Popen(
            [os.environ.get('COOP_HARNESS_EXE', str(ROOT/'build/coop/melon-test')),
             str(Path(rom).resolve()), *['-']*clients],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=dict(os.environ, COOP_LIVE='1'))
        self.count = clients+1
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._collect, daemon=True)
        self.reader.start()

    def _collect(self):
        for line in self.process.stdout:
            self.log.write(line)
            self.log.flush()
            self.lines.put(line.rstrip())
        self.lines.put(None)

    def command(self, text):
        self.log.write('> '+text+'\n')
        self.process.stdin.write(text+'\n')
        self.process.stdin.flush()
        result=[]
        while True:
            try:
                line=self.lines.get(timeout=60)
            except queue.Empty:
                raise RuntimeError('Emulator command timed out: '+text)
            if line is None:
                raise RuntimeError('Emulator exited during: '+text)
            if line=='done '+text:
                return result
            result.append(line)

    def run(self, frames):
        return self.command(f'run {frames}')

    def touch(self, index, x, y):
        self.command(f'touch {index} {x} {y}')
        self.run(12)
        self.command(f'release {index}')

    def accept(self):
        for i in range(1,self.count):
            self.command(f'keys {i} ffe')
        self.run(12)
        for i in range(1,self.count):
            self.command(f'keys {i} fff')

    def screens(self, name):
        for i in range(self.count):
            self.command(f'screen {i} {self.output/(name+str(i)+".ppm")}')

    def read(self, index, address, size=4):
        result=self.command(f'read {index} {address:08x} {size}')
        line=next(line for line in result if line.startswith('RAM '))
        return bytes(int(v,16) for v in line.split(':',1)[1].split())

    def word(self, index, address):
        return int.from_bytes(self.read(index,address),'little')

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.reader.join(timeout=2)
        self.log.close()
