//cpp
#include "types.h"
#include "dScEntry_c.h"
#include "OamAttr.h"
struct OAM {
    static void Render(bool, OamAttr *, int, int, int, int, int, int, int, int);
};
extern "C" int _ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi(int, OamAttr*, int, int, int, int, int, int);
extern "C" int func_0203da9c(void);
extern "C" void func_ov075_0211621c(char *sl);
extern "C" int func_0200f0bc(void);
extern "C" void func_0202048c(void *dst, int a, int b);
extern u8 data_0209b2f0[];
extern OamAttr data_ov075_0211cb84;
extern OamAttr *data_ov075_0211c9f4[];
extern OamAttr *data_ov075_0211c9e0[];

extern "C" void func_ov075_021184b0(char *sl)
{
    dScEntry_c *scene = (dScEntry_c *)sl;
    int id = func_0203da9c();
    OAM::Render(false, &data_ov075_0211cb84, 0x80, 0x20, -1, -1, 0x1000, 0x1000, 0, -1);
    func_ov075_0211621c(sl);

    u8 *p = data_0209b2f0 + id;
    OamAttr *sb;
    if (*p != 0)
        sb = data_ov075_0211c9f4[func_0200f0bc()];
    else
        sb = data_ov075_0211c9e0[func_0200f0bc()];

    {
        int i = 0;
        int x = 0x80;
        int y = 0x60;
        do {
            int fix = (i == scene->mStepWork[1]) ? 0xe00 : 0x1000;
            _ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi(true, sb, x, y, -1, -1, fix, 0);
            if (sb->attr3 == 0xffff)
                break;
            sb++;
            i++;
        } while (1);

        /* mStepWork[1] is the sprite drawn at 0xe00 scale; every third
           frame (mStepWork[0]) it moves one along the string and wraps. */
        scene->mStepWork[0]++;
        if (scene->mStepWork[0] >= 3) {
            scene->mStepWork[0] = 0;
            scene->mStepWork[1]++;
            if (scene->mStepWork[1] > i)
                scene->mStepWork[1] = 0;
        }
    }

    if (*p != 0) {
        func_0202048c(&scene->mOamAnimations[2], 0x80, 0x88);
        func_0202048c(&scene->mOamAnimations[0], 0x80, 0x88);
    } else {
        func_0202048c(&scene->mOamAnimations[0], 0x80, 0x88);
        func_0202048c(&scene->mOamAnimations[3], 0x6c, 0x6e);
        func_0202048c(&scene->mOamAnimations[2], 0xa6, 0x6e);
    }
    func_0202048c(&scene->mOamAnimations[1], 0x80, 0x88);
}
