//cpp
/* leftovers:
 * - defer_codegen off stays, and the file stays in ROM order, the
 *   same form as d_s_entry.cpp below the hole. Reordering moves the
 *   run.
 * - This is the upper part of dScEntry_c's translation unit. The
 *   lower part is d_s_entry.cpp (0x02115ab8..0x021165b0). The hole
 *   that still separates them is 0x021165b0..0x02118a84: 31 functions
 *   still in separate sources, including the d_s_entry_readiness.cpp
 *   slice (0x02116c8c..0x02116e00). No other class's
 *   code reaches them. They are called from InitResources, Behavior
 *   or one another, or reached through the step tables that
 *   __sinit_ov075_0211bb00 copies into .bss. That initializer also
 *   builds the graphCallback_c, so it is this unit's. 31 of those
 *   helpers remain. A delinks entry is one contiguous .text claim,
 *   so the two parts join only once that remaining hole is folded.
 * - The transition helpers use native Step member-pointer copies.
 * - The destructor, the key function, is in d_s_entry.cpp. This file
 *   defines no virtual the class declares first, so it emits no
 *   dScEntry_c vtable or typeinfo.
 * - OamAnimation() and icon_c() are written out of line. The
 *   cartridge's copies close the run after the RESULT factory, the
 *   place the inline copies a factory forces would land. Inline
 *   copies are not emitted here: the factories name the two
 *   constructors by their linker names, so nothing in C++ uses them.
 * - The factory keeps its hand-built construction. A `new dScEntry_c'
 *   would need the class constructor, which is not reconstructed.
 *   Its __cxa_vec_ctor calls take the icon_c and OamAnimation
 *   structors by address, which C++ cannot spell.
 * - The header names the entry object and shared step workspace. The
 *   extern "C" step callbacks take the scene as a dScEntry_c pointer and
 *   reach it through those members. The transition helpers use the
 *   typed pending StepSet pointer at 0x6c.
 * - InitResources keeps its `int isResult = (actorID == 7)' flag locals.
 *   Folding the first one into its condition rewrites the function
 *   (999 words, measured).
 * - The helpers it calls stay func_ov075_* and the arm9 globals keep
 *   their linker names. Naming belongs with recovered members.
 *
 * dScEntry_c, the course-entry / results scene. ov075 .text
 * 0x02118a84..0x0211a854: the course-select and match-loading steps,
 * the player-select and sync steps, the
 * waiting-text render, the helpers through SetSteps, the
 * six scene methods, the RESULT factory, then the OamAnimation and
 * icon_c constructors. The ENTRY factory at 0x0211a854 is not in
 * this file. It sits past the constructor tail that closes this
 * run. The code after it is reached from dEntObj_c (d_ent_obj.cpp)
 * and through tables __sinit_ov075_0211c51c reads, not from this
 * class.
 */
#pragma defer_codegen off

#include "types.h"
#include "PlayerInput.h"
#include "Sound.h"
#include "decl_common.h"
#include "dScEntry_c.h"
#include "dFdBrightness_c.h"
#include "AsyncJob.h"
#include "Heap.h"

/* The Nitro SDK's sub-engine palette loader. No header in the tree
 * declares the namespace yet; d_s_star_sel_methods.cpp spells it the
 * same way. */
namespace GXS {
void LoadBGPltt(const void *, unsigned int, unsigned int);
}

extern "C" {
void func_020308b4(void *self);
void func_020551f0(void *s, int v);
extern int data_0209fc68;

void Enable3dEngines(void);
void func_0200f2cc(void);
int func_0203d9b4(void);
void LoadTextNarcs(void);
int LoadArchive(int idx);
void func_0200f220(void);
int LoadFile(int handle);
void SetBg0Offset(int a, int b);
void SetBg2Offset(int a, int b);
void SetBg3Offset(int a, int b);
void SetSubBg0Offset(int a, int b);
void SetSubBg2Offset(int a, int b);
void SetSubBg3Offset(int a, int b);
void LoadFont3D(void);
int func_ov075_02116ad4(void *arg);
int func_0203da3c(void);
void UnloadArchive(int i);
void func_02030aa4(int arg);
int func_0203da9c(void);
void func_02020028(int a, int b);
void func_ov075_02116818(char *c);
void func_ov075_0211601c(char *c, int a, int b);
}

extern void *data_0209d4a8;
extern u8 data_0209d45c;
extern u8 data_0209d454;
extern u8 data_0209f4ae[];
extern s32 data_0208ee44;

/* The scene manager Behavior polls through its slot 5. */
extern "C" dFdBrightness_c *data_0209f5bc;

#include "dEntObj_c.h"
#include "OAM.h"
#include "OamAttr.h"
#include "G2x.h"

namespace G2S {
u32 GetBG2ScrPtr();
u32 GetBG3ScrPtr();
}

/* The RESULT factory retains its two-word aggregate-copy schedule. */
struct P2Copy {
    int words[2];
};

