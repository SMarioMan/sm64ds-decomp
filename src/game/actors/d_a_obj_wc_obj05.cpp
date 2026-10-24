//cpp
/* Cage Lift (CAGE_LIFT 99) -- ov029/daObjWc_Obj05_c.
 *
 * ov029 is WDW. RTTI ov029:0x02113e30 names daObjWc_Obj05_c; overlay_actors
 * maps profile 99 to CAGE_LIFT. Not daObjWc_Obj02_c (ARROW_LIFT), not
 * daObjWc_Obj03_c (WATER_DIAMOND), not daObjWc_Obj04_c
 * (SWITCH_ACTIVATED_PLANK), and not daObjWc_Mizu_c (WDW_WATER).
 *
 * common.h FIRST: dBgActor_c.h / dExtSimpleModel_c.h otherwise win with math/Matrix.h's
 * nested Matrix4x3, and InitResources' SetFile matrix argument scalarizes.
 *
 * FUNCTION ORDER IS THE REVERSE OF THE ROM'S. Highest-address first.
 * The destructor is inline in include/daObjWc_Obj05_c.h (D1 then D0, no D2).
 *
 * deslop leftovers:
 * - dBgW_KcMbg::SetFile 6az: InitResources passes Fix12<int> by value; the
 *   header method form size-DIFFs.
 * - dBgActor_c::IsClsnInRange 6az: Behavior; header method form refused
 *   (include/dBgActor_c.h).
 * - func_020393d4 / func_020393c4 / func_020393a4: InitResources stores
 *   dBgW::UpdatePosWithTransform and &func_ov029_02111e60 on mMeshCollider;
 *   Behavior clips at 0x250000; dBgW.h has no setter.
 * - Sound::PlayLong: Behavior recycles mSoundHandle at mCamSpacePosX.
 *   Including Sound.h renumbers this TU's pinned @NNN temps, so the
 *   declaration stays local.
 * - gWcObj05ModelFile / 02114284 are this TU's BMD/KCL file handles;
 *   data_ov029_0211306c the CLPS block stays unowned overlay data.
 * - func_ov029_02111e40 / 02111e60 stay placeholder labels (BeforeClsn
 *   veneer + player-id trigger). decl_common.h's `void(void)` view of
 *   02111e60 forces the namespaced definition.
 * - S14: g_profile_WC_OBJ05 stays outside the licensed .text.
 * - common.h first (InitResources SetFile matrix argument).
 */

/* Runtime asset handles resolved through the overlay 0 file table. */
enum d_a_obj_wc_obj05_AssetId {
    ASSET_WC_OBJ05_BMD = 0x06d3,
    ASSET_WC_OBJ05_KCL = 0x06d4
};

#include "common.h"
#include "daObjWc_Obj05_c.h"
#include "decl_common.h"
#include "SharedFilePtr.h"

/* Retail constructs these 8-byte handles in this order and registers
 * their destructors. The wrapper names are local; the ctor/dtor
 * addresses are the ROM resource-family functions. */
struct WcObj05ModelFilePtr : SharedFilePtr {
    WcObj05ModelFilePtr(u32 fileID);
    ~WcObj05ModelFilePtr();
};

struct WcObj05CollisionFilePtr : SharedFilePtr {
    WcObj05CollisionFilePtr(u32 fileID);
    ~WcObj05CollisionFilePtr();
};

namespace Sound {
/* local extern: including Sound.h renumbers @NNN. */
int PlayLong(u32, u32, u32, const Vector3 &, s16);
}

