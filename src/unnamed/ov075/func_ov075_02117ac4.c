
extern unsigned char data_0209d45c;
extern unsigned char data_0209d454;
extern int data_ov075_0211d71c[];
extern void func_ov075_02116028(int *p, int v);
extern void func_020338b0(int a, int b, int c, int d);
extern void _ZN3G2x18SetBlendBrightnessEPVtts(void *p, unsigned short a, unsigned short b, short c);
/* C view of include/dScEntry_c.h's dScEntry_c (a C++ class this C file
 * cannot include), with the header's names; only the fields used here.
 * A dScEntry_c::Step: the step-set data at 0x0211c8a0 points at it. */
typedef struct dScEntry_c {
    unsigned char pad_000[0x264];
    int mStepDelay;                      /* 0x264 */
    int mStepWork[4];                    /* 0x268 */
    int mSoundHandle;                    /* 0x278 */
    unsigned char mResultLeaderFlags[4]; /* 0x27c */
    unsigned char mIconCount;            /* 0x280 */
} dScEntry_c;
typedef char
    dScEntry_c_mIconCount_must_be_at_0x280[(int)&((dScEntry_c *)0)->mIconCount == 0x280 ? 1 : -1];

void func_ov075_02117ac4(char *r4)
{
  data_0209d45c = data_0209d45c & (~0xe);
  data_0209d454 = data_0209d454 & (~1);
  func_ov075_02116028(data_ov075_0211d71c, 6);
  func_020338b0(0x145, 0xb0, 0x17, -1);
  data_0209d454 = data_0209d454 | 5;
  ((dScEntry_c *)r4)->mIconCount = 0;
  _ZN3G2x18SetBlendBrightnessEPVtts((void *) 0x4000050, 0x1f, (double) (~5), 0);
  ((dScEntry_c *)r4)->mStepDelay = 2;
}
