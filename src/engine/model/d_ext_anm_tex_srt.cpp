//cpp
/* dExtAnmTexSRT_c -- dExtFrameCtrl_c child driving BTA-file playback. Cartridge
   class: _ZTV15dExtAnmTexSRT_c at 0x0208e7c4 (two slots, the destructor
   pair), RTTI record _ZTI15dExtAnmTexSRT_c at 0x0208e74c. TU claims
   0x0201587c..0x0201597c, the whole class run in delinks order. Written
   back-to-front: mwccarm emits .text in reverse source order under default
   deferred codegen.

   leftovers:
   - SetFile keeps its mangled spelling (Fix12<int> by value, wall 6az).
     SetAnimation is the scalar method. The member declarations are real.
   - func_020469e8 and func_02046b64 stay extern "C" helpers with no
     declaring header; Prepare's ROM body is a 0xc long-call veneer, so it
     calls func_02046b64 with that function's own two-argument signature.
   - RTTI stays off; see the note above the pragma. */
#include "dExtAnmTexSRT_c.h"

/* Compiling with RTTI off emits no _ZTI/_ZTS records at all; the vtable
   preamble's typeinfo word deadstrips with the rest of the data sections.
   The pragma dates from when this class and its base carried coined names
   whose records had no cartridge home; under the cartridge spelling they
   would (_ZTI15dExtAnmTexSRT_c at 0x0208e74c, _ZTS15dExtAnmTexSRT_c at 0x0208e810),
   so RTTI on is open as a manifest change (notes/model-rtti-names.md). */
#pragma RTTI off

extern "C" void func_02046b64(BMD_File *model, BTA_File *file);
extern "C" void func_020469e8(ModelComponents *model, BTA_File *file, int frame);

// @symbol _ZN15dExtAnmTexSRT_cC1Ev
dExtAnmTexSRT_c::dExtAnmTexSRT_c() {
    file = 0;
}

// @symbol _ZN15dExtAnmTexSRT_cD1Ev
dExtAnmTexSRT_c::~dExtAnmTexSRT_c() {}

// @symbol _ZN15dExtAnmTexSRT_c7SetFileER8BTA_Filei5Fix12IiEj
extern "C" void _ZN15dExtAnmTexSRT_c7SetFileER8BTA_Filei5Fix12IiEj(dExtAnmTexSRT_c *self,
                                                                   BTA_File *file, s32 flags,
                                                                   s32 speed, u16 startFrame) {
    if (file == self->file) {
        self->SetFlags(flags);
        self->speed = speed;
    } else {
        self->file = file;
        self->SetAnimation(file->numFrames, flags, speed, startFrame);
    }
}

// @symbol _ZN15dExtAnmTexSRT_c6UpdateER15ModelComponents
void dExtAnmTexSRT_c::Update(ModelComponents &model) {
    func_020469e8(&model, file, (u16)((u32)currFrame >> 12));
}

/* The ROM body is a 0xc long-call veneer (ldr ip, [pc]; bx ip); the
   registers pass through untouched, so the matched func_02046b64.c's
   own two-argument signature is the call surface. Prepare is static:
   no this. */
// @symbol _ZN15dExtAnmTexSRT_c7PrepareER8BMD_FileR8BTA_File
void dExtAnmTexSRT_c::Prepare(BMD_File &model, BTA_File &animFile) {
    func_02046b64(&model, &animFile);
}
