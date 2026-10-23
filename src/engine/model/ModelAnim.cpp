//cpp
/* ModelAnim -- Model + Animation multiple inheritance: the animated-model
   base the scene objects embed. Cartridge class: _ZTV9ModelAnim at
   0x0208e980 plus its Animation-side thunk vtable; the cartridge RTTI
   names it dExtAnmModel_c (_ZTI14dExtAnmModel_c at 0x0208e924,
   base dExtSimpleModel_c at 0x00 and dExtFrameCtrl_c at 0x50).
   TU claims 0x02016714..0x020169d8: the method run, then D2, D0, D1, C1
   and C2. The two _ZThn80_ destructor thunks stay in their own block.
   Defining ~ModelAnim() emits the MI vtable group. Its secondary preamble
   sits inside _ZTV9ModelAnim's compared extent, so RTTI stays on: the
   -0x50 word is a literal, and the manifest retargets the coined
   _ZTI/_ZTS records onto dExtAnmModel_c, dExtSimpleModel_c and
   dExtModel_c for that compare. The coined type strings are not the
   cartridge's and are discarded, not linked. Written back-to-front:
   mwccarm emits .text in reverse source order under default deferred
   codegen. The constructor and destructor stand above the methods so the
   lifecycle emits after them, D2 D0 D1 then C1 C2. */
#include "ModelAnim.h"

extern "C" {
/* SetAnim keeps its mangled spelling because of the NAME, not wall 6az:
   measured 2026-10-22, it reproduces as a real method under the scalar
   mangling _ZN9ModelAnim7SetAnimEP8BCA_Fileiit, and only the class-typed
   `5Fix12IiE` spelling costs (+0x18, since the body reads `speed`). The
   rename is a campaign, not a local edit -- notes/mwccarm-codegen.md 6az,
   MEASURED 2026-10-22. ModelAnim.h's declaration is the one callers use,
   but the measured method takes Fix12i and a u16 startFrame (retail
   reads it with `ldrh`), not Fix12<int> and u32.
   local extern: Fix12 by-value speed. */
void _ZN15dExtFrameCtrl_c12SetAnimationEti5Fix12IiEt(dExtFrameCtrl_c *self, u16 numFrames,
                                                     s32 flags, s32 speed, u16 startFrame);
}

/* Only the header word SetAnim reads; Animation::UpdateFileOffsets' shard
   spells the pointer fields instead. */
struct BCA_File {
    u16 unk_00;
    u16 numFrames;
};

/* One definition emits C1 and C2: Model::C2, dExtFrameCtrl_c::C2 at +0x50,
   both vptr stores, and file = 0. The cartridge keeps both variants. */
// @symbol _ZN9ModelAnimC1Ev
// @symbol _ZN9ModelAnimC2Ev
ModelAnim::ModelAnim() {
    file = 0;
}

/* One definition emits D2, D0 and D1. The body is empty: both vptr restores
   and the base destructor calls are the compiler's, and D0 finishes with
   ModelAnim::operator delete. The cartridge keeps all three. */
// @symbol _ZN9ModelAnimD2Ev
// @symbol _ZN9ModelAnimD0Ev
// @symbol _ZN9ModelAnimD1Ev
ModelAnim::~ModelAnim() {}

// @symbol _ZN9ModelAnim11UpdateVertsEv
void ModelAnim::UpdateVerts() {
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    data.UpdateVertsUsingBones();
}

// @symbol _ZN9ModelAnim9Virtual10ER9Matrix4x3
void ModelAnim::Virtual10(Matrix4x3 &mat) {
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    Model::Virtual10(mat);
}

// @symbol _ZN9ModelAnim6RenderEPK7Vector3
void ModelAnim::Render(const Vector3 *scale) {
    UpdateVerts();
    Model::Render(scale);
}

// @symbol _ZN9ModelAnim9Virtual18EjPK7Vector3
void ModelAnim::Virtual18(u32 mat, const Vector3 *scale) {
    Virtual10(*(Matrix4x3 *)mat);
    Model::Render(scale);
}

/* Refresh bones without touching verts -- UpdateVerts' first half kept
   file-local; daMoray_c calls it on a BlendModelAnim*. */
// @symbol func_020167a4
extern "C" void func_020167a4(ModelAnim *self) {
    s32 frame = self->currFrame;
    self->data.UpdateBones(self->file, (u32)(frame << 4) >> 0x10);
}

// @symbol _ZN9ModelAnim7SetAnimEP8BCA_Filei5Fix12IiEj
extern "C" void _ZN9ModelAnim7SetAnimEP8BCA_Filei5Fix12IiEj(ModelAnim *thiz, BCA_File *animFile,
                                                            s32 flags, s32 speed, u16 startFrame) {
    if (animFile == thiz->file) {
        thiz->SetFlags(flags);
        thiz->speed = speed;
    } else {
        thiz->file = animFile;
        _ZN15dExtFrameCtrl_c12SetAnimationEti5Fix12IiEt(
            &static_cast<dExtFrameCtrl_c &>(*thiz), animFile->numFrames, flags, speed, startFrame);
    }
}

/* Both this and src adjust by +0x50 for the base call: the first real
   multiple-inheritance argument conversion in the tree. */
// @symbol _ZN9ModelAnim4CopyERKS_Pc
void ModelAnim::Copy(const ModelAnim &src, char *newFile) {
    dExtFrameCtrl_c::Copy(src);
    if (newFile != 0)
        file = (BCA_File *)newFile;
    else
        file = src.file;
}
