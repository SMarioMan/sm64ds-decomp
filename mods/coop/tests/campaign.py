"""Campaign checks driven only by controller input and read-only RAM snapshots."""
import os
import math
import json
import struct

MIPS_VTABLE = 0x021300f8
PLAYER_POINTERS = 0x0209f394


class ControllerRouteFailure(RuntimeError):
    """The input driver missed a route; distinct from a game/network failure."""


class PlayerUnavailable(RuntimeError):
    """The old scene's player objects have been retired during a transition."""


def wait_controller_buttons(ds, console, mask, held=False):
    """Wait for a real button edge to appear in native synchronized input.

    A one-emulator-frame release may occur while NET is waiting for peers.
    Keep the physical input unchanged until its decoded state is observed.
    """
    slot=ds.read(console,0x020a0f10,1)[0]
    for attempt in range(90):
        value=int.from_bytes(ds.read(console,0x020a0e58+4*slot,2),'little')
        if (value&mask)==(mask if held else 0):return
        ds.run(1)
    snapshot(ds,'controller-edge-not-acknowledged')
    raise RuntimeError(f'Console {console} button state was not decoded by native input')


def check_yoshi_colors(ds):
    """Require the retail per-slot palettes and both render gates in story mode."""
    parameters=[]
    for console in range(ds.count):
        if ds.read(console,0x0209f2d8,1)!=b'\0':
            raise RuntimeError('Yoshi colors changed the story rules')
        for address in (0x020e3ae8,0x020e3c88):
            if ds.word(console,address)!=0xe3a00001:
                raise RuntimeError(f'Console {console} has no Yoshi palette render gate at {address:#x}')
        values=[]
        for slot in range(ds.count):
            actor=ds.word(console,PLAYER_POINTERS+4*slot)
            if ds.word(console,actor+8)!=3 or ds.read(console,actor+0x6d8,1)!=bytes([slot]):
                raise RuntimeError(f'Console {console} player {slot} is not its native Yoshi slot')
            values.append(ds.word(console,actor+0x61c))
        if values!=[values[0]+2*slot for slot in range(ds.count)]:
            raise RuntimeError(f'Console {console} lost the original multiplayer palette order: {values}')
        parameters.append(values)
    if any(values!=parameters[0] for values in parameters):
        raise RuntimeError(f'Yoshi palettes disagree between consoles: {parameters}')
    (ds.output/'yoshi-colors.json').write_text(json.dumps(parameters,indent=2)+'\n')
    ds.screens('yoshi-colors-')
    print(f'Original per-slot Yoshi palettes active on {ds.count} consoles: {parameters[0]}',flush=True)


def player_position(ds, console=0, player=0):
    actor=ds.word(console,PLAYER_POINTERS+player*4)
    if not 0x02000000 <= actor <= 0x023ff000:
        raise PlayerUnavailable(f'Console {console} has no live player {player}: {actor:#x}')
    return tuple(v/4096 for v in struct.unpack('<iii',ds.read(console,actor+0x5c,12)))


def check_controller_movement(ds, console, checkpoint, press_frames=24, release_frames=120):
    """Require real horizontal movement, allowing an adjacent player or wall.

    Native entry points can place a party side by side. One fixed direction
    can push into another player even while input works; try other physical
    directions before declaring lost control. Never change a player position.
    """
    slot=ds.read(console,0x020a0f10,1)[0]
    for direction in (0x10,0x20,0x80,0x40)*2:
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            finish_messages(ds)
        actor=ds.word(console,PLAYER_POINTERS+4*slot)
        if ds.read(console,0x02092144+2*slot,2)==b'\0\0':
            snapshot(ds,checkpoint+'-controller-dead')
            raise ControllerRouteFailure(f'Console {console} died before its movement check')
        swimming=bool(ds.read(console,actor+0x706,1)[0])
        before=player_position(ds,console,slot)
        # Underwater directions only turn Yoshi; B supplies the native stroke.
        ds.set_input(console,0xfff^(direction | (2 if swimming else 0)))
        wait_controller_buttons(ds,console,direction,held=True)
        ds.run(press_frames)
        ds.set_input(console,0xfff)
        wait_controller_buttons(ds,console,direction | (2 if swimming else 0))
        ds.run(release_frames)
        if ds.read(console,0x02092144+2*slot,2)==b'\0\0':
            snapshot(ds,checkpoint+'-controller-died')
            raise ControllerRouteFailure(f'Console {console} died during its movement check')
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            # A first movement can open the native control/cap tutorial after
            # stage readiness. Finish it with host input before testing again.
            finish_messages(ds)
            continue
        after=player_position(ds,console,slot)
        if before[0]!=after[0] or before[2]!=after[2]:
            assert_party_synchronized(ds,f'{checkpoint}-input-{console}')
            return {'console':console,'slot':slot,'direction':direction,'swimming':swimming,'before':before,'after':after}
    snapshot(ds,checkpoint+'-input-failed')
    raise RuntimeError(f'Console {console} could not move in any tested direction after {checkpoint}')


