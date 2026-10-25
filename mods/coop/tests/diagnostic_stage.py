"""Later-stage checks for explicitly marked diagnostic cartridges.

The compiled entry point chooses the stage before native loading. These are
stage compatibility checks, not evidence that its access/unlocks were earned.
All live emulator control is physical input; observations are read-only.
"""
import json
import struct

from campaign import (advance_message, assert_party_synchronized, check_controller_movement, finish_messages,
                      snapshot, wait_controller_buttons, ControllerRouteFailure)


def check_characters(ds):
    """Record the native character fixture when bypassing castle startup.

    Direct course entry retains the native Mario/Luigi/Wario/Yoshi slot array;
    ordinary castle startup creates the four Yoshis tested by campaign smoke.
    """
    for attempt in range(6):
        parties=[]
        for console in range(ds.count):
            actors=[ds.word(console,0x0209f394+4*slot) for slot in range(ds.count)]
            fields=ds.readv(console,tuple(field for actor in actors
                                         for field in ((actor+8,4),(actor+0x6d8,1))))
            characters=[]
            for slot in range(ds.count):
                character=int.from_bytes(fields[slot*2],'little')
                if character>3 or fields[slot*2+1][0]!=slot:
                    raise RuntimeError('Invalid native player character in diagnostic fixture')
                characters.append(character)
            parties.append(characters)
        if all(party==parties[0] for party in parties[1:]):return parties[0]
        # A real cap loss changes a native character during gameplay. Reads
        # from different emulated frames can straddle that transformation.
        if attempt<5:ds.run(6)
    snapshot(ds,'diagnostic-characters-differ')
    raise RuntimeError('Diagnostic native characters persistently differ between consoles')


def heap_status(ds):
    """Read native expanding-heap free lists while the party is paused."""
    module=getattr(ds,'runtime_module',None)
    if not module or not module.get('particlePoolFallback'):return None
    result=[]
    for console in range(ds.count):
        base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
        state={'console':console,'particleFallbacks':ds.word(
            console,base+module['diagnosticOffsets']['coopParticleFallbacks'])}
        if module.get('streamUncachedNarcMembers'):
            state['streamedNarcReads']=ds.word(console,base+module['diagnosticOffsets']['coopStreamedNarcReads'])
        if module.get('streamCompressedDiskFiles'):
            state['streamedLzReads']=ds.word(console,base+module['diagnosticOffsets']['coopStreamedLzReads'])
        if module.get('evictCommonStageSourceCache'):
            state['stageCacheEvictions']=ds.word(console,base+module['diagnosticOffsets']['coopStageCacheEvictions'])
        if module.get('particleSplitFallback'):
            for key,symbol in (('particleSplitFallbacks','coopParticleSplitFallbacks'),
                               ('particleSegments','coopParticleSegmentCount')):
                state[key]=ds.word(console,base+module['diagnosticOffsets'][symbol])
        if module.get('sharedResourceFallback'):
            for key,symbol in (('resourceFallbacks','coopResourceFallbacks'),
                               ('resourceFallbacksLive','coopResourceFallbacksLive'),
                               ('resourceFallbacksPeak','coopResourceFallbacksPeak')):
                state[key]=ds.word(console,base+module['diagnosticOffsets'][symbol])
        for name,address in (('root',0x020a0e9c),('game',0x020a0eac)):
            heap=ds.word(console,address)
            fields=struct.unpack('<6I',ds.read(console,heap,24))
            allocator=fields[5]
            if ds.word(console,allocator)!=0x45585048:
                raise RuntimeError('Expected a native expanding heap for memory observation')
            node=ds.word(console,allocator+0x24)
            seen=set()
            sizes=[]
            while node:
                if not 0x02000000<=node<=0x023ffff0 or node in seen or len(seen)>=4096:
                    raise RuntimeError('Invalid native heap free list during paused observation')
                seen.add(node)
                _,size,_,node=struct.unpack('<4I',ds.read(console,node,16))
                sizes.append(size)
            state[name]={'bytes':fields[2],'freeBytes':sum(sizes),
                         'largestFreeBlock':max(sizes,default=0),'freeBlocks':len(sizes)}
        result.append(state)
    return result


