//cpp
#include "Ov007Sprite.h"

namespace cstd { int div(int, int); }

extern "C" {
extern int func_ov007_020c5014(void *, int);
extern void func_ov007_020bdbcc(int, int);
}

/* data_ov007_02104ba0: the 0x4c record func_ov007_020b9880 allocates; names
 * as in func_ov007_020b91b4 and func_ov007_020ba05c, only the slots this
 * file touches. */
struct Ov007PickerScene {
    int picker; /* 0x00: func_ov007_020c690c */
    char pad_04[0x14];
    /* 0x18, medium confidence: func_ov007_020c5d5c's sum of each group's
     * last progress threshold, i.e. the drawing's whole stroke time */
    int totalStrokeTime;
    char pad_1c[0x18];
    int strokeTime; /* 0x34: Q12 frames since the stroke began */
    /* 0x38, medium confidence: the frames a replay of the drawing takes;
     * func_ov007_020bbe60 sets 0x78 (1.5 times that for one portrait) when
     * it loads a portrait drawing, func_ov007_020b9880 clears it */
    int replayFrames;
};

/* data_ov007_02104b9c: the 0x14 record of the scene's sprites
 * (func_ov007_020b9880); names as in func_ov007_020b91b4. */
struct Ov007PickerSprites {
    int slideProgress;       /* 0x00 */
    Ov007Sprite *sprites[4]; /* 0x04: func_ov007_020c44e4 */
};

typedef char Ov007PickerScene_replayFrames_must_be_at_0x38
    [(int)&((Ov007PickerScene *)0)->replayFrames == 0x38 ? 1 : -1];

/* The externs take the tree's char * spelling (include/decl_common.h); the
 * typed views are reached through cast macros. */
extern char *data_ov007_02104ba0;
extern char *data_ov007_02104b9c;

#define SCENE ((Ov007PickerScene *)data_ov007_02104ba0)
#define SPRITES ((Ov007PickerSprites *)data_ov007_02104b9c)

/* Replays the drawing one frame: strokeTime advances so that it covers
 * totalStrokeTime in replayFrames frames (param 0) or 0x168 frames, by at
 * least 0x1000 (one frame) a frame, and func_ov007_020c5014 moves the
 * picker's draw limit to it (strokeTime restarts when the limit steps on to
 * the next stroke). For param 0, sprites[0] also fades in up to alpha
 * 0x1f000. Returns 1 once the replay has passed the last stroke (for
 * param 0, only once sprites[0] is fully opaque). */
extern "C" int func_ov007_020bbd24(int param)
{
    int r4;
    int r5;

    if (param == 0)
        r4 = SCENE->replayFrames;
    else
        r4 = 0x168;

    r4 = cstd::div(SCENE->totalStrokeTime << 0xc, r4);
    if (r4 < 0x1000)
        r4 = 0x1000;

    r5 = func_ov007_020c5014((void *)SCENE->picker, SCENE->strokeTime >> 0xc);
    if (r5 == 1) {
        SCENE->strokeTime = 0;
    } else if (r5 == 0) {
        int *fp = (int *)(((int)&SCENE->strokeTime));
        *fp += r4;
    }

    func_ov007_020bdbcc(4, 4);

    switch (param) {
    case 0: {
        int *q = (int *)(((int)&SPRITES->sprites[0]->alpha));
        int v = *q;
        if (v <= 0x5000) {
            *q = v + 0x7d0;
            break;
        }
        if (v <= 0x14000) {
            *q = v + 0x190;
            break;
        }
        if (v <= 0x1f000) {
            *q = v + 0xbb8;
            break;
        }
        *q = 0x1f000;
        return r5 == 2;
    }
    case 1:
        return r5 == 2;
    }
    return 0;
}
