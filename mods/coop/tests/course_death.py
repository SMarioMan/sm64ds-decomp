"""Exercise a real enemy death and the party's return to castle gameplay."""
from campaign import (PLAYER_POINTERS, PlayerUnavailable, assert_party_synchronized,
                      direction_toward, finish_messages, player_position,
                      snapshot, walk_to)


def walk_to_chain_field(ds, console=0):
    # Cross the level's actual ramps to the Chain Chomp field. All movement
    # uses the host controller; no damage, health, scene or position writes.
    for point in ((-5000,5200),(-4000,4500),(-1500,5500),(-700,5500),
                  (900,5500),(1250,5000),(1800,4900),(2000,4500),
                  (2200,4200),(1750,3800),(1700,3500)):
        walk_to(ds,*point,console=console)


def check_course_death(ds, controller=0):
    if any(ds.read(i,0x0209f2f8,1)!=b'\x06' for i in range(ds.count)):
        raise RuntimeError('Death check must start in Bob-omb Battlefield')
    if not 0<=controller<ds.count:
        raise ValueError("Death controller is not connected")
    walk_to_chain_field(ds,controller)
    slot=ds.read(controller,0x020a0f10,1)[0]
    initial_health=int.from_bytes(ds.read(0,0x02092144+2*slot,2),'little')
    if not initial_health:
        raise RuntimeError('Death check started without a living host player')
    death_seen=False
    for step in range(900):
        if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
            snapshot(ds,'course-death-connection-failed')
            raise RuntimeError('Wireless session failed during enemy death')
        level=ds.read(0,0x0209f2f8,1)[0]
        health=int.from_bytes(ds.read(0,0x02092144+2*slot,2),'little')
        if level==6 and health==0:
            death_seen=True
        if death_seen and all(_castle_ready(ds,i) for i in range(ds.count)):
            ds.command(f'keys {controller} fff')
            finish_messages(ds)
            assert_party_synchronized(ds,'course-death-arrival')
            for console in range(ds.count):
                player=ds.read(console,0x020a0f10,1)[0]
                before=player_position(ds,0,player)
                ds.command(f'keys {console} fef')
                ds.run(24)
                ds.command(f'keys {console} fff')
                ds.run(120)
                after=player_position(ds,0,player)
                if before[0]==after[0] and before[2]==after[2]:
                    snapshot(ds,'course-death-input-failed')
                    raise RuntimeError(f'Console {console} could not move after death')
                assert_party_synchronized(ds,'course-death-input-'+str(console))
            snapshot(ds,'course-death-recovery')
            print(f'Enemy death returned {ds.count} synchronized controllers to the castle.',flush=True)
            return
        try:
            held=direction_toward(ds,600,2100,controller)|0x800 if level==6 and not death_seen else 0
        except PlayerUnavailable:
            held=0
        ds.command(f'keys {controller} {0xfff^held:03x}')
        ds.run(12)
        if step%60==0:
            print('Death check:',step,'controller',controller,'player',slot,'level',level,'health',health,'deathSeen',death_seen,flush=True)
    snapshot(ds,'course-death-failed')
    raise RuntimeError('Enemy death did not return every console to active castle gameplay')


def _castle_ready(ds, console):
    if ds.read(console,0x0209f2f8,1)!=b'\x02':
        return False
    scene=ds.word(console,0x0209f5c0)
    if not 0x02000000<=scene<0x023ff000:
        return False
    if ds.read(console,scene+0xc,2)!=b'\x03\0' or ds.read(console,scene+0x13,1)[0]&1:
        return False
    for slot in range(ds.count):
        player=ds.word(console,PLAYER_POINTERS+slot*4)
        if not 0x02000000<=player<0x023ff000 or ds.read(console,player+0x709,1)[0]:
            return False
    return True
