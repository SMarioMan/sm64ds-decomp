/* dScMgRoulette_c -- Mushroom Roulette. The dealer hands out racers, the
 * player drops them on the board's tiles, and a ball spins round the wheel;
 * the racers on the tile it stops on pay out. Child of dScMgSingle3DBase_c,
 * size 0x5400.
 *
 * RTTI: dScMgRoulette_c : dScMgSingle3DBase_c (tools/rtti_extract.py).
 * Factory dScMgRoulette_c_classInit; historical alias MgMushroomRoulette_Spawn.
 * ROM: D1 0x0210788c below D0 0x02107920, no D2; out of line would emit
 * D2, D0, D1. InitResources is then the first declared non-inline virtual,
 * so it is the key function; this TU licenses _ZTV/_ZTI/_ZTS in
 * compiler_only_output.
 *
 * The destructor is inline and declared first, so D1 comes out before D0
 * and no D2 is emitted. Its four calls follow the ROM: second model, first
 * model, racer array, table. Typed members would destroy in a different
 * order. InitResources stays the key function. dScMgBase_c supplies
 * operator delete.
 */
#ifndef DSCMGROULETTE_C_H
#define DSCMGROULETTE_C_H
#include "dScMgSingle3DBase_c.h"

extern "C" int  Dealer_Destruct(char *t); /* decl_common.h's own signature */
extern "C" void __cxa_vec_cleanup(void *base, int count, int stride, void *dtor);
extern "C" void Roulette_Nothing(void);
extern "C" void _ZN17dExtSimpleModel_cD1Ev(void *);

struct dScMgRoulette_c : dScMgSingle3DBase_c {
    /* Inline and declared first: see the file banner. The four explicit calls
       are the ROM's own order -- mModel2, mModel1, mArray, mDealer -- which
       typed members could not reproduce. */
    virtual ~dScMgRoulette_c() {
        _ZN17dExtSimpleModel_cD1Ev(mModel2);
        _ZN17dExtSimpleModel_cD1Ev(mModel1);
        __cxa_vec_cleanup(mArray, 5, 0x34, (void *)Roulette_Nothing);
        Dealer_Destruct((char *)mDealer);
    }

    /* --- this class's own vtable slots, named from the table ---
       Re-overrides of slots fBase_c already owns, NOT new virtuals: the
       table stays the base's width and no field moves. Declared AFTER the
       destructor so the destructor is still the first virtual declared. */
    virtual s32 InitResources();     /* slot 0 -- src/_ZN15dScMgRoulette_c13InitResourcesEv.cpp */
    virtual s32 CleanupResources();  /* slot 3 -- ov006 0x0210980c */
    virtual s32 Behavior();          /* slot 6 -- ov006 0x02109aac */
    virtual s32 Render();            /* slot 9 -- ov006 0x02109834 */
    virtual void StartRound(int arg);               /* slot 18 */
    virtual int  CanEndState(int mode);              /* slot 19 */

    u8 mDealer[0x270];     /* 0x4f38 -- the dealer (Dealer.h) */
    u8    mArray[0x104];   /* 0x51a8 -- 5 racers, 0x34 each */
    u8    mMeter[4][0x18]; /* 0x52ac -- strips for payouts 12, 6, 3, 2 */
    /* mBoard through mBraking is the wheel and its ball. The RouletteBoard_
       helpers in d_s_mg_roulette_methods.cpp take mBoard and reach all of
       it through their RouletteBoardView. */
    u8 mBoard[0x10];       /* 0x530c -- PMF state and the two model files */
    u8 mModel1[0x50];      /* 0x531c -- raw dExtSimpleModel_c, the wheel; destroyed explicitly */
    u8 mModel2[0x50];      /* 0x536c -- the ball */
    s32 mBallRadius;       /* 0x53bc -- Fix12; 0x4200 when the spin starts */
    s32 mBallRadiusVel;    /* 0x53c0 -- added to mBallRadius each frame */
    s32 mSpinSpeed;        /* 0x53c4 -- the ball's speed; at 0 it has stopped:
                              Render draws the cursor and phase 3 pays out */
    s32 mRollSoundHandle;  /* 0x53c8 -- Sound_PlayIfNotActive's handle */
    s16 mOrbitAngle;       /* 0x53cc -- the ball's angle round the wheel */
    s16 mBoardAngle;       /* 0x53ce -- the wheel's own angle */
    s16 mSlowBias;         /* 0x53d0 -- -mBoardAngle when the slowdown starts */
    s16 mAngleStep;        /* 0x53d2 -- mOrbitAngle's step this frame */
    s16 mBoardSpin;        /* 0x53d4 -- mBoardAngle's step, -0x200 */
    s16 mStopTile;         /* 0x53d6 -- the tile under the ball; phase 3 scores against it */
    s16 mRollSound;        /* 0x53d8 -- 0 quiet; 1 on the rim (sound 0x157); 2 off
                              the rim, in the bowl (0x158). Phase 1 sets 1 once the
                              dealer is done; striking a stop plays 0x159 and clears it */
    s16   pad_53da;        /* 0x53da */
    s32 mBraking;          /* 0x53dc -- phase 2 sets it; the spin then eases to 0 */
    s32   unk_53e0;        /* 0x53e0 -- reset to 0x100; not read in this TU */
    s16   mCameraPreset;     /* 0x53e4 -- Render copies row n of the camera
                                tables (data_ov006_0213e34c / _0213e370 at stride
                                0xc, and _0213e2e0 for the angle) into
                                mCameraEye/mCameraTarget/mCameraAngle, then calls
                                Camera_UpdateMatrices. 0 leaves the camera alone */
    s16   mPhase;            /* 0x53e6 -- 1 deals the racers out, 2 runs the
                                countdown and reads the board, 3 pays out per
                                landed tile, 4 announces the result */
    s16   mPhaseTimer;       /* 0x53e8 -- counted down in every phase; each
                                phase reloads it on entry */
    s16   unk_53ea;          /* 0x53ea */
    u8    unk_53ec;          /* 0x53ec */
    u8    unk_53ed;          /* 0x53ed */
    u8    unk_53ee;          /* 0x53ee */
    u8    unk_53ef;          /* 0x53ef */
    u8    unk_53f0;          /* 0x53f0 */
    u8    pad_53f1[0x1];
    s16   mScore;            /* 0x53f2 -- the payout summed over the racers;
                                phase 4 compares it against mTargetScore */
    s16   unk_53f4;          /* 0x53f4 -- cleared when the payout is posted */
    s16   mTargetScore;      /* 0x53f6 -- one per racer that missed the winning
                                tile; the bar mScore has to beat */
    s32   mDealIndex;        /* 0x53f8 -- how many racers have been dealt out;
                                also reused as a loop cursor between phases */
    s32   mRacerCount;       /* 0x53fc -- the bound of every per-racer loop in
                                Behavior and Render */
};

#ifndef SM64DS_PLATFORM_PC
/* ROM layout under mwccarm; host ABI divergence is tracked separately. */
typedef char dScMgRoulette_c_size_must_be_0x5400[sizeof(dScMgRoulette_c) == 0x5400 ? 1 : -1];
#endif

#endif
