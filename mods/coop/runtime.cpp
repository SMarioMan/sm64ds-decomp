//cpp
// Experimental story-mode session hooks. The original wireless lobby provides
// player selection and input exchange; changes are confined to this mod.
#include "types.h"
#include "SaveData.h"
#include "Heap.h"
#include "Sound.h"
#include "dScStage_c.h"
#include "PlayerInput.h"
#include "dActor_c.h"
#include "dCamera_c.h"
#include "LVL_Overlay.h"
#include "ExpandingHeapAllocator.h"

namespace Memory { extern mHeap::Heap_t *defaultHeapPtr; }

// Test builds can enter a later stage through the normal native loader.
// Shipping builds always start at the castle grounds.
#ifndef COOP_DIAGNOSTIC_START_LEVEL
#define COOP_DIAGNOSTIC_START_LEVEL 1
#endif
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
static bool coopDiagnosticChordHeld=false;
extern "C" u16 data_020a0e58[];
extern "C" u8 data_0209f2f8;
#endif

extern "C" {
void PrepareVsMode(void);
void SetPlayerGlobals(void);
void SetNumPlayers(int count);
void UnloadOverlay(int index);
int CoopOriginalEntryCleanup(void *scene);
void CoopOriginalLoadLevelOverlays(int level);
int CoopOriginalStageInit(void *scene);
int CoopOriginalSceneBefore(void *scene);
int CoopOriginalActorBefore(void *actor);
void CoopOriginalLoadEntrances(LVL_Overlay::ObjSubTable *table, int area, u32 index);
void func_0202b0e0(void *entries, u32 count);
void func_0203d918(void);
void func_0203d930(void);
void func_0203d854(void);
int func_020308a8(void);
int CoopOriginalReadFile(void *file, void *destination, int size, int async);
void func_02030a78(void);
void func_02030500(void);
void func_020199a4(void);
void func_02040aa4(void);
extern int data_020a0f94;
extern void *data_0209d4a8;
void *func_02054ea8(void);
void *_ZN3G2S13GetBG1CharPtrEv(void);
void *_ZN2G212GetBG1ScrPtrEv(void);
void *_ZN3G2S12GetBG1ScrPtrEv(void);
void CoopOriginalMessageUpdate(void);
void CoopOriginalKillPlayer(void);
void CoopOriginalHitDeathPlane(int reason);
int CoopOriginalStarTutorial(void *player);
int CoopOriginalCourseTutorial(void *player);
int CoopOriginalLevelEnterInit(void *player);
void CoopOriginalGiveCoins(int player, int amount);
int GiveHealth(int player, int amount);
static void Patch(u32 address, void *target);
static void PatchCall(u32 address, void *target);
void *_ZN6Memory13operator_new2Ej(u32 size);
void func_0203cbc0(void *ptr);
void *_ZN6Memory8AllocateEji(u32 size,int align);
void _ZN6Memory10DeallocateEPv(void *ptr);
u32 CoopOriginalTrimModel(void *ptr);
u32 func_020469e0(void *ptr);
void Crash(void);
extern u8 *data_0209ee78;
void *CoopOriginalResolveFile(u32 fileID);
int CoopOriginalOpenFile(void *file,u32 fileID);
void CoopOriginalLoadSkybox(void *scene);
int CoopOriginalCameraFar(void *camera,unsigned player);
void CoopOriginalCameraNear(void *camera,unsigned player);
void CoopOriginalCameraBehind(void *camera,unsigned player);
void CoopOriginalCameraFirstPerson(void *camera,unsigned player);
void CoopOriginalCameraNormal(void *camera,unsigned player);
void CoopOriginalPlayerHeadLook(void *player);
void *CoopOriginalLoadDiskFile(void *file,int flush);
int func_02018568(void *data);
void func_02018770(void);
void FS_InitFile(void *file);
int FS_ReadFile(void *file,void *dst,int size);
int FS_CloseFile(void *file);
int func_02018d98(void *file,const char *path);
int func_0205d368(void *file,int offset,int origin);
int func_0205d5e8(void *file,void *archive,u32 top,u32 bottom,u32 index);
extern mHeap::Heap_t *data_020a0e9c;
int func_0205d3f4(void *file);
void func_0201ffcc(void);
void func_02040724(void);
int CoopOriginalWirelessReset(void *callback);
void func_02042778(void);
void func_0201fe08(void);
void func_0201a428(void);
extern void *data_0209d524;
extern void *data_0209d708;
extern u16 data_020a1160[];
extern void *data_020a613c;
extern u8 data_020a621c[];
void LoadLevelNoReturn(int level, u32 entrance, u32 star, u32 reason);
int LoadArchive(int index);
void UnloadArchive(int index);
extern u8 data_0209caa0[];
extern u8 data_0209f2d8;
extern u8 data_0209f250;
extern u8 data_0209f2fc;
extern u8 data_0209f20c;
extern u8 data_0209d660;
extern u16 data_02092664;
extern u8 data_020a0f10;
extern u8 data_0209fc50;
extern u8 data_0209f21c;
extern s16 data_0209f358[];
extern s8 data_02092124;
extern s8 data_02092110;
extern u8 data_0209f228[];
extern void *data_0209f394[];
extern s16 data_02092144[];
extern u8 data_02092778;
extern void *data_020a0eac;
extern int data_0209fc68;
extern u32 data_0209e650;
extern u32 data_020a1154[];
extern u8 data_020a1052[];
extern u8 data_020a1166[];
extern dCamera_c *data_0209f318;
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
void _ZN4CP1514FlushDataCacheEv(void);
void _ZN4CP1514FlushDataCacheEjj(u32 address, u32 size);
void _ZN4CP1527FlushAndInvalidateDataCacheEjj(u32 address,u32 size);


// Kept with the executable module in ROOT, across scene/overlay changes.
u32 coopEnabled = 0;
u32 coopEntryRetired = 0;
// 0: loading; 1: host file loaded and shared; 2: cart read failed, RAM only.
u32 coopSaveState = 0;
u32 coopSavePage = 0;
static u32 coopSaveEpoch = 0;
static u8 coopSaveStorage[100];

static u8 *CoopSaveBuffer() {
    return (u8 *)(((u32)coopSaveStorage+31)&~31u);
}

static void CoopApplyHostSave() {
    u8 *buffer=CoopSaveBuffer();
    for (unsigned i=0;i<0x44;++i)data_0209caa0[i]=buffer[i];
    data_0209caa0[0x328]=COOP_SAVE_SLOT;
    ((SaveData *)data_0209caa0)->flags2|=0x80;
    SetPlayerGlobals();
}

static void CoopPublishSavePage(unsigned page) {
    u8 *buffer=CoopSaveBuffer();
    for (unsigned i=0;i<9;++i) {
        unsigned offset=(page-1)*9+i;
        data_020a1052[7+i]=offset<0x44 ? buffer[offset] : 0;
    }
    data_020a1052[6]=0x10+page;
    coopSavePage=page;
}

static bool CoopLoadHostSave() {
    if (COOP_SAVE_SLOT<0 || coopSaveState)return true;
    if (data_020a0f10==0) {
        if (!coopSavePage) {
            if (!SaveData::ReadFileData(COOP_SAVE_SLOT,(FileSaveData *)CoopSaveBuffer())) {
                // Do not turn an unreadable existing file into a fresh save.
                coopSaveState=2;
                data_020a1052[6]=0x7f;
                return true;
            }
            if (!data_0209fc68) {
                CoopApplyHostSave();
                coopSaveState=1;
                return true;
            }
            CoopPublishSavePage(1);
            return false;
        }
        u8 acknowledgement=coopSavePage<=8 ? 0x90+coopSavePage : 0xc0;
        for (unsigned slot=1;slot<data_0209fc50;++slot)
            if (data_020a1166[slot*36+6]!=acknowledgement)return false;
        if (coopSavePage<8) {
            CoopPublishSavePage(coopSavePage+1);
        } else if (coopSavePage==8) {
            CoopApplyHostSave();
            data_020a1052[6]=0x40;
            coopSavePage=9;
        } else {
            data_020a1052[6]=0;
            coopSaveState=1;
            return true;
        }
        return false;
    }
    unsigned tag=data_020a1166[6];
    if (tag==0x7f) {
        coopSaveState=2;
        return true;
    }
    if (tag>=0x11 && tag<=0x18 && tag==0x11+coopSavePage) {
        unsigned page=tag-0x10;
        for (unsigned i=0;i<9;++i) {
            unsigned offset=coopSavePage*9+i;
            if (offset<0x44)CoopSaveBuffer()[offset]=data_020a1166[7+i];
        }
        coopSavePage=page;
        data_020a1052[6]=0x90+page;
    } else if (tag==0x40 && coopSavePage==8) {
        CoopApplyHostSave();
        data_020a1052[6]=0xc0;
        coopSavePage=9;
    } else if (!tag && coopSavePage==9) {
        data_020a1052[6]=0;
        coopSaveState=1;
        return true;
    }
    return false;
}

extern u32 coopStageLoading;
extern u32 coopMenuLoading;
extern u32 coopSceneInitializing;
extern u32 coopTitleLoading;
extern u32 coopSessionEnded;
extern u32 coopDeathTriggered;
extern u32 coopGuestTutorialSkips;
extern u32 coopParticleFallbacks;
extern u32 coopParticleSplitFallbacks;
extern u32 coopStreamedLzReads;
extern u32 coopTitleRadioResetPending;
extern u32 coopStageCacheEvictions;
extern u32 coopResourceFallbacks;
extern u32 coopStreamedNarcReads;
extern u32 coopResourceFallbacksLive;
extern u32 coopResourceFallbacksPeak;

void CoopStartMatch(void *) {
    unsigned count = data_0209fc50;
    if (count < 1 || count > 4)
        return;

    PrepareVsMode();
    coopEnabled = 1;
    coopEntryRetired=0;
    coopStageLoading=coopMenuLoading=coopSceneInitializing=0;
    coopTitleLoading=0;
    coopTitleRadioResetPending=0;
    coopSessionEnded=0;
    coopDeathTriggered=0;
    coopGuestTutorialSkips=0;
    coopParticleFallbacks=0;
    coopParticleSplitFallbacks=0;
    coopResourceFallbacks=0;
    coopStreamedNarcReads=0;
    coopStreamedLzReads=0;
    coopStageCacheEvictions=0;
    coopResourceFallbacksPeak=coopResourceFallbacksLive;
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
    coopDiagnosticChordHeld=false;
#endif
    coopSaveState=coopSavePage=0;
    coopSaveEpoch=0;
    data_020a1052[6]=0;
    data_0209f2d8 = 0;
    // Story input is gated until the intro has completed. The lobby replaces
    // that introduction; begin a fresh, RAM-only Yoshi session.
    ((SaveData *)data_0209caa0)->flags2 |= 0x80;
    SetPlayerGlobals();
    SetNumPlayers(count);
    LoadLevelNoReturn(COOP_DIAGNOSTIC_START_LEVEL, 0, 1, 0);
    data_02092124 = 6;
    data_0209f228[0] = 0;
    Sound::StopLoadedMusic_Layer1(0x3c);
    data_02092778 = 1;
}

void CoopLoadCourseResources(int) {
    mHeap::Heap_t *previous = static_cast<mHeap::Heap_t *>(data_020a0eac)->SetDefault();
    LoadArchive(7);
    previous->SetDefault();
    // Downloaded children skip BOOT's story message-bank initialization.
    // Load it on the native course worker, in the persistent default heap,
    // before ENTRY cleanup destroys its temporary resources.
    if (!data_0209d708)
        func_0201fe08();
    // Stage initialization loads the story overlay set after the lobby has
    // finished. Loading it inside the lobby would risk overwriting live code.
    data_0209f2d8 = 0;
}

int CoopEntryCleanup(void *scene) {
    int result = CoopOriginalEntryCleanup(scene);
    // Archive 0 lives in ROOT on both cartridge and downloaded clients.
    // Keep that shared cache; unmount the remaining archives while ENTRY's
    // temporary heaps are still alive, before STAGE replaces them.
    if (coopEnabled)
        for (int archive = 1; archive < 13; ++archive)
            UnloadArchive(archive);
    return result;
}

void CoopLoadLevelOverlays(int level) {
    // ENTRY retains overlay 75 during ordinary VS. Story object overlay 62
    // overlaps it. Retire ENTRY only once its scene has finished cleanup and
    // STAGE is loading resources; this runtime survives outside either overlay.
    if (coopEnabled && !coopEntryRetired) {
        // Download Play's auxiliary VS heap occupies 0x0211d9c0..0x02140d80,
        // inside the story overlay range. ENTRY has finished using it now.
        // Destroy it while intact, so TITLE cannot later call a virtual
        // destructor through heap metadata overwritten by story actors.
        if (data_0209d524)func_0201a428();
        UnloadOverlay(75);
        UnloadOverlay(100);
        UnloadOverlay(102);
        coopEntryRetired = 1;
    }
    CoopOriginalLoadLevelOverlays(level);
    if (coopEnabled) {
        // Overlay 2 stays authenticated on disk. Patch only its two native
        // talk/event camera-completion reads after the story loader runs.
        extern void CoopCameraFlagsRead(void);
        extern void CoopLoadEntrances(LVL_Overlay::ObjSubTable *, int, u32);
        extern int CoopStarTutorial(void *);
        extern int CoopCourseTutorial(void *);
        extern int CoopLevelEnterInit(void *);
        extern void CoopPlayerHeadLook(void *);
        Patch(0x020c6e14,(void *)CoopStarTutorial);
        Patch(0x020c44c4,(void *)CoopCourseTutorial);
        Patch(0x020c7838,(void *)CoopLevelEnterInit);
        Patch(0x020cae10,(void *)CoopPlayerHeadLook);
        u32 target = (u32)CoopCameraFlagsRead;
        *(volatile u32 *)0x020c4364 = 0xeb000000 | ((target-0x020c436c)>>2 & 0x00ffffff);
        *(volatile u32 *)0x020c4b34 = 0xeb000000 | ((target-0x020c4b3c)>>2 & 0x00ffffff);
        target = (u32)CoopLoadEntrances;
        *(volatile u32 *)0x020fe6c8 = 0xea000000 | ((target-0x020fe6d0)>>2 & 0x00ffffff);
        // Player::Render already uses the original per-slot Yoshi material
        // parameters, initialized for story players too. Enable only its two
        // palette gates; changing the global VS rule would alter gameplay.
        *(volatile u32 *)0x020e3ae8 = 0xe3a00001; // mov r0, #1 (body)
        *(volatile u32 *)0x020e3c88 = 0xe3a00001; // mov r0, #1 (head)
        _ZN4CP1514FlushDataCacheEv();
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020c4364, 0x7d4);
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020e3ae8, 0x1a4);
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020fe6c8, 4);
    }
}

