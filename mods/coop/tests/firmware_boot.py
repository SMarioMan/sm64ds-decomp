"""Boot a cartridge through the real BIOS/firmware in the stock melonDS core.

This does not emulate a flashcart kernel or establish a physical-hardware pass.
"""
import argparse
import json
import os
from pathlib import Path
from emulators import Emulators


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    os.environ['COOP_HOST_FIRMWARE_BOOT']='1'
    os.environ.setdefault('COOP_HARNESS_EXE',str(Path(__file__).resolve().parents[3]/
                                              'build/coop/melon-test-jit-firmware-boot'))
    report={'status':'running','directBoot':False,'physicalHardwareVerified':False}
    args.output.mkdir(parents=True,exist_ok=True)
    def save():
        (args.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        with Emulators(args.image,0,args.output) as ds:
            report['initialBootKind']=ds.read(0,0x023ffc40,2).hex()
            if report['initialBootKind']!='0000':
                raise RuntimeError('Frontend did not start in BIOS/firmware boot mode')
            ds.run(180)
            def title():
                scene=ds.word(0,0x0209f5c0)
                return (ds.word(0,0x02004800)==0xe3a0c301 and
                        0x02000000<=scene<0x023ff000 and
                        ds.read(0,scene+12,2)==b'\x01\0' and
                        ds.read(0,scene+14,1)!=b'\0' and
                        not ds.read(0,scene+19,1)[0]&1)
            for attempt in range(40):
                if title():break
                # Dismiss the health screen, select the Slot-1 panel, and
                # confirm through ordinary firmware input. Observe title
                # before sending another input to the loaded application.
                for x,y in ((128,160),(128,50)):
                    if title():break
                    ds.touch(0,x,y)
                    ds.run(120)
                if not title():
                    ds.set_input(0,0xffe);ds.run(12)
                    ds.set_input(0,0xfff);ds.run(120)
                if attempt%5==0:
                    print('Firmware boot',attempt,'kind',ds.read(0,0x023ffc40,2).hex(),flush=True)
            else:
                ds.screens('firmware-boot-failed-')
                ds.command(f'dump 0 {args.output/"firmware-boot-failed.ram"}')
                ds.command('regs 0')
                raise RuntimeError('Firmware did not reach an initialized native title scene')
            ds.screens('firmware-title-')
            report['status']='passed'
            report['finalBootKind']=ds.read(0,0x023ffc40,2).hex()
            save()
            print('Native title reached through BIOS/firmware boot.',flush=True)
    except Exception as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}')
        save()
        raise


if __name__=='__main__':main()
