// Minimal POSIX frontend for automated tests of the unmodified melonDS core.
#include "Platform.h"
#include "SPI_Firmware.h"
#include "net/LocalMP.h"
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <chrono>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <dlfcn.h>
#include <unistd.h>

namespace melonDS::Platform {
static FILE* fp(FileHandle* p) { return reinterpret_cast<FILE*>(p); }
static int instance(void* p) { return int(reinterpret_cast<uintptr_t>(p)); }
static LocalMP& bus() { static LocalMP b; return b; }
void SignalStop(StopReason r, void* p) { fprintf(stderr,"STOP instance=%d reason=%d\n",instance(p),r); }
std::string GetLocalFilePath(const std::string& p) { return p; }
FileHandle* OpenFile(const std::string& p,FileMode m) {
    bool exists=access(p.c_str(),F_OK)==0;
    if ((m&NoCreate)&&!exists) return nullptr;
    const char* mode=(m&Append)?"a+b":(m&Write)?((m&Preserve)&&exists?"r+b":"w+b"):"rb";
    return reinterpret_cast<FileHandle*>(fopen(p.c_str(),mode));
}
FileHandle* OpenLocalFile(const std::string& p,FileMode m) { return OpenFile(p,m); }
bool FileExists(const std::string& p) { return access(p.c_str(),F_OK)==0; }
bool LocalFileExists(const std::string& p) { return FileExists(p); }
bool CheckFileWritable(const std::string& p) { auto f=OpenFile(p,FileMode(ReadWrite|Preserve)); if(!f)return false;return CloseFile(f); }
bool CheckLocalFileWritable(const std::string& p) { return CheckFileWritable(p); }
bool CloseFile(FileHandle* f) { return fclose(fp(f))==0; }
bool IsEndOfFile(FileHandle* f) { return feof(fp(f)); }
bool FileReadLine(char* s,int n,FileHandle* f) { return fgets(s,n,fp(f))!=nullptr; }
u64 FilePosition(FileHandle* f) { return ftello(fp(f)); }
bool FileSeek(FileHandle* f,s64 n,FileSeekOrigin o) { return fseeko(fp(f),n,o==FileSeekOrigin::Start?SEEK_SET:o==FileSeekOrigin::Current?SEEK_CUR:SEEK_END)==0; }
void FileRewind(FileHandle* f) { rewind(fp(f)); }
u64 FileRead(void* d,u64 s,u64 n,FileHandle* f) { return fread(d,s,n,fp(f)); }
u64 FileWrite(const void* d,u64 s,u64 n,FileHandle* f) { return fwrite(d,s,n,fp(f)); }
bool FileFlush(FileHandle* f) { return fflush(fp(f))==0; }
u64 FileWriteFormatted(FileHandle* f,const char* fmt,...) { va_list a;va_start(a,fmt);int r=vfprintf(fp(f),fmt,a);va_end(a);return r; }
u64 FileLength(FileHandle* f) { auto p=ftello(fp(f));fseeko(fp(f),0,SEEK_END);auto n=ftello(fp(f));fseeko(fp(f),p,SEEK_SET);return n; }
void Log(LogLevel l,const char* fmt,...) { if(l<Warn)return;va_list a;va_start(a,fmt);vfprintf(stderr,fmt,a);va_end(a); }
struct Thread { std::thread t; };
Thread* Thread_Create(std::function<void()> f) { return new Thread{std::thread(std::move(f))}; }
void Thread_Wait(Thread* t) { if(t->t.joinable())t->t.join(); }
void Thread_Free(Thread* t) { Thread_Wait(t);delete t; }
struct Semaphore { std::mutex m;std::condition_variable cv;int n=0; };
Semaphore* Semaphore_Create() { return new Semaphore; }
void Semaphore_Free(Semaphore* s) { delete s; }
void Semaphore_Reset(Semaphore* s) { std::lock_guard<std::mutex> l(s->m);s->n=0; }
bool Semaphore_TryWait(Semaphore* s,int ms) { std::unique_lock<std::mutex> l(s->m);if(!s->cv.wait_for(l,std::chrono::milliseconds(ms),[s]{return s->n>0;}))return false;--s->n;return true; }
void Semaphore_Wait(Semaphore* s) { std::unique_lock<std::mutex> l(s->m);s->cv.wait(l,[s]{return s->n>0;});--s->n; }
void Semaphore_Post(Semaphore* s,int n) { std::lock_guard<std::mutex> l(s->m);s->n+=n;s->cv.notify_all(); }
struct Mutex { std::mutex m; };
Mutex* Mutex_Create() { return new Mutex; }
void Mutex_Free(Mutex* m) { delete m; }
void Mutex_Lock(Mutex* m) { m->m.lock(); }
void Mutex_Unlock(Mutex* m) { m->m.unlock(); }
bool Mutex_TryLock(Mutex* m) { return m->m.try_lock(); }
void Sleep(u64 us) { std::this_thread::sleep_for(std::chrono::microseconds(us)); }
u64 GetUSCount() { return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
u64 GetMSCount() { return GetUSCount()/1000; }
// Tests keep all save and firmware changes in each emulated console's RAM.
void WriteNDSSave(const u8*,u32,u32,u32,void*) {}
void WriteGBASave(const u8*,u32,u32,u32,void*) {}
void WriteFirmware(const Firmware&,u32,u32,void*) {}
void WriteDateTime(int,int,int,int,int,int,void*) {}
void MP_Begin(void* p) { bus().Begin(instance(p)); }
void MP_End(void* p) { bus().End(instance(p)); }
int MP_SendPacket(u8* d,int n,u64 t,void* p) { return bus().SendPacket(instance(p),d,n,t); }
int MP_RecvPacket(u8* d,u64* t,void* p) { return bus().RecvPacket(instance(p),d,t); }
int MP_SendCmd(u8* d,int n,u64 t,void* p) { return bus().SendCmd(instance(p),d,n,t); }
int MP_SendReply(u8* d,int n,u64 t,u16 a,void* p) { return bus().SendReply(instance(p),d,n,t,a); }
int MP_SendAck(u8* d,int n,u64 t,void* p) { return bus().SendAck(instance(p),d,n,t); }
int MP_RecvHostPacket(u8* d,u64* t,void* p) { return bus().RecvHostPacket(instance(p),d,t); }
u16 MP_RecvReplies(u8* d,u64 t,u16 a,void* p) { return bus().RecvReplies(instance(p),d,t,a); }
int Net_SendPacket(u8*,int,void*) { return 0; }
int Net_RecvPacket(u8*,void*) { return 0; }
void Camera_Start(int,void*) {}
void Camera_Stop(int,void*) {}
void Camera_CaptureFrame(int,u32* f,int w,int h,bool,void*) { memset(f,0,w*h*4); }
void Mic_Start(void*) {}
void Mic_Stop(void*) {}
int Mic_ReadInput(s16* d,int n,void*) { memset(d,0,n*2);return n; }
AACDecoder* AAC_Init() { return nullptr; }
void AAC_DeInit(AACDecoder*) {}
bool AAC_Configure(AACDecoder*,int,int) { return false; }
bool AAC_DecodeFrame(AACDecoder*,const void*,int,void*,int) { return false; }
bool Addon_KeyDown(KeyType,void*) { return false; }
void Addon_RumbleStart(u32,void*) {}
void Addon_RumbleStop(void*) {}
float Addon_MotionQuery(MotionQueryType,void*) { return 0; }
DynamicLibrary* DynamicLibrary_Load(const char* p) { return reinterpret_cast<DynamicLibrary*>(dlopen(p,RTLD_NOW)); }
void DynamicLibrary_Unload(DynamicLibrary* p) { dlclose(p); }
void* DynamicLibrary_LoadFunction(DynamicLibrary* p,const char* s) { return dlsym(p,s); }
}
