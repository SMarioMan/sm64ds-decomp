"""Controller socket lifecycle checks with a fake frontend, not gameplay."""
import json
from pathlib import Path
import socket
import struct
import tempfile
import threading
import unittest

from session_control import RemoteEmulators, serve


class SessionControlTests(unittest.TestCase):
    def test_interrupted_client_does_not_end_the_listener(self):
        with tempfile.TemporaryDirectory(prefix='coop-controller-') as directory:
            root=Path(directory)
            path=root/'control.sock'
            entered=threading.Event()
            release=threading.Event()
            errors=[]
            class Frontend:
                count=1
                output=root
                def set_input(self,*args):pass
                def read(self,*args):return b'\x01' # Already physically paused.
                def command(self,value):
                    if value=='blocked':
                        entered.set()
                        if not release.wait(2):raise RuntimeError('Test command did not resume')
                    return ['ok']
            def run():
                try:serve(Frontend(),path)
                except Exception as error:errors.append(error)
            thread=threading.Thread(target=run,daemon=True)
            thread.start()
            client=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            for _ in range(200):
                try:client.connect(str(path));break
                except (FileNotFoundError,ConnectionRefusedError):threading.Event().wait(.01)
            else:self.fail('Controller listener did not start')
            client.sendall(json.dumps(['command','blocked']).encode()+b'\n')
            self.assertTrue(entered.wait(1))
            # Reset the connection while the server is still handling input.
            client.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0))
            client.close()
            release.set()
            with RemoteEmulators(path,root/'second',count=1) as remote:
                self.assertEqual(remote.command('ping'),['ok'])
                remote.shutdown()
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors,[])
            self.assertEqual(json.loads((root/'control-session.json').read_text())['status'],'closed')

    def test_timed_out_client_does_not_send_a_misordered_pause_request(self):
        with tempfile.TemporaryDirectory(prefix='coop-controller-timeout-') as directory:
            root=Path(directory)
            path=root/'control.sock'
            listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            listener.bind(str(path))
            listener.listen(1)
            received=[]
            def run():
                connection,_=listener.accept()
                with connection,connection.makefile('rb') as stream:
                    received.append(stream.readline())
                    received.append(stream.readline()) # EOF, never another RPC.
            thread=threading.Thread(target=run,daemon=True)
            thread.start()
            try:
                with self.assertRaises(TimeoutError):
                    with RemoteEmulators(path,root/'remote',count=1) as remote:
                        remote.connection.settimeout(.05)
                        remote.command('unanswered')
                thread.join(2)
                self.assertFalse(thread.is_alive())
                self.assertEqual(json.loads(received[0]),['command','unanswered'])
                self.assertEqual(received[1],b'')
            finally:listener.close()


if __name__=='__main__':unittest.main()
