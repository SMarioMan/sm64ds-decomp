"""Campaign checks driven only by controller input and read-only RAM snapshots."""
import math
import struct

MIPS_VTABLE = 0x021300f8
PLAYER_POINTERS = 0x0209f394


def player_position(ds, console=0, player=0):
    actor=ds.word(console,PLAYER_POINTERS+player*4)
    if not 0x02000000 <= actor <= 0x023ff000:
        raise RuntimeError(f'Console {console} has no live player {player}: {actor:#x}')
    return tuple(v/4096 for v in struct.unpack('<iii',ds.read(console,actor+0x5c,12)))


def snapshot(ds, name):
    ds.screens(name+'-')
    for console in range(ds.count):
        ds.command(f'dump {console} {ds.output/(name+"-"+str(console)+".ram")}')
        ds.command(f'dumptcm {console} {ds.output/(name+"-"+str(console)+".dtcm")}')
        ds.command(f'regs {console}')


def assert_party_synchronized(ds, name):
    positions=[tuple(player_position(ds,i,p) for p in range(ds.count))
               for i in range(ds.count)]
    progress=[ds.read(i,0x0209caa0,0x40) for i in range(ds.count)]
    if len(set(positions))!=1 or len(set(progress))!=1:
        snapshot(ds,name+'-desynchronized')
        raise RuntimeError(f'Player positions or campaign progress diverged after {name}')


def find_castle_rabbit(ds):
    path=ds.output/'campaign-scan.ram'
    ds.command(f'dump 0 {path}')
    data=path.read_bytes()
    pattern=struct.pack('<I',MIPS_VTABLE)
    offset=data.find(pattern,0x14eb18)
    while offset>=0:
        if offset%4==0 and offset+0x474<=len(data):
            actor=struct.unpack_from('<H',data,offset+0xc)[0]
            rabbit=struct.unpack_from('<i',data,offset+0x43c)[0]
            if actor==187 and rabbit==7:
                return 0x02000000+offset
        offset=data.find(pattern,offset+4)
    raise RuntimeError('Castle-key rabbit was not present in the actual story stage')


def direction_toward(ds, x, z):
    px,_,pz=player_position(ds)
    # GetAngleToCamera(0) reads this synchronized NET record. Native actor
    # velocity uses x=sin(heading), z=cos(heading).
    yaw=struct.unpack('<h',ds.read(0,0x020a1164,2))[0]
    desired=math.atan2(x-px,z-pz)-yaw*math.tau/65536
    # Native Standard-mode D-pad angles, relative to the synchronized camera.
    choices=((0x10,math.pi/2),(0x20,-math.pi/2),(0x40,math.pi),(0x80,0),
             (0x50,3*math.pi/4),(0x60,-3*math.pi/4),(0x90,math.pi/4),(0xa0,-math.pi/4))
    return min(choices,key=lambda item:abs(math.remainder(item[1]-desired,math.tau)))[0]


def advance_message(ds):
    ds.command('keys 0 fff')
    ds.run(20)
    ds.command('keys 0 ffe')
    ds.run(12)
    ds.command('keys 0 fff')
    ds.run(30)


def finish_messages(ds):
    ds.command('keys 0 fff')
    for step in range(120):
        if not any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            ds.run(180)
            if not any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
                return
        advance_message(ds)
    snapshot(ds,'dialogue-failed')
    raise RuntimeError('Shared dialogue did not finish')


def walk_to(ds, x, z, tolerance=100, limit=160):
    for step in range(limit):
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
            continue
        px,_,pz=player_position(ds)
        distance=math.hypot(x-px,z-pz)
        if distance<tolerance:
            ds.command('keys 0 fff')
            ds.run(30)
            return
        held=direction_toward(ds,x,z)
        if distance>300:
            held|=0x800
        ds.command(f'keys 0 {0xfff^held:03x}')
        ds.run(12)
        if step%30==0:
            print('Waypoint:',(x,z),'position',player_position(ds),flush=True)
    snapshot(ds,'waypoint-failed')
    raise RuntimeError(f'Controller route could not reach {(x,z)}')


