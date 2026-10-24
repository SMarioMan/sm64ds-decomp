//cpp
/* dExtSimpleModel_c -- the concrete model class (_ZTI17dExtSimpleModel_c at
   0x0208e794, _ZTV17dExtSimpleModel_c at 0x0208e90c). TU claims
   0x020169d8..0x02017168: the dExtSimpleModel_c run, the dExtModel_c edge interleaved with
   it, and the unnamed helpers between them. Written back-to-front: mwccarm
   emits .text in reverse source order under default deferred codegen.

   One ~dExtSimpleModel_c() emits D2, D0, D1 and one dExtSimpleModel_c() emits C1, C2, and the
   cartridge homes all five. One ~dExtModel_c() likewise emits D2, D0, D1 in
   that order. One dExtModel_c() emits C1 beside C2; the cartridge homes only
   C2 (nothing constructs a complete dExtModel_c), which is the variant
   objisolate used to keep from the C2 shard. C1 is licensed deadstrip, not
   a second definition.

   The six _ZThn80_ destructor thunks at 0x02017168..0x020171c8 stay in
   their shards. Only a member destructor of dExtAnmModel_c / dExtBlendAnmModel_c /
   dExtAnm2Model_c emits them, and that definition also emits those classes'
   D-variants, which already have homes in the neighbouring TUs. */

/* common.h comes first so this TU sees the flat Matrix4x3 { s32 m[12]; }
   spelling: the ctor's mat4x3 = IDENTITY_MATRIX4X3 copy block-moves twelve
   words under it, where the structured Matrix3x3+Vector3 spelling
   scalarizes and lands +0x1c bytes long. */
#include "common.h"
#include "dExtSimpleModel_c.h"
#include "Memory.h"
#include "Heap.h"

/* Compiling with RTTI off emits no _ZTI/_ZTS records at all; the vtable
   preamble's typeinfo word deadstrips with the rest of the data sections.
   dExtModel_c's vtable is the same shape. The pragma dates from when the
   class carried a coined name whose records had no cartridge home; under
   the cartridge spelling they would, so RTTI on is open as a manifest
   change (notes/model-rtti-names.md). */
#pragma RTTI off

extern Matrix4x3 IDENTITY_MATRIX4X3;

extern "C" {
extern Matrix4x3 data_0209b3ec;      /* local extern: the camera-space matrix Render uses */
/* local extern: no header declares it */
void MulMat4x3Mat4x3(const Matrix4x3 *m1, const Matrix4x3 *m0, Matrix4x3 *mF);
/* local extern: no header declares it; data.transforms-bone walk in Virtual10 */
void func_02045074(ModelComponents *data, BMD_Bone *bones);
/* local extern: no header declares it; sizes the transforms buffer from the file */
u32 func_02046564(BMD_File *file);
/* local extern: no header declares it; initializes ModelComponents over the file */
void func_020462d0(ModelComponents *data, BMD_File *file, void *buffer);
/* defined below; DoSetFile calls it */
void func_02016b24(dExtSimpleModel_c *model, u32 mask);
/* local extern: no header declares it; delete veneer for the transforms buffer */
void func_0203cbc0(void *ptr);
#ifdef _MSC_VER
/* local extern: host only. ::operator new is the CRT's on the PC port, but
   Memory::operator_delete2 hands this block back to the DS default heap, so
   the host allocates it from that heap directly (src/engine/heap/Heap.cpp
   defines this veneer for the host). */
void *func_0203cc0c(u32 size);
#endif
/* local extern: LoadFile.c defines int(int). This is the spelling
   LoadAndSetFile's shard matched (banked return and parameter rows). */
void *LoadFile(u16 ov0ID);
/* local extern: func_020469e0.c defines int(int *). The caller's shard
   matched this spelling (banked rows). */
u32 func_020469e0(void *ptr);
/* local extern: no header declares it; dExtModel_c's destructor frees the file.
   decl_common.h's copy is the same spelling; that catch-all does not count. */
void Deallocate(void *ptr);
/* local extern: game heap pointer func_02017060 reads */
extern void *data_020a0ea0;
/* decl_common.h's int[] spelling. The records are 0xc-byte CommonModelData. */
extern int data_0209cef8[];
extern int data_0209cefc[];
/* local extern: no header declares it; CleanCommonModelDataArr clears it.
   int, not void *: the other readers declare int, and the store of 0 is
   the same word. */
extern int data_0209cef0;
/* local extern: AddToCommonModelDataArr's "textures already loaded" flag.
   A scalar, matching the other reader; [0] on an int[] is the same word
   but flips the declaration plurality onto this shorter path. */
extern int data_0208e738;
/* local extern: polygon-mode / polygon-id / opacity. Model4.cpp defines the
   first and third as (void *, void *) and (void *, unsigned); these are the
   spellings the call shards matched (banked rows). */
void func_02046234(ModelComponents *data, int mode);
void func_02046008(ModelComponents *data, int id);
void func_020461b4(ModelComponents *data, u32 a);
/* local extern: the +8 adjustors the low veneers forward to. The one-param
   spellings are deliberate under-declarations -- the thunks forward r1/r2
   untouched, which C cannot express (banked arity rows). */
void func_02045ec4(void *self, unsigned int value, int index);
void func_02045e70(char *p);
void func_02045ef8(char *p);
void func_02045f80(char *p);
void func_0204605c(char *p);
/* defined below; LoadAndSetFile calls it */
int func_02016ff4(dExtModel_c *self, BMD_File *file, int c, int d);
u32 func_02017060(void *ptr);
}

