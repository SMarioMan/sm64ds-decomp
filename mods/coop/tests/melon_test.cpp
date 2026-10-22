#include "NDS.h"
#include "Args.h"
#include "GPU3D_Soft.h"
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

using namespace melonDS;
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
    std::vector<unsigned long> frames;
    for(int i=1;i<argc;i++) {
        NDSArgs a;
        bios(*a.ARM9BIOS,inputs + "/bios9.bin");
        bios(*a.ARM7BIOS,inputs + "/bios7.bin");
        auto firmware=readfile(inputs + "/firmware-original.bin");
        a.Firmware=Firmware(firmware.data(),firmware.size());
        a.Firmware.GetHeader().MacAddr[5]+=i;
        a.Firmware.UpdateChecksums();
        a.JIT=std::nullopt;
        auto ds=std::make_unique<NDS>(std::move(a),reinterpret_cast<void*>(uintptr_t(i-1)));
        if(std::string(argv[i])!="-") {
            auto rom=readfile(argv[i]);
            auto cart=NDSCart::ParseROM(rom.data(),rom.size(),reinterpret_cast<void*>(uintptr_t(i-1)));
            if(!cart)throw std::runtime_error("ROM parse failed");
            ds->SetNDSCart(std::move(cart));
        }
        ds->Reset();
        ds->RTC.SetDateTime(2026,10,21,12,0,0);
        if(std::string(argv[i])!="-")ds->SetupDirectBoot(argv[i]);
        ds->Start();
        consoles.push_back(std::move(ds));frames.push_back(0);
    }
    std::vector<std::mutex> locks(consoles.size());
    LiveWorkers live;
    const bool realtime=std::getenv("COOP_LIVE")!=nullptr;
    if(realtime)for(size_t i=0;i<consoles.size();i++)live.threads.emplace_back([&,i]{
        auto next=std::chrono::steady_clock::now();
        while(!live.stop) {
            { std::lock_guard lock(locks[i]);if(consoles[i]->IsRunning()){consoles[i]->RunFrame();++frames[i];} }
            next+=std::chrono::microseconds(16667);
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
        if(cmd=="run") {
            unsigned n;if(!(s>>n)||n>36000)throw std::runtime_error("Bad frame count");
            if(realtime) {
                std::vector<unsigned long> targets;
                for(size_t i=0;i<consoles.size();i++){std::lock_guard lock(locks[i]);targets.push_back(frames[i]+n);}
                bool complete=false;
                while(!complete){complete=true;for(size_t i=0;i<consoles.size();i++){std::lock_guard lock(locks[i]);if(consoles[i]->IsRunning()&&frames[i]<targets[i])complete=false;}std::this_thread::sleep_for(std::chrono::milliseconds(10));}
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
            else if(cmd=="screen") { std::string p;s>>p;image(ds,p); }
            else if(cmd=="read") { unsigned addr,n;s>>std::hex>>addr>>std::dec>>n;if(addr<0x02000000||addr+n>0x02400000||n>1024)throw std::runtime_error("Read outside main RAM");std::cout<<"RAM "<<i<<" "<<std::hex<<addr<<":";for(unsigned j=0;j<n;j++)std::cout<<" "<<unsigned(ds.MainRAM[(addr+j)&ds.MainRAMMask]);std::cout<<std::dec<<"\n"; }
            else if(cmd=="regs") {
                for(int reg=0;reg<16;reg++)std::cout<<"r"<<reg<<"="<<std::hex<<ds.ARM9.R[reg]<<" ";
                std::cout<<"dtcm="<<ds.ARM9.DTCMBase<<std::dec<<"\n";
                u32 sp=ds.ARM9.R[13];
                for(unsigned word=0;word<64;word++) {
                    u32 address=sp+word*4,value=0;
                    if((address&ds.ARM9.DTCMMask)==ds.ARM9.DTCMBase)std::memcpy(&value,ds.ARM9.DTCM+(address&0x3fff),4);
                    else if(address>=0x02000000&&address<0x02400000)std::memcpy(&value,ds.MainRAM+(address&ds.MainRAMMask),4);
                    std::cout<<std::hex<<address<<":"<<value<<" ";
                }
                std::cout<<std::dec<<"\n";
            }
            else if(cmd=="dump") { std::string path;s>>path;std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<char*>(ds.MainRAM),0x400000); }
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