// Shared arrival results and progression messages have one owner. Retail
// starts them independently from each Player, which lets multiple return
// animations reopen the result and dialogue state machines over one another.
u32 coopGuestTutorialSkips=0;

int CoopStarTutorial(void *player) {
    if (coopEnabled && data_0209fc68 && *((u8 *)player+0x6d8)!=0) {
        ++coopGuestTutorialSkips;
        return 0;
    }
    return CoopOriginalStarTutorial(player);
}

int CoopCourseTutorial(void *player) {
    if (coopEnabled && data_0209fc68 && *((u8 *)player+0x6d8)!=0) {
        ++coopGuestTutorialSkips;
        return 0;
    }
    return CoopOriginalCourseTutorial(player);
}

int CoopLevelEnterInit(void *player) {
    if (coopEnabled && data_0209fc68 && data_0209f2fc==1 &&
        *((u8 *)player+0x6d8)!=0)
        // Native normal arrival grounds this player without starting another
        // star/key victory or loading a duplicate carried-key model.
    {
        *((u8 *)player+0x6e3)=0;
        GiveHealth(*((u8 *)player+0x6d8),0x880);
    }
    return CoopOriginalLevelEnterInit(player);
}

// 0: idle; 1: advertising loading; 2: initializing.
u32 coopStageLoading = 0;
u32 coopStageIdentity = 0;
u32 coopDeathTriggered = 0;