def snapshot(ds, name):
    ds.screens(name+'-')
    for console in range(ds.count):
        ds.command(f'dump {console} {ds.output/(name+"-"+str(console)+".ram")}')
        ds.command(f'dumptcm {console} {ds.output/(name+"-"+str(console)+".dtcm")}')
        if os.environ.get('COOP_DUMP_ITCM'):
            ds.command(f'dumpitcm {console} {ds.output/(name+"-"+str(console)+".itcm")}')
        ds.command(f'dump7 {console} {ds.output/(name+"-"+str(console)+".arm7")}')
        ds.command(f'regs {console}')
    if os.environ.get('COOP_PERF_SAMPLES'):
        from performance import capture_performance
        capture_performance(ds,name)
    # Decode the captured images, rather than adding live reads that could
    # perturb a failing wireless session. These counters exist only in stage
    # diagnostic builds and never change the normal cartridge image.
    module=getattr(ds,'runtime_module',None) or {}
    diagnostic_fields={
        'coopDiagnosticConnectionFailure':module.get('connectionFailureFields'),
        'coopDiagnosticGameplayRead':module.get('gameplayReadFields'),
        'coopDiagnosticSlowGameplayRead':module.get('gameplayReadFields'),
    }
    render_cost=module.get('diagnosticRenderCost')
    if not any(diagnostic_fields.values()) and not render_cost:return
    diagnostics=[]
    for console in range(ds.count):
        ram=(ds.output/(name+'-'+str(console)+'.ram')).read_bytes()
        if struct.unpack_from('<I',ram,0x4180)[0]!=0x31504f43:
            diagnostics.append({'console':console,'runtimeInstalled':False})
            continue
        base=struct.unpack_from('<I',ram,0x4184)[0]-int(module['entryOffset'],16)
        values={'console':console}
        for symbol,fields in diagnostic_fields.items():
            if not fields:continue
            offset=base+module['diagnosticOffsets'][symbol]-0x02000000
            if offset<0 or offset+len(fields)*4>len(ram):
                values[symbol]={'captureAddressInvalid':hex(base+module['diagnosticOffsets'][symbol])}
                continue
            values[symbol]=dict(zip(fields,struct.unpack_from('<'+'I'*len(fields),ram,offset)))
        if render_cost:
            offsets=module['diagnosticOffsets']
            count=struct.unpack_from('<I',ram,base+offsets['coopDiagnosticRenderCount']-0x02000000)[0]
            fields=render_cost['fields']
            capacity=render_cost['capacity']
            samples=[]
            # The oldest slot may already be receiving its next uncommitted
            # sample when a frame-boundary RAM capture interrupts the draw.
            for sequence in range(max(0,count-capacity+1),count):
                offset=base+offsets['coopDiagnosticRenderCosts']-0x02000000+(sequence%capacity)*len(fields)*4
                samples.append(dict(zip(fields,struct.unpack_from('<'+'I'*len(fields),ram,offset))))
            values['renderCosts']={'completed':count,'changesScheduling':True,'samples':samples}
        diagnostics.append(values)
    if diagnostics:
        (ds.output/(name+'-runtime.json')).write_text(json.dumps(diagnostics,indent=2)+'\n')


