//cpp
// @symbol _ZN8Particle19SetSelfDestructFlagEj
// @symbol func_020226fc
// @symbol func_02022774
// @symbol func_020227ec
// @symbol func_02022864
// @symbol func_020228dc
// @symbol func_0202293c
// @symbol _ZN8Particle6System9NewRippleE5Fix12IiES2_S2_
// @symbol func_020229f0
// @symbol func_02022a4c
// @symbol _ZN8Particle6System12NewBigSplashE5Fix12IiES2_S2_
// @symbol func_02022b04
// @symbol _ZN8Particle20RunningSlidingDustAtE5Fix12IiES1_S1_
// @symbol _ZN8Particle6System17NewUnkCallback818Ejj5Fix12IiES2_S2_PK11Vector3_16f
// @symbol _ZN8Particle6System10NewWeatherEjj5Fix12IiES2_S2_PK11Vector3_16fj
// @symbol func_02022c3c
// @symbol func_02022c80
// @symbol func_02022cbc
// @symbol func_02022d00
// @symbol func_02022d44
// @symbol _ZN8Particle6System3NewEjjiiiPK11Vector3_16fPNS_8CallbackE
// @symbol _ZN8Particle6System12FromUniqueIDEj
// @symbol _ZN8Particle6System9NewSimpleEjiii
// @symbol _ZN8Particle9RenderAllEv
// @symbol _ZN8Particle10SysTracker6UpdateEv
// @symbol _ZN8Particle10SysTracker10InitialiseEv
// @symbol _ZN8Particle7Texture12AllocPalVramEjb
// @symbol _ZN8Particle7Texture12AllocTexVramEjb
// @symbol func_02023178
// @symbol _ZN8Particle10SysTrackerD1Ev
// @symbol _ZN8Particle10SysTrackerC1Ev
/* engine/particle/Particle.cpp -- Particle TU (arm9 0x020226d4..0x020233d4)
 *
 * The singleton particle engine's core translation unit: SysTracker lifecycle
 * (construct, Initialise, Update, destruct), the System::New front door and
 * its fixed-effect-id wrapper family, the Texture VRAM allocators, RenderAll,
 * and SetSelfDestructFlag. The SysTracker object itself is the single global
 * at data_0209ee74; every wrapper reaches it directly.
 *
 * mwccarm emits .text in reverse source order here, so the definitions below
 * run ROM-descending; the roster above reads ROM-ascending. */
#include "types.h"
#include "Heap.h"
#include "decl_common.h"
#include "dExtSimpleModel_c.h"
#include "Particle__SysTracker.h"
#include "Particle__Texture.h"
#include "Particle__Manager.h"
#include "Particle__System.h"

extern "C" {
void func_0203cbc0(void *p);
void func_02049ee8(void* manager, void* renderState);
void DecompressLZ16(const void* src, void* dst);
}

extern int data_0209b3ec;
extern u32 data_0209ee84;
extern u32 data_0209ee8c;
extern signed char data_0209f2f8;
extern void* data_020a0ea0;

struct Vec3 {
    s16 x, y, z;
};

namespace Particle {

// @symbol _ZN8Particle10SysTrackerC1Ev
SysTracker::SysTracker()
{
    data_0209ee74 = this;
    mManager = 0;
    mRunningSlidingDustSystemID = 0;
    mSystemID_75c = 0;
    mBigSplashSystemID = 0;
    mSystemID_774 = 0;
    mSystemID_780 = 0;
    mRippleSystemID = 0;
    mSystemID_798 = 0;
    mSystemID_7a4 = 0;
    mSystemID_7b0 = 0;
    mSystemID_7c0 = 0;
    mCallback_800.waterOffset = 0x4b000;
}

// @symbol _ZN8Particle10SysTrackerD1Ev
SysTracker::~SysTracker()
{
    if (data_0209ee80 != 0) {
        mContents.Clear();
        func_0203cbc0(data_0209ee80);
        data_0209ee80 = 0;
    }
    if (mResourceFile != (void *)data_02075f14) {
        _ZN6Memory10DeallocateEPv(mResourceFile);
    }
    data_0209ee74 = 0;
}

}

extern "C" {

// @symbol func_02023178
char* func_02023178(int n) {
    char* old = (char*)data_0209ee78;
    data_0209ee78 = old + n;
    return old;
}

}

