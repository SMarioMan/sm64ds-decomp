"""Local controller RPC for keeping real emulator sessions alive between checks.

Start smoke.py --story --control-socket PATH, then use RemoteEmulators from
another test process. This socket controls only the test frontend; the game
and its wireless packets still run in unmodified melonDS cores.
"""
import json
from pathlib import Path
import socket

from emulators import Emulators


def _pause(ds):
    for console in range(ds.count):
        ds.set_input(console,0xfff)
    for _ in range(20):
        if ds.read(0,0x0209f2c4,1)[0]:return True
        scene=ds.word(0,0x0209f5c0)
        if (0x02000000<=scene<0x023ff000 and
            ds.read(0,scene+0xc,2)==b'\x03\0' and
            not ds.read(0,scene+0x13,1)[0]&1):
            ds.command('keys 0 ff7')
            ds.run(24)
            ds.command('keys 0 fff')
        ds.run(30)
    return False


def serve(ds, path):
    path=Path(path).resolve()
    if path.exists():raise RuntimeError(f'Control socket already exists: {path}')
    state=ds.output/'control-session.json'
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    shutdown=False
    try:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(1)
        state.write_text(json.dumps({'status':'ready','socket':str(path),
            'consoles':ds.count,'paused':_pause(ds)},indent=2)+'\n')
        print('Controller session ready:',path,flush=True)
        while not shutdown:
            connection,_=listener.accept()
            try:
                with connection, connection.makefile('rwb') as stream:
                    for line in stream:
                        try:
                            action,value=json.loads(line)
                            if action=='command':result=ds.command(value)
                            elif action=='pause':result=_pause(ds)
                            elif action=='shutdown':
                                shutdown=True
                                result=True
                            else:raise ValueError('Unknown controller action')
                            reply={'result':result}
                        except Exception as error:
                            reply={'error':f'{type(error).__name__}: {error}'}
                        stream.write(json.dumps(reply).encode()+b'\n')
                        stream.flush()
                        if shutdown:break
            except (BrokenPipeError,ConnectionResetError):
                # A client may be interrupted while an ordinary frontend
                # command is running. Keep the cores and listener alive.
                pass
            finally:
                if not shutdown:_pause(ds)
        state.write_text(json.dumps({'status':'closed','socket':str(path),
                                    'consoles':ds.count},indent=2)+'\n')
    finally:
        listener.close()
        path.unlink(missing_ok=True)


class RemoteEmulators(Emulators):
    """Reuse ordinary input/read helpers without restarting the consoles."""
    def __init__(self, path, output, count=4):
        self.output=Path(output).resolve()
        self.output.mkdir(parents=True,exist_ok=True)
        self.count=count
        self.closed=False
        self.request_pending=False
        self.connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.connection.settimeout(90)
        self.connection.connect(str(path))
        self.stream=self.connection.makefile('rwb')

    def _request(self, action, value=None):
        if self.request_pending:
            raise RuntimeError('An earlier controller request did not finish; reconnect')
        self.request_pending=True
        self.stream.write(json.dumps([action,value]).encode()+b'\n')
        self.stream.flush()
        line=self.stream.readline()
        if not line:raise RuntimeError('Controller session disconnected')
        response=json.loads(line)
        self.request_pending=False
        if 'error' in response:raise RuntimeError(response['error'])
        return response['result']

    def command(self, text):
        return self._request('command',text)

    def shutdown(self):
        self._request('shutdown')
        self.closed=True

    def __exit__(self, *error):
        try:
            if not self.closed and not self.request_pending:self._request('pause')
        except (OSError,RuntimeError):
            if not error[0]:raise
        finally:
            self.stream.close()
            self.connection.close()