def _same_tick_party(ds, name):
    lines=ds.command('partyhistory')
    histories=[{} for _ in range(ds.count)]
    for line in lines:
        if not line.startswith('PARTY '):continue
        fields=line.split()
        console,tick,level,count=map(int,fields[1:5])
        if count!=ds.count:continue
        positions=tuple(map(int,fields[5:5+count*3]))
        histories[console][tick]=(level,positions,fields[5+count*3])
    # The latest tick can still receive its final actor updates. Compare
    # completed ticks retained independently by each running console.
    completed=[set(sorted(history)[:-2]) for history in histories]
    ticks=sorted(set.intersection(*completed))[-12:]
    matched=len(ticks)==12 and ticks==list(range(ticks[0],ticks[0]+12))
    for tick in ticks:
        reference=histories[0][tick]
        for history in histories[1:]:
            level,positions,progress=history[tick]
            if level!=reference[0] or progress!=reference[2]:matched=False
            for component,(a,b) in enumerate(zip(reference[1],positions)):
                if (abs(a-b)>256 if component%3==1 else a!=b):matched=False
    (ds.output/(name+'-same-tick.json')).write_text(json.dumps({
        'matched':matched,'ticks':ticks,
        'samples':[{str(tick):history[tick] for tick in ticks} for history in histories]
    },indent=2)+'\n')
    return matched


def assert_party_synchronized(ds, name):
    # These read-only snapshots are taken serially, on separate VBlanks.
    # The native slope solver adjusts stationary Y by a fraction of a unit;
    # require exact horizontal positions and at most 1/16 unit vertically.
    # Overlapping players can also alternate between the floor and collision
    # pushback while idle. Retry the same strict comparison before declaring
    # divergence; a subsequent diagnostic dump previously showed all four
    # replicas identical after a transient 12-unit vertical difference.
    for attempt in range(4):
        if os.environ.get('COOP_FRAME_SAMPLES') and ds.count>1:
            if _same_tick_party(ds,name):return
            if attempt<3:
                ds.run(60)
                continue
            snapshot(ds,name+'-desynchronized')
            raise RuntimeError(f'Player positions or campaign progress differ at matching input ticks after {name}')
        positions=[tuple(player_position(ds,i,p) for p in range(ds.count))
                   for i in range(ds.count)]
        progress=[ds.read(i,0x0209caa0,0x40) for i in range(ds.count)]
        matched=all(a[0]==b[0] and a[2]==b[2] and abs(a[1]-b[1])<=1/16
                    for party in positions[1:] for a,b in zip(positions[0],party))
        if matched and len(set(progress))==1:
            return
        if attempt<3:
            ds.run(60)
    print('Party positions after',name,positions,flush=True)
    print('Party progress after',name,[value.hex() for value in progress],flush=True)
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


def direction_toward(ds, x, z, console=0):
    slot=ds.read(console,0x020a0f10,1)[0]
    px,_,pz=player_position(ds,console,slot)
    # Physical input is paired with this console's outgoing camera angle.
    # The echoed NET angle is older and can drift badly while the camera
    # rotates. Native actor velocity uses x=sin(heading), z=cos(heading).
    yaw=struct.unpack('<h',ds.read(console,0x020a1050,2))[0]
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


def finish_messages(ds, level_clear_choice=None):
    ds.command('keys 0 fff')
    def ready():
        for console in range(ds.count):
            if ds.read(console,0x0209d660,1)[0]:return False
            for slot in range(ds.count):
                actor=ds.word(console,PLAYER_POINTERS+4*slot)
                if not 0x02000000<=actor<0x023ff000:return False
                if ds.read(console,actor+0x709,1)[0] or ds.read(console,actor+0x71e,1)[0]:return False
        return True
    for step in range(120):
        for console in range(ds.count):
            crash,exception=ds.readv(console,((0x0209d4d8,1),(0x0209cddc,4)))
            if crash!=b'\0' or int.from_bytes(exception,'little'):
                snapshot(ds,'dialogue-native-fault')
                raise RuntimeError(f'Native fault while finishing shared messages on console {console}')
        if level_clear_choice is not None and ds.read(0,0x0209f2d4,1)==b'\x03':
            ds.touch(0,*level_clear_choice)
            ds.run(120)
            continue
        if ready():
            ds.run(30)
            if ready():return
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
        else:
            # A message can close before the actor's next conversation step
            # opens another one. Wait for every player to regain control.
            ds.run(30)
    snapshot(ds,'dialogue-failed')
    raise RuntimeError('Shared dialogue did not finish')