void CoopKillPlayer(void) {
    if (coopEnabled && data_0209fc68) {
        if (coopDeathTriggered)return;
        coopDeathTriggered=1;
    }
    CoopOriginalKillPlayer();
}

void CoopHitDeathPlane(int reason) {
    if (coopEnabled && data_0209fc68) {
        if (coopDeathTriggered)return;
        coopDeathTriggered=1;
    }
    // SetNextLevel consumes the return entrance. A second dying player must
    // not replace the first transition with an already-consumed destination.
    CoopOriginalHitDeathPlane(reason);
}
// Star selection also loads files on the main thread, starting inside the
// scene base's graphics setup, before its own InitResources is called.
u32 coopMenuLoading = 0;
u32 coopSceneInitializing = 0;
u32 coopTitleLoading = 0;
u32 coopSessionEnded = 0;
static u32 coopTitleGuest = 0;

static void CoopSessionEndedScreen() {
    // A small independent 5x7 alphabet replaces the retail error artwork:
    // a planned host quit is not a wireless failure. The resident error-screen
    // setup supplies both BG1 maps and needs no cartridge or WFS resources.
    static const u8 letters[26][5]={
        {0x7e,0x11,0x11,0x11,0x7e},{0x7f,0x49,0x49,0x49,0x36},
        {0x3e,0x41,0x41,0x41,0x22},{0x7f,0x41,0x41,0x22,0x1c},
        {0x7f,0x49,0x49,0x49,0x41},{0x7f,0x09,0x09,0x09,0x01},
        {0x3e,0x41,0x49,0x49,0x7a},{0x7f,0x08,0x08,0x08,0x7f},
        {0,0x41,0x7f,0x41,0},{0x20,0x40,0x41,0x3f,0x01},
        {0x7f,0x08,0x14,0x22,0x41},{0x7f,0x40,0x40,0x40,0x40},
        {0x7f,0x02,0x0c,0x02,0x7f},{0x7f,0x04,0x08,0x10,0x7f},
        {0x3e,0x41,0x41,0x41,0x3e},{0x7f,0x09,0x09,0x09,0x06},
        {0x3e,0x41,0x51,0x21,0x5e},{0x7f,0x09,0x19,0x29,0x46},
        {0x46,0x49,0x49,0x49,0x31},{0x01,0x01,0x7f,0x01,0x01},
        {0x3f,0x40,0x40,0x40,0x3f},{0x1f,0x20,0x40,0x20,0x1f},
        {0x3f,0x40,0x38,0x40,0x3f},{0x63,0x14,0x08,0x14,0x63},
        {0x07,0x08,0x70,0x08,0x07},{0x61,0x51,0x49,0x45,0x43}
    };
    static const char *lines[]={"SESSION ENDED","THE HOST ENDED THE GAME.",
                                "TURN YOUR DS OFF.","USE DS DOWNLOAD PLAY",
                                "TO JOIN A NEW SESSION."};
    for (unsigned screen=0;screen<2;++screen) {
        volatile u32 *tiles=(volatile u32 *)(screen?_ZN3G2S13GetBG1CharPtrEv():func_02054ea8());
        volatile u16 *map=(volatile u16 *)(screen?_ZN3G2S12GetBG1ScrPtrEv():_ZN2G212GetBG1ScrPtrEv());
        volatile u16 *palette=(volatile u16 *)(screen?0x05000400:0x05000000);
        palette[0]=0x7fff;
        palette[1]=0;
        for (unsigned tile=0;tile<28;++tile)
            for (unsigned y=0;y<8;++y) {
                u32 row=0;
                if (tile>=1 && tile<=26 && y<7)
                    for (unsigned x=0;x<5;++x)
                        if (letters[tile-1][x]&(1u<<y))row|=1u<<(4*(x+1));
                if (tile==27 && y==6)row=1u<<12;
                tiles[tile*8+y]=row;
            }
        for (unsigned cell=0;cell<1024;++cell)map[cell]=0;
        for (unsigned line=0;line<5;++line) {
            const char *text=lines[line];
            unsigned length=0;
            while (text[length])++length;
            unsigned start=(5+line*3)*32+(32-length)/2;
            for (unsigned i=0;i<length;++i)
                map[start+i]=text[i]=='.'?27:(text[i]>='A' && text[i]<='Z'?text[i]-'A'+1:0);
        }
    }
}

static void CoopConnectionLost() {
    // Story rules bypass the retail VS disconnection branch. End the file
    // server before entering its resident error screen, including when the
    // loss interrupts a synchronous WFS read during a scene transition.
    coopEnabled=coopTitleLoading=coopMenuLoading=0;
    coopSaveState=coopSavePage=0;
    func_02030a78();
    func_0201ffcc();
    func_02040aa4();
    coopSessionEnded=3;
    data_0209d4a8=0;
    func_02030500();
    func_020199a4();
}

u32 coopTitleRadioResetPending=0;
static void (*coopTitleResetCallback)(void *)=0;

void CoopTitleResetDone(void *event) {
    // The native callback continues through Disable and End. Keep the reset
    // marked in flight through that entire chain, until radio state is zero.
    if (((u16 *)event)[1])coopTitleRadioResetPending=0;
    if (coopTitleResetCallback)coopTitleResetCallback(event);
}

int CoopWirelessReset(void *callback) {
    if (!coopEnabled || !coopTitleLoading || !callback)
        return CoopOriginalWirelessReset(callback);
    if (coopTitleRadioResetPending)return 2; // Native async request accepted.
    coopTitleResetCallback=(void (*)(void *))callback;
    coopTitleRadioResetPending=1;
    int result=CoopOriginalWirelessReset((void *)CoopTitleResetDone);
    if (result!=2)coopTitleRadioResetPending=0;
    return result;
}

int CoopSceneBeforeInit(dScene_c *scene) {
    if (coopEnabled && data_0209fc68==6)CoopConnectionLost();
    if ((scene->actorID==1 || scene->actorID==8) && coopEnabled) {
        if (!coopTitleLoading && data_0209fc68) {
            // Every console must finish the transition's overlay reads
            // before shutting WFS down. Keep normal input sharing alive:
            // the native loading barrier suspends these user-byte records.
            coopTitleLoading=1;
            coopTitleRadioResetPending=0;
            coopTitleGuest=data_020a0f10!=0;
            coopMenuLoading=1;
            data_020a1052[6]=0x50;
            return 0;
        }
        if (coopTitleLoading && coopMenuLoading==1) {
            if (!coopTitleGuest) {
                bool ready=true;
                for (unsigned slot=1;slot<data_0209fc50;++slot)
                    if (data_020a1166[slot*36+6]!=0x50 &&
                        data_020a1166[slot*36+6]!=0x52)ready=false;
                if (ready)data_020a1052[6]=0x51;
            } else if (data_020a1166[6]==0x51) {
                data_020a1052[6]=0x52;
            }
            bool acknowledged=data_020a1166[6]==0x51;
            for (unsigned slot=1;slot<data_0209fc50;++slot)
                if (data_020a1166[slot*36+6]!=0x52)acknowledged=false;
            if (!acknowledged)return 0;
            func_02030a78();
            func_0201ffcc(); // Native mode change resets WM and shuts WFS down.
            coopMenuLoading=5;
            return 0;
        }
        if (coopTitleLoading && data_020a0f94!=0) {
            if (coopMenuLoading==5 && data_020a0f94==1) {
                CoopConnectionLost(); // Native failure must not leave a waiting screen.
                return 0;
            }
            // A parent disconnect can put a child back into native state 4
            // after the first mode-change update. Keep driving the native
            // teardown state machine without resubmitting an accepted async
            // reset while its native Reset/Disable/End callbacks are pending.
            if (coopMenuLoading==5 && !coopTitleRadioResetPending)func_02040724();
            return 0;
        }
        coopTitleRadioResetPending=0;
        coopEnabled=coopTitleLoading=coopMenuLoading=0;
        coopSaveState=coopSavePage=0;
        data_020a1052[6]=0;
        if (coopTitleGuest) {
            // A cartridge-free client cannot use an independent file menu.
            // The resident retail communication-ended screen needs no WFS
            // reads and remains visible until the player turns the DS off.
            coopSessionEnded=1;
            data_0209d4a8=0;
            func_02030500();
            CoopSessionEndedScreen();
            func_020199a4();
            return 0;
        }
        coopSessionEnded=2;
        SetNumPlayers(1);
        data_0209fc50=1;
        data_0209f250=gActivePlayerSlot=0;
    }
    coopSceneInitializing = coopEnabled && data_0209fc68 &&
        (scene->actorID == 3 || scene->actorID == 4);
    if (!scene->ResetFadersAndSound())
        return 0;
    if (coopEnabled && data_0209fc68 && scene->actorID == 4) {
        if (!coopMenuLoading) {
            func_0203d854();
            func_0203d918();
            coopMenuLoading = 1;
            return 0;
        }
        if (!(data_020a1160[0] & 0x2000))
            return 0;
        coopMenuLoading = 2;
        coopStageLoading = 2;
    }
    dScene_c::Initialise3dGraphics();
    return 1;
}

