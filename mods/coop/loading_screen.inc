// Included only by runtime.cpp with COOP_EXPERIMENTAL_LOADING_SCREEN.
// Lease a small sub-OBJ region only during native stage initialization.
void CoopLoadingOriginalDisableBanks(void);
void CoopLoadingOriginalDecompress(const void *source,void *destination);
void CoopLoadingOriginalObjPalette(const void *source,u32 offset,u32 size);
int CoopLoadingOriginalReadAt(void *file,void *destination,u32 size);
void CoopLoadingSetSubObjBank(u16 banks);
void CoopLoadingOriginalVBlank(void);

static volatile u32 coopLoadingWanted=0,coopLoadingActive=0;
static u32 coopLoadingWriting=0,coopLoadingBorrowedBank=0;
static u32 coopLoadingSavedDisplay=0;
static u16 coopLoadingSavedBrightness=0,coopLoadingSavedPalette[2];
static u8 coopLoadingSavedBank=0;
static u16 coopLoadingSavedLcdc=0,coopLoadingSavedOam[24];
static u32 coopLoadingSavedTiles[64];
// starts, stops, VBlank draws, asset pauses, bank skips, context skips, faults.
u32 coopLoadingScreenStats[7]={0};
static const u8 coopLoadingLetters[7][5]={
    {16,16,16,16,31}, {14,17,17,17,14}, {14,17,31,17,17},
    {30,17,17,17,30}, {31,4,4,4,31}, {17,25,21,19,17}, {14,16,23,17,15}
};
static const u8 coopLoadingSpinner[4][5]={
    {4,4,4,4,4}, {1,2,4,8,16}, {0,0,31,0,0}, {16,8,4,2,1}
};
static unsigned CoopLoadingPixel(const u8 *glyph,int x,int y) {
    return x>=1 && x<6 && y>=1 && y<6 && (glyph[y-1]&(1u<<(5-x)));
}
static void CoopLoadingGlyph(unsigned tile,const u8 *glyph) {
    volatile u32 *out=(volatile u32 *)(0x06603f00+tile*32);
    for (int y=0;y<8;++y) {
        u32 row=0;
        for (int x=0;x<8;++x) {
            unsigned color=CoopLoadingPixel(glyph,x,y) ? 1 : 0;
            if (!color && (CoopLoadingPixel(glyph,x-1,y) || CoopLoadingPixel(glyph,x+1,y) ||
                CoopLoadingPixel(glyph,x,y-1) || CoopLoadingPixel(glyph,x,y+1)))color=2;
            row|=color<<(x*4);
        }
        out[y]=row;
    }
}
void CoopLoadingVBlank(void) {
    CoopLoadingOriginalVBlank();
    if (!coopLoadingActive)return;
    if (*(volatile u8 *)0x04000249!=0x82) {
        ++coopLoadingScreenStats[6];return;
    }
    unsigned frame=(*(volatile u32 *)0x027ffc3c>>3)&3;
    CoopLoadingGlyph(7,coopLoadingSpinner[frame]);
    for (unsigned i=0;i<8;++i) {
        volatile u16 *oam=(volatile u16 *)0x07000400+i*4;
        oam[0]=88;oam[1]=(u16)(96+i*8);oam[2]=(u16)(0xf000+504+i);
    }
    ++coopLoadingScreenStats[2];
}

