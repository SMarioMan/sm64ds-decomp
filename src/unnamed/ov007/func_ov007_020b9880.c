#include "types.h"
#include "Ov007MenuState.h"
#include "Ov007Tween.h"
#pragma opt_strength_reduction off

#include "Ov007Sprite.h"

/* The 0x1c record func_ov007_020b4c04 returns (names as in that file). */
typedef struct Ov007ItemView {
    struct Ov007Item *item; /* 0x00 */
    Ov007Sprite *sprite;    /* 0x04 */
} Ov007ItemView;

/* data_ov007_0210342c: the overlay's manager. No class or header names it;
 * only the slots this file touches are spelled. */
typedef struct Ov007Work {
    char pad_00[0x30];
    void *cameras[2]; /* 0x30: both built by func_ov007_020c023c; [1] is the
                         * one func_ov007_020b2160 loads into the projection */
    char pad_38[0x40];
    void *textures[11]; /* 0x78: func_ov007_020b697c builds them from the BMD textures */
    char pad_a4[0x70];
    Ov007ItemView *itemViews[0x18]; /* 0x114: func_ov007_020b693c, one per func_ov007_020b4c04 */
} Ov007Work;

/* data_ov007_02104ba0: the 0x4c record this function allocates and
 * func_ov007_020b9770 frees. It owns the touch picker func_ov007_020c690c
 * builds (fields named in func_ov007_020c5a6c). springSet and
 * introVariant as in func_ov007_020ba368,
 * restartCount/idleFrames as in func_ov007_020b9ca8, and
 * strokeCount/awaitingTap/strokeTime as in func_ov007_020ba05c. +0x38 stays
 * raw: only this file and func_ov007_020bbe60 (0x78, or 1.5x that for one
 * drawing) write it, and no reader shows its role. */
typedef struct Ov007PickerScene {
    void *picker;              /* 0x00: func_ov007_020c690c; freed by c6684 */
    Ov007MenuState *states[4]; /* 0x04: func_ov007_020c9388; [1] is the main one */
    char pad_14[8];
    /* 0x1c: which six-int row of data_ov007_020d7b80 func_ov007_020ba9bc
     * installs as the picker's springConstants */
    int springSet;
    int introVariant; /* 0x20: func_ov007_020ba368's intro shape */
    int restartCount; /* 0x24: func_ov007_020ba2e0 counts each restart */
    int idleFrames;   /* 0x28: frames with no touch and no key */
    int strokeCount;  /* 0x2c: picker->groupCount once a stroke is committed */
    /* 0x30: set here for mode 0; the next fresh press clears it and resets
     * the picker (func_ov007_020ba05c) */
    int awaitingTap;
    int strokeTime; /* 0x34: Q12 frames since the stroke began */
    char pad_38[4];
    s32 tweenOut[2];       /* 0x3c: bound as tweens[i]->out */
    Ov007Tween *tweens[2]; /* 0x44: func_ov007_020c908c */
} Ov007PickerScene;

typedef char Ov007PickerScene_size_must_be_0x4c[sizeof(Ov007PickerScene) == 0x4c ? 1 : -1];

/* data_ov007_02104b9c: the 0x14 record of the scene's sprites (freed by
 * func_ov007_020b9770). +0x00 is not touched here. */
typedef struct Ov007PickerSprites {
    char pad_00[4];
    Ov007Sprite *sprites[4]; /* 0x04: func_ov007_020c44e4 */
} Ov007PickerSprites;
extern void *func_ov007_020c3df4(int a, int b);
extern void *func_ov007_020c690c(int a0, int a1, int a2, int a3, void *a4, void *a5);
extern void *func_ov007_020c9388(int a);
extern void *func_ov007_020c908c(void *r5);
extern void *func_ov007_020c44e4(int a);
extern void func_ov007_020c43bc(void *a, int b);
extern void func_ov007_020c4388(char *r0, int r1);
extern void func_ov007_020bbe60(int idx);

extern char *data_ov007_02104ba0;
extern char *data_ov007_02104b9c;
extern char *data_ov007_0210342c;
/* The extern keeps the tree's char * spelling (the declaration-agreement
 * gate); the typed view is reached through a cast macro. */
#define WORK ((Ov007Work *)data_ov007_0210342c)
#define SCENE ((Ov007PickerScene *)data_ov007_02104ba0)
#define SCENE_SPRITES ((Ov007PickerSprites *)data_ov007_02104b9c)
extern int data_ov007_020d7b60;
extern int data_ov007_020d7b80;