/* 0xc-byte records in the common model data array at data_0209cefc, counted
   by data_0209cef8. func_02016e70 fills the two owned slots; the destructors
   and CleanCommonModelDataArr free them. */
struct CommonModelData {
    BMD_File *file;              /* 0x00 */
    ModelComponents *components; /* 0x04 */
    void *buffer;                /* 0x08 */
};

/* One definition emits C1 and C2. C1 has no cartridge home -- objisolate
   kept C2 from the shard -- so the manifest deadstrips C1. */
// @symbol _ZN11dExtModel_cC2Ev
dExtModel_c::dExtModel_c() : modelFile(0) {}

/* One definition emits D2, D0 and D1, in that order: the vptr store is the
   compiler's; the body releases modelFile. D0 follows with the dExtModel_c
   operator delete (Memory::operator_delete2). */
// @symbol _ZN11dExtModel_cD2Ev
// @symbol _ZN11dExtModel_cD0Ev
// @symbol _ZN11dExtModel_cD1Ev
dExtModel_c::~dExtModel_c() {
    if (modelFile != 0) {
        Deallocate(modelFile);
    }
}

// @symbol func_02017060
extern "C" u32 func_02017060(void *ptr) {
    if (!ptr)
        return 0;
    void *heap = data_020a0ea0;
    ((Heap *)heap)->_Sizeof(ptr);
    u32 newSize = func_020469e0(ptr);
    return ((Heap *)heap)->Reallocate(ptr, newSize);
}

/* Loads the file offsets, calls the object's DoSetFile through vtable slot 2,
   and on success reallocs the file down to its reported size. */
// @symbol func_02016ff4
extern "C" int func_02016ff4(dExtModel_c *self, BMD_File *file, int c, int d) {
    int ret;
    if (!file)
        return 0;
    dExtSimpleModel_c::UpdateFileOffsets(*file);
    ret = self->DoSetFile((char *)file, c, d);
    if (ret)
        func_02017060(file);
    return ret;
}

// @symbol _ZN11dExtModel_c7SetFileEP8BMD_Fileii
int dExtModel_c::SetFile(BMD_File *file, int a, int b) {
    return DoSetFile((char *)file, a, b);
}

