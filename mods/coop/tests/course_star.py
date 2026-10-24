"""Collect the real Chain Chomp star, save it and regain castle control."""
import json
import math
import struct

from campaign import (ControllerRouteFailure, PLAYER_POINTERS, assert_party_synchronized, check_controller_movement, direction_toward,
                      player_position, snapshot, touch_walk_to, wait_controller_buttons, walk_to)
from course_death import _castle_ready, walk_to_chain_field


def check_repeated_jumps(ds, controller):
    """Prove repeated physical jump edges reach the selected guest."""
    slot=ds.read(controller,0x020a0f10,1)[0]
    actor=ds.word(controller,PLAYER_POINTERS+4*slot)
    jumps=[]
    for attempt in range(3):
        ds.set_input(controller,0xfff)
        wait_controller_buttons(ds,controller,0x102)
        before=player_position(ds,controller,slot)
        ds.set_input(controller,0xffd)
        wait_controller_buttons(ds,controller,2,held=True)
        for _ in range(40):
            state=ds.word(controller,actor+0x370)
            if 0x02000000<=state<=0x023ffff4 and ds.word(controller,state+8)==0x020e2118:
                break
            ds.run(1)
        else:
            snapshot(ds,'repeated-jump-failed')
            raise RuntimeError('An acknowledged jump press did not enter the native jump state')
        ds.run(12)
        airborne=player_position(ds,controller,slot)
        ds.set_input(controller,0xfff)
        wait_controller_buttons(ds,controller,2)
        ds.run(90)
        if airborne[1]<=before[1]+64:
            raise RuntimeError('The native jump did not rise above its initial floor')
        jumps.append({'before':before,'airborne':airborne})
    assert_party_synchronized(ds,'repeated-guest-jumps')
    (ds.output/'repeated-guest-jumps.json').write_text(json.dumps({
        'controller':controller,'slot':slot,'jumps':jumps,'nativeEdgesObserved':True},indent=2)+'\n')


def _find_stump(ds, controller=0):
    path=ds.output/'star-actor-scan.ram'
    ds.command(f'dump {controller} {path}')
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


def _check_chain_star(ds, controller=0):
    if any(ds.read(i,0x0209f2f8,1)!=b'\x06' for i in range(ds.count)):
        raise RuntimeError('Star check must start in Bob-omb Battlefield')
    before=ds.read(0,0x0209cab4,30)
    if before[0]&0x80:raise RuntimeError('This private adventure already contains the test star')
    if getattr(ds,'shared_course_coins',False) and ds.read(0,0x0209f358,2)==b'\0\0':
        # A real death/exit resets course coins. Re-establish the actual pickup
        # witness on a navigation retry instead of inheriting an earlier level.
        from course_coins import check_shared_coin_pickup
        check_shared_coin_pickup(ds,(controller+1)%ds.count)
    walk_to_chain_field(ds,controller)
    # Approach the post from the south. The head starts north of it; the
    # northern route put this controller directly in its lunging corridor.
    walk_to(ds,1400,3000,tolerance=60,pulse_frames=6,console=controller)
    touch_walk_to(ds,400,3000,tolerance=80,limit=400,run=True,
                  jump=False,console=controller)
    check_chain_post(ds,before,controller)


