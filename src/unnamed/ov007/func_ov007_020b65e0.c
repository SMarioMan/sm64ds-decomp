extern void func_ov007_020c937c(void *state);
extern void func_ov007_020c020c(void *a);
extern void func_ov007_020c2410(int a);
extern void func_ov007_020c2018(int a);
extern void func_ov007_020c22f8(int a);
extern void func_ov007_020c9080(int a);
extern void func_ov007_020c3d1c(void *p);
extern void func_ov007_020c1620(int a);
extern void func_ov007_020b3edc(int a);
extern void func_ov007_020c9460(int a);
extern int func_ov007_020b4bd4(int *a);
extern void func_ov007_020b6cd0(void);
extern void func_ov007_020b283c(void);
extern void func_ov007_020b9770(void);
extern void func_ov007_020bf304(void);

/* data_ov007_0210342c: the overlay's manager, allocated by func_ov007_020b6a84
 * and friends and torn down here. No class or header names it; only slots
 * with an evidenced role are spelled. paletteState as in func_ov007_020b1718,
 * pad as in func_ov007_020b1cf0. +0x44..+0x4f (three func_ov007_020c946c
 * records) have no role yet and stay raw. */
typedef struct Ov007Work {
    char pad_00[4];
    struct Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388 */
    char pad_10[0x18];
    struct Ov007Settings *settings; /* 0x28: 0x3c bytes; +0x3a language */
    char pad_2c[4];
    void *cameras[2]; /* 0x30: func_ov007_020c023c; freed by func_ov007_020c020c */
    void *lights[2];  /* 0x38: func_ov007_020c241c(0/1); func_ov007_020c232c
                       * writes them to LIGHT_VECTOR / LIGHT_COLOR */
    /* 0x40: func_ov007_020bce70 requests palette n on it and blends over its
     * stateTicks */
    struct Ov007MenuState *paletteState;
    char pad_44[0xc];
    void *touch; /* 0x50: func_ov007_020c2068's 0x44-byte touch-panel record,
                       * updated by func_ov007_020c1db0, read by func_ov007_020b46b0 */
    void *pad;   /* 0x54: Ov007Pad, func_ov007_020c2304's 0x70-byte key record */
    char pad_58[0xc];
    int tweenOut[2];              /* 0x64: bound as tweens[i]->out */
    struct Ov007Tween *tweens[2]; /* 0x6c: func_ov007_020c908c */
    char pad_74[4];
    void *textures[11]; /* 0x78: func_ov007_020b697c builds them from the BMD textures */
    char pad_a4[0x70];
    struct Ov007ItemView
        *itemViews[0x18]; /* 0x114: func_ov007_020b693c, one per func_ov007_020b4c04 */
} Ov007Work;

extern char *data_ov007_0210342c;
/* The extern keeps the tree's char * spelling (the declaration-agreement
 * gate); the typed view is reached through a cast macro. */
#define WORK ((Ov007Work *)data_ov007_0210342c)

/* Teardown of the data_ov007_0210342c manager. */
#pragma opt_strength_reduction off
#pragma opt_common_subs off
void func_ov007_020b65e0(void)
{
    int i;

    if (WORK->states[0] != 0) {
        func_ov007_020c937c(WORK->states[0]);
        WORK->states[0] = 0;
    }
    if (WORK->states[1] != 0) {
        func_ov007_020c937c(WORK->states[1]);
        WORK->states[1] = 0;
    }
    if (WORK->states[2] != 0) {
        func_ov007_020c937c(WORK->states[2]);
        WORK->states[2] = 0;
    }
    if (WORK->cameras[0] != 0) {
        func_ov007_020c020c(WORK->cameras[0]);
        WORK->cameras[0] = 0;
    }
    if (WORK->cameras[1] != 0) {
        func_ov007_020c020c(WORK->cameras[1]);
        WORK->cameras[1] = 0;
    }
    if (WORK->lights[0] != 0) {
        func_ov007_020c2410((int)WORK->lights[0]);
        WORK->lights[0] = 0;
    }
    if (WORK->lights[1] != 0) {
        func_ov007_020c2410((int)WORK->lights[1]);
        WORK->lights[1] = 0;
    }
    if (WORK->touch != 0) {
        func_ov007_020c2018((int)WORK->touch);
        WORK->touch = 0;
    }
    if (WORK->pad != 0) {
        func_ov007_020c22f8((int)WORK->pad);
        WORK->pad = 0;
    }
    if (WORK->tweens[0] != 0) {
        func_ov007_020c9080((int)WORK->tweens[0]);
        WORK->tweens[0] = 0;
    }
    if (WORK->tweens[1] != 0) {
        func_ov007_020c9080((int)WORK->tweens[1]);
        WORK->tweens[1] = 0;
    }
    if (WORK->settings != 0) {
        func_ov007_020c3d1c(WORK->settings);
        WORK->settings = 0;
    }

    for (i = 0; i < 0xb; i++) {
        if (WORK->textures[i] != 0) {
            func_ov007_020c1620((int)WORK->textures[i]);
            WORK->textures[i] = 0;
        }
    }

    func_ov007_020b3edc(0x16);

    if (WORK->paletteState != 0) {
        func_ov007_020c937c(WORK->paletteState);
        WORK->paletteState = 0;
    }

    for (i = 0; i < 3; i++) {
        if (*(int *)(data_ov007_0210342c + i * 4 + 0x44) != 0) {
            func_ov007_020c9460(*(int *)(data_ov007_0210342c + i * 4 + 0x44));
            *(int *)(data_ov007_0210342c + i * 4 + 0x44) = 0;
        }
    }

    for (i = 0; i < 0x18; i++) {
        if (WORK->itemViews[i] != 0) {
            func_ov007_020b4bd4((int *)WORK->itemViews[i]);
            WORK->itemViews[i] = 0;
        }
    }

    func_ov007_020b6cd0();
    func_ov007_020b283c();
    func_ov007_020b9770();
    func_ov007_020bf304();

    if (data_ov007_0210342c == 0) {
        return;
    }

    func_ov007_020c3d1c((void *)data_ov007_0210342c);
    data_ov007_0210342c = 0;
}
