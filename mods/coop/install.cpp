//cpp
// Install only after Download Play authentication and player/course selection.
// The SDK constructs the signed child image partly from the parent's secure-area
// RAM, so modifying that RAM during ENTRY initialization breaks authentication.
#include "types.h"
#include "decl_common.h"

extern "C" {
extern const u32 CoopPayload[];
void CoopLoadCourseResources(int course);
void CoopStartMatch(void *scene);
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 start, u32 size);

static void Install() {
    volatile u32 *destination = (volatile u32 *)0x02004100;
    for (unsigned i = 0; i < COOP_PAYLOAD_SIZE / 4; ++i)
        destination[i] = CoopPayload[i];
    *(volatile u32 *)0x02013b9c = COOP_SAVE_BRANCH;
    *(volatile u32 *)0x0202ded4 = COOP_LEVEL_BRANCH;
    *(volatile u32 *)COOP_CLEANUP_ADDRESS = COOP_CLEANUP_BRANCH;
    _ZN4CP1514FlushDataCacheEjj(0x02004100, COOP_PAYLOAD_SIZE);
    _ZN4CP1514FlushDataCacheEjj(0x02013b9c, 4);
    _ZN4CP1514FlushDataCacheEjj(0x0202ded4, 4);
    _ZN4CP1514FlushDataCacheEjj(COOP_CLEANUP_ADDRESS, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(0x02004100, COOP_PAYLOAD_SIZE);
    _ZN4CP1526InvalidateInstructionCacheEjj(0x02013b9c, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(0x0202ded4, 4);
    _ZN4CP1526InvalidateInstructionCacheEjj(COOP_CLEANUP_ADDRESS, 4);
}

void CoopInstallResources(int course) {
    Install();
    CoopLoadCourseResources(course);
}

void CoopInstallMatch(void *scene) {
    Install();
    CoopStartMatch(scene);
}
}