def check_chain_post(ds, before=None, controller=0):
    """Finish the real post/star/save checkpoint from the northern approach."""
    if not 0<=controller<ds.count:raise ValueError("Star controller is not connected")
    slot=ds.read(controller,0x020a0f10,1)[0]
    if ds.read(controller,0x0209f2f8,1)!=b'\x06':
        raise RuntimeError('The post controller must start in Bob-omb Battlefield')
    if before is None:before=ds.read(0,0x0209cab4,30)
    if before[0]&0x80:raise RuntimeError('This adventure already contains the test star')
    stump=_find_stump(ds,controller)
    # Initialize the stick outside the Chain Chomp's reach, then jump toward
    # the post. Standing next to it during touch initialization invites hits.
    # Eight-way D-pad directions can skim the narrow post. Use the game's
    # normal analog stylus control for the final alignment instead.
    ds.command(f'keys {controller} fff')
    ds.command(f'touch {controller} 128 96')
    ds.run(24)
    wait_controller_buttons(ds,controller,0x102)
    origin=ds.read(controller,0x0209f4a8+24*slot,2)
    actor=ds.word(controller,PLAYER_POINTERS+4*slot)
    # State descriptors are resident for this overlay. Their function pointers
    # were already captured in the read-only actor scan, so avoid repeatedly
    # querying them while the live game continues between driver commands.
    state_image=(ds.output/'star-actor-scan.ram').read_bytes()
    def steer(active):
        if not active:return tuple(origin)
        px,_,pz=p
        angle=math.atan2(400-px,1900-pz)-yaw*math.tau/65536
        radius=24 if (400-px)**2+(1900-pz)**2>150**2 else 14
        return (origin[0]+round(radius*math.sin(angle)),origin[1]+round(radius*math.cos(angle)))
    def drive(held,active):
        ds.set_input(controller,0xfff^(held|(0x800 if active else 0)),steer(active))
    completed=False
    previous_health=None
    shared_coin_witness=False
    for step in range(2400):
        fields=ds.readv(controller,((stump+0x31e,1),(0x0209fc68,4),
            (0x0209f2f8,1),(PLAYER_POINTERS+4*slot,4),(actor+0x5c,12),
            (actor+0x370,4),(actor+0x6e3,1),(stump+0x60,4),
            (0x020a1050,2),(0x02092144+2*slot,2),(0x020a1154,4),(0x0209f358,8)))
        remaining=fields[0][0]
        if int.from_bytes(fields[1],'little')==6:
            snapshot(ds,'star-connection-failed')
            raise RuntimeError('Wireless connection failed during the star route')
        if fields[2]!=b'\x06' or int.from_bytes(fields[3],'little')!=actor:
            snapshot(ds,'star-route-died')
            raise ControllerRouteFailure('Controller route died before releasing the Chain Chomp')
        if not remaining:
            completed=True
            break
        p=tuple(v/4096 for v in struct.unpack('<iii',fields[4]))
        state=int.from_bytes(fields[5],'little')
        if not 0x02000000<=state<=0x023ffff4:
            raise RuntimeError('Invalid player state during star controller route')
        main=struct.unpack_from('<I',state_image,state+8-0x02000000)[0]
        post_y=struct.unpack('<i',fields[7])[0]/4096
        yaw=struct.unpack('<h',fields[8])[0]
        health=int.from_bytes(fields[9],'little')
        tick=int.from_bytes(fields[10],'little')
        coins=struct.unpack('<4h',fields[11])
        if coins[0]>0 and len(set(coins))==1:shared_coin_witness=True
        distance=((p[0]-400)**2+(p[2]-1900)**2)**.5
        if health!=previous_health or step%120==0:
            print('Chain Chomp star:',step,'tick',tick,'post hits remaining',remaining,
                  'health',health,'state',hex(main),p,flush=True)
            previous_health=health
        if main==0x020dd9f8: # Ground pound, including its landing animation.
            if fields[6]==b'\xff':
                drive(0,True)
                ds.run(1)
                drive(0,False)
                wait_controller_buttons(ds,controller,0x102)
            else:
                drive(0,False)
                ds.run(1)
        elif main==0x020e2118: # Jump: pound only above the actual narrow post.
            held=0x100 if distance<45 and p[1]>post_y+230 else 2
            drive(held,distance>35)
            ds.run(1)
        else:
            drive(2,distance>35)
            ds.run(1)
            wait_controller_buttons(ds,controller,2,held=True)
            if step%12==0:
                drive(0,False)
                wait_controller_buttons(ds,controller,0x102)
    ds.command(f'keys {controller} fff')
    ds.command(f'release {controller}')
    ds.run(180)
    snapshot(ds,'star-post-release')
    if not completed:raise ControllerRouteFailure('Controller route did not finish pounding the stump')
    if getattr(ds,'shared_course_coins',False) and not shared_coin_witness:
        raise RuntimeError('No actual shared coin pickup was observed during the star checkpoint')
    for step in range(300):
        if ds.read(0,0x0209cab4,30)!=before:break
        if ds.read(controller,0x0209f2f8,1)!=b'\x06':
            snapshot(ds,'star-approach-died')
            raise ControllerRouteFailure('Controller died before collecting the released star')
        held=direction_toward(ds,1529,264,controller)|0x800
        if step%8<6:held|=2
        ds.command(f'keys {controller} {0xfff^held:03x}')
        ds.run(12)
    ds.command(f'keys {controller} fff')
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
    movement=[check_controller_movement(ds,i,'star-castle-return') for i in range(ds.count)]
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
        'consoles':ds.count,'controller':controller,'playerSlot':slot,'before':before.hex(),'after':after.hex(),
        'starPersisted':True,'castleControlRestored':True,'movement':movement,'sharedCoinPickupWitness':shared_coin_witness},indent=2)+'\n')
    print(f'Real Chain Chomp star collected, shared and saved with {ds.count} consoles.',flush=True)


def check_chain_star(ds, controller=0):
    """Retry navigation misses through actual exits; retain every attempt.

    Network, save and synchronization failures always fail immediately. A bot
    falling off a ramp or dying is recovered using normal game transitions,
    never a savestate or writes to emulated memory.
    """
    from campaign import check_first_course, check_course_return, finish_messages
    if not 0<=controller<ds.count:raise ValueError("Star controller is not connected")
    slot=ds.read(controller,0x020a0f10,1)[0]
    root=ds.output
    attempts=[]
    try:
        for attempt in range(1,4):
            ds.output=root/f'star-route-{attempt}'
            ds.output.mkdir(parents=True,exist_ok=True)
            try:
                _check_chain_star(ds,controller)
            except ControllerRouteFailure as error:
                attempts.append({'attempt':attempt,'status':'controller-route-failed','error':str(error)})
                (root/'course-star-route-attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
                if attempt==3:raise
                ds.set_input(controller,0xfff)
                ds.run(180)
                level=ds.read(0,0x0209f2f8,1)[0]
                health=int.from_bytes(ds.read(controller,0x02092144+2*slot,2),'little')
                if level==6 and health:
                    check_course_return(ds)
                else:
                    for _ in range(120):
                        if all(_castle_ready(ds,i) for i in range(ds.count)):break
                        ds.run(30)
                    else:
                        snapshot(ds,'star-route-death-recovery-failed')
                        raise RuntimeError('A driver death did not restore castle gameplay') from error
                    finish_messages(ds)
                    assert_party_synchronized(ds,'star-route-death-recovery')
                print('Retrying star input route through the real castle painting:',attempt+1,flush=True)
                if player_position(ds)[0]<-3100:
                    walk_to(ds,-4500,-450)
                check_first_course(ds)
            else:
                attempts.append({'attempt':attempt,'status':'passed'})
                (root/'course-star-route-attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
                for filename in ('course-star.json','earned-star.sav'):
                    (root/filename).write_bytes((ds.output/filename).read_bytes())
                return
    finally:
        ds.output=root