void CoopSceneAfterInit(dScene_c *scene, u32 success) {
    coopSceneInitializing = 0;
    if (coopEnabled && scene->actorID == 4 && coopMenuLoading == 2) {
        coopStageLoading = 0;
        func_0203d930();
        coopMenuLoading = success == 2 ? 3 : 0;
    }
    scene->dBase_c::AfterInitResources(success);
    if (scene->actorID==1 && success==2 && !data_0209fc68)coopEnabled=0;
}

static void CoopReserveParticlePool(unsigned level);

int CoopStageInit(void *scene) {
    dScStage_c *stage = (dScStage_c *)scene;
    if (!coopEnabled)
        return CoopOriginalStageInit(scene);
    if (!data_0209fc68) {
        if (!CoopLoadHostSave())return -1;
        return CoopOriginalStageInit(scene);
    }
    // The native all-loading acknowledgement stops MP data sharing. Publish
    // and acknowledge the host file while the normal packet clock is alive,
    // before advertising that this console is ready for the loading barrier.
    if (!CoopLoadHostSave())return -1;
    if (!stage->mWaitingForLoad) {
        if (!coopStageLoading) {
            coopStageIdentity = stage->uniqueID;
            coopDeathTriggered=0;
            func_0203d854();
            func_0203d918();
            coopStageLoading = 1;
            return -1;
        }
        // Host bit 0x2000 acknowledges that every client advertised loading.
        // Let NET clear ENTRY's old barrier bits before the cartridge can
        // finish its local files ahead of the downloaded clients.
        if (!(data_020a1160[0] & 0x2000))
            return -1;
    }
    if (!stage->mWaitingForLoad)
        // Keep the native resource table contiguous before model loading.
        // Reserve the larger particle array only after temporary files free.
        CoopReserveParticlePool((u8)data_02092110);
    coopStageLoading = 2;
    int result = CoopOriginalStageInit(scene);
    coopStageLoading = 0;
    if (stage->mWaitingForLoad)
        func_0203d930();
    return result;
}

u32 coopFileWaiting = 0;

int CoopReadFile(void *file, void *destination, int size, int async) {
    // SDK overlay-table and overlay-image reads call this shared reader
    // directly, before a replacement scene reaches BeforeInitResources.
    // Cover those main-thread waits as well as ordinary FS_ReadFile callers.
    if (!coopEnabled || !data_0209fc68 || async || coopFileWaiting ||
        data_020a613c != data_020a621c ||
        (!coopSceneInitializing && !coopTitleLoading && data_02092664 == 0x187))
        return CoopOriginalReadFile(file, destination, size, async);
    coopFileWaiting = 1;
    u32 *fields = (u32 *)file;
    u32 position = fields[0x28 / 4];
    CoopOriginalReadFile(file, destination, size, 1);
    // Keep only NET alive while WFS fills this file. Scene behavior/drawing
    // must not run against partially initialized or retired resources.
    while (fields[0x0c / 4] & 1) {
        if (data_0209fc68==6)CoopConnectionLost();
        func_0201ffcc();
        func_02042778();
    }
    int result = func_0205d3f4(file) ? fields[0x28 / 4] - position : -1;
    coopFileWaiting = 0;
    return result;
}

void CoopLoadEntrances(LVL_Overlay::ObjSubTable *table, int area, u32 index) {
    if (!coopEnabled) {
        CoopOriginalLoadEntrances(table, area, index);
        return;
    }
    if (!table->count || !table->entries)
        return;
    if (index >= table->count)
        index = 0;
    LVL_Overlay::StandardEntry *entries = (LVL_Overlay::StandardEntry *)table->entries;
    LVL_Overlay::StandardEntry *selected = entries + index;
    bool group = index + 4 <= table->count;
    for (unsigned i = 1; group && i < 4; ++i) {
        LVL_Overlay::StandardEntry *next = selected + i;
        int dx = next->x - selected->x;
        int dy = next->y - selected->y;
        int dz = next->z - selected->z;
        group = next->raw == selected->raw &&
                next->rot.x == selected->rot.x && next->rot.y == selected->rot.y &&
                next->rot.z == selected->rot.z &&
                (next->param & 0x787) == (selected->param & 0x787) &&
                dx >= -600 && dx <= 600 && dy >= -300 && dy <= 300 &&
                dz >= -600 && dz <= 600;
    }
    // StandardEntry's Vector3s member has a native constructor. These are
    // serialized records: copy their four words without constructing vectors.
    u32 party[16];
    for (unsigned player = 0; player < 4; ++player)
        for (unsigned word = 0; word < 4; ++word)
            party[player*4+word] = ((u32 *)(selected + (group ? player : 0)))[word];
    LVL_Overlay::ObjSubTable temporary = *table;
    temporary.count = 4;
    temporary.entries = party;
    // Native code consumes one consecutive record per player. Many story
    // doors have only one arrival record, or sit near the end of the table.
    // Retain a real four-player group when present; otherwise share the
    // selected safe arrival point, never another door or an out-of-bounds row.
    CoopOriginalLoadEntrances(&temporary, area, 0);
    // The native loader registers its table for later warps/camera setup.
    // Restore the persistent original instead of leaving our stack registered.
    func_0202b0e0(entries, table->count);
}

int CoopSaveCurrentFile(void) {
    // Default builds retain the VS scratch file in RAM. An opt-in host slot
    // must first have been read successfully and distributed to every guest.
    if (coopEnabled) {
        if (COOP_SAVE_SLOT<0 || coopSaveState!=1)return 0;
        if (data_0209fc68) {
            if (data_0209fc68==6)return 0;
            coopSaveEpoch^=1;
            unsigned ready=0x30+2*coopSaveEpoch;
            unsigned response=0x20+2*coopSaveEpoch;
            data_020a1052[6]=ready;
            if (data_020a0f10==0) {
                // Hold each replica inside this save call, but keep NET
                // exchanging user bytes until every guest is participating.
                bool waiting=true;
                while (waiting) {
                    if (data_0209fc68==6)return 0;
                    waiting=false;
                    for (unsigned slot=1;slot<data_0209fc50;++slot)
                        if (data_020a1166[slot*36+6]!=ready)waiting=true;
                    if (waiting) {
                        func_0201ffcc();
                        func_02042778();
                    }
                }
                int result=SaveData::SaveFile(COOP_SAVE_SLOT,(FileSaveData *)data_0209caa0);
                if (result)result=SaveData::SaveMinigames((MinigameSaveData *)(data_0209caa0+0x44));
                data_020a1052[6]=response+(result!=0);
            }
            while ((data_020a1166[6]&0xfe)!=response) {
                if (data_0209fc68==6)return 0;
                func_0201ffcc();
                func_02042778();
            }
            int result=data_020a1166[6]&1;
            // SaveFile marks the live block as used even on a cart failure.
            ((SaveData *)data_0209caa0)->flags1|=1;
            // A guest advertises loading only after consuming this result.
            // Thus stopping the packet clock now cannot strand an unread
            // result. Alternate the response tag between transactions so a
            // previous successful save cannot acknowledge a later failure.
            func_0203d854();
            func_0203d918();
            while (!(data_020a1160[0]&0x2000)) {
                if (data_0209fc68==6)return 0;
                func_0201ffcc();
                func_02042778();
            }
            func_0203d930();
            while (!func_020308a8()) {
                if (data_0209fc68==6)return 0;
                func_0201ffcc();
                func_02042778();
            }
            data_020a1052[6]=0;
            return result;
        }
    }
    if (!SaveData::SaveFile(data_0209caa0[0x328], (FileSaveData *)data_0209caa0))
        return 0;
    return SaveData::SaveMinigames((MinigameSaveData *)(data_0209caa0 + 0x44));
}

