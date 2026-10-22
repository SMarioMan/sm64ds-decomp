#include "types.h"
#include "Ov007MenuState.h"
extern char* data_ov007_0210342c;

/* func_ov007_020c9110's animation player; names as in func_ov007_020bc02c,
 * only the slots this file reads. */
typedef struct Ov007AnimPlayer {
    char pad_00[0xc];
    s16 anim; /* 0x0c: index into the owner's animation table; -1 none */
    char pad_0e[2];
    u16 frame; /* 0x10: the whole frame func_ov007_020c9110 last reached */
} Ov007AnimPlayer;

/* The model record func_ov007_020bc6d4 allocates; names as in
 * func_ov007_020bc02c, only the slot this file reads. */
typedef struct Ov007Model {
    char pad_00[0x18];
    Ov007AnimPlayer *boneAnim; /* 0x18: func_ov007_020bc894 ticks it */
} Ov007Model;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020b257c and func_ov007_020b2370, only the slots this file
 * reads. Left raw on `g`: +0xe8 and +0xec, with no role evidenced yet. */
typedef struct Ov007Work {
    char pad_00[4];
    Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388; [1] is the main one */
    char pad_10[0xe4];
    Ov007Model *model; /* 0xf4: func_ov007_020b2998 stores func_ov007_020b2bd4's model */
    char pad_f8[8];
    void *figure; /* 0x100: func_ov007_020beaa0 */
    /* 0x104: the second figure; returned in place of figure when +0xec is 1 */
    void *altFigure;
} Ov007Work;

typedef char Ov007Work_size_must_be_0x108[sizeof(Ov007Work) == 0x108 ? 1 : -1];

/* Picks a figure: none while +0xe8 is 0; while the model's bone animation
 * is animation 0, the figure (or, from frame 0x7c on with +0xec set to 1,
 * the second figure); otherwise the figure only in main state 0xb. */
int func_ov007_020be850(void) {
    char* g = data_ov007_0210342c;
    Ov007Work *work = (Ov007Work *)g;
    Ov007AnimPlayer *r2;
    int res = 0;
    if (*(int*)(g + 0xe8) == 0) return res;
    r2 = work->model->boneAnim;
    if (r2->anim == 0) {
        if (r2->frame >= 0x7c) {
            if (*(int *)(g + 0xec) == 1)
                return (int)work->altFigure;
        }
        return (int)work->figure;
    }
    if (work->states[1]->currentState == 0xb)
        res = (int)work->figure;
    return res;
}
