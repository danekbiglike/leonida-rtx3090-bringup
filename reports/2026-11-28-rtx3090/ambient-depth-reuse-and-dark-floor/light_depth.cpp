#include "d3d_test.hpp"
#include <set>

constexpr UINT cellBytes = (2 * 64 * 36 + 1 + 25 * 64 * 36) * 16;
constexpr UINT pointCount = 160 * 90;
using Pso = ComPtr<ID3D12PipelineState>;

struct Programs {
    Pso gather, diffuse, reflection;
};

struct Capture {
    std::vector<uint32_t> pixels, cells;
    double gatherUs, finishUs;
};

// The fixture varies depth, incoming light, discontinuities and sky coverage.
// The renderer's gather and both output shaders are loaded from disk verbatim.
static const char* seedSource = R"(
#ifdef SEED_WORLD
RWTexture2D<float> seedImage : register(u0);
#elif defined(SEED_DIFFUSE)
RWTexture2D<uint> seedImage : register(u0);
#else
RWTexture2D<float3> seedImage : register(u0);
#endif
[RootSignature(RS)] [numthreads(8,8,1)]
void seed(uint3 at : SV_DispatchThreadID) {
    uint w,h; seedImage.GetDimensions(w,h);
    if (at.x >= w || at.y >= h) return;
    uint scene = (uint)level;
    uint i = at.y*w + at.x;
#ifdef SEED_WORLD
    float z = 1.5 + 0.002*at.x + 0.004*at.y + ((at.x/93 + at.y/117 + scene) % 4)*1.7;
    if (scene == 2) z = 0.85 + (at.x % 197)*0.026 + (at.y % 61)*0.011;
    seedImage[at.xy] = (at.x > w / 2 && at.y < h / 11) ? 0 : 0.1/z;
    if (i<CELLS) {
        float cz = 1.2 + (i % 118)*0.085;
        cells[i] = float4(float3(0.02+(i%11)*0.12,0.04+(i%19)*0.036,0.03+(i%23)*0.06*scene) * (scene==3?0.01:1.0),1);
        cells[CELLS+1+i] = float4(((i%CX)-31.5)*cz/64.0, ((i/CX)-17.5)*cz/64.0,cz,cz*cz);
    }
    if (i==0) cells[CELLS]=float4(float3(0.25,0.38,0.19)*(scene==3?0.01:1.0),1);
    if (i<CELLS*25) cells[SHARES+i]=float4(-1.0,0,0,0);
#elif defined(SEED_DIFFUSE)
    seedImage[at.xy] = ((i%5)==1) ? 0x79a0a117u : 0;
#else
    seedImage[at.xy] = float3(0.1,0.08,0.04) * (1+(i%5));
#endif
})";

struct Test {
    Gpu gpu;
    ComPtr<ID3D12RootSignature> root;
    ComPtr<ID3D12DescriptorHeap> heap;
    ComPtr<ID3D12QueryHeap> ticks;
    UINT step;
    UINT candidateWidth;
    bool floorTest;
    std::array<UINT,2> strides{};
    std::array<Programs,2> programs;
    Pso seedWorld, seedDiffuse, seedReflection;

