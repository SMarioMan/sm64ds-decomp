#include "nitro/fx/fx.h"
typedef struct { int x, y, z; } Vec3;
/* A path point: a negative flag ends the path; amt (whole units) feeds the
   fixed-point reciprocal that scales progress through the segment. */
typedef struct {
    signed char flag;
    unsigned char amt;
    short x, y, z;
} Elem;

/* The path table the script ops hand in (camera and demo paths): a point
   count, then the Elem array. */
typedef struct {
    unsigned char numPoints; /* 0x00 */
    unsigned char pad_01[3];
    Elem *points; /* 0x04 */
} PathTable;

extern void func_ov002_020effb8(void* a0, int m, Vec3* v0, Vec3* v1, Vec3* v2, Vec3* v3);
extern int func_02053200(int x);

int func_02008b4c(void* a0, short* p1, int* p2, char* tbl) {
    int idx;
    Elem *elem;
    PathTable *path = (PathTable *)tbl;
    int i;
    Vec3 v[4];
    int lo, hi;
    int m;

    idx = *p1;
    if (idx + 3 >= path->numPoints) {
        return 1;
    }

    elem = path->points + idx;

    if (elem[0].flag < 0 || elem[1].flag < 0 || elem[2].flag < 0) {
        return 1;
    }

    for (i = 0; i < 4; i++) {
        int x = elem[i].x << 12;
        int z = elem[i].z << 12;
        int y = elem[i].y << 12;
        v[i].x = x;
        v[i].y = y;
        v[i].z = z;
    }

    func_ov002_020effb8(a0, *p2, &v[0], &v[1], &v[2], &v[3]);

    lo = 0;
    hi = 0;
    if (elem[1].amt != 0) {
        lo = func_02053200(elem[1].amt << 12);
    }
    if (elem[2].amt != 0) {
        hi = func_02053200(elem[2].amt << 12);
    }

    {
        int d = hi - lo;
        m = *p2;
        *p2 = lo + FX_MUL(d, m) + m;
    }

    if (*p2 >= 0x1000) {
        *p1 = *p1 + 1;
        *p2 -= 0x1000;
    }

    return 0;
}