extern "C" {
int func_0203d974(void);
u8 func_02020168(void);
void func_02020304(void);
void func_020200e0(void);
void func_02020334(void);
void func_02020124(void);
int func_0203d890(void);
u32 LoadCompressedFileAt(u16, void *);
u32 func_02012790(u32);
int Sound_PlayIfNotActive(int, int, int, int);
void func_ov075_02116030(void *, int);
void func_ov075_02116028(int *, int);
void func_020338b0(int, int, short, int);
void func_02033464(int, int, int);
void func_ov075_02115e8c(char *, int, int, short, short);
void func_02034414(unsigned short);
void func_02030a38(void);
void func_02030a78(void);
void func_02030a6c(void);
void func_020337ec(void);
int TouchArea_Update(char *, int);
void func_ov001_020ab41c(void *);
void func_ov001_020ab3f0(void *);

extern u8 data_0208f274;
extern OamAttr *data_0208a0f8[];
extern s16 data_02082214[];
extern dScEntry_c::StepSet data_ov075_0211d918;
// Behavior slot of the player-sync step set, at data_ov075_0211d918 + 8.
extern dScEntry_c::Step data_ov075_0211d920;
extern dScEntry_c::StepSet data_ov075_0211d900;
extern dScEntry_c::StepSet data_ov075_0211d8b8;
extern OamAttr *data_ov075_0211c968[];
extern u8 data_0209fc58;
extern u8 data_0209fc5c[];
extern u8 data_0209fc5d[];
extern dScEntry_c::StepSet data_ov075_0211d8a0;
extern dScEntry_c::StepSet data_ov075_0211d8d0;

/* local extern: OAM.h excludes this Fix12-by-value overload. */
OamAttr *_ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi(int, OamAttr *, int, int, int, int, int, int);
}

/* Course-select and match-loading steps, directly below the player-select
 * run in ROM order. The declarations below are the union of the six shards'
 * extern blocks, minus names this file already declares. */
extern "C" {
int func_0203d8fc(void);
int func_0201a1bc(void);
void func_0203d930(void);
extern unsigned char EntryCourseLoadStarted;
void func_0202deac(int level);
void func_0203d918();
extern u8 data_0208a0e0;
u8 func_020202dc(void);
u8 func_020200b8(void);
void func_02020078(u32 flags);
void func_0202029c(u32 idx);
extern u16 data_020a0e5a[];
extern s8 data_ov075_0211c6ec[];
extern u8 data_0209f2d8;
extern u8 data_0209b2e4;
}

extern dScEntry_c::StepSet data_ov075_0211d798;
extern dScEntry_c::StepSet data_ov075_0211d7f8;
extern struct OamAttr data_ov075_0211cba4[];

// local extern: the Fix12-by-value overload retains its measured scalar ABI bridge.
extern "C" void OamRender10_d_s_entry_methods(int sub, struct OamAttr *data, s32 x, s32 y,
                                              s32 palette, s32 priority, s32 scaleX, s32 scaleY,
                                              s32 rotation, s32 mode);

// @symbol _ZN10dScEntry_c18UpdateMatchLoadingEv
void dScEntry_c::UpdateMatchLoading() {
    if (mSawLoadSignal == 0) {
        if (func_0203d8fc() != 0)
            mSawLoadSignal = 1;
    }
    if (mStepPhase == MATCH_LOAD_RESOURCES) {
        if (data_0209fc68 != 0) {
            if (EntryCourseLoadStarted == 0) {
                func_0201a244(&dScEntry_c::LoadCourseResources, data_0209b2e4, 0xf, 0, 0x1000);
                EntryCourseLoadStarted = 1;
            }
            if (EntryCourseLoadStarted != 0 && func_0201a1bc() != 0) {
                mStepPhase = MATCH_LOAD_WAIT_FOR_SIGNAL_CLEAR;
                EntryCourseLoadStarted = 0;
                func_0203d930();
            }
        } else {
            mStepPhase = MATCH_LOAD_READY;
        }
    }
    if (mStepPhase == MATCH_LOAD_WAIT_FOR_SIGNAL_CLEAR && mSawLoadSignal != 0) {
        if (func_0203d8fc() == 0)
            mStepPhase = MATCH_LOAD_READY;
    }
    if (mStepDelay > 0) {
        mStepDelay -= data_0208ee44;
    }
    if (mStepPhase < MATCH_LOAD_READY)
        return;
    if (mStepDelay > 0)
        return;
    StartMatch();
    mBehaviorStep = 0;
}

// @symbol _ZN10dScEntry_c19LoadCourseResourcesEi
void dScEntry_c::LoadCourseResources(int course) {
    mHeap::Heap_t *previousHeap = static_cast<mHeap::Heap_t *>(data_020a0eac)->SetDefault();
    LoadArchive(7);
    int selectedArchive = course + 2;
    unsigned int archive;
    for (archive = 2; archive <= 5; ++archive) {
        if (archive == (unsigned int)selectedArchive)
            continue;
        UnloadArchive(archive);
    }
    LoadArchive(selectedArchive);
    previousHeap->SetDefault();
    data_0209f2d8 = 1;
    func_0202deac(data_ov075_0211c6ec[course]);
}

// @symbol _ZN10dScEntry_c17EnterMatchLoadingEv
void dScEntry_c::EnterMatchLoading() {
    mEntObj->func_ov075_02114fa8();
    mStepDelay = 240;
    mStepPhase = MATCH_LOAD_RESOURCES;
    mSawLoadSignal = 0;
    if (data_0209fc68 != 0)
        data_0208a0e0 = 4;
    func_0203d918();
}

