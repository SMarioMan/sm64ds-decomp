"""Collect the real Chain Chomp star, save it and regain castle control."""
import json
import math
import struct

from campaign import (PLAYER_POINTERS, assert_party_synchronized, direction_toward,
                      player_position, snapshot, walk_to)
from course_death import _castle_ready, walk_to_chain_field


def _find_stump(ds):
    path=ds.output/'star-actor-scan.ram'
    ds.command(f'dump 0 {path}')
    ram=path.read_bytes()
    def word(address):
        if not 0x02000000<=address<=0x023ffffc:
            raise RuntimeError('Invalid actor list during star check')
        return struct.unpack_from('<I',ram,address-0x02000000)[0]
    node=word(0x0209b468)
    seen=set()
    while node and node not in seen and len(seen)<4096:
        seen.add(node)
        actor=word(node+8)
        if word(actor+0xc)&0xffff==27 and word(actor+8)==17:return actor
        node=word(node+4)
    raise RuntimeError('No live Chain Chomp stump in the actual course')


def check_chain_star(ds):
    if any(ds.read(i,0x0209f2f8,1)!=b'\x06' for i in range(ds.count)):
        raise RuntimeError('Star check must start in Bob-omb Battlefield')
    before=ds.read(0,0x0209cab4,30)
    if before[0]&0x80:raise RuntimeError('This private adventure already contains the test star')
    walk_to_chain_field(ds)
    stump=_find_stump(ds)
    # Stay on the upper field, crossing its eastern lip in short controller
    # bursts. A single long diagonal can turn into the mountain collision
    # wall as the following camera rotates.
    for target in ((1700,2850),(1400,2300),(1400,1000),(400,1400)):
        for step in range(180):
            p=player_position(ds)
            if (p[0]-target[0])**2+(p[2]-target[1])**2<90**2:break
            held=direction_toward(ds,*target)|0x800
            if step%8<6:held|=2
            ds.command(f'keys 0 {0xfff^held:03x}')
            ds.run(6)
        else:
            snapshot(ds,'star-field-approach-failed')
            raise RuntimeError(f'Controller route could not cross the field to {target}')
        ds.command('keys 0 fff')
        ds.run(30)
    walk_to(ds,400,1600,tolerance=40,pulse_frames=2,limit=600)
    # Eight-way D-pad directions can skim the narrow post. Use the game's
    # normal analog stylus control for the final alignment instead.
    ds.command('keys 0 fff')
    ds.command('touch 0 128 96')
    ds.run(24)
    origin=ds.read(0,0x0209f4a8,2)
    def steer(active):
        if not active:
            ds.command(f'touch 0 {origin[0]} {origin[1]}')
            return
        px,_,pz=player_position(ds)
        yaw=struct.unpack('<h',ds.read(0,0x020a1164,2))[0]
        angle=math.atan2(400-px,1900-pz)-yaw*math.tau/65536
        radius=24 if (400-px)**2+(1900-pz)**2>150**2 else 14
        ds.command(f'touch 0 {origin[0]+round(radius*math.sin(angle))} {origin[1]+round(radius*math.cos(angle))}')
    completed=False
    for step in range(2400):
        remaining=ds.read(0,stump+0x31e,1)[0]
        if not remaining:
            completed=True
            break
        if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
            raise RuntimeError('Wireless connection failed during the star route')
        if ds.read(0,0x0209f2f8,1)!=b'\x06':
            raise RuntimeError('Controller route died before releasing the Chain Chomp')
        actor=ds.word(0,PLAYER_POINTERS)
        p=player_position(ds)
        main=ds.word(0,ds.word(0,actor+0x370)+8)
        post_y=struct.unpack('<i',ds.read(0,stump+0x60,4))[0]/4096
        distance=((p[0]-400)**2+(p[2]-1900)**2)**.5
        if main==0x020dd9f8: # Ground pound, including its landing animation.
            if ds.read(0,actor+0x6e3,1)==b'\xff':
                steer(True)
                ds.command('keys 0 fff')
                ds.run(1)
                steer(False)
                ds.command('keys 0 fff')
                ds.run(3)
            else:
                steer(False)
                ds.command('keys 0 fff')
                ds.run(1)
        elif main==0x020e2118: # Jump: pound only when above the actual post.
            # The actual pile KCL is only about 107 units wide. Land near
            # its center; the generic actor's interaction radius is too wide.
            held=0x100 if distance<25 and p[1]>post_y+230 else 2
            steer(distance>20)
            ds.command(f'keys 0 {0xfff^held:03x}')
            ds.run(1)
        else:
            held=2
            steer(distance>20)
            ds.command(f'keys 0 {0xfff^held:03x}')
            ds.run(1)
            if step%12==0:
                ds.command('keys 0 fff')
                ds.run(1)
        if step%120==0:
            print('Chain Chomp star:',step,'post hits remaining',remaining,player_position(ds),flush=True)
    ds.command('keys 0 fff')
    ds.command('release 0')
    ds.run(180)
    snapshot(ds,'star-post-release')
    if not completed:raise RuntimeError('Controller route did not finish pounding the stump')
    for step in range(300):
        if ds.read(0,0x0209cab4,30)!=before:break
        held=direction_toward(ds,1529,264)|0x800
        if step%8<6:held|=2
        ds.command(f'keys 0 {0xfff^held:03x}')
        ds.run(12)
    ds.command('keys 0 fff')
    ds.run(180)
    after=ds.read(0,0x0209cab4,30)
    if after==before or not after[0]&0x80:
        snapshot(ds,'star-collection-failed')
        raise RuntimeError('Controller route did not collect the real course star')
    for attempt in range(300):
        if all(_castle_ready(ds,i) for i in range(ds.count)):break
        if ds.read(0,0x0209f2d4,1)==b'\x03':
            ds.touch(0,128,56) # The real Save and Continue button.
            ds.run(120)
            continue
        ds.command('keys 0 ffe')
        ds.run(12)
        ds.command('keys 0 fff')
        ds.run(18)
    else:
        snapshot(ds,'star-castle-return-failed')
        raise RuntimeError('Star collection did not restore castle control on every console')
    assert_party_synchronized(ds,'star-castle-return')
    for console in range(ds.count):
        if ds.read(console,0x0209cab4,30)!=after:
            raise RuntimeError(f'Console {console} did not retain the shared star')
    snapshot(ds,'star-castle-return')
    path=ds.output/'earned-star.sav'
    ds.command(f'dumpcart 0 {path}')
    cart=path.read_bytes()
    selected=ds.read(0,0x0209cdc8,1)[0]
    if selected>2:raise RuntimeError('Invalid host adventure slot after star save')
    offset=selected*128+0x1e
    for bank in (0,len(cart)//2):
        if cart[bank+offset:bank+offset+30]!=after:
            raise RuntimeError('The controller-earned star was not saved in both host backup banks')
    (ds.output/'course-star.json').write_text(json.dumps({
        'consoles':ds.count,'before':before.hex(),'after':after.hex(),
        'starPersisted':True,'castleControlRestored':True},indent=2)+'\n')
    print(f'Real Chain Chomp star collected, shared and saved with {ds.count} consoles.',flush=True)
