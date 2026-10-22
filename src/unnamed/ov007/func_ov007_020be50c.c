extern int func_ov007_020c3df4(int a, void* b);
extern void* func_ov007_020c3f00(int* r6, void* r4);
extern int func_ov007_020c3ee8(int a, int b);
extern void Sprite_SetAnimation(char *c, int r1, int r2, int r3, int sp0);
extern void func_0204dc84(char *p);
extern void func_ov007_020be8b8(void);

extern int* data_ov007_0210342c;
extern int* data_ov007_02104bc0;

extern int data_ov007_020d7c6c;
extern int data_ov007_02103234;

/* The 0x44-byte OAM sprite node func_ov007_020c11ac allocates; names as in
 * func_ov007_020ade58, only the slot this file writes. */
typedef struct Ov007OamNode {
    char pad_00[0x18];
    void **anims; /* 0x18: the node's animations (func_ov007_020c11ac) */
} Ov007OamNode;

/* A func_ov007_020c40d4 record; node as in func_ov007_020be684, margin as
 * in func_ov007_020c3fe4, which shows the node only while it lies within
 * margin pixels of the screen. */
typedef struct Ov007SpriteItem {
    Ov007OamNode *node; /* 0x00 */
    char pad_04[6];
    unsigned char margin; /* 0x0a */
} Ov007SpriteItem;

/* The sprite group func_ov007_020c3f00 builds; names as there. +0x0c (the
 * extra func_ov007_020c40d4 record) stays raw. */
typedef struct Ov007SpriteGroup {
    int *layout;             /* 0x00: [0] is the item count */
    Ov007OamNode *root;      /* 0x04: the items' parent */
    Ov007SpriteItem **items; /* 0x08: layout[0] records */
} Ov007SpriteGroup;

/* The manager's +0x74: the 2D display record func_ov007_020b7594
 * allocates; names as in func_ov007_020ade58, only the slots read here. A
 * bank's +0xc (its array of 0x10-byte animations) stays raw. */
typedef struct Ov007Display {
    void *oamListMain; /* 0x00 */
    void *oamListSub;  /* 0x04 */
    char pad_08[0x34];
    char **spriteBanks; /* 0x3c: the six func_ov007_020c9688 sprite banks */
} Ov007Display;

/* data_ov007_0210342c: the overlay's manager; only the slot read here. */
typedef struct Ov007Work {
    char pad_00[0x74];
    Ov007Display *display; /* 0x74: func_ov007_020b6d40 */
} Ov007Work;

typedef char
    Ov007SpriteItem_margin_must_be_at_0xa[(int)&((Ov007SpriteItem *)0)->margin == 0xa ? 1 : -1];
typedef char Ov007Display_spriteBanks_must_be_at_0x3c[(int)&((Ov007Display *)0)->spriteBanks == 0x3c
                                                          ? 1
                                                          : -1];
typedef char Ov007Work_size_must_be_0x78[sizeof(Ov007Work) == 0x78 ? 1 : -1];

/* The extern keeps the tree's int * spelling; the typed view is reached
 * through a cast macro. */
#define WORK ((Ov007Work *)data_ov007_0210342c)

/* Builds the sprite group (and its tracking records) at
 * data_ov007_02104bc0 in the sub OAM list: every item shows sprite bank 2's
 * animation 1 with an 8-pixel margin, the extra record animations 2 and 0
 * with a 0x20-pixel one. */
void func_ov007_020be50c(void) {
    int *t;
    Ov007SpriteGroup *n;
    Ov007SpriteItem *e;
    Ov007OamNode *ef0;
    int *t2;
    int count;
    int i;
    int off;

    t = (int *)WORK->display->spriteBanks;

    data_ov007_02104bc0 = (int *)func_ov007_020c3df4(0, (void *)0x108);
    data_ov007_02104bc0[0] = (int)func_ov007_020c3f00(&data_ov007_020d7c6c, (void *)2);

    data_ov007_02104bc0[1] =
        func_ov007_020c3df4((int)&data_ov007_02103234, (void *)(data_ov007_020d7c6c * 0xc));

    func_ov007_020c3ee8(data_ov007_02104bc0[0], (int)WORK->display->oamListSub);

    n = (Ov007SpriteGroup *)data_ov007_02104bc0[0];
    count = n->layout[0];
    i = 0;
    if (count > 0) {
        off = i;
        do {
            e = n->items[i];
            t2 = (int *)t[2];
            ef0 = e->node;
            ef0->anims[0] = (void *)(t2[3] + 0x10);
            e->margin = 8;
            Sprite_SetAnimation((char *)e->node, 0, 1, 0, 0);
            func_0204dc84((char *)((char *)data_ov007_02104bc0[1] + off));
            n = (Ov007SpriteGroup *)data_ov007_02104bc0[0];
            i++;
            off += 0xc;
            count = n->layout[0];
        } while (i < count);
    }

    e = (Ov007SpriteItem *)((int *)n)[3];
    e->node->anims[0] = (void *)(((int *)t[2])[3] + 0x20);
    ef0 = e->node;
    ef0->anims[1] = (void *)((int *)t[2])[3];
    e->margin = 0x20;

    func_ov007_020be8b8();
}
