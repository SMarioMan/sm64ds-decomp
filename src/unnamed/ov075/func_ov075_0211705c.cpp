//cpp
#include "dScEntry_c.h"
#pragma opt_strength_reduction off
#include "common.h"

namespace G2S {
u16 *GetBG2ScrPtr(void);
}
extern "C" {

extern int func_0203da9c(void);
extern int TouchArea_Update(void *p, int x);
extern void func_ov001_020ab41c(void *p);
extern void func_ov075_02116c38(void *self);
extern void func_02012790(int a);
extern int GetSoundMode(void);
extern void SetSoundMode(int mode);
extern void func_ov001_020ab3f0(void *p);
extern int func_02033ae0(int a);
extern void TurnBacklightOn(void);
extern void TurnBacklightOff(void);

extern u16 data_020a0e5a[];

void func_ov075_0211705c(void *thiz) {
    dScEntry_c *scene = reinterpret_cast<dScEntry_c *>(thiz);
    int w = func_0203da9c();
    int dir;
    u16 flags;

    if (TouchArea_Update(&scene->mIcons[5], -1) != 0 ||
        TouchArea_Update(&scene->mIcons[8], -1) != 0 ||
        ((flags = data_020a0e5a[w << 1]) & 8) != 0 || (flags & 4) != 0 ||
        (scene->CheckMenuConfirm(-1) != 0 && scene->mSelectedIcon == 2)) {
        func_ov001_020ab41c(&scene->mIcons[5]);
        scene->mSelectedIcon = 2;
        func_ov075_02116c38(scene);
        func_02012790(0x11b);
    } else {
        dir = 0;
        if (scene->mIcons[2].mReady != 0) {
            if (TouchArea_Update(&scene->mIcons[2], -1) != 0 ||
                TouchArea_Update(&scene->mIcons[1], -1) != 0 ||
                TouchArea_Update(&scene->mIcons[6], -1) != 0) {
                scene->mSelectedIcon = 0;
                dir = 1;
            } else if (TouchArea_Update(&scene->mIcons[0], -1) != 0) {
                scene->mSelectedIcon = dir;
                dir = -1;
            } else if (scene->CheckMenuConfirm(-1) != 0) {
                if (scene->mSelectedIcon == 0)
                    dir = 1;
            }
            if (dir != 0 && scene->mSelectedIcon == 0) {
                int mode = GetSoundMode();
                unsigned newmode;
                if (dir > 0) {
                    if (mode == 2)
                        newmode = 0;
                    else
                        newmode = (mode + 1) & 0xff;
                    scene->mIcons[1].mOn = 0;
                    func_ov001_020ab3f0(&scene->mIcons[1]);
                } else {
                    if (mode == 0)
                        newmode = 2;
                    else
                        newmode = (mode - 1) & 0xff;
                    scene->mIcons[0].mOn = 0;
                    func_ov001_020ab3f0(&scene->mIcons[0]);
                }
                SetSoundMode(newmode);
                func_02033ae0((s16)(GetSoundMode() + 9));
                func_ov001_020ab41c(&scene->mIcons[2]);
                func_02012790(100);
            }
        }
        if (scene->mIcons[3].mReady != 0 && scene->mIcons[4].mReady != 0) {
            if ((scene->CheckMenuConfirm(-1) != 0 && scene->mSelectedIcon == 1) ||
                TouchArea_Update(&scene->mIcons[7], -1) != 0) {
                dir = 1;
                scene->mSelectedIcon = 1;
                if (scene->mIcons[3].mOn == 0)
                    dir = -1;
            }
            if (TouchArea_Update(&scene->mIcons[3], -1) != 0 ||
                (dir < 0 && scene->mSelectedIcon == 1)) {
                TurnBacklightOn();
                func_ov001_020ab41c(&scene->mIcons[3]);
                scene->mIcons[4].mOn = 0;
                scene->mSelectedIcon = 1;
                func_02012790(0x66);
            } else if (TouchArea_Update(&scene->mIcons[4], -1) != 0 ||
                       (dir > 0 && scene->mSelectedIcon == 1)) {
                TurnBacklightOff();
                scene->mIcons[3].mOn = 0;
                func_ov001_020ab41c(&scene->mIcons[4]);
                scene->mSelectedIcon = 1;
                func_02012790(0x66);
            }
        }
    }

    /* Light the selected option's label: two 11 x 2-tile strips of the
       BG2 screen from tile (2, 6), six rows apart, take palette 4 when
       their index is mSelectedIcon and palette 3 otherwise. dir is reused
       as the strip's tile offset. */
    {
        int i;
        int zero;
        u16 palOff;
        u16 palOn;
        u16 mask;
        i = 0;
        dir = i;
        zero = i;
        palOff = 0x3000;
        palOn = 0x4000;
        mask = 0xfff;
        do {
            u16 *p = G2S::GetBG2ScrPtr() + 6 * 32 + 2;
            p += dir;
            u16 pal = (i == scene->mSelectedIcon) ? palOn : palOff;
            int j = zero;
            do {
                unsigned v = *p;
                j++;
                v = v & mask;
                *p = v | pal;
                v = p[32];
                v = v & mask;
                p[32] = v | pal;
                p++;
            } while (j < 11);
            i++;
            dir += 6 * 32;
        } while (i < 2);
    }
}
}
