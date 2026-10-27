//cpp
// Parent-side signed Download Station first stage. Heap loaded and relocated.
#include "types.h"
#include "WmWork.h"
#include "private/arm9_a9db8_mb_parent.h"
#include "dScEntry_c.h"
#include "Memory.h"
#include "Heap.h"
extern dScEntry_c::StepSet data_ov075_0211d8d0;
extern "C" {
void CoopOriginalMBTick(void);
void CoopOriginalMBReceive(void *, u32);
void CoopOriginalParentEvent(int, void *);
void CoopOriginalMBSend(void);
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
int func_02068e44(int parentSize, int childSize, int entries);
int func_02067f2c(u32 size, u32 bitmap, void *data);
u8 *func_02065d5c(void *record, u8 *destination);
void _ZN4CP1514FlushDataCacheEjj(u32 address, u32 size);
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
extern u8 data_020a0fec[];
extern u8 data_020a1064[];
extern int data_020a0f50;
extern int data_020a0f70;
extern u8 data_020a0f04;
extern u8 data_020a0f08;
extern u16 data_020a0f28;
extern u16 data_020a0f20;
extern int data_020a0f40;
extern u8 data_020a0f9d[];
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
    u32 phase, offset, chunk, repeats, cooldown, generation;
};
static Peer peers[4];
static u8 *menuData = 0;
static u8 *payloadData = 0;
static u16 *transmitBuffer = 0;
static u8 *mpSendWork = 0;
static volatile u32 transmitBusy = 0;
static u32 transmitAid, transmitPhase, transmitBytes, transmitGeneration, nextAid = 1;
#ifdef COOP_EXPERIMENTAL_BOOTSTRAP_MULTICAST
static u32 transmitTargets,transmitOffset,transmitChunk,transmitGenerations[4];
u32 coopBootstrapMulticastStats[4]={0}; // completed groups, recipient advances, saved payload bytes, stale recipients.
#endif

static u32 payloadDone = 0;
static u32 stationChildren = 0;
static u32 stationAssociations = 0;
static u32 bootstrapPhase = 1;
static volatile u32 bootAccepted = 0;
static u32 bootControls[4];
static u32 handoffDelay = 0;
static const u32 hookAddresses[8]={0x02067e70,0x02067bfc,0x0203e20c,
                                 0x0206655c,0x02066470,0x02068dc8,0x02066a94,0x02065f78};
static u32 originalHooks[8];
static u32 originalRegistryId;
static u16 originalGameId[2];
static dScEntry_c *entryScene;
static mHeap::Heap_t *assetHeap;
static void Pump();
int CoopBootstrapControl(u8 type, u32 bitmap);
void func_02065f78(void);
static volatile u32 *const debug = (volatile u32 *)0x02000000;
static u32 nextBootAid=1;
#if COOP_RESTART_STATION_PARENT
static u32 stationRestarted=0;
static u16 firmwareTGID=0;
#endif

void CoopBootstrapMBSend(void) {
    // Keep the parent available for scans between associations. Empty MP
    // sends have no recipient and needlessly keep the radio in its data loop.
    // CONNECTED and the normal tick resume the sender when a child returns.
    if (!data_020a9db4 || !WM_WORK->childBitmap)return;
#if COOP_SERIAL_BOOT
    // Retain the other firmware children in their ready-to-boot state until
    // this signed client has actually received its menu. Their occupied AIDs
    // keep the reconnecting client's radio slot stable. Native MB continues
    // serving its fake-child handshake and NI requests between boot commands.
    while (nextBootAid<=COOP_EXPECTED_CLIENTS && peers[nextBootAid].phase>=4)
        ++nextBootAid;
    u32 interrupts=_ZN3IRQ7DisableEv();
    u32 hidden=0;
    for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid) {
        s32 *state=(s32 *)(data_020a9db8+0x14e8+(aid-1)*4);
        if (aid!=nextBootAid && *state==8) {
            *state=0;
            hidden|=1u<<aid;
        }
    }
    CoopOriginalMBSend();
    for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
        if (hidden&(1u<<aid))*(s32 *)(data_020a9db8+0x14e8+(aid-1)*4)=8;
    _ZN3IRQ7RestoreEj(interrupts);
