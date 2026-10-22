#!/usr/bin/env python3
"""Read registers and stacks at loader shutdown using melonDS's stock GDB stub.

No emulated memory/register writes: hardware breakpoints, reads, and continue.
This debugger run is separate from the ordinary emulator acceptance tests.
"""
import argparse
import json
from pathlib import Path
import socket
import struct
import time


class Remote:
    def __init__(self, port):
        deadline=time.monotonic()+60
        while True:
            try:
                self.socket=socket.create_connection(('127.0.0.1',port),timeout=2)
                self.socket.settimeout(180)
                self.socket.sendall(b'+')
                if self.socket.recv(1)!=b'+':
                    self.socket.close()
                    continue
                break
            except (ConnectionRefusedError,ConnectionResetError):
                if time.monotonic()>deadline:raise
                time.sleep(.2)

    def send(self, command):
        data=command.encode('ascii')
        self.socket.sendall(b'$'+data+b'#'+f'{sum(data)&255:02x}'.encode())

    def receive(self):
        while True:
            byte=self.socket.recv(1)
            if not byte:raise EOFError('GDB stub closed')
            if byte==b'$':break
        data=bytearray()
        while True:
            byte=self.socket.recv(1)
            if not byte:raise EOFError('Truncated GDB packet')
            if byte==b'#':break
            data+=byte
        check=b''
        while len(check)<2:check+=self.socket.recv(2-len(check))
        if int(check,16)!=sum(data)&255:raise ValueError('GDB checksum mismatch')
        self.socket.sendall(b'+')
        return data.decode('ascii')

    def command(self, command):
        self.send(command)
        return self.receive()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=3149)
    parser.add_argument('--address',type=lambda s:int(s,16),action='append')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ready',type=Path,help='Write this marker after installing breakpoints')
    args=parser.parse_args()
    remote=Remote(args.port)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w') as out:
        capabilities=remote.command('qSupported')
        out.write(json.dumps({'capabilities':capabilities})+'\n');out.flush()
        for address in args.address or [0x02331ad8]:
            result=remote.command(f'Z1,{address:x},2')
            if result!='OK':raise RuntimeError('Breakpoint rejected: '+result)
        if args.ready:args.ready.write_text('ready\n')
        remote.send('c')
        while True:
            try:stop=remote.receive()
            except (EOFError,ConnectionError):break
            if not stop.startswith(('S','T')):continue
            registers=bytes.fromhex(remote.command('g'))
            words=struct.unpack('<'+'I'*(len(registers)//4),registers)
            stack=remote.command(f'm{words[13]:x},200')
            out.write(json.dumps({'stop':stop,'registers':[hex(w) for w in words],
                                  'stackAddress':hex(words[13]),'stack':stack})+'\n')
            out.flush()
            remote.send('c')


if __name__=='__main__':main()
