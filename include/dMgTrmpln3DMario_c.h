#ifndef DMGTRMPLN3DMARIO_C_H
#define DMGTRMPLN3DMARIO_C_H

#include "types.h"
#include "dExtAnmModel_c.h"

/* dMgTrmpln3DMario_c, the Mario of Trampoline (ROM RTTI _ZTI18dMgTrmpln3DMario_c;
 * constructor 0x020cd12c, D1 0x020ccfc8; 0xd0 bytes, the stride the trampoline
 * scene's __cxa_vec_ctor builds four of).
 *
 * A layout view only, read through d_mg_trmpln2_mario.cpp's MARIO3D() cast; the
 * helpers there are still free functions over a char* record. The first five
 * fields are the jumper fields the drawn line writes, the same as
 * dMgTrmpln2Mario_c's (TrmpLine_PushJumper, unit020cd744.cpp). */
struct dMgTrmpln3DMario_c {
    void *mVtable;          /* 0x00 */
    Vector3 mContactNormal; /* 0x04 -- the drawn line's normal */
    s32 mContactOffset;     /* 0x10 -- signed distance from the line's centre */
    s32 mContactHalfWidth;  /* 0x14 -- the line's half width */
    u16 mContact;           /* 0x18 -- 0 none, 1 hit, 2 hard hit, 3 the line's end */
    u8 pad_1a[0x2];         /* 0x1a */
    Vector3 mPos;           /* 0x1c */
    Vector3 mPrevPos;       /* 0x28 -- mPos before this frame's move */
    Vector3 mVel;           /* 0x34 */
    s32 mGravityStep;       /* 0x40 -- ApproachLinear step of mVel.y toward the fall speed */
    s32 mBounceVy;          /* 0x44 -- mVel.y as the bounce left it */
    u8 pad_48[0x2];         /* 0x48 */
    s16 mRotY;              /* 0x4a */
    u8 pad_4c[0x2];         /* 0x4c */
    s16 mScreenPos[2];      /* 0x4e -- Camera_ProjectToScreen16 output */
    s16 mHeightRow;         /* 0x52 -- row of the height table sTrmpRowHeights */
    s32 mParticleId;        /* 0x54 -- Particle::System unique ID */
    s32 mAnim;              /* 0x58 -- anim number; also the bank-1 voice */
    u8 pad_5c[0x4];         /* 0x5c */
    s16 mTimer;             /* 0x60 -- state countdown */
    u8 pad_62[0x2];         /* 0x62 */
    s32 mState[2];          /* 0x64 -- the current state's member-pointer record */
    dExtAnmModel_c mModelAnim; /* 0x6c -- 0x64 bytes: UpdateMatrix sets its mat4x3, the
                             * states drive its dExtFrameCtrl_c base and read its file */
};

#ifndef SM64DS_PLATFORM_PC
typedef char dMgTrmpln3DMario_c_size_must_be_0xd0[sizeof(dMgTrmpln3DMario_c) == 0xd0 ? 1 : -1];
#endif

#endif
