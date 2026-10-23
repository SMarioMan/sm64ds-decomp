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
void func_0203d918(void);
void func_0203d930(void);
void func_0203d854(void);
int func_0205d688(void *file, void *destination, int size, int async);
int func_0205d3f4(void *file);
void func_0201ffcc(void);
void func_02042778(void);
void func_0201fe08(void);
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
extern u8 data_020a0f10;
extern u8 data_0209fc50;
extern s8 data_02092124;
extern u8 data_0209f228[];
extern u8 data_02092778;
extern void *data_020a0eac;
extern int data_0209fc68;
extern u32 data_0209e650;
extern u32 data_020a1154[];
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
void _ZN4CP1514FlushDataCacheEv(void);


// Kept with the executable module in ROOT, across scene/overlay changes.
u32 coopEnabled = 0;
u32 coopEntryRetired = 0;

void CoopStartMatch(void *) {
    unsigned count = data_0209fc50;
    if (count < 1 || count > 4)
        return;

    PrepareVsMode();
    coopEnabled = 1;
    data_0209f2d8 = 0;
    // Story input is gated until the intro has completed. The lobby replaces
    // that introduction; begin a fresh, RAM-only Yoshi session.
    ((SaveData *)data_0209caa0)->flags2 |= 0x80;
    SetPlayerGlobals();
    SetNumPlayers(count);
    LoadLevelNoReturn(1, 0, 1, 0);
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
        UnloadOverlay(75);
        UnloadOverlay(100);
        UnloadOverlay(102);
        coopEntryRetired = 1;
    }
    CoopOriginalLoadLevelOverlays(level);
}

// 0: idle; 1: advertising loading; 2: initializing; 3: servicing a file wait.
u32 coopStageLoading = 0;
u32 coopStageIdentity = 0;

int CoopStageInit(void *scene) {
    dScStage_c *stage = (dScStage_c *)scene;
    if (!coopEnabled || !data_0209fc68)
        return CoopOriginalStageInit(scene);
    if (!stage->mWaitingForLoad) {
        if (!coopStageLoading) {
            coopStageIdentity = stage->uniqueID;
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
    coopStageLoading = 2;
    int result = CoopOriginalStageInit(scene);
    coopStageLoading = 0;
    if (stage->mWaitingForLoad)
        func_0203d930();
    return result;
}

int CoopReadFile(void *file, void *destination, int size) {
    if (coopStageLoading != 2 || data_020a613c != data_020a621c)
        return func_0205d688(file, destination, size, 0);
    coopStageLoading = 3;
    u32 *fields = (u32 *)file;
    u32 position = fields[0x28 / 4];
    func_0205d688(file, destination, size, 1);
    // Keep only NET alive while WFS fills this file. Scene behavior/drawing
    // must not run against STAGE's partially initialized resources.
    while (fields[0x0c / 4] & 1) {
        func_0201ffcc();
        func_02042778();
    }
    int result = func_0205d3f4(file) ? fields[0x28 / 4] - position : -1;
    coopStageLoading = 2;
    return result;
}

int CoopSaveCurrentFile(void) {
    // A session has not selected a host save slot yet. Never let the VS scratch
    // save overwrite an existing adventure file, on either host or clients.
    if (coopEnabled)
        return 0;
    if (!SaveData::SaveFile(data_0209caa0[0x328], (FileSaveData *)data_0209caa0))
        return 0;
    return SaveData::SaveMinigames((MinigameSaveData *)(data_0209caa0 + 0x44));
}

int CoopSceneBefore(void *scene) {
    int result = CoopOriginalSceneBefore(scene);
    // Shared scene decisions consume the host's synchronized controller.
    // Player behavior still selects each actor's own input record.
    unsigned id = ((dScene_c *)scene)->actorID;
    if (result && coopEnabled && (id == 3 || id == 4)) {
        gActivePlayerSlot = 0;
        data_0209f250 = 0;
        if (data_0209fc68)
            data_0209e650 = data_020a1154[0] ^ 0x6d2b79f5;
    }
    return result;
}

void CoopSceneAfter(dScene_c *scene, u32 success) {
    if (coopEnabled && (scene->actorID == 3 || scene->actorID == 4)) {
        data_0209f250 = data_020a0f10;
        gActivePlayerSlot = data_020a0f10;
    }
    scene->fBase_c::AfterBehavior(success);
}

int CoopActorBefore(void *actor) {
    // Doors and NPCs run separately from the scene. Their single-player
    // interaction paths must choose the same player and controller on every
    // replica. Player::Behavior still selects its own synchronized input.
    if (coopEnabled) {
        gActivePlayerSlot = 0;
        data_0209f250 = 0;
    }
    int result = CoopOriginalActorBefore(actor);
    if (result && coopEnabled && data_0209fc68) {
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
    if (coopEnabled) {
        gActivePlayerSlot = data_020a0f10;
        data_0209f250 = data_020a0f10;
    }
    actor->fBase_c::AfterBehavior(success);
}

static void Patch(u32 address, void *target) {
    *(volatile u32 *)address = 0xea000000 | (((u32)target-address-8)>>2 & 0x00ffffff);
}

void CoopRuntimeDispatch(unsigned operation, u32 argument) {
    // Reapply the ENTRY hook when that overlay is reloaded for a new party.
    Patch(0x02013b9c, (void *)CoopSaveCurrentFile);
    Patch(0x0202ded4, (void *)CoopLoadLevelOverlays);
    Patch(0x0202cc0c, (void *)CoopStageInit);
    Patch(0x0205d3d4, (void *)CoopReadFile);
    Patch(0x0202e3d4, (void *)CoopSceneBefore);
    Patch(0x0202e3c8, (void *)CoopSceneAfter);
    Patch(0x0211a210, (void *)CoopEntryCleanup);
    Patch(0x02010fd4, (void *)CoopActorBefore);
    Patch(0x02010fc8, (void *)CoopActorAfter);
    _ZN4CP1514FlushDataCacheEv();
    _ZN4CP1526InvalidateInstructionCacheEjj(0x02010fc8, 0x4c410);
    _ZN4CP1526InvalidateInstructionCacheEjj(0x0211a210, 4);
    if (operation == 0) {
        coopEntryRetired = coopStageLoading = 0;
        CoopLoadCourseResources((int)argument);
    } else if (operation == 1) {
        CoopStartMatch((void *)argument);
    }
}
}