namespace Particle {

// @symbol _ZN8Particle7Texture12AllocTexVramEjb
u32 Texture::AllocTexVram(u32 size, bool isTexel4x4)
{
    if (isTexel4x4) {
        u32 address = data_0209ee88;
        data_0209ee88 = address + size;
        return address;
    }

    return dExtSimpleModel_c::GetVramOffset(size);
}

// @symbol _ZN8Particle7Texture12AllocPalVramEjb
u32 Texture::AllocPalVram(u32 size, bool fromLowAddress)
{
    if (fromLowAddress) {
        u32 alignedSize = (size + 7) & ~7;
        u32 address = data_0209ee84;
        data_0209ee84 = address + alignedSize;
        return address;
    }

    u32 alignedSize = (size + 15) & ~15;
    u32 address = data_0209ee8c - alignedSize;
    data_0209ee8c = address;
    return address;
}

#define M(p) ((long long)(int)(p))

// @symbol _ZN8Particle10SysTracker10InitialiseEv
void SysTracker::Initialise()
{
    signed char v = data_0209f2f8;
    unsigned int allocSize = 0x8c00;
    int countA = 0x28;
    int countB = 0x100;

    if (v == 0x24 || v == 0x26 || v == 0x28) {
        countA = 0x40;
        countB = 0x140;
        allocSize = 0xa800;
    }

    {
        char* base = (char*)_ZN6Memory13operator_new2Ej(allocSize);
        char* end = base + allocSize;
        data_0209ee80 = base;
        data_0209ee78 = base;
        data_0209ee7c = end;
    }

    data_0209ee88 = func_02045d10();
    data_0209ee84 = func_02045cf0();
    data_0209ee8c = func_02045ce0();

    mManager = (Manager*)func_0204a4c8(
        func_02023178, countA, countB, 0x1a, 0x3e);
    /* Manager +0x30 sits in its unnamed pad_030; nothing else reaches it. */
    *(int*)((char*)mManager + 0x30) = 0x8000;

    if (func_0206e28c((u8*)data_02075f14, data_0208f668, 4) != 0) {
        mResourceFile = data_02075f14;
    } else {
        char* hdr = (char*)(int)M(data_02075f14);
        unsigned int size = (unsigned int)M(*(unsigned int*)(hdr + 4) >> 8);
        void* dst = _ZN6Memory8AllocateEj(size);
        DecompressLZ16(hdr + 4, dst);
        _ZN4CP1514FlushDataCacheEjj((unsigned int)dst, size);
        mResourceFile = dst;
    }

    func_0204a17c(mManager, mResourceFile);
    func_0204a0dc(mManager,
        (u32 (*)(const void *, u32))Texture::AllocTexVram);
    func_0204a028(mManager,
        (u32 (*)(u32, u32))Texture::AllocPalVram);

    if (mResourceFile != data_02075f14) {
        mHeap::Heap_t *heap = (mHeap::Heap_t *)(int)M(data_020a0ea0);
        /* +0x18 of the particle resource file header; no header models that file. */
        unsigned int oldSize = (unsigned int)M(*(unsigned int*)((char*)mResourceFile + 0x18));
        heap->_Sizeof(mResourceFile);
        heap->Reallocate(mResourceFile, oldSize);
    }
}

// @symbol _ZN8Particle10SysTracker6UpdateEv
void SysTracker::Update()
{
    mContents.Update();
    func_02049f58(mManager);
}

// @symbol _ZN8Particle9RenderAllEv
void RenderAll()
{
    Particle__SysTracker* tracker = data_0209ee74;
    if (!tracker)
        return;

    func_02049ee8(tracker->mManager, &data_0209b3ec);
}

}

namespace Particle {

// @symbol _ZN8Particle6System9NewSimpleEjiii
void *System::NewSimple(u32 uniqueID, Fix12i x, Fix12i y, Fix12i z) {
    Vector3 pos;
    s32 xv = x >> 3;
    s32 yv = y >> 3;
    s32 zv = z >> 3;
    pos.x = xv;
    pos.y = yv;
    pos.z = zv;
    Particle::Manager *mgr = data_0209ee74->mManager;
    return mgr->AddSystem(uniqueID, pos);
}

}

namespace Particle {

// @symbol _ZN8Particle6System12FromUniqueIDEj
System *System::FromUniqueID(u32 uniqueID)
{
    SysTracker::Contents::Entry *entry =
        data_0209ee74->mContents.FindData(uniqueID);
    return entry->system;
}

}

extern "C" {

struct ParamBlk
{
  char pad20[0x20];
  int f20;
  int f24;
  int f28;
  char pad2c[0x3c - 0x2c];
  short f3c;
  short f3e;
  short f40;
};
typedef void (*VFn)(void *, void *);
struct VObj
{
  VFn *vtable;
};
struct System
{
  int f0;
  char pad4[6];
  unsigned char fa;
  char padb[1];
  struct ParamBlk *fc;
  struct VObj *f10;
};
struct Args3
{
  int a;
  int b;
  int c;
};
}