// @symbol _ZN17dExtSimpleModel_c14LoadAndSetFileEtii
void dExtSimpleModel_c::LoadAndSetFile(u16 ov0ID, int a, int b) {
    BMD_File *file = (BMD_File *)::LoadFile(ov0ID);
    modelFile = file;
    func_02016ff4(this, file, a, b);
}

// @symbol _ZN17dExtSimpleModel_c23AddToCommonModelDataArrER8BMD_File
void *dExtSimpleModel_c::AddToCommonModelDataArr(BMD_File &file) {
    CommonModelData *p = (CommonModelData *)data_0209cefc;
    int i = 0;
    int n = data_0209cef8[0];
    while (i < n) {
        if (&file == p->file)
            return p;
        i++;
        p++;
    }
    p->file = &file;
    p->components = 0;
    p->buffer = 0;
    data_0209cef8[0] = data_0209cef8[0] + 1;
    if (data_0208e738 == 0)
        return p;
    LoadTexAndPal(file);
    return p;
}

/* Get-or-create the pooled ModelComponents entry for the pointer-holding
   siblings (dExtCommonModel_c/dExtShadowModel_c). */
// @symbol func_02016e70
extern "C" void *func_02016e70(void *file) {
    CommonModelData *e;
    void *b;

    e = (CommonModelData *)dExtSimpleModel_c::AddToCommonModelDataArr(*(BMD_File *)file);
    if (e->components == 0) {
#ifdef _MSC_VER
        e->components = (ModelComponents *)func_0203cc0c(0x14);
#else
        e->components = (ModelComponents *)::operator new(0x14);
#endif
        if (e->components == 0)
            return 0;
        e->buffer = Memory::operator_new2(func_02046564((BMD_File *)file));
        b = e->buffer;
        if (b == 0) {
            Memory::operator_delete2(e->components);
            e->components = 0;
            return 0;
        }
        func_020462d0(e->components, (BMD_File *)file, b);
    }
    return e->components;
}

// @symbol CleanCommonModelDataArr
extern "C" void CleanCommonModelDataArr(void) {
    CommonModelData *e = (CommonModelData *)data_0209cefc;
    int i = 0;

    if (data_0209cef8[0] > 0) {
        do {
            if (e->buffer)
                func_0203cbc0(e->buffer);
            if (e->components)
                Memory::operator_delete2(e->components);
            i++;
            e++;
        } while (i < data_0209cef8[0]);
    }

    data_0209cef8[0] = 0;
    data_0209cef0 = 0;
}

/* One definition emits C1 and C2: the base-chain call to dExtModel_c::C2, the
   _ZTV17dExtSimpleModel_c vptr store, the flat twelve-word identity copy, and the
   transformsBuf zero. The cartridge keeps both variants. */
// @symbol _ZN17dExtSimpleModel_cC2Ev
// @symbol _ZN17dExtSimpleModel_cC1Ev
dExtSimpleModel_c::dExtSimpleModel_c() : transformsBuf(0) {
    mat4x3 = IDENTITY_MATRIX4X3;
}

/* One definition emits D2, D0 and D1: the vptr store and the dExtModel_c
   destructor call are the compiler's; the body is the class's one written
   obligation -- handing transformsBuf back through the delete veneer. D0
   follows with the dExtModel_c operator delete (Memory::operator_delete2). */
// @symbol _ZN17dExtSimpleModel_cD1Ev
dExtSimpleModel_c::~dExtSimpleModel_c() {
    if (transformsBuf)
        func_0203cbc0(transformsBuf);
}

// @symbol _ZN17dExtSimpleModel_c11UpdateVertsEv
void dExtSimpleModel_c::UpdateVerts() {
    data.UpdateVertsUsingBones();
}

// @symbol _ZN17dExtSimpleModel_c9DoSetFileEPcii
int dExtSimpleModel_c::DoSetFile(char *file_, int a, int b) {
    BMD_File *file = (BMD_File *)file_;
    void *buffer;
    AddToCommonModelDataArr(*file);
    transformsBuf = Memory::operator_new2(func_02046564(file));
    buffer = transformsBuf;
    if (buffer == 0) return 0;
    func_020462d0(&data, file, buffer);
    data.UpdateVertsUsingBones();
    if (a != 0) func_02016b24(this, 0x8000);
    if (b < 0) return 1;
    SetPolygonID(b & 0xff);
    return 1;
}

