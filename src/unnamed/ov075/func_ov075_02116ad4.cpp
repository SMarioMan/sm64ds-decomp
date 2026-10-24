//cpp
#include "dScEntry_c.h"
#include "types.h"

namespace G2S {
void *GetBG2ScrPtr(void);
}

namespace GX {
void LoadBGPltt(const void *p, u32 a, u32 b);
void LoadOBJPltt(const void *p, u32 a, u32 b);
}

extern dScEntry_c::StepSet data_ov075_0211d888;

extern "C" {
/* Runtime asset handles resolved through the overlay 0 file table. */
enum func_ov075_02116ad4_AssetId {
    ASSET_D_2D_BATTLE_FRAMEWORK_GAMESTART_P_NSC_BIN = 0x025e
};

extern int func_0203d9b4(void);
extern void func_0200f13c(void);

extern u32 LoadCompressedFileAt(int fileID, void *target);
extern int func_0200f0bc(void);
extern void DecompressLZ16(void *src, int dst);
extern void *LoadFile(int handle);

extern void Deallocate(void *ptr);

extern int func_0203da3c(void);
extern void func_02030aa4(int arg);
extern void func_ov075_02116e00(void *p);
extern struct fBase_c *_ZN7dBase_c5SpawnEjP7fBase_cii(u32 a, void *b, int c, int d);

extern void *data_0208a0e4[];
extern int data_ov075_0211c9a4[];
extern void *data_0209f5c0;

int func_ov075_02116ad4(void *arg) {
    dScEntry_c *scene = reinterpret_cast<dScEntry_c *>(arg);
    void *tmp;
    int mode;

    if (scene->param1 != 0 || func_0203d9b4() != 0) {
        func_0200f13c();
        if (func_0203d9b4() != 0) {
            LoadCompressedFileAt(ASSET_D_2D_BATTLE_FRAMEWORK_GAMESTART_P_NSC_BIN,
                                 G2S::GetBG2ScrPtr());
        }
        DecompressLZ16(data_0208a0e4[func_0200f0bc()], 0x6600000);
    }
    LoadCompressedFileAt(data_ov075_0211c9a4[func_0200f0bc()], (void *)0x6400000);

    tmp = LoadFile(0x8412);
    GX::LoadOBJPltt(tmp, 0, 0xc0);
    Deallocate(tmp);

    tmp = LoadFile(0x980b);
    GX::LoadBGPltt(tmp, 0, 0xc0);
    Deallocate(tmp);

    scene->mStepDelay = 0;
    scene->mIconCount = 0;

    if (scene->param1 == 0) {
        if (func_0203da3c() == 0) {
            func_02030aa4(0);
            scene->SetSteps(&data_ov075_0211d888);
        } else {
            scene->SetSteps(&EntryPlayerSelectIntroSteps);
        }
        func_ov075_02116e00(arg);
        mode = 0;
    } else {
        scene->SetSteps(&EntryCourseSelectSteps);
        mode = 2;
    }

    scene->mEntObj = (dEntObj_c *)_ZN7dBase_c5SpawnEjP7fBase_cii(0x15a, data_0209f5c0, mode, 0);
    return 1;
}
}
