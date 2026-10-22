#include "types.h"
#pragma opt_strength_reduction off
#pragma opt_common_subs off
extern u8 data_ov007_02104bd4[];
extern u8 data_ov007_0210342c[];

extern void func_ov007_020cbb04(void *c);
extern int func_ov007_020ca26c(void *c);
extern void func_ov007_020c3d1c(void *thiz);
extern void func_ov007_020c9fa0(void *c);
extern int func_ov007_020c44c4(void *r4);

/* *data_ov007_02104bd4: the 0x30-byte record func_ov007_020bf428 builds;
 * names as in func_ov007_020beeb0. */
typedef struct Ov007MeshScene {
    void *mesh;         /* 0x00: func_ov007_020cbbb0's Ov007Mesh */
    void *materials[2]; /* 0x04: func_ov007_020bee14 draws the mesh with each */
    void *wave;         /* 0x0c: func_ov007_020ca2a8's Ov007MeshWave */
    void *swings[8];    /* 0x10: func_ov007_020ca010's Ov007Swing, one per item */
} Ov007MeshScene;

typedef char Ov007MeshScene_size_must_be_0x30[sizeof(Ov007MeshScene) == 0x30 ? 1 : -1];

/* data_ov007_0210342c: the overlay's manager; only the slots this file
 * frees. */
typedef struct Ov007Work {
    char pad_00[0x174];
    /* 0x174, medium confidence: the three Ov007Sprites func_ov007_020b42d8
     * builds (func_ov007_020c44e4) for func_ov007_020bf428; func_ov007_020b413c
     * draws a number with them: [2] once per decimal digit, [0] after the
     * digits, [1] alone when there is no number */
    void *numberSprites[3];
} Ov007Work;

typedef char Ov007Work_size_must_be_0x180[sizeof(Ov007Work) == 0x180 ? 1 : -1];

/* The externs keep the tree's u8[] spelling; the typed views are reached
 * through cast macros. */
#define WORK (*(Ov007Work **)data_ov007_0210342c)
#define SCENE (*(Ov007MeshScene **)data_ov007_02104bd4)

/* Tears down the mesh scene: frees the mesh, the wave, both materials and
 * the eight swings, then the manager's number sprites and the scene itself. */
void func_ov007_020bf304(void)
{
    int i;
    Ov007MeshScene *g;
    void *p;

    g = SCENE;
    if (g == 0) {
        return;
    }

    p = g->mesh;
    if (p != 0) {
        func_ov007_020cbb04(p);
        SCENE->mesh = 0;
    }

    p = SCENE->wave;
    if (p != 0) {
        func_ov007_020ca26c(p);
        SCENE->wave = 0;
    }

    for (i = 0; i < 2; i++) {
        if (SCENE->materials[i] != 0) {
            func_ov007_020c3d1c(SCENE->materials[i]);
            SCENE->materials[i] = 0;
        }
    }

    for (i = 0; i < 8; i++) {
        func_ov007_020c9fa0(SCENE->swings[i]);
    }

    for (i = 0; i <= 2; i++) {
        if (WORK->numberSprites[i] != 0) {
            func_ov007_020c44c4(WORK->numberSprites[i]);
            WORK->numberSprites[i] = 0;
        }
    }

    func_ov007_020c3d1c(SCENE);
    SCENE = 0;
}
