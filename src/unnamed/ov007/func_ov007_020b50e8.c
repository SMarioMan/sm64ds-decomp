#include "types.h"
#include "nitro/fx/fx.h"
#include "Ov007MenuState.h"
#include "Ov007Sprite.h"
extern char *data_ov007_0210342c;
extern int data_ov007_02103428;

extern void func_ov007_020c1d8c(int i);
extern void func_ov007_020b647c(int r0, int r1, short r2);
extern void func_ov007_020b6208(int s);
extern void func_ov007_020b64a8(int a);
extern void func_ov007_020b7eec(void *t);
extern int _ZN4cstd3divEii(int a, int b);
extern void func_ov007_020aec94(int a);
extern void func_ov007_020b6134(int a);
extern void func_ov007_020b7a44(void);

/* The 10-byte layout row func_ov007_020aea6c's item points at; names as in
 * func_ov007_020b5bf0, only the slots this file reads. */
typedef struct Ov007ItemLayout {
    u16 kind;  /* 0x0 */
    s16 homeX; /* 0x2: func_ov007_020ae810 seeds posX from it */
} Ov007ItemLayout;

/* The 0x2c-byte record func_ov007_020aea6c allocates; names as in
 * func_ov007_020b5bf0 and func_ov007_020b5f64, only the slots this file
 * touches. */
typedef struct Ov007Item {
    u16 id; /* 0x00 */
    char pad_02[2];
    Ov007MenuState *state; /* 0x04: func_ov007_020c9388(1) */
    s32 posX;              /* 0x08: Q12 */
    char pad_0c[0x18];
    Ov007ItemLayout *layout; /* 0x24 */
} Ov007Item;

/* The 0x1c record func_ov007_020b4c04 returns; names as in that file. */
typedef struct Ov007ItemView {
    Ov007Item *item;     /* 0x00 */
    Ov007Sprite *sprite; /* 0x04: func_ov007_020c44e4 */
} Ov007ItemView;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020afc44 and func_ov007_020b3360, only the slots this file
 * reads. The callback at +0x2c stays raw. */
typedef struct Ov007Work {
    char pad_00[4];
    Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388; [1] is the main one */
    char pad_10[0x18];
    /* 0x28: the 0x3c-byte record func_ov007_020b6a84 allocates; its first
     * word points at a record with no layout yet, so `gp` stays raw */
    struct Ov007Settings *settings;
    char pad_2c[0x2c];
    int selectedSlot; /* 0x58: -1 = none (func_ov007_020b0244) */
    char pad_5c[0xb8];
    Ov007ItemView *itemViews[0x18]; /* 0x114: func_ov007_020b693c, one per func_ov007_020b4c04 */
} Ov007Work;

typedef char Ov007Item_layout_must_be_at_0x24[(int)&((Ov007Item *)0)->layout == 0x24 ? 1 : -1];
typedef char Ov007Sprite_scaleY_must_be_at_0x40[(int)&((Ov007Sprite *)0)->scaleY == 0x40 ? 1 : -1];
typedef char
    Ov007Work_selectedSlot_must_be_at_0x58[(int)&((Ov007Work *)0)->selectedSlot == 0x58 ? 1 : -1];
typedef char Ov007Work_size_must_be_0x174[sizeof(Ov007Work) == 0x174 ? 1 : -1];

#define WORK ((Ov007Work *)data_ov007_0210342c)

/* The item's state-2 step: on the state's first tick, sends the follow-up
 * state requests for this item, then over `thresh` ticks pops (ids 3/4),
 * nudges sideways (ids 10/11) or squashes its sprite; when the ticks run out
 * it resets the scale and requests the item's next state. arg keeps the
 * char * spelling of the definition; `view` is the typed view. */
