//cpp
/* BlendModelAnim -- ModelAnim child that cross-fades from the old pose into
   the new animation. Cartridge class: _ZTV14BlendModelAnim at 0x0208e94c
   plus its Animation-side thunk vtable at 0x0208e970; the cartridge RTTI
   names it dExtBlendAnmModel_c. TU claims 0x020163e0..0x02016714 -- the
   method run, then D0, D1 and C1. ~BlendModelAnim() is the key function, so
   this object also emits the MI vtable group, D2, C2 and the two _ZThn80_
   thunks. RTTI stays off across that definition: the coined name would emit
   homeless _ZTI/_ZTS records, and the secondary preamble (inside the primary
   _ZTV, ahead of VTable_Animation_BlendModelAnimThunk) comes out as zeros.
   Those two cartridge words are a real preamble, not slots; the retail table
   is externalized unchanged. D2 and C2 have no cartridge home. The thunks
   stay enrolled in their own shards; this copy is a duplicate. Written
   back-to-front: mwccarm emits .text in reverse source order under default
   deferred codegen, so the constructor and destructor are first in the file
   and land after the methods. */
#include "BlendModelAnim.h"
#include "Memory.h"

/* RTTI stays off for the whole TU. Deferred codegen emits the key function
   at the end of the file, so a later `#pragma RTTI on` would turn the records
   back on. On, the TU would emit _ZTI/_ZTS for BlendModelAnim and every
   coined base. Off, the secondary preamble's offset-to-top and typeinfo
   words are zeros; romdata_check masks that pair when the cartridge has a
   negative offset-to-top and a _ZTI pointer. The method bodies do not use
   RTTI and match either way. */
#pragma RTTI off

extern "C" {
/* local extern: no header declares it; blends verts toward the old pose in
   Virtual10/UpdateVerts while blendWeight is still below 1.0 */
void func_0204531c(ModelComponents *data, s32 weight);
/* local extern: no header declares it; sizes the mBlendBuffer blend buffer off the
   file. Spelled (int *) the way func_020462bc.c defines it */
u32 func_020462bc(int *file);
/* local extern: no header declares it; initializes ModelComponents' side of
   the blend buffer. Spelled (int *, int) the way func_020462b4.c defines it */
void func_020462b4(int *data, int buf);
/* local extern: no header declares it; D1 frees mBlendBuffer through this veneer */
void func_0203cbc0(void *ptr);
/* defined below -- DoSetFile's tail; it sits between UpdateVerts and
   DoSetFile in the ROM and DoSetFile is its only caller here */
int func_020165c4(BlendModelAnim *self, char *file);
/* SetAnim below and its SetAnimation call keep their mangled spellings
   because of the NAMES, not wall 6az. Measured 2026-10-22: SetAnim
   reproduces 0x020163e0/0x9c as a real method under the scalar mangling
   _ZN14BlendModelAnim7SetAnimER8BCA_Fileiiit; only the class-typed
   `5Fix12IiE` spelling costs. The rename is a campaign, not a local edit --
   notes/mwccarm-codegen.md 6az, MEASURED 2026-10-22. The declarations in
   BlendModelAnim.h and dExtFrameCtrl_c.h are the ones callers use; the
   measured method takes Fix12i where they say Fix12<int>. */
void _ZN15dExtFrameCtrl_c12SetAnimationEti5Fix12IiEt(dExtFrameCtrl_c *self, u16 numFrames, s32 flags, s32 speed, u16 startFrame);
}

namespace cstd { int fdiv(int a, int b); }

/* Only the header word SetAnim reads; dExtFrameCtrl_c::UpdateFileOffsets' shard
   spells the pointer fields instead. */
struct BCA_File {
    u16 unk_00;
    u16 numFrames;
};

/* One definition emits C1 and C2. C2 has no cartridge home. blendStep stays
   uninitialised: Advance seeds it from SetAnim, and the ROM ctor never stores
   it. Empty body; the two stores are the init list. */
