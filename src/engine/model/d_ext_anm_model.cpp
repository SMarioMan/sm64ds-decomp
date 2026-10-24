//cpp
/* dExtAnmModel_c -- dExtSimpleModel_c + Animation multiple inheritance: the animated-model
   base the scene objects embed. Cartridge class: _ZTV14dExtAnmModel_c at
   0x0208e980 plus its Animation-side thunk vtable; _ZTI14dExtAnmModel_c
   at 0x0208e924 records bases dExtSimpleModel_c at 0x00 and
   dExtFrameCtrl_c at 0x50.
   TU claims 0x02016714..0x020169d8: the method run, then D2, D0, D1, C1
   and C2. The two _ZThn80_ destructor thunks stay in their own block.
   Defining ~dExtAnmModel_c() emits the MI vtable group. Its secondary preamble
   sits inside _ZTV14dExtAnmModel_c's compared extent, so RTTI stays on: the
   -0x50 word is a literal, and the _ZTI/_ZTS records emitted for
   dExtAnmModel_c, dExtSimpleModel_c and dExtModel_c compare against
   their cartridge homes before they are discarded. Written back-to-front:
   mwccarm emits .text in reverse source order under default deferred
   codegen. The constructor and destructor stand above the methods so the
   lifecycle emits after them, D2 D0 D1 then C1 C2. */
#include "dExtAnmModel_c.h"

/* Only the header word SetAnim reads; Animation::UpdateFileOffsets' shard
   spells the pointer fields instead. */
struct BCA_File {
    u16 unk_00;
    u16 numFrames;
};

/* One definition emits C1 and C2: dExtSimpleModel_c::C2, dExtFrameCtrl_c::C2 at +0x50,
   both vptr stores, and file = 0. The cartridge keeps both variants. */
// @symbol _ZN14dExtAnmModel_cC1Ev
// @symbol _ZN14dExtAnmModel_cC2Ev
dExtAnmModel_c::dExtAnmModel_c() {
    file = 0;
}

/* One definition emits D2, D0 and D1. The body is empty: both vptr restores
   and the base destructor calls are the compiler's, and D0 finishes with
   dExtAnmModel_c::operator delete. The cartridge keeps all three. */
// @symbol _ZN14dExtAnmModel_cD2Ev
// @symbol _ZN14dExtAnmModel_cD0Ev
// @symbol _ZN14dExtAnmModel_cD1Ev
dExtAnmModel_c::~dExtAnmModel_c() {}

// @symbol _ZN14dExtAnmModel_c11UpdateVertsEv
void dExtAnmModel_c::UpdateVerts() {
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    data.UpdateVertsUsingBones();
}

// @symbol _ZN14dExtAnmModel_c9Virtual10ER9Matrix4x3
void dExtAnmModel_c::Virtual10(Matrix4x3 &mat) {
    s32 frame = currFrame;
    data.UpdateBones(file, (u32)(frame << 4) >> 0x10);
    dExtSimpleModel_c::Virtual10(mat);
}

// @symbol _ZN14dExtAnmModel_c6RenderEPK7Vector3
void dExtAnmModel_c::Render(const Vector3 *scale) {
    UpdateVerts();
    dExtSimpleModel_c::Render(scale);
}

// @symbol _ZN14dExtAnmModel_c9Virtual18EjPK7Vector3
void dExtAnmModel_c::Virtual18(u32 mat, const Vector3 *scale) {
    Virtual10(*(Matrix4x3 *)mat);
    dExtSimpleModel_c::Render(scale);
}

/* Refresh bones without touching verts -- UpdateVerts' first half kept
   file-local; daMoray_c calls it on a dExtBlendAnmModel_c*. */
// @symbol func_020167a4
extern "C" void func_020167a4(dExtAnmModel_c *self) {
    s32 frame = self->currFrame;
    self->data.UpdateBones(self->file, (u32)(frame << 4) >> 0x10);
}

// @symbol _ZN14dExtAnmModel_c7SetAnimEP8BCA_Fileiit
void dExtAnmModel_c::SetAnim(BCA_File *animFile, int flags, Fix12i speed, u16 startFrame) {
    if (animFile == file) {
        SetFlags(flags);
        this->speed = speed;
    } else {
        file = animFile;
        static_cast<dExtFrameCtrl_c &>(*this).SetAnimation(animFile->numFrames, flags, speed,
                                                           startFrame);
    }
}

/* Both this and src adjust by +0x50 for the base call: the first real
   multiple-inheritance argument conversion in the tree. */
// @symbol _ZN14dExtAnmModel_c4CopyERKS_Pc
void dExtAnmModel_c::Copy(const dExtAnmModel_c &src, char *newFile) {
    dExtFrameCtrl_c::Copy(src);
    if (newFile != 0)
        file = (BCA_File *)newFile;
    else
        file = src.file;
}