void func_ov007_020b50e8(char *arg)
{
    Ov007ItemView *view = (Ov007ItemView *)arg;
    Ov007Item *st;
    u16 state;
    int t;
    int result;
    int is34;
    int thresh;
    Ov007MenuState *pv;
    char *gp;
    int v4;
    int posX;
    Ov007ItemLayout *r3p;

    st = view->item;
    state = st->id;
    r3p = st->layout;
    gp = *(char **)WORK->settings;
    t = st->state->stateTicks;
    v4 = r3p->kind;
    is34 = (state == 3 || state == 4);
    thresh = is34 ? 0x18 : 8;
    pv = WORK->states[1];
    posX = r3p->homeX << 12;
    result = 0x1000;

    if (t == 0) {
        func_ov007_020c1d8c(0);
        if (v4 == 0) {
            func_ov007_020b647c(view->item->id, 0, 6);
            func_ov007_020b647c(view->item->id, 1, 6);
            func_ov007_020b647c(view->item->id, 2, 6);
            func_ov007_020b647c(view->item->id, 7, 6);
        } else if ((u32)(state - 0xe) <= 2 && pv->currentState == 0) {
            func_ov007_020b647c(view->item->id, 0xe, 4);
            func_ov007_020b647c(view->item->id, 0xf, 4);
            func_ov007_020b647c(view->item->id, 0x10, 4);
            func_ov007_020b647c(view->item->id, 0x15, 4);
            func_ov007_020b647c(view->item->id, 0x14, 4);
        }
        {
            int flag;
            flag = 1;
            func_ov007_020b6208(state);
            switch (st->id) {
            case 9:
                break;
            case 11:
                func_ov007_020b64a8(flag);
                break;
            case 10:
                func_ov007_020b64a8(-1);
                break;
            case 12:
                if (*(u8 *)(gp + 9) == 0) {
                    ((void (*)(int))*(int *)(data_ov007_0210342c + 0x2c))(4);
                }
                break;
            case 13:
                if (*(u8 *)(gp + 9) != 0) {
                    ((void (*)(int))*(int *)(data_ov007_0210342c + 0x2c))(5);
                }
                break;
            default:
                flag = 0;
                break;
            }
            if (flag != 0) {
                func_ov007_020b7eec(*(char **)WORK->settings);
            }
        }
    }

    if (t < thresh) {
        int q;
        if (t <= 0) {
            q = 0;
        } else if (t >= thresh) {
            q = 0x1000;
        } else {
            q = _ZN4cstd3divEii(t << 12, thresh);
        }
        if (is34 != 0) {
            if (q < 0x555) {
                int c;
                int w;
                w = q * 3;
                w <<= 2;
                if (w <= 0x1000) {
                    c = FX_MUL(w, 0x1000);
                } else if (w <= 0x3000) {
                    c = FX_MUL(w - 0x1000, 0x800) + 0x1000;
                } else {
                    c = FX_MUL(w - 0x3000, -0x2000) + 0x2000;
                }
                result = 0x1000 - FX_MUL(c, 0x4b0);
            } else {
                int c;
                int w;
                w = ((q * 3 - 0x1000) / 2) * 4;
                if (w <= 0x1000) {
                    c = FX_MUL(w, 0x800);
                } else if (w <= 0x3000) {
                    c = FX_MUL(w - 0x1000, 0x400) + 0x800;
                } else {
                    c = FX_MUL(w - 0x3000, -0x1000) + 0x1000;
                }
                result = FX_MUL(c, 0x640) + 0x1000;
            }
        } else {
            u16 s2;
            s2 = st->id;
            if ((u16)(s2 + 0xfff6) <= 1) {
                int dir;
                int w;
                int d8;
                dir = (s2 == 10) ? -1 : 1;
                w = q * 2;
                if (w > 0x1000) {
                    w = -(w - 0x2000);
                }
                d8 = dir * 8;
                posX += d8 * w;
            } else {
                int c;
                int w;
                w = q * 4;
                if (w <= 0x1000) {
                    c = FX_MUL(w, 0x1000);
                } else if (w <= 0x3000) {
                    c = FX_MUL(w - 0x1000, -0x2ec) + 0x1000;
                } else {
                    c = FX_MUL(w - 0x3000, -0xa28) + 0xa28;
                }
                result = 0x1000 - FX_MUL(c, 0x514);
            }
        }
    } else {
        Ov007Sprite *p;
        int next;
        u16 s;
        p = view->sprite;
        next = 0;
        p->scaleY = 0x1000;
        p->scaleX = p->scaleY;
        s = st->id;
        switch (s) {
        case 0:
            func_ov007_020aec94(9);
            break;
        case 1:
            func_ov007_020aec94(6);
            break;
        case 2:
            func_ov007_020aec94(7);
            break;
        case 7:
            pv->requestedState = 8;
            next = 6;
            break;
        case 3:
            next = 1;
            WORK->states[0]->requestedState = 2;
            break;
        case 4:
            next = 1;
            WORK->states[0]->requestedState = 3;
            break;
        case 6:
            WORK->states[0]->requestedState = 4;
            break;
        case 8:
            pv->requestedState = next;
            break;
        case 14:
        case 15:
        case 16:
            func_ov007_020b6134(s - 0xe);
            break;
        case 21:
            pv->requestedState = 1;
            break;
        case 17:
            pv->requestedState = 3;
            break;
        case 18:
            pv->requestedState = 7;
            break;
        case 19:
            pv->requestedState = 9;
            break;
        case 20:
            switch (pv->currentState) {
            case 0:
                pv->requestedState = 0xb;
                break;
            case 1:
                pv->requestedState = next;
                break;
            case 2:
                pv->requestedState = 6;
                break;
            case 3:
            case 9:
                pv->requestedState = 1;
                break;
            case 7: {
                Ov007Work *d;
                d = WORK;
                if (d->selectedSlot != -1) {
                    d->selectedSlot = -1;
                } else {
                    pv->requestedState = 1;
                }
                break;
            }
            case 12:
                break;
            }
            break;
        case 22:
        case 23:
            if (s == 0x16) {
                data_ov007_02103428 = 2;
                WORK->itemViews[0x17]->item->state->requestedState = 4;
            } else if (s == 0x17) {
                data_ov007_02103428 = 3;
                WORK->itemViews[0x16]->item->state->requestedState = 4;
            }
            func_ov007_020b7a44();
            next = 4;
            break;
        }
        st->state->requestedState = next;
    }

    view->sprite->scaleY = result;
    view->sprite->scaleX = view->sprite->scaleY;
    view->item->posX = posX;
}
