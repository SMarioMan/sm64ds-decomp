//cpp
/* dExtAnmTexPat_c -- dExtFrameCtrl_c child driving BTP-file playback. Cartridge
   class: _ZTV15dExtAnmTexPat_c at 0x0208e7d4 (two slots, the destructor
   pair), RTTI record _ZTI15dExtAnmTexPat_c at 0x0208e758. TU claims
   0x0201597c..0x02015a7c, the whole class run in delinks order. Written
   back-to-front: mwccarm emits .text in reverse source order under default
   deferred codegen.

   leftovers:
   - SetFile is defined under the scalar mangling (Fix12i speed, u16
     startFrame) rather than Fix12<int> by value (wall 6az), like
     SetAnimation. The member declarations are real.
   - func_02046d50 and func_02046bbc stay extern "C" helpers with no
     declaring header; Prepare's ROM body is a 0xc long-call veneer, so it
     calls func_02046d50 with that function's own two-argument signature.
   - file->unk_00 is the frame count handed to SetAnimation (the sibling
     BTA names it numFrames); BTP_File names only the words UpdateFileOffsets
     touches.
   - RTTI stays off; see the note above the pragma. */
#include "dExtAnmTexPat_c.h"

/* Compiling with RTTI off emits no _ZTI/_ZTS records at all; the vtable
   preamble's typeinfo word deadstrips with the rest of the data sections.
   The pragma dates from when this class and its base carried coined names
   whose records had no cartridge home; under the cartridge spelling they
   would (_ZTI15dExtAnmTexPat_c at 0x0208e758, _ZTS15dExtAnmTexPat_c at 0x0208e824),
   so RTTI on is open as a manifest change (notes/model-rtti-names.md). */
#pragma RTTI off

extern "C" void func_02046d50(BMD_File *model, BTP_File *file);
extern "C" void func_02046bbc(ModelComponents *model, BTP_File *file, int frame);

// @symbol _ZN15dExtAnmTexPat_cC1Ev
dExtAnmTexPat_c::dExtAnmTexPat_c() {
    file = 0;
}

// @symbol _ZN15dExtAnmTexPat_cD1Ev
dExtAnmTexPat_c::~dExtAnmTexPat_c() {}

// @symbol _ZN15dExtAnmTexPat_c7SetFileER8BTP_Fileiit
void dExtAnmTexPat_c::SetFile(BTP_File &animFile, int flags, Fix12i speed, u16 startFrame) {
    if (&animFile == file) {
        SetFlags(flags);
        this->speed = speed;
    } else {
        file = &animFile;
        SetAnimation(animFile.unk_00, flags, speed, startFrame);
    }
}

// @symbol _ZN15dExtAnmTexPat_c6UpdateER15ModelComponents
void dExtAnmTexPat_c::Update(ModelComponents &model) {
    func_02046bbc(&model, file, (u16)((u32)currFrame >> 12));
}

/* The ROM body is a 0xc long-call veneer (ldr ip, [pc]; bx ip); the
   registers pass through untouched, so the matched func_02046d50.c's
   own two-argument signature is the call surface. Prepare is static:
   no this. */
// @symbol _ZN15dExtAnmTexPat_c7PrepareER8BMD_FileR8BTP_File
void dExtAnmTexPat_c::Prepare(BMD_File &model, BTP_File &animFile) {
    func_02046d50(&model, &animFile);
}