extern "C" {
void _ZN10dBgW_KcMbg7SetFileEP8KCL_FileRK9Matrix4x35Fix12IiEsR10CLPS_Block(
    dBgW_KcMbg *self, KCL_File *file, Matrix4x3 *mat, int scale, short angY, CLPS_Block &clps);
void func_020393d4(void *p, void *v);
void func_020393c4(void *p, void *v);
void func_020393a4(int *p, int v);
void d_a_obj_wc_obj05PlayLongHold(unsigned a, unsigned b, unsigned c, void *pos, unsigned e);
extern WcObj05ModelFilePtr gWcObj05ModelFile;
extern WcObj05CollisionFilePtr gWcObj05CollisionFile;
extern CLPS_Block data_ov029_0211306c;
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// @symbol daObjWc_Obj05_c_classInit
/* Reconstructed source-style name; exact original SM64DS spelling is not
 * preserved. Historical alias: CageLift_Spawn. Attribution stays on
 * daObjWc_Obj05_c_classInit. */
extern "C" daObjWc_Obj05_c *daObjWc_Obj05_c_classInit()
{
    return new daObjWc_Obj05_c();
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// Arg-shifting tail-call veneer. Drops the first argument and forwards the next two;
// #pragma long_calls emits the pooled `ldr ip,[pc,#8]; bx ip` absolute tail-call
// (bracketed with `off` so it cannot leak into later members). decl_common.h
// declares this name as `void(void)` for the callback-pointer view; the definition
// and the callee's int view live in namespaces, all binding the same C symbols.
namespace tail_e40 { extern "C" int func_ov029_02111e40(void *b, void *c); }
#pragma long_calls on
namespace fndef_e60 {
// @symbol func_ov029_02111e60
extern "C" int func_ov029_02111e60(void *a, void *b, void *c)
{
    return tail_e40::func_ov029_02111e40(b, c);
}
}
#pragma long_calls off

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
/* BeforeClsn helper: if the other actor's actorID is PLAYER (0xbf), arm
 * mPlayerOnTop. The unsigned char temporary is load-bearing. */
// @symbol func_ov029_02111e40
extern "C" void func_ov029_02111e40(char *a, char *b)
{
    unsigned char ok = ((dActor_c *)b)->actorID == 0xbf;
    if (ok)
        ((daObjWc_Obj05_c *)a)->mPlayerOnTop = 1;
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// @symbol _ZN15daObjWc_Obj05_c13InitResourcesEv
s32 daObjWc_Obj05_c::InitResources()
{
    BMD_File *f = (BMD_File *)dExtSimpleModel_c::LoadFile(gWcObj05ModelFile);
    mModel.SetFile(f, 1, -1);
    UpdateModelPosAndRotY();
    UpdateClsnPosAndRot();
    KCL_File *mc = (KCL_File *)dBgW_Kc::LoadFile(gWcObj05CollisionFile);
    _ZN10dBgW_KcMbg7SetFileEP8KCL_FileRK9Matrix4x35Fix12IiEsR10CLPS_Block(
        &mMeshCollider, mc, &mClsnMat, 0x1000, mAngleY, data_ov029_0211306c);
    func_020393d4(&mMeshCollider, (void *)&dBgW::UpdatePosWithTransform);
    func_020393c4(&mMeshCollider, (void *)&func_ov029_02111e60);
    mPrevPlayerOnTop = 0;
    mPlayerOnTop = mPrevPlayerOnTop;
    mDwellTimer = 0;
    if (param1 & 1)
        mState = 3;
    else
        mState = 0;
    mRestPosY = mPosY;
    return 1;
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// @symbol _ZN15daObjWc_Obj05_c8BehaviorEv
s32 daObjWc_Obj05_c::Behavior()
{
    func_020393a4((int *)&mMeshCollider, 0x250000);

    switch (mState) {
    case 0:
        if (mPlayerOnTop != 0) {
            if (mPrevPlayerOnTop == 0) {
                u8 *p = &mState;
                *p = *p + 1;
            }
        }
        mPrevPlayerOnTop = mPlayerOnTop;
        break;
    case 1: {
        s32 *p60 = &mPosY;
        *p60 = *p60 - 0x14000;
        mSoundHandle =
            Sound::PlayLong((unsigned)mSoundHandle, 3, 0x8d, *(Vector3 *)&mCamSpacePosX, 0);
        {
            int v = mRestPosY + (int)0xff5d8000;
            if (mPosY <= v) {
                mPosY = v;
                {
                    u8 *p = &mState;
                    *p = *p + 1;
                }
                mDwellTimer = 0;
            }
        }
        break;
    }
    case 2: {
        if ((u16)mDwellTimer >= 0x6e) {
            int snd =
                Sound::PlayLong((unsigned)mSoundHandle, 3, 0x8d, *(Vector3 *)&mCamSpacePosX, 0);
            mSoundHandle = snd;
            {
                s32 *p60 = &mPosY;
                *p60 = *p60 + 0xa000;
            }
            if (mPosY >= mRestPosY) {
                mPosY = mRestPosY;
                mState = 0;
                mDwellTimer = 0;
            }
        } else {
            u16 *p = (u16 *)&mDwellTimer;
            *p = *p + 1;
        }
        break;
    }
    case 3:
        break;
    }

    UpdateModelPosAndRotY();
    if (IsClsnInRange(0, 0)) {
        UpdateClsnPosAndRot();
    }
    mMeshCollider.Transform(mClsnMat, mAngleY);
    mPlayerOnTop = 0;
    return 1;
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// @symbol _ZN15daObjWc_Obj05_c6RenderEv
s32 daObjWc_Obj05_c::Render()
{
    mModel.Render(0);
    return 1;
}

/* -------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------- */
// @symbol _ZN15daObjWc_Obj05_c16CleanupResourcesEv
s32 daObjWc_Obj05_c::CleanupResources()
{
    if (mMeshCollider.IsEnabled()) {
        mMeshCollider.Disable();
    }
    gWcObj05ModelFile.Release();
    gWcObj05CollisionFile.Release();
    return 1;
}
// @symbol _ZN15daObjWc_Obj05_cD1Ev
// @symbol _ZN15daObjWc_Obj05_cD0Ev
/* daObjWc_Obj05_c's inline class-body destructor is instantiated by the
 * definitions above. mwccarm emits D1 and D0 into this object. */

/* The static-init globals -- mwcc emits __sinit_d_a_obj_wc_obj05.cpp
   from these: one ctor veneer plus destructor registration per handle. */
WcObj05ModelFilePtr gWcObj05ModelFile(ASSET_WC_OBJ05_BMD);
WcObj05CollisionFilePtr gWcObj05CollisionFile(ASSET_WC_OBJ05_KCL);