// @symbol _ZN17dExtSimpleModel_c9Virtual10ER9Matrix4x3
void dExtSimpleModel_c::Virtual10(Matrix4x3 &mat) {
    /* The copy is one flat 12-word ldm/stm run in the ROM. CW copies the
       nested Matrix4x3 (Matrix3x3 + Vector3) memberwise, which is bigger,
       so it goes through a flat 12-word view instead. */
    struct Mtx12w { Fix12i m[12]; };
    *(Mtx12w *)data.transforms = *(const Mtx12w *)&mat;
    func_02045074(&data, data.modelFile->bones);
}

// @symbol _ZN17dExtSimpleModel_c6RenderEPK7Vector3
void dExtSimpleModel_c::Render(const Vector3 *scale) {
    Matrix4x3 temp;
    MulMat4x3Mat4x3(&mat4x3, &data_0209b3ec, &temp);
    data.Render(&temp, (Vector3 *)scale);
}

// @symbol func_02016b24
extern "C" void func_02016b24(dExtSimpleModel_c *model, u32 mask) {
    u32 count = model->data.modelFile->numMaterials;
    BMD_Material *p = model->data.materials;
    u32 i;
    for (i = 0; i < count; i++) {
        p->flags |= mask;
        p++;
    }
}

// @symbol func_02016acc
extern "C" void func_02016acc(dExtSimpleModel_c *model, unsigned int mask) {
    BMD_File *file = model->data.modelFile;
    unsigned int n = file->numMaterials;
    BMD_Material *q = model->data.materials;

    for (unsigned int i = 0; i < n; i++) {
        unsigned int nmask = ~mask;
        q->flags &= nmask;
        q++;
    }
}

// @symbol _ZN17dExtSimpleModel_c12SetPolygonIDEi
void dExtSimpleModel_c::SetPolygonID(int id) {
    func_02046008(&data, id);
}

// @symbol func_02016aac
extern "C" void func_02016aac(char *self) {
    func_0204605c(self + 8);
}

// @symbol _ZN11dExtModel_c12ApplyOpacityEjj
void dExtModel_c::ApplyOpacity(u32 opacity, u32) {
    func_020461b4(&static_cast<dExtSimpleModel_c *>(this)->data, opacity);
}

// @symbol _ZN17dExtSimpleModel_c14SetPolygonModeEi
void dExtSimpleModel_c::SetPolygonMode(int mode) {
    func_02046234(&data, mode);
}

// @symbol _ZN17dExtSimpleModel_c12HideMaterialEii
void dExtSimpleModel_c::HideMaterial(int boneID, int listIdx) {
    BMD_File *file = data.modelFile;
    BMD_Material *mats = data.materials;
    u8 *ids = file->bones[boneID].materialIds;
    mats[ids[listIdx]].flags |= 0x80000000;
}

// @symbol _ZN17dExtSimpleModel_c12ShowMaterialEii
void dExtSimpleModel_c::ShowMaterial(int boneID, int listIdx) {
    BMD_File *file = data.modelFile;
    BMD_Material *mats = data.materials;
    u8 *ids = file->bones[boneID].materialIds;
    mats[ids[listIdx]].flags &= 0x7fffffff;
}

// @symbol func_02016a14
extern "C" void func_02016a14(char *self) {
    func_02045f80(self + 8);
}

// @symbol func_02016a04
extern "C" void func_02016a04(char *self) {
    func_02045ef8(self + 8);
}

// @symbol func_020169f4
extern "C" void func_020169f4(char *self) {
    func_02045e70(self + 8);
}

// @symbol func_020169d8
extern "C" void func_020169d8(char *self, int index, unsigned int value) {
    func_02045ec4(self + 8, value, index);
}