def walk_to(ds, x, z, tolerance=100, limit=160, pulse_frames=12, stop_when=None, console=0):
    slot=ds.read(console,0x020a0f10,1)[0]
    stalled=0
    for step in range(limit):
        if stop_when is not None and stop_when():
            ds.command(f'keys {console} fff')
            ds.run(30)
            return
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
            continue
        px,_,pz=player_position(ds,console,slot)
        distance=math.hypot(x-px,z-pz)
        if distance<tolerance:
            ds.command(f'keys {console} fff')
            ds.run(30)
            stopped=player_position(ds,console,slot)
            if math.hypot(x-stopped[0],z-stopped[2])<tolerance:
                return
            continue
        held=direction_toward(ds,x,z,console)
        if distance>300 and pulse_frames>2:
            held|=0x800
        if stalled>=3 and pulse_frames>2:
            held|=2 # B: clear a hedge or small terrain lip
            stalled=0
        ds.command(f'keys {console} {0xfff^held:03x}')
        # Shorten the final input burst so narrow doors can be approached
        # accurately without stylus input being consumed by map controls.
        ds.run(max(1,min(pulse_frames,int(distance/30))))
        after=player_position(ds,console,slot)
        stalled=stalled+1 if math.hypot(after[0]-px,after[2]-pz)<3 else 0
        if step%30==0:
            print('Waypoint:',(x,z),'position',player_position(ds,console,slot),flush=True)
    snapshot(ds,'waypoint-failed')
    raise ControllerRouteFailure(f'Controller route could not reach {(x,z)}')


