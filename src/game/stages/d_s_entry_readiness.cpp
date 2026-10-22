//cpp
/* leftovers:
 * - defer_codegen off stays, and the file stays in ROM order, the
 *   same form as d_s_entry.cpp and d_s_entry_methods.cpp. Reordering
 *   moves the run.
 * - Readiness slice of dScEntry_c's unit: StartMatch, the 02116ce4
 *   player-loop helper, ArePlayersReady, CheckMenuConfirm. Left
 *   neighbor func_ov075_02116c38 (0x02116c38..0x02116c8c) and right
 *   neighbor func_ov075_02116e00 (0x02116e00..0x02116e44) stay in
 *   their own sources; this claim is exactly 0x02116c8c..0x02116e00.
 * - func_ov075_02116ce4 stays a free extern "C" helper. Its scene
 *   parameter is unused: the body only reads the player-active flags
 *   and calls func_020201f0 per active player. The sole caller,
 *   func_ov075_02117e84 at 0x02117f2c, passes its scene in r0, so
 *   dropping the parameter changes the caller. Same precedent as the
 *   free func_ov075_* helpers in d_s_entry_methods.cpp.
 * - The destructor, the key function, is in d_s_entry.cpp. This file
 *   defines no virtual the class declares first, so it emits no
 *   dScEntry_c vtable or typeinfo.
 * - Local externs keep the shards' spellings (LoadLevelNoReturn's
 *   first param, the u8/u16 data handles, func_020201f0/func_02020364
 *   return types); the decl-agreement rows move onto this file.
 *
 * dScEntry_c readiness: match loading, per-player predicate loop,
 * ready polling, menu-confirm input. ov075 .text
 * 0x02116c8c..0x02116e00.
 */
#pragma defer_codegen off

#include "dScEntry_c.h"
#include "Sound.h"

// @symbol _ZN10dScEntry_c10StartMatchEv
extern "C" {
void PrepareVsMode(void);
void LoadLevelNoReturn(int levelID, u32 entranceID, u32 mode, u32 arg3);
extern u8 data_0209b2e4;
extern s8 data_ov075_0211c6ec[];
extern u8 data_02092778;
}
void dScEntry_c::StartMatch() {
    PrepareVsMode();
    u8 course = data_0209b2e4;
    LoadLevelNoReturn(data_ov075_0211c6ec[course], 0, 2, 0);
    Sound::StopLoadedMusic_Layer1(0x3c);
    data_02092778 = 1;
}

/* The Entry caller supplies its scene in r0; this helper only reads player flags. */
// @symbol func_ov075_02116ce4
extern "C" {
extern unsigned char data_0209fc5c[];
extern int func_020201f0(int);
int func_ov075_02116ce4(void *scene) {
    int i;
    for (i = 0; i < 4; i++) {
        if (data_0209fc5c[i]) {
            int r = func_020201f0(i);
            if (!r)
                return 0;
        }
    }
    return 1;
}
}

// @symbol _ZN10dScEntry_c15ArePlayersReadyEv
extern "C" {
extern u8 data_0209fc5c[];
u8 func_02020364(int player);
}
int dScEntry_c::ArePlayersReady() {
    int player = 0;
    u8 *active = data_0209fc5c;
    for (;;) {
        if (*active != 0) {
            int ready = func_02020364(player);
            if (ready == 0)
                return 0;
        }
        ++player;
        ++active;
        if (player >= 4)
            break;
    }
    return 1;
}

// @symbol _ZN10dScEntry_c16CheckMenuConfirmEi
extern "C" {
int func_0203da9c();
u32 func_02012790(u32 sound);
extern u16 data_020a0e5a[];
}

int dScEntry_c::CheckMenuConfirm(int player) {
    u16 pressed;
    if (player >= 0)
        pressed = data_020a0e5a[player * 2];
    else
        pressed = data_020a0e5a[func_0203da9c() * 2];
    if (pressed != 0) {
        if (pressed & 0xc)
            return 1;
        func_02012790(0xe);
    }
    return 0;
}
