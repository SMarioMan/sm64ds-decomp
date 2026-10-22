#include "types.h"
#include "Ov007MenuState.h"
extern int func_ov007_020c1da0(int i);
extern void func_ov007_020bdeb0(int i);

extern char* data_ov007_0210342c;
extern char* data_ov007_02103360;

/* data_ov007_02103360: the 0x1c-byte menu cursor func_ov007_020b30b0
 * allocates; names as in func_ov007_020b2e64, only the slot this file
 * touches. */
typedef struct Ov007Cursor {
    Ov007MenuState *state; /* 0x00: func_ov007_020c9388(0xff) */
} Ov007Cursor;

/* The 0x70-byte key record func_ov007_020c2304 allocates; names as in
 * func_ov007_020b1cf0. */
typedef struct Ov007Pad {
    u16 keys;     /* 0x00: held this frame */
    u16 prevKeys; /* 0x02: held last frame */
} Ov007Pad;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020b1cf0, only the slots this file reads. */
typedef struct Ov007Work {
    char pad_00[4];
    Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388 */
    char pad_10[0x44];
    Ov007Pad *pad; /* 0x54: func_ov007_020c2304 */
} Ov007Work;

typedef char Ov007Work_size_must_be_0x58[sizeof(Ov007Work) == 0x58 ? 1 : -1];

/* The externs keep the tree's char * spelling; the typed views are reached
 * through cast macros. */
#define CURSOR ((Ov007Cursor *)data_ov007_02103360)
#define WORK ((Ov007Work *)data_ov007_0210342c)

/* On a fresh key press with B not held (and no touch, func_ov007_020c1da0):
 * from states[0] 0 / states[1] 0 it requests cursor state 0 and plays sound
 * 3; from states[0] 5 (unless states[1] is 0xb or 0xc) cursor state 0xe and
 * sound 3. states[1] 8 requests cursor state 9 at once. */
void func_ov007_020b3190(void) {
    Ov007Work *g = WORK;
    int state1 = g->states[0]->currentState;

    switch (state1) {
    case 0: {
        int state2 = g->states[1]->currentState;
        switch (state2) {
        case 0: {
            int r5 = 0;
            int r4 = 0;
            if (func_ov007_020c1da0(0) == 0) {
                Ov007Pad *p = WORK->pad;
                if (p->keys & ~p->prevKeys)
                    r4 = 1;
            }
            if (r4) {
                Ov007Pad *p2 = WORK->pad;
                if ((p2->keys & 2) == 0)
                    r5 = 1;
            }
            if (r5 == 0)
                return;
            CURSOR->state->requestedState = 0;
            func_ov007_020bdeb0(3);
            return;
        }
        case 8:
            CURSOR->state->requestedState = 9;
            return;
        }
        return;
    }
    case 5: {
        int r5 = 0;
        int r4 = 0;
        int st;
        if (func_ov007_020c1da0(0) == 0) {
            Ov007Pad *p = WORK->pad;
            if (p->keys & ~p->prevKeys)
                r4 = 1;
        }
        if (r4) {
            Ov007Pad *p2 = WORK->pad;
            if ((p2->keys & 2) == 0)
                r5 = 1;
        }
        if (r5 == 0)
            return;
        st = WORK->states[1]->currentState;
        if (st == 0xc)
            return;
        if (st == 0xb)
            return;
        CURSOR->state->requestedState = 0xe;
        func_ov007_020bdeb0(3);
        return;
    }
    }
}
