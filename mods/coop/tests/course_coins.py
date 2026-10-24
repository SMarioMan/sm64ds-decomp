"""Collect a real Bob-omb Battlefield coin with a selected controller."""
import json
import struct

from campaign import assert_party_synchronized, snapshot, walk_to


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
    for x,z in ((-5000,5200),(-4000,4500),(-664,4500),(-664,5506)):
        final=(x,z)==(-664,5506)
        walk_to(ds,x,z,console=controller,tolerance=45 if final else 100,
                pulse_frames=2 if final else 6,limit=300)
    ds.run(120)
    after=counters()
    if len(set(after))!=1 or len(set(after[0]))!=1 or after[0][0]<=before[0][0]:
        snapshot(ds,'shared-coin-pickup-failed')
        raise RuntimeError(f'Real coin pickup did not increase one shared total on every console: {before} -> {after}')
    assert_party_synchronized(ds,'shared-coin-pickup')
    snapshot(ds,'shared-coin-pickup')
    result={'controller':controller,'consoles':ds.count,'before':before,'after':after,
            'syntheticState':False,'sharedTotalPassed':True}
    (ds.output/'shared-coin-pickup.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Real guest coin pickup shared on {ds.count} consoles: {before[0][0]} -> {after[0][0]}',flush=True)
