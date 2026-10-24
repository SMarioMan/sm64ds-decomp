//cpp
/* dExtAnm2Model_c -- a dExtAnmModel_c that carries a second dExtFrameCtrl_c (otherAnim)
   and the BCA file it plays (otherFile). _ZTI15dExtAnm2Model_c at 0x0208e788
   records single inheritance from dExtAnmModel_c; the vtable
   _ZTV15dExtAnm2Model_c at 0x0208e9b4 overrides only the destructor pair.
   TU claims 0x02016254..0x020163e0 -- the method run, then D0, D1 and C1.
   ~dExtAnm2Model_c() is the key function, so this object also emits the MI vtable
   group, D2, C2 and the two _ZThn80_ thunks. RTTI stays off across that
   definition, so no _ZTI/_ZTS records are emitted, and the
   secondary preamble (inside the primary _ZTV, ahead of
   VTable_Animation_ModelAnim2Thunk) comes out as zeros. Those two cartridge
   words are a real preamble, not slots; the retail table is externalized
   unchanged. D2 and C2 have no cartridge home. The thunks stay enrolled in
   their own shards; this copy is a duplicate. Written back-to-front: mwccarm
   emits .text in reverse source order under default deferred codegen, so the
   constructor and destructor are first in the file and land after the methods. */
#include "dExtAnm2Model_c.h"

/* RTTI stays off for the whole TU. Deferred codegen emits the key function
   at the end of the file, so a later `#pragma RTTI on` would turn the records
   back on. On, the TU would emit _ZTI/_ZTS for dExtAnm2Model_c and each of
   its bases. Off, the secondary preamble's offset-to-top and typeinfo words are
   zeros; romdata_check masks that pair when the cartridge has a negative
   offset-to-top and a _ZTI pointer. The method bodies do not use RTTI and
   match either way. */
#pragma RTTI off

extern "C" {
/* local extern: defined in src/engine/model/Model4.cpp, which types the frame
   `short`; no header declares it. Stores (file, frame) into bone slot i of the
   components' animation array. The frame stays `int` here: the ROM passes
   func_020162a4's `lsr #16` result with no sign extension, which a `short`
   parameter would add (the one-function source this TU absorbed carried
   the same banked param:#4 int disagreement). */
void func_02045e2c(int obj, int i, int a, int b);
}

/* Only the header word Func_020162C4 reads; the first halfword is not
   read anywhere in this TU. */
struct BCA_File {
    u8 pad_00[0x2];
    u16 numFrames; /* 0x02 */
};

/* One definition emits C1 and C2. C2 has no cartridge home. otherFile is
   declared before otherAnim, so the init list stores it before the member
   constructor; a body store would land one call too late. */
// @symbol _ZN15dExtAnm2Model_cC1Ev
dExtAnm2Model_c::dExtAnm2Model_c() : otherFile(0) {}

/* One definition emits D2, D0 and D1, then the _ZThn80_ pair. D0 adds the
   class operator delete. The body is empty: the vptr stores and the base
   destructor follow from the class. */
// @symbol _ZN15dExtAnm2Model_cD1Ev
dExtAnm2Model_c::~dExtAnm2Model_c() {}

/* The second animation's SetAnim, fast path and all: the same body as
   dExtAnmModel_c::SetAnim, run on otherFile and otherAnim. */
// @symbol _ZN15dExtAnm2Model_c13Func_020162C4Ejiit
void dExtAnm2Model_c::Func_020162C4(u32 animFile, int flags, Fix12i speed, u16 startFrame) {
    if (animFile == otherFile) {
        otherAnim.SetFlags(flags);
        otherAnim.speed = speed;
    } else {
        otherFile = animFile;
        otherAnim.SetAnimation(((BCA_File *)animFile)->numFrames, flags, speed, startFrame);
    }
}

/* Pose bone `bone` from the second animation at its current frame. Player
   calls it on a body model with bone 8; the int `self` keeps Player's
   declaration and this definition in agreement. */
// @symbol func_020162a4
extern "C" void func_020162a4(int self, int bone) {
    dExtAnm2Model_c *model = (dExtAnm2Model_c *)self;
    s32 frame = model->otherAnim.currFrame;
    func_02045e2c((int)&model->data, bone, model->otherFile, (u32)(frame << 4) >> 16);
}

/* Release bone `bone` back to the primary animation (no file, frame 0). */
// @symbol func_0201628c
extern "C" void func_0201628c(int self, int bone) {
    dExtAnm2Model_c *model = (dExtAnm2Model_c *)self;
    func_02045e2c((int)&model->data, bone, 0, 0);
}

/* otherAnim.Copy(src) upcasts src to its dExtFrameCtrl_c BASE (+0x50): the
   second animation is seeded from the first one's state. */
// @symbol _ZN15dExtAnm2Model_c4CopyERKS_Pcj
void dExtAnm2Model_c::Copy(const dExtAnm2Model_c &src, char *newFile, u32 newOtherFile) {
    dExtAnmModel_c::Copy(src, newFile);
    otherAnim.Copy(src);
    if (newOtherFile)
        otherFile = newOtherFile;
    else
        otherFile = src.otherFile;
}
