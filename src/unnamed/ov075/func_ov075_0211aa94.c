#include "BMD_File.h"
#include "private/ov075_entry_mesh.h"

void *_ZN17dExtSimpleModel_c27LoadCompressedTextureToVramEPcjS0_(char *a, unsigned int b, char *c);
int func_02045ad8(void *p);
unsigned int func_02045a50(const void *src, unsigned int size);

/* A BMD_Material's two colour words, which BMD_File.h still keeps inside
 * pad_28 (a shared header with hundreds of consumers): func_ov075_0211a948
 * pushes the copies below to DIF_AMB and SPE_EMI. Names as in
 * EntryMesh::mMaterial. */
typedef struct BMDMaterialColors {
    char pad_00[0x28];
    int difAmb; /* 0x28 */
    int speEmi; /* 0x2c */
} BMDMaterialColors;
typedef char BMDMaterialColors_size_must_be_0x30[sizeof(BMDMaterialColors) == 0x30 ? 1 : -1];

/* Load the mesh's texture and palette from its BMD file into VRAM and keep
 * the addresses with the first material's colours and the texture's
 * parameter word; 0 if either load failed. */
int func_ov075_0211aa94(char *c, char *b)
{
    EntryMesh *mesh = (EntryMesh *)c;
    struct BMD_File *file = (struct BMD_File *)b;
    char *d;
    struct BMD_Texture *tex;
    struct BMD_Palette *pal;
    int sz;

    tex = file->textures;
    d = (char *)file->materials;
    pal = file->palettes;

    mesh->mMaterial.texAddr = (u32)_ZN17dExtSimpleModel_c27LoadCompressedTextureToVramEPcjS0_(
        tex->data, tex->size, tex->data + tex->size);
    sz = pal->size;
    if (sz <= 8)
        mesh->mMaterial.pltAddr = func_02045ad8(pal->data);
    else
        mesh->mMaterial.pltAddr = func_02045a50(pal->data, (unsigned int)sz);
    /* d is the first BMD_Material. */
    mesh->mMaterial.difAmb = ((BMDMaterialColors *)d)->difAmb;
    mesh->mMaterial.speEmi = ((BMDMaterialColors *)d)->speEmi;
    mesh->mMaterial.param = tex->flags;
    if (mesh->mMaterial.texAddr == 0 || mesh->mMaterial.pltAddr == 0)
        return 0;
    return 1;
}
