"""Later-stage checks for explicitly marked diagnostic cartridges.

The compiled entry point chooses the stage before native loading. These are
stage compatibility checks, not evidence that its access/unlocks were earned.
All live emulator control is physical input; observations are read-only.
"""
import json
import struct

from campaign import (advance_message, assert_party_synchronized, check_controller_movement, finish_messages,
                      snapshot)


def check_characters(ds):
    """Record the native character fixture when bypassing castle startup.

    Direct course entry retains the native Mario/Luigi/Wario/Yoshi slot array;
    ordinary castle startup creates the four Yoshis tested by campaign smoke.
    """
    parties=[]
    for console in range(ds.count):
        characters=[]
        for slot in range(ds.count):
            actor=ds.word(console,0x0209f394+4*slot)
            character=ds.word(console,actor+8)
            if character>3 or ds.read(console,actor+0x6d8,1)[0]!=slot:
                raise RuntimeError('Invalid native player character in diagnostic fixture')
            characters.append(character)
        parties.append(characters)
    if any(party!=parties[0] for party in parties[1:]):
        raise RuntimeError('Diagnostic native characters differ between consoles')
    return parties[0]


def heap_status(ds):
    """Read native expanding-heap free lists while the party is paused."""
    module=getattr(ds,'runtime_module',None)
    if not module or not module.get('particlePoolFallback'):return None
    result=[]
    for console in range(ds.count):
        base=ds.word(console,0x02004184)-int(module['entryOffset'],16)
        state={'console':console,'particleFallbacks':ds.word(
            console,base+module['diagnosticOffsets']['coopParticleFallbacks'])}
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


def check_stage(ds, level):
    resume_stage(ds)
    # Some native entrance-0 records are star-return arrivals and open the
    # level-clear menu. Choose Continue without saving this synthetic entry.
    finish_messages(ds,level_clear_choice=(128,136))
    characters=check_characters(ds)
    assert_party_synchronized(ds,'diagnostic-stage-entry')
    movement=[]
    for console in range(ds.count):
        movement.append(check_controller_movement(ds,console,'diagnostic-stage'))
        if any(ds.read(i,0x0209f2f8,1)!=bytes([level]) for i in range(ds.count)):
            snapshot(ds,'diagnostic-stage-unexpected-transition')
            raise RuntimeError('Diagnostic movement left the selected stage')
    def paused():return [ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)]
    def start(console):
        ds.set_input(console,0xff7)
        ds.run(18)
        ds.set_input(console,0xfff)
        ds.run(90)
    for console in range(1,ds.count):
        start(console)
        if any(paused()):raise RuntimeError('Guest changed shared pause in a diagnostic stage')
    start(0)
    if not all(paused()):raise RuntimeError('Host pause did not reach the diagnostic party')
    heaps=heap_status(ds)
    start(0)
    if any(paused()):raise RuntimeError('Host resume did not reach the diagnostic party')
    assert_party_synchronized(ds,'diagnostic-stage-resume')
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
        ds.set_input(0,0xff7)
        ds.run(24)
        ds.set_input(0,0xfff)
        ds.run(90)
        if any(ds.read(i,0x0209f2c4,1)[0] for i in range(ds.count)):
            raise RuntimeError('Host could not resume the retained diagnostic party')


def next_stage(ds):
    """Request the next stage through a diagnostic build's real host chord."""
    current=ds.read(0,0x0209f2f8,1)[0]
    expected=current+1
    if expected==41:expected+=1
    if expected>=52:expected=1
    if ds.read(0,0x0209f2c4,1)[0]:
        ds.set_input(0,0xff7)
        ds.run(24)
        ds.set_input(0,0xfff)
        ds.run(90)
    ds.set_input(0,0xfff^0x304)
    ds.run(24)
    ds.set_input(0,0xfff)
    for attempt in range(360):
        ready=True
        for console in range(ds.count):
            if ds.word(console,0x0209fc68)==6:
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
        if ready:return expected
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