def introduce_castle_key(ds):
    if all(ds.word(i,0x0209caa8)&0x20000 for i in range(ds.count)):
        return
    # The locked front door triggers Lakitu's explanation. Until it finishes,
    # the native game deliberately leaves the key rabbit inactive.
    # Approach the bridge along the western slope, avoiding the steep bank
    # directly between the spawn clearing and the bridge lawn.
    for x,z in ((-3000,5500),(-3000,3000),(0,1600),(0,500),(0,-1000)):
        walk_to(ds,x,z,tolerance=55)
    walk_to(ds,0,500)
    for step in range(100):
        advance_message(ds)
        if all(ds.word(i,0x0209caa8)&0x20000 for i in range(ds.count)):
            finish_messages(ds)
            assert_party_synchronized(ds,'lakitu-introduction')
            snapshot(ds,'lakitu-introduction')
            print('Lakitu activated the castle-key rabbit on every console.',flush=True)
            return
    snapshot(ds,'castle-introduction-failed')
    raise RuntimeError('Locked-door/Lakitu introduction did not synchronize')


def check_castle_key(ds):
    introduce_castle_key(ds)
    rabbit=find_castle_rabbit(ds)
    print('Castle-key rabbit:',hex(rabbit),flush=True)
    stalled=0
    for step in range(360):
        if all(ds.word(i,0x0209caa4)&0x40 for i in range(ds.count)):
            finish_messages(ds)
            assert_party_synchronized(ds,'castle-key')
            snapshot(ds,'castle-key')
            print(f'Castle key collected and shared on all {ds.count} consoles.',flush=True)
            return
        messages=[ds.read(i,0x0209d660,1)[0] for i in range(ds.count)]
        if any(messages):
            advance_message(ds)
            continue
        if ds.read(0,rabbit+0x107,1)[0] or ds.read(0,rabbit+0x426,1)[0]:
            # Let the capture/talk animation finish without spitting it out.
            ds.command('keys 0 fff')
            ds.run(30)
            continue
        px,py,pz=player_position(ds)
        rx,ry,rz=(v/4096 for v in struct.unpack('<iii',ds.read(0,rabbit+0x5c,12)))
        distance=math.hypot(rx-px,rz-pz)
        held=direction_toward(ds,rx,rz)|0x800 # Y: run
        if distance<350 and step%2==0:
            held|=1 # A: tongue, pulsed so another attack can start
        if stalled>=3:
            held|=2 # B: jump over a small terrain lip
            stalled=0
        ds.command(f'keys 0 {0xfff^held:03x}')
        ds.run(12 if distance<350 else 18)
        after=player_position(ds)
        stalled=stalled+1 if math.hypot(after[0]-px,after[2]-pz)<3 else 0
        if step%20==0:
            print('Rabbit approach:',step,tuple(round(v,1) for v in after),
                  tuple(round(v,1) for v in (rx,ry,rz)),round(distance,1),
                  'caught',ds.read(0,rabbit+0x426,1)[0],flush=True)
    ds.command('keys 0 fff')
    snapshot(ds,'castle-key-failed')
    raise RuntimeError('Controller-driven castle-key interaction did not complete')


def check_castle_entry(ds):
    for x,z in ((-3000,5000),(-3000,3000),(0,1600),(0,500)):
        walk_to(ds,x,z)
    for step in range(180):
        if any(ds.read(i,0x0209f2f8,1)[0]==2 for i in range(ds.count)):
            ds.command('keys 0 fff')
            break
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
        else:
            held=direction_toward(ds,0,-1200)
            ds.command(f'keys 0 {0xfff^held:03x}')
            ds.run(12)
    else:
        snapshot(ds,'castle-door-failed')
        raise RuntimeError('The unlocked castle door did not request level 2')
    for step in range(300):
        ready=all(ds.read(i,0x0209f2f8,1)[0]==2 and
                  not ds.read(i,0x02092778,1)[0] and
                  ds.read(i,0x0209f21c,1)[0]==ds.count and
                  0x02000000<=ds.word(i,PLAYER_POINTERS)<0x023ff000
                  for i in range(ds.count))
        if ready:
            ds.run(180)
            assert_party_synchronized(ds,'castle-entry')
            snapshot(ds,'castle-entry')
            print(f'Castle interior loaded with {ds.count} synchronized players on every console.',flush=True)
            return
        ds.run(60)
    snapshot(ds,'castle-entry-failed')
    raise RuntimeError('Castle interior did not finish loading on every console')