    Pso pipeline(const std::string& src, const char* entry) {
        const auto blob = compile(src, entry);
        if (!root) check(gpu.device->CreateRootSignature(0,blob->GetBufferPointer(),blob->GetBufferSize(),IID_PPV_ARGS(&root)));
        D3D12_COMPUTE_PIPELINE_STATE_DESC desc{};
        desc.pRootSignature = root.Get();
        desc.CS = {blob->GetBufferPointer(), blob->GetBufferSize()};
        Pso p;
        check(gpu.device->CreateComputePipelineState(&desc, IID_PPV_ARGS(&p)));
        return p;
    }
    Test(const std::string& original, const std::string& candidate, UINT width, bool floor) : candidateWidth(width), floorTest(floor) {
        if (width != 8 && candidate.find("numthreads(GATHER_WIDTH, 2, 1)") == candidate.npos)
            throw std::runtime_error("candidate does not support a configurable gather width");
        const std::array<std::string,2> sources{original,candidate};
        for (size_t i=0; i<sources.size(); ++i) {
            if (floorTest && sources[i].find("num32BitConstants=13") == sources[i].npos)
                throw std::runtime_error("light floor probe expects the renderer with 13 root constants");
            strides[i] = sources[i].find("points[at0 + 3] = float4(p.z") != sources[i].npos ? 64 : 48;
            const std::string group = i == 0 ? "" : "#define GATHER_WIDTH " + std::to_string(width) + "\n";
            programs[i] = {pipeline("#define GATHER\n" + group + sources[i],"gather"),
                           pipeline("#define RAISE\n" + sources[i],"raise"),
                           pipeline("#define REFLECT\n" + sources[i],"reflect_light")};
        }
        seedWorld = pipeline("#define SEED_WORLD\n"+original+seedSource,"seed");
        seedDiffuse = pipeline("#define SEED_DIFFUSE\n"+original+seedSource,"seed");
        seedReflection = pipeline(original+seedSource,"seed");
        D3D12_DESCRIPTOR_HEAP_DESC hd{D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV,3,D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE,0};
        check(gpu.device->CreateDescriptorHeap(&hd,IID_PPV_ARGS(&heap)));
        step = gpu.device->GetDescriptorHandleIncrementSize(hd.Type);
        D3D12_QUERY_HEAP_DESC qd{D3D12_QUERY_HEAP_TYPE_TIMESTAMP,3,0};
        check(gpu.device->CreateQueryHeap(&qd,IID_PPV_ARGS(&ticks)));
    }
    D3D12_CPU_DESCRIPTOR_HANDLE cpu(UINT i) {
        auto h=heap->GetCPUDescriptorHandleForHeapStart(); h.ptr += i*step; return h;
    }
    D3D12_GPU_DESCRIPTOR_HANDLE handle(UINT i) {
        auto h=heap->GetGPUDescriptorHandleForHeapStart(); h.ptr += i*step; return h;
    }
};

