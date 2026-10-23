#include "private/arm9_a1fc0_file_share.h"

extern unsigned int _ZN3IRQ7DisableEv(void);
extern void _ZN3IRQ7RestoreEj(unsigned int savedState);

/* Moves node off the list headed by *from onto the front of the list headed
 * by *to, with interrupts off. The parent's three node lists (free, ready,
 * busy) change only through here: func_02041b60, func_02041b24,
 * func_02041ae8 and func_02041a94 are its four moves.
 *
 * The search never advances: the loop either unlinks the node from behind
 * the head or breaks. A node third in its list is left where it is, and
 * nothing is moved. That is the ROM's code (0x02041bf4..0x02041c14), not a
 * decompilation slip; with a pool of three nodes, a list can be three long. */
void func_02041bbc(FileShareNode **from, FileShareNode **to, FileShareNode *node) {
    unsigned int saved = _ZN3IRQ7DisableEv();
    FileShareNode *cur = *from;
    if (cur == node) {
        *from = node->mNext;
        node->mNext = *to;
        *to = node;
    } else {
        while (cur != 0) {
            if (cur->mNext != node)
                break;
            cur->mNext = node->mNext;
            node->mNext = *to;
            *to = node;
            break;
        }
    }
    _ZN3IRQ7RestoreEj(saved);
}
