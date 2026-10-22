#include "types.h"
#pragma opt_common_subs off
extern int func_02054d88(void);
extern void MultiCopy_Int(int *src, int *dst, int len);

extern int data_0209fd00;
extern u8 data_0209fc78;
extern u8 data_0209fc7c;
extern u8 data_0209fcd8;
extern u8 data_0209fc70;
extern u8 data_0209fd20[];
extern u32 data_0209287c[];
extern u32 data_0209fd5c[];
extern u32 data_0209283c[];

/* The current message's 8-byte table entry (data_0209fd00 points into the
 * table at data_0209fd08, idx * 8; Message3.cpp sets it). Message3.cpp reads
 * +4 as the box width in pixels ((width + 7) / 8 tile columns into
 * data_0209fc78) and +6 as the number of text lines: it counts lines against
 * it and sizes the box from (lineCount * 2 + 1) * 8. Here each line is two
 * tile rows. Only the fields these readers touch are spelled out. */
typedef struct MessageEntry {
    s32 textOffset; /* 0x0 */
    u16 width;      /* 0x4 */
    u8 lineCount;   /* 0x6 */
} MessageEntry;

void func_02031428(void)
{
    int cnt;
    int i;
    int rows;
    int j;
    int base;

    base = func_02054d88() + 0x4000;

    cnt = (int)((MessageEntry *)data_0209fd00)->lineCount << 1;
    i = 0;
    if (cnt > 0) {
        do {
            rows = data_0209fc78;
            j = 0;
            if (rows > 0) {
                do {
                    /* scroll the tile up four pixel rows (4 bytes per 4bpp row) */
                    MultiCopy_Int(&((int *)base)[4], (int *)base, 0x10);
                    if (i == (((int)((MessageEntry *)data_0209fd00)->lineCount << 1) - 1)) {
                        ((int *)base)[4] = 0;
                        ((int *)base)[5] = 0;
                        ((int *)base)[6] = 0;
                        ((int *)base)[7] = 0;
                    } else {
                        int rc2 = data_0209fc78;
                        MultiCopy_Int((int *)(base + rc2 * 0x20), &((int *)base)[4], 0x10);
                    }
                    rows = data_0209fc78;
                    j++;
                    base += 0x20;
                } while (j < rows);
            }
            cnt = (int)((MessageEntry *)data_0209fd00)->lineCount << 1;
            i++;
        } while (i < cnt);
    }

    {
        u32 col;
        int rowIdx;
        u8 rem;
        int count;
        int j;
        int blk;
        int wordIdx;
        u8 *inc;
        u32 *dst;
        int i2;
        int i3;

        dst = (u32 *)(func_02054d88() + (((data_0209fc78 * (cnt - 1)) + 0x200) << 5) + 0x10);
        col = data_0209fc7c;
        count = data_0209fcd8;

        j = 0;
        if (count > 0) {
            rowIdx = data_0209fc70;
            inc = data_0209fd20;
            do {
                rem = col & 7;
                blk = col >> 3;
                wordIdx = blk << 3;
                dst[wordIdx] = (data_0209287c[rem] & data_0209fd5c[rowIdx + 0]) | dst[wordIdx];
                *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 4) & ~0ULL)) = (data_0209287c[rem] & data_0209fd5c[rowIdx + 1]) | *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 4) & ~0ULL));
                i2 = rowIdx + 2;
                *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 8) & ~0ULL)) = (data_0209287c[rem] & data_0209fd5c[i2]) | *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 8) & ~0ULL));
                i3 = rowIdx + 3;
                *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 12) & ~0ULL)) = (data_0209287c[rem] & data_0209fd5c[i3]) | *(u32 *)(((u64)(int)((char *)&dst[wordIdx] + 12) & ~0ULL));
                if (rem != 0) {
                    /* the next tile's first four rows (8 words on); dst[wordIdx + 8]
                     * builds 28 bytes longer */
                    (&dst[wordIdx])[8] = data_0209283c[rem] & data_0209fd5c[rowIdx + 0];
                    (&dst[wordIdx])[9] = data_0209283c[rem] & data_0209fd5c[rowIdx + 1];
                    (&dst[wordIdx])[10] = data_0209283c[rem] & data_0209fd5c[i2];
                    (&dst[wordIdx])[11] = data_0209283c[rem] & data_0209fd5c[i3];
                }
                col = (col + *inc) & 0xff;
                rowIdx += 0x10;
                inc++;
                j++;
            } while (j < count);
        }
    }

    data_0209fc70 = data_0209fc70 + 3;
}