// @symbol _ZN10dScEntry_c23RenderCourseSelectTitleEv
void dScEntry_c::RenderCourseSelectTitle() {
    OAM::Render(0, data_ov075_0211cba4, 0x80, 0x20, -1, -1, 0x1000, 0x1000, 0, -1);
}

// @symbol _ZN10dScEntry_c18UpdateCourseSelectEv
void dScEntry_c::UpdateCourseSelect() {
    if (func_0203d974() && func_020202dc() != data_0209b2e4) {
        data_0209b2e4 = func_020202dc();
    }
    if (func_02020168()) {
        u8 action;
        func_02020304();
        func_020200e0();
        action = func_020200b8();
        if (action == 0) {
            int index;
            func_ov001_020ab3f0(&mIcons[data_0209b2e4]);
            mIcons[data_0209b2e4].mReady = 0;
            index = 0;
            for (; index < 4; index++) {
                if (index != data_0209b2e4)
                    mIcons[index].mOn = 0;
            }
            SetSteps(&EntryMatchLoadingSteps);
            func_02012790(0xa0);
            func_02012790(0x128);
            return;
        }
        if (action == 1) {
            SetSteps(&data_ov075_0211d798);
            func_02012790(0x9e);
            return;
        }
        SetSteps(&data_ov075_0211d7f8);
        func_02012790(0x9f);
        return;
    }
    if (func_0203d9b4()) {
        if (ArePlayersReady()) {
            bool touched;
            int index;
            touched = false;
            index = 0;
            icon_c *icon = mIcons;
            for (; index < 4; index++) {
                if (TouchArea_Update((char *)icon, 0)) {
                    touched = true;
                    data_0209b2e4 = index;
                    break;
                }
                ++icon;
            }
            if (touched) {
                func_02020078(0);
                func_02020124();
            } else {
                if (data_020a0e5a[gActivePlayerSlot * 2] & 4) {
                    func_02020078(1);
                    func_02020124();
                } else if (data_020a0e5a[gActivePlayerSlot * 2] & 8) {
                    func_02020078(2);
                    func_02020124();
                }
            }
            func_0202029c(data_0209b2e4);
        }
    }
    *(u16 *)0x4000050 = 0;
    if (data_020a0e5a[func_0203da9c() * 2] & ~0xc) {
        func_02012790(0xe);
    }
}

// @symbol _ZN10dScEntry_c17EnterCourseSelectEv
void dScEntry_c::EnterCourseSelect() {
    int index;
    int x;
    icon_c *icon;

    data_0209d45c &= ~4;
    data_0209d454 &= ~5;
    func_ov075_02116028((int *)&data_ov075_0211d71c, 1);
    func_ov075_02116030((void *)&data_ov075_0211d71c, LoadFile(0x8409));
    LoadCompressedFileAt(0x8407, (void *)G2S::GetBG3ScrPtr());

    if (func_0203d9b4() != 0)
        func_020338b0(0x205, 0xb0, 0x21, -1);
    else
        func_020338b0(0x225, 0xb0, 0x1d, -1);

    data_0209d454 |= 5;

    icon = mIcons;
    index = 0;
    x = 0x20;
    for (; index < 4; index++) {
        func_ov075_02115e8c((char *)icon, 7, index, (short)x, 0x48);
        mIcons[index].mOn = 1;
        mIcons[index].mPressTime = 8;
        x += 0x40;
        ++icon;
    }

    data_0209b2e4 = 4;
    func_ov075_02115e8c((char *)&mIcons[4], 0xd, 4, 0x80, -0x14);
    mIconCount = 5;
    func_02020334();
    func_020200e0();
}

// @symbol _ZN10dScEntry_c23UpdatePlayerSelectIntroEv
void dScEntry_c::UpdatePlayerSelectIntro() {
    if (func_0203d974()) {
        if (!mPlayerSelectReady) {
            mEntObj->func_ov075_02115134();
            if (mEntObj->func_ov075_02115098(func_0203da9c()))
                mPlayerSelectReady = 1;
        }
        if (mPlayerSelectReady)
            mStepPhase = 1;
    }

    if (func_02020168()) {
        func_02020304();
        func_020200e0();
        ChangeStepsAfterDelay(&EntryCourseSelectSteps, 5);
        return;
    }

    if (mStepDelay > 0) {
        mStepDelay -= data_0208ee44;
        return;
    }
    if (!mStepPhase)
        return;
    func_02020334();
    if (!func_0203d9b4())
        return;
    if (!ArePlayersReady())
        return;
    func_02020124();
}

