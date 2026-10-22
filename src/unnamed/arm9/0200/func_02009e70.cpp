//cpp
// func_02009e70 @ 0x02009e70 (arm9): per-frame camera follow update.
// Register-shaped locals keep their ROM register names.  The compiler ranks a
// reused local's later live ranges by the order the local was first assigned,
// so the near limit reuses the mode-flags local and the far limit reuses the
// rate/near-distance local; that reuse is what places them in fp and sl.
#include "dBgCh_Gnd.h"
#include "dBgCh_Lin.h"
#include "PlayerInput.h"
#include "nitro/fx/fx.h"

extern "C" {
struct CamMode {
    s32 nearDist;   /* 0x00 */
    s32 farDist;    /* 0x04 */
    s32 f08;
    s32 f0c;
    s32 f10;
    s32 f14;
    s32 f18;
    s32 f1c;        /* 0x1c */
    s32 f20;        /* 0x20 */
    u16 f24;
    u16 flags;      /* 0x26 */
};

extern s16 Vec3_HorzAngle(const struct Vector3 *a, const struct Vector3 *b);
extern s16 Vec3_VertAngle(const struct Vector3 *a, const struct Vector3 *b);
extern void Vec3_Sub(struct Vector3 *out, const struct Vector3 *a, const struct Vector3 *b);
extern void Vec3_Add(struct Vector3 *out, const struct Vector3 *a, const struct Vector3 *b);
extern s32 Vec3_HorzLen(const struct Vector3 *v);
extern s32 LenVec3(const struct Vector3 *v);
extern void SubVec3(struct Vector3 *a, struct Vector3 *b, struct Vector3 *c);
extern void Vec3_MulScalarInPlace(s32 *v, s32 s);
extern s32 *Vec3_AsrInPlace(s32 *v, s32 sh);
extern void Vec3_RotateYAndTranslate(s32 *out, s32 *in, s16 angle, s32 *src);
extern s32 Math_Function_0203b14c(s32 *p, s32 tgt, s32 rate, s32 lim, s32 step);
extern s32 ApproachAngle(s16 *cur, s32 target, s32 div, s32 band, s32 step);
extern s32 AngleDiff(s32 a, s32 b);
extern s16 _ZN4cstd5atan2E5Fix12IiES1_(s32 y, s32 x);
extern s32 _ZN4cstd4fdivEii(s32 a, s32 b);
extern s32 _ZN4cstd4sqrtEy(u64 v);
extern u32 func_020093f4(void *p, s32 x);
extern u32 func_020093d4(void *p, s32 x);
extern s32 func_02009374(void *self);
extern s32 func_02008cb4(void *self);
extern void func_0200897c(void *self, void *arg);
extern s32 func_0200c66c(void *self, struct Vector3 *pos, void *out2, void *out1, void *out3);
extern s32 func_0200bec4(void *self, struct Vector3 *v, s32 a2, struct CamMode *mode, s32 a4);
extern void func_0200bb28(void *self, void *a);
extern void func_0200b798(void *self, void *a, s32 b);
extern void func_0200b590(void *self, void *a, s32 b);
extern void func_0200b0fc(void *self, void *a, s32 b);
extern void func_0200b990(void *self, void *a, s32 b);
extern void func_0200c9e0(void *self, s32 *a, s32 *b);
extern u32 func_02012790(u32 a);
extern s32 Sound_PlayIfNotActive(s32 a, s32 b, s32 c, s32 d);

static inline void SetVec(struct Vector3 &v, s32 x, s32 y, s32 z) { v.x = x; v.y = y; v.z = z; }
extern s16 data_02082214[];
extern u16 data_0209f49c[];
extern u16 data_0209f49e[];
extern u8 data_0209f2d8;
extern signed char data_0209f2f8;
extern s32 data_0209f32c;
extern s32 data_0209b000;

extern struct CamMode data_02086fcc;
extern struct CamMode data_02086ff4;
extern struct CamMode data_0208706c;
extern struct CamMode data_02087094;
extern struct CamMode data_020870e4;
extern struct CamMode data_0208710c;
extern struct CamMode data_020871ac;
extern struct CamMode data_020871d4;
extern struct CamMode data_0208724c;
extern struct CamMode data_0208733c;
extern struct CamMode data_020873dc;
extern struct CamMode data_02087404;
extern struct CamMode data_0208742c;
extern struct CamMode data_0208747c;
extern struct CamMode data_020874cc;

/* File-local views of the two objects this function reads (dActor_c.h and
   dCamera_c.h are not included here); field names follow those headers. */
struct ActorView {
    u8 pad_000[0x5c];
    Vector3 mPos; /* 0x05c */
    u8 pad_068[0x26];
    s16 mAngleY; /* 0x08e */
    u8 pad_090[0x4];
    s16 mPrevAngleY; /* 0x094 */
};

struct CameraView {
    u8 pad_000[0x80];
    Vector3 lookAt;     /* 0x080 */
    Vector3 pos;        /* 0x08c */
    Vector3 mTargetPos; /* 0x098 */
    u8 pad_0a4[0x3c];
    Vector3 mWallPos;    /* 0x0e0 */
    Vector3 mWallNormal; /* 0x0ec */
    u8 pad_0f8[0x18];
    ActorView *mTargetPlayer; /* 0x110 */
    ActorView *mFramedActor;  /* 0x114 */
    ActorView *mFocusActor;   /* 0x118 */
    u8 pad_11c[0x4];
    Vector3 mLookTargetPos; /* 0x120 */
    s32 mFocusDist;         /* 0x12c */
    s32 mFocusBlend;        /* 0x130 */
    u8 pad_134[0x8];
    struct CamMode *mMode; /* 0x13c */
    u8 pad_140[0x14];
    u32 mFlags;     /* 0x154 */
    s32 mTurnSound; /* 0x158 */
    u8 pad_15c[0x20];
    s16 mAngleY; /* 0x17c */
    s16 mAngleX; /* 0x17e */
    u8 pad_180[0x4];
    s16 mBaseAngleOffset; /* 0x184 */
    s16 mTargetAngleY;    /* 0x186 */
    s16 mInputYawLag;     /* 0x188 -- dCamera_c::mInputYawLag */
    u8 pad_18a[0x14];
    s16 mBehindAngleY; /* 0x19e */
    u16 mRecentering;  /* 0x1a0 */
    u8 pad_1a2[0x4];
    u8 mTurningToTarget; /* 0x1a6 */
};

/* GetViewObj's 0xe-byte record, as d_camera.cpp's CamViewObj reads it.
   func_0200c66c hands back the view object for the camera area. For type 2,
   byte 1 zero places pos at (x, y, z) at once; otherwise the camera turns
   toward the object's yaw. */
struct CamViewObj {
    u8 type;     /* 0x0 */
    u8 p1;       /* 0x1 */
    s16 x, y, z; /* 0x2 */
    u8 pad_8[2];
    s16 angleY; /* 0xa */
};

static inline int CheckMode(void) { return data_0209f2d8 == 1; }

static inline s32 CollisionCeiling(dBgCh_Lin &line, s32 floorHeight)
{
    Vector3 pos = line.GetClsnPos();
    s32 height = pos.y - 0x80000;
    if (height < floorHeight) height = floorHeight;
    return height;
}

static inline void SetCollisionPosition(CameraView *cam, dBgCh_Lin &line) {
    Vector3 pos = line.GetClsnPos();
    cam->mWallPos.x = pos.x;
    cam->mWallPos.y = pos.y;
    cam->mWallPos.z = pos.z;
}

static inline void MoveCameraPosition(CameraView *cam, const Vector3 &offset) {
    Vector3 pos;
    Vec3_Add(&pos, &cam->lookAt, &offset);
    cam->pos.x = pos.x;
    cam->pos.y = pos.y;
    cam->pos.z = pos.z;
}

static inline s32 LimitCameraCeiling(dBgCh_Lin &line, Vector3 &endpoint, s32 ceiling)
{
    Vector3 pos = line.GetClsnPos();
    endpoint.y = pos.y;
    if (ceiling > pos.y - 0x80000) ceiling = pos.y - 0x80000;
    return ceiling;
}

static inline s32 LimitMidpointCeiling(dBgCh_Lin &line, Vector3 &endpoint, s32 ceiling)
{
    Vector3 pos = line.GetClsnPos();
    endpoint.y = pos.y - 0x80000;
    if (ceiling > endpoint.y) ceiling = endpoint.y;
    return ceiling;
}

s32 func_02009e70(char *self)
{
    CameraView *cam = (CameraView *)self;
    s32 sp04;
    s32 sp08;
    s32 sp0c;
    s32 sp10;
    s32 sp14;
    u16 sp18;
    struct CamMode *sp1c;
    CamViewObj *sp20;
    s32 sp24;
    s32 sp28;
    s32 sp2c;
    s32 sp30;
    struct Vector3 sp34;
    struct Vector3 sp40;
    s32 r7;
    s32 r6;
    s32 sb;
    s32 r4;
    s16 sba;
    s32 r5;
    s32 fp;
    u32 r7h;
    struct CamMode *m;
    s32 t0;
    s32 kf;
    s16 diff;
    s32 ceil;

    if (cam->mTargetPlayer == 0) {
        cam->mAngleY = Vec3_HorzAngle(&cam->lookAt, &cam->pos);
    } else {
        sp1c = (cam->mFlags & 0x100) ? &data_0208747c : cam->mMode;
        Vec3_Sub(&sp34, &cam->mTargetPlayer->mPos, &cam->mTargetPos);
        {
            struct Vector3 *q = &cam->mTargetPlayer->mPos;
            cam->mTargetPos.x = q->x;
            cam->mTargetPos.y = q->y;
            cam->mTargetPos.z = q->z;
        }
        r7 = Vec3_HorzLen(&sp34);
        sp20 = 0;
        sp24 = 0;
        if (cam->mFocusActor != 0) {
            struct Vector3 *q;
            sp24 = 1;
            cam->mFramedActor = 0;
            q = &cam->mFocusActor->mPos;
            cam->mLookTargetPos.x = q->x;
            cam->mLookTargetPos.y = q->y;
            cam->mLookTargetPos.z = q->z;
            cam->mFocusDist = 0xdfe60;
        }
        r6 = func_0200c66c(self, &cam->mTargetPos, &sp20, &sp1c, &sp24);
        r4 = 0;
        if (sp24 != 0) {
            r4 = 0x1000;
            SubVec3(&cam->mLookTargetPos, &cam->mTargetPos, &cam->mLookTargetPos);
        }
        Math_Function_0203b14c(&cam->mFocusBlend, r4, 0x100, 0x80, 0x10);

        fp = sp1c->flags;
        r4 = sp1c->f1c;
        r5 = sp1c->f20;
        if ((fp & 1) == 0 && (cam->mFlags & 2) != 0) {
            r4 = FX_MUL(r4, 0x1800);
            r5 = FX_MUL(r5, 0x1800);
        }
        if (CheckMode() && (fp & 2) != 0 && func_02009374(self) != 0) {
            r4 = FX_MUL(r4, 0x14cc);
            r5 = FX_MUL(r5, 0x14cc);
        }
        if (cam->mFlags & 0x80) {
            r4 = FX_MUL(r4, 0x1800);
            r5 = FX_MUL(r5, 0x1800);
        }
        /* near limit -> fp (reuses the flags local), far limit -> r4 (reuses the
           near-distance local): both must be later live ranges of already-assigned
           locals for the allocator to colour them fp/sl. */
        t0 = cam->mFocusDist - r4;
        fp = func_020093f4(self, r4 + FX_MUL(t0, cam->mFocusBlend));
        if (sp24 != 0) {
            r4 = fp;
        } else {
            if (r5 < 0)
                r5 = -r5;
            r4 = func_020093f4(self, r5);
        }
        sp04 = func_0200bec4(self, &cam->mTargetPos, r6, sp1c, r7);
        kf = *(u16 *)((char *)data_0209f49e + gActivePlayerSlot * 0x18) & 0x4300;
        if (cam->mFocusActor != 0) {
            cam->mAngleY = Vec3_HorzAngle(&cam->lookAt, &cam->pos);
        } else if (sp1c == &data_0208733c) {
            func_0200bb28(self, sp20);
            kf = 0;
        } else if (sp1c == &data_020873dc) {
            func_0200b798(self, sp20, r6);
        } else if ((cam->mFlags & 0x400) == 0) {
            if (sp1c == &data_02087404) {
                func_0200b590(self, sp20, r6);
            } else if (sp1c == &data_0208742c) {
                func_0200b0fc(self, sp20, r6);
            } else {
                cam->mFlags |= 0x1000;
                sp08 = func_020093f4(self, sp1c->nearDist);
                sp0c = func_020093f4(self, sp1c->farDist);
                if (sp20 != 0 && sp20->type == 2) {
                    if (sp20->p1 == 0) {
                        s32 tx = sp20->x << 12;
                        s32 tz = sp20->z << 12;
                        s32 ty = sp20->y << 12;
                        cam->pos.x = tx;
                        cam->pos.y = ty;
                        cam->pos.z = tz;
                    } else {
                        s16 a = (s16)(sp20->angleY + 0x8000);
                        if (cam->mTargetAngleY != a) {
                            cam->mTargetAngleY = a;
                            cam->mTurningToTarget = 1;
                        }
                    }
                } else {
                    if (cam->mTurningToTarget == 0) {
                        cam->mTargetAngleY += 0x8000;
                    }
                }
                Vec3_Sub(&sp40, &cam->pos, &cam->lookAt);
                sp28 = LenVec3(&sp40);
                {
                    sp10 = 0x80000000;
                    Vector3 sp4c(cam->mTargetPos.x, cam->mTargetPos.y + 0x3e8000,
                                 cam->mTargetPos.z);
                    Vector3 sp58;
                    Vector3 sp64;
                    ceil = 0x7fffffff;
                    sb = cam->mTargetPos.y + 0x82500;
                    {
                        dBgCh_Lin line;
                        func_0200897c(self, &line);
                        line.SetObjAndLine(cam->mTargetPos, sp4c, 0);
                        if (line.DetectClsn() != 0) {
                            ceil = CollisionCeiling(line, sb);
                        }
                        if ((cam->mFlags & 0x100) == 0 && (sp1c->flags & 8) != 0) {
                            {
                                s32 tz = cam->mTargetPos.z;
                                s32 tx = cam->mTargetPos.x;
                                sp58.x = tx;
                                sp58.y = sb;
                                sp58.z = tz;
                            }
                            if (sb <= ceil) {
                                line.SetObjAndLine(sp58, cam->pos, 0);
                                if (line.DetectClsn() != 0) {
                                    line.surface.CopyNormalTo(sp64);
                                    SetCollisionPosition(cam, line);
                                    cam->mWallNormal.x = sp64.x;
                                    cam->mWallNormal.y = sp64.y;
                                    cam->mWallNormal.z = sp64.z;
                                    t0 = sp64.y;
                                    if (t0 < 0)
                                        t0 = -t0;
                                    if (t0 > 0xb50) {
                                        cam->mFlags |= 0x80200;
                                    } else {
                                        Vector3 sp70 = line.GetClsnPos();
                                        sba = _ZN4cstd5atan2E5Fix12IiES1_(sp64.x, sp64.z) + 0x8000;
                                        diff = sba - cam->mAngleY;
                                        sba += (diff < 0) ? 0x4000 : -0x4000;
                                        if (cam->mTurningToTarget != 0) {
                                            if (AngleDiff(sba, cam->mTargetAngleY) >= 0x4000)
                                                sba = cam->mTargetAngleY;
                                        }
                                        cam->mTargetAngleY = sba;
                                        cam->mTurningToTarget = 1;
                                        t0 = (s16)(cam->mAngleY - cam->mTargetAngleY);
                                        if (kf & 0x200)
                                            t0 = (s16)(-t0);
                                        if (t0 > 0)
                                            kf = 0;
                                        cam->mFlags |= 0x40000;
                                    }
                                }
                            }
                        }
                        Vector3 sp7c;
                        Vector3 sp88;
                        if (kf != 0) {
                            if (kf & 0x4000)
                                func_02012790(0x1a);
                            cam->mTurningToTarget = 0;
                        } else {
                            if (cam->mTurningToTarget == 0) {
                                kf = *(u16 *)((char *)data_0209f49c + gActivePlayerSlot * 0x18) &
                                     0x4300;
                            }
                        }
                        if (cam->mFlags & 0x100) {
                            if (sp28 > (s32)func_020093f4(self, 0xdfe60))
                                cam->mFlags &= ~0x100;
                        }
                        /* sb = sp28 is assigned inside the test: hoisting it above the if
                           re-lays the function (290 words differ). */
                        if (kf != 0 || cam->mRecentering != 0 || cam->mTurningToTarget != 0 ||
                            r7 <= sp08 || (sb = sp28) < fp || sb <= sp0c) {
                            sb = cam->mAngleY;
                            cam->mAngleY = Vec3_HorzAngle(&cam->lookAt, &cam->pos);
                            if (kf != 0 || cam->mRecentering != 0) {
                                if ((kf & 0x4000) || cam->mRecentering != 0) {
                                    if (kf != 0) {
                                        cam->mBehindAngleY = cam->mTargetPlayer->mAngleY + 0x8000;
                                    }
                                    cam->mRecentering =
                                        ApproachAngle(&cam->mAngleY, cam->mBehindAngleY, 4, 0x800,
                                                      0x400) != 0;
                                    if (cam->mRecentering != 0)
                                        cam->mFlags |= 0x60;
                                } else {
                                    if (kf & 0x200) {
                                        cam->mAngleY -= 0x400;
                                        cam->mFlags |= 0x20;
                                    } else {
                                        cam->mAngleY += 0x400;
                                        cam->mFlags |= 0x40;
                                    }
                                }
                                kf = 0;
                            } else if (cam->mTurningToTarget != 0) {
                                if (ApproachAngle(&cam->mAngleY, cam->mTargetAngleY, 0x10, 0x200,
                                                  0x100) == 0)
                                    cam->mTurningToTarget = 0;
                            } else {
                                m = sp1c;
                                if (m == &data_020871ac || m == &data_020871d4) {
                                    func_0200b990(self, sp20, r7);
                                } else if (sp24 == 0) {
                                    if (m == &data_0208724c)
                                        t0 = cam->mTargetPlayer->mPrevAngleY;
                                    else
                                        t0 = cam->mTargetPlayer->mAngleY;
                                    t0 = (s16)(t0 + 0x8000);
                                    if (m == &data_020874cc) {
                                        cam->mAngleY = t0 + cam->mBaseAngleOffset;
                                    } else if (sp28 <= sp0c) {
                                        ApproachAngle(&cam->mAngleY, t0, 0x14, 0x600, 0x28);
                                    } else if (m->flags & 0x100) {
                                        cam->mAngleY = sb;
                                    } else if (r7 <= sp08) {
                                        ApproachAngle(&cam->mAngleY, t0, 0x14, 0x64, 0x28);
                                    }
                                }
                            }

                            sp14 = sp28;
                            if (sp28 > r4) {
                                if (r7 != 0 && sp1c == &data_02086fcc) {
                                    sb = _ZN4cstd5atan2E5Fix12IiES1_(sp34.y, Vec3_HorzLen(&sp34));
                                    if (sb < -0x3f80)
                                        sb = -0x3f80;
                                    else if (sb > 0x3f80)
                                        sb = 0x3f80;
                                    fp = Vec3_HorzLen(&sp40);
                                    sp18 = _ZN4cstd5atan2E5Fix12IiES1_(-sp40.y, fp);
                                    ApproachAngle((s16 *)&sp18, sb, 0x20, 0x800, 0);
                                    t0 = (sp18 >> 4) * 2;
                                    sp40.y = FX_MUL(sp28, -data_02082214[t0]);
                                    t0 = _ZN4cstd4fdivEii(FX_MUL(sp28, data_02082214[t0 + 1]), fp);
                                    sp40.x = FX_MUL(sp40.x, t0);
                                    sp40.z = FX_MUL(sp40.z, t0);
                                }
                                Math_Function_0203b14c(&sp28, r4, 0x400, r7 + 0x20000, 0x100);
                                Vec3_MulScalarInPlace((s32 *)&sp40, _ZN4cstd4fdivEii(sp28, sp14));
                            } else if (sp28 < fp) {
                                Math_Function_0203b14c(&sp28, fp, 0x400, r7 + 0x20000, 0x100);
                                {
                                    s64 distanceSq = sp28;
                                    distanceSq *= sp28;
                                    distanceSq -= (s64)sp40.y * sp40.y;
                                    r7 = _ZN4cstd4sqrtEy((u64)distanceSq);
                                }
                                t0 = _ZN4cstd4fdivEii(r7, Vec3_HorzLen(&sp40));
                                sp40.x = FX_MUL(sp40.x, t0);
                                sp40.z = FX_MUL(sp40.z, t0);
                                cam->mInputYawLag -= cam->mAngleY - sb;
                            }
                            t0 = Vec3_HorzLen(&sp40);
                            if (t0 < 0x1000)
                                t0 = 0x1000;
                            sp40.z = t0;
                            sp40.x = 0;
                            Vec3_RotateYAndTranslate(&cam->pos.x, &cam->lookAt.x, cam->mAngleY,
                                                     (s32 *)&sp40);
                        } else {
                            if (sb > r4) {
                                Math_Function_0203b14c(&sp28, r4, 0x400, r7 + 0x20000, 0x100);
                                Vec3_MulScalarInPlace((s32 *)&sp40, _ZN4cstd4fdivEii(sp28, sb));
                                MoveCameraPosition(cam, sp40);
                            }
                        }
                        if (func_02008cb4(self) != 0) {
                            if (cam->mFlags & 0x60) {
                                kf = 1;
                                cam->mFlags &= ~0x60;
                            }
                        }
                        SetVec(sp4c, cam->pos.x, cam->pos.y + 0x100000, cam->pos.z);
                        line.SetObjAndLine(cam->pos, sp4c, 0);
                        if (line.DetectClsn() != 0) {
                            ceil = LimitCameraCeiling(line, sp4c, ceil);
                        }
                        Vec3_Add(&sp7c, &cam->pos, &cam->lookAt);
                        Vec3_AsrInPlace((s32 *)&sp7c, 1);
                        sp88.x = sp7c.x;
                        sp88.y = sp7c.y + 0x100000;
                        sp88.z = sp7c.z;
                        line.SetObjAndLine(sp7c, sp88, 0);
                        if (line.DetectClsn() != 0) {
                            ceil = LimitMidpointCeiling(line, sp88, ceil);
                        }
                        s32 y = cam->mTargetPos.y;
                        dBgCh_Gnd ground;
                        ground.mProbeHeight = 0x5dc000;
                        func_0200897c(self, &ground);
                        ground.SetObjAndPos(sp4c, 0);
                        if (sp1c > &data_02086fcc)
                            ground.StartDetectingWater();
                        sb = (ground.DetectClsn() != 0) ? ground.clsnY : y;
                        if (sp1c == &data_02086ff4) {
                            if (sb < data_0209f32c)
                                sb = data_0209f32c;
                            r7h = sb + 0x64000;
                        } else {
                            r7h = sb;
                            if (sb < r6)
                                r7h = r6;
                            r7h = r7h +
                                  func_020093d4(self, (r6 - sp04) + ((cam->mFlags & 2) ? 0x1e8000
                                                                                       : 0x138000));
                            if (sp1c->flags & 0x80) {
                                if (cam->pos.y > (s32)r7h)
                                    r7h = cam->pos.y;
                            }
                            sp2c = sp1c->f08;
                            sp30 = sp1c->f0c;
                            func_0200c9e0(self, &sp2c, &sp30);
                            sp40.y = r7h - cam->lookAt.y;
                            if (sp1c == &data_0208706c && sp34.y < 0)
                                t0 = 0xa49;
                            else
                                t0 = sp2c;
                            r6 = FX_MUL(sp28, t0);
                            t0 = FX_MUL(sp28, sp30);
                            if (sp40.y < r6)
                                r7h = cam->lookAt.y + r6;
                            else if (sp40.y > t0)
                                r7h = cam->lookAt.y + t0;
                            if (data_0209f2f8 == 0x26) {
                                if (cam->pos.y < sb + 0x25bc8)
                                    cam->pos.y = sb + 0x25bc8;
                            }
                            if (ceil < sb + 0x25bc8)
                                ceil = sp4c.y;
                            if (sb + 0x25bc8 > (s32)0x80000000)
                                sp10 = sb + 0x25bc8;
                        }
                        if (sp1c != &data_02087094 && sp1c != &data_020870e4 &&
                            sp1c != &data_0208710c) {
                            if ((s32)r7h < sp10)
                                r7h = sp10;
                            else if ((s32)r7h > ceil)
                                r7h = ceil;
                        }
                        Math_Function_0203b14c(&cam->pos.y, r7h, 0x300, 0x14000, 0x100);
                        cam->mAngleY = Vec3_HorzAngle(&cam->lookAt, &cam->pos);
                    }
                }
            }
        }
        if (kf != 0) {
            if (data_0209b000 == 0)
                func_02012790(0xe);
            data_0209b000 = kf;
        } else {
            data_0209b000 = 0;
            if (cam->mFlags & 0x60) {
                cam->mTurnSound = Sound_PlayIfNotActive(cam->mTurnSound, 2, 0x43, 0);
            }
        }
    }
    cam->mAngleX = Vec3_VertAngle(&cam->lookAt, &cam->pos);
    return 1;
}
}