static bool CoopSharedCoins() {
    return coopEnabled && data_0209fc68 && data_0209f2d8==0;
}

static mHeap::Heap_t *coopParticleHeap=0;
static void *coopParticlePool=0;
u32 coopParticleFallbacks=0;
u32 coopParticleSplitFallbacks=0;
struct CoopParticleSegment {
    mHeap::Heap_t *heap;
    u8 *ptr, *cursor, *end;
};
static CoopParticleSegment coopParticleSegments[8];
u32 coopParticleSegmentCount=0;
static u32 coopParticleBudget=0,coopParticleUsed=0;
static u32 coopParticleReservedSize=0;
static u32 coopParticleReservedArena=0,coopParticlePendingArray=0;
static void *coopParticleReservedTable=0;
static mHeap::Heap_t *coopParticleTableHeap=0;
extern u8 data_02075f14[];

void *CoopAllocateParticlePool(u32 size) {
    if (!coopEnabled || !data_0209fc68)
        return _ZN6Memory13operator_new2Ej(size);
    mHeap::Heap_t *owner=Memory::defaultHeapPtr;
    mHeap::Heap_t *game=(mHeap::Heap_t *)data_020a0eac;
    u32 available=owner->MaxAllocationUnitSize();
    u32 spare=game && game!=owner ? game->MaxAllocationUnitSize() : 0;
    coopParticleSegmentCount=0;
    if (coopParticleReservedArena) {
        if (size!=coopParticleReservedArena) { Crash(); return 0; }
        // These are the native manager's only two large indexed arrays.
        // Protect the particle array from earlier small callback requests;
        // the resource table was reserved before stage loading fragmented it.
        u32 particleBytes=(size==0xa800 ? 320u : 256u)*0x44;
        if (available<particleBytes && spare>=particleBytes)owner=game;
        void *pool=owner->Allocate(particleBytes);
        coopParticleHeap=owner;
        coopParticlePool=pool;
        coopParticleSegments[0].heap=owner;
        coopParticleSegments[0].ptr=(u8 *)pool;
        coopParticleSegments[0].cursor=coopParticleSegments[0].end=(u8 *)pool+particleBytes;
        coopParticleSegments[1].heap=coopParticleTableHeap;
        coopParticleSegments[1].ptr=(u8 *)coopParticleReservedTable;
        coopParticleSegments[1].cursor=coopParticleSegments[1].end=
            (u8 *)coopParticleReservedTable+coopParticleReservedSize;
        coopParticleSegmentCount=2;
        coopParticlePendingArray=particleBytes;
        coopParticleReservedArena=0;
        coopParticleBudget=size;
        coopParticleUsed=0;
        return pool;
    }
    bool split=false;
    u32 allocated=size;
    if (available<size && spare>=size) {
        owner=game;
        ++coopParticleFallbacks;
    } else if (available<size && owner->VMemoryLeft()+
               (game && game!=owner ? game->VMemoryLeft() : 0)>=size) {
        // The native manager requests separate contiguous arrays through its
        // bump callback. Keep those arrays/counts intact across heap segments
        // when neither heap can hold the entire conservative arena reserve.
        // More than one free block in either heap can contribute. Comparing
        // only the two largest blocks rejects valid fragmented guest heaps.
        if (spare>available) { owner=game; available=spare; }
        allocated=available;
        split=true;
        ++coopParticleFallbacks;
        ++coopParticleSplitFallbacks;
    }
    void *pool=owner->Allocate(allocated);
    coopParticleHeap=owner;
    coopParticlePool=pool;
    if (split) {
        coopParticleSegments[0].heap=owner;
        coopParticleSegments[0].ptr=(u8 *)pool;
        coopParticleSegments[0].cursor=(u8 *)pool;
        coopParticleSegments[0].end=(u8 *)pool+allocated;
        coopParticleSegmentCount=1;
        coopParticleBudget=size;
        coopParticleUsed=0;
    }
    return pool;
}

static void CoopReserveParticlePool(unsigned level) {
    coopParticleReservedSize=*(u16 *)(data_02075f14+8)*32u;
    coopParticleTableHeap=Memory::defaultHeapPtr;
    coopParticleReservedTable=coopParticleTableHeap->Allocate(coopParticleReservedSize,-4);
    coopParticleReservedArena=(level==0x24 || level==0x26 || level==0x28) ? 0xa800 : 0x8c00;
}

void *CoopAllocateParticleChunk(u32 size) {
    if (!coopParticleSegmentCount) {
        // Native func_02023178 is just this pointer bump. Its first LDR is
        // PC-relative, so reproduce it rather than relocating that prologue.
        u8 *result=data_0209ee78;
        data_0209ee78=result+size;
        return result;
    }
    if (size>coopParticleBudget-coopParticleUsed) { Crash(); return 0; }
    int reserved=-1;
    if (coopParticlePendingArray && size==coopParticlePendingArray) {
        reserved=0; coopParticlePendingArray=0;
    } else if (coopParticleReservedSize && size==coopParticleReservedSize) {
        reserved=1; coopParticleReservedSize=0;
    }
    if (reserved>=0) {
        coopParticleUsed+=size;
        data_0209ee78=coopParticleSegments[reserved].end;
        return coopParticleSegments[reserved].ptr;
    }
    for (unsigned pass=0;pass<2;++pass) {
        for (unsigned i=0;i<coopParticleSegmentCount;++i) {
            CoopParticleSegment *segment=&coopParticleSegments[i];
            if ((u32)(segment->end-segment->cursor)>=size) {
                u8 *result=segment->cursor;
                segment->cursor+=size;
                coopParticleUsed+=size;
                data_0209ee78=segment->cursor;
                return result;
            }
        }
        if (pass || coopParticleSegmentCount==8)break;
        // Return unusable tails before extending the arena. Otherwise a
        // fragmented callback request can reserve more than the native pool,
        // even though every individual allocation stays inside its segment.
        for (unsigned i=0;i<coopParticleSegmentCount;++i) {
            CoopParticleSegment *segment=&coopParticleSegments[i];
            if (segment->cursor<segment->end) {
                u32 used=segment->cursor-segment->ptr;
                u32 actual=segment->heap->Reallocate(segment->ptr,used);
                if (actual)segment->end=segment->ptr+actual;
            }
        }
        mHeap::Heap_t *owner=Memory::defaultHeapPtr;
        mHeap::Heap_t *game=(mHeap::Heap_t *)data_020a0eac;
        u32 available=owner->MaxAllocationUnitSize();
        u32 remaining=coopParticleBudget-coopParticleUsed-
                      coopParticlePendingArray-coopParticleReservedSize;
        if (available<remaining && game && game!=owner) {
            u32 spare=game->MaxAllocationUnitSize();
            if (spare>available) { owner=game; available=spare; }
        }
        if (available<size)break;
        u32 allocated=available<remaining ? available : remaining;
        CoopParticleSegment *segment=&coopParticleSegments[coopParticleSegmentCount++];
        segment->heap=owner;
        segment->ptr=(u8 *)owner->Allocate(allocated);
        segment->cursor=segment->ptr;
        segment->end=segment->ptr+allocated;
    }
    Crash();
    return 0;
}

void CoopFreeParticlePool(void *ptr) {
    if (ptr && ptr==coopParticlePool && coopParticleHeap) {
        mHeap::Heap_t *owner=coopParticleHeap;
        coopParticlePool=0;
        coopParticleHeap=0;
        coopParticleReservedSize=0;
        coopParticleReservedArena=coopParticlePendingArray=0;
        coopParticleReservedTable=0;
        coopParticleTableHeap=0;
        if (coopParticleSegmentCount) {
            while (coopParticleSegmentCount) {
                CoopParticleSegment *segment=&coopParticleSegments[--coopParticleSegmentCount];
                segment->heap->Deallocate(segment->ptr);
            }
        } else owner->Deallocate(ptr);
    } else func_0203cbc0(ptr);
}

