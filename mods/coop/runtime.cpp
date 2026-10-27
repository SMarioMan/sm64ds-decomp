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
#include "dMap_c.h"
#include "OAM.h"
#ifdef COOP_EXPERIMENTAL_PAINTING_MATH
#include "daPicGate_c.h"
#endif
#include "LVL_Overlay.h"
#include "ExpandingHeapAllocator.h"
#if defined(COOP_DIAGNOSTIC_RENDER_COST) || defined(COOP_DIAGNOSTIC_PLAYER_COST)
#include "dExtSimpleModel_c.h"
#include "dExtShadowModel_c.h"
#include "dCc_c.h"
#endif
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
#include "dCc_c.h"
#endif

namespace Memory { extern mHeap::Heap_t *defaultHeapPtr; }

// Test builds can enter a later stage through the normal native loader.
// Shipping builds always start at the castle grounds.
#ifndef COOP_DIAGNOSTIC_START_LEVEL
#define COOP_DIAGNOSTIC_START_LEVEL 1
#endif
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
static bool coopDiagnosticChordHeld=false;
extern "C" u16 data_020a0e58[];
#endif

extern "C" {
void PrepareVsMode(void);
void SetPlayerGlobals(void);
void SetNumPlayers(int count);
void *_ZN6Memory13operator_new2Ej(u32 size);
void UnloadOverlay(int index);
int CoopOriginalEntryCleanup(void *scene);
void CoopOriginalLoadLevelOverlays(int level);
int CoopOriginalStageInit(void *scene);
int CoopOriginalMinimapBehavior(dMap_c *map);
int CoopOriginalMinimapRender(dMap_c *map);
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
// local extern: only decl_common.h's untyped catch-all declares this SDK clock.
unsigned long long func_02059650(void);
int CoopOriginalStageRender(void *scene);
void CoopCostBodyRender(void *model,const Vector3 *scale);
void CoopCostHeadRender(void *model,const Vector3 *scale);
#endif
#ifdef COOP_EXPERIMENTAL_COLLISION_BROADPHASE
// local extern: no typed shared header declares this native vector function.
int Vec3_HorzLen(const Vector3 *vector);
#endif
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
void CoopCollisionProcess(void);
void CoopReleaseCollisionPlan(unsigned pressure);
void CoopCollisionMakeRoom(mHeap::Heap_t *heap,u32 size,int align);
void CoopCollisionPairContinue(void);
void CoopCollisionPairDone(void);
// local extern: no shared header declares this native collision notifier.
void func_02014f44(u32 owner,dCc_c *node);
#endif
int CoopOriginalSceneBefore(void *scene);
int CoopOriginalActorBefore(void *actor);
int CoopOriginalActorBeforeInit(void *actor);
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
void func_02012790(unsigned sound);
void CoopOriginalCameraNear(void *camera,unsigned player);
void CoopOriginalCameraBehind(void *camera,unsigned player);
void CoopOriginalCameraFirstPerson(void *camera,unsigned player);
void CoopOriginalCameraNormal(void *camera,unsigned player);
void CoopOriginalCameraLookTarget(void *camera,unsigned player,void *target);
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
#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
u32 _ZN3IRQ7DisableEv(void);
void _ZN3IRQ7RestoreEj(u32 state);
void CpuCopy8(const void *source,void *destination,u32 size);
void *CoopOriginalHeapAllocate(mHeap::Heap_t *heap,u32 size,int align);
int CoopOriginalStageCleanup(void *scene);
u32 CoopOriginalHeapReallocate(mHeap::Heap_t *heap,void *ptr,u32 size);
void CoopFlushAnimationReadCache(void);
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
void CoopTraceAnimationFlush(unsigned reason);
#else
#define CoopTraceAnimationFlush(reason) ((void)0)
#endif
#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
void CoopAnimationTransitionCleanup(void);
#endif
#endif
void func_02040724(void);
int CoopOriginalWirelessReset(void *callback);
int CoopOriginalConnectionUpdate(void);
extern u16 data_020a0f1c;
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
extern u8 data_02092128[];
extern s8 data_02092114;
extern u8 data_0209f2d8;
extern u8 data_0209f250;
extern u8 data_0209f2fc;
extern u8 data_0209f2f8;
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
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
u32 coopDiagnosticConnectionFailure[8]={0,0,0,0,0,0,0,0};
u32 coopDiagnosticGameplayRead[20]={0};
u32 coopDiagnosticSlowGameplayRead[20]={0};
extern u32 coopFileWaiting;
#endif

#ifdef COOP_DIAGNOSTIC_RENDER_COST
u32 coopDiagnosticRenderCount=0;
u32 coopDiagnosticRenderCosts[64][12]={{0}};

static void CoopDiagnosticGeometryIdle() {
    // Measurement builds drain pending geometry before reading hardware RAM
    // counts. This changes scheduling: never use their cadence as a benchmark.
    while (*(volatile u32 *)0x04000600&0x08000000) {}
}

static u32 *CoopDiagnosticRenderBegin(unsigned kind,unsigned slot) {
    CoopDiagnosticGeometryIdle();
    u32 *row=coopDiagnosticRenderCosts[coopDiagnosticRenderCount&63];
    row[0]=*(volatile u32 *)0x020a1040;
    row[1]=kind;
    row[2]=slot;
    row[3]=*(volatile u16 *)0x04000604;
    row[5]=*(volatile u16 *)0x04000606;
    row[7]=(*(volatile u16 *)0x04000060>>13)&1;
    row[9]=*(volatile u32 *)0x027ffc3c;
    row[11]=data_020a0f10;
    return row;
}

static void CoopDiagnosticRenderFinish(u32 *row) {
    CoopDiagnosticGeometryIdle();
    row[4]=*(volatile u16 *)0x04000604;
    row[6]=*(volatile u16 *)0x04000606;
    row[8]=(*(volatile u16 *)0x04000060>>13)&1;
    row[10]=*(volatile u32 *)0x027ffc3c;
    ++coopDiagnosticRenderCount;
}

static unsigned CoopDiagnosticModelSlot(void *model,unsigned part) {
    for (unsigned slot=0;slot<4;++slot) {
        u8 *actor=(u8 *)data_0209f394[slot];
        if ((u32)actor<0x02000000 || (u32)actor>=0x023ff800)continue;
        void **models=(void **)(actor+(part==2 ? 0xdc : 0x154));
        for (unsigned index=0;index<(part==2 ? 5 : 8);++index)
            if (models[index]==model)return slot;
    }
    return 0xffffffff;
}

static void CoopDiagnosticPlayerPart(void *model,const Vector3 *scale,unsigned part) {
    u32 *row=coopEnabled && data_0209fc68==4 ?
        CoopDiagnosticRenderBegin(part,CoopDiagnosticModelSlot(model,part)) : 0;
    ((dExtSimpleModel_c *)model)->dExtSimpleModel_c::Render(scale);
    if (row)CoopDiagnosticRenderFinish(row);
}
void CoopDiagnosticBodyRender(void *model,const Vector3 *scale) {
    CoopDiagnosticPlayerPart(model,scale,2);
}
void CoopDiagnosticHeadRender(void *model,const Vector3 *scale) {
    CoopDiagnosticPlayerPart(model,scale,3);
}
void CoopDiagnosticOpaqueRender(dScStage_c *scene) {
    u32 *row=coopEnabled && data_0209fc68==4 ? CoopDiagnosticRenderBegin(0,0xffffffff) : 0;
    scene->RenderModel();
    if (row)CoopDiagnosticRenderFinish(row);
}
void CoopDiagnosticTransparentRender(dScStage_c *scene) {
    u32 *row=coopEnabled && data_0209fc68==4 ? CoopDiagnosticRenderBegin(1,0xffffffff) : 0;
    scene->RenderModelTransparent();
    if (row)CoopDiagnosticRenderFinish(row);
}
#endif

void CoopStartMatch(void *) {
#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
    CoopTraceAnimationFlush(7);
    CoopFlushAnimationReadCache();
#elif defined(COOP_EXPERIMENTAL_COLLISION_PLAN)
    CoopReleaseCollisionPlan(0);
#endif
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
#ifdef COOP_DIAGNOSTIC_RENDER_COST
    coopDiagnosticRenderCount=0;
#endif
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
    coopDiagnosticChordHeld=false;
    for (unsigned field=0;field<8;++field)coopDiagnosticConnectionFailure[field]=0;
    for (unsigned field=0;field<20;++field) {
        coopDiagnosticGameplayRead[field]=0;
        coopDiagnosticSlowGameplayRead[field]=0;
    }
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
#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
    CoopAnimationTransitionCleanup();
#elif defined(COOP_EXPERIMENTAL_ANIMATION_CACHE)
    CoopTraceAnimationFlush(1);
    CoopFlushAnimationReadCache();
#endif
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
        extern void *CoopAllocatePaintingMesh(u32);
        // Object overlays reuse these addresses. Match the verified PicGate
        // allocation sequence before touching overlay80's resident code.
        if (*(u32 *)0x02126e08==0xe3a00018 &&
            *(u32 *)0x02126e0c==0xe0000091 &&
            *(u32 *)0x02126e10==0xebfc5770 &&
            *(u32 *)0x02126e14==0xe58401a0)
        {
            PatchCall(0x02126e10,(void *)CoopAllocatePaintingMesh);
#ifdef COOP_EXPERIMENTAL_PAINTING_MATH
            extern int CoopPaintingHeight(daPicGate_c *,int);
            Patch(0x02125bb0,(void *)CoopPaintingHeight);
#endif
        }
        // Overlay 2 stays authenticated on disk. Patch native story camera
        // reads and state helpers only after the authenticated loader runs.
        extern void CoopCameraFlagsRead(void);
        extern void CoopPersonalCameraFlagsRead(void);
        extern void CoopCannonPitchRead(void);
        extern void CoopLoadEntrances(LVL_Overlay::ObjSubTable *, int, u32);
        extern int CoopStarTutorial(void *);
        extern int CoopCourseTutorial(void *);
        extern int CoopLevelEnterInit(void *);
        extern void CoopPlayerHeadLook(void *);
        extern int CoopMinimapBehavior(dMap_c *);
        extern int CoopMinimapRender(dMap_c *);
        Patch(0x020fa690,(void *)CoopMinimapBehavior);
        Patch(0x020f9e98,(void *)CoopMinimapRender);
        Patch(0x020c6e14,(void *)CoopStarTutorial);
        Patch(0x020c44c4,(void *)CoopCourseTutorial);
        Patch(0x020c7838,(void *)CoopLevelEnterInit);
        Patch(0x020cae10,(void *)CoopPlayerHeadLook);
        PatchCall(0x020df6a0,(void *)CoopPersonalCameraFlagsRead);
        PatchCall(0x020def88,(void *)CoopCannonPitchRead);
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
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
        PatchCall(0x020e3b4c,(void *)CoopCostBodyRender);
        PatchCall(0x020e3cfc,(void *)CoopCostHeadRender);
#endif
#ifdef COOP_DIAGNOSTIC_RENDER_COST
        PatchCall(0x020e3b4c,(void *)CoopDiagnosticBodyRender);
        PatchCall(0x020e3cfc,(void *)CoopDiagnosticHeadRender);
#endif
        _ZN4CP1514FlushDataCacheEv();
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020c4364, 0x7d4);
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020e3ae8, 0x1a4);
        _ZN4CP1526InvalidateInstructionCacheEjj(0x020fe6c8, 4);
    }
}

