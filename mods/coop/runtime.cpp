//cpp
// Experimental story-mode session hooks. The original wireless lobby provides
// player selection and input exchange; changes are confined to this mod.
#include "types.h"
#include "SaveData.h"
#include "Heap.h"
#include "Sound.h"

extern "C" {
void PrepareVsMode(void);
void SetPlayerGlobals(void);
void SetNumPlayers(int count);
void UnloadOverlay(int index);
void UnloadArchives(void);
int CoopOriginalEntryCleanup(void *scene);
void CoopOriginalLoadLevelOverlays(int level);
void LoadLevelNoReturn(int level, u32 entrance, u32 star, u32 reason);
int LoadArchive(int index);
void UnloadArchive(int index);
extern u8 data_0209caa0[];
extern u8 data_0209f2d8;
extern u8 data_0209fc50;
extern s8 data_02092124;
extern u8 data_0209f228[];
extern u8 data_02092778;
extern void *data_020a0eac;


// Located alongside the injected code, outside the game's heap/overlay ranges.
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
    for (int archive = 2; archive <= 5; ++archive)
        UnloadArchive(archive);
    LoadArchive(7);
    previous->SetDefault();
    // Stage initialization loads the story overlay set after the lobby has
    // finished. Loading it inside the lobby would risk overwriting live code.
    data_0209f2d8 = 0;
}

int CoopEntryCleanup(void *scene) {
    int result = CoopOriginalEntryCleanup(scene);
    // Unmount cached NARCs while their owning ENTRY heap is still alive.
    // STAGE creates a different heap and must reload its own archives.
    if (coopEnabled)
        UnloadArchives();
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

int CoopSaveCurrentFile(void) {
    // A session has not selected a host save slot yet. Never let the VS scratch
    // save overwrite an existing adventure file, on either host or clients.
    if (coopEnabled)
        return 0;
    if (!SaveData::SaveFile(data_0209caa0[0x328], (FileSaveData *)data_0209caa0))
        return 0;
    return SaveData::SaveMinigames((MinigameSaveData *)(data_0209caa0 + 0x44));
}
}
