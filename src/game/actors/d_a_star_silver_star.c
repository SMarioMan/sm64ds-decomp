// @symbol daStar_c_classInit_SILVER_STAR
/* recovered: vtable identified, globals resolved, declarations from a shared header */
#include "decl_ActorBase.h"
#include "decl_Enemy.h"
#include "decl_ModelAnim.h"
#include "decl_dCcAcPos_c.h"
#include "decl_ShadowModel.h"
#include "decl_dBgCh_Actr.h"
#include "decl_common.h"

/* File-local view of daStar_c (include/daStar_c.h is C++): the five
   members the factory constructs, sized as that header's layout table. */
typedef struct {
    char pad_000[0x110];
    char mdCc_c[0x40];         /* 0x110 dCcAcPos_c */
    char mWithMeshClsn[0x1bc]; /* 0x150 dBgCh_Actr */
    char mModelAnim1[0x64];    /* 0x30c dExtAnmModel_c */
    char mModelAnim2[0x64];    /* 0x370 dExtAnmModel_c */
    char mShadowModel[0x28];   /* 0x3d4 dExtShadowModel_c */
} StarView;
/* recovered: vtable identified, globals resolved */
/* resolved: VT0 = _ZTV8daStar_c */
/* Reconstructed source-style name: SM64DS proves daStar_c through RTTI,
 * allocation size, vtable identity, and the SILVER_STAR registry profile;
 * later EAD lineage supplies classInit. Exact original spelling is not
 * preserved. Historical alias: SilverStar_Spawn. */
int *daStar_c_classInit_SILVER_STAR(void)
{
    int *p = (int *)_ZN7fBase_cnwEj(1220);
    if (p) {
        _ZN12dEnemyBase_cC2Ev(p);
        p[0] = (int)_ZTV8daStar_c;
        _ZN10dCcAcPos_cC1Ev(((StarView *)p)->mdCc_c);
        _ZN10dBgCh_ActrC1Ev(((StarView *)p)->mWithMeshClsn);
        _ZN14dExtAnmModel_cC1Ev(((StarView *)p)->mModelAnim1);
        _ZN14dExtAnmModel_cC1Ev(((StarView *)p)->mModelAnim2);
        _ZN17dExtShadowModel_cC1Ev(((StarView *)p)->mShadowModel);
    }
    return p;
}
