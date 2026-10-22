#include "Ov007MenuState.h"

extern void func_ov007_020c1d8c(int i);
extern void RequestScreenFade(int a, int b, void* p);
extern char data_ov007_0210342c[];
extern char func_ov007_020b0520[];
extern char func_ov007_020af580[];

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020aec94 and func_ov007_020b0834, only the slots this file
 * reads. The callback at +0x2c stays raw, as in func_ov007_020b0834. */
typedef struct Ov007Work {
    char pad_00[4];
    Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388 */
    /* 0x10: the choice func_ov007_020aec94 was last given */
    int pendingChoice;
} Ov007Work;

typedef char Ov007Work_size_must_be_0x14[sizeof(Ov007Work) == 0x14 ? 1 : -1];

/* The extern keeps its char[] spelling; the typed view is reached through a
 * cast macro. */
#define WORK (*(Ov007Work **)data_ov007_0210342c)

/* On entering states[1]'s current state it calls func_ov007_020c1d8c(0);
 * 0x1e ticks in, it fades out to func_ov007_020b0520 (no choice pending)
 * or func_ov007_020af580, and passes 0x13 to the manager's callback. */
void func_ov007_020af4dc(void) {
    Ov007Work *g = WORK;
    if (g->states[1]->stateTicks == 0) {
        func_ov007_020c1d8c(0);
    }
    g = WORK;
    if (g->states[1]->stateTicks != 0x1e)
        return;
    if (g->pendingChoice == 0) {
        RequestScreenFade(2, 1, func_ov007_020b0520);
    } else {
        RequestScreenFade(1, 0, func_ov007_020af580);
    }
    (*(void (**)(int))(*(char **)data_ov007_0210342c + 0x2c))(0x13);
}
