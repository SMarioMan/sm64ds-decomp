extern int *data_ov007_02104bd8;

/* The screen-fade record at data_ov007_02104bd8; names copied from
 * Ov007Fade in src/unnamed/ov007/func_ov007_020bfcec.c. */
typedef struct Ov007Fade {
    void *transition; /* 0x00 */
    void *model;      /* 0x04 */
    int flags;        /* 0x08 */
    void *onEnd;      /* 0x0c */
    int request;      /* 0x10 */
} Ov007Fade;
typedef char Ov007Fade_size_must_be_0x14[sizeof(Ov007Fade) == 0x14 ? 1 : -1];

void RequestScreenFade(int r0, int r1, int r2) {
    ((Ov007Fade *)data_ov007_02104bd8)->request = r0;
    ((Ov007Fade *)data_ov007_02104bd8)->flags = r1;
    ((Ov007Fade *)data_ov007_02104bd8)->onEnd = (void *)r2;
}
