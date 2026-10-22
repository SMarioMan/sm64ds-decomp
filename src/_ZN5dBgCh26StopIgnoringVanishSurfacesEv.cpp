//cpp
#include "dBgCh.h"

// @symbol _ZN5dBgCh26StopIgnoringVanishSurfacesEv
void dBgCh::StopIgnoringVanishSurfaces() {
    mDetectFlags &= ~0x20;
}