// @symbol _ZN10dScEntry_c22EnterPlayerSelectIntroEv
void dScEntry_c::EnterPlayerSelectIntro() {
    int row;
    int col;
    u16 *tiles;
    u32 palette;
    data_0209d454 &= ~5;
    if (func_0200f0bc() == 0)
        LoadCompressedFileAt(0x840a, reinterpret_cast<void *>(G2S::GetBG2ScrPtr()));
    else
        LoadCompressedFileAt(0x980c, reinterpret_cast<void *>(G2S::GetBG2ScrPtr()));
    LoadCompressedFileAt(0x840b, reinterpret_cast<void *>(G2S::GetBG3ScrPtr()));

    // Color the 9-by-10 tile panel for this player's wireless station.
    tiles = reinterpret_cast<u16 *>(G2S::GetBG2ScrPtr()) + 11 * 32 + 11;
    palette = (static_cast<u32>(func_0203da9c() + 10) << 28) >> 16;
    for (row = 0; row < 10; ++row) {
        for (col = 0; col < 9; ++col)
            tiles[col] = palette | (tiles[col] & 0xfff);
        tiles += 32;
    }
    data_0209d454 |= 4;
    mIconCount = 0;
    mStepDelay = 180;
    if (func_0203d974()) {
        mStepPhase = 0;
        mPlayerSelectReady = 0;
        mWaiting.syncTicks = 0;
    } else {
        mStepPhase = 1;
    }
    func_02012790(0x122);
}

// @symbol _ZN10dScEntry_c16UpdatePlayerSyncEv
void dScEntry_c::UpdatePlayerSync() {
    mSoundHandle = Sound_PlayIfNotActive(mSoundHandle, 2, 0x11d, 0);

    switch (mStepPhase) {
    case 0: {
        u8 activePlayers = data_0209fc50;
        int sessionPlayers = func_0203d890();
        if (activePlayers == sessionPlayers) {
            func_020308b4((void *)sessionPlayers);
            ++mStepPhase;
        } else {
            ++mWaiting.playerWaitTicks;
            if (mWaiting.playerWaitTicks >= 900)
                data_0209fc54 = 1;
        }
        break;
    }
    case 1:
        if (func_020308a8())
            ++mStepPhase;
        break;
    case 2: {
        int hostReady = func_0203d8fc();
        if (hostReady) {
            func_020308b4((void *)hostReady);
            ++mStepPhase;
        }
        break;
    }
    case 3:
        if (func_020308a8()) {
            ChangeStepsWithFade(&EntryPlayerSelectIntroSteps);
            u8 observedPlayers = data_0208f274;
            int sessionPlayers = func_0203d890();
            if (observedPlayers == sessionPlayers) {
                func_02012790(0x11f);
                return;
            }
        }
        break;
    }

    if (mStepPhase < 1)
        return;
    ++mWaiting.syncTicks;
    if (mWaiting.syncTicks >= 2700)
        data_0209fc54 = 1;
}

// @symbol _ZN10dScEntry_c15EnterPlayerSyncEv
void dScEntry_c::EnterPlayerSync() {
    // Download-play clients and non-host stations install the waiting screen.
    if (func_0203d974()) {
        data_0209d454 &= ~5;
        int screen = LoadFile(0x8409);
        func_ov075_02116030((void *)&data_ov075_0211d71c, screen);
        func_020338b0(0x225, 0xb0, 0x1d, -1);
        data_0209d454 |= 5;
        mIconCount = 0;
        mWaiting.wavePhase = 0;
        mWaiting.waveDelay = 120;
    }
    mStepPhase = 0;
    mWaiting.playerWaitTicks = 0;
    mWaiting.syncTicks = 0;
}

// @symbol _ZN10dScEntry_c17RenderWaitingTextEv
void dScEntry_c::RenderWaitingText() {
    OamAttr *glyph = data_0208a0f8[func_0200f0bc()];

    if (mWaiting.waveDelay <= 0) {
        int phase;
        bool waving;

        phase = mWaiting.wavePhase;
        waving = false;
        do {
            int y;
            if (phase >= 0 && phase < 0x10000) {
                waving = true;
                // The intermediate narrowing preserves the retail ARM shifts.
                y = (data_02082214[2 * ((u16)(s16)(u16)phase >> 4)] >> 10) + 96;
            } else {
                y = 96;
            }
            _ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi(true, glyph, 128, y, -1, -1, 0x1000, 0);
            if (glyph->attr3 == 0xffff)
                break;
            ++glyph;
            phase -= 0x2000;
        } while (true);

        mWaiting.wavePhase += 0x800;
        if (!waving)
            mWaiting.waveDelay = 120;
    } else {
        OAM::RenderSub(glyph, 128, 96);
        mWaiting.waveDelay -= data_0208ee44;
        mWaiting.wavePhase = 0;
    }
}

// @symbol func_ov075_02119640
extern "C" void func_ov075_02119640(dScEntry_c *self) {
    self->mSoundHandle = Sound_PlayIfNotActive(self->mSoundHandle, 2, 0x11d, 0);
    if (self->mStepPhase == 0) {
        self->mEntObj->func_ov075_02115134();
        self->mStepPhase = (unsigned char)self->mEntObj->func_ov075_02115098(func_0203da9c());
    }
    if (func_0203da3c() != 0)
        return;
    LoadTextNarcs();
    LoadArchive(0);
    LoadArchive(1);
    func_02030aa4(1);
    self->SetSteps(&data_ov075_0211d918);
}

