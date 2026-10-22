//cpp
// Parent-side signed Download Station first stage. Heap loaded and relocated.
#include "types.h"
#include "WmWork.h"
extern "C" {
void CoopOriginalMBTick(void);
void CoopOriginalMBReceive(void *, u32);
u32 _ZN3IRQ7DisableEv(void);
void _ZN3IRQ7RestoreEj(u32 state);
void FS_InitFile(void *file);
int func_020185c0(void *file, unsigned fileID);
int FS_ReadFile(void *file, void *out, int size);
int FS_CloseFile(void *file);
int func_0205d368(void *file, int offset, int origin);
int func_02061c88(int port, void *callback, int argument);
int func_0206703c(unsigned aid, int request);
int func_02067250(unsigned aid);
void func_02067f2c(u32 size, u32 bitmap, void *data);
void _ZN4CP1514FlushDataCacheEjj(u32 address, u32 size);
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
extern u8 data_020a0fec[];
extern u8 data_020a1064[];
extern int data_020a0f50;
extern int data_020a0f70;
extern char *data_020a9db4;
extern u8 *data_020a9db8;
void *_ZN6Memory8AllocateEji(unsigned size, int align);
int func_02062428(void *callback, void *argument, const void *data, int length,
                   u16 destinations, u16 port, u16 priority);

struct PortReceive {
    u16 apiid, error, state, port;
    void *buffer;
    u8 *data;
    u16 length, aid;
    u8 mac[6];
    u16 sequence;
    void *argument;
};
static u32 callbacksInstalled = 0;
struct Peer {
    u32 phase, offset, chunk, repeats, cooldown;
};
static Peer peers[4];
static u8 *menuData = 0;
static u8 *payloadData = 0;
static u16 *transmitBuffer = 0;
static volatile u32 transmitBusy = 0;
static u32 transmitAid, transmitPhase, transmitBytes, nextAid = 1;
static u32 payloadDone = 0;
static u32 stationChildren = 0;
static void Pump();
void CoopBootstrapControl(u8 type, u32 bitmap);
static volatile u32 *const debug = (volatile u32 *)0x02000000;

static void Patch(u32 address, void *target) {
    *(u32 *)address = 0xea000000 | (((u32)target-address-8)>>2 & 0x00ffffff);
    _ZN4CP1514FlushDataCacheEjj(address, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(address, 4);
}

int CoopSignedBootSize(void *) {
    return COOP_SIGNED_BOOT_SIZE;
}

int CoopSignedBootRead(void *, u8 *output, u32 size) {
    u32 file[17];
    FS_InitFile(file);
    if (size < COOP_SIGNED_BOOT_SIZE || !func_020185c0(file, COOP_SIGNED_BOOT_FILE))
        return 0;
    if (FS_ReadFile(file, output, 0x160) != 0x160)
        return 0;
    const u32 *header = (const u32 *)output;
    u8 *next = output + 0x160;
    for (unsigned i=0; i<2; ++i) {
        u32 offset = header[(i ? 0x30 : 0x20)/4];
        u32 length = header[(i ? 0x3c : 0x2c)/4];
        func_0205d368(file, offset, 0);
        if (FS_ReadFile(file, next, length) != (int)length)
            return 0;
        next += length;
    }
    func_0205d368(file, header[0x80/4], 0);
    int result = FS_ReadFile(file, next, 0x88) == 0x88;
    FS_CloseFile(file);
    _ZN4CP1514FlushDataCacheEjj((u32)output, size);
    debug[2] = result;
    return result;
}

static u8 *ReadAsset(unsigned id, unsigned size) {
    u32 file[17];
    FS_InitFile(file);
    if (!func_020185c0(file,id))
        return 0;
    u8 *buffer=(u8 *)_ZN6Memory8AllocateEji(size,32);
    int ok=FS_ReadFile(file,buffer,size)==(int)size;
    FS_CloseFile(file);
    return ok ? buffer : 0;
}

void CoopStationSent(u8 *result) {
    u16 error=*(u16 *)(result+2);
    transmitBusy=0;
    debug[25]=error;
    debug[23]=*(u16 *)(result+10);
    Peer *peer=&peers[transmitAid];
    if (error)
        return; // retry on the next parent tick, not recursively in the IRQ
    ++debug[26];
    if (peer->phase==transmitPhase) {
        if (peer->phase==1 || peer->phase==5) {
            if (++peer->repeats>=1) {
                ++peer->phase; // wait for the child's port-14/15 length ACK
                peer->repeats=0;
            }
        } else if (peer->phase==7) {
            if (++peer->repeats>=1) {
                peer->phase=8;
                peer->cooldown=60;
                peer->repeats=0;
            }
        } else if (peer->phase==3 || peer->phase==8) {
            unsigned size=peer->phase==3 ? COOP_MENU_SIZE : COOP_PAYLOAD_SIZE;
            if (peer->offset==size) {
                if (peer->phase==3)
                    peer->phase=4;
                else {
                    peer->phase=9;
                    payloadDone|=1u<<transmitAid;
                    debug[27]=payloadDone;
                }
            } else if (++peer->repeats>=1) {
                peer->offset+=transmitBytes;
                ++peer->chunk;
                peer->repeats=0;
            }
        }
    }
    // Queue the next chunk on the next game tick. The signed loader has
    // a small receive queue; draining recursively from WM IRQ callbacks can
    // overrun it before its ARM9 application consumes the data.
}

static void Pump() {
    u32 interrupts=_ZN3IRQ7DisableEv();
    if (transmitBusy || !transmitBuffer) {
        _ZN3IRQ7RestoreEj(interrupts);
        return;
    }
    for (unsigned attempt=0;attempt<3;++attempt) {
        unsigned aid=nextAid;
        nextAid=nextAid==3 ? 1 : nextAid+1;
        Peer *peer=&peers[aid];
        u32 phase=peer->phase;
        if (peer->cooldown) {
            --peer->cooldown;
            continue;
        }
        unsigned port=0,length=0;
        transmitBytes=0;
        if (phase==1 || phase==5) {
            *(u32 *)transmitBuffer=phase==1 ? COOP_MENU_SIZE : COOP_PAYLOAD_SIZE;
            port=13;
            length=4;
        } else if (phase==7) {
            transmitBuffer[0]=0xfffe;
            for (unsigned i=1;i<16;++i)
                transmitBuffer[i]=0;
            port=15;
            length=32;
        } else if (phase==3 || phase==8) {
            const u8 *data=phase==3 ? menuData : payloadData;
            unsigned size=phase==3 ? COOP_MENU_SIZE : COOP_PAYLOAD_SIZE;
            unsigned capacity=phase==3 ? 30 : 126;
            port=phase==3 ? 14 : 15;
            if (peer->offset==size) {
                transmitBuffer[0]=0xffff;
                length=2;
            } else {
                unsigned remaining=size-peer->offset;
                transmitBytes=remaining<capacity ? remaining : capacity;
                transmitBuffer[0]=(u16)peer->chunk;
                for (unsigned i=0;i<transmitBytes;++i)
                    ((u8 *)(transmitBuffer+1))[i]=data[peer->offset+i];
                length=2+transmitBytes;
            }
        } else
            continue;
        transmitAid=aid;
        transmitPhase=phase;
        transmitBusy=1;
        int error=func_02062428((void *)CoopStationSent,0,transmitBuffer,length,
                                (u16)(1u<<aid),(u16)port,0);
        debug[28]=error;
        if (error!=2)
            transmitBusy=0;
        _ZN3IRQ7RestoreEj(interrupts);
        return;
    }
    _ZN3IRQ7RestoreEj(interrupts);
}

void CoopStationReceive(PortReceive *packet) {
    if (packet->error || packet->state != 0x15 || packet->aid==0 || packet->aid>3)
        return;
    ++debug[4];
    debug[5]=packet->aid;
    debug[6]=packet->port;
    debug[7]=packet->length;
    for (unsigned i=0;i<packet->length && i<32;++i)
        ((volatile u8 *)(debug+8))[i]=packet->data[i];
    Peer *peer=&peers[packet->aid];
    if (packet->port==13 && data_020a9db8) {
        stationChildren|=1u<<packet->aid;
        Patch(0x02066470, (void *)CoopBootstrapControl);
        // The signed station reconnects with its blank user name, then uses
        // ports 13-15 rather than requesting MB image blocks. Stop the MB
        // image sender for this peer while retaining the WM connection.
        *(u32 *)(data_020a9db8+0x14e8+(packet->aid-1)*4)=0;
        *(u16 *)(data_020a9db8+0x1754+(packet->aid-1)*2)=0;
        for (unsigned file=0;file<16;++file)
            *(u16 *)(data_020a9db8+0x1788+file*0x5c4+0x5bc)&=~(1u<<packet->aid);
    }
    if (packet->port==13 && packet->length>=8) {
        // The signed client requests the menu by name, then the selected SRL.
        // All three visible menu entries refer to the same private payload.
        bool menu=true;
        const char *name="demomenu";
        for (unsigned i=0;i<8;++i)
            if (packet->data[i]!=(u8)name[i])menu=false;
        peer->phase=menu ? 1 : 5;
        peer->offset=peer->chunk=peer->repeats=0;
    } else if (packet->port==14 && (peer->phase==1 || peer->phase==2)) {
        peer->phase=3;
        peer->offset=peer->chunk=peer->repeats=0;
    } else if (packet->port==15 && (peer->phase==5 || peer->phase==6)) {
        peer->phase=7;
        peer->offset=peer->chunk=peer->repeats=0;
    }
    debug[19+packet->aid]=peer->phase;
    Pump();
}

void CoopBootstrapControl(u8 type, u32 bitmap) {
    // Download Station keeps a small application heartbeat on port 1 after
    // multiboot. Its loader expects the original station heartbeat contents.
    data_020a9db8[0]=type;
    data_020a9db8[1]=0;
    *(u16 *)(data_020a9db8+2)=type==0 ? 0x48 : 0;
    *(u16 *)(data_020a9db8+4)=type==0 ? 2 : 0;
    func_02067f2c(6,bitmap,data_020a9db8);
}

void CoopBootstrapMBReceive(void *packet, u32 aid) {
    if (aid<=3 && peers[aid].phase)
        return;
    CoopOriginalMBReceive(packet,aid);
}

void CoopBootstrapMBTick(void) {
    // Keep the parent SDK alive after each signed client boots. The ordinary
    // game ends MB once every child boots; HaxxStation still needs its second
    // transfer over ports 13/14/15 before switching to the game session.
    if (data_020a0f50 == 3)
        data_020a0f70 = 0;
    CoopOriginalMBTick();
    debug[1] = data_020a0f50;
    for (unsigned aid=1;aid<=3;++aid)debug[19+aid]=peers[aid].phase;
    debug[29]=peers[1].offset;
    debug[30]=peers[1].chunk;
    if (!callbacksInstalled && data_020a9db4 && WM_WORK->mpStarted) {
        int result = 0;
        for (int port=13; port<=15; ++port)
            result |= func_02061c88(port, (void *)CoopStationReceive, 0);
        if (result == 0)
            callbacksInstalled = 1;
        debug[3] = result;
    }
    Pump();
    if (data_020a0f50 != 3)
        return;
    for (unsigned aid=1; aid<=3; ++aid) {
        int state = func_02067250(aid);
        debug[16+aid] = state;
        if (data_020a9db8) {
            const u16 *name=(const u16 *)(data_020a9db8+0x1340+(aid-1)*0x16+2);
            bool blank=true;
            for (unsigned n=0;n<10;++n)
                if (name[n]!=0x20)blank=false;
            if (blank)stationChildren|=1u<<aid;
        }
        if (state == 0xa)
            func_0206703c(aid, 1);
        if (stationChildren&(1u<<aid))
            continue;
        if (state == 0xe)
            func_0206703c(aid, 2);
        else if (state == 7)
            func_0206703c(aid, 3);
    }
}

int CoopBootstrapInit(void *) {
    for (unsigned i=0; i<32; ++i)
        debug[i] = 0;
    debug[0] = 0x58584148;
    debug[24] = (u32)CoopBootstrapMBTick;
    menuData=ReadAsset(COOP_MENU_FILE,COOP_MENU_SIZE);
    payloadData=ReadAsset(COOP_PAYLOAD_FILE,COOP_PAYLOAD_SIZE);
    transmitBuffer=(u16 *)_ZN6Memory8AllocateEji(160,32);
    if (!menuData || !payloadData || !transmitBuffer) {
        debug[31]=1;
        return 0;
    }
    // Download Station's client searches for the Download Station GGID.
    *(u32 *)(data_020a0fec+0x14) = 0x00400120;
    *(u16 *)(data_020a1064+6) = 0x0120;
    *(u16 *)(data_020a1064+8) = 0x0040;
    Patch(0x02067e70, (void *)CoopSignedBootSize);
    Patch(0x02067bfc, (void *)CoopSignedBootRead);
    Patch(0x0203e20c, (void *)CoopBootstrapMBTick);
    Patch(0x0206655c, (void *)CoopBootstrapMBReceive);
    return 1;
}
}
