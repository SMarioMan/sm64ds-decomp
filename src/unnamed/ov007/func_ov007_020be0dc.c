#include "types.h"
#include "dExtModel_c.h"

/* Names as in func_ov007_020bc02c and func_ov007_020b257c, only the slots
 * this file reads. */
typedef struct Ov007AnimPlayer {
    char pad_00[0x10];
    u16 frame; /* 0x10: the whole frame func_ov007_020c9110 last reached */
} Ov007AnimPlayer;

typedef struct Ov007Model {
    struct ModelComponents *model; /* 0x00 */
    char pad_04[0x14];
    Ov007AnimPlayer *boneAnim; /* 0x18 */
    char pad_1c[0x78];
    int visible; /* 0x94: func_ov007_020bbff0 renders only while it is nonzero */
} Ov007Model;

/* func_ov007_020beaa0's 0x1c-byte figure; func_ov007_020be850 returns one.
 * +0x01 (a copy of Work +0xec) stays raw on ev. */
typedef struct Ov007Figure {
    char pad_00[2];
    /* 0x02: func_ov007_020beaa0 seeds it (figure index != 0); this file
     * hands it to func_ov007_020b7690, the particle system lookup */
    u8 particleIndex;
    char pad_03;
    Ov007Model *model; /* 0x04: func_ov007_020bc6d4 */
} Ov007Figure;

/* The 0x44-byte OAM sprite node; names as in func_ov007_020c10ec. */
typedef struct Ov007OamNode {
    int x;       /* 0x00: Q12 screen x */
    int y;       /* 0x04: Q12 screen y */
    int visible; /* 0x08: func_ov007_020c0b78 draws this node and its children only when set */
    char pad_0c[8];
    u8 priority;    /* 0x14: OAM priority, used when the caller passes none (> 3) */
    s8 affineIndex; /* 0x15: OAM affine matrix, -1 = none */
    char pad_16[7];
    u8 animIndex; /* 0x1d: Sprite_SetAnimation's first argument */
} Ov007OamNode;

/* The sprite group func_ov007_020c3f00 builds; names as there. +0x0c (the
 * extra func_ov007_020c40d4 record) stays raw on G1. */
typedef struct Ov007SpriteGroup {
    int *layout;        /* 0x00 */
    Ov007OamNode *root; /* 0x04: the items' parent */
} Ov007SpriteGroup;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020b1fa4, only the slots this file reads. +0xec stays raw. */
typedef struct Ov007Work {
    char pad_00[0x24];
    /* 0x24, medium confidence: the preset func_ov007_020b1fa4 last applied;
     * this file moves the sprite down 0x14b under preset 4 */
    int cameraPreset;
    char pad_28[8];
    void *cameras[2]; /* 0x30: func_ov007_020c023c */
} Ov007Work;

extern char **data_ov007_02104bc0;
extern int data_ov007_02103230;
extern char *data_ov007_0210342c;
extern u16 data_ov007_020d7c58[];

int func_ov007_020be850(void);
void Sprite_SetAnimation(void *c, int a, int b, int d, int e);
void func_ov007_020bfd70(void *a0, void *a1, int *o1, int *o2);
int func_020538b8(int x, int y);
int _ZN4cstd3divEii(int a, int b);
void *func_ov007_020b7690(int i);
void func_ov007_020be684(void *a0, void *ctx);
void func_ov007_020c3fe4(void *p);

/* The externs keep the tree's spellings (the declaration-agreement gate);
 * the typed views are reached through cast macros. */
#define G1 (*data_ov007_02104bc0)
#define GROUP ((Ov007SpriteGroup *)G1)
#define WORK ((Ov007Work *)data_ov007_0210342c)
/* bone 0's transform */
#define BONE0 (fig->model->model->transforms)

int func_ov007_020be0dc(void) {
    int modelVisible = 0;
    char *actor;
    Ov007OamNode *node;
    void *system = 0;
    char *ev;
    Ov007Figure *fig;
    int val;
    int sp4, sp8;

    actor = *(char **)(*(char **)(G1 + 0xc));
    node = (Ov007OamNode *)actor;
    ev = (char *)func_ov007_020be850();
    fig = (Ov007Figure *)ev;

    if (ev == 0) {
        val = data_ov007_02103230;
    } else {
        u8 kind = *(u8 *)(ev + 1);
        Vector3 *pos;

        switch (kind) {
        case 0:
            if (node->animIndex != 0)
                Sprite_SetAnimation(node, 0, 1, 0, 0);
            break;
        case 1: {
            Ov007AnimPlayer *y = fig->model->boneAnim;
            int idv = y->frame;
            if (idv >= 0x226) {
                if (node->animIndex != 1)
                    Sprite_SetAnimation(node, 1, 1, 0, 0);
            } else {
                if (node->animIndex != 0)
                    Sprite_SetAnimation(node, 0, 1, 0, 0);
            }
        } break;
        }

        pos = &BONE0->t;
        func_ov007_020bfd70(WORK->cameras[0], pos, &sp4, &sp8);

        {
            char *P = data_ov007_0210342c;
            if (((Ov007Work *)P)->cameraPreset == 4) {
                sp8 += 0x14b;
            } else {
                sp8 += data_ov007_020d7c58[*(int *)(P + 0xec)];
            }
        }

        {
            int t0 = (short)sp4 << 0xc;
            int t1 = (short)sp8 << 0xc;
            node->x = t0;
            node->y = t1;
        }

        {
            int *pp = &BONE0->r.m[6];
            int d = func_020538b8(pp[0], pp[2]);
            int e = _ZN4cstd3divEii(d << 0xc, 0xffff);
            unsigned int scale = ((e * 0x12) >> 0xc) & 0xff;
            if (scale >= 0x12)
                scale = 0x11;
            if (node->animIndex == 0)
                Sprite_SetAnimation(node, 0, 0, 0, (int)scale);
        }

        if (node->animIndex == 0)
            node->affineIndex = 0xf;
        else
            node->affineIndex = -1;

        if (pos->z > 0)
            node->priority = 0;
        else
            node->priority = 3;

        modelVisible = fig->model->visible;
        val = fig->particleIndex;
    }

    data_ov007_02103230 = val;
    if (val != -1)
        system = func_ov007_020b7690(val);

    if (system != 0) {
        Ov007OamNode *q = GROUP->root;
        if (q->visible == 0)
            q->visible = 1;
        func_ov007_020be684(system, (void *)G1);
    } else {
        Ov007OamNode *q = GROUP->root;
        if (q->visible != 0)
            q->visible = 0;
    }

    func_ov007_020c3fe4(*(char **)(G1 + 0xc));

    {
        int r0 = node->visible;
        if (r0 != 0 && modelVisible != 0)
            r0 = 1;
        else
            r0 = 0;
        node->visible = r0;
        return r0;
    }
}
