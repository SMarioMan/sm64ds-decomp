#include "private/arm9_a1fc0_file_share.h"

extern void func_02041bbc(FileShareNode **from, FileShareNode **to, FileShareNode *node);

/* busy -> free: the loader has closed the node's file (state 0), and the
 * node is no longer counted in mBusyCount. */
void func_02041a94(FileShareParentArea *area, FileShareNode *node) {
    func_02041bbc(&area->mBusyList, &area->mFreeList, node);
    node->mState = 0;
    area->mBusyCount -= 1;
}