// @symbol _ZN14BlendModelAnimC1Ev
BlendModelAnim::BlendModelAnim() : blendWeight(0x1000), mBlendBuffer(0) {}

/* One definition emits D2, D0 and D1, then the _ZThn80_ pair. D0 adds the
   class operator delete. The written obligation is the conditional free of
   mBlendBuffer; a bare delete would call operator delete with no test. */
// @symbol _ZN14BlendModelAnimD1Ev
BlendModelAnim::~BlendModelAnim() {
    if (mBlendBuffer)
        func_0203cbc0(mBlendBuffer);
}

// @symbol _ZN14BlendModelAnim9DoSetFileEPcii
int BlendModelAnim::DoSetFile(char *file, int a, int b)
{
    char *f = file;
    int r = Model::DoSetFile(file, a, b);
    if (r == 0)
        return 0;
    return func_020165c4(this, f);
}

/* DoSetFile's tail: allocates the mBlendBuffer blend buffer sized off the file and
   hands it plus the ModelComponents member to func_020462b4. It sits between
   UpdateVerts and DoSetFile in the ROM. */
// @symbol func_020165c4
extern "C" int func_020165c4(BlendModelAnim *self, char *file)
{
    self->mBlendBuffer = Memory::operator_new2(func_020462bc((int *)file));
    void *p = self->mBlendBuffer;
    if (p == 0) return 0;
    func_020462b4((int *)&self->data, (int)p);
    return 1;
}

// @symbol _ZN14BlendModelAnim11UpdateVertsEv
void BlendModelAnim::UpdateVerts()
{
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    if (blendWeight < 0x1000) {
        func_0204531c(&data, blendWeight);
    } else {
        data.UpdateVertsUsingBones();
    }
}

// @symbol _ZN14BlendModelAnim9Virtual10ER9Matrix4x3
void BlendModelAnim::Virtual10(Matrix4x3 &mat)
{
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    if (blendWeight < 0x1000) {
        func_0204531c(&data, blendWeight);
    } else {
        Model::Virtual10(mat);
    }
}

// @symbol _ZN14BlendModelAnim6RenderEPK7Vector3
void BlendModelAnim::Render(const Vector3 *scale)
{
    UpdateVerts();
    Model::Render(scale);
}

// @symbol _ZN14BlendModelAnim9Virtual18EjPK7Vector3
void BlendModelAnim::Virtual18(u32 mat, const Vector3 *scale)
{
    Virtual10(*(Matrix4x3 *)mat);
    Model::Render(scale);
}

// @symbol _ZN14BlendModelAnim7AdvanceEv
void BlendModelAnim::Advance()
{
    dExtFrameCtrl_c::Advance();
    if (blendWeight < 0x1000) {
        /* launder: keep the RMW aliasing the member so the compiler
           re-reads it the way the ROM does */
        *(int *)(&blendWeight) += blendStep;
    }
}

// @symbol _ZN14BlendModelAnim7SetAnimER8BCA_Fileii5Fix12IiEt
extern "C" void _ZN14BlendModelAnim7SetAnimER8BCA_Fileii5Fix12IiEt(
    BlendModelAnim *thiz, BCA_File &file, s32 numBlendFrames, s32 flags,
    s32 speed, u16 startFrame)
{
    if (&file == thiz->file)
    {
        thiz->SetFlags(flags);
        thiz->speed = speed;
    }
    else
    {
        thiz->file = &file;
        _ZN15dExtFrameCtrl_c12SetAnimationEti5Fix12IiEt(
            &static_cast<dExtFrameCtrl_c &>(*thiz), file.numFrames, flags, speed,
            startFrame);
        if (numBlendFrames <= 0)
        {
            thiz->blendWeight = 0x1000;
        }
        else
        {
            thiz->blendWeight = 0;
            thiz->blendStep = cstd::fdiv(0x1000, (numBlendFrames + 1) << 12);
        }
    }
}
