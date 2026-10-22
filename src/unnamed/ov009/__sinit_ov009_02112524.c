#include "types.h"

/* Runtime asset handles resolved through the overlay 0 file table. */
enum sinit_ov009_02112524_AssetId {
    ASSET_MC_WATER_BMD = 0x0693,
    ASSET_MC_WATER_KCL = 0x0694
};

/* These ov009 globals are Vector3s (x, y, z in fx32): each one is registered
 * for destruction with Vector3's destructor below. Most blocks keep their `p`
 * local: spelling them through VEC3() like the others changes the .text bytes. */
#define VEC3(v) ((Vector3 *)(v))

extern void func_02017acc(void*, int);
extern void func_02017b4c(void*, int);
extern void func_020731dc(void*, void*, void*);
extern int func_02017ab4[];
extern int SharedFilePtr_Destruct_Clsn[];
extern int _ZN7Vector3D1Ev[];
extern int data_ov009_02113c68[];
extern int data_ov009_02113c70[];
extern int data_ov009_02113c78[];
extern int data_ov009_02113c84[];
extern int data_ov009_02113c90[];
extern int data_ov009_02113c9c[];
extern int data_ov009_02113ca8[];
extern int data_ov009_02113cb4[];
extern int data_ov009_02113cc0[];
extern int data_ov009_02113ccc[];
extern int data_ov009_02113cd8[];
extern int data_ov009_02113ce4[];
extern int data_ov009_02113cf0[];
extern int data_ov009_02113cfc[];
extern int data_ov009_02113d08[];
extern int data_ov009_02113d14[];
extern int data_ov009_02113d20[];
extern int data_ov009_02113d2c[];
extern int data_ov009_02113d38[];
extern int data_ov009_02113d44[];
extern int data_ov009_02113d50[];
extern int data_ov009_02113d5c[];
extern int data_ov009_02113d68[];
extern int data_ov009_02113d74[];
extern int data_ov009_02113d80[];
extern int data_ov009_02113d8c[];
extern int data_ov009_02113d98[];
extern int data_ov009_02113da4[];
extern int data_ov009_02113db0[];
extern int data_ov009_02113dbc[];
extern int data_ov009_02113dc8[];
extern int data_ov009_02113dd4[];
extern int data_ov009_02113de0[];
extern int data_ov009_02113dec[];
extern int data_ov009_02113df8[];
extern int data_ov009_02113e04[];
extern int data_ov009_02113e10[];
extern int data_ov009_02113e1c[];
extern int data_ov009_02113e28[];
extern int data_ov009_02113e34[];
extern int data_ov009_02113e40[];
extern int data_ov009_02113e4c[];
extern int data_ov009_02113e58[];
extern int data_ov009_02113e64[];
extern int data_ov009_02113e70[];
extern int data_ov009_02113e7c[];

void __sinit_ov009_02112524(void)
{
    func_02017acc(data_ov009_02113c68, ASSET_MC_WATER_BMD);
    func_020731dc(data_ov009_02113c68, func_02017ab4, data_ov009_02113c78);
    func_02017b4c(data_ov009_02113c70, ASSET_MC_WATER_KCL);
    func_020731dc(data_ov009_02113c70, SharedFilePtr_Destruct_Clsn, data_ov009_02113cc0);
    VEC3(data_ov009_02113d8c)->x = 0xfe94e000;
    VEC3(data_ov009_02113d8c)->y = (unsigned int)-0x5a000;
    VEC3(data_ov009_02113d8c)->z = 0xff60a000;
    func_020731dc(data_ov009_02113d8c, _ZN7Vector3D1Ev, data_ov009_02113d74);
    {
        Vector3 *p = (Vector3 *)data_ov009_02113d98;
        p->x = 0xfea20000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xff52e000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d80);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113da4;
        p->x = (unsigned int)-0x1540000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xff43e000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d08);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113db0;
        p->x = 0xfeb56000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xff344000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d14);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113dbc;
        p->x = 0xfebb0000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xff236000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d5c);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113dc8;
        p->x = 0xfebe2000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xff114000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d50);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113dd4;
        p->x = 0xfebe2000;
        p->y = (unsigned int)-0x5a000;
        p->z = 0xfeff2000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d44);
    }
    {
        VEC3(data_ov009_02113e34)->x = 0xfead4000;
        VEC3(data_ov009_02113e34)->y = (unsigned int)-0x320000;
        VEC3(data_ov009_02113e34)->z = 0xff682000;
        func_020731dc(data_ov009_02113e34, _ZN7Vector3D1Ev, data_ov009_02113d2c);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e40;
        p->x = 0xfebb0000;
        p->y = (unsigned int)-0x320000;
        p->z = 0xff5ba000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d20);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e4c;
        p->x = 0xfec5a000;
        p->y = (unsigned int)-0x320000;
        p->z = 0xff4d4000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113c90);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e58;
        p->x = 0xfecdc000;
        p->y = (unsigned int)-0x320000;
        p->z = (unsigned int)-0xc30000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113c84);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e64;
        p->x = 0xfed54000;
        p->y = (unsigned int)-0x320000;
        p->z = 0xff2cc000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113cfc);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e70;
        p->x = 0xfed54000;
        p->y = (unsigned int)-0x320000;
        p->z = 0xff25e000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113cf0);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e7c;
        p->x = 0xfed68000;
        p->y = (unsigned int)-0x320000;
        p->z = 0xff1aa000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113cb4);
    }
    {
        VEC3(data_ov009_02113de0)->x = 0xfeb2e000;
        VEC3(data_ov009_02113de0)->y = 0xffbd2000;
        VEC3(data_ov009_02113de0)->z = (unsigned int)-0x960000;
        func_020731dc(data_ov009_02113de0, _ZN7Vector3D1Ev, data_ov009_02113ccc);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113dec;
        p->x = 0xfebf6000;
        p->y = 0xffbd2000;
        p->z = 0xff5ce000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113cd8);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113df8;
        p->x = 0xfec96000;
        p->y = 0xffbd2000;
        p->z = 0xff4e8000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113ce4);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e04;
        p->x = 0xfed0e000;
        p->y = 0xffbd2000;
        p->z = 0xff3ee000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d68);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e10;
        p->x = 0xfed7c000;
        p->y = 0xffbd2000;
        p->z = 0xff2f4000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113ca8);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e1c;
        p->x = 0xfed9a000;
        p->y = 0xffbd2000;
        p->z = 0xff1e6000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113d38);
    }
    {
        Vector3 *p = (Vector3 *)data_ov009_02113e28;
        p->x = 0xfed72000;
        p->y = 0xffbd2000;
        p->z = 0xff0ce000;
        func_020731dc(p, _ZN7Vector3D1Ev, data_ov009_02113c9c);
    }
}
