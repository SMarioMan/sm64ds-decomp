//cpp
#include "dBgCh.h"

// @symbol _ZNK5dBgCh21IsIgnoringType14WallsEv
int dBgCh::IsIgnoringType14Walls() const {
    return mDetectFlags & 0x40;
}
