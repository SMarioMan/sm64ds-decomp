typedef struct ARMMathState { int pad[7]; } ARMMathState;

extern void ARMMathSaveState(ARMMathState* s);
extern void ARMMathLoadState(ARMMathState* s);
extern void func_ov007_020bf690(void);
extern void func_ov007_020bd4e8(void);
extern void func_ov007_020bd648(int mode);
extern void func_ov007_020b72a0(void);
extern char* data_ov007_02103430;
extern char* data_ov007_0210342c;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020b0358, only the slots this file touches. */
typedef struct Ov007Work {
    char pad_00[0x18];
    /* 0x18: while set, a display capture is started here
     * (func_ov007_020bd4e8 writes DISPCAPCNT) and the flag cleared */
    int pendingCapture;
    int pendingBgMode; /* 0x1c: handed to func_ov007_020bd648, then cleared */
} Ov007Work;

typedef char Ov007Work_size_must_be_0x20[sizeof(Ov007Work) == 0x20 ? 1 : -1];

/* The extern keeps the tree's char * spelling; the typed view is reached
 * through a cast macro. */
#define WORK ((Ov007Work *)data_ov007_0210342c)

int func_ov007_020b6eb4(void) {
    ARMMathState s;
    if (data_ov007_02103430 != 0) {
        ARMMathSaveState(&s);
        func_ov007_020bf690();
        if (WORK->pendingCapture != 0) {
            func_ov007_020bd4e8();
            WORK->pendingCapture = 0;
        }
        if (WORK->pendingBgMode != 0) {
            func_ov007_020bd648(WORK->pendingBgMode);
            WORK->pendingBgMode = 0;
        }
        func_ov007_020b72a0();
        ARMMathLoadState(&s);
    }
    return 1;
}