void CoopLoadingSuspend(void) {
    if (!coopLoadingActive)return;
    u32 irq=_ZN3IRQ7DisableEv();
    coopLoadingActive=0;
    if (IRQ::GetIRQHandler(1)==CoopLoadingVBlank)
        IRQ::SetIRQHandler(1,CoopLoadingOriginalVBlank);
    if (*(volatile u8 *)0x04000249==0x82) {
        volatile u32 *tiles=(volatile u32 *)0x06603f00;
        for (unsigned i=0;i<64;++i)tiles[i]=coopLoadingSavedTiles[i];
    } else ++coopLoadingScreenStats[6];
    volatile u16 *palette=(volatile u16 *)0x050007e2;
    palette[0]=coopLoadingSavedPalette[0];palette[1]=coopLoadingSavedPalette[1];
    for (unsigned i=0;i<8;++i) {
        volatile u16 *oam=(volatile u16 *)0x07000400+i*4;
        for (unsigned j=0;j<3;++j)oam[j]=coopLoadingSavedOam[i*3+j];
    }
    const u32 mask=0x00031000;
    volatile u32 *display=(volatile u32 *)0x04001000;
    *display=(*display&~mask)|coopLoadingSavedDisplay;
    *(volatile u16 *)0x0400106c=coopLoadingSavedBrightness;
    if (coopLoadingBorrowedBank) {
        CoopLoadingSetSubObjBank(0);
        *(volatile u8 *)0x04000249=coopLoadingSavedBank;
        volatile u16 *lcdc=(volatile u16 *)0x020a6088;
        *lcdc=(*lcdc&~0x100)|(coopLoadingSavedLcdc&0x100);
        coopLoadingBorrowedBank=0;
    }
    ++coopLoadingScreenStats[1];
    _ZN3IRQ7RestoreEj(irq);
}
void CoopLoadingBegin(void) {
    if (!coopLoadingWanted || coopLoadingActive || coopLoadingWriting ||
        !coopEnabled || data_0209fc68!=4)return;
    u32 irq=_ZN3IRQ7DisableEv();
    u32 display=*(volatile u32 *)0x04001000;
    if (!(*(volatile u16 *)0x04000304&0x200) || (display&0x80300010) ||
        IRQ::GetIRQHandler(1)!=CoopLoadingOriginalVBlank) {
        ++coopLoadingScreenStats[5];_ZN3IRQ7RestoreEj(irq);return;
    }
    volatile u16 *banks=(volatile u16 *)0x020a6088;
    u8 bank=*(volatile u8 *)0x04000249;
    if (bank!=0x82 || banks[10]!=0x100) {
        unsigned owned=0;
        for (unsigned i=1;i<13;++i)owned|=banks[i];
        if ((bank!=0 && bank!=0x80) || (owned&0x100)) {
            ++coopLoadingScreenStats[4];_ZN3IRQ7RestoreEj(irq);return;
        }
        coopLoadingSavedBank=bank;coopLoadingSavedLcdc=banks[0];
        CoopLoadingSetSubObjBank(0x100);coopLoadingBorrowedBank=1;
    }
    volatile u32 *tiles=(volatile u32 *)0x06603f00;
    for (unsigned i=0;i<64;++i)coopLoadingSavedTiles[i]=tiles[i];
    volatile u16 *palette=(volatile u16 *)0x050007e2;
    coopLoadingSavedPalette[0]=palette[0];coopLoadingSavedPalette[1]=palette[1];
    palette[0]=0x7fff;palette[1]=0;
    for (unsigned i=0;i<8;++i) {
        volatile u16 *oam=(volatile u16 *)0x07000400+i*4;
        for (unsigned j=0;j<3;++j)coopLoadingSavedOam[i*3+j]=oam[j];
    }
    for (unsigned i=0;i<7;++i)CoopLoadingGlyph(i,coopLoadingLetters[i]);
    coopLoadingSavedDisplay=display&0x00031000;
    coopLoadingSavedBrightness=*(volatile u16 *)0x0400106c;
    *(volatile u32 *)0x04001000=(display&~0x00030000)|0x00011000;
    *(volatile u16 *)0x0400106c=0;
    coopLoadingActive=1;++coopLoadingScreenStats[0];
    IRQ::SetIRQHandler(1,CoopLoadingVBlank);
    _ZN3IRQ7RestoreEj(irq);
}
void CoopLoadingAllow(void) { coopLoadingWanted=1;CoopLoadingBegin(); }
void CoopLoadingEnd(void) { coopLoadingWanted=0;CoopLoadingSuspend(); }
static bool CoopLoadingWritesOwned(void *destination) {
    u32 dest=(u32)destination;
    return (dest>=0x06600000 && dest<0x06604000) || (dest>=0x05000600 && dest<0x05000800);
}
void CoopLoadingDisableBanks(void) {
    CoopLoadingSuspend();CoopLoadingOriginalDisableBanks();
}
void CoopLoadingDecompress(const void *source,void *destination) {
    bool pause=coopLoadingWanted && CoopLoadingWritesOwned(destination);
    if (pause) { ++coopLoadingWriting;++coopLoadingScreenStats[3];CoopLoadingSuspend(); }
    CoopLoadingOriginalDecompress(source,destination);
    if (pause) { --coopLoadingWriting;CoopLoadingBegin(); }
}
void CoopLoadingObjPalette(const void *source,u32 offset,u32 size) {
    bool pause=coopLoadingWanted!=0;
    if (pause) { ++coopLoadingWriting;++coopLoadingScreenStats[3];CoopLoadingSuspend(); }
    CoopLoadingOriginalObjPalette(source,offset,size);
    if (pause) { --coopLoadingWriting;CoopLoadingBegin(); }
}
int CoopLoadingReadAt(void *file,void *destination,u32 size) {
    bool pause=coopLoadingWanted && CoopLoadingWritesOwned(destination);
    if (pause) { ++coopLoadingWriting;++coopLoadingScreenStats[3];CoopLoadingSuspend(); }
    int result=CoopLoadingOriginalReadAt(file,destination,size);
    if (pause) { --coopLoadingWriting;CoopLoadingBegin(); }
    return result;
}
