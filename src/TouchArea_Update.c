#include "PlayerInput.h"
extern int func_0203da9c(void);

/* C view of dThIcon_c (include/dThIcon_c.h is C++): the touch-area fields,
   under the header's names. */
typedef struct ThIconView {
    void *vtable;             /* 0x00 */
    short mX;                 /* 0x04 */
    short mY;                 /* 0x06 */
    short mHalfW;             /* 0x08 */
    short mHalfH;             /* 0x0a */
    int mPressTimer;          /* 0x0c */
    unsigned char mOn;        /* 0x10 */
    unsigned char mReady;     /* 0x11 */
    unsigned char mPenInside; /* 0x12 */
    unsigned char pad_13;
    int mTouchKind; /* 0x14 */
} ThIconView;

int TouchArea_Update(char *c, int a1)
{
    int ret;
    int flag;
    int dx, dy;
    int v;
    ThIconView *icon = (ThIconView *)c;

    if (icon->mReady == 0)
        return 0;
    if (a1 < 0)
        a1 = func_0203da9c();
    ret = 0;
    flag = 0;
    if (gTouchHeld[a1 * 4] != 0) {
        int i4 = a1 * 4;
        dx = gTouchX[i4] - icon->mX;
        dy = gTouchY[i4] - icon->mY;
        if (dx >= -icon->mHalfW && dx <= icon->mHalfW && dy >= -icon->mHalfH && dy <= icon->mHalfH)
            flag = 1;
    }
    if (flag != 0) {
        v = icon->mTouchKind;
        if ((v == 1 && gTouchEdge[(unsigned int)a1 * 4] != 0) || (v == 2 && icon->mPenInside == 0))
            ret = 1;
    }
    icon->mPenInside = (unsigned char)flag;
    return ret;
}
