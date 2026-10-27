"""Command driver for real melonDS cores; no emulated memory writes or protocol substitutes."""
import os
import json
from pathlib import Path
import queue
import re
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[3]


class Emulators:
    def __init__(self, rom, clients, output, mp_timeout_ms=None, real_time=True):
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.log = (self.output/'transcript.log').open('w')
        environment=dict(os.environ, COOP_LIVE='1',COOP_STALL_DUMP_DIR=str(self.output))
        if not real_time:
            environment.pop('COOP_LIVE',None)
        if mp_timeout_ms is not None:
            environment['COOP_MP_TIMEOUT_MS']=str(mp_timeout_ms)
        self.process = subprocess.Popen(
            [os.environ.get('COOP_HARNESS_EXE', str(ROOT/'build/coop/melon-test')),
             str(Path(rom).resolve()), *['-']*clients],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=environment)
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
        self.log.flush()
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
        result=[]
        # Several interpreter cores can take more than a minute for a large
        # frame batch. Keep acknowledgements flowing without changing timeouts
        # or the actual number of emulated frames requested.
        while frames:
            batch=min(frames,60)
            result.extend(self.command(f'run {batch}'))
            frames-=batch
        return result

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

    def select_firmware_downloads(self):
        """Retry real firmware selection without selecting the signed menu.

        The BIOS multiboot marker is mirrored in main RAM. Once it is 2 the
        console has left firmware; never send these retries to its application.
        """
        attempts=0
        for i in range(1,self.count):
            if self.read(i,0x023ffc40,2)==b'\x02\0':
                continue
            self.touch(i,180,75)
            if self.read(i,0x023ffc40,2)==b'\x02\0':
                continue
            self.command(f'keys {i} ffe')
            self.run(12)
            self.command(f'keys {i} fff')
            attempts+=1
        return attempts

    def screens(self, name):
        for i in range(self.count):
            self.command(f'screen {i} {self.output/(name+str(i)+".ppm")}')

    def read(self, index, address, size=4):
        result=self.command(f'read {index} {address:08x} {size}')
        line=next(line for line in result if line.startswith('RAM '))
        return bytes(int(v,16) for v in line.split(':',1)[1].split())

    def readv(self, index, fields):
        """Read at most4KB under one core lock; split large individual fields.

        Validate before sending: a malformed command terminates the test
        frontend, so a diagnostic size mistake must not discard a live party.
        """
        fields=list(fields)
        if not 0<=index<self.count:raise ValueError('Invalid console index')
        if any(size<0 or size>4096 or address<0x02000000 or address>0x02400000-size
               for address,size in fields) or sum(size for _,size in fields)>4096:
            raise ValueError('Read vector must fit4KB of main RAM')
        chunks=[];groups=[]
        for address,size in fields:
            start=len(chunks)
            chunks.extend((address+offset,min(1024,size-offset)) for offset in range(0,size,1024))
            groups.append((start,len(chunks)))
        if not chunks:return [b'' for _ in fields]
        if not os.environ.get('COOP_BATCH_INPUT'):
            values=[self.read(index,address,size) for address,size in chunks]
        else:
            lines=self.command(f'readv {index} '+ ' '.join(f'{address:08x} {size}' for address,size in chunks))
            values=[bytes(int(v,16) for v in line.split(':',1)[1].split())
                    for line in lines if line.startswith('RAM ')]
        if len(values)!=len(chunks) or any(len(value)!=size for value,(_,size) in zip(values,chunks)):
            raise RuntimeError('Incomplete read vector')
        return [b''.join(values[start:end]) for start,end in groups]

    def set_input(self, index, keys, touch=None):
        if os.environ.get('COOP_BATCH_INPUT'):
            x,y=touch if touch is not None else (-1,0)
            self.command(f'input {index} {keys:03x} {x} {y}')
        else:
            self.command(f'keys {index} {keys:03x}')
            self.command(f'touch {index} {touch[0]} {touch[1]}' if touch is not None else f'release {index}')

    def word(self, index, address):
        return int.from_bytes(self.read(index,address),'little')

    def __enter__(self):
        return self

    def __exit__(self, *error):
        retained=os.environ.get('COOP_FAILURE_CONTROL_SOCKET')
        if error[0] is not None and retained and self.process.poll() is None:
            # Keep the original failure, even if later physical-input work
            # succeeds. A separate continuation report must record that work.
            (self.output/'retained-failure.json').write_text(json.dumps({
                'status':'failed','error':f'{error[0].__name__}: {error[1]}',
                'controlSocket':retained},indent=2)+'\n')
            report=self.output/'result.json'
            if report.exists():
                result=json.loads(report.read_text())
                result.update(status='failed',error=f'{error[0].__name__}: {error[1]}')
                report.write_text(json.dumps(result,indent=2)+'\n')
            from session_control import serve
            serve(self,Path(retained))
        self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.reader.join(timeout=2)
        self.log.close()
