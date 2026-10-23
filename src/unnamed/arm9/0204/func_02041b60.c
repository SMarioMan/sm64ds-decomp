#include "private/arm9_a1fc0_file_share.h"

extern void func_02041bbc(FileShareNode **from, FileShareNode **to, FileShareNode *node);

/* free -> busy: takes the free list's head to be loaded (state 1) and
 * counts it in mBusyCount. */
FileShareNode *func_02041b60(FileShareParentArea *area) {
    FileShareNode *node;
    node = area->mFreeList;
    func_02041bbc(&area->mFreeList, &area->mBusyList, node);
    node->mState = 1;
    area->mBusyCount += 1;
    return node;
}