// @symbol func_ov075_021196d0
extern "C" void func_ov075_021196d0(dScEntry_c *self) {
    self->mEntObj->func_ov075_02115134();
    data_0209d454 &= ~5;
    func_ov075_02116030((void *)&data_ov075_0211d71c, (int)data_0209b2e8);
    data_0209b2e8 = 0;
    func_020338b0(0x225, 0xb0, 0x1d, -1);
    data_0209d454 |= 5;
    self->mIconCount = 0;
    self->mWaiting.wavePhase = 0;
    self->mWaiting.waveDelay = 0x78;
    func_02012790(0x11e);
    self->mStepPhase = self->mEntObj->func_ov075_02115098(func_0203da9c());
}

// @symbol func_ov075_0211977c
extern "C" void func_ov075_0211977c(dScEntry_c *self) {
    int r = func_0203da3c();
    if (r != 0)
        return;
    Deallocate(data_0209b2e8);
    data_0209b2e8 = 0;
    LoadTextNarcs();
    LoadArchive(0);
    LoadArchive(1);
    self->SetSteps(&EntryCourseSelectSteps);
}

// @symbol func_ov075_021197dc
extern "C" void func_ov075_021197dc(dScEntry_c *self) {
    self->mIconCount = 0;
}

// @symbol func_ov075_021197e8
extern "C" void func_ov075_021197e8(dScEntry_c *self) {
    if (self->mStepPhase == 0)
        self->mStepPhase = self->mEntObj->func_ov075_02115098(func_0203da9c()) != 0;
    if (self->mStepPhase == 0)
        return;
    if (TouchArea_Update((char *)&self->mIcons[0], -1) != 0 ||
        (self->CheckMenuConfirm(-1) != 0 && self->mSelectedIcon == 0)) {
        self->mIcons[1].mOn = 0;
        func_ov001_020ab41c(&self->mIcons[0]);
        SetNumPlayers(1);
        self->ChangeStepsAfterDelay(&data_ov075_0211d900, 0x14);
        func_02012790(0x118);
        return;
    }
    if (TouchArea_Update((char *)&self->mIcons[1], -1) == 0) {
        if (self->CheckMenuConfirm(-1) == 0)
            return;
        if (self->mSelectedIcon != 1)
            return;
    }
    self->mIcons[0].mOn = 0;
    func_ov001_020ab41c(&self->mIcons[1]);
    self->ChangeStepsAfterDelay(&data_ov075_0211d8b8, 0x14);
    self->mEntObj->func_ov075_0211505c();
    func_02012790(0x119);
}

// @symbol func_ov075_02119918
extern "C" void func_ov075_02119918(dScEntry_c *self) {
    data_0209d454 = data_0209d454 & ~1;
    func_ov075_02116028((int *)&data_ov075_0211d71c, 2);
    func_02034414(0x11);

    data_0209d454 = data_0209d454 | 5;
    self->mSelectedIcon = 1;
    func_ov075_02115e8c((char *)&self->mIcons[0], 8, 0, 0x50, 0xa8);
    func_ov075_02115e8c((char *)&self->mIcons[1], 8, 0, 0xb0, 0xa8);

    self->mIconCount = 2;
    func_02030a38();
    {
        int r = func_0203da9c();
        self->mStepPhase = self->mEntObj->func_ov075_02115098(r) != 0;
    }
}

struct SinePair {
    short a, b;
};

// @symbol func_ov075_021199d8
extern "C" void func_ov075_021199d8(dScEntry_c *self) {
    OamAttr *attr;

    attr = data_ov075_0211c968[func_0200f0bc()];

    if (self->mWaiting.waveDelay <= 0) {
        int ang;
        int flag;
        int fallback = 0x1c;
        int zero = 0;
        int one = 1;
        int minus = -1;
        int fx = 0x1000;
        int x = 0x80;

        ang = self->mWaiting.wavePhase;
        flag = 0;

        do {
            int y;

            if (ang >= 0 && ang < 0x10000) {
                flag = one;
                y = (((SinePair *)data_02082214)[(unsigned short)(short)(unsigned short)ang >> 4]
                         .a >>
                     0xa) +
                    fallback;
            } else {
                y = fallback;
            }

            _ZN3OAM6RenderEbP7OamAttriiii5Fix12IiEi(one, attr, x, y, minus, minus, fx, zero);

            if (attr->attr3 == 0xffff)
                break;

            attr += 1;
            ang -= 0x2000;
        } while (1);

        self->mWaiting.wavePhase += 0x800;

        if (flag == zero)
            self->mWaiting.waveDelay = 0x78;
    } else {
        OAM::RenderSub(attr, 0x80, 0x1c);
        self->mWaiting.waveDelay -= data_0208ee44;
        self->mWaiting.wavePhase = 0;
    }
}

// @symbol func_ov075_02119b34
extern "C" void func_ov075_02119b34(dScEntry_c *self) {
    int r5 = func_0203da9c();
    int r4 = data_0209fc50;
    for (int i = 1; i < 4; i++) {
        func_02033464((unsigned char)i, (signed char)i, 0);
    }
    self->mEntObj->func_ov075_02115134();
    self->mSoundHandle = Sound_PlayIfNotActive(self->mSoundHandle, 2, 0x11c, 0);
    if (data_0209fc5c[r5] == 0)
        return;
    if (r4 < 4) {
        if (TouchArea_Update((char *)&self->mIcons[0], 0) == 0) {
            if (self->CheckMenuConfirm(0) == 0)
                return;
        }
    }
    func_ov001_020ab3f0(&self->mIcons[0]);
    if (r4 <= 1) {
        self->ChangeStepsAfterDelay(&data_ov075_0211d8a0, 0x14);
    } else {
        func_02030a6c();
        self->ChangeStepsAfterDelay(&data_ov075_0211d8d0, 0x14);
    }
    func_02012790(0x117);
}