namespace Particle {

// @symbol _ZN8Particle6System3NewEjjiiiPK11Vector3_16fPNS_8CallbackE
int System::New(u32 type, u32 u, int a, int b, int c, const Vector3_16f *pos, Callback *cb) {
    ::System *new_var;
    Particle::SysTracker::Contents *contents;
    ::System *sys;
    struct Args3 args;
    args.a = a >> 3;
    contents = &data_0209ee74->mContents;
    args.b = b >> 3;
    args.c = (c >> 1) >> 2;
    new_var = (::System *)contents->FindData(type);
    sys = new_var;
    if (sys) {
        struct VObj *o;
        struct ParamBlk *p;
        sys->fa = 1;
        p = sys->fc;
        p->f20 = args.a;
        p->f24 = args.b;
        p->f28 = args.c;
        if (pos != 0) {
            p->f3c = pos->x;
            p->f3e = pos->y;
            p->f40 = pos->z;
        }
        o = sys->f10;
        if (o != 0) {
            o->vtable[0](o, p);
        }
        return sys->f0;
    }
    return (int)contents->Create(u, *(Vector3 *)&args, (const Vector3_16f *)pos,
                                 (dPa_c::level_c::callback_c *)cb);
}

}

extern "C" {

// @symbol func_02022d44
u32 func_02022d44(u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, void *dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_7f0);
}

// @symbol func_02022d00
u32 func_02022d00(u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, void *dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_7f4);
}

// @symbol func_02022cbc
u32 func_02022cbc(int uniqueID, int effectID, s32 x, s32 y, s32 z, int dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_7f8);
}

// @symbol func_02022c80
u32 func_02022c80(
    u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, const void* dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_800);
}

// @symbol func_02022c3c
u32 func_02022c3c(
    u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, const void* dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_808);
}

// @symbol _ZN8Particle6System10NewWeatherEjj5Fix12IiES2_S2_PK11Vector3_16fj
u32 _ZN8Particle6System10NewWeatherEjj5Fix12IiES2_S2_PK11Vector3_16fj(
    u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, const void* dir, u8 numWeatherEffectsNow)
{
    dPa_c::level_c::clipCallback_c *callback = &data_0209ee74->mWeatherCallback;
    callback->enabled = numWeatherEffectsNow;
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)callback);
}

// @symbol _ZN8Particle6System17NewUnkCallback818Ejj5Fix12IiES2_S2_PK11Vector3_16f
u32 _ZN8Particle6System17NewUnkCallback818Ejj5Fix12IiES2_S2_PK11Vector3_16f(
    u32 uniqueID, u32 effectID, Fix12i x, Fix12i y, Fix12i z, const struct Vector3_16f* dir)
{
    return Particle::System::New(uniqueID, effectID, x, y, z, (const Vector3_16f *)dir,
                                 (Particle::Callback *)&data_0209ee74->mCallback_818);
}

// @symbol _ZN8Particle20RunningSlidingDustAtE5Fix12IiES1_S1_
void _ZN8Particle20RunningSlidingDustAtE5Fix12IiES1_S1_(Fix12i x, Fix12i y, Fix12i z)
{
    data_0209ee74->mRunningSlidingDustSystemID = Particle::System::New(
        data_0209ee74->mRunningSlidingDustSystemID, 0xda, x, y, z, (const Vector3_16f *)0,
        (Particle::Callback *)&data_0209ee74->mRunningSlidingDustCallback);
}

// @symbol func_02022b04
void func_02022b04(Fix12i x, Fix12i y, Fix12i z)
{
    data_0209ee74->mSystemID_75c =
        Particle::System::New(data_0209ee74->mSystemID_75c, 0x61, x, y, z, (const Vector3_16f *)0,
                              (Particle::Callback *)&data_0209ee74->mCallback_760);
}

// @symbol _ZN8Particle6System12NewBigSplashE5Fix12IiES2_S2_
void _ZN8Particle6System12NewBigSplashE5Fix12IiES2_S2_(Fix12i x, Fix12i y, Fix12i z)
{
    data_0209ee74->mBigSplashSystemID = Particle::System::New(
        data_0209ee74->mBigSplashSystemID, 0xdd, x, y, z, (const Vector3_16f *)0,
        (Particle::Callback *)&data_0209ee74->mBigSplashCallback);
}

// @symbol func_02022a4c
u32 func_02022a4c(Fix12i x, Fix12i y, Fix12i z)
{
    Particle::SysTracker *base = data_0209ee74;
    u32 result = Particle::System::New(base->mSystemID_774, 0xdf, x, y, z, (const Vector3_16f *)0,
                                       (Particle::Callback *)&base->mBigSplashCallback);
    data_0209ee74->mSystemID_774 = result;
    return result;
}