static void measure(Test& t, UINT width, UINT height, bool reflect) {
    auto& g = t.gpu;
    const UINT w = reflect ? (width+1)/2 : width, h = reflect ? (height+1)/2 : height;
    auto depth = g.resource(0,false,DXGI_FORMAT_R32_FLOAT,width,height);
    auto output = g.resource(0,false,reflect ? DXGI_FORMAT_R11G11B10_FLOAT : DXGI_FORMAT_R32_UINT,w,h);
    auto cells = g.resource(cellBytes);
    std::array<ComPtr<ID3D12Resource>,2> points{g.resource(pointCount*t.strides[0]),g.resource(pointCount*t.strides[1])};
    t.gpu.device->CreateShaderResourceView(depth.Get(),nullptr,t.cpu(0));
    t.gpu.device->CreateUnorderedAccessView(depth.Get(),nullptr,nullptr,t.cpu(1));
    t.gpu.device->CreateUnorderedAccessView(output.Get(),nullptr,nullptr,t.cpu(2));
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT fp{};
    UINT64 bytes{};
    const auto desc=output->GetDesc();
    g.device->GetCopyableFootprints(&desc,0,1,0,&fp,nullptr,nullptr,&bytes);
    const UINT64 cellsAt=(bytes+255) & ~UINT64(255), timesAt=cellsAt+cellBytes;
    auto back=g.resource(timesAt+24,true);
    auto capture=[&](int scene, int variant) -> Capture {
        auto& list=g.list;
        ID3D12DescriptorHeap* heaps[]{t.heap.Get()};
        list->SetDescriptorHeaps(1,heaps);
        list->SetComputeRootSignature(t.root.Get());
        list->SetComputeRootDescriptorTable(1,t.handle(0));
        list->SetComputeRootUnorderedAccessView(3,cells->GetGPUVirtualAddress());
        list->SetComputeRootUnorderedAccessView(4,points[variant]->GetGPUVirtualAddress());
        UINT words[13]{};
        const float settings[]{float(scene),0.0f,0.85f,1.4f,0.1f,0.45f};
        std::memcpy(words,settings,sizeof(settings));
        words[6]=width; words[7]=height;
        const float extra[]{0.04f,4.0f,0.1f,1.0f};
        std::memcpy(words+8,extra,sizeof(extra));
        const float floor=t.floorTest && variant ? 0.05f : 0.0f;
        std::memcpy(words+12,&floor,4);
        const UINT count=t.floorTest ? 13 : 12;
        list->SetComputeRoot32BitConstants(0,count,words,0);
        list->SetComputeRootDescriptorTable(2,t.handle(1));
        list->SetPipelineState(t.seedWorld.Get()); list->Dispatch((width+7)/8,(height+7)/8,1); g.barrier();
        list->SetComputeRootDescriptorTable(2,t.handle(2));
        list->SetPipelineState(reflect?t.seedReflection.Get():t.seedDiffuse.Get());
        list->Dispatch((w+7)/8,(h+7)/8,1); g.barrier();
        const float scale = 1.0f, retainedSky = reflect ? 0.35f : 0.0f;
        std::memcpy(words,&scale,4); std::memcpy(words+1,&retainedSky,4);
        list->SetComputeRoot32BitConstants(0,count,words,0);
        g.transition(depth.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);
        list->EndQuery(t.ticks.Get(),D3D12_QUERY_TYPE_TIMESTAMP,0);
        list->SetPipelineState(t.programs[variant].gather.Get());
        list->Dispatch(160 / (variant ? t.candidateWidth : 8),45,1); g.barrier();
        list->EndQuery(t.ticks.Get(),D3D12_QUERY_TYPE_TIMESTAMP,1);
        list->SetPipelineState(reflect?t.programs[variant].reflection.Get():t.programs[variant].diffuse.Get());
        list->Dispatch((w+7)/8,(h+7)/8,1); g.barrier();
        list->EndQuery(t.ticks.Get(),D3D12_QUERY_TYPE_TIMESTAMP,2);
        list->ResolveQueryData(t.ticks.Get(),D3D12_QUERY_TYPE_TIMESTAMP,0,3,back.Get(),timesAt);
        g.transition(output.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE);
        g.transition(cells.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE);
        D3D12_TEXTURE_COPY_LOCATION to{},from{};
        to.pResource=back.Get(); to.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT; to.PlacedFootprint=fp;
        from.pResource=output.Get(); from.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        list->CopyTextureRegion(&to,0,0,0,&from,nullptr);
        list->CopyBufferRegion(back.Get(),cellsAt,cells.Get(),0,cellBytes);
        g.transition(output.Get(),D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
        g.transition(cells.Get(),D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
        g.transition(depth.Get(),D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
        g.submit();
        Capture c;
        c.pixels.resize(size_t(w)*h); c.cells.resize(cellBytes/4);
        void* mapped=nullptr;
        D3D12_RANGE range{0,static_cast<SIZE_T>(timesAt+24)}, none{};
        check(back->Map(0,&range,&mapped));
        auto data=static_cast<const uint8_t*>(mapped);
        for (UINT y=0;y<h;++y) std::memcpy(c.pixels.data()+size_t(y)*w,data+fp.Offset+UINT64(y)*fp.Footprint.RowPitch,w*4);
        std::memcpy(c.cells.data(),data+cellsAt,cellBytes);
        UINT64 stamp[3]; std::memcpy(stamp,data+timesAt,24); back->Unmap(0,&none);
        if (!(stamp[0]<stamp[1] && stamp[1]<stamp[2])) throw std::runtime_error("nonmonotonic GPU timestamps");
        c.gatherUs=(stamp[1]-stamp[0])*1e6/g.frequency; c.finishUs=(stamp[2]-stamp[1])*1e6/g.frequency;
        return c;
    };
    for (int scene=1;scene<=(t.floorTest ? 3 : 2);++scene) {
        auto original=capture(scene,0);
        std::set<uint32_t> colors;
        for (size_t i=0;i<original.pixels.size();i+=101) colors.insert(original.pixels[i]);
        if (colors.size()<64) throw std::runtime_error("reference did not render the varied scene");
        if (t.floorTest) {
            const auto raised=capture(scene,1);
            const auto shareStart=(2*64*36+1)*4;
            if (!std::equal(original.cells.begin(),original.cells.begin()+shareStart,raised.cells.begin()))
                throw std::runtime_error("light floor changed input cell lighting or positions");
            unsigned changed=0;
            for (size_t i=0;i<original.pixels.size();++i) {
                if (original.pixels[i]==raised.pixels[i]) continue;
                if (reflect) throw std::runtime_error("diffuse light floor changed reflections");
                const auto a=original.pixels[i], b=raised.pixels[i];
                const float sa=std::ldexp(1.0f,int(a>>27)-24), sb=std::ldexp(1.0f,int(b>>27)-24);
                const float channels[]{0.05f,0.05f*0.98f,0.05f*0.94f};
                bool wasDark=false;
                for (int k=0;k<3;++k) {
                    const float old=((a>>(9*k))&511)*sa, now=((b>>(9*k))&511)*sb;
                    wasDark |= old <= channels[k] + 0.5f*sa;
                    if (now + 0.5f*(sa+sb) < old) throw std::runtime_error("a channel became darker beyond quantization");
                }
                if (!wasDark) throw std::runtime_error("floor changed an already lit pixel");
                ++changed;
            }
            if (!reflect && scene==3 && changed < w*h/4) throw std::runtime_error("dim scene did not exercise the floor");
            std::printf("%u,%u,%u,%u,%s,%d,%zu,%u\n",width,height,w,h,reflect?"reflection":"diffuse",scene,original.pixels.size(),changed);
            continue;
        }
        for (int round=-1;round<7;++round) {
            for (int order=0;order<2;++order) {
                const int v=(round+1+order)%2;
                auto c=capture(scene,v);
                if (c.pixels!=original.pixels || c.cells!=original.cells) {
                    auto pixel=std::mismatch(c.pixels.begin(),c.pixels.end(),original.pixels.begin());
                    std::fprintf(stderr,"Mismatch: %ux%u scene %d reflect %d variant %d, pixel offset %zu, cells equal %d\n",
                                 w,h,scene,reflect,v,size_t(pixel.first-c.pixels.begin()),int(c.cells==original.cells));
                    throw std::runtime_error("lighting readback differs");
                }
                if (round>=0) std::printf("%u,%u,%u,%u,%s,%d,%d,%d,%.3f,%.3f,%zu,%u\n",width,height,w,h,
                    reflect?"reflection":"diffuse",scene,round,v,c.gatherUs,c.finishUs,c.pixels.size()*4,cellBytes);
            }
        }
    }
}

int wmain(int argc,wchar_t** argv) {
    if (argc<3 || argc>5) return 2;
    try {
        const UINT width = argc < 4 ? 8 : std::stoul(argv[3]);
        if (width != 8 && width != 16 && width != 32) return 2;
        const bool floor=argc==5 && std::wstring(argv[4])==L"floor";
        if (argc==5 && !floor) return 2;
        Test test(shader_source(argv[1]),shader_source(argv[2]),width,floor);
        std::puts(floor ? "depth_w,depth_h,output_w,output_h,pass,scene,pixels,changed_pixels" :
            "depth_w,depth_h,output_w,output_h,pass,scene,round,cached,gather_us,resolve_us,compared_pixel_bytes,compared_cell_bytes");
        for (auto size : {std::pair<UINT,UINT>{1297,733},{2560,1440},{3840,2160}})
            for (bool reflect : {false,true}) measure(test,size.first,size.second,reflect);
        return 0;
    } catch (const std::exception& e) {std::fprintf(stderr,"%s\n",e.what());return 1;}
}