// @symbol func_ov075_02119c38
extern "C" void func_ov075_02119c38(dScEntry_c *self) {
    data_0209d454 &= ~1;
    func_ov075_02116028((int *)&data_ov075_0211d71c, 1);
    func_020337ec();
    data_0209d454 |= 5;
    func_ov075_02115e8c((char *)&self->mIcons[0], 0xa, 0, 0x80, 0xa8);
    self->mIconCount = 1;
    self->mStepPhase = 0;
    self->mWaiting.wavePhase = 0;
    self->mWaiting.waveDelay = 0x78;
}

// @symbol _ZN10dScEntry_c17UpdateStepFadeOutEv
void dScEntry_c::UpdateStepFadeOut() {
    ++mFadeTick;
    if (mFadeTick & 1)
        return;
    ++mFadeBrightness;
    func_020551f0((void *)0x4001050, mFadeBrightness);
    if (mFadeBrightness < 16)
        return;
    mIsFading = 1;
    SetSteps(mPendingSteps);
}

// @symbol _ZN10dScEntry_c16EnterStepFadeOutEv
void dScEntry_c::EnterStepFadeOut() {
    *(volatile u16 *)0x4000050 = 0;
    G2x::SetBlendBrightness((volatile u16 *)0x4001050, 0x1d, 0);
    mFadeBrightness = 0;
    mFadeTick = 0;
}

// @symbol _ZN10dScEntry_c15UpdateStepDelayEv
void dScEntry_c::UpdateStepDelay() {
    mStepDelay -= data_0208ee44;
    if (mStepDelay > 0)
        return;
    SetSteps(mPendingSteps);
}

/* State 6 is written by the wireless teardown path. Keep the materialized
 * predicate: flattening it changes the retail branch sequence. */
static inline int HasConnectionError() {
    return data_0209fc68 == 6;
}

// @symbol _ZN10dScEntry_c22HandlePlayerDisconnectEPKNS_7StepSetE
void dScEntry_c::HandlePlayerDisconnect(const StepSet *resumeSteps) {
    u8 activePeerMask;
    u8 *peerActive;
    int player;
    u8 disconnectFlags;

    data_0209d454 = data_0209d454 & ~0x11;
    activePeerMask = 0;
    peerActive = data_0209fc5d;
    for (player = 1; player < 4; player++) {
        if (peerActive[0])
            activePeerMask = activePeerMask | (1 << player);
        peerActive++;
    }
    disconnectFlags = data_0209fc58;
    if (HasConnectionError()) {
        func_ov075_02116028((int *)&data_ov075_0211d71c, 5);
        func_02030a78();
        {
            if ((disconnectFlags & 0x30) != 0 || mBehaviorStep == data_ov075_0211d920) {
                if (GetOwnerLanguage() == 3)
                    func_020338b0(0xa5, 0xb0, 0x15, -1);
                else
                    func_020338b0(0xc5, 0xb0, 0x15, -1);
            } else {
                func_020338b0(0xc5, 0xb0, 0x13, -1);
            }
        }
        mBehaviorStep = 0;
        data_0209d45c = data_0209d45c & ~mDisconnectHideMask;
        if (mDisconnectHideMask)
            mRenderStep = 0;
        G2x::SetBlendBrightness((volatile u16 *)0x4000050, 0x1f, -6);
        *(volatile u16 *)0x4001050 = 0;
        Sound::StopLoadedMusic_Layer1(4);
        func_02012790(0x123);
        mEntObj->mSuspended = 1;
    } else {
        func_ov075_02116028((int *)&data_ov075_0211d71c, 6);
        if ((func_0203d974() && data_0209fc5c[0] == 0) ||
            (func_0203d9b4() && activePeerMask == 0)) {
            if (func_0203d974())
                func_020338b0(0x125, 0xb0, 0x1b, 0);
            else
                func_020338b0(0x125, 0xb0, 0x1a, -1);
            func_02030a78();
            ChangeStepsAfterDelay(reinterpret_cast<const StepSet *>(&data_ov075_0211d930), 0xb4);
            data_0209d45c = data_0209d45c & ~mDisconnectHideMask;
            if (mDisconnectHideMask)
                mRenderStep = 0;
            G2x::SetBlendBrightness((volatile u16 *)0x4000050, 0x1f, -6);
            func_02012790(0x12a);
        } else {
            for (player = 0; player < 4; player++) {
                int bit = 1 << player;
                if (disconnectFlags & bit) {
                    func_020338b0(0x125, 0xb0, 0x1c, (s8)(u8)player);
                    data_0209fc58 = data_0209fc58 & ~bit;
                    ChangeStepsAfterDelay(resumeSteps, 0x78);
                    func_02012790(0x12a);
                    break;
                }
            }
        }
    }
    data_0209d454 = data_0209d454 | 5;
    mIconCount = 0;
}

