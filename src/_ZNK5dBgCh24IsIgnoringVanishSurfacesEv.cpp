//cpp
#include "dBgCh.h"

// @symbol _ZNK5dBgCh24IsIgnoringVanishSurfacesEv
int dBgCh::IsIgnoringVanishSurfaces() const {
    return mDetectFlags & 0x20;
}
