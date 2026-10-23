//cpp
// Load only the parent's bootstrap. Downloaded children use the original ENTRY
// initializer; their executable was loaded through the signed HaxxStation stage.
#include "types.h"
#include "decl_common.h"
extern "C" {
void FS_InitFile(void *file);
int func_020185c0(void *file, unsigned fileID);
int FS_ReadFile(void *file, void *out, int size);
int FS_CloseFile(void *file);
void *_ZN6Memory8AllocateEji(unsigned size, int align);
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
int CoopOriginalEntryInit(void *scene);

int CoopHeapBootstrap(void *scene) {
    int result = CoopOriginalEntryInit(scene);
    if (*(volatile u16 *)0x027ffc40 == 2 || result != 1)
        return result;
    u32 file[17], header[6];
    FS_InitFile(file);
    if (!func_020185c0(file, COOP_BOOTSTRAP_FILE) || FS_ReadFile(file, header, 24) != 24 || header[0] != 0x31584248)
        return 0;
    u32 storedSize=header[2]+header[4]*4;
    u32 *body = (u32 *)_ZN6Memory8AllocateEji(storedSize, 32);
    if (FS_ReadFile(file, body, storedSize) != (int)storedSize)
        return 0;
    u32 *records=(u32 *)((u8 *)body+header[2]);
    s32 delta = (u32)body - header[1];
    for (unsigned i = 0; i < header[4]; ++i) {
        u32 record=records[i];
        u32 *word = (u32 *)((u8 *)body + (record & 0x7fffffff));
        if (record & 0x80000000)
            *word = (*word & 0xff000000) | ((*word - (delta >> 2)) & 0x00ffffff);
        else
            *word += delta;
    }
    FS_CloseFile(file);
    _ZN4CP1514FlushDataCacheEjj((u32)body, header[2]);
    _ZN4CP1526InvalidateInstructionCacheEjj((u32)body, header[2]);
    ((int (*)(void *))((u8 *)body + header[3]))(scene);
    return result;
}
}