struct CoopArchiveEntry {
    void *image;
    mHeap::Heap_t *heap;
    u16 first,limit;
    const char *name,*path;
};
extern CoopArchiveEntry data_0208ecf4[];
u32 coopStreamedNarcReads=0;
u32 coopNarcOpenDiagnostic[6]={0,0,0,0,0,0};
u32 coopStageCacheEvictions=0;

void CoopLoadSkybox(void *scene) {
    // Native SharedFilePtr/LoadFile copy or decompress cached members into
    // their own buffers and close their file views. All stage model/object
    // loads have returned at this boundary. Drop the 321 KB common source
    // cache before skybox/particle/arrival peaks; later members stream through
    // the uncached NARC path rather than pinning the whole archive again.
    if (coopEnabled && data_0209fc68 && data_0208ecf4[0].image) {
        UnloadArchive(0);
        ++coopStageCacheEvictions;
    }
    CoopOriginalLoadSkybox(scene);
}

static CoopArchiveEntry *CoopUncachedArchive(u32 fileID) {
    if (!coopEnabled || !data_0209fc68 || fileID<0x8000)return 0;
    for (unsigned i=0;i<13;++i) {
        CoopArchiveEntry *entry=&data_0208ecf4[i];
        if (entry->first<=fileID && fileID<entry->limit)
            return entry->image ? 0 : entry;
    }
    return 0;
}

void *CoopResolveFile(u32 fileID) {
    // Both native callers copy/decompress the returned cached member, or
    // load it through OpenFile when null. Stream an unmounted archive member
    // instead of temporarily allocating the entire NARC beside its result.
    if (CoopUncachedArchive(fileID))return 0;
    return CoopOriginalResolveFile(fileID);
}

struct CoopArchiveIndex {
    u16 first,limit;
    u32 fileID,romTop,extentOffset;
};
extern const u8 coopNarcIndex[];
extern void *data_0209d3b4;

static int CoopOpenNarcMember(void *file,CoopArchiveEntry *entry,u32 member) {
    const CoopArchiveIndex *index=(const CoopArchiveIndex *)coopNarcIndex;
    for (unsigned i=0;i<13;++i) {
        if (entry!=&data_0208ecf4[i])continue;
        const CoopArchiveIndex *row=&index[i];
        if (row->first!=entry->first || row->limit!=entry->limit ||
            member>=(u32)(row->limit-row->first))return 0;
        // Original native file extents are authenticated and preserved by the
        // builder. Derive the member view from its verified immutable index;
        // no tiny metadata transfers or whole-container reads during behavior.
        const u32 *extent=(const u32 *)(coopNarcIndex+row->extentOffset)+member*2;
        u32 top=row->romTop+extent[0],bottom=row->romTop+extent[1];
        coopNarcOpenDiagnostic[0]=0x80;
        coopNarcOpenDiagnostic[1]=member;
        coopNarcOpenDiagnostic[2]=(u32)data_0209d3b4;
        coopNarcOpenDiagnostic[3]=row->fileID;
        coopNarcOpenDiagnostic[4]=top;
        coopNarcOpenDiagnostic[5]=bottom;
        FS_InitFile(file);
        int opened=func_0205d5e8(file,data_0209d3b4,top,bottom,row->fileID);
        if (opened)coopNarcOpenDiagnostic[0]=0;
        return opened;
    }
    return 0;
}

int CoopOpenFile(void *file,u32 fileID) {
    CoopArchiveEntry *entry=CoopUncachedArchive(fileID);
    if (entry && CoopOpenNarcMember(file,entry,fileID-entry->first)) {
        ++coopStreamedNarcReads;
        return 1;
    }
    return CoopOriginalOpenFile(file,fileID);
}

struct CoopResourceOwner {
    void *ptr;
    mHeap::Heap_t *heap;
};
static CoopResourceOwner coopResourceOwners[64];
u32 coopResourceFallbacks=0;
u32 coopResourceFallbacksLive=0;
u32 coopResourceFallbacksPeak=0;

static u32 CoopAlignedFree(mHeap::Heap_t *heap,int align) {
    // ROOT and GAME are native expanding heaps. Their allocator follows the
    // common Heap_t header; query the actual requested alignment, not just 4.
    ExpandingHeapAllocator *allocator=*(ExpandingHeapAllocator **)
        ((u8 *)heap+sizeof(mHeap::Heap_t));
    return allocator->MaxAllocatableSize(align);
}

void *CoopAllocateAlignedResource(u32 size,int align) {
    mHeap::Heap_t *root=Memory::defaultHeapPtr;
    mHeap::Heap_t *game=(mHeap::Heap_t *)data_020a0eac;
    // Restrict balancing to file buffers allocated from ROOT. Actor
    // private heaps retain their original allocation and lifetime rules.
    if (coopEnabled && data_0209fc68 && root==data_020a0e9c &&
        game && game!=root && CoopAlignedFree(root,align)<size &&
        CoopAlignedFree(game,align)>=size) {
        for (unsigned slot=0;slot<64;++slot)
            if (!coopResourceOwners[slot].ptr) {
                void *ptr=game->Allocate(size,align);
                coopResourceOwners[slot].ptr=ptr;
                coopResourceOwners[slot].heap=game;
                ++coopResourceFallbacks;
                ++coopResourceFallbacksLive;
                if (coopResourceFallbacksLive>coopResourceFallbacksPeak)
                    coopResourceFallbacksPeak=coopResourceFallbacksLive;
                return ptr;
            }
    }
    return _ZN6Memory8AllocateEji(size,align);
}

void *CoopAllocateResource(u32 size) {
    return CoopAllocateAlignedResource(size,4);
}

u32 CoopTrimResourceModel(void *ptr) {
    if (ptr)
        for (unsigned slot=0;slot<64;++slot)
            if (coopResourceOwners[slot].ptr==ptr) {
                // Shared models shed their uploaded texture tail. Keep the
                // native size and in-place resize, using the allocating heap.
                mHeap::Heap_t *owner=coopResourceOwners[slot].heap;
                owner->_Sizeof(ptr);
                return owner->Reallocate(ptr,func_020469e0(ptr));
            }
    return CoopOriginalTrimModel(ptr);
}

void CoopFreeResource(void *ptr) {
    if (ptr)
        for (unsigned slot=0;slot<64;++slot)
            if (coopResourceOwners[slot].ptr==ptr) {
                mHeap::Heap_t *owner=coopResourceOwners[slot].heap;
                coopResourceOwners[slot].ptr=0;
                coopResourceOwners[slot].heap=0;
                --coopResourceFallbacksLive;
                owner->Deallocate(ptr);
                return;
            }
    _ZN6Memory10DeallocateEPv(ptr);
}

struct CoopLzReader {
    void *file;
    u32 remaining,at,count;
    u8 storage[512+31];
    u8 Read() {
        u8 *buffer=(u8 *)(((u32)storage+31)&~31u);
        if (at==count) {
            count=remaining<512 ? remaining : 512;
            // CARD reads may DMA into this window on hardware. Keep cache
            // maintenance inside its own aligned storage, away from fields.
            _ZN4CP1527FlushAndInvalidateDataCacheEjj((u32)buffer,count);
            if (!count || FS_ReadFile(file,buffer,count)!=(int)count) {
                Crash(); return 0;
            }
            remaining-=count;
            at=0;
        }
        return buffer[at++];
    }
};