// @symbol _ZN10dScEntry_c19ChangeStepsWithFadeEPKNS_7StepSetE
void dScEntry_c::ChangeStepsWithFade(const StepSet *steps) {
    mPendingSteps = steps;
    Step render = mRenderStep;
    SetSteps(&EntryFadeOutSteps);
    mRenderStep = render;
}

// @symbol _ZN10dScEntry_c21ChangeStepsAfterDelayEPKNS_7StepSetEi
void dScEntry_c::ChangeStepsAfterDelay(const StepSet *steps, s32 delay) {
    mPendingSteps = steps;
    mStepDelay = delay;
    Step render = mRenderStep;
    SetSteps(&EntryDelaySteps);
    mRenderStep = render;
}

// @symbol _ZN10dScEntry_c8SetStepsEPKNS_7StepSetE
void dScEntry_c::SetSteps(const StepSet *steps) {
    mEnterStep = steps->enter;
    mBehaviorStep = steps->behavior;
    mRenderStep = steps->render;
    if (mEnterStep != 0)
        (this->*mEnterStep)();
}

/* Slot 3. Releases the level-entry scratch buffer, unregisters the
 * graph callback, drops the voice group and clears the shared
 * model-data array. */
// @symbol _ZN10dScEntry_c16CleanupResourcesEv
s32 dScEntry_c::CleanupResources() {
    func_020308b4(this);
    if (data_0209b2e8 != (void *)0) {
        Deallocate(data_0209b2e8);
        data_0209b2e8 = (void *)0;
    }
    data_0209d4a8 = (void *)0;
    Sound::UnsetPlayerVoiceGroup();
    CleanCommonModelDataArr();
    return 1;
}

/* Slot 12. Empty override. */
// @symbol _ZN10dScEntry_c16OnPendingDestroyEv
void dScEntry_c::OnPendingDestroy() {}

/* Slot 9. */
// @symbol _ZN10dScEntry_c6RenderEv
s32 dScEntry_c::Render() {
    if (mRenderStep != 0)
        (this->*mRenderStep)();
    func_0203083c();
    return 1;
}

/* Slot 6. Restores the sub-screen brightness after a step change, then the
 * per-frame step, then every live icon. */
// @symbol _ZN10dScEntry_c8BehaviorEv
s32 dScEntry_c::Behavior() {
    if (mIsFading != 0) {
        mFadeTick++;
        if ((mFadeTick & 1) == 0) {
            mFadeBrightness--;
            func_020551f0((void *)0x4001050, mFadeBrightness);
            if (mFadeBrightness == 0) {
                *(u16 *)0x4001050 = 0;
                mFadeBrightness = 0;
                mIsFading = 0;
            }
        }
    }

    if (data_0209f5bc->IsAtStart() == 0 || mIsFading != 0)
        return 1;

    if (data_0209fc68 != 0) {
        int t = (data_0209fc68 == 6);
        if (t != 0)
            HandlePlayerDisconnect(reinterpret_cast<const StepSet *>(&data_ov075_0211d930));
    }

    if (mBehaviorStep != 0)
        (this->*mBehaviorStep)();

    {
        int i = 0;
        int n = mIconCount;
        if (n > 0) {
            icon_c *o = mIcons;
            do {
                o->Behavior();
                i++;
                o++;
            } while (i < mIconCount);
        }
    }
    return 1;
}

/* Slot 0. */
// @symbol _ZN10dScEntry_c13InitResourcesEv
s32 dScEntry_c::InitResources() {
    char *rawScene = (char *)this;
    Enable3dEngines();
    func_0200f2cc();

    {
        int isResult = (actorID == 7);
        if (isResult || param1 != 0 || func_0203d9b4() != 0) {
            LoadTextNarcs();
            LoadArchive(0);
            LoadArchive(1);
            func_0200f220();
        }
    }

    {
        void *paletteData = (void *)LoadFile(0x9807);
        GXS::LoadBGPltt(paletteData, 0, 0xe0);
        Deallocate(paletteData);
    }
    {
        void *paletteData = (void *)LoadFile(0x8406);
        GXS::LoadBGPltt(paletteData, 0xe0, 0x120);
        Deallocate(paletteData);
    }

    *(u16 *)0x4000008 = (*(u16 *)0x4000008 & ~3) | 3;
    *(u16 *)0x400000c = (*(u16 *)0x400000c & ~3) | 2;
    *(u16 *)0x400000e = (*(u16 *)0x400000e & ~3) | 1;
    SetBg0Offset(0, 0);
    SetBg2Offset(0, 0);
    SetBg3Offset(0, 0);
    data_0209d45c = 0x11;

    *(u16 *)0x4001008 = (*(u16 *)0x4001008 & ~3) | 1;
    *(u16 *)0x400100c = (*(u16 *)0x400100c & ~3) | 3;
    *(u16 *)0x400100e = (*(u16 *)0x400100e & ~3) | 3;
    SetSubBg0Offset(0, 0);
    SetSubBg2Offset(0, 0);
    SetSubBg3Offset(0, 0);
    data_0209d454 = 0x18;

    mFadeBrightness = 0;
    mFadeTick = 0;
    mIsFading = 0;

    if (data_0209b2e8 != 0) {
        Deallocate(data_0209b2e8);
        data_0209b2e8 = 0;
    }
    mDisconnectHideMask = 0;
    LoadFont3D();

    {
        int isEntry = (actorID == 6);
        if (isEntry) {
            func_ov075_02116ad4(rawScene);
            if (param1 == 0) {
                if (func_0203da3c() == 0) {
                    data_0209b2e8 = (void *)LoadFile(0x8409);
                    UnloadArchive(0);
                    func_02030aa4(3);
                }
                {
                    int localPlayer = func_0203da9c();
                    func_02020028(localPlayer, data_0209f4ae[gActivePlayerSlot * 0x18]);
                }
            }
        } else {
            func_ov075_02116818(rawScene);
        }
    }

    func_ov075_0211601c((char *)&data_ov075_0211d71c, (int)rawScene, 1);
    data_0209d4a8 = &data_ov075_0211d71c;
    Sound::LoadInitialGroup(0x2b);

    {
        int isEntry = (actorID == 6);
        if (isEntry) {
            if (param1 < 2) {
                Sound::LoadAndSetMusic_Layer1(0x4c);
            }
        } else {
            if (data_0209b2f0[func_0203da9c()] != 0) {
                Sound::LoadAndSetMusic_Layer1(0x51);
            } else {
                Sound::LoadAndSetMusic_Layer1(0x52);
            }
        }
    }

    data_0208ee44 = 2;
    data_02092778 = 0;
    return 1;
}

