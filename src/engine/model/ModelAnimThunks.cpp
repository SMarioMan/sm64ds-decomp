//cpp
#pragma RTTI off
#include "dExtAnmModel_c.h"
#include "dExtBlendAnmModel_c.h"
#include "dExtAnm2Model_c.h"

/* The six _ZThn80_ destructor thunks are one run, 0x02017168..0x020171c8,
 * immediately after dExtModel_c's constructor. Each is the adjustor from the
 * dExtFrameCtrl_c base at +0x50 back to the complete object. They are not
 * contiguous with the class translation units, so those files discard their
 * own copies and this file is the enrolled home.
 *
 * Defining the three destructors is what emits the thunks. RTTI is off: the
 * cartridge type names are the dExt* spellings, and this file does not own
 * the vtables. The destructor bodies are duplicates of the lifecycle homes
 * below 0x020169d8. */

extern "C" void func_0203cbc0(void *ptr);

dExtAnmModel_c::~dExtAnmModel_c() {}

dExtBlendAnmModel_c::~dExtBlendAnmModel_c() {
    if (mBlendBuffer)
        func_0203cbc0(mBlendBuffer);
}

dExtAnm2Model_c::~dExtAnm2Model_c() {}