void func_ov007_020b9880(int a0, int a1)
{
    int sp14, sp18, sp10, sp1c;
    int var_sl;
    Ov007Sprite *sprite;
    Ov007Sprite *itemSprite;
    Ov007Sprite *temp_r5;

    if (data_ov007_02104ba0 != 0)
        return;

    data_ov007_02104ba0 = (char *)func_ov007_020c3df4(0, 0x4c);
    data_ov007_02104b9c = (char *)func_ov007_020c3df4(0, 0x14);

    SCENE->picker = func_ov007_020c690c(0xc8, 0x1f4, 0x1f4, (int)WORK->cameras[0],
                                        &data_ov007_020d7b60, &data_ov007_020d7b80);

    SCENE->states[0] = func_ov007_020c9388(0);
    SCENE->states[1] = func_ov007_020c9388(-1);
    SCENE->states[2] = func_ov007_020c9388(0);
    SCENE->states[3] = func_ov007_020c9388(0);

    SCENE->springSet = 0;
    SCENE->introVariant = 0;
    SCENE->idleFrames = 0;
    SCENE->restartCount = 0;
    SCENE->strokeCount = 0;
    *(int *)(data_ov007_02104ba0 + 0x38) = 0;

    SCENE->tweens[0] = func_ov007_020c908c(&SCENE->tweenOut[0]);
    SCENE->tweens[1] = func_ov007_020c908c(&SCENE->tweenOut[1]);

    sp1c = 0;
    sp14 = 0x60000;
    sp18 = 0x100;
    sp10 = 1;

    for (var_sl = 0; var_sl < 2; var_sl++) {
        SCENE_SPRITES->sprites[var_sl] = func_ov007_020c44e4(sp10);
        sprite = SCENE_SPRITES->sprites[var_sl];

        if (var_sl == 0) {
            sprite->frames[0] = WORK->textures[3];
            sprite->depth = 0xfffcdf01;
            sprite->polygonId = 0x18;
        } else {
            sprite->frames[0] = WORK->textures[4];
            sprite->depth = -0x32000;
            sprite->polygonId = 0x17;
        }

        sprite->repeatV = 8;
        sprite->repeatU = sprite->repeatV;
        sprite->screenX = 0x80000;
        sprite->screenY = sp14;
        sprite->width = (s16)sp18;
        sprite->height = (s16)sp18;
        sprite->alpha = sp1c;

        func_ov007_020c43bc(sprite, (int)WORK->cameras[1]);
        func_ov007_020c4388((char *)sprite, (int)WORK->cameras[1]);
    }

    SCENE_SPRITES->sprites[2] = func_ov007_020c44e4(1);
    temp_r5 = SCENE_SPRITES->sprites[2];
    temp_r5->width = 0x48;
    temp_r5->height = 8;
    temp_r5->cornerColors[3] = 0x7f8a;
    temp_r5->cornerColors[0] = temp_r5->cornerColors[3];
    temp_r5->cornerColors[2] = 0x6e02;
    temp_r5->cornerColors[1] = temp_r5->cornerColors[2];
    temp_r5->drawFlags = temp_r5->drawFlags | 2;
    temp_r5->polygonId = 0x19;

    SCENE_SPRITES->sprites[3] = func_ov007_020c44e4(1);
    temp_r5 = SCENE_SPRITES->sprites[3];
    temp_r5->width = 0x48;
    temp_r5->height = 8;
    temp_r5->color = 0x294a;
    temp_r5->alpha = 0x5000;
    temp_r5->drawFlags = temp_r5->drawFlags | 1;
    temp_r5->polygonId = 0x1a;

    itemSprite = WORK->itemViews[5]->sprite;
    SCENE_SPRITES->sprites[2]->depth = itemSprite->depth - 0x10;
    SCENE_SPRITES->sprites[3]->depth = itemSprite->depth - 0xff;

    func_ov007_020c43bc(SCENE_SPRITES->sprites[2], (int)WORK->cameras[1]);
    func_ov007_020c43bc(SCENE_SPRITES->sprites[3], (int)WORK->cameras[1]);

    SCENE->strokeTime = 0;
    SCENE->tweens[0]->to = 0x800;
    SCENE->tweenOut[0] = SCENE->tweens[0]->to;

    if (a0 != 0) {
        if (a0 == 1) {
            SCENE->awaitingTap = 0;
            SCENE->tweenOut[1] = 0;
            SCENE->states[1]->requestedState = 0;
        }
    } else {
        SCENE->awaitingTap = 1;
        SCENE->tweenOut[1] = 0x1000;
        SCENE->states[1]->requestedState = 2;
    }

    if (a0 != 1)
        return;

    func_ov007_020bbe60(a1);
}
