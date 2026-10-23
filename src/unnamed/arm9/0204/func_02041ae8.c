#include "private/arm9_a1fc0_file_share.h"

extern void func_02041bbc(FileShareNode **from, FileShareNode **to, FileShareNode *node);

/* ready -> busy: no child reads the node's region any more, so the loader
 * closes its file (state 3, releasing). */
void func_02041ae8(FileShareParentArea *area, FileShareNode *node) {
    func_02041bbc(&area->mReadyList, &area->mBusyList, node);
    node->mState = 3;
}
