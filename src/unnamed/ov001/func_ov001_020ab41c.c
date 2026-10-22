extern void func_ov001_020ab3f0(void *r0);

/* File-local C view of the head of dThIcon_c (include/dThIcon_c.h is
 * C++ only); callers pass &mIcons[i]. */
typedef struct dThIconView {
    void *vtable;      /* 0x00 */
    short mX;          /* 0x04 */
    short mY;          /* 0x06 */
    short mHalfW;      /* 0x08 */
    short mHalfH;      /* 0x0a */
    int mPressTimer;   /* 0x0c */
    unsigned char mOn; /* 0x10 */
} dThIconView;
typedef char dThIconView_mOn_must_be_at_0x10[(int)&((dThIconView *)0)->mOn == 0x10 ? 1 : -1];

void func_ov001_020ab41c(void *c) {
    if (((dThIconView *)c)->mOn == 0) {
        ((dThIconView *)c)->mOn = 1;
        return;
    }
    func_ov001_020ab3f0(c);
}
