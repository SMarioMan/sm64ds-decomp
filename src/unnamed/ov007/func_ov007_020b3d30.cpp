//cpp
#include "Ov007Sprite.h"

extern "C" {
extern void func_ov007_020c43bc(void*, int);
extern char* data_ov007_0210342c;
extern unsigned char data_ov007_020d7dc8[];
extern unsigned char data_ov007_020d7dd0[];
extern unsigned char data_ov007_020d7dd1[];
extern unsigned char data_ov007_020d7ddc[];
extern unsigned char data_ov007_020d7ddd[];
extern unsigned char data_ov007_020d7dc0[];
extern short data_ov007_020d7de8[];
extern short data_ov007_020d7dea[];

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020b9880, only the slots this file reads. */
struct Ov007Work {
    char pad_00[0x30];
    void *cameras[2]; /* 0x30: both built by func_ov007_020c023c; [1] is the
                         * one func_ov007_020b2160 loads into the projection */
    char pad_38[0x40];
    void *textures[11]; /* 0x78: func_ov007_020b697c builds them from the BMD textures */
};

typedef char Ov007Work_size_must_be_0xa4[sizeof(Ov007Work) == 0xa4 ? 1 : -1];

#define WORK ((Ov007Work *)data_ov007_0210342c)

/* Sets up sprite `thiz` as entry idx of the data_ov007_020d7dc0..
 * data_ov007_020d7dea tables: its texture, texel origin, pixel size, shadow
 * polygon id and shadow offset, and its depth; then sizes it in world space
 * through camera 1 (func_ov007_020c43bc). */
void func_ov007_020b3d30(char* thiz, int idx){
    Ov007Sprite *sprite = (Ov007Sprite *)thiz;
    sprite->frames[0] = WORK->textures[data_ov007_020d7dc8[idx]];
    sprite->texS = data_ov007_020d7dd0[idx * 2];
    sprite->texT = data_ov007_020d7dd1[idx * 2];
    sprite->width = data_ov007_020d7ddc[idx * 2];
    sprite->height = data_ov007_020d7ddd[idx * 2];
    sprite->shadowPolygonId = data_ov007_020d7dc0[idx];
    sprite->shadowOffset[0] = data_ov007_020d7de8[idx * 2];
    sprite->shadowOffset[1] = data_ov007_020d7dea[idx * 2];
    if (idx == 1)
        sprite->depth = -0x10c0;
    else
        sprite->depth = (int)0xffffef38;
    func_ov007_020c43bc(thiz, (int)WORK->cameras[1]);
}
}