#ifdef COOP_EXPERIMENTAL_PAINTING_MATH
extern "C" int CoopOriginalPaintingHeight(daPicGate_c *,int);
// local extern: no shared header declares this fixed-point scalar helper.
extern "C" int _ZN4cstd4fdivEii(int,int);
// local extern: no typed shared header declares the native signed divider.
extern "C" int CoopPaintingDivide(int,int);
struct CoopPaintingCoefficients {
    u32 valid,timer;
    s32 params[5],speed,amplitude,slope;
};
static CoopPaintingCoefficients coopPaintingCoefficients={0};
u32 coopPaintingMathStats[3]={0}; // coefficient hits, fills, native fallback.
static s32 CoopPaintingMultiply(s32 a,s32 b) {
    return (s32)(((s64)a*b+0x800)>>12);
}
int CoopPaintingHeight(daPicGate_c *painting,int distance) {
    u32 pointer=(u32)painting->mWaveParams;
    if (!coopEnabled || data_0209fc68!=4 || ((painting->param1>>13)&3)!=1 ||
        pointer<0x02000000 || pointer>0x023fffec || (pointer&3)) {
        ++coopPaintingMathStats[2];
        return CoopOriginalPaintingHeight(painting,distance);
    }
    unsigned timer=painting->mWaveTimer;
    if (!timer)return 0;
    const s32 *params=(const s32 *)pointer;
    if (!params[2] || !params[3] || !params[4] ||
        (params[0]==(s32)0x80000000 && params[4]==-1)) {
        ++coopPaintingMathStats[2];
        return CoopOriginalPaintingHeight(painting,distance);
    }
    CoopPaintingCoefficients *cache=&coopPaintingCoefficients;
    bool same=cache->valid && cache->timer==timer;
    for (unsigned i=0;i<5 && same;++i)same=cache->params[i]==params[i];
    if (!same) {
        cache->valid=0;
        cache->timer=timer;
        for (unsigned i=0;i<5;++i)cache->params[i]=params[i];
        // Exactly the three native invariant divisions, in native order.
        cache->speed=_ZN4cstd4fdivEii(0xffff,params[2]);
        s32 quotient=CoopPaintingDivide(params[0],params[4]);
        cache->amplitude=(s32)((u32)params[0]-(u32)quotient*((u32)params[4]-timer));
        cache->slope=_ZN4cstd4fdivEii(cache->amplitude,params[3]);
        cache->valid=1;++coopPaintingMathStats[1];
    } else ++coopPaintingMathStats[0];
    s16 phase=(s16)((u32)CoopPaintingMultiply(distance,cache->speed)-(s32)painting->mWavePhase);
    s32 sum=(s32)((u32)cache->amplitude+(u32)CoopPaintingMultiply((s32)(0u-(u32)cache->slope),distance));
    if (sum<0)sum=0;
    const s16 *sine=(const s16 *)0x02082214;
    return CoopPaintingMultiply(sine[((u16)phase>>4)*2],sum);
}
#endif

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
    u8 arrival=*((u8 *)player+0x6e3);
    bool sharedResult=arrival==4 || arrival==8 || arrival==11 ||
                      arrival==15 || arrival==16 || arrival==18;
    bool leaderResult=(data_0209f2fc==1 && sharedResult) ||
                      (data_0209f2fc==0 && arrival==8);
    if (coopEnabled && data_0209fc68 && leaderResult &&
        *((u8 *)player+0x6d8)!=0) {
        // Some castle entrances use celebration pose8 even for an ordinary
        // transition. Multiple celebrations can freeze the remaining entrants
        // behind the shared tally. Keep that pose with the leader as well.
        // Preserve native water, flight, falling and other arrivals. Grounding
        // a flying guest with no floor produces INT_MIN Y and a party exit.
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
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
    if (coopEnabled) {
        // Preserve the first native reason before SDK teardown can replace it.
        coopDiagnosticConnectionFailure[0]=data_020a0f1c;
        coopDiagnosticConnectionFailure[1]=data_020a0f94;
        coopDiagnosticConnectionFailure[2]=data_0209fc68;
        coopDiagnosticConnectionFailure[3]=data_020a1154[0];
        coopDiagnosticConnectionFailure[4]=data_0209f2f8;
        coopDiagnosticConnectionFailure[5]=*(volatile u8 *)0x0209f2c4;
        coopDiagnosticConnectionFailure[6]=*(volatile u32 *)0x0209d50c;
        coopDiagnosticConnectionFailure[7]=coopFileWaiting;
    }
#endif
#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
    CoopTraceAnimationFlush(6);
    CoopFlushAnimationReadCache();
#endif
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

u32 coopLoadingChecksumGraceClears=0;

int CoopConnectionUpdate(void) {
    if (coopEnabled && data_0209fc68>=3 && data_0209fc68<5 &&
        (data_020a0f1c&8)) {
        // Native NET clears the rendered wing-state checksum when this
        // console advertises loading. A peer that receives that packet before
        // entering its own loading phase must allow the same transition grace.
        // Keep checksum failures fatal in gameplay, and retain every radio,
        // timeout and membership error even during loading.
        bool loading=(*(volatile u16 *)0x020a104c&0x4000)!=0;
        for (unsigned slot=0;slot<data_0209fc50 && slot<4;++slot)
            if ((data_020a1160[slot*18]&0xc000)==0xc000)loading=true;
        if (loading) {
            data_020a0f1c&=~8;
            ++coopLoadingChecksumGraceClears;
        }
    }
    return CoopOriginalConnectionUpdate();
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
#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
        CoopTraceAnimationFlush(8);
        CoopFlushAnimationReadCache();
#endif
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
    if (coopEnabled && data_0209fc68==6)CoopConnectionLost();
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

#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
int CoopReadFileUncached(void *file, void *destination, int size, int async) {
#else
int CoopReadFile(void *file, void *destination, int size, int async) {
#endif
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
    if (coopEnabled && data_0209fc68==4 && !async && !coopFileWaiting &&
        data_020a613c==data_020a621c && !coopSceneInitializing &&
        !coopTitleLoading && data_02092664==0x187 &&
        !(*(volatile u16 *)0x020a104c&0x4000)) {
        // Observe the existing synchronous gameplay path without changing it.
        // SDK VBlank time keeps advancing while the main thread waits for WFS.
        u32 *words=(u32 *)file;
        u32 start=*(volatile u32 *)0x027ffc3c;
        if (!coopDiagnosticGameplayRead[0] ||
            coopDiagnosticGameplayRead[14]!=data_020a1154[0]) {
            coopDiagnosticGameplayRead[14]=data_020a1154[0];
            coopDiagnosticGameplayRead[15]=start;
            coopDiagnosticGameplayRead[17]=0;
            coopDiagnosticGameplayRead[18]=0;
            coopDiagnosticGameplayRead[19]=0;
        }
        ++coopDiagnosticGameplayRead[0];
        ++coopDiagnosticGameplayRead[17];
        coopDiagnosticGameplayRead[18]+=size;
        coopDiagnosticGameplayRead[1]=size;
        coopDiagnosticGameplayRead[2]=words[0x20/4];
        coopDiagnosticGameplayRead[3]=words[0x28/4];
        coopDiagnosticGameplayRead[4]=*(volatile u8 *)0x0209f2c4;
        coopDiagnosticGameplayRead[5]=start;
        coopDiagnosticGameplayRead[7]=1;
        coopDiagnosticGameplayRead[8]=data_020a1154[0];
        coopDiagnosticGameplayRead[11]=*(volatile u16 *)0x020a104c;
        coopDiagnosticGameplayRead[12]=*(volatile u32 *)0x0209d50c;
        coopDiagnosticGameplayRead[13]=data_02092664;
        int observed=CoopOriginalReadFile(file,destination,size,async);
        coopDiagnosticGameplayRead[6]=*(volatile u32 *)0x027ffc3c;
        coopDiagnosticGameplayRead[7]=0;
        coopDiagnosticGameplayRead[9]=data_020a1154[0];
        coopDiagnosticGameplayRead[10]=observed;
        coopDiagnosticGameplayRead[16]=coopDiagnosticGameplayRead[6];
        u32 elapsed=coopDiagnosticGameplayRead[6]-start;
        if (elapsed>coopDiagnosticGameplayRead[19])coopDiagnosticGameplayRead[19]=elapsed;
        if (coopDiagnosticGameplayRead[16]-coopDiagnosticGameplayRead[15]>
            coopDiagnosticSlowGameplayRead[16]-coopDiagnosticSlowGameplayRead[15])
            for (unsigned field=0;field<20;++field)
                coopDiagnosticSlowGameplayRead[field]=coopDiagnosticGameplayRead[field];
        return observed;
    }
#endif

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
    // A native flight entrance rejects non-Mario bodies and drops them into
    // the void. Give every entrant the ordinary Mario cap while its actor is
    // constructed. Keep base identities and later character choices intact.
    bool flight=data_0209fc68 && ((selected->param>>7)&15)==2;
    u8 previousCharacters[4];
    s8 pendingCharacter=data_02092114;
    if (flight) {
        for (unsigned slot=0;slot<4;++slot) {
            previousCharacters[slot]=data_02092128[slot];
            data_02092128[slot]=0;
        }
        data_02092114=-1;
    }
    CoopOriginalLoadEntrances(&temporary, area, 0);
    if (flight) {
        for (unsigned slot=0;slot<4;++slot)data_02092128[slot]=previousCharacters[slot];
        data_02092114=pendingCharacter;
    }
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

static void CoopReleaseStageSourceCache(void) {
    if (coopEnabled && data_0209fc68 && data_0208ecf4[0].image) {
        UnloadArchive(0);
        ++coopStageCacheEvictions;
    }
}

void CoopLoadSkybox(void *scene) {
    // Native SharedFilePtr/LoadFile copy or decompress cached members into
    // their own buffers and close their file views. All stage model/object
    // loads have returned at this boundary. Drop the 321 KB common source
    // cache before skybox/particle/arrival peaks; later members stream through
    // the uncached NARC path rather than pinning the whole archive again.
    CoopReleaseStageSourceCache();
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

#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
// Private immutable compressed bytes, never borrowed by a file/model caller.
// ROOT pressure may discard every entry before a native allocation.
struct CoopAnimationReadEntry {
    u32 top,length,bytes,age;
    u8 *data;
    mHeap::Heap_t *owner;
};
static CoopAnimationReadEntry coopAnimationReadEntries[32];
static u32 coopAnimationReadClock=0;
// hits, misses, stores, evictions, payload bytes, entries, peak bytes, flushes.
u32 coopAnimationCacheStats[8]={0};
extern const u8 coopAnimationCacheMask[];
extern const u32 coopAnimationDirectIndex[];
#ifdef COOP_DIAGNOSTIC_STAGE_CYCLE
u32 coopDiagnosticAnimationFlushCount=0;
u32 coopDiagnosticAnimationFlushes[16][8]={{0}};
void CoopTraceAnimationFlush(unsigned reason) {
    u32 irq=_ZN3IRQ7DisableEv();
    if (coopAnimationCacheStats[5]) {
        u32 sequence=++coopDiagnosticAnimationFlushCount;
        volatile u32 *row=coopDiagnosticAnimationFlushes[(sequence-1)&15];
        row[0]=0;
        row[1]=reason;row[2]=data_0209f2f8;row[3]=data_0209fc68;
        row[4]=coopAnimationCacheStats[4];row[5]=coopAnimationCacheStats[5];
        row[6]=*(volatile u32 *)0x027ffc3c;row[7]=*(volatile u32 *)0x0209d50c;
        row[0]=sequence;
    }
    _ZN3IRQ7RestoreEj(irq);
}
#endif


static unsigned CoopOldestAnimationRead() {
    unsigned oldest=32;
    u32 age=0;
    for (unsigned i=0;i<32;++i)
        if (coopAnimationReadEntries[i].data) {
            u32 elapsed=coopAnimationReadClock-coopAnimationReadEntries[i].age;
            if (oldest==32 || elapsed>age) { oldest=i; age=elapsed; }
        }
    return oldest;
}

static void CoopEvictAnimationRead(unsigned slot) {
    CoopAnimationReadEntry *entry=&coopAnimationReadEntries[slot];
    u8 *data=entry->data;
    mHeap::Heap_t *owner=entry->owner;
    coopAnimationCacheStats[4]-=entry->bytes;
    --coopAnimationCacheStats[5];
    ++coopAnimationCacheStats[3];
    entry->data=0;
    entry->owner=0;
    owner->Deallocate(data);
}

void CoopFlushAnimationReadCache() {
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    CoopReleaseCollisionPlan(0);
#endif
    u32 irq=_ZN3IRQ7DisableEv();
    for (unsigned i=0;i<32;++i)
        if (coopAnimationReadEntries[i].data)CoopEvictAnimationRead(i);
    ++coopAnimationCacheStats[7];
    _ZN3IRQ7RestoreEj(irq);
}

static void CoopAnimationCacheMakeRoom(mHeap::Heap_t *heap,u32 size,int align) {
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    CoopCollisionMakeRoom(heap,size,align);
#endif
    if (!coopAnimationCacheStats[5] || !heap || heap!=data_020a0e9c)return;
    u32 irq=_ZN3IRQ7DisableEv();
    while (CoopAlignedFree(heap,align)<size) {
        unsigned oldest=CoopOldestAnimationRead();
        if (oldest==32)break;
        CoopEvictAnimationRead(oldest);
    }
    _ZN3IRQ7RestoreEj(irq);
}

void *CoopAnimationHeapAllocate(mHeap::Heap_t *heap,u32 size,int align) {
    CoopAnimationCacheMakeRoom(heap,size,align);
    return CoopOriginalHeapAllocate(heap,size,align);
}

u32 CoopAnimationHeapReallocate(mHeap::Heap_t *heap,void *ptr,u32 size) {
    // Even with ample total free memory, a cached block could obstruct an
    // adjacent in-place grow. Restore the native layout before attempting it.
    if (heap==data_020a0e9c && coopAnimationCacheStats[5] && ptr &&
        size>(u32)heap->_Sizeof(ptr)) {
        CoopTraceAnimationFlush(3);
        CoopFlushAnimationReadCache();
    }
    return CoopOriginalHeapReallocate(heap,ptr,size);
}

#ifdef COOP_EXPERIMENTAL_LAZY_ANIMATION_EVICTION
u32 coopAnimationVirtualQueries=0,coopAnimationVirtualFallbacks=0;
struct CoopAnimationExtent { u32 start,end,node; };

// Read-only prediction of the exact native free list after releasing all cache
// blocks. Caller holds IRQs; uncertainty retains the existing flush policy.
static bool CoopAnimationCapacityLocked(mHeap::Heap_t *heap,u32 *capacity) {
    if (heap!=data_020a0e9c || !coopAnimationCacheStats[5])return false;
    ExpandingHeapAllocator *allocator=*(ExpandingHeapAllocator **)
        ((u8 *)heap+sizeof(mHeap::Heap_t));
    if ((u32)allocator<0x02000000 || (u32)allocator>0x023fffc8 ||
        allocator->mMagic!=0x45585048)return false;
    u32 begin=(u32)allocator->mStart,end=(u32)allocator->mEnd;
    if (begin<0x02000000 || end>0x02400000 || begin>=end || ((begin|end)&3))return false;
    CoopAnimationExtent cached[32];unsigned count=0;u32 bytes=0;
    for (unsigned slot=0;slot<32;++slot) {
        CoopAnimationReadEntry *entry=&coopAnimationReadEntries[slot];
        if (!entry->data)continue;
        u32 data=(u32)entry->data;
        if (entry->owner!=heap || data<begin+16 || data>end || (data&3))return false;
        MemoryNode *node=(MemoryNode *)(data-16);
        u32 padding=(node->flags>>8)&0x7f;
        if (node->tag!=0x5544 || node->size!=entry->bytes ||
            entry->length>node->size || node->size>end-data || (node->size&3) ||
            padding>data-16-begin || (padding&3))return false;
        CoopAnimationExtent extent={data-16-padding,data+node->size,data-16};
        unsigned index=count++;
        while (index && cached[index-1].start>extent.start) {
            cached[index]=cached[index-1];--index;
        }
        cached[index]=extent;bytes+=entry->bytes;
    }
    if (count!=coopAnimationCacheStats[5] || bytes!=coopAnimationCacheStats[4])return false;
    for (unsigned index=1;index<count;++index)
        if (cached[index-1].end>cached[index].start)return false;
    // Verify every cached header is still in this allocator's actual used
    // list. The cache owns the bytes exclusively; no game file borrows them.
    MemoryNode *node=allocator->mUsedFirstNode,*previous=0;
    unsigned visited=0;u32 found=0;
    while (node) {
        u32 address=(u32)node;
        if (++visited>1024 || address<begin || address>end-16 || (address&3) ||
            node->tag!=0x5544 || node->prev!=previous || node->size>end-address-16)return false;
        unsigned low=0,high=count;
        while (low<high) {
            unsigned middle=(low+high)/2;
            if (cached[middle].node<address)low=middle+1;else high=middle;
        }
        if (low<count && cached[low].node==address) {
            u32 bit=1u<<low;if (found&bit)return false;found|=bit;
        }
        previous=node;node=node->next;
    }
    if (previous!=allocator->mUsedLastNode ||
        found!=(count==32 ? 0xffffffffu : (1u<<count)-1))return false;
    // Merge the sorted cache extents with the native address-ordered free
    // list, counting reclaimed headers/padding only when native FreeNode would.
    node=allocator->mFirstNode;previous=0;visited=0;
    unsigned index=0;u32 start=0,limit=0,total=0,largest=0,previousEnd=0;
    while (node || index<count) {
        u32 a,b;
        if (node && (index==count || (u32)node<cached[index].start)) {
            a=(u32)node;
            if (++visited>256 || a<begin || a>end-16 || (a&3) ||
                node->tag!=0x4652 || node->flags || node->prev!=previous ||
                node->size>end-a-16 || (node->size&3) || (previous && a<=previousEnd))return false;
            b=a+16+node->size;previousEnd=b;previous=node;node=node->next;
        } else {
            a=cached[index].start;b=cached[index].end;++index;
        }
        if (limit && a<limit)return false;
        if (limit && a!=limit) {
            u32 size=limit-start-16;total+=size;if (size>largest)largest=size;
            start=a;
        } else if (!limit)start=a;
        limit=b;
    }
    if (previous!=allocator->mLastNode || !limit)return false;
    u32 size=limit-start-16;total+=size;if (size>largest)largest=size;
    capacity[0]=largest;capacity[1]=total;
    return true;
}

bool CoopAnimationQueryCapacity(mHeap::Heap_t *heap,u32 *capacity) {
    u32 irq=_ZN3IRQ7DisableEv();
    bool valid=CoopAnimationCapacityLocked(heap,capacity);
    if (valid)++coopAnimationVirtualQueries;else ++coopAnimationVirtualFallbacks;
    _ZN3IRQ7RestoreEj(irq);return valid;
}
#endif

u32 CoopAnimationMaxMemory(mHeap::Heap_t *heap) {
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    if (heap==data_020a0e9c)CoopReleaseCollisionPlan(1);
#endif
    // Native callers sometimes choose a heap or reject a request before they
    // allocate. Optional cache storage must not lower those capacity queries.
    if (heap==data_020a0e9c && coopAnimationCacheStats[5]) {
#ifdef COOP_EXPERIMENTAL_LAZY_ANIMATION_EVICTION
        u32 capacity[2];if (CoopAnimationQueryCapacity(heap,capacity))return capacity[0];
#endif
        CoopTraceAnimationFlush(4);
        CoopFlushAnimationReadCache();
    }
    return CoopAlignedFree(heap,4);
}

u32 CoopAnimationMemoryLeft(mHeap::Heap_t *heap) {
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    if (heap==data_020a0e9c)CoopReleaseCollisionPlan(1);
#endif
    if (heap==data_020a0e9c && coopAnimationCacheStats[5]) {
#ifdef COOP_EXPERIMENTAL_LAZY_ANIMATION_EVICTION
        u32 capacity[2];if (CoopAnimationQueryCapacity(heap,capacity))return capacity[1];
#endif
        CoopTraceAnimationFlush(5);
        CoopFlushAnimationReadCache();
    }
    ExpandingHeapAllocator *allocator=*(ExpandingHeapAllocator **)
        ((u8 *)heap+sizeof(mHeap::Heap_t));
    return allocator->MemoryLeft();
}

#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
void CoopAnimationTransitionCleanup() {
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    CoopReleaseCollisionPlan(0);
#endif
    // ROOT lives for the process; these are owned immutable bytes keyed by
    // verified cartridge extents, never stage model pointers. Native ROOT
    // pressure/queries still reclaim them before any game decision. Flush
    // ended/offline sessions, retaining bytes only across live stage changes.
    if (!coopEnabled || !data_0209fc68 || data_0209fc68==6 ||
        coopTitleLoading || coopSessionEnded) {
        CoopTraceAnimationFlush(2);
        CoopFlushAnimationReadCache();
    }
}
#endif

int CoopAnimationStageCleanup(void *scene) {
#ifdef COOP_EXPERIMENTAL_PERSISTENT_ANIMATION_CACHE
    CoopAnimationTransitionCleanup();
#else
    CoopTraceAnimationFlush(9);
    CoopFlushAnimationReadCache();
#endif
    return CoopOriginalStageCleanup(scene);
}

static u32 CoopAnimationReadKey(void *file,int size,int async) {
    if (!coopEnabled || data_0209fc68!=4 || (data_020a0f1c&0x9f) || async || size<8 || size>16384 ||
        data_020a613c!=data_020a621c)return 0;
    const u32 *fields=(const u32 *)file;
    if (fields[3]!=0x10 || fields[5] || (void *)fields[2]!=data_0209d3b4 || fields[10]!=fields[8] ||
        fields[9]-fields[8]!=(u32)size)return 0;
    u32 archiveFlags=*((volatile u32 *)data_0209d3b4+4);
    if (!(archiveFlags&2) || (archiveFlags&0xe0))return 0;
    const CoopArchiveIndex *index=(const CoopArchiveIndex *)coopNarcIndex;
    const u32 *extents=(const u32 *)(coopNarcIndex+index[0].extentOffset);
    for (unsigned member=0;member<(unsigned)(index[0].limit-index[0].first);++member)
        if ((coopAnimationCacheMask[member>>3] & (1u<<(member&7))) &&
            fields[8]==index[0].romTop+extents[member*2] &&
            (u32)size==extents[member*2+1]-extents[member*2])return fields[8];
    // Shared player poses such as paddle_end are direct NitroFS files rather
    // than common-NARC members. Match their exact original immutable extents.
    const u32 *direct=coopAnimationDirectIndex+1;
    unsigned low=0,high=coopAnimationDirectIndex[0];
    while (low<high) {
        unsigned middle=(low+high)/2;
        if (direct[middle*2]<fields[8])low=middle+1;else high=middle;
    }
    if (low<coopAnimationDirectIndex[0] && direct[low*2]==fields[8] &&
        direct[low*2+1]==(u32)size)return fields[8];
    return 0;
}

static bool CoopCopyAnimationRead(void *file,u32 top,void *destination,u32 size) {
    u32 irq=_ZN3IRQ7DisableEv();
    // Recheck the native ready/error/cursor state at the copy's atomic point.
    if (CoopAnimationReadKey(file,size,0)!=top) {
        _ZN3IRQ7RestoreEj(irq);
        return false;
    }
    for (unsigned i=0;i<32;++i) {
        CoopAnimationReadEntry *entry=&coopAnimationReadEntries[i];
        if (entry->data && entry->top==top && entry->length==size) {
            CpuCopy8(entry->data,destination,size);
            entry->age=++coopAnimationReadClock;
            ++coopAnimationCacheStats[0];
            _ZN3IRQ7RestoreEj(irq);
            return true;
        }
    }
    ++coopAnimationCacheStats[1];
    _ZN3IRQ7RestoreEj(irq);
    return false;
}

static void CoopStoreAnimationRead(u32 top,void *source,u32 size) {
    if (!func_02018568(source) || ((const u8 *)source)[4]!=0x10)return;
    mHeap::Heap_t *root=data_020a0e9c;
    if (!root)return;
    u32 irq=_ZN3IRQ7DisableEv();
    unsigned empty=32;
    for (unsigned i=0;i<32;++i) {
        CoopAnimationReadEntry *entry=&coopAnimationReadEntries[i];
        if (entry->data && entry->top==top && entry->length==size) {
            entry->age=++coopAnimationReadClock;
            _ZN3IRQ7RestoreEj(irq);
            return;
        }
        if (!entry->data)empty=i;
    }
    while (empty==32 || coopAnimationCacheStats[4]+((size+3)&~3u)>65536) {
        unsigned oldest=CoopOldestAnimationRead();
        if (oldest==32)break;
        CoopEvictAnimationRead(oldest);
        empty=oldest;
    }
    // Optional storage must never invoke the native game allocation's Crash
    // policy. Do not reserve more memory when the aligned block cannot fit.
    if (empty==32 || CoopAlignedFree(root,32)<size) {
        _ZN3IRQ7RestoreEj(irq);
        return;
    }
    u8 *copy=(u8 *)root->VAllocate(size,32);
    if (copy) {
        u32 bytes=root->_Sizeof(copy);
        while (coopAnimationCacheStats[4]+bytes>65536) {
            unsigned oldest=CoopOldestAnimationRead();
            if (oldest==32)break;
            CoopEvictAnimationRead(oldest);
        }
        CpuCopy8(source,copy,size);
        CoopAnimationReadEntry *entry=&coopAnimationReadEntries[empty];
        entry->top=top;
        entry->length=size;
        entry->bytes=bytes;
        entry->age=++coopAnimationReadClock;
        entry->owner=root;
        entry->data=copy;
        ++coopAnimationCacheStats[2];
        ++coopAnimationCacheStats[5];
        coopAnimationCacheStats[4]+=bytes;
        if (coopAnimationCacheStats[4]>coopAnimationCacheStats[6])
            coopAnimationCacheStats[6]=coopAnimationCacheStats[4];
    }
    _ZN3IRQ7RestoreEj(irq);
}

int CoopReadFile(void *file,void *destination,int size,int async) {
    u32 key=destination ? CoopAnimationReadKey(file,size,async) : 0;
    if (key && CoopCopyAnimationRead(file,key,destination,size)) {
        // Native SeekFile is a synchronous cursor adjustment, without I/O.
        // Keep the native view/CloseFile lifetime; only supply immutable bytes.
        u32 *fields=(u32 *)file;
        fields[4]=0; // Completed FS_COMMAND_READFILE.
        fields[11]=(u32)destination;
        fields[12]=fields[13]=size;
        if (func_0205d368(file,size,1))return size;
        return -1;
    }
    int result=CoopReadFileUncached(file,destination,size,async);
    if (key && result==size && ((u32 *)file)[10]==key+(u32)size)
        CoopStoreAnimationRead(key,destination,size);
    return result;
}
#endif

#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
// Reclaimable conservative candidates are checked against fresh native nodes
// and bounds every frame. Unknown types, domains or pressure retain retail.
struct CoopCollisionRecord { int minX,maxX,minZ,maxZ; u32 index; };
enum { CoopCollisionNodeLimit=256,CoopCollisionWindowBudget=2048,CoopCollisionCandidateBudget=1024 };
struct CoopCollisionPlan {
    mHeap::Heap_t *owner;
    u32 count,words,outer,next;
    void *last;
    u32 rowsOffset,nodesOffset,envelopesOffset,stage,sortedOffset,axis,candidateCount;
};
CoopCollisionPlan *volatile coopCollisionPlan=0;
// prepared, fallback, candidates, dispatched, notifications, pressure, peak, abort.
u32 coopCollisionPlanStats[8]={0};
u32 coopCollisionPlanReuses=0;
u32 coopCollisionPlanRefreshes=0;
u32 coopCollisionPlanEdgeRefreshes=0;
u32 coopCollisionCallbackDepth=0;
u32 coopCollisionValidatedCallbacks=0;
u32 coopCollisionCallbackAllocations=0;

static Vector3 *CoopCollisionPosition(void *node) {
    u32 table=*(u32 *)node;
    if (table<0x02000000 || table>=0x023ffff0)return 0;
    u32 *methods=(u32 *)table;
    if (methods[2]==0x02014820 && methods[3]==0x02014818)
        return (Vector3 *)((u8 *)node+0x30);
    if (methods[2]==0x02014a2c && methods[3]==0x02014a20)
        return (Vector3 *)((u8 *)node+0x34);
    if (methods[2]==0x02014948 && methods[3]==0x0201493c) {
        u32 owner=*(u32 *)((u8 *)node+0x30);
        if (owner>=0x02000000 && owner<0x023fff80)return (Vector3 *)(owner+0x5c);
    }
    return 0;
}
static u32 CoopCollisionAbs(int value) { return value<0 ? 0u-(u32)value : (u32)value; }

void CoopReleaseCollisionPlan(unsigned pressure) {
    u32 irq=_ZN3IRQ7DisableEv();
    CoopCollisionPlan *plan=coopCollisionPlan;
    if (plan) {
        coopCollisionPlan=0;
        mHeap::Heap_t *owner=plan->owner;
        if (pressure)++coopCollisionPlanStats[5];
        owner->Deallocate(plan);
    }
    _ZN3IRQ7RestoreEj(irq);
}
void CoopCollisionMakeRoom(mHeap::Heap_t *heap,u32 size,int align) {
    if (heap!=data_020a0e9c || !coopCollisionPlan)return;
    u32 irq=_ZN3IRQ7DisableEv();
    if (coopCollisionPlan && (coopCollisionCallbackDepth || CoopAlignedFree(heap,align)<size)) {
        if (coopCollisionCallbackDepth)++coopCollisionCallbackAllocations;
        CoopReleaseCollisionPlan(1);
    }
    _ZN3IRQ7RestoreEj(irq);
}
void *CoopCollisionVAllocate(mHeap::Heap_t *heap,u32 size,int align) {
    ExpandingHeapAllocator *allocator=*(ExpandingHeapAllocator **)((u8 *)heap+sizeof(mHeap::Heap_t));
    if (heap!=data_020a0e9c || !coopCollisionPlan)return allocator->Allocate(size,align);
    // A different SDK thread can allocate between native pairs. Keep the
    // capacity check, optional eviction and actual request atomic while this
    // collision storage is resident; leave other heaps' policy unchanged.
    u32 irq=_ZN3IRQ7DisableEv();
    CoopCollisionMakeRoom(heap,size,align);
    void *result=allocator->Allocate(size,align);
    _ZN3IRQ7RestoreEj(irq);
    return result;
}
u32 CoopCollisionVReallocate(mHeap::Heap_t *heap,void *ptr,u32 size) {
    if (heap==data_020a0e9c)CoopReleaseCollisionPlan(1);
    ExpandingHeapAllocator *allocator=*(ExpandingHeapAllocator **)((u8 *)heap+sizeof(mHeap::Heap_t));
    return allocator->Reallocate(ptr,size);
}

static int CoopCollisionEnvelopeMargin(void *node) {
    // Velocity sizes a conservative box only. Every frame still validates the
    // actual geometry; acceleration, reversals and teleports are never assumed.
    u32 speed=0;
    u32 getter=(*(u32 **)node)[2];
    if (getter!=0x02014820) {
        u32 owner=*(u32 *)((u8 *)node+0x30);
        if (owner>=0x02000000 && owner<0x023fff50) {
            const dActor_c *actor=(const dActor_c *)owner;
            speed=CoopCollisionAbs(actor->mHorzSpeed);
            u32 axis=CoopCollisionAbs(actor->mSpeedX);if (axis>speed)speed=axis;
            axis=CoopCollisionAbs(actor->mSpeedZ);if (axis>speed)speed=axis;
        }
    }
    const u32 maximum=2048*4096;
    u32 margin=speed>maximum/32 ? maximum : speed*32;
    return margin<32*4096 ? 32*4096 : (int)margin;
}
static void CoopCollisionSift(CoopCollisionRecord *records,unsigned count,unsigned root) {
    while (root*2+1<count) {
        unsigned child=root*2+1;
        if (child+1<count && records[child].minX<records[child+1].minX)++child;
        if (records[root].minX>=records[child].minX)break;
        CoopCollisionRecord temp=records[root]; records[root]=records[child]; records[child]=temp;
        root=child;
    }
}
static void CoopCollisionSort(CoopCollisionRecord *records,unsigned count) {
    for (unsigned root=count/2;root;--root)CoopCollisionSift(records,count,root-1);
    for (unsigned end=count-1;end;--end) {
        CoopCollisionRecord temp=records[0];records[0]=records[end];records[end]=temp;
        CoopCollisionSift(records,end,0);
    }
}
static bool CoopCollisionWindowFits(CoopCollisionRecord *records,unsigned count,int *ends) {
    // Sorted starts plus a min-heap of active ends count exact 1D overlap
    // windows in bounded O(n log n), without first walking rejected pairs.
    // The unpublished candidate bitmap provides scratch for at most256 ends.
    unsigned active=0,checks=0;
    for (unsigned index=0;index<count;++index) {
        while (active && ends[0]<=records[index].minX) {
            int tail=ends[--active];unsigned root=0;
            while (root*2+1<active) {
                unsigned child=root*2+1;
                if (child+1<active && ends[child+1]<ends[child])++child;
                if (tail<=ends[child])break;
                ends[root]=ends[child];root=child;
            }
            if (active)ends[root]=tail;
        }
        checks+=active;
        if (checks>CoopCollisionWindowBudget)return false;
        int value=records[index].maxX;unsigned position=active++;
        while (position && ends[(position-1)/2]>value) {
            ends[position]=ends[(position-1)/2];position=(position-1)/2;
        }
        ends[position]=value;
    }
    return true;
}

static bool CoopCollisionPlanCoversRange(CoopCollisionPlan *plan,unsigned begin) {
    if (plan->stage!=coopStageIdentity || begin>=plan->count)return false;
    void **nodes=(void **)((u8 *)plan+plan->nodesOffset);
    int *bounds=(int *)((u8 *)plan+plan->envelopesOffset);
    void *node=*(void **)0x0209cee8;
    for (unsigned index=begin;index<plan->count;++index) {
        // Compare fresh list nodes before dereferencing anything cached. Removed,
        // reordered or reallocated actors must never leave a stale game pointer.
        if (!node || node!=nodes[index])return false;
        Vector3 *pos=CoopCollisionPosition(node);
        int radius=*(int *)((u8 *)node+4);
        if (!pos || (u32)pos<0x02000000 || (u32)pos>=0x023ffff4 ||
            CoopCollisionAbs(pos->x)>0x0fffffff || CoopCollisionAbs(pos->z)>0x0fffffff ||
            (u32)radius>0x1fffffff ||
            pos->x-radius<bounds[index*4] || pos->x+radius>bounds[index*4+1] ||
            pos->z-radius<bounds[index*4+2] || pos->z+radius>bounds[index*4+3])return false;
        node=*(void **)((u8 *)node+0x2c);
    }
    return node==0;
}
// Returns -1 to use the full refresh, 0 to retain native processing after
// bounded work, or 1 after updating only escaped nodes. Caller holds IRQs.
static int CoopRefreshCollisionEdges(CoopCollisionPlan *plan) {
    void **nodes=(void **)((u8 *)plan+plan->nodesOffset);
    int *bounds=(int *)((u8 *)plan+plan->envelopesOffset);
    u16 changed[8];unsigned changes=0;
    for (unsigned index=0;index<plan->count;++index) {
        Vector3 *pos=CoopCollisionPosition(nodes[index]);
        int radius=*(int *)((u8 *)nodes[index]+4);
        if (!pos || (u32)pos<0x02000000 || (u32)pos>=0x023ffff4 ||
            CoopCollisionAbs(pos->x)>0x0fffffff || CoopCollisionAbs(pos->z)>0x0fffffff ||
            (u32)radius>0x1fffffff)return 0;
        if (pos->x-radius<bounds[index*4] || pos->x+radius>bounds[index*4+1] ||
            pos->z-radius<bounds[index*4+2] || pos->z+radius>bounds[index*4+3]) {
            if (changes==8)return -1;
            changed[changes++]=(u16)index;
        }
    }
    if (changes*(plan->count-1)>1024)return -1;
    u16 *sorted=(u16 *)((u8 *)plan+plan->sortedOffset);
    u32 *rows=(u32 *)((u8 *)plan+plan->rowsOffset);
    unsigned shifts=0;
    for (unsigned change=0;change<changes;++change) {
        unsigned index=changed[change];
        Vector3 *pos=CoopCollisionPosition(nodes[index]);
        int radius=*(int *)((u8 *)nodes[index]+4);
        int margin=CoopCollisionEnvelopeMargin(nodes[index]);
        int *box=bounds+index*4;
        box[0]=pos->x-radius-margin;box[1]=pos->x+radius+margin;
        box[2]=pos->z-radius-margin;box[3]=pos->z+radius+margin;
        // Change one key at a time so the other sorted keys stay ordered.
        unsigned position=0;
        while (position<plan->count && sorted[position]!=index)++position;
        if (position==plan->count)return 0;
        int key=box[plan->axis*2];
        while (position) {
            unsigned previous=sorted[position-1];
            if (previous>=plan->count)return 0;
            if (bounds[previous*4+plan->axis*2]<=key)break;
            if (++shifts>256)return 0;
            sorted[position]=previous;--position;
        }
        while (position+1<plan->count) {
            unsigned next=sorted[position+1];
            if (next>=plan->count)return 0;
            if (bounds[next*4+plan->axis*2]>=key)break;
            if (++shifts>256)return 0;
            sorted[position]=next;++position;
        }
        sorted[position]=(u16)index;
        // Unchanged envelopes retain their edges. A pair changed twice is
        // recomputed after each endpoint, so its final bit uses both new boxes.
        for (unsigned other=0;other<plan->count;++other) {
            if (other==index)continue;
            const int *b=bounds+other*4;
            bool overlap=box[0]<b[1] && b[0]<box[1] && box[2]<b[3] && b[2]<box[3];
            unsigned first=index,second=other;
            if (first>second) { unsigned swap=first;first=second;second=swap; }
            u32 *word=rows+first*plan->words+second/32;
            u32 mask=0x80000000u>>(second&31);
            if (overlap) {
                if (!(*word&mask))++plan->candidateCount;
                *word|=mask;
            } else if (*word&mask) {
                *word&=~mask;--plan->candidateCount;
            }
        }
    }
    if (plan->candidateCount>CoopCollisionCandidateBudget)return 0;
    plan->outer=0xffffffff;plan->next=0;plan->last=0;
    coopCollisionPlanStats[2]+=plan->candidateCount;
    ++coopCollisionPlanRefreshes;++coopCollisionPlanEdgeRefreshes;
    return 1;
}

// Returns -1 before doing work if a fresh construction is required, 0 after
// bounded work if this frame must retain retail, or 1 after an in-place refresh.
static int CoopRefreshCollisionPlan(CoopCollisionPlan *plan) {
    if (plan->stage!=coopStageIdentity || plan->axis>1)return -1;
    void **nodes=(void **)((u8 *)plan+plan->nodesOffset);
    void *node=*(void **)0x0209cee8;
    for (unsigned index=0;index<plan->count;++index) {
        if (!node || node!=nodes[index])return -1;
        node=*(void **)((u8 *)node+0x2c);
    }
    if (node)return -1;
    int edges=CoopRefreshCollisionEdges(plan);
    if (edges>=0)return edges;
    mHeap::Heap_t *owner=plan->owner;
    u32 size=plan->count*sizeof(CoopCollisionRecord);
    if (CoopAlignedFree(owner,32)<size)return -1;
    // The caller already holds IRQs. Detach only while allocating private
    // construction records, so our own optional-allocation hook cannot evict
    // the block being refreshed. No game callbacks or I/O occur here.
    coopCollisionPlan=0;
    CoopCollisionRecord *records=(CoopCollisionRecord *)owner->VAllocate(size,32);
    if (!records) { coopCollisionPlan=plan;return -1; }
    u16 *sorted=(u16 *)((u8 *)plan+plan->sortedOffset);
    int *bounds=(int *)((u8 *)plan+plan->envelopesOffset);
    bool valid=true;
    for (unsigned position=0;position<plan->count;++position) {
        unsigned index=sorted[position];
        if (index>=plan->count) { valid=false;break; }
        void *item=nodes[index];Vector3 *pos=CoopCollisionPosition(item);
        int radius=*(int *)((u8 *)item+4);
        if (!pos || (u32)pos<0x02000000 || (u32)pos>=0x023ffff4 ||
            CoopCollisionAbs(pos->x)>0x0fffffff || CoopCollisionAbs(pos->z)>0x0fffffff ||
            (u32)radius>0x1fffffff) { valid=false;break; }
        int margin=CoopCollisionEnvelopeMargin(item);
        int minX=pos->x-radius-margin,maxX=pos->x+radius+margin;
        int minZ=pos->z-radius-margin,maxZ=pos->z+radius+margin;
        bounds[index*4]=minX;bounds[index*4+1]=maxX;
        bounds[index*4+2]=minZ;bounds[index*4+3]=maxZ;
        records[position].minX=plan->axis ? minZ : minX;
        records[position].maxX=plan->axis ? maxZ : maxX;
        records[position].minZ=plan->axis ? minX : minZ;
        records[position].maxZ=plan->axis ? maxX : maxZ;
        records[position].index=index;
    }
    unsigned shifts=0;
    if (valid)for (unsigned index=1;index<plan->count;++index) {
        CoopCollisionRecord item=records[index];unsigned position=index;
        while (position && records[position-1].minX>item.minX) {
            if (++shifts>256) { valid=false;break; }
            records[position]=records[position-1];--position;
        }
        if (!valid)break;
        records[position]=item;
    }
    unsigned candidates=0,checks=0;
    u32 *rows=(u32 *)((u8 *)plan+plan->rowsOffset);
    if (valid) {
        for (unsigned word=0;word<plan->count*plan->words;++word)rows[word]=0;
        for (unsigned first=0;first<plan->count && valid;++first) {
            const CoopCollisionRecord *a=&records[first];
            for (unsigned other=first+1;other<plan->count;++other) {
                const CoopCollisionRecord *b=&records[other];
                if (b->minX>=a->maxX)break;
                if (++checks>CoopCollisionWindowBudget) { valid=false;break; }
                if (b->minZ>=a->maxZ || a->minZ>=b->maxZ)continue;
                if (++candidates>CoopCollisionCandidateBudget) { valid=false;break; }
                unsigned i=a->index,j=b->index;
                if (i>j) { unsigned swap=i;i=j;j=swap; }
                rows[i*plan->words+j/32]|=0x80000000u>>(j&31);
            }
        }
    }
    if (valid) {
        for (unsigned index=0;index<plan->count;++index)sorted[index]=(u16)records[index].index;
        plan->outer=0xffffffff;plan->next=0;plan->last=0;
        plan->candidateCount=candidates;
        coopCollisionPlanStats[2]+=candidates;++coopCollisionPlanRefreshes;
    }
    owner->Deallocate(records);
    coopCollisionPlan=plan;
    return valid ? 1 : 0;
}

static void CoopPrepareCollisionPlan() {
    if (!coopEnabled || data_0209fc68!=4 || (data_020a0f1c&0x9f) || coopCollisionCallbackDepth ||
        data_020a613c!=data_020a621c || !data_020a0e9c) {
        CoopReleaseCollisionPlan(0);++coopCollisionPlanStats[1];return;
    }
    // Bounded RAM/heap work only: no I/O, callbacks, thread sleeps or native
    // game updates while IRQs protect the optional temporary allocation.
    u32 irq=_ZN3IRQ7DisableEv();
    CoopCollisionPlan *cached=coopCollisionPlan;
    if (cached) {
        if (CoopCollisionPlanCoversRange(cached,0)) {
            cached->outer=0xffffffff;cached->next=0;cached->last=0;
            ++coopCollisionPlanReuses;_ZN3IRQ7RestoreEj(irq);return;
        }
        int refreshed=CoopRefreshCollisionPlan(cached);
        if (refreshed>0) { _ZN3IRQ7RestoreEj(irq);return; }
        CoopReleaseCollisionPlan(0);
        if (!refreshed) {
            ++coopCollisionPlanStats[1];++coopCollisionPlanStats[7];
            _ZN3IRQ7RestoreEj(irq);return;
        }
    }
    void *head=*(void **)0x0209cee8,*node=head;
    unsigned count=0;
    while (node && count<CoopCollisionNodeLimit) {
        if ((u32)node<0x02000000 || (u32)node>=0x023fffc0 || !CoopCollisionPosition(node))break;
        ++count;node=*(void **)((u8 *)node+0x2c);
    }
    if (node || count<48) {
        ++coopCollisionPlanStats[1];
        if (node)++coopCollisionPlanStats[7];
        _ZN3IRQ7RestoreEj(irq);return;
    }
    unsigned words=(count+31)/32;
    u32 liveBytes=(sizeof(CoopCollisionPlan)+count*words*4+count*4+count*16+count*2+3)&~3u;
    u32 bytes=liveBytes+count*sizeof(CoopCollisionRecord);
    mHeap::Heap_t *owner=data_020a0e9c;
    if (CoopAlignedFree(owner,32)<bytes) {
        ++coopCollisionPlanStats[1];_ZN3IRQ7RestoreEj(irq);return;
    }
    CoopCollisionPlan *plan=(CoopCollisionPlan *)owner->VAllocate(bytes,32);
    if (!plan) {
        ++coopCollisionPlanStats[1];_ZN3IRQ7RestoreEj(irq);return;
    }
    plan->owner=owner;plan->count=count;plan->words=words;
    plan->outer=0xffffffff;plan->next=0;plan->last=0;plan->candidateCount=0;
    plan->rowsOffset=sizeof(CoopCollisionPlan);
    plan->nodesOffset=plan->rowsOffset+count*words*4;
    plan->envelopesOffset=plan->nodesOffset+count*4;plan->stage=coopStageIdentity;
    plan->sortedOffset=plan->envelopesOffset+count*16;plan->axis=0;
    u32 *rows=(u32 *)((u8 *)plan+plan->rowsOffset);
    void **nodes=(void **)((u8 *)plan+plan->nodesOffset);
    int *envelopes=(int *)((u8 *)plan+plan->envelopesOffset);
    CoopCollisionRecord *records=(CoopCollisionRecord *)((u8 *)plan+liveBytes);
    node=head;
    bool valid=true;
    int minX=0x7fffffff,maxX=-0x7fffffff,minZ=0x7fffffff,maxZ=-0x7fffffff;
    for (unsigned index=0;index<count;++index) {
        Vector3 *pos=CoopCollisionPosition(node);
        int radius=*(int *)((u8 *)node+4);
        if (!pos || (u32)pos<0x02000000 || (u32)pos>=0x023ffff4 ||
            CoopCollisionAbs(pos->x)>0x0fffffff || CoopCollisionAbs(pos->z)>0x0fffffff ||
            (u32)radius>0x1fffffff) { valid=false;break; }
        // A reusable superset of possible contacts. Every frame revalidates
        // actual cylinder bounds against these envelopes before using the plan.
        const int margin=CoopCollisionEnvelopeMargin(node);
        records[index].minX=pos->x-radius-margin;records[index].maxX=pos->x+radius+margin;
        records[index].minZ=pos->z-radius-margin;records[index].maxZ=pos->z+radius+margin;
        envelopes[index*4]=records[index].minX;envelopes[index*4+1]=records[index].maxX;
        envelopes[index*4+2]=records[index].minZ;envelopes[index*4+3]=records[index].maxZ;
        if (records[index].minX<minX)minX=records[index].minX;
        if (records[index].maxX>maxX)maxX=records[index].maxX;
        if (records[index].minZ<minZ)minZ=records[index].minZ;
        if (records[index].maxZ>maxZ)maxZ=records[index].maxZ;
        records[index].index=index;nodes[index]=node;
        node=*(void **)((u8 *)node+0x2c);
    }
    if (!valid) {
        owner->Deallocate(plan);++coopCollisionPlanStats[1];++coopCollisionPlanStats[7];
        _ZN3IRQ7RestoreEj(irq);return;
    }
    // Sweep the more spread-out horizontal axis; long narrow levels should
    // not generate a quadratic window merely because it follows Z rather than X.
    if ((u32)(maxZ-minZ)/2>(u32)(maxX-minX))plan->axis=1;
    if (plan->axis)for (unsigned index=0;index<count;++index) {
        int value=records[index].minX;records[index].minX=records[index].minZ;records[index].minZ=value;
        value=records[index].maxX;records[index].maxX=records[index].maxZ;records[index].maxZ=value;
    }
    CoopCollisionSort(records,count);
    if (!CoopCollisionWindowFits(records,count,(int *)rows)) {
        plan->axis^=1;
        for (unsigned index=0;index<count;++index) {
            int value=records[index].minX;records[index].minX=records[index].minZ;records[index].minZ=value;
            value=records[index].maxX;records[index].maxX=records[index].maxZ;records[index].maxZ=value;
        }
        CoopCollisionSort(records,count);
        if (!CoopCollisionWindowFits(records,count,(int *)rows)) {
            owner->Deallocate(plan);++coopCollisionPlanStats[1];++coopCollisionPlanStats[7];
            _ZN3IRQ7RestoreEj(irq);return;
        }
    }
    for (unsigned word=0;word<count*words;++word)rows[word]=0;
    u16 *sorted=(u16 *)((u8 *)plan+plan->sortedOffset);
    for (unsigned index=0;index<count;++index)sorted[index]=(u16)records[index].index;
    unsigned candidates=0,checks=0;
    for (unsigned first=0;first<count;++first) {
        const CoopCollisionRecord *a=&records[first];
        for (unsigned other=first+1;other<count;++other) {
            const CoopCollisionRecord *b=&records[other];
            if (b->minX>=a->maxX)break;
            // Dense scenes retain native processing instead of extending the
            // IRQ-protected preparation into an unbounded quadratic pass.
            if (++checks>CoopCollisionWindowBudget) {
                owner->Deallocate(plan);++coopCollisionPlanStats[1];++coopCollisionPlanStats[7];
                _ZN3IRQ7RestoreEj(irq);return;
            }
            if (b->minZ>=a->maxZ || a->minZ>=b->maxZ)continue;
            if (++candidates>CoopCollisionCandidateBudget) {
                owner->Deallocate(plan);++coopCollisionPlanStats[1];++coopCollisionPlanStats[7];
                _ZN3IRQ7RestoreEj(irq);return;
            }
            unsigned i=a->index,j=b->index;
            if (i>j) { unsigned temp=i;i=j;j=temp; }
            rows[i*words+j/32]|=0x80000000u>>(j&31);
        }
    }
    // Shrink away construction records before the native game runs. A failed
    // shrink still leaves a valid optional block, reclaimed before native pressure.
    owner->Reallocate(plan,liveBytes);
    plan->candidateCount=candidates;
    coopCollisionPlan=plan;
    ++coopCollisionPlanStats[0];coopCollisionPlanStats[2]+=candidates;
    if (count>coopCollisionPlanStats[6])coopCollisionPlanStats[6]=count;
    _ZN3IRQ7RestoreEj(irq);
}
__asm u32 CoopCollisionLeadingZeroes(u32 value) { clz r0,r0; bx lr }

void *CoopCollisionCandidate(void *first,void *other) {
    // A pressure eviction may occur between native pairs. Protect all reads
    // of the optional block, not the original collision/game processing.
    u32 irq=_ZN3IRQ7DisableEv();
    CoopCollisionPlan *plan=coopCollisionPlan;
    if (!plan || coopCollisionCallbackDepth) { _ZN3IRQ7RestoreEj(irq);return other; }
    void **nodes=(void **)((u8 *)plan+plan->nodesOffset);
    if (plan->last!=first) {
        ++plan->outer;plan->next=plan->outer+1;plan->last=first;
    }
    if (plan->outer>=plan->count || plan->next>=plan->count ||
        nodes[plan->outer]!=first || nodes[plan->next]!=other) {
        CoopReleaseCollisionPlan(0);_ZN3IRQ7RestoreEj(irq);return other;
    }
    u32 *row=(u32 *)((u8 *)plan+plan->rowsOffset)+plan->outer*plan->words;
    unsigned word=plan->next/32;
    u32 mask=row[word]&(0xffffffffu>>(plan->next&31));
    while (!mask && ++word<plan->words)mask=row[word];
    void *result=0;
    if (mask) {
        unsigned index=word*32+CoopCollisionLeadingZeroes(mask);
        if (index<plan->count) {
            result=nodes[index];plan->next=index+1;++coopCollisionPlanStats[3];
        }
    }
    _ZN3IRQ7RestoreEj(irq);return result;
}
void CoopCollisionNotify(u32 owner,dCc_c *node) {
    u32 irq=_ZN3IRQ7DisableEv();
    CoopCollisionPlan *before=coopCollisionPlan;
    void *first=*(void **)0x0209cee8;
    Vector3 *position=before && before->outer<before->count ? CoopCollisionPosition(first) : 0;
    if (before)++coopCollisionPlanStats[4];
    ++coopCollisionCallbackDepth;
    _ZN3IRQ7RestoreEj(irq);
    // Candidate use is suspended throughout game code. Any ROOT allocation,
    // capacity query, growth or cleanup reclaims optional storage BEFORE the
    // native decision. Do not hold an IRQ guard across the game callback.
    func_02014f44(owner,node);
    irq=_ZN3IRQ7DisableEv();
    --coopCollisionCallbackDepth;
    if (before && coopCollisionPlan==before && !coopCollisionCallbackDepth) {
        // Native r9 still refers to this outer collider's original position.
        // Preserve that reference, list suffix/order and all remaining bounds
        // before using another cached edge. A changed plan is never trusted.
        if (coopEnabled && data_0209fc68==4 && position &&
            *(void **)0x0209cee8==first && CoopCollisionPosition(first)==position &&
            CoopCollisionPlanCoversRange(before,before->outer))
            ++coopCollisionValidatedCallbacks;
        else CoopReleaseCollisionPlan(0);
    }
    _ZN3IRQ7RestoreEj(irq);
}

void CoopCollisionProcess() {
    CoopPrepareCollisionPlan();
    dCc_c::Process();
    // Keep only a pressure-reclaimable conservative plan, not borrowed actor
    // resources. The next frame validates fresh nodes/bounds before any reuse.
}
__asm void CoopCollisionPairRead(void) {
    // Missing/evicted plans retain the native walk without calling the C++
    // selector for every pair. A later eviction is still rechecked under IRQs
    // by CoopCollisionCandidate before it dereferences any workspace.
    ldr r0,=coopCollisionPlan
    ldr r0,[r0]
    cmp r0,#0
    beq nativePair
    stmfd sp!, {r1-r3,r12,lr}
    sub sp,sp,#4
    ldr r0,[r4]
    mov r1,r8
    bl CoopCollisionCandidate
    mov r8,r0
    add sp,sp,#4
    ldmfd sp!, {r1-r3,r12,lr}
    cmp r8,#0
    beq CoopCollisionPairDone
nativePair:
    ldr r0,[r4]
    b CoopCollisionPairContinue
}
#endif

void *CoopAllocatePaintingMesh(u32 size) {
    // PicGate allocates its cells before opening its texture. Prior synchronous
    // resource reads have closed their source views and own their model copies.
    // Release the common NARC source only when ROOT cannot fit the full mesh;
    // later members can use the verified streaming path. Keep native mesh
    // dimensions, allocator and cleanup ownership unchanged.
    if (coopEnabled && data_0209fc68 && Memory::defaultHeapPtr==data_020a0e9c &&
        CoopAlignedFree(Memory::defaultHeapPtr,4)<size)
        CoopReleaseStageSourceCache();
    return _ZN6Memory13operator_new2Ej(size);
}

void *CoopAllocateAlignedResource(u32 size,int align) {
    mHeap::Heap_t *root=Memory::defaultHeapPtr;
    mHeap::Heap_t *game=(mHeap::Heap_t *)data_020a0eac;
#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
    CoopAnimationCacheMakeRoom(root,size,align);
#endif
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

// Overlay1's common HUD digits are present in every story HUD language.
// Reuse those assets instead of VS's incompatible bottom-screen atlas.
static void CoopDrawMinimapPlayers(dMap_c *map,unsigned local) {
    if (data_0209f2d8 || local>=4)return;
    u8 hidden=*(volatile u8 *)0x0209f294 | *(volatile u8 *)0x0209f2c4 | data_0209f20c;
    // Match the native map's cutscene/pause visibility policy.
    if (hidden && (*(volatile u32 *)0x0209caa8&0x80) &&
        !(data_0209f20c && *(volatile u32 *)0x0209f2d4<3))return;
    int mapID=*(volatile s8 *)0x02111148;
    if (mapID<0)return;
    OamAttr *const *numbers=(OamAttr *const *)0x020aba70;
    for (unsigned slot=0;slot<4;++slot) {
        u32 player=(u32)data_0209f394[slot];
        if (!player || map->mPlayerMapIDs[slot]!=mapID)continue;
        int x=map->mPlayerIconX[slot],y=map->mPlayerIconY[slot];
        if ((u32)(x+16)>=288 || (u32)(y+16)>=224)continue;
        // The existing head/arrow identifies this console; a small numbered
        // badge identifies its slot. Remote numbered markers use their exact
        // native map position and remain distinguishable for all-Yoshi parties.
        OAM::RenderSub(numbers[slot+1],x+(slot==local ? 10 : -4),y-8,-1,2);
    }
}

static bool CoopMinimapLocalReady(unsigned local) {
    u32 player=local<4 ? (u32)data_0209f394[local] : 0;
    return coopEnabled && data_0209fc68==4 &&
        player>=0x02000000 && player<=0x023ffff4 && !(player&3);
}

int CoopMinimapBehavior(dMap_c *map) {
    u8 previous=data_0209f250,input=gActivePlayerSlot,local=CoopCameraOwner();
    bool active=CoopMinimapLocalReady(local);
    if (active)data_0209f250=gActivePlayerSlot=local;
    int result=CoopOriginalMinimapBehavior(map);
    if (active) { data_0209f250=previous;gActivePlayerSlot=input; }
    return result;
}

int CoopMinimapRender(dMap_c *map) {
    u8 previous=data_0209f250,local=CoopCameraOwner();
    bool active=CoopMinimapLocalReady(local);
    if (active)data_0209f250=local;
    int result=CoopOriginalMinimapRender(map);
    if (active)CoopDrawMinimapPlayers(map,local);
    if (active)data_0209f250=previous;
    return result;
}

static u8 CoopLocalCameraInfo(dCamera_c *camera) {
    u8 info=(camera->mFlags&0x8000)!=0;
    if (camera->mFlags&0x1000)info|=2;
    if (camera->mAreaMode && (*(const u16 *)((const u8 *)camera->mAreaMode+0x26)&1))info|=4;
    return info;
}

u32 CoopInputCameraFlags(dCamera_c *camera,unsigned player) {
    u32 flags=camera->mFlags;
    if (coopEnabled && data_0209fc68 && player<4)
        flags=(flags&~0x1000u)|((data_020a1166[player*36+5]&2)<<11);
    return flags;
}

u32 CoopPersonalCameraFlags(dCamera_c *camera) {
    u32 flags=camera->mFlags;
    if (coopEnabled && data_0209fc68 && gActivePlayerSlot<4)
        flags=(flags&~0x8000u)|((data_020a1166[gActivePlayerSlot*36+5]&1)<<15);
    return flags;
}

u32 CoopPersonalCameraPitch(dCamera_c *camera) {
    if (coopEnabled && data_0209fc68 && gActivePlayerSlot<4) {
        unsigned offset=gActivePlayerSlot*36+7;
        return data_020a1166[offset]|(data_020a1166[offset+1]<<8);
    }
    return (u16)camera->mAngleX;
}

// St_Cannon_Main keeps the camera in r4. Replace only the unsigned pitch
// load, retaining native trigonometry and every other launch calculation.
__asm void CoopCannonPitchRead(void) {
    stmfd sp!, {r1-r4, r12, lr}
    mrs r1, cpsr
    stmfd sp!, {r1-r2}
    mov r0, r4
    bl CoopPersonalCameraPitch
    ldmfd sp!, {r1-r2}
    msr cpsr_f, r1
    ldmfd sp!, {r1-r4, r12, pc}
}

// CheckCameraInput has its player index in r1 and camera pointer in r9.
// Replace its flags load while preserving every other register and CPSR.
__asm void CoopCameraInputFlagsRead(void) {
    stmfd sp!, {r0-r3, r12, lr}
    mrs r2, cpsr
    stmfd sp!, {r2-r3}
    mov r0, r9
    bl CoopInputCameraFlags
    mov r9, r0
    ldmfd sp!, {r2-r3}
    msr cpsr_f, r2
    ldmfd sp!, {r0-r3, r12, pc}
}

__asm void CoopPersonalCameraFlagsRead(void) {
    stmfd sp!, {r1-r3, r12, lr}
    bl CoopPersonalCameraFlags
    ldmfd sp!, {r1-r3, r12, pc}
}

int CoopCameraFar(void *camera,unsigned player) {
    if (coopEnabled && data_0209fc68 && player<4) {
        // The native foreign-player guard returns success even when that
        // player's own area disallows zoom. Story mode uses this result to
        // enter first person, so all replicas must consume its echoed choice.
        if (data_020a1166[player*36+5]&4)return 0;
        if (player==data_020a0f10) {
            ((dCamera_c *)camera)->mFlags|=2;
            func_02012790(7);
        }
        return 1;
    }
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

// Native player-specific camera state setters include swimming, flying,
// climbing and launched states. Their player guard must use the displayed
// local slot even while shared actor decisions consume the host's input.
#define COOP_LOCAL_CAMERA_MODE(suffix) \
    void CoopOriginalCameraMode##suffix(void *,unsigned); \
    void CoopCameraMode##suffix(void *camera,unsigned player) { \
        u8 previous=data_0209f250; \
        data_0209f250=CoopCameraOwner(); \
        CoopOriginalCameraMode##suffix(camera,player); \
        data_0209f250=previous; \
    }
COOP_LOCAL_CAMERA_MODE(D10c)
COOP_LOCAL_CAMERA_MODE(D148)
COOP_LOCAL_CAMERA_MODE(D438)
COOP_LOCAL_CAMERA_MODE(D474)
COOP_LOCAL_CAMERA_MODE(D508)
COOP_LOCAL_CAMERA_MODE(D544)
COOP_LOCAL_CAMERA_MODE(D580)
COOP_LOCAL_CAMERA_MODE(D5c0)
COOP_LOCAL_CAMERA_MODE(D5fc)
COOP_LOCAL_CAMERA_MODE(D63c)
COOP_LOCAL_CAMERA_MODE(D678)
COOP_LOCAL_CAMERA_MODE(D6b4)
COOP_LOCAL_CAMERA_MODE(D6f0)
COOP_LOCAL_CAMERA_MODE(D72c)
COOP_LOCAL_CAMERA_MODE(D768)
COOP_LOCAL_CAMERA_MODE(D7a4)
#undef COOP_LOCAL_CAMERA_MODE

void CoopCameraLookTarget(void *camera,unsigned player,void *target) {
    u8 previous=data_0209f250;
    data_0209f250=CoopCameraOwner();
    CoopOriginalCameraLookTarget(camera,player,target);
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
        // carries per-player completion, input availability and zoom limits.
        // Shared dialogs use the host's echoed completion bit.
        if (data_0209f318) {
            data_020a1052[5] = CoopLocalCameraInfo(data_0209f318);
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

u32 CoopShadowActorFlags(dActor_c *actor) {
    u32 flags=actor->mFlags;
    if (coopEnabled && data_0209fc68 && coopBehaviorActor==(u32)actor)
        // AI sees consistent visibility during Behavior, but native shadow
        // registration must still reject actors beyond this camera's range.
        // Keep any additional shadow suppression set by the actor itself.
        flags|=coopBehaviorVisibility&0x10;
    return flags;
}

// Replace only each native shadow helper's flags load. Its following ANDS,
// early return, scale arguments and native list registration remain intact.
__asm void CoopShadowFlagsRead(void) {
    stmfd sp!, {r1-r3, r12, lr}
    mrs r1, cpsr
    stmfd sp!, {r1}
    bl CoopShadowActorFlags
    ldmfd sp!, {r1}
    msr cpsr_f, r1
    ldmfd sp!, {r1-r3, r12, pc}
}

#ifdef COOP_DIAGNOSTIC_PLAYER_COST
// SDK Timer0 is initialized by retail. Observe it; never reconfigure it.
// Elapsed ticks include interrupts and native I/O/GPU waits, not CPU cycles.
u32 coopPlayerCostStage=0;
enum { COOP_COST_KINDS=8 };
u32 coopPlayerCosts[COOP_COST_KINDS*2][6]={{0}};
struct CoopCostScope { u32 active,start,stage,tick,bucket; };
static CoopCostScope coopPlayerBehaviorCost={0,0,0,0,0};
static void *coopPlayerCostActor=0;

static bool CoopCostReady() {
    return coopEnabled && data_0209fc68==4 && coopStageIdentity &&
        !coopStageLoading && !coopMenuLoading && !coopSceneInitializing &&
        !coopTitleLoading && !(*(volatile u16 *)0x020a104c&0x4000) &&
        *(volatile u16 *)0x020a6430;
}
static void CoopCostBegin(CoopCostScope *scope,unsigned kind) {
    scope->active=0;
    if (!CoopCostReady())return;
    if (coopPlayerCostStage!=coopStageIdentity) {
        for (unsigned row=0;row<COOP_COST_KINDS*2;++row)
            for (unsigned field=0;field<6;++field)coopPlayerCosts[row][field]=0;
        coopPlayerCostStage=coopStageIdentity;
    }
    scope->stage=coopStageIdentity;
    scope->tick=data_020a1154[0];
    scope->bucket=kind+(*(volatile u8 *)0x0209f2c4 ? COOP_COST_KINDS : 0);
    scope->active=1;
    scope->start=(u32)func_02059650();
}
static void CoopCostFinish(CoopCostScope *scope) {
    if (!scope->active)return;
    u32 elapsed=(u32)func_02059650()-scope->start;
    scope->active=0;
    if (!CoopCostReady() || scope->stage!=coopStageIdentity ||
        scope->tick!=data_020a1154[0])return;
    volatile u32 *row=coopPlayerCosts[scope->bucket];
    ++row[0]; // Odd while updating; RAM observers discard partial records.
    u32 low=row[2]+elapsed;
    row[3]+=low<row[2];
    row[2]=low;
    if (!row[1] || elapsed>row[4])row[4]=elapsed;
    if (!row[1] || elapsed<row[5])row[5]=elapsed;
    ++row[1];
    ++row[0];
}
static void CoopCostPlayerPart(void *model,const Vector3 *scale,unsigned kind) {
    CoopCostScope scope;
    CoopCostBegin(&scope,kind);
    ((dExtSimpleModel_c *)model)->dExtSimpleModel_c::Render(scale);
    CoopCostFinish(&scope);
}
void CoopCostBodyRender(void *model,const Vector3 *scale) { CoopCostPlayerPart(model,scale,1); }
void CoopCostHeadRender(void *model,const Vector3 *scale) { CoopCostPlayerPart(model,scale,2); }
void CoopCostOpaqueRender(dScStage_c *scene) {
    CoopCostScope scope; CoopCostBegin(&scope,4);
    scene->RenderModel(); CoopCostFinish(&scope);
}
void CoopCostShadowRender() {
    CoopCostScope scope; CoopCostBegin(&scope,5);
    dExtShadowModel_c::RenderAll(); CoopCostFinish(&scope);
}
void CoopCostTransparentRender(dScStage_c *scene) {
    CoopCostScope scope; CoopCostBegin(&scope,6);
    scene->RenderModelTransparent(); CoopCostFinish(&scope);
}
void CoopCostCollisionProcess() {
    CoopCostScope scope; CoopCostBegin(&scope,7);
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    CoopCollisionProcess();
#else
    dCc_c::Process();
#endif
    CoopCostFinish(&scope);
}
int CoopCostStageRender(void *scene) {
    CoopCostScope scope;
    CoopCostBegin(&scope,3);
    int result=CoopOriginalStageRender(scene);
    CoopCostFinish(&scope);
    return result;
}
#endif

static void CoopSeedActor(dActor_c *actor,u32 frame) {
    u32 identity=actor->uniqueID-coopStageIdentity;
    u32 seed=frame^(identity*0x9e3779b9);
    seed^=seed>>16;
    seed*=0x85ebca6b;
    data_0209e650=seed^(seed>>13);
}

u32 coopActorInitializationsSeeded=0;

int CoopActorBeforeInit(dActor_c *actor) {
    int result=CoopOriginalActorBeforeInit(actor);
    if (result && coopEnabled && data_0209fc68 && coopStageIdentity) {
        // Initial AI timers/headings must not inherit random draws from this
        // console's camera, effects or differently timed wireless file reads.
        // Initialization can occur on different NET ticks, so use level and
        // stage-relative creation identity without the live packet clock.
        CoopSeedActor(actor,0x6d2b79f5^((u32)data_0209f2f8*0x85ebca6b));
        ++coopActorInitializationsSeeded;
    }
    return result;
}

int CoopActorBefore(void *actor) {
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
    coopPlayerCostActor=0;
    coopPlayerBehaviorCost.active=0;
#endif
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
        CoopSeedActor((dActor_c *)actor,data_020a1154[0]);
    }
    if (!result && coopEnabled) {
        gActivePlayerSlot = data_020a0f10;
        data_0209f250 = data_020a0f10;
    }
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
    if (result)for (unsigned slot=0;slot<4;++slot)
        if (data_0209f394[slot]==actor) {
            coopPlayerCostActor=actor;
            CoopCostBegin(&coopPlayerBehaviorCost,0);
            break;
        }
#endif
    return result;
}

void CoopActorAfter(dActor_c *actor, u32 success) {
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
    if (coopPlayerCostActor==actor)CoopCostFinish(&coopPlayerBehaviorCost);
    coopPlayerCostActor=0;
#endif
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

#ifdef COOP_EXPERIMENTAL_COLLISION_BROADPHASE
__asm void CoopCollisionHorizontalRead(void) {
    // This replaces only the norm call in the native cylinder pair walk.
    // r4 points to its current head, r8 is the other node, r0 separation.
    // Scratch r0-r3/r12 match the original norm's ABI; saved registers and
    // the caller's stack are untouched. No helper-call overhead on rejection.
    ldr r1,=coopEnabled
    ldr r1,[r1]
    cmp r1,#0
    beq nativeLength
    ldr r1,=0x0209fc68
    ldr r1,[r1]
    cmp r1,#4
    bne nativeLength
    ldr r1,[r4]
    ldr r1,[r1,#4]
    tst r1,#0xe0000000
    bne nativeLength
    ldr r2,[r8,#4]
    tst r2,#0xe0000000
    bne nativeLength
    add r1,r1,r2
    cmp r1,#0
    beq nativeLength
    ldr r2,[r0]
    ldr r3,[r0,#8]
    cmp r2,#0
    rsbmi r2,r2,#0
    cmp r3,#0
    rsbmi r3,r3,#0
    orr r12,r2,r3
    // Both axes must be inside the original signed-result sqrt domain,
    // even if only one axis suffices to establish a separated pair.
    tst r12,#0xe0000000
    bne nativeLength
    cmp r2,r1
    cmplo r3,r1
    movhs r0,r1
    bxhs lr
nativeLength:
    b Vec3_HorzLen
}
#endif

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
#ifdef COOP_EXPERIMENTAL_COLLISION_PLAN
    Patch(0x02014b0c,(void *)CoopCollisionPairRead);
    Patch(0x0203c6bc,(void *)CoopCollisionVAllocate);
    Patch(0x0203c568,(void *)CoopCollisionVReallocate);
    PatchCall(0x02014d0c,(void *)CoopCollisionNotify);
    PatchCall(0x02014dcc,(void *)CoopCollisionNotify);
#ifndef COOP_DIAGNOSTIC_PLAYER_COST
    PatchCall(0x0202ba14,(void *)CoopCollisionProcess);
#endif
#endif
#ifdef COOP_EXPERIMENTAL_COLLISION_BROADPHASE
    PatchCall(0x02014bb4,(void *)CoopCollisionHorizontalRead);
#endif
#ifdef COOP_DIAGNOSTIC_PLAYER_COST
    Patch(0x0202b8a4,(void *)CoopCostStageRender);
    PatchCall(0x0202b998,(void *)CoopCostOpaqueRender);
    PatchCall(0x0202b99c,(void *)CoopCostShadowRender);
    PatchCall(0x0202b9a4,(void *)CoopCostTransparentRender);
    PatchCall(0x0202ba14,(void *)CoopCostCollisionProcess);
#endif
#ifdef COOP_EXPERIMENTAL_ANIMATION_CACHE
    Patch(0x0203c6cc,(void *)CoopAnimationHeapAllocate);
    Patch(0x0202c9a8,(void *)CoopAnimationStageCleanup);
    Patch(0x0203c578,(void *)CoopAnimationHeapReallocate);
    Patch(0x0203c5d0,(void *)CoopAnimationMaxMemory);
    Patch(0x0203c5f8,(void *)CoopAnimationMaxMemory);
    Patch(0x0203c5ac,(void *)CoopAnimationMemoryLeft);
#endif
    PatchCall(0x02010ba4,(void *)CoopShadowFlagsRead);
    PatchCall(0x02010bf0,(void *)CoopShadowFlagsRead);
#ifdef COOP_DIAGNOSTIC_RENDER_COST
    PatchCall(0x0202b998,(void *)CoopDiagnosticOpaqueRender);
    PatchCall(0x0202b9a4,(void *)CoopDiagnosticTransparentRender);
#endif
    Patch(0x02017060,(void *)CoopTrimResourceModel);
    Patch(0x020186c0,(void *)CoopResolveFile);
    Patch(0x020185c0,(void *)CoopOpenFile);
    Patch(0x0201834c,(void *)CoopLoadDiskFile);
    Patch(0x02062200,(void *)CoopWirelessReset);
    Patch(0x02030e4c,(void *)CoopConnectionUpdate);
    Patch(0x0202b0fc,(void *)CoopLoadSkybox);
    PatchCall(0x02024d40,(void *)CoopCameraInputFlagsRead);
    Patch(0x0200d0ac,(void *)CoopCameraFar);
    Patch(0x0200d064,(void *)CoopCameraNear);
    Patch(0x0200d304,(void *)CoopCameraBehind);
    Patch(0x0200ca14,(void *)CoopCameraFov);
    Patch(0x0200d7e0,(void *)CoopCameraFirstPerson);
    Patch(0x0200d81c,(void *)CoopCameraNormal);
    Patch(0x0200d3f8,(void *)CoopCameraLookTarget);
    Patch(0x0200d10c,(void *)CoopCameraModeD10c);
    Patch(0x0200d148,(void *)CoopCameraModeD148);
    Patch(0x0200d438,(void *)CoopCameraModeD438);
    Patch(0x0200d474,(void *)CoopCameraModeD474);
    Patch(0x0200d508,(void *)CoopCameraModeD508);
    Patch(0x0200d544,(void *)CoopCameraModeD544);
    Patch(0x0200d580,(void *)CoopCameraModeD580);
    Patch(0x0200d5c0,(void *)CoopCameraModeD5c0);
    Patch(0x0200d5fc,(void *)CoopCameraModeD5fc);
    Patch(0x0200d63c,(void *)CoopCameraModeD63c);
    Patch(0x0200d678,(void *)CoopCameraModeD678);
    Patch(0x0200d6b4,(void *)CoopCameraModeD6b4);
    Patch(0x0200d6f0,(void *)CoopCameraModeD6f0);
    Patch(0x0200d72c,(void *)CoopCameraModeD72c);
    Patch(0x0200d768,(void *)CoopCameraModeD768);
    Patch(0x0200d7a4,(void *)CoopCameraModeD7a4);
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
    Patch(0x02011268,(void *)CoopActorBeforeInit);
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