#else
    CoopOriginalMBSend();
#endif
    // Count every sender invocation, including completion-driven calls.
    ++debug[15];
}
#if COOP_REARM_MP_AFTER_BOOT
int WM_CheckStateEx(int count, ...);
void WM_SetCallbackTable(int api, void *callback);
int WM_SendCommand(s16 api, u16 arguments, ...);
int func_020625fc(void *callback, int receive, int receiveSize, int send,
                  u16 sendSize, u16 frequency, u16 minimum, int maximum,
                  int single, int fixed, int ignoreFatal);
void func_02069994(char *packet);
static volatile u32 mpRearm = 0;
static volatile u32 mpNewAssociation = 0;
void CoopBootEndMP(void *packet) {
    u16 error = ((u16 *)packet)[1];
    debug[31] = bootAccepted | (error << 16) | 0x200;
    WM_SetCallbackTable(0x10, 0);
    if (error) {
        mpRearm = 0;
        return;
    }
    WM_WORK->mpStarted = 0;
    WM_WORK->mpSending = 0;
    // EndMP preserves WM's port callback table. Keep the receivers installed
    // throughout the restart, including a child's first reconnect packet.
    *(u32 *)(data_020a9db8+0x1324) = 0;
    // Retain parent mode, channel/TGID and beacons. Wait for an actual new
    // association before starting another MP clock, rather than a tick delay.
    mpRearm = 2;
    mpNewAssociation = 0;
}
#endif

#if COOP_CLOSE_ENTRY_BEFORE_BOOT
int func_020635d8(void *callback,int enabled);
int func_02063648(void *callback,int *info,int length,int ggidLow,
                  u16 ggidHigh,u16 tgid,u8 attributes);
int func_020688e4(void);
int func_020688cc(void);
int func_020688b4(void);
int func_02068844(void);
void WM_SetCallbackTable(int api,void *callback);
void func_02069994(char *packet);
// 1/3 request SDK operations, 2/4 wait for their callbacks, 5 permits BOOT.
static volatile u32 bootEntryState=0;
void CoopBootEntryClosed(void *packet) {
    bootEntryState=((u16 *)packet)[1] ? 1 : 3;
    debug[31]=0x1000|bootEntryState;
    WM_SetCallbackTable(0x19,(void *)func_02069994);
}
void CoopBootClosedBeacon(void *packet) {
    bootEntryState=((u16 *)packet)[1] ? 3 : 5;
    debug[31]=0x1000|bootEntryState;
    WM_SetCallbackTable(0x18,0);
}
static void CloseBootEntry() {
    if (bootEntryState==1) {
        // Existing firmware associations remain. Returning signed loaders
        // must wait for the recreated parent instead of joining one closing.
        WM_WORK->parentParam.entryFlag=0;
        bootEntryState=2;
        if (func_020635d8((void *)CoopBootEntryClosed,0)!=2)bootEntryState=1;
    } else if (bootEntryState==3) {
        // Publish the closed ENTRY attribute using the native valid MB
        // beacon body. Await its ARM7 acknowledgement before sending BOOT.
        bootEntryState=4;
        if (func_02063648((void *)CoopBootClosedBeacon,(int *)0x020a9d40,0x70,
                func_020688e4(),func_020688cc(),func_020688b4(),
                func_02068844()|2)!=2)bootEntryState=3;
    }
    debug[31]=0x1000|bootEntryState;
}
#endif