/* Slot 1 forwards this and the boolean result through an interworking
 * tail call. ResetFadersAndSound returns only false or true on its two
 * exits. */
// @symbol _ZN10dScEntry_c19BeforeInitResourcesEv
bool dScEntry_c::BeforeInitResources() {
    return ResetFadersAndSound();
}

// @symbol dScEntry_c_classInit_RESULT
/* The array runtime passes each element address and ignores lifecycle
 * results. Explicit function-pointer casts mark that runtime ABI
 * boundary. */
extern "C" {
extern void *_ZN7fBase_cnwEj(unsigned int);
extern void *_ZN7fBase_cC2Ev(void *);
extern void __cxa_vec_ctor(void *base, unsigned int count, unsigned int stride,
                           void (*ctor)(void *), void (*dtor)(void *));

extern char data_0208e4b8[];
extern char _ZTV10dScEntry_c[];
extern dScEntry_c::icon_c *_ZN10dScEntry_c6icon_cD1Ev(dScEntry_c::icon_c *object);
extern dScEntry_c::icon_c *_ZN10dScEntry_c6icon_cC1Ev(dScEntry_c::icon_c *object);
extern OamAnimation *_ZN12OamAnimationD1Ev(OamAnimation *object);
extern OamAnimation *_ZN12OamAnimationC1Ev(OamAnimation *object);

/* Reconstructed source-style name: SM64DS proves dScEntry_c through RTTI,
 * allocation size, vtable identity, and the RESULT registry profile;
 * later EAD lineage supplies classInit. Exact original spelling is not
 * preserved. Historical alias: func_ov075_0211a740. */
void *dScEntry_c_classInit_RESULT(void) {
    /* The raw byte pointer preserves the ROM factory's address-expression
       tree; typed member expressions fold five instructions in mwccarm.
       Members cast through it (pauseFlags, the three steps, mIcons,
       mOamAnimations) are byte-neutral. */
    char *p = (char *)_ZN7fBase_cnwEj(sizeof(dScEntry_c));
    if (p) {
        dScEntry_c::Step v;
        _ZN7fBase_cC2Ev(p);
        *(char **)p = data_0208e4b8;
        *(char **)p = (char *)_ZTV8dScene_c;
        {
            unsigned char *flags = &((dScEntry_c *)p)->pauseFlags;
            *flags |= 1;
            *flags |= 4;
        }
        *(char **)p = _ZTV10dScEntry_c;
        v = 0;
        /* Keep the factory's aggregate-copy schedule for these three stores. */
        *(struct P2Copy *)&((dScEntry_c *)p)->mEnterStep = *(struct P2Copy *)&v;
        *(struct P2Copy *)&((dScEntry_c *)p)->mBehaviorStep = *(struct P2Copy *)&v;
        *(struct P2Copy *)&((dScEntry_c *)p)->mRenderStep = *(struct P2Copy *)&v;
        __cxa_vec_ctor(((dScEntry_c *)p)->mIcons, 9, sizeof(dScEntry_c::icon_c),
                       (void (*)(void *))_ZN10dScEntry_c6icon_cC1Ev,
                       (void (*)(void *))_ZN10dScEntry_c6icon_cD1Ev);
        __cxa_vec_ctor(
            ((dScEntry_c *)p)->mOamAnimations, 4, sizeof(((dScEntry_c *)p)->mOamAnimations[0]),
            (void (*)(void *))_ZN12OamAnimationC1Ev, (void (*)(void *))_ZN12OamAnimationD1Ev);
    }
    return p;
}
}

// @symbol _ZN12OamAnimationC1Ev
OamAnimation::OamAnimation() {}

// @symbol _ZN10dScEntry_c6icon_cC1Ev
dScEntry_c::icon_c::icon_c() {}
