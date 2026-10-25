//cpp
// Load the resident module only after Download Play authentication.
#include "types.h"
#include "Heap.h"
#include "decl_common.h"

extern "C" {
void FS_InitFile(void *file);
int func_020185c0(void *file, unsigned fileID);
int FS_ReadFile(void *file, void *destination, int size);
int FS_CloseFile(void *file);
void _ZN4CP1526InvalidateInstructionCacheEjj(u32 address, u32 size);
void _ZN4CP1527FlushAndInvalidateDataCacheEjj(u32 address,u32 size);
extern mHeap::Heap_t *data_020a0e9c;

typedef void (*RuntimeEntry)(unsigned operation, u32 argument);

static RuntimeEntry LoadRuntime() {
    // These words are outside the client's pre-crt0 stub and parent loader.
    // The builder checks that the retail prefix cannot match this marker.
    volatile u32 *cache = (volatile u32 *)0x02004180;
    if (cache[0] == 0x31504f43)
        return (RuntimeEntry)cache[1];

    u32 file[18], header[6];
    FS_InitFile(file);
    if (!func_020185c0(file, COOP_RUNTIME_FILE))
        return 0;
    if (FS_ReadFile(file, header, 24) != 24 || header[0] != 0x31584248 ||
        header[2] < 32 || header[2] > 0x10000 || header[3] >= header[2] ||
        (header[3] & 3) || header[4] > header[2] / 4) {
        FS_CloseFile(file);
        return 0;
    }
#ifdef COOP_RUNTIME_PREFIX
    // Retail ARM9 begins at 0x02004000. The first 256 bytes below it retain
    // bootstrap diagnostics; this opt-in placement owns the remainder only
    // after the signed loader has handed control to the native game.
    if (header[2]>0x3f00) { FS_CloseFile(file); return 0; }
    u32 *body=(u32 *)0x02000100;
    _ZN4CP1527FlushAndInvalidateDataCacheEjj((u32)body,header[2]);
    if (FS_ReadFile(file,body,header[2])!=(int)header[2]) {
        FS_CloseFile(file); return 0;
    }
    u8 recordStorage[256+31];
    u32 *recordBuffer=(u32 *)(((u32)recordStorage+31)&~31u);
#else
    u32 storedSize = header[2] + header[4] * 4;
    // This module lives for the session. Keep it at ROOT's high end so
    // transient models/files can coalesce their ordinary low-end blocks.
    u32 *body = (u32 *)data_020a0e9c->Allocate(storedSize, -32);
    _ZN4CP1527FlushAndInvalidateDataCacheEjj((u32)body,storedSize);
    if (FS_ReadFile(file, body, storedSize) != (int)storedSize) {
        FS_CloseFile(file);
        data_020a0e9c->Deallocate(body);
        return 0;
    }
    FS_CloseFile(file);
    u32 *records = (u32 *)((u8 *)body + header[2]);
#endif
    s32 delta = (u32)body - header[1];
    for (unsigned i = 0; i < header[4]; ++i) {
#ifdef COOP_RUNTIME_PREFIX
        if (!(i&63)) {
            unsigned count=header[4]-i;
            if (count>64)count=64;
            _ZN4CP1527FlushAndInvalidateDataCacheEjj((u32)recordBuffer,count*4);
            if (FS_ReadFile(file,recordBuffer,count*4)!=(int)(count*4)) {
                FS_CloseFile(file); return 0;
            }
        }
        u32 record=recordBuffer[i&63];
#else
        u32 record = records[i];
#endif
        if ((record & 0x7fffffff) > header[2] - 4 || (record & 3)) {
#ifdef COOP_RUNTIME_PREFIX
            FS_CloseFile(file);
#else
            data_020a0e9c->Deallocate(body);
#endif
            return 0;
        }
        u32 *word = (u32 *)((u8 *)body + (record & 0x7fffffff));
        if (record & 0x80000000)
            *word = (*word & 0xff000000) | ((*word - (delta >> 2)) & 0x00ffffff);
        else
            *word += delta;
    }
#ifdef COOP_RUNTIME_PREFIX
    FS_CloseFile(file);
#else
    // Relocation records are installation-only. Return their tail to ROOT;
    // Reallocate shrinks this native expanding-heap block in place.
    data_020a0e9c->Reallocate(body, header[2]);
#endif
    _ZN4CP1514FlushDataCacheEjj((u32)body, header[2]);
    _ZN4CP1526InvalidateInstructionCacheEjj((u32)body, header[2]);
    cache[1] = (u32)body + header[3];
    cache[0] = 0x31504f43;
    return (RuntimeEntry)cache[1];
}

void CoopInstallResources(int course) {
    RuntimeEntry entry = LoadRuntime();
    if (entry)
        entry(0, course);
}

void CoopInstallMatch(void *scene) {
    RuntimeEntry entry = LoadRuntime();
    if (entry)
        entry(1, (u32)scene);
}
}
