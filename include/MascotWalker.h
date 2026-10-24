#ifndef MASCOTWALKER_H
#define MASCOTWALKER_H

#include "types.h"
#include "dExtBlendAnmModel_c.h"

/* MascotWalker, the small figure that walks the card table's paths in the card
 * games (the dealer embeds one at +0xdc, which fixes the 0xf8 size): a Toad,
 * whose files resolve (tools/asset_catalog.py) to MG/kino_d.bmd, kino_wait.bca
 * and kino_walk.bca. The name is coined. A layout view only: the MascotWalker_* helpers in
 * src/minigames/unit020bfec0.cpp are free functions over a char* record and
 * read it through their WALKER() cast. Unnamed regions are touched in one
 * place at most, or sit inside an embedded object. */
struct MascotWalker {
    /* Three SharedFilePtrs, each a handle and then the loaded file. */
    s32 mModelFile[2]; /* 0x00 -- kino_d.bmd (0x205) */
    /* kino_wait.bca (0x206): [1] is the BCA Load starts and StartPause restarts. */
    s32 mPauseAnimFile[2]; /* 0x08 */
    s32 mWalkAnimFile[2];  /* 0x10 -- kino_walk.bca (0x207): [1] StartNextPath restarts */
    /* 0x70 bytes. UpdateMatrix sets its mat4x3 and turns bone 6 of its
       data.transforms by mHeadAngle; StateWalk pauses when its dExtFrameCtrl_c
       base hits frame 0. */
    dExtBlendAnmModel_c mModel; /* 0x18 */
    /* Built by Construct, InitCylinder'd by Load and InitModel'd on mModel.mat4x3 by Draw. */
    u8 mShadow[0x28]; /* 0x88 -- a dExtShadowModel_c */
    s32 mPath;        /* 0xb0 -- the path walked: a point count, then the points */
    s32 mState[2];    /* 0xb4 -- the current state's member-pointer record */
    /* Load sets all three to 0x1000 (1.0), beside mPos and the angles; nothing
       in this file reads it back. */
    Vector3 mScale;   /* 0xbc */
    Vector3 mPos;     /* 0xc8 */
    Vector3 mDir;     /* 0xd4 -- unit vector toward the next point */
    s32 mPathPoint;   /* 0xe0 -- the point being walked to */
    s32 mPathIndex;   /* 0xe4 -- which of the four paths, cycling */
    /* Load copies data_020a0edc's x/y/z into 0xe8/0xea/0xec, the same start
       rotation Dealer_Load copies into Dealer::mRot. */
    s16 mAngleX;      /* 0xe8 */
    s16 mAngleY;      /* 0xea -- eased toward mTargetAngle */
    s16 mAngleZ;      /* 0xec */
    s16 mTargetAngle; /* 0xee -- horizontal angle to the next point */
    /* Applied as an X rotation to bone 6 by UpdateMatrix; Update eases it
       toward sMascotWalkerOffset (clamped to +/-0x3000) while mPaused, else to 0. */
    s16 mHeadAngle; /* 0xf0 */
    /* Counted down by StateWalk and StatePause: 0x78 frames of pause from
       StartPause, then 0x258..0x4af frames of walking from StatePause. */
    s16 mStateTimer; /* 0xf2 */
    s32 mPaused;     /* 0xf4 -- set by StartPause, cleared when StatePause resumes the walk */
};

#ifndef SM64DS_PLATFORM_PC
typedef char MascotWalker_size_must_be_0xf8[sizeof(MascotWalker) == 0xf8 ? 1 : -1];
#endif

#endif