def check_connected_party(ds):
    states=[{'console':console,'net':ds.word(console,0x0209fc68),
             'radio':ds.word(console,0x020a0f94)} for console in range(ds.count)]
    if any(state['net']!=4 or state['radio']!=(3 if state['console']==0 else 4) for state in states):
        snapshot(ds,'diagnostic-party-disconnected')
        raise RuntimeError(f'Diagnostic party is no longer in wireless gameplay: {states}')


def check_living_party(ds):
    for console in range(ds.count):
        health=struct.unpack('<'+'h'*ds.count,ds.read(console,0x02092144,ds.count*2))
        if any(value<=0 for value in health):
            snapshot(ds,'diagnostic-controller-died')
            raise ControllerRouteFailure(f'Diagnostic input route killed a player: {health}')


def toggle_pause(ds, console=0):
    """Press START after the native menu/input cooldown, using real input.

    A resumed menu temporarily rejects another START. Observe that state
    instead of assuming an elapsed delay is sufficient for the next press.
    """
    def paused():return [ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)]
    expected=not bool(paused()[0])
    check_connected_party(ds)
    if not console:
        for _ in range(180):
            ready=True
            for peer in range(ds.count):
                if (ds.read(peer,0x0209f300,2)!=b'\0\0' or
                        ds.read(peer,0x0209f22c,1)!=b'\0' or
                        (not expected and ds.read(peer,0x0209f248,1)[0] not in (1,3,11))):
                    ready=False
            if ready:break
            check_connected_party(ds)
            ds.run(1)
        else:raise RuntimeError('Native pause menu/input cooldown did not finish')
    ds.set_input(console,0xff7)
    wait_controller_buttons(ds,console,8,held=True)
    ds.set_input(console,0xfff)
    wait_controller_buttons(ds,console,8)
    if console:
        ds.run(12)
        return
    for _ in range(180):
        check_connected_party(ds)
        if all(bool(value)==expected for value in paused()):return
        ds.run(1)
    snapshot(ds,'diagnostic-pause-state-failed')
    raise RuntimeError('Host START did not change the shared pause state')


def check_stage(ds, level):
    resume_stage(ds)
    # Some native entrance-0 records are star-return arrivals and open the
    # level-clear menu. Choose Continue without saving this synthetic entry.
    finish_messages(ds,level_clear_choice=(128,136))
    actual=[ds.read(i,0x0209f2f8,1)[0] for i in range(ds.count)]
    if actual!=[level]*ds.count:
        snapshot(ds,'diagnostic-stage-arrival-transition')
        raise ControllerRouteFailure(
            f'Native arrival left stage {level} before controller checks: {actual}')
    check_connected_party(ds)
    characters=check_characters(ds)
    assert_party_synchronized(ds,'diagnostic-stage-entry')
    check_living_party(ds)
    movement=[]
    for console in range(ds.count):
        movement.append(check_controller_movement(ds,console,'diagnostic-stage',
                                                  press_frames=8,release_frames=12))
        check_living_party(ds)
        if any(ds.read(i,0x0209f2f8,1)!=bytes([level]) for i in range(ds.count)):
            snapshot(ds,'diagnostic-stage-unexpected-transition')
            raise RuntimeError('Diagnostic movement left the selected stage')
    def paused():return [ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)]
    for console in range(1,ds.count):
        toggle_pause(ds,console)
        if any(paused()):raise RuntimeError('Guest changed shared pause in a diagnostic stage')
    toggle_pause(ds,0)
    if not all(paused()):raise RuntimeError('Host pause did not reach the diagnostic party')
    heaps=heap_status(ds)
    toggle_pause(ds,0)
    if any(paused()):raise RuntimeError('Host resume did not reach the diagnostic party')
    check_connected_party(ds)
    assert_party_synchronized(ds,'diagnostic-stage-resume')
    check_living_party(ds)
    snapshot(ds,'diagnostic-stage-passed')
    (ds.output/'diagnostic-stage.json').write_text(json.dumps({
        'level':level,'consoles':ds.count,'characters':characters,'movement':movement,
        'heaps':heaps,
        'sharedPausePassed':True,'levelClearChoice':'continue-without-saving',
        'campaignProgressionVerified':False},indent=2)+'\n')
    print(f'Diagnostic native stage {level}: {ds.count} controls and shared pause passed.',flush=True)