u32 coopStreamedLzReads=0;
void *CoopLoadDiskFile(void *file,int flush) {
    if (!coopEnabled || !data_0209fc68)return CoopOriginalLoadDiskFile(file,flush);
    u32 length=((u32 *)file)[9]-((u32 *)file)[8];
    if (length<=512)return CoopOriginalLoadDiskFile(file,flush);
    u32 header[2];
    if (FS_ReadFile(file,header,8)!=8) { Crash(); return 0; }
    if (!func_02018568(header) || (header[1]&255)!=0x10) {
        func_0205d368(file,0,0);
        return CoopOriginalLoadDiskFile(file,flush);
    }
    // Native LoadFile keeps the entire compressed file beside its output.
    // Decode its ordinary LZ10 stream with a bounded input window instead.
    u32 size=header[1]>>8;
    if (!size || size>0x400000) { Crash(); return 0; }
    u8 *output=(u8 *)CoopAllocateResource(size);
    CoopLzReader input;
    input.file=file;
    input.remaining=length-8;
    input.at=input.count=0;
    u32 written=0;
    while (written<size) {
        unsigned flags=input.Read();
        for (unsigned bit=0x80;bit && written<size;bit>>=1) {
            if (flags&bit) {
                unsigned first=input.Read(),second=input.Read();
                unsigned count=(first>>4)+3,distance=((first&15)<<8)+second+1;
                if (distance>written || count>size-written) { Crash(); return 0; }
                while (count--) { output[written]=output[written-distance]; ++written; }
            } else output[written++]=input.Read();
        }
    }
    FS_CloseFile(file);
    func_02018770();
    if (flush)_ZN4CP1514FlushDataCacheEjj((u32)output,size);
    ++coopStreamedLzReads;
    return output;
}

s16 CoopNumCoins(void) {
    if (CoopSharedCoins())return data_0209f358[0];
    // Preserve the native sum outside story co-op. Its first instruction is
    // PC-relative, so reproduce this small accessor instead of relocating it.
    s16 total=data_0209f358[0];
    for (unsigned slot=1;slot<data_0209f21c;++slot)
        total=(s16)(total+data_0209f358[slot]);
    return total;
}

void CoopGiveCoins(int player, int amount) {
    if (!CoopSharedCoins()) {
        CoopOriginalGiveCoins(player,amount);
        return;
    }
    if ((unsigned)player>=4)return;
    int total=data_0209f358[0]+amount;
    if (total<0)total=0;
    if (total>255)total=255;
    for (unsigned slot=0;slot<4;++slot)data_0209f358[slot]=(s16)total;
    // Native GiveCoins checks the collector's individual counter to spawn
    // the hundred-coin star. Mirror the team total first, then retain that
    // native check at the actual collector's position. Coin healing remains
    // on the original collecting Player in daCoin_c.
    CoopOriginalGiveCoins(player,0);
}

void CoopMessageUpdate(void) {
    // Message::Update also runs from display/render helpers, after actor
    // updates restore the local controller. Every shared text window and
    // choice must consume the same host packet regardless of that caller.
    u8 previous=gActivePlayerSlot;
    if (coopEnabled)gActivePlayerSlot=0;
    CoopOriginalMessageUpdate();
    gActivePlayerSlot=previous;
}

static u8 CoopCameraOwner(void) {
    return coopEnabled && data_0209fc68 ? data_020a0f10 : data_0209f250;
}

int CoopCameraFar(void *camera,unsigned player) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    int result=CoopOriginalCameraFar(camera,player);
    data_0209f250=previous;
    return result;
}

void CoopCameraNear(void *camera,unsigned player) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    CoopOriginalCameraNear(camera,player);
    data_0209f250=previous;
}

void CoopCameraBehind(void *camera,unsigned player) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    CoopOriginalCameraBehind(camera,player);
    data_0209f250=previous;
}

void CoopCameraFirstPerson(void *camera,unsigned player) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    CoopOriginalCameraFirstPerson(camera,player);
    data_0209f250=previous;
}

void CoopCameraNormal(void *camera,unsigned player) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    CoopOriginalCameraNormal(camera,player);
    data_0209f250=previous;
}

void CoopPlayerHeadLook(void *player) {
    unsigned slot=*((u8 *)player+0x6d8);
    if (!coopEnabled || !data_0209fc68 || !data_0209f318 || slot>=4) {
        CoopOriginalPlayerHeadLook(player);
        return;
    }
    // Head pitch also controls the castle's look-up entrance. Each replica
    // must use this player's echoed pitch, independent of its displayed view.
    u8 previous=data_0209f250;
    s16 pitch=data_0209f318->mAngleX;
    data_0209f250=(u8)slot;
    data_0209f318->mAngleX=(s16)(data_020a1166[slot*36+7] |
                               data_020a1166[slot*36+8]<<8);
    CoopOriginalPlayerHeadLook(player);
    data_0209f318->mAngleX=pitch;
    data_0209f250=previous;
}

void CoopCameraFov(dCamera_c *camera,u8 player,int mode) {
    // Native func_0200ca14 starts with a PC-relative literal load. Preserve
    // its complete flag semantics rather than relocating that instruction.
    if (player==CoopCameraOwner())camera->mFlags|=mode ? 0x10000 : 0x20000;
}

int CoopSceneBefore(void *scene) {
    if (coopEnabled && data_0209fc68==6)CoopConnectionLost();
    // Keep the cartridge on the same menu until downloaded clients have
    // finished their wireless reads. Otherwise it can enter the next stage
    // while they are still initializing and their synchronous reads fail.
    unsigned id = ((dScene_c *)scene)->actorID;
    if (coopEnabled && id==4 && coopMenuLoading==3) {
        if (!func_020308a8())
            return 0;
        coopMenuLoading = 0;
    }
    int result = CoopOriginalSceneBefore(scene);
    // Shared scene decisions consume the host's synchronized controller.
    // Player behavior still selects each actor's own input record.
    if (result && coopEnabled && (id == 3 || id == 4)) {
        gActivePlayerSlot = 0;
        data_0209f250 = 0;
        if (data_0209fc68)
            data_0209e650 = data_020a1154[0] ^ 0x6d2b79f5;
        // Native story flags occupy NET user bytes 0..4 and 16. Byte 5
        // carries the host camera's completion status; every replica,
        // including the host, consumes the same echoed packet below.
        if (data_0209f318) {
            data_020a1052[5] = (data_0209f318->mFlags & 0x8000) != 0;
            // Initial host-file transfer owns bytes7..15 only while scenes
            // are held at initialization. In gameplay7..8 carry local pitch.
            if (COOP_SAVE_SLOT<0 || coopSaveState==1) {
                data_020a1052[7]=(u8)data_0209f318->mAngleX;
                data_020a1052[8]=(u8)(data_0209f318->mAngleX>>8);
            }
        }
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
        // Explicit test builds only: the host's synchronized L+R+X
        // requests the next native stage. Use the normal transition/loader,
        // never a frontend write to scenes, actors, positions or progress.
        bool chord=(data_020a0e58[0] & 0x700)==0x700;
        if (id==3 && chord && !coopDiagnosticChordHeld) {
            unsigned next=(unsigned)data_0209f2f8+1;
            if (next==41)++next; // Unused native stage.
            if (next>=52)next=1;
            LoadLevelNoReturn(next,0,1,0);
        }
        coopDiagnosticChordHeld=chord;
#endif
    }
    return result;
}

u32 CoopSharedCameraFlags(dCamera_c *camera) {
    u32 flags = camera->mFlags;
    if (coopEnabled && data_0209fc68)
        flags = (flags & ~0x8000) | ((data_020a1166[5] & 1) << 15);
    return flags;
}

// Replace an LDR r0,[r0,#0x154] immediately followed by ANDS. Preserve all
// other volatile registers; the native function already saves its caller LR.
__asm void CoopCameraFlagsRead(void) {
    stmfd sp!, {r1-r3, r12, lr}
    bl CoopSharedCameraFlags
    ldmfd sp!, {r1-r3, r12, pc}
}

void CoopSceneAfter(dScene_c *scene, u32 success) {
    if (coopEnabled && (scene->actorID == 3 || scene->actorID == 4)) {
        data_0209f250 = data_020a0f10;
        gActivePlayerSlot = data_020a0f10;
    }
    if (scene->actorID==3 && CoopSharedCoins())
        // The level-clear tally clears slot 0. Keep local coin displays and
        // later per-player reads on the same team total after that reset.
        for (unsigned slot=1;slot<4;++slot)data_0209f358[slot]=data_0209f358[0];
    scene->fBase_c::AfterBehavior(success);
}