// @symbol func_020229f0
u32 func_020229f0(Fix12i x, Fix12i y, Fix12i z)
{
    Particle::SysTracker *base = data_0209ee74;
    u32 result = Particle::System::New(base->mSystemID_780, 0xc4, x, y, z, (const Vector3_16f *)0,
                                       (Particle::Callback *)&base->mCallback_784);
    data_0209ee74->mSystemID_780 = result;
    return result;
}

// @symbol _ZN8Particle6System9NewRippleE5Fix12IiES2_S2_
u32 _ZN8Particle6System9NewRippleE5Fix12IiES2_S2_(Fix12i x, Fix12i y, Fix12i z)
{
    Particle::SysTracker *tracker = data_0209ee74;
    u32 result =
        Particle::System::New(tracker->mRippleSystemID, 0x109, x, y, z, (const Vector3_16f *)0,
                              (Particle::Callback *)&tracker->mRippleCallback);
    data_0209ee74->mRippleSystemID = result;
    return result;
}

// @symbol func_0202293c
u32 func_0202293c(Fix12i x, Fix12i y, Fix12i z)
{
    Particle::SysTracker *base = data_0209ee74;
    u32 result = Particle::System::New(base->mSystemID_798, 0x118, x, y, z, (const Vector3_16f *)0,
                                       (Particle::Callback *)&base->mCallback_79c);
    data_0209ee74->mSystemID_798 = result;
    return result;
}

// @symbol func_020228dc
u32 func_020228dc(Fix12i x, Fix12i y, Fix12i z)
{
    Particle::SysTracker *base = data_0209ee74;
    u32 result = Particle::System::New(base->mSystemID_7a4, 0x117, x, y, z, (const Vector3_16f *)0,
                                       (Particle::Callback *)&base->mCallback_7a8);
    data_0209ee74->mSystemID_7a4 = result;
    return result;
}

// @symbol func_02022864
void func_02022864(Fix12i x, Fix12i y, Fix12i z, s16 ang1, s16 ang2)
{
    data_0209ee74->mCallback_7b4.scale = ang1;
    data_0209ee74->mCallback_7b4.velocity = ang2;
    data_0209ee74->mSystemID_7b0 =
        Particle::System::New(data_0209ee74->mSystemID_7b0, 0x51, x, y, z, (const Vector3_16f *)0,
                              (Particle::Callback *)&data_0209ee74->mCallback_7b4);
}

// @symbol func_020227ec
void func_020227ec(Fix12i x, Fix12i y, Fix12i z, s16 ang1, s16 ang2)
{
    data_0209ee74->mCallback_7c4.scale = ang1;
    data_0209ee74->mCallback_7c4.velocity = ang2;
    data_0209ee74->mSystemID_7c0 =
        Particle::System::New(data_0209ee74->mSystemID_7c0, 0x52, x, y, z, (const Vector3_16f *)0,
                              (Particle::Callback *)&data_0209ee74->mCallback_7c4);
}

// @symbol func_02022774
void func_02022774(Fix12i x, Fix12i y, Fix12i z, s16 ang1, s16 ang2)
{
    data_0209ee74->mCallback_7d4.scale = ang1;
    data_0209ee74->mCallback_7d4.velocity = ang2;
    data_0209ee74->mSystemID_7d0 =
        Particle::System::New(data_0209ee74->mSystemID_7d0, 0x4f, x, y, z, (const Vector3_16f *)0,
                              (Particle::Callback *)&data_0209ee74->mCallback_7d4);
}

// @symbol func_020226fc
void func_020226fc(Fix12i x, Fix12i y, Fix12i z, s16 arg3, s16 arg4)
{
    Particle::SysTracker *sys1;
    Particle::SysTracker *sys2;
    Particle::SysTracker *sys3;
    Particle::SysTracker *sys4;
    u32 result;

    sys1 = data_0209ee74;
    sys1->mCallback_7e4.scale = arg3;
    sys2 = data_0209ee74;
    sys2->mCallback_7e4.velocity = arg4;
    sys3 = data_0209ee74;
    result = Particle::System::New(sys3->mSystemID_7e0, 0x50, x, y, z, (const Vector3_16f *)0,
                                   (Particle::Callback *)&sys3->mCallback_7e4);
    sys4 = data_0209ee74;
    sys4->mSystemID_7e0 = result;
}
}

namespace Particle {

// @symbol _ZN8Particle19SetSelfDestructFlagEj
void SetSelfDestructFlag(u32 definitionID)
{
    data_0209ee74->mManager->mDefinitions[definitionID].data->flags |= 0x4000;
}

}
