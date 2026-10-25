"""Collect a real Bob-omb Battlefield coin with a selected controller."""
import json
import math
import struct

from campaign import assert_party_synchronized, player_position, snapshot, touch_walk_to, walk_to


def check_shared_coin_pickup(ds, controller):
    if not 0<=controller<ds.count:raise ValueError('Coin controller is not connected')
    if any(ds.read(i,0x0209f2f8,1)!=b'\x06' for i in range(ds.count)):
        raise RuntimeError('Shared coin pickup must start in Bob-omb Battlefield')
    def counters():
        return [struct.unpack('<4h',ds.read(i,0x0209f358,8)) for i in range(ds.count)]
    before=counters()
    if len(set(before))!=1 or len(set(before[0]))!=1:
        raise RuntimeError(f'Team coins already disagree before the pickup: {before}')
    # These five native gold coins are on the lower floor under the bridge.
    # Keep the collecting guest there while another controller uses the deck.
    slot=ds.read(controller,0x020a0f10,1)[0]
    px,py,pz=player_position(ds,controller,slot)
    near=py<100 and math.hypot(px+664,pz-5506)<300
    if not near:
        for x,z in ((-5000,5200),(-4000,4500),(-664,4500)):
            walk_to(ds,x,z,console=controller,tolerance=100,pulse_frames=6,limit=300)
    # Inspect the remaining native gold coins in this lower-floor row. A
    # previous navigation attempt may already have collected its first coin.
    scan=ds.output/'coin-targets.ram'
    ds.command(f'dump {controller} {scan}')
    data=scan.read_bytes()
    pattern=struct.pack('<I',0x021087ec) # EU0 daCoin_c vtable.
    targets=[]
    offset=data.find(pattern)
    while offset>=0:
        if offset%4==0 and offset+0x68<=len(data):
            kind=struct.unpack_from('<H',data,offset+12)[0]
            cx,cy,cz=(v/4096 for v in struct.unpack_from('<3i',data,offset+0x5c))
            if kind==0x120 and -800<=cx<=600 and abs(cy)<20 and abs(cz-5506)<10:
                targets.append((cx,cz))
        offset=data.find(pattern,offset+4)
    if not targets:raise RuntimeError('No native gold coins remain in the test row')
    px,_,pz=player_position(ds,controller,slot)
    target=min(targets,key=lambda point:math.hypot(point[0]-px,point[1]-pz))
    # The lower approach has a terrain lip that slow walking cannot clear.
    # Native jump pulses cross it; land near the real coin before checking
    # the shared total. This path is controller input, not a position write.
    touch_walk_to(ds,*target,console=controller,tolerance=60,limit=400,jump=True)
    ds.run(120)
    after=counters()
    if len(set(after))!=1 or len(set(after[0]))!=1 or after[0][0]<=before[0][0]:
        snapshot(ds,'shared-coin-pickup-failed')
        raise RuntimeError(f'Real coin pickup did not increase one shared total on every console: {before} -> {after}')
    assert_party_synchronized(ds,'shared-coin-pickup')
    snapshot(ds,'shared-coin-pickup')
    result={'controller':controller,'consoles':ds.count,'before':before,'after':after,
            'syntheticState':False,'sharedTotalPassed':True,'nativeCoinTarget':target}
    (ds.output/'shared-coin-pickup.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Real guest coin pickup shared on {ds.count} consoles: {before[0][0]} -> {after[0][0]}',flush=True)