def touch_walk_to(ds, x, z, tolerance=30, limit=160, console=0, jump=False, run=False, stop_when=None):
    # Keep the real stylus held through native NET updates. Batched reads
    # observe position and camera together; no scene or position is written.
    slot=ds.read(console,0x020a0f10,1)[0]
    actor=ds.word(console,PLAYER_POINTERS+slot*4)
    initial_level=ds.read(console,0x0209f2f8,1)
    if not 0x02000000<=actor<0x023ff000:
        raise PlayerUnavailable("Analog controller has no live player")
    # The native stick initializes over five synchronized input updates.
    # Video frames do not establish readiness during synchronous WFS stalls.
    # First acknowledge release so a previous map/camera touch cannot carry
    # into this new stick gesture, then wait for its actual initialization.
    control=0x0209f498+24*slot
    touch=0x020a0de8+4*slot
    ds.set_input(console,0xfff)
    for _ in range(180):
        raw,state=ds.readv(console,((touch,4),(control+0x12,3)))
        if not raw[0] and not state[2]:break
        ds.run(1)
    else:
        snapshot(ds,'analog-touch-release-failed')
        raise ControllerRouteFailure('Native touch release was not acknowledged')
    ds.set_input(console,0xfff,(128,96))
    for _ in range(180):
        raw,state,origin=ds.readv(console,((touch,4),(control+0x12,3),(control+0x10,2)))
        if raw[0] and state[2] and not state[0]:break
        ds.run(1)
    else:
        ds.set_input(console,0xfff)
        snapshot(ds,'analog-touch-initialization-failed')
        raise ControllerRouteFailure('Native touch stick did not finish initialization')
    radius=24 if jump or run else (18 if ds.read(console,0x0209f4ae+24*slot,1)[0]==2 else 14)
    try:
        for step in range(limit):
            if stop_when is not None and stop_when():return
            position,yaw_data,level,live_actor=ds.readv(console,(
                (actor+0x5c,12),(0x020a1050,2),(0x0209f2f8,1),
                (PLAYER_POINTERS+slot*4,4)))
            if level!=initial_level or int.from_bytes(live_actor,'little')!=actor:
                snapshot(ds,'analog-route-scene-changed')
                raise ControllerRouteFailure('Analog controller route changed scenes')
            px,_,pz=(v/4096 for v in struct.unpack('<iii',position))
            distance=math.hypot(x-px,z-pz)
            if distance<tolerance:return
            yaw=struct.unpack('<h',yaw_data)[0]
            angle=math.atan2(x-px,z-pz)-yaw*math.tau/65536
            tx=origin[0]+round(radius*math.sin(angle))
            ty=origin[1]+round(radius*math.cos(angle))
            held=(0x800 if jump or run else 0) | (2 if jump and step%8<6 else 0)
            ds.set_input(console,0xfff^held,(tx,ty))
            ds.run(6)
            if step%40==0:
                print('Analog waypoint:',(x,z),'controller',console,'position',(px,pz),flush=True)
        snapshot(ds,'analog-waypoint-failed')
        raise ControllerRouteFailure(f'Analog controller route could not reach {(x,z)}')
    finally:
        ds.set_input(console,0xfff)
        ds.run(30)


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
    # Return across the bridge and along the west lawn before pursuing the
    # rabbit. Chasing it directly from the locked door drops into the moat.
    for point in ((0,1600),(0,3000),(-3000,3000),(-3000,5500)):
        walk_to(ds,*point)
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
        if any(ds.read(i,0x0209f2f8,1)[0]==2 or
               not ds.word(i,PLAYER_POINTERS) for i in range(ds.count)):
            ds.command('keys 0 fff')
            break
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
        else:
            # The old actors can disappear between the level read and this
            # position read, before the replacement scene publishes level 2.
            try:
                held=direction_toward(ds,0,-1200)
            except PlayerUnavailable:
                ds.command('keys 0 fff')
                break
            ds.command(f'keys 0 {0xfff^held:03x}')
            ds.run(12)
    else:
        snapshot(ds,'castle-door-failed')
        raise RuntimeError('The unlocked castle door did not request level 2')
    for step in range(300):
        ready=True
        for console in range(ds.count):
            scene=ds.word(console,0x0209f5c0)
            players=[ds.word(console,PLAYER_POINTERS+4*p) for p in range(ds.count)]
            if (ds.read(console,0x0209f2f8,1)[0]!=2 or
                not 0x02000000<=scene<0x023ff000 or
                ds.read(console,scene+0x13,1)[0]&1 or
                not all(0x02000000<=p<0x023ff000 for p in players)):
                ready=False
                continue
            if any(ds.read(console,p+0x709,1)[0] for p in players):
                ready=False
        if any(ds.read(i,0x0209d660,1)[0] for i in range(ds.count)):
            advance_message(ds)
            continue
        if ready:
            ds.run(180)
            assert_party_synchronized(ds,'castle-entry')
            for console in range(ds.count):
                check_controller_movement(ds,console,'castle-entry')
            snapshot(ds,'castle-entry')
            print(f'Castle interior playable with {ds.count} synchronized controllers.',flush=True)
            return
        if step%20==0:
            print('Castle transition:',[{
                'level':ds.read(i,0x0209f2f8,1)[0],
                'loading':ds.read(i,0x02092778,1)[0],
                'players':sum(bool(ds.word(i,PLAYER_POINTERS+4*p)) for p in range(ds.count)),
                'session':ds.word(i,0x0209fc68),
                'wfsRead':hex(ds.word(i,0x020a1fdc))}
                for i in range(ds.count)],flush=True)
        ds.run(60)
    snapshot(ds,'castle-entry-failed')
    raise RuntimeError('Castle interior did not finish loading on every console')


