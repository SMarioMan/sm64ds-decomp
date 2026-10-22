#include "types.h"
#include "Ov007Sprite.h"
extern void MultiStore16(u16 val, s16 *dst, int nbytes);
extern void func_ov007_020c43bc(char *a, char *b);
extern void func_ov007_020c4388(char *a, char *b);

extern char *data_ov007_02103460;
extern s16 data_ov007_02103484[];
extern char *data_ov007_0210346c;
extern char *data_ov007_02103470;

/* The window's two Ov007Sprites, both built by func_ov007_020b8714
 * (func_ov007_020c44e4): data_ov007_02103460 draws the frame through the
 * tilemap data_ov007_02103484 (drawFlags 8) that this function lays out,
 * data_ov007_0210346c is the translucent plain quad inside it, 2 px
 * smaller. The externs keep the tree's char * spelling; the typed views
 * are reached through cast macros. */
#define WINDOW_FRAME ((Ov007Sprite *)data_ov007_02103460)
#define WINDOW_FILL ((Ov007Sprite *)data_ov007_0210346c)

void func_ov007_020b88c0(void)
{
    volatile u16 v0;
    volatile u16 v1;
    volatile u16 v2;
    int w;
    int h;
    int botrow;
    int i;
    int r;

    {
        Ov007Sprite *G = WINDOW_FRAME;
        w = G->width >> 3;
        h = G->height >> 3;
    }

    v0 = 0xffff;
    MultiStore16(v0, data_ov007_02103484, (w * h) << 1);
    v1 = 1;
    MultiStore16(v1, data_ov007_02103484, w << 1);
    v2 = 9;
    botrow = (h - 1) * w;
    MultiStore16(v2, data_ov007_02103484 + botrow, w << 1);

    i = 0;
    if (h > 0) {
        r = i;
        do {
            data_ov007_02103484[r] = 4;
            data_ov007_02103484[(int)(((long long)r)) + w - 1] = 6;
            i++;
            r += w;
        } while (i < h);
    }

    data_ov007_02103484[0] = 0;
    data_ov007_02103484[w - 1] = 2;
    data_ov007_02103484[botrow] = 8;
    data_ov007_02103484[(unsigned int)w * h - 1] = 0xa;

    WINDOW_FILL->screenX = WINDOW_FRAME->screenX;
    WINDOW_FILL->screenY = WINDOW_FRAME->screenY;
    WINDOW_FILL->width = (s16)(WINDOW_FRAME->width - 2);
    WINDOW_FILL->height = (s16)(WINDOW_FRAME->height - 2);

    func_ov007_020c43bc(data_ov007_0210346c, data_ov007_02103470);
    func_ov007_020c4388(data_ov007_0210346c, data_ov007_02103470);
    func_ov007_020c43bc(data_ov007_02103460, data_ov007_02103470);
    func_ov007_020c4388(data_ov007_02103460, data_ov007_02103470);
}
