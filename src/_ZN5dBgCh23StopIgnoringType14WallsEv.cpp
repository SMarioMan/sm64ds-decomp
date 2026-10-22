//cpp
#include "dBgCh.h"

// @symbol _ZN5dBgCh23StopIgnoringType14WallsEv
void dBgCh::StopIgnoringType14Walls() {
    mDetectFlags &= ~0x40;
}
