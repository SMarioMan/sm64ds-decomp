#include "types.h"

extern void func_020731dc(void*, void*, void*);
extern int data_ov002_0211116c[];
extern int _ZN7Vector3D1Ev[];
extern int data_ov002_02111160[];

void __sinit_ov002_0210804c(void) {
    /* A static Vector3, destroyed through _ZN7Vector3D1Ev. */
    ((Vector3 *)data_ov002_0211116c)->x = 0x80000;
    ((Vector3 *)data_ov002_0211116c)->y = 0;
    ((Vector3 *)data_ov002_0211116c)->z = 0x60000;
    func_020731dc(data_ov002_0211116c, _ZN7Vector3D1Ev, data_ov002_02111160);
}
