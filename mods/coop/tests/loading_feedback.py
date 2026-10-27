"""Read-only rendered loading-text and animation observations during live loads."""
import json
import os
import struct
from pathlib import Path

LETTERS=((16,16,16,16,31),(14,17,17,17,14),(14,17,31,17,17),
         (30,17,17,17,30),(31,4,4,4,31),(17,25,21,19,17),(14,16,23,17,15))
SPINNERS=((4,4,4,4,4),(1,2,4,8,16),(0,0,31,0,0),(16,8,4,2,1))


def rendered_glyphs(path):
    header,widthheight,maximum,pixels=Path(path).read_bytes().split(b'\n',3)
    if (header,widthheight,maximum)!=(b'P6',b'256 384',b'255'):
        raise ValueError('Unexpected frontend screenshot format')
    if len(pixels)!=256*384*3:raise ValueError('Incomplete screenshot')
    def match(glyph,x0,y0):
        passed=total=0
        def white(x,y):return 1<=x<6 and 1<=y<6 and glyph[y-1]&(1<<(5-x))
        for y in range(8):
            for x in range(8):
                light=bool(white(x,y))
                dark=not light and any(white(a,b) for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
                if not light and not dark:continue
                rgb=pixels[((y0+y)*256+x0+x)*3:((y0+y)*256+x0+x)*3+3]
                total+=1;passed+=all(c>=225 for c in rgb) if light else all(c<=30 for c in rgb)
        return passed/total
    for screen in (0,1):
        y=screen*192+88
        letter_scores=[match(g,96+i*8,y) for i,g in enumerate(LETTERS)]
        if min(letter_scores)<0.95:continue
        scores=[match(g,152,y) for g in SPINNERS];phase=max(range(4),key=scores.__getitem__)
        return {'textVisible':True,'physicalScreen':screen,'minimumLetterMatch':min(letter_scores),
                'spinnerPhase':phase if scores[phase]>=0.95 else None,'spinnerMatch':max(scores)}
    return {'textVisible':False,'spinnerPhase':None}


class LoadingFeedbackCapture:
    def __init__(self,ds,label):
        self.ds=ds;self.meta=ds.runtime_module['experimentalLoadingScreen']
        self.path=ds.output/('loading-feedback-'+label+'.json')
        self.report={'readOnly':True,'registersOrPacketsModified':False,'consoles':[[] for _ in range(ds.count)]}
        self.probes=[0]*ds.count
        self.save()

    def save(self):self.path.write_text(json.dumps(self.report,indent=2)+'\n')

    def sample(self):
        for c in range(self.ds.count):
            rows=self.report['consoles'][c]
            if len({x.get('spinnerPhase') for x in rows if x.get('textVisible') and x.get('spinnerPhase') is not None})>=2:
                continue
            if self.probes[c]>=8:continue
            for repeat in range(2):
                module=self.ds.runtime_module
                entry=self.ds.word(c,0x02004184)
                base=entry-int(module['entryOffset'],16)
                if not 0x02000000<=base<0x02400000-module['bodyBytes']:continue
                values=self.ds.readv(c,((base+self.meta['activeOffset'],4),
                    (base+self.meta['statsOffset'],28),(0x023ffc3c,4)))
                if int.from_bytes(values[0],'little')!=1:break
                stats=dict(zip(self.meta['fields'],struct.unpack('<7I',values[1])))
                hardware={}
                if 'hardwareOffset' in self.meta:
                    count=len(self.meta['hardwareFields'])
                    raw=self.ds.read(c,base+self.meta['hardwareOffset'],count*4)
                    hardware=dict(zip(self.meta['hardwareFields'],struct.unpack('<'+str(count)+'I',raw)))
                if stats['ownershipFaults']:raise RuntimeError('Loading UI lost its native VRAM ownership')
                number=self.probes[c];self.probes[c]+=1
                filename=self.path.stem+f'-console{c}-{number}.ppm'
                self.ds.command(f'screen {c} {self.ds.output/filename}')
                if os.environ.get('COOP_CAPTURE_LOADING_GRAPHICS')=='1':
                    self.ds.command(f'graphics-snapshot {c} {self.ds.output/Path(filename).stem}')
                row={'screenshot':filename,'sdkVBlank':int.from_bytes(values[2],'little'),'stats':stats,'hardware':hardware,
                     **rendered_glyphs(self.ds.output/filename)}
                rows.append(row);self.save()
                if not repeat:
                    # Test sampling only: observe a later native animation phase.
                    # Runtime loading/boot behavior never depends on this delay.
                    self.ds.run(9)

    def finish(self):
        phases=[{x.get('spinnerPhase') for x in rows if x.get('textVisible') and x.get('spinnerPhase') is not None}
                for rows in self.report['consoles']]
        self.report['renderedAnimationVerified']=[len(p)>=2 for p in phases]
        self.save()
        if not all(self.report['renderedAnimationVerified']):
            raise RuntimeError('Loading feedback was not observed animating on every console; inspect '+str(self.path))