static void Patch(u32 address, void *target) {
    *(u32 *)address = 0xea000000 | (((u32)target-address-8)>>2 & 0x00ffffff);
    _ZN4CP1514FlushDataCacheEjj(address, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(address, 4);
}

static void RestoreBootstrap() {
    // The executable is already in every child's RAM. Release the transfer
    // buffers before native WFS and ENTRY load their models and archives.
    // The executing bootstrap itself stays allocated until ENTRY retires.
    assetHeap->Deallocate(payloadData);
    assetHeap->Deallocate(menuData);
    assetHeap->Deallocate(transmitBuffer);
    assetHeap->Deallocate(mpSendWork);
    payloadData=menuData=0;
    transmitBuffer=0;
    mpSendWork=0;
    *(u32 *)(data_020a0fec+0x14)=originalRegistryId;
    *(u16 *)(data_020a1064+6)=originalGameId[0];
    *(u16 *)(data_020a1064+8)=originalGameId[1];
    for (unsigned i=0;i<8;++i) {
        *(u32 *)hookAddresses[i]=originalHooks[i];
        _ZN4CP1514FlushDataCacheEjj(hookAddresses[i],4);
        _ZN4CP1526InvalidateInstructionCacheEjj(hookAddresses[i],4);
    }
}

int CoopBootstrapSetPacketSize(int, int childSize, int entries) {
    if (!mpSendWork || WM_WORK->initialized || !func_02068e44(0xfe,childSize,entries))
        return 0;
    // Retail MB aliases its message source with WM's MP assembly workspace.
    // That single-port shortcut corrupts the MB message when NI menu/payload
    // packets share a frame: their chunk number becomes an MB command byte.
    // Keep every queued message source separate from the SDK's output buffer.
    WM_WORK->sendBuf=(char *)mpSendWork;
#if COOP_RESTART_STATION_PARENT
    if (!stationRestarted)firmwareTGID=WM_WORK->parentParam.tgid;
    else {
        WM_WORK->parentParam.tgid=firmwareTGID;
        data_020a0f20=firmwareTGID;
    }
#endif
    WM_WORK->parentParam.maxEntry=entries;
    WM_WORK->parentMaxSize=0xfe;
    WM_WORK->childMaxSize=childSize;
#if COOP_BOOT_BEACON_PERIOD
    // The signed station scans for this parent after its firmware reset.
    // Keep this opt-in while checking discovery against the native 200..219 TU.
    WM_WORK->parentParam.beaconPeriod=COOP_BOOT_BEACON_PERIOD;
#endif
#if COOP_BOOT_CHANNEL
    // Native MB start consumes this measured channel after packet sizing.
    // Keep the signed loader and subsequent native session on the same radio.
    data_020a0f28=COOP_BOOT_CHANNEL;
#endif
    return 1;
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


#ifdef COOP_EXPERIMENTAL_BOOTSTRAP_MULTICAST
u32 CoopBootstrapPayloadTargets(unsigned aid) {
    if (!aid || aid>COOP_EXPECTED_CLIENTS || !data_020a9db4 ||
        !(WM_WORK->childBitmap&(1u<<aid)))return 0;
    const Peer *first=&peers[aid];
    u32 targets=1u<<aid;
    // Only identical nonterminal execution-payload blocks share a send.
    // Length/menu/start/execute messages keep their original per-peer path.
    if (first->phase!=8 || first->offset>=COOP_PAYLOAD_SIZE || first->cooldown)return targets;
    for (unsigned other=1;other<=COOP_EXPECTED_CLIENTS;++other) {
        const Peer *peer=&peers[other];
        if ((WM_WORK->childBitmap&(1u<<other)) && peer->phase==8 &&
            peer->offset==first->offset && peer->chunk==first->chunk && !peer->cooldown)
            targets|=1u<<other;
    }
    return targets;
}
#endif

void CoopStationSent(u8 *result) {
    u16 error=*(u16 *)(result+2);
    transmitBusy=0;
    debug[25]=error;
    debug[23]=*(u16 *)(result+10);
    Peer *peer=&peers[transmitAid];
    if (error)
        return; // retry on the next parent tick, not recursively in the IRQ
    ++debug[26];
#ifdef COOP_EXPERIMENTAL_BOOTSTRAP_MULTICAST
    if (transmitTargets) {
        unsigned advanced=0;
        for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid) {
            if (!(transmitTargets&(1u<<aid)))continue;
            Peer *recipient=&peers[aid];
            // A reconnect/request may replace a peer while the SDK owns the
            // send. Its success must never acknowledge that new transaction.
            if (recipient->phase!=8 || recipient->generation!=transmitGenerations[aid] ||
                recipient->offset!=transmitOffset || recipient->chunk!=transmitChunk) {
                ++coopBootstrapMulticastStats[3];continue;
            }
            recipient->offset+=transmitBytes;++recipient->chunk;recipient->repeats=0;
            ++advanced;
        }
        ++coopBootstrapMulticastStats[0];coopBootstrapMulticastStats[1]+=advanced;
        if (advanced>1)coopBootstrapMulticastStats[2]+=(advanced-1)*transmitBytes;
        Pump();return;
    }
#endif
    if (peer->phase==transmitPhase && peer->generation==transmitGeneration) {
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
    // WM has released this buffer. Keep only one application packet pending,
    // and refill from completion just as the station's sender does. The
    // receiver consumes its port packet in the WM callback.
    Pump();
}

static void Pump() {
    // Serve the signed loader's menu as soon as each child asks. Waiting
    // for the last child here strands earlier requests during mixed firmware
    // and signed-loader reconnects. Gate only execution payloads, so all
    // native game clients still start within their connection deadline.
    u32 interrupts=_ZN3IRQ7DisableEv();
    if (bootstrapPhase==2 || transmitBusy || !transmitBuffer || !data_020a9db4 ||
        !WM_WORK->initialized || !WM_WORK->mpStarted || WM_WORK->resetting) {
        _ZN3IRQ7RestoreEj(interrupts);
        return;
    }
    bool payloadReady=stationChildren==((1u<<(COOP_EXPECTED_CLIENTS+1))-2);
    bool payloadTransferred=true;
    for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid) {
        if (peers[aid].phase<7)payloadReady=false;
        if (peers[aid].phase<8 || peers[aid].offset!=COOP_PAYLOAD_SIZE)
            payloadTransferred=false;
    }
    for (unsigned attempt=0;attempt<3;++attempt) {
        unsigned aid=nextAid;
        nextAid=nextAid==3 ? 1 : nextAid+1;
        Peer *peer=&peers[aid];
        u32 phase=peer->phase;
        if (!(WM_WORK->childBitmap&(1u<<aid)))continue;
        if ((phase==7 || phase==8) && !payloadReady)
            continue;
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
                // This terminator executes the received ROM. A slow guest
                // must finish its body before any earlier guest boots into
                // the native game's finite connection deadline.
                if (phase==8 && !payloadTransferred)continue;
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
        transmitGeneration=peer->generation;
#ifdef COOP_EXPERIMENTAL_BOOTSTRAP_MULTICAST
        u16 destinations=(u16)CoopBootstrapPayloadTargets(aid);
        transmitTargets=destinations&(destinations-1) ? destinations : 0;
        transmitOffset=peer->offset;transmitChunk=peer->chunk;
        for (unsigned recipient=1;recipient<=COOP_EXPECTED_CLIENTS;++recipient)
            transmitGenerations[recipient]=peers[recipient].generation;
#endif
        transmitBusy=1;
        int error=func_02062428((void *)CoopStationSent,0,transmitBuffer,length,
#ifdef COOP_EXPERIMENTAL_BOOTSTRAP_MULTICAST
                                destinations,
#else
                                (u16)(1u<<aid),
#endif
                                (u16)port,0);
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

static void InstallStationReceivers() {
    int result=0;
    for (int port=13;port<=15;++port)
        result|=func_02061c88(port,(void *)CoopStationReceive,0);
    callbacksInstalled=result==0;
    debug[3]=result;
}

void CoopBootstrapParentEvent(int event, void *packet) {
    // CONNECTED follows WM initialization and precedes this association's
    // MP start. Reinstall here even if an earlier initialization cleared the
    // SDK's tables; the first reliable NI request must have a receiver.
    if (event==0)InstallStationReceivers();
    if (event==0 && packet) {
        unsigned aid=*(u16 *)((u8 *)packet+0x10);
        // Callbacks can precede the scene's phase transition. Once BOOT has
        // been submitted, a returning association belongs to the downloaded
        // station, even if the main-thread tick still reports phase 1.
        // This role is monotonic for the remainder of the bootstrap.
        if (aid>=1 && aid<=COOP_EXPECTED_CLIENTS &&
            (bootstrapPhase==3 || bootControls[aid]))stationAssociations|=1u<<aid;
    }
#if COOP_REARM_MP_AFTER_BOOT
    if (event==0 && mpRearm==2)mpNewAssociation=1;
#endif
    if (event==0 && bootstrapPhase==1 && packet) {
        unsigned aid=*(u16 *)((u8 *)packet+0x10);
        if (aid>=1 && aid<=COOP_EXPECTED_CLIENTS && !(stationAssociations&(1u<<aid))) {
            // Firmware can leave and retry before the group starts. A radio
            // slot reused by that association has not acknowledged its BOOT.
            bootControls[aid]=0;
            bootAccepted&=~(1u<<aid);
        }
    }
    // WM's CONNECTED callback identifies the new association, before MB
    // processes its first request. An AID is a reusable radio slot, not a
    // permanent player identity. Invalidate callbacks from its previous use.
    if (bootstrapPhase==3 && (event==0 || event==1) && packet) {
        unsigned aid=*(u16 *)((u8 *)packet+0x10);
        if (aid>=1 && aid<=COOP_EXPECTED_CLIENTS) {
            Peer *peer=&peers[aid];
            // A finished executable is expected to leave this association.
            // Retain its completion until the party handoff. Earlier losses
            // abandon the transfer immediately instead of pumping a dead AID.
            if (event==0 || peer->phase<9) {
                peer->phase=peer->offset=peer->chunk=peer->repeats=peer->cooldown=0;
                ++peer->generation;
                stationChildren&=~(1u<<aid);
                payloadDone&=~(1u<<aid);
            }
        }
    }
#if COOP_CLOSE_ENTRY_BEFORE_BOOT
    // Native BEACON_SENT handling queues SetGameInfo without a callback.
    // Keep it from replacing our outstanding SetGameInfo completion handler.
    if (event==0x1c && (bootEntryState==3 || bootEntryState==4))return;
#endif
    CoopOriginalParentEvent(event,packet);
    debug[16]=(u32)event;
}

int CoopBootstrapControl(u8 type, u32 bitmap) {
    if (bootstrapPhase==2)return 0;
#if COOP_REARM_MP_AFTER_BOOT
    if (mpRearm == 1)return 0;
#endif
#if COOP_CLOSE_ENTRY_BEFORE_BOOT
    if (type==5 && (bootstrapPhase==1 || bootstrapPhase==3) &&
        !stationRestarted && bootEntryState!=5) {
        if (!bootEntryState)bootEntryState=1;
        type=0;
        bitmap=0xffff;
    }
#endif
    if (type==5) {
        // BOOT is a two-phase firmware handshake. The first request enters
        // BOOTREQ_ACCEPTED (reply 11); a later BOOT sets boot_end_flag and
        // starts MBi_CommEnd. Keep the native request active until actual
        // disconnection. Stopping on reply 11 makes success depend on whether
        // another request happened to be queued before that reply arrived.
        u32 pending=0;
        for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
            if ((bitmap&(1u<<aid)) && !(stationAssociations&(1u<<aid)) &&
                func_02067250(aid)==8 && !peers[aid].phase) {
                pending|=1u<<aid;
            }
        if (pending)bitmap=pending;
        else {type=0;bitmap=0xffff;}
    }
    u32 active=0;
    for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
        if (peers[aid].phase)active|=1u<<aid;
    if (active==((1u<<(COOP_EXPECTED_CLIENTS+1))-2))return 0;
    // Download Station keeps a small application heartbeat on port 1 after
    // multiboot. Its loader expects the original station heartbeat contents.
    if (type==0 && (bootstrapPhase==3
#if COOP_SERIAL_BOOT
        // Serial BOOT keeps later firmware clients connected while an earlier
        // signed station downloads its menu. Its application heartbeat is
        // needed as soon as that station associates, before the group phase
        // changes. Firmware ignores the extra fields of an idle command.
        || stationAssociations
#endif
        )) {
        data_020a9db8[0]=0;
        data_020a9db8[1]=0;
        *(u16 *)(data_020a9db8+2)=0x48;
        *(u16 *)(data_020a9db8+4)=2;
    } else {
        // Preserve the SDK's firmware control serialization, including bytes
        // outside the selected record. Only the station heartbeat differs.
        u32 record[2];
        record[0]=type;
        record[1]=0;
        func_02065d5c(record,data_020a9db8);
    }
    int result=func_02067f2c(6,bitmap,data_020a9db8);
    if (type==5 && result==0)
        for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
            if (bitmap&(1u<<aid))++bootControls[aid];
    return result;
}

void CoopBootstrapMBReceive(void *packet, u32 aid) {
    // Observe the firmware's boot acknowledgement without resetting the WM
    // parent that the signed application will reconnect to.
    if (aid>=1 && aid<=3 && packet) {
        u8 type=((u8 *)packet)[10];
        debug[12]=type;
        // Tracking begins at bootstrap installation, so acknowledgements of
        // native BOOT requests preceding the scene-phase change count too.
        if (type==11 && bootControls[aid] && func_02067250(aid)==8) {
            ++debug[13];
            bootAccepted |= 1u<<aid;
        }
    }
    if (aid<=3 && peers[aid].phase)
        return;
    if (aid>=1 && aid<=3 && packet && (stationAssociations&(1u<<aid))) {
        // The signed loader's fake MB child needs the file header, then
        // requests its menu over NI. It must not enter a second legacy image
        // transfer or BOOT cycle while that NI request is being initialized.
        // Allow the first type-8 header ACK to reach native state 14, but
        // never consume a stale SEND_START response on a subsequent ACK.
        unsigned type=((u8 *)packet)[10];
        if ((type==8 && func_02067250(aid)!=5) || type==9 || type==10 || type==11)
            return;
    }
    CoopOriginalMBReceive(packet,aid);
}

void CoopBootstrapMBTick(void) {
    if (!callbacksInstalled && data_020a9db4 && WM_WORK->mpStarted && !WM_WORK->resetting)
        InstallStationReceivers();
    // Keep the parent SDK alive after each signed client boots. The ordinary
    // game ends MB once every child boots; HaxxStation still needs its second
    // transfer over ports 13/14/15 before switching to the game session.
    if (data_020a0f50==3) {
        bool ready=bootstrapPhase==1 && data_020a0f08==COOP_EXPECTED_CLIENTS+1;
        // A roster name alone does not establish download readiness. Native
        // state 14 means this association acknowledged the image header and
        // is waiting for permission to request its data. Require every guest,
        // rather than latching START from a previous frame's roster count.
        for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
            if (func_02067250(aid)!=14)ready=false;
        data_020a0f70=ready;
    }
    if (COOP_GAME_HANDOFF && bootstrapPhase==3 &&
        payloadDone==((1u<<(COOP_EXPECTED_CLIENTS+1))-2) && ++handoffDelay>=3) {
        // Every end packet has completed. Leave only a short callback grace
        // period: the booted games have a finite connection deadline, while
        // an old MP parent waiting for their replies can run very slowly.
        for (int port=13;port<=15;++port)func_02061c88(port,0,0);
        // The native parent admits only the MACs from the download roster.
        // Its MB tick clears the presence flags while the downloaded games
        // reboot. Keep the captured MACs and restore the original party.
        for (unsigned aid=1;aid<=3;++aid)
            data_020a0f9d[aid-1]=aid<=COOP_EXPECTED_CLIENTS;
        data_020a0f08=COOP_EXPECTED_CLIENTS+1;
        bootstrapPhase=4;
        data_020a0f50=6;
    }
#if COOP_RESTART_STATION_PARENT
    bool restart=bootstrapPhase==3 && !stationRestarted && !stationAssociations;
    if (restart)
        for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
            if (peers[aid].phase || func_02067250(aid)!=0 || !bootControls[aid])restart=false;
    if (restart && data_020a9db4 && !WM_WORK->childBitmap && !WM_WORK->resetting) {
        // The firmware associations have all ended. Recreate the parent
        // through its native shutdown/start sequence before any signed
        // application associates; no user timing or fixed delay is involved.
        stationRestarted=1;
        bootstrapPhase=2;
        data_020a0f50=6;
        data_020a0f70=0;
    }
#endif
    CoopOriginalMBTick();
#if COOP_CLOSE_ENTRY_BEFORE_BOOT
    if ((bootstrapPhase==1 || bootstrapPhase==3) &&
        !stationRestarted && bootEntryState)CloseBootEntry();
#endif
#if COOP_RESTART_STATION_PARENT
    if (bootstrapPhase==2) {
        if (data_020a0f04==0) {
            // Native case 8 has released the old WM/MB work allocation.
            // Hide its retired pointers until the new case 2 initializes it.
            data_020a9db4=0;
            data_020a9db8=0;
            callbacksInstalled=0;
            data_020a0f40=0;
            data_020a0f50=0;
            data_020a0f04=3;
            bootstrapPhase=3;
        }
        return;
    }
#endif
    if (bootstrapPhase==4 && data_020a0f04==0) {
        // Enter the ordinary host player-sync step to initialize native
        // parent networking/WFS. Restore every RAM hook
        // before that scene can release the heap containing this code.
        RestoreBootstrap();
        entryScene->SetSteps(&data_ov075_0211d8d0);
        debug[14]=5;
        return;
    }
    if (bootstrapPhase==1 && data_020a0f50==6) {
        // Stay on this channel while the signed applications reconnect.
        // Their WM reset is asynchronous; the retail game would reset its
        // parent here, racing the firmware's boot-ready callback.
        data_020a0f50=3;
        data_020a0f70=0;
        bootstrapPhase=3;
        Patch(0x02066470, (void *)CoopBootstrapControl);
    }
#if COOP_REARM_MP_AFTER_BOOT
    bool firmwareReady=true;
    for (unsigned aid=1;aid<=COOP_EXPECTED_CLIENTS;++aid)
        if (peers[aid].phase || func_02067250(aid)!=0 ||
            !bootControls[aid])
            firmwareReady=false;
    if (bootstrapPhase==3 && !mpRearm &&
        firmwareReady &&
        WM_WORK->mpStarted && !WM_WORK->mpSending && !WM_WORK->childBitmap &&
        WM_CheckStateEx(2,9,10)==0) {
        WM_SetCallbackTable(0x10,(void *)CoopBootEndMP);
        int result=WM_SendCommand(0x10,0);
        debug[31]=bootAccepted | (result<<16) | 0x100;
        if (result==2)mpRearm=1;
        else WM_SetCallbackTable(0x10,0);
    }
    if (mpRearm==2 && mpNewAssociation && WM_WORK->childBitmap) {
        if (WM_WORK->mpStarted) {
            mpRearm=4;
            debug[31]=bootAccepted | 0x400;
        } else if (WM_CheckStateEx(1,7)==0) {
            u32 interrupts=_ZN3IRQ7DisableEv();
            bool available=*(u32 *)(data_020a9db8+0x1324)==0;
            if (available)*(u32 *)(data_020a9db8+0x1324)=1;
            _ZN3IRQ7RestoreEj(interrupts);
            if (available) {
                int result=func_020625fc((void *)func_02069994,(int)WM_WORK->recvBuf,
                    WM_WORK->recvBufSize,(int)WM_WORK->sendBuf,WM_WORK->sendBufSize,
                    WM_WORK->mpContinuous ? 0 : 1,0,0,0,1,1);
                debug[31]=bootAccepted | 0x300 | (result<<16);
                if (result==2)mpRearm=3;
                else *(u32 *)(data_020a9db8+0x1324)=0;
            }
        }
    }
    if (mpRearm==3 && WM_WORK->mpStarted) {
        mpRearm=4;
        debug[31]=bootAccepted | 0x400;
    }
#endif
    debug[1] = data_020a0f50;
    for (unsigned aid=1;aid<=3;++aid)debug[19+aid]=peers[aid].phase;
    debug[29]=peers[1].offset;
    debug[30]=peers[1].chunk;
    // The older parent SDK clears mpSending on WM send error 0x0a, then
    // dispatches MB event 0x2a, which its MB handler does not handle. Its
    // callback-driven sender otherwise remains idle indefinitely. Resume it
    // from the normal tick when no packet is pending, including during the
    // firmware-to-station reconnect. Application transfers have their own
    // completion-driven pump and suppress MB controls once all peers request.
    u32 interrupts = _ZN3IRQ7DisableEv();
    if ((bootstrapPhase==1 || bootstrapPhase==3) && data_020a9db8 &&
        WM_WORK->mpStarted && !WM_WORK->resetting && !WM_WORK->mpSending) {
        func_02065f78();
    }
    _ZN3IRQ7RestoreEj(interrupts);
    Pump();
    if (data_020a0f50 != 3)
        return;
    for (unsigned aid=1; aid<=3; ++aid) {
        int state = func_02067250(aid);
        debug[16+aid] = state;
        debug[14]=bootstrapPhase;
        if (bootstrapPhase==3 && state==10 && !(stationChildren&(1u<<aid))) {
            MbParentWork *work=(MbParentWork *)data_020a9db8;
            const u16 *name=(const u16 *)(work->mChildUser[aid-1]+2);
            bool blank=true;
            for (unsigned n=0;n<10;++n)
                if (name[n]!=0x20)blank=false;
            if (blank) {
                // The station reuses its AID. The older game's MB code
                // retains the firmware's file entry across that reconnect.
                u16 bit=1u<<aid;
                if (work->mChildEntryBitmap&bit) {
                    work->mChildEntryBitmap&=~bit;
                    --work->mChildCount;
                }
                for (unsigned file=0;file<16;++file) {
                    work->mFiles[file].mEntryBitmap&=~bit;
                    work->mFiles[file].mChildBitmap&=~bit;
                    work->mFiles[file].mEntryChanged|=bit;
                }
                stationChildren|=bit;
                func_0206703c(aid,1);
            }
        }
    }
}

int CoopBootstrapInit(void *scene) {
    entryScene=(dScEntry_c *)scene;
    assetHeap=Memory::defaultHeapPtr;
    for (unsigned i=0; i<32; ++i)
        debug[i] = 0;
    debug[0] = 0x58584148;
    debug[24] = (u32)CoopBootstrapMBTick;
    for (unsigned i=0;i<8;++i)originalHooks[i]=*(u32 *)hookAddresses[i];
    originalRegistryId=*(u32 *)(data_020a0fec+0x14);
    originalGameId[0]=*(u16 *)(data_020a1064+6);
    originalGameId[1]=*(u16 *)(data_020a1064+8);
    menuData=ReadAsset(COOP_MENU_FILE,COOP_MENU_SIZE);
    payloadData=ReadAsset(COOP_PAYLOAD_FILE,COOP_PAYLOAD_SIZE);
    transmitBuffer=(u16 *)_ZN6Memory8AllocateEji(160,32);
    mpSendWork=(u8 *)_ZN6Memory8AllocateEji(0x400,32);
    if (!menuData || !payloadData || !transmitBuffer || !mpSendWork) {
        debug[31]=1;
        return 0;
    }
    for (unsigned i=0;i<0x400/4;++i)((u32 *)mpSendWork)[i]=0;
    // Download Station's client searches for the Download Station GGID.
    *(u32 *)(data_020a0fec+0x14) = 0x00400120;
    *(u16 *)(data_020a1064+6) = 0x0120;
    *(u16 *)(data_020a1064+8) = 0x0040;
    Patch(0x02067e70, (void *)CoopSignedBootSize);
    Patch(0x02067bfc, (void *)CoopSignedBootRead);
    Patch(0x0203e20c, (void *)CoopBootstrapMBTick);
    Patch(0x0206655c, (void *)CoopBootstrapMBReceive);
    Patch(0x02066470, (void *)CoopBootstrapControl);
    Patch(0x02066a94, (void *)CoopBootstrapParentEvent);
    Patch(0x02065f78, (void *)CoopBootstrapMBSend);
    Patch(0x02068dc8, (void *)CoopBootstrapSetPacketSize);
    return 1;
}
}