def check_first_course(ds):
    # Native castle door 5 and exit 0 lead to course 6. Coordinates come
    # from the level's door/exit records; travel uses only controller input.
    # The west landing is 200 units above the lobby. Its collision ramp
    # runs northwest from (-2317, 412) to (-2564, 164); approaching the
    # landing directly from the east hits its vertical side.
    px,py,pz=player_position(ds)
    # Course returns spawn inside the painting room, beyond the lobby door.
    in_painting_room=px<-3100 and -1500<pz<500 and 0<=py<=600
    if not in_painting_room:
        for point in ((-1000,500),(-2300,430),(-2580,150)):
            walk_to(ds,*point)
        # The doorway is narrow. The general 100-unit waypoint tolerance can
        # accept its north edge and make the following diagonal hit the wall.
        # The KCL opening is centered near z=-825. Aim through its center;
        # z=-700 can meet the jamb with a 45-degree D-pad heading.
        # Input has native wireless latency. If the approach already carries us
        # through the opening, continue into the room instead of backtracking to
        # an obsolete approach point and orbiting the door.
        through_door=lambda: player_position(ds)[0]<-3100
        walk_to(ds,-2850,-825,tolerance=45,limit=600,pulse_frames=2,stop_when=through_door)
        walk_to(ds,-3350,-825,tolerance=60,limit=600,pulse_frames=2,stop_when=through_door)
    walk_to(ds,-4500,-450)
    previous_scene_state=None
    for step in range(300):
        if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
            snapshot(ds,'first-course-connection-failed')
            raise RuntimeError('Native wireless session failed during the first course transition')
        levels=[ds.read(i,0x0209f2f8,1)[0] for i in range(ds.count)]
        scenes=[ds.word(i,0x0209f5c0) for i in range(ds.count)]
        ids=[int.from_bytes(ds.read(i,s+0xc,2),'little')
             if 0x02000000<=s<0x023ff000 else 0 for i,s in enumerate(scenes)]
        scene_state=(tuple(levels),tuple(ids))
        if scene_state!=previous_scene_state or step%20==0:
            print('First course transition:',levels,ids,flush=True)
            previous_scene_state=scene_state
        if 4 in ids: # Star selection follows the host's controller.
            advance_message(ds)
            continue
        ready=all(level==6 and actor==3 for level,actor in zip(levels,ids))
        if ready:
            for console,scene in enumerate(scenes):
                players=[ds.word(console,PLAYER_POINTERS+4*p) for p in range(ds.count)]
                if (ds.read(console,scene+0x13,1)[0]&1 or
                    not all(0x02000000<=p<0x023ff000 for p in players)):
                    ready=False
                    break
                if any(ds.read(console,p+0x709,1)[0] for p in players):
                    ready=False
        if ready:
            ds.command('keys 0 fff')
            if os.environ.get('COOP_CAPTURE_COURSE_ARRIVAL'):
                snapshot(ds,'first-course-initial-arrival')
            finish_messages(ds)
            assert_party_synchronized(ds,'first-course-arrival')
            for console in range(ds.count):
                check_controller_movement(ds,console,'first-course')
            snapshot(ds,'first-course')
            print(f'Bob-omb Battlefield playable with {ds.count} synchronized controllers.',flush=True)
            return
        try:
            if levels[0]==2 and ids[0]==3:
                held=direction_toward(ds,-5300,-450)|0x800
                if step%4==0:
                    held|=2 # Jump into the painting above the floor.
                ds.command(f'keys 0 {0xfff^held:03x}')
            else:
                ds.command('keys 0 fff')
        except PlayerUnavailable:
            ds.command('keys 0 fff')
        ds.run(60)
    snapshot(ds,'first-course-failed')
    raise RuntimeError('First course did not become playable on every console')