u32 coopBehaviorActor = 0;
u32 coopBehaviorVisibility = 0;
static u32 coopBehaviorHealthSaved = 0;
static u8 coopBehaviorHealth = 0;

int CoopActorBefore(void *actor) {
    coopBehaviorActor = 0;
    coopBehaviorHealthSaved = 0;
    // Doors and NPCs run separately from the scene. Their single-player
    // interaction paths must choose the same player and controller on every
    // replica. Player::Behavior still selects its own synchronized input.
    if (coopEnabled) {
        gActivePlayerSlot = 0;
        data_0209f250 = 0;
    }
    int result = CoopOriginalActorBefore(actor);
    if (result && coopEnabled && data_0209fc68 && data_0209f2fc==1 &&
        data_0209f394[0] && actor!=data_0209f394[0]) {
        for (unsigned slot=1;slot<4;++slot)
            if (data_0209f394[slot]==actor && *((u8 *)actor+0x709) &&
                (*((u8 *)data_0209f394[0]+0x709) || data_0209f20c || data_0209d660))
                // Spectators finish their ordinary arrival only after the
                // leader's result menu and shared dialogue have completed.
                result=0;
    }
    if (result && coopEnabled && data_0209fc68) {
        for (unsigned slot=0;slot<4;++slot)
            if (data_0209f394[slot]==actor) {
                // Retail death states wait for the displayed HUD meter to
                // reach zero. That meter belongs to a different local player
                // on each guest. Use this actor's health during its behavior,
                // then restore the local meter for HUD animation/rendering.
                volatile u8 *meter=(volatile u8 *)0x0211117c;
                coopBehaviorHealth=*meter;
                coopBehaviorHealthSaved=1;
                *meter=(u8)(data_02092144[slot]>>8);
                break;
            }
        // NET already forces ordinary actors to update beyond the local
        // camera. Their behavior must also see consistent visibility: Goomba
        // stuck counters, for example, otherwise depend on each player's view.
        // Preserve the native clip result for this console's later rendering.
        coopBehaviorActor = (u32)actor;
        coopBehaviorVisibility = ((dActor_c *)actor)->mFlags & 0x38;
        ((dActor_c *)actor)->mFlags &= ~0x38;
        // Local cameras and visual effects consume different random draws.
        // Give each actor update a stream derived from the shared input frame
        // and its stage-relative identity, rather than those local draws.
        // The title/BOOT scenes allocate different numbers of base objects;
        // subtracting STAGE's identity removes that pre-session difference.
        u32 identity = ((dActor_c *)actor)->uniqueID - coopStageIdentity;
        u32 seed = data_020a1154[0] ^ (identity * 0x9e3779b9);
        seed ^= seed >> 16;
        seed *= 0x85ebca6b;
        data_0209e650 = seed ^ (seed >> 13);
    }
    if (!result && coopEnabled) {
        gActivePlayerSlot = data_020a0f10;
        data_0209f250 = data_020a0f10;
    }
    return result;
}

void CoopActorAfter(dActor_c *actor, u32 success) {
    if (coopBehaviorHealthSaved) {
        *(volatile u8 *)0x0211117c=coopBehaviorHealth;
        coopBehaviorHealthSaved=0;
    }
    if (coopBehaviorActor == (u32)actor) {
        actor->mFlags = (actor->mFlags & ~0x38) | coopBehaviorVisibility;
        coopBehaviorActor = 0;
    }
    if (coopEnabled) {
        gActivePlayerSlot = data_020a0f10;
        data_0209f250 = data_020a0f10;
    }
    actor->fBase_c::AfterBehavior(success);
}

static void Patch(u32 address, void *target) {
    *(volatile u32 *)address = 0xea000000 | (((u32)target-address-8)>>2 & 0x00ffffff);
    // Invalidate every installed branch, including SDK hooks outside the
    // scene/actor span. New hook sites must not depend on a fixed cache range.
    _ZN4CP1514FlushDataCacheEjj(address, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(address, 4);
}

static void PatchCall(u32 address, void *target) {
    *(volatile u32 *)address=0xeb000000 | (((u32)target-address-8)>>2 & 0x00ffffff);
    _ZN4CP1514FlushDataCacheEjj(address,4);
    _ZN4CP1526InvalidateInstructionCacheEjj(address,4);
}

void CoopRuntimeDispatch(unsigned operation, u32 argument) {
    Patch(0x02017060,(void *)CoopTrimResourceModel);
    Patch(0x020186c0,(void *)CoopResolveFile);
    Patch(0x020185c0,(void *)CoopOpenFile);
    Patch(0x0201834c,(void *)CoopLoadDiskFile);
    Patch(0x02062200,(void *)CoopWirelessReset);
    Patch(0x0202b0fc,(void *)CoopLoadSkybox);
    Patch(0x0200d0ac,(void *)CoopCameraFar);
    Patch(0x0200d064,(void *)CoopCameraNear);
    Patch(0x0200d304,(void *)CoopCameraBehind);
    Patch(0x0200ca14,(void *)CoopCameraFov);
    Patch(0x0200d7e0,(void *)CoopCameraFirstPerson);
    Patch(0x0200d81c,(void *)CoopCameraNormal);
    Patch(0x02023178,(void *)CoopAllocateParticleChunk);
    PatchCall(0x02022f88,(void *)CoopAllocateParticlePool);
    PatchCall(0x020231bc,(void *)CoopFreeParticlePool);
    PatchCall(0x02017c98,(void *)CoopAllocateResource);
    PatchCall(0x02017cd8,(void *)CoopAllocateAlignedResource);
    PatchCall(0x02017d40,(void *)CoopAllocateAlignedResource);
    PatchCall(0x02017da8,(void *)CoopAllocateResource);
    PatchCall(0x02017dcc,(void *)CoopAllocateResource);
    PatchCall(0x02017c3c,(void *)CoopFreeResource);
    PatchCall(0x02017dc4,(void *)CoopFreeResource);
    PatchCall(0x02017de4,(void *)CoopFreeResource);
    // The plain LoadFile path (including map graphics) also holds a scratch
    // copy while allocating its result. Track both buffers and its release.
    PatchCall(0x020181c4,(void *)CoopAllocateResource);
    PatchCall(0x02018204,(void *)CoopAllocateAlignedResource);
    PatchCall(0x02018378,(void *)CoopAllocateAlignedResource);
    PatchCall(0x020183c4,(void *)CoopAllocateResource);
    PatchCall(0x020183e0,(void *)CoopAllocateResource);
    PatchCall(0x020183fc,(void *)CoopFreeResource);
    PatchCall(0x0201815c,(void *)CoopFreeResource);
    // Reapply the ENTRY hook when that overlay is reloaded for a new party.
    Patch(0x02013b9c, (void *)CoopSaveCurrentFile);
    Patch(0x0201c0b8, (void *)CoopMessageUpdate);
    Patch(0x02029b30, (void *)CoopKillPlayer);
    Patch(0x02029b84, (void *)CoopHitDeathPlane);
    Patch(0x0202a770, (void *)CoopNumCoins);
    Patch(0x0202a7b8, (void *)CoopGiveCoins);
    Patch(0x0202ded4, (void *)CoopLoadLevelOverlays);
    Patch(0x0202cc0c, (void *)CoopStageInit);
    Patch(0x0205d688, (void *)CoopReadFile);
    Patch(0x0202e638, (void *)CoopSceneBeforeInit);
    Patch(0x0202e62c, (void *)CoopSceneAfterInit);
    Patch(0x0202e3d4, (void *)CoopSceneBefore);
    Patch(0x0202e3c8, (void *)CoopSceneAfter);
    Patch(0x0211a210, (void *)CoopEntryCleanup);
    Patch(0x02010fd4, (void *)CoopActorBefore);
    Patch(0x02010fc8, (void *)CoopActorAfter);
    if (operation == 0) {
        coopEntryRetired = coopStageLoading = coopMenuLoading = coopFileWaiting = coopSceneInitializing = 0;
        CoopLoadCourseResources((int)argument);
    } else if (operation == 1) {
        CoopStartMatch((void *)argument);
    }
}
}
