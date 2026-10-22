#include "Ov007Sprite.h"

extern int func_ov007_020c43bc(void* a, void* b);
extern void func_ov007_020c4388(void* a, void* b);
extern void func_ov007_020c9f10(void* a, void* b, int c, int d);
extern void func_ov007_020c9d90(void* a, void* b);
extern char* data_ov007_0210342c;
extern char* data_ov007_02104bd4;

/* The overlay's camera (func_ov007_020c023c); names as in
 * func_ov007_020c0128, only the slot read here. */
typedef struct Ov007Camera {
    char pad_00[0x2c];
    int distance; /* 0x2c */
} Ov007Camera;

/* The record func_ov007_020b693c builds; names as in func_ov007_020b1390,
 * only the slot read here. */
typedef struct Ov007ItemView {
    void *item;          /* 0x00 */
    Ov007Sprite *sprite; /* 0x04: func_ov007_020c44e4 */
} Ov007ItemView;

/* data_ov007_0210342c: the overlay's manager; only the slot read here. */
typedef struct Ov007Work {
    char pad_00[0x114];
    Ov007ItemView *itemViews[0x18]; /* 0x114: func_ov007_020b693c */
} Ov007Work;

/* data_ov007_02104bd4: the 0x30-byte record func_ov007_020bf428 builds;
 * names as in func_ov007_020beeb0. */
typedef struct Ov007MeshScene {
    void *mesh;         /* 0x00: func_ov007_020cbbb0's Ov007Mesh */
    void *materials[2]; /* 0x04: func_ov007_020bee14 draws the mesh with each */
    void *wave;         /* 0x0c: func_ov007_020ca2a8's Ov007MeshWave */
    void *swings[8];    /* 0x10: func_ov007_020ca010's Ov007Swing, one per item */
} Ov007MeshScene;

typedef char Ov007MeshScene_size_must_be_0x30[sizeof(Ov007MeshScene) == 0x30 ? 1 : -1];
typedef char Ov007Work_size_must_be_0x174[sizeof(Ov007Work) == 0x174 ? 1 : -1];

/* The externs keep the tree's char * spelling; the typed views are reached
 * through cast macros. */
#define WORK ((Ov007Work *)data_ov007_0210342c)
#define SCENE ((Ov007MeshScene *)data_ov007_02104bd4)

/* Places swing idx on item view idx + 0xe's sprite: a copy of the sprite,
 * set the camera's distance in front of it (arg0 is cameras[0] for both
 * callers), is sized and moved into the world, and the swing takes its
 * position and world size and is bound to the mesh. arg0 keeps the tree's
 * char * spelling. */
void func_ov007_020bf57c(char *arg0, int idx) {
    Ov007Sprite *e = WORK->itemViews[idx + 0xe]->sprite;
    void *r4 = SCENE->swings[idx];

    Ov007Sprite buf;
    buf = *e;
    buf.depth = -((Ov007Camera *)arg0)->distance;
    func_ov007_020c43bc(&buf, arg0);
    func_ov007_020c4388(&buf, arg0);
    func_ov007_020c9f10(r4, &buf.pos, buf.worldWidth, buf.worldHeight);
    func_ov007_020c9d90(r4, SCENE->mesh);
}