def check_course_return(ds):
    """Exit through the host's actual pause menu and check the reloaded party."""
    # Await the native menu cooldown and echoed press/release, as in the
    # repeated pause check. A fixed-duration pulse can fall inside a cold
    # synchronous asset read and disappear before the next input exchange.
    from diagnostic_stage import toggle_pause
    if any(ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)):
        raise RuntimeError('Course return check must start in active gameplay')
    toggle_pause(ds,0)
    if not all(ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)):
        snapshot(ds,'course-return-pause-failed')
        raise RuntimeError('Course pause did not open on every console')
    # Retain a quiescent world checkpoint as well as the player checks. These
    # dumps allow enemy positions/timers to be compared without mistaking
    # ordinary movement between serial console snapshots for a divergence.
    snapshot(ds,'course-return-pause')
    check_paused_course_enemies(ds,'course-return-pause')
    # PS_Update case3 ignores touch edges while its opening cooldown is
    # nonzero. Pause flags become true earlier; wait for the actual menu on
    # every replica, then hold the physical touch until its action is accepted.
    for _ in range(180):
        if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
            raise RuntimeError('Wireless session failed while opening course pause')
        ready=True
        for console in range(ds.count):
            state,draw_state,cooldown,animation=ds.readv(console,(
                (0x0209f1ec,1),(0x0209f248,1),(0x0209f300,2),(0x0209f22c,1)))
            if state!=b'\x03' or draw_state!=b'\x03' or any(cooldown) or any(animation):
                ready=False
        if ready:break
        ds.run(1)
    else:
        snapshot(ds,'course-return-menu-not-ready')
        raise RuntimeError('Native course pause menu did not finish opening')
    ds.set_input(0,0xfff)
    for _ in range(90):
        if not ds.read(0,0x020a0de8,1)[0]:break
        ds.run(1)
    else:raise RuntimeError('Host touch release was not acknowledged before course exit')
    # Fourth row: y144..175. Do not substitute a timed touch pulse.
    ds.set_input(0,0xfff,(128,160))
    try:
        for _ in range(180):
            if ds.read(0,0x0209f1ec,1)!=b'\x03':break
            ds.run(1)
        else:
            snapshot(ds,'course-return-menu-touch-not-accepted')
            raise RuntimeError('Native course pause did not accept the exit touch')
    finally:
        ds.set_input(0,0xfff)
    for step in range(300):
        if any(ds.word(i,0x0209fc68)==6 for i in range(ds.count)):
            snapshot(ds,'course-return-connection-failed')
            raise RuntimeError('Native wireless session failed during course return')
        ready=True
        for console in range(ds.count):
            scene=ds.word(console,0x0209f5c0)
            if (ds.read(console,0x0209f2f8,1)[0]!=2 or
                not 0x02000000<=scene<0x023ff000 or
                int.from_bytes(ds.read(console,scene+0xc,2),'little')!=3 or
                ds.read(console,scene+0x13,1)[0]&1):
                ready=False
                break
            players=[ds.word(console,PLAYER_POINTERS+4*p) for p in range(ds.count)]
            if (not all(0x02000000<=p<0x023ff000 for p in players) or
                any(ds.read(console,p+0x709,1)[0] for p in players)):
                ready=False
                break
        if ready:
            finish_messages(ds)
            assert_party_synchronized(ds,'course-return-arrival')
            for console in range(ds.count):
                check_controller_movement(ds,console,'course-return')
            snapshot(ds,'course-return')
            print(f'Course return playable with {ds.count} synchronized controllers.',flush=True)
            return
        ds.run(60)
    snapshot(ds,'course-return-failed')
    raise RuntimeError('Course exit did not return every console to active castle gameplay')


def check_paused_course_enemies(ds, checkpoint):
    """Compare Goomba simulation fields in already captured, paused RAM."""
    parties=[]
    for console in range(ds.count):
        ram=(ds.output/f'{checkpoint}-{console}.ram').read_bytes()
        def word(address):
            if not 0x02000000<=address<=0x02000000+len(ram)-4:
                raise RuntimeError('Invalid actor list address in paused checkpoint')
            return struct.unpack_from('<I',ram,address-0x02000000)[0]
        node=word(0x0209b468)
        seen=set()
        enemies=[]
        while node:
            if node in seen or len(seen)>=4096:
                raise RuntimeError('Invalid actor list in paused checkpoint')
            seen.add(node)
            actor=word(node+8)
            kind=word(actor+0xc)&0xffff
            if kind in (200,201,202):
                offset=actor-0x02000000
                enemies.append({
                    'kind':kind,
                    'home':struct.unpack_from('<3i',ram,offset+0x41c),
                    'position':struct.unpack_from('<3i',ram,offset+0x5c),
                    'angle':struct.unpack_from('<3h',ram,offset+0x8c),
                    'state':word(actor+0x434),
                    'timers':ram[offset+0x450:offset+0x45e].hex()})
            node=word(node+4)
        enemies.sort(key=lambda enemy:(enemy['kind'],enemy['home']))
        if not enemies:
            raise RuntimeError('No Goombas found in the actual course checkpoint')
        parties.append(enemies)
    (ds.output/f'{checkpoint}-enemies.json').write_text(json.dumps(parties,indent=2)+'\n')
    if any(party!=parties[0] for party in parties[1:]):
        raise RuntimeError('Goomba positions, states, or timers diverged in the paused course')
    print(f'{len(parties[0])} Goomba simulation states match across {ds.count} consoles.',flush=True)
