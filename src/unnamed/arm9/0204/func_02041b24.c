#include "private/arm9_a1fc0_file_share.h"

extern void func_02041bbc(FileShareNode **from, FileShareNode **to, FileShareNode *node);

/* busy -> ready: the loader has read the region's first pages and
 * func_02041d28 has registered it (state 2). */
void func_02041b24(FileShareParentArea *area, FileShareNode *node) {
    func_02041bbc(&area->mBusyList, &area->mReadyList, node);
    node->mState = 2;
}
