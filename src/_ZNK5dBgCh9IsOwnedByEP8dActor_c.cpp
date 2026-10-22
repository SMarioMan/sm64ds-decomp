//cpp
#include "dBgCh.h"
#include "dActor_c.h"

// @symbol _ZNK5dBgCh9IsOwnedByEP8dActor_c
bool dBgCh::IsOwnedBy(dActor_c *actor) const {
    if (actor == 0 || mOwner == 0)
        return false;
    u32 uniqueID = actor->uniqueID;
    if (mOwner == actor && mOwnerUniqueID == uniqueID)
        return true;
    return false;
}