def resume_stage(ds):
    states=[bool(ds.read(i,0x0209f2c4,1)[0]) for i in range(ds.count)]
    if len(set(states))!=1:raise RuntimeError('Party pause flags differ before a diagnostic check')
    if states[0]:
        toggle_pause(ds,0)


def next_stage(ds):
    """Request the next stage through a diagnostic build's real host chord."""
    current=ds.read(0,0x0209f2f8,1)[0]
    expected=current+1
    if expected==41:expected+=1
    if expected>=52:expected=1
    resume_stage(ds)
    chord=getattr(ds,'runtime_module',{}).get('diagnosticStageChord',0x304)
    ds.set_input(0,0xfff^chord)
    ds.run(24)
    ds.set_input(0,0xfff)
    for attempt in range(360):
        exceptions=[i for i in range(ds.count) if ds.word(i,0x0209cddc)]
        if exceptions:
            snapshot(ds,'diagnostic-transition-native-exception')
            raise RuntimeError(f'Native exception during stage transition on consoles {exceptions}')
        crashed=[i for i in range(ds.count) if ds.read(i,0x0209d4d8,1)!=b'\0']
        if crashed:
            snapshot(ds,'diagnostic-transition-native-crash')
            raise RuntimeError(f'Native Crash() during stage transition on consoles {crashed}')
        ready=True
        arrived=[]
        for console in range(ds.count):
            if ds.word(console,0x0209fc68) in (0,6):
                snapshot(ds,'diagnostic-transition-connection-failed')
                raise RuntimeError('Native wireless failed during a diagnostic stage transition')
            scene=ds.word(console,0x0209f5c0)
            if not 0x02000000<=scene<0x023ff000:
                ready=False
                continue
            actor=int.from_bytes(ds.read(console,scene+0xc,2),'little')
            if not console and actor==4:advance_message(ds)
            if (actor!=3 or ds.read(console,scene+0x13,1)[0]&1 or
                    ds.read(console,0x0209f2f8,1)[0]!=expected or
                    ds.read(console,0x02092778,1)[0] or
                    any(not 0x02000000<=ds.word(console,0x0209f394+4*s)<0x023ff000
                        for s in range(ds.count))):
                ready=False
            if (actor==3 and not ds.read(console,scene+0x13,1)[0]&1 and
                    not ds.read(console,0x02092778,1)[0] and
                    all(0x02000000<=ds.word(console,0x0209f394+4*s)<0x023ff000
                        for s in range(ds.count))):
                arrived.append(ds.read(console,0x0209f2f8,1)[0])
        if ready:return expected
        if len(arrived)==ds.count and len(set(arrived))==1 and arrived[0] not in (current,expected):
            snapshot(ds,'diagnostic-transition-unexpected-arrival')
            raise ControllerRouteFailure(
                f'Native arrival reached stage {arrived[0]} while requesting {expected} from {current}')
        ds.run(30)
    snapshot(ds,'diagnostic-transition-failed')
    raise RuntimeError(f'Diagnostic host chord did not enter stage {expected}')


def check_cycle(ds, count):
    root=ds.output
    report={'campaignProgressionVerified':False,'consoles':ds.count,
            'physicalInputStageRequests':True,'stages':[],'status':'running'}
    def save():
        (root/'diagnostic-cycle.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        for step in range(count):
            ds.output=root/f'cycle-{step+1:02d}'
            ds.output.mkdir(parents=True,exist_ok=True)
            level=next_stage(ds)
            item={'level':level,'status':'running'}
            report['stages'].append(item)
            save()
            check_stage(ds,level)
            item['status']='passed'
            save()
    except Exception as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}')
        if report['stages'] and report['stages'][-1]['status']=='running':
            report['stages'][-1]['status']='failed'
        save()
        raise
    else:
        report['status']='passed'
        save()
    finally:
        ds.output=root
