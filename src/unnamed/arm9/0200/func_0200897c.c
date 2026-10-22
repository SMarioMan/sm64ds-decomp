#include "types.h"
/* func_0200897c @ 0x0200897c, size 0x5c, ARM.
 * dCamera_c-cluster member taking (dCamera_c *self, void *arg).
 * arg is a dBgCh query. Always runs dBgCh::StopIgnoringVanishSurfaces on it.
 * Then, if the camera's owner dActor_c (self->owner @0x110) has actorID 0xbf
 * (PLAYER) AND Player::mIsVanish (owner+0x6fb) is set, runs
 * dBgCh::StartIgnoringVanishSurfaces. Finally always runs func_02035468(arg).
 * This is a C file, so the dBgCh members are called by their mangled names.
 *
 * Codegen note: the (actorID == 0xbf) test is held in an enum-typed boolean.
 * Under -O4 -enum int this materializes the comparison as a full 32-bit 0/1
 * value (cmp; moveq #1; movne #0; cmp #0; beq) instead of folding it into a
 * single branch -- that is what the ROM does. A plain `int` bool folds to a
 * bare `bne`; a `u8` bool masks with `ands #0xff`; only the (int-width) enum
 * bool gives the exact `cmp r0, #0`.
 */
enum Bool { FALSE, TRUE };

typedef struct dActor_c {
    char _pad0[0xc];
    u16 actorID;        /* 0x0c */
    char _pad1[0x6fb - (0xc + 2)];
    u8 flag6fb;         /* 0x6fb */
} dActor_c;

typedef struct dCamera_c {
    char _pad0[0x110];
    dActor_c *owner;       /* 0x110 */
} dCamera_c;

extern void _ZN5dBgCh26StopIgnoringVanishSurfacesEv(void *query);
extern void _ZN5dBgCh27StartIgnoringVanishSurfacesEv(void *query);
extern void func_02035468(void *arg);

void func_0200897c(dCamera_c *self, void *arg) {
    dActor_c *owner;
    enum Bool isType;
    _ZN5dBgCh26StopIgnoringVanishSurfacesEv(arg);
    owner = self->owner;
    isType = (enum Bool)(owner->actorID == 0xbf);
    if (isType && owner->flag6fb != 0) {
        _ZN5dBgCh27StartIgnoringVanishSurfacesEv(arg);
    }
    func_02035468(arg);
}
