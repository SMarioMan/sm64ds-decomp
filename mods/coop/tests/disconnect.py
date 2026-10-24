"""Require the remaining consoles to end cleanly after a guest powers off."""
from campaign import snapshot


def check_guest_disconnect(ds, metadata, removed=None):
    if ds.count<2:
        raise RuntimeError('Disconnect check requires at least one guest')
    module=metadata['runtimeModule']
    if removed is None:removed=ds.count-1
    if not 0<=removed<ds.count:raise RuntimeError('Invalid console to power off')
    remaining=[i for i in range(ds.count) if i!=removed]
    ds.command(f'poweroff {removed}')
    for attempt in range(120):
        complete=True
        for console in remaining:
            context=ds.word(console,0x0209cddc)
            if 0x02000000<=context<0x023fff80:
                snapshot(ds,'guest-disconnect-exception')
                raise RuntimeError(f'Console {console} raised an exception after guest loss')
            base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
            if (ds.word(console,base+module['diagnosticOffsets']['coopSessionEnded'])!=3 or
                ds.word(console,base+module['diagnosticOffsets']['coopEnabled']) or
                ds.read(console,0x020a0f04,1)[0] or ds.word(console,0x020a1fcc)):
                complete=False
        if complete:
            ds.run(120)
            snapshot(ds,'guest-disconnect-ended')
            print(f'Console {removed} powered off; all remaining consoles ended the session without exceptions.',flush=True)
            return
        ds.run(30)
    snapshot(ds,'guest-disconnect-failed')
    raise RuntimeError('A powered-off guest left a remaining console stuck in gameplay or file sharing')
