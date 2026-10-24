#include "NDS.h"
#include "Args.h"
#include "GPU3D_Soft.h"
#include "Savestate.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <thread>
#include <stdexcept>
#include <cstring>
#include <barrier>
#include <cstdlib>
#include <atomic>
#include <chrono>
#include <mutex>
#include <algorithm>
#include <filesystem>

using namespace melonDS;
namespace melonDS::Platform { void SetMPRecvTimeout(int timeout); }
static std::vector<u8> readfile(const std::string& name) {
    std::ifstream f(name,std::ios::binary);
    if(!f)throw std::runtime_error("Cannot read "+name);
    return {std::istreambuf_iterator<char>(f),{}};
}
template<class T>static void bios(T& a,const std::string& path) {
    auto b=readfile(path);if(b.size()!=a.size())throw std::runtime_error("Wrong BIOS size");
    std::memcpy(a.data(),b.data(),b.size());
}
static void image(NDS& ds,const std::string& path) {
    std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Cannot write image");
    f<<"P6\n256 384\n255\n";
    for(int screen=0;screen<2;screen++) {
        auto p=ds.GPU.Framebuffer[ds.GPU.FrontBuffer][screen].get();
        for(int n=0;n<256*192;n++) { auto c=p[n];f.put((c>>16)&255);f.put((c>>8)&255);f.put(c&255); }
    }
}
struct LiveWorkers {
    std::atomic<bool> stop{false};
    std::vector<std::thread> threads;
    void finish() {
        if(threads.empty())return;
        stop=true;
        // Wake peers waiting for host packets before joining the workers.
        for(size_t i=0;i<threads.size();i++)Platform::MP_End(reinterpret_cast<void*>(i));
        for(auto& t:threads)t.join();
        threads.clear();
    }
    ~LiveWorkers() { finish(); }
};
int main(int argc,char** argv) try {
    if(argc<2) { std::cerr<<"usage: melon-test ROM|- [ROM|- ...] < commands\n";return 1; }
    const char* configured = std::getenv("COOP_INPUT_DIR");
    const std::string inputs = configured ? configured : "/workspace/inputs";
    std::vector<std::unique_ptr<NDS>> consoles;
    std::vector<std::atomic<unsigned long>> frames(argc-1);
    std::vector<std::atomic<bool>> running(argc-1);
    for(int i=1;i<argc;i++) {
        NDSArgs a;
        bios(*a.ARM9BIOS,inputs + "/bios9.bin");
        bios(*a.ARM7BIOS,inputs + "/bios7.bin");
        auto firmware=readfile(inputs + "/firmware-original.bin");
        a.Firmware=Firmware(firmware.data(),firmware.size());
        a.Firmware.GetHeader().MacAddr[5]+=i;
        a.Firmware.UpdateChecksums();
        a.JIT=std::nullopt;
#ifdef JIT_ENABLED
        if(std::getenv("COOP_JIT")) {
            a.JIT=JITArgs();
            a.JIT->FastMemory=false;
        }
#else
        if(std::getenv("COOP_JIT"))throw std::runtime_error("Frontend built without JIT support");
#endif
#ifdef GDBSTUB_ENABLED
        if(i==2)if(const char* port=std::getenv("COOP_GDB_START_ARM9")) {
            GDBArgs debug;
            debug.PortARM9=std::stoi(port);
            if(const char* arm7=std::getenv("COOP_GDB_START_ARM7"))debug.PortARM7=std::stoi(arm7);
            a.GDB=debug;
        }
#endif
        auto ds=std::make_unique<NDS>(std::move(a),reinterpret_cast<void*>(uintptr_t(i-1)));
        if(std::string(argv[i])!="-") {
            auto rom=readfile(argv[i]);
            auto cart=NDSCart::ParseROM(rom.data(),rom.size(),reinterpret_cast<void*>(uintptr_t(i-1)));
            if(!cart)throw std::runtime_error("ROM parse failed");
            if(const char* directory=std::getenv("COOP_SAVE_DIR")) {
                std::filesystem::create_directories(directory);
                const auto path=std::filesystem::path(directory)/("console-"+std::to_string(i-1)+".sav");
                if(std::filesystem::exists(path)) {
                    auto saved=readfile(path.string());
                    if(saved.size()!=cart->GetSaveMemoryLength())
                        throw std::runtime_error("Test cartridge save size differs from ROM backup size");
                    cart->SetSaveMemory(saved.data(),saved.size());
                }
            }
            ds->SetNDSCart(std::move(cart));
        }
        ds->Reset();
        ds->RTC.SetDateTime(2026,10,21,12,0,0);
        if(std::string(argv[i])!="-")ds->SetupDirectBoot(argv[i]);
        ds->Start();
        consoles.push_back(std::move(ds));running[i-1]=true;
    }
    std::vector<std::mutex> locks(consoles.size());
    LiveWorkers live;
    const bool realtime=std::getenv("COOP_LIVE")!=nullptr;
    unsigned frameMicros=16667;
    unsigned maxFrameLead=0;
    if(const char* lead=std::getenv("COOP_MAX_FRAME_LEAD")) {
        maxFrameLead=std::stoul(lead);
        if(maxFrameLead>120)throw std::runtime_error("COOP_MAX_FRAME_LEAD must be between 0 and 120");
    }
    if(const char* pace=std::getenv("COOP_FRAME_US")) {
        frameMicros=std::stoul(pace);
        if(frameMicros<1000 || frameMicros>1000000)
            throw std::runtime_error("COOP_FRAME_US must be between 1000 and 1000000");
    }
    if(realtime)for(size_t i=0;i<consoles.size();i++)live.threads.emplace_back([&,i]{
        auto next=std::chrono::steady_clock::now();
        while(!live.stop) {
            // A delayed wireless RunFrame must not leave the other consoles
            // seconds ahead and overwrite LocalMP's finite packet queue.
            // Leave several frames of slack: a barrier after every frame can
            // deadlock a core waiting for a peer's next wireless event.
            if(maxFrameLead) {
                auto slowest=frames[i].load();
                for(size_t peer=0;peer<consoles.size();++peer)
                    if(running[peer])slowest=std::min(slowest,frames[peer].load());
                if(frames[i].load()>=slowest+maxFrameLead) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                    next=std::chrono::steady_clock::now();
                    continue;
                }
            }
            {
                std::lock_guard lock(locks[i]);
                if(consoles[i]->IsRunning()){consoles[i]->RunFrame();++frames[i];}
                running[i]=consoles[i]->IsRunning();
            }
            next+=std::chrono::microseconds(frameMicros);
            const auto now=std::chrono::steady_clock::now();
            if(now-next>std::chrono::milliseconds(250))next=now;
            // A wireless RunFrame can exceed its deadline. Give command
            // handlers a chance to take the per-console mutex in that case.
            if(next>now)std::this_thread::sleep_until(next);
            else std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    });
    std::string line;
    while(std::getline(std::cin,line)) {
        if(line.empty()||line[0]=='#')continue;
        std::istringstream s(line);std::string cmd;s>>cmd;
        if(cmd=="mptimeout") {
            int timeout;if(!(s>>timeout)||timeout<0||timeout>10000)throw std::runtime_error("Bad MP timeout");
            // LocalMP's setting is not atomic. Change it only while every
            // console is between frames, without modifying the core or packets.
            std::vector<std::unique_lock<std::mutex>> held;
            const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);
            while(held.size()!=locks.size()) {
                held.clear();
                for(auto& mutex:locks) {
                    held.emplace_back(mutex,std::try_to_lock);
                    if(!held.back().owns_lock()){held.clear();break;}
                }
                if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("Could not pause cores to set MP timeout");
                if(held.empty())std::this_thread::yield();
            }
            Platform::SetMPRecvTimeout(timeout);
        } else if(cmd=="run") {
            unsigned n;if(!(s>>n)||n>36000)throw std::runtime_error("Bad frame count");
            if(realtime) {
                std::vector<unsigned long> targets;
                for(size_t i=0;i<consoles.size();i++)targets.push_back(frames[i].load()+n);
                auto lastReport=std::chrono::steady_clock::now();
                std::vector<unsigned long> previous(consoles.size());
                std::vector<std::chrono::steady_clock::time_point> changed(consoles.size(),lastReport);
                bool complete=false;
                while(!complete) {
                    complete=true;
                    const auto now=std::chrono::steady_clock::now();
                    for(size_t i=0;i<consoles.size();i++) {
                        const auto frame=frames[i].load();
                        if(frame!=previous[i]){previous[i]=frame;changed[i]=now;}
                        if(running[i] && frame<targets[i]) {
                            complete=false;
                            if(now-changed[i]>std::chrono::seconds(60)) {
                                std::cerr<<"Frame stalled on console "<<i<<" at "<<frame<<std::endl;
                                // A stuck core owns its mutex. Capture only
                                // peers we can lock safely, without touching
                                // the stalled core's live emulated state.
                                if(const char* directory=std::getenv("COOP_STALL_DUMP_DIR")) {
                                    for(size_t peer=0;peer<consoles.size();peer++) {
                                        std::unique_lock capture(locks[peer],std::try_to_lock);
                                        if(!capture.owns_lock())continue;
                                        auto& core=*consoles[peer];
                                        std::string prefix=std::string(directory)+"/stalled-peer-"+std::to_string(peer);
                                        std::ofstream ram(prefix+".ram",std::ios::binary);
                                        ram.write(reinterpret_cast<char*>(core.MainRAM),0x400000);
                                        std::ofstream tcm(prefix+".dtcm",std::ios::binary);
                                        tcm.write(reinterpret_cast<char*>(core.ARM9.DTCM),0x4000);
                                        std::cerr<<"Captured peer "<<peer<<" ARM9 PC "<<std::hex<<core.ARM9.R[15]
                                                 <<" ARM7 PC "<<core.ARM7.R[15]<<std::dec<<std::endl;
                                    }
                                }
                                throw std::runtime_error("A console made no frame progress for 60 seconds");
                            }
                        }
                    }
                    if(now-lastReport>std::chrono::seconds(5)) {
                        std::cout<<"progress run "<<n;
                        for(size_t i=0;i<consoles.size();i++)std::cout<<" console="<<i<<":"<<frames[i].load()<<"/"<<targets[i];
                        std::cout<<std::endl;
                        lastReport=now;
                    }
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            } else {
            std::vector<std::thread> workers;
            std::barrier gate(static_cast<std::ptrdiff_t>(consoles.size()));
            for(size_t i=0;i<consoles.size();i++)workers.emplace_back([&,i]{for(unsigned f=0;f<n;f++){if(consoles[i]->IsRunning()){consoles[i]->RunFrame();++frames[i];}gate.arrive_and_wait();}});
            for(auto& t:workers)t.join();
            }
        } else if(cmd=="status") {
            for(size_t i=0;i<consoles.size();i++){std::lock_guard lock(locks[i]);std::cout<<"console="<<i<<" frame="<<frames[i]<<" running="<<consoles[i]->IsRunning()<<" arm9pc="<<std::hex<<consoles[i]->ARM9.R[15]<<" arm7pc="<<consoles[i]->ARM7.R[15]<<std::dec<<"\n";}
        } else {
            unsigned i;if(!(s>>i)||i>=consoles.size())throw std::runtime_error("Bad console index");
            std::lock_guard lock(locks[i]);
            auto& ds=*consoles[i];
            if(cmd=="touch") { unsigned x,y;if(!(s>>x>>y)||x>255||y>191)throw std::runtime_error("Bad touch");ds.TouchScreen(x,y); }
            else if(cmd=="release")ds.ReleaseScreen();
            else if(cmd=="keys") { unsigned k;if(!(s>>std::hex>>k))throw std::runtime_error("Bad key mask");ds.SetKeyMask(k); }
            else if(cmd=="poweroff") {
                // Remove a console like closing its emulator window. Peers
                // must detect the missing radio through the normal transport;
                // no RAM, registers, receive buffers or packets are injected.
                ds.Stop(Platform::StopReason::PowerOff);
                Platform::MP_End(reinterpret_cast<void*>(i));
                running[i]=false;
            }
#ifdef GDBSTUB_ENABLED
            else if(cmd=="gdb") { unsigned port;if(!(s>>port)||port>65535)throw std::runtime_error("Bad GDB port");GDBArgs args;args.PortARM9=port;ds.SetGdbArgs(args); }
#endif
            else if(cmd=="screen") { std::string p;s>>p;image(ds,p); }
            else if(cmd=="dumpcart") {
                std::string path;s>>path;
                const auto length=ds.GetNDSSaveLength();
                const auto data=ds.GetNDSSave();
                if(!data || !length)throw std::runtime_error("Console has no cartridge backup memory");
                std::ofstream file(path,std::ios::binary);
                file.write(reinterpret_cast<const char*>(data),length);
                if(!file)throw std::runtime_error("Cannot capture cartridge backup memory");
            }
            else if(cmd=="dumpwifi") {
                // Capture only; never load a state or alter the transport.
                std::string path;s>>path;
                Savestate capture(0x10000);
                ds.Wifi.DoSavestate(&capture);
                capture.Finish();
                if(capture.Error)throw std::runtime_error("Cannot capture wireless state");
                std::ofstream file(path,std::ios::binary);
                file.write(reinterpret_cast<const char*>(capture.Buffer()),capture.Length());
                if(!file)throw std::runtime_error("Cannot write wireless state capture");
            }
            else if(cmd=="read") { unsigned addr,n;s>>std::hex>>addr>>std::dec>>n;if(addr<0x02000000||addr+n>0x02400000||n>1024)throw std::runtime_error("Read outside main RAM");std::cout<<"RAM "<<i<<" "<<std::hex<<addr<<":";for(unsigned j=0;j<n;j++)std::cout<<" "<<unsigned(ds.MainRAM[(addr+j)&ds.MainRAMMask]);std::cout<<std::dec<<"\n"; }
            else if(cmd=="regs") {
                for(int reg=0;reg<16;reg++)std::cout<<"r"<<reg<<"="<<std::hex<<ds.ARM9.R[reg]<<" ";
                std::cout<<"arm7:";for(int reg=0;reg<16;reg++)std::cout<<" r"<<reg<<"="<<std::hex<<ds.ARM7.R[reg]<<" ";
                std::cout<<"dtcm="<<ds.ARM9.DTCMBase<<std::dec<<"\n";
                std::cout<<"irq9: ime="<<std::hex<<ds.ARM9Read32(0x04000208)
                         <<" ie="<<ds.ARM9Read32(0x04000210)<<" if="<<ds.ARM9Read32(0x04000214)
                         <<" dispstat="<<ds.ARM9Read16(0x04000004)<<" vcount="<<ds.ARM9Read16(0x04000006)
                         <<" cpustop="<<ds.CPUStop<<" cpsr9="<<ds.ARM9.CPSR<<" cpsr7="<<ds.ARM7.CPSR
                         <<std::dec<<"\n";
                u32 sp=ds.ARM9.R[13];
                for(unsigned word=0;word<64;word++) {
                    u32 address=sp+word*4,value=0;
                    if((address&ds.ARM9.DTCMMask)==ds.ARM9.DTCMBase)std::memcpy(&value,ds.ARM9.DTCM+(address&0x3fff),4);
                    else if(address>=0x02000000&&address<0x02400000)std::memcpy(&value,ds.MainRAM+(address&ds.MainRAMMask),4);
                    std::cout<<std::hex<<address<<":"<<value<<" ";
                }
                std::cout<<std::dec<<"\n";
                u32 subsp=ds.ARM7.R[13];
                if(subsp>=0x02000000 && subsp+256<0x04000000) {
                    for(unsigned word=0;word<64;word++) {
                        u32 address=subsp+word*4;
                        std::cout<<std::hex<<address<<":"<<ds.ARM7Read32(address)<<" ";
                    }
                    std::cout<<std::dec<<"\n";
                }
            }
            else if(cmd=="dump") { std::string path;s>>path;std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<char*>(ds.MainRAM),0x400000); }
            else if(cmd=="dumptcm") {
                std::string path;s>>path;std::ofstream out(path,std::ios::binary);
                out.write(reinterpret_cast<char*>(ds.ARM9.DTCM),0x4000);
            }
            else if(cmd=="dump7") {
                std::string path;s>>path;std::ofstream out(path,std::ios::binary);
                for(u32 address=0x037f8000;address<0x03810000;++address)out.put(ds.ARM7Read8(address));
            }
            else if(cmd=="savesram") { std::string path;s>>path;std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(ds.GetNDSSave()),ds.GetNDSSaveLength()); }
            else if(cmd=="loadsram") { std::string path;s>>path;auto b=readfile(path);ds.SetNDSSave(b.data(),b.size()); }
            else throw std::runtime_error("Unknown command: "+cmd);
        }
        std::cout<<"done "<<line<<std::endl;
    }
    live.finish();
    bool stopped=false;
    for(auto& ds:consoles) { stopped|=!ds->IsRunning();ds->Stop(); }
    return stopped?2:0;
} catch(const std::exception& e) { std::cerr<<e.what()<<"\n";return 1; }
