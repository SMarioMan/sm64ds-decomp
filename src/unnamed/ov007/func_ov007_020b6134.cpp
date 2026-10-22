//cpp
#include "Ov007MenuState.h"

extern "C" {
extern void func_ov007_020aec94(int);
extern char* data_ov007_0210342c;

/* data_ov007_0210342c: the overlay's manager; names as in
 * func_ov007_020afc44 and func_ov007_020b5f64, only the slots this file
 * touches. */
struct Ov007Work {
    char pad_00[4];
    Ov007MenuState *states[3]; /* 0x04: func_ov007_020c9388; [1] is the main one */
    char pad_10[0x48];
    /* 0x58/0x5c, medium confidence: this function stores the tapped slot
     * (item id - 0xe for ids 0xe..0x10, func_ov007_020b50e8) in one or the other by menu
     * state; func_ov007_020af84c indexes
     * data_ov007_020ccc20[selectedSlot][targetSlot]; -1 = none */
    int selectedSlot;
    int targetSlot;
};

typedef char Ov007Work_size_must_be_0x60[sizeof(Ov007Work) == 0x60 ? 1 : -1];

/* Slot `arg` was tapped: in main state 0 it hands arg + 3 to
 * func_ov007_020aec94; in 3 it becomes the selected slot, in 2 the target;
 * in 7 the first tap selects, tapping the selection again clears it and any
 * other slot becomes the target; in 9 it selects only when nothing is. */
void func_ov007_020b6134(int arg){
    Ov007Work *G = (Ov007Work *)data_ov007_0210342c;
    switch (G->states[1]->currentState) {
    case 0:
        func_ov007_020aec94(arg + 3);
        break;
    case 3:
        G->selectedSlot = arg;
        break;
    case 2:
        G->targetSlot = arg;
        break;
    case 7: {
        int v = G->selectedSlot;
        if (v == -1) {
            G->selectedSlot = arg;
            return;
        }
        if (arg == v)
            G->selectedSlot = -1;
        else
            G->targetSlot = arg;
    }
    break;
  case 9:
      if (G->selectedSlot == -1)
          G->selectedSlot = arg;
      break;
  }
}
}
