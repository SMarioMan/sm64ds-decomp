//cpp
#include "dBgCh.h"

// @symbol _ZN5dBgChaSERKS_
dBgCh &dBgCh::operator=(const dBgCh &other) {
    mDetectFlags = other.mDetectFlags;
    mOwnerUniqueID = other.mOwnerUniqueID;
    mOwner = other.mOwner;
    return *this;
}
