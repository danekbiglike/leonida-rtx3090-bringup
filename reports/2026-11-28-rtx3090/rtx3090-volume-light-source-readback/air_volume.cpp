#define NOMINMAX
#include "d3d_test.hpp"

constexpr UINT W=160, H=90, D=17;
using Resource=ComPtr<ID3D12Resource>;
using Pipeline=ComPtr<ID3D12PipelineState>;

static const char* seed = R"(
RWTexture3D<float3> initial : register(u0);
[RootSignature(RS)] [numthreads(8,8,2)]
void seed_air(uint3 p : SV_DispatchThreadID) {
    uint w,h,d; initial.GetDimensions(w,h,d);
    if (p.x>=w || p.y>=h || p.z>=d) return;
    uint scene=(uint)level, i=p.y*w+p.x;
    initial[p] = scene==4 ? float3(0.0625,0.09375,0.125) : float3(3,3,3);
    if (p.z!=0) return;
    if (i<CELLS) {
        float local = scene==3 ? 0.25+1.5*(i%CX)/(CX-1.0) : 1.0;
        cells[i]=float4(local,local,local,1);
    }
    if (i==0) cells[CELLS]=float4(1,1,1,1);
    float prior = scene==0 || scene==3 ? 1.0 : ((p.x+p.y+scene)%2 ? 0.25 : 1.75);
    for (int k=0;k<3;k++) points[i*4+k]=float4(0,0,0,prior);
}
)";

struct Test {
    Gpu gpu;
    ComPtr<ID3D12RootSignature> root;
    ComPtr<ID3D12DescriptorHeap> heap;
    Resource volume, cells, points, readback;
    D3D12_PLACED_SUBRESOURCE_FOOTPRINT footprint{};
    Pipeline init, reference, candidate;
    UINT step;

    Pipeline pipeline(const std::string& source, const char* entry) {
        auto code=compile(source,entry);
        if (!root) check(gpu.device->CreateRootSignature(0,code->GetBufferPointer(),code->GetBufferSize(),IID_PPV_ARGS(&root)));
        D3D12_COMPUTE_PIPELINE_STATE_DESC desc{};
        desc.pRootSignature=root.Get(); desc.CS={code->GetBufferPointer(),code->GetBufferSize()};
        Pipeline result; check(gpu.device->CreateComputePipelineState(&desc,IID_PPV_ARGS(&result))); return result;
    }
    Test(const std::string& oldAir,const std::string& newAir) {
        init=pipeline(oldAir+seed,"seed_air");
        reference=pipeline("#define AIR\n"+oldAir,"clear_air");
        candidate=pipeline("#define AIR\n"+newAir,"clear_air");
        cells=gpu.resource((2*64*36+1+25*64*36)*16);
        points=gpu.resource(160*90*64);
        D3D12_HEAP_PROPERTIES props{};props.Type=D3D12_HEAP_TYPE_DEFAULT;
        D3D12_RESOURCE_DESC desc{};desc.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE3D;
        desc.Width=W;desc.Height=H;desc.DepthOrArraySize=D;desc.MipLevels=1;
        desc.Format=DXGI_FORMAT_R11G11B10_FLOAT;desc.SampleDesc.Count=1;
        desc.Flags=D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
        check(gpu.device->CreateCommittedResource(&props,D3D12_HEAP_FLAG_NONE,&desc,
              D3D12_RESOURCE_STATE_UNORDERED_ACCESS,nullptr,IID_PPV_ARGS(&volume)));
        UINT64 bytes;gpu.device->GetCopyableFootprints(&desc,0,1,0,&footprint,nullptr,nullptr,&bytes);
        readback=gpu.resource(bytes,true);
        D3D12_DESCRIPTOR_HEAP_DESC hd{D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV,2,D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE,0};
        check(gpu.device->CreateDescriptorHeap(&hd,IID_PPV_ARGS(&heap)));
        step=gpu.device->GetDescriptorHandleIncrementSize(hd.Type);
        auto cpu=heap->GetCPUDescriptorHandleForHeapStart();
        D3D12_SHADER_RESOURCE_VIEW_DESC nullView{};nullView.Format=DXGI_FORMAT_R32_FLOAT;
        nullView.ViewDimension=D3D12_SRV_DIMENSION_TEXTURE2D;nullView.Texture2D.MipLevels=1;
        nullView.Shader4ComponentMapping=D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
        gpu.device->CreateShaderResourceView(nullptr,&nullView,cpu);cpu.ptr+=step;
        gpu.device->CreateUnorderedAccessView(volume.Get(),nullptr,nullptr,cpu);
    }
    std::vector<uint32_t> capture(int scene,Pipeline& pass) {
        auto& list=gpu.list;ID3D12DescriptorHeap* hs[]{heap.Get()};
        list->SetDescriptorHeaps(1,hs);list->SetComputeRootSignature(root.Get());
        auto handle=heap->GetGPUDescriptorHandleForHeapStart();list->SetComputeRootDescriptorTable(1,handle);
        handle.ptr+=step;list->SetComputeRootDescriptorTable(2,handle);
        list->SetComputeRootUnorderedAccessView(3,cells->GetGPUVirtualAddress());
        list->SetComputeRootUnorderedAccessView(4,points->GetGPUVirtualAddress());
        float words[13]{};words[0]=float(scene);words[10]=1.0f;
        list->SetComputeRoot32BitConstants(0,13,words,0);
        for(auto* p:{init.Get(),pass.Get()}) {
            list->SetPipelineState(p);list->Dispatch((W+7)/8,(H+7)/8,(D+1)/2);gpu.barrier();
        }
        gpu.transition(volume.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE);
        D3D12_TEXTURE_COPY_LOCATION src{},dst{};
        src.pResource=volume.Get();src.Type=D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
        dst.pResource=readback.Get();dst.Type=D3D12_TEXTURE_COPY_TYPE_PLACED_FOOTPRINT;dst.PlacedFootprint=footprint;
        list->CopyTextureRegion(&dst,0,0,0,&src,nullptr);
        gpu.transition(volume.Get(),D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
        gpu.submit();
        std::vector<uint32_t> data(W*H*D);
        void* mapped=nullptr;check(readback->Map(0,nullptr,&mapped));
        for(UINT row=0;row<H*D;row++) std::memcpy(data.data()+size_t(row)*W,
              static_cast<uint8_t*>(mapped)+footprint.Offset+size_t(row)*footprint.Footprint.RowPitch,W*4);
        D3D12_RANGE written{0,0};readback->Unmap(0,&written);
        return data;
    }
};

static float red(uint32_t pixel) {
    const unsigned bits=pixel&2047, exp=bits>>6, frac=bits&63;
    return exp ? std::ldexp(1.0f+frac/64.0f,int(exp)-15) : std::ldexp(float(frac),-20);
}

int wmain(int argc,wchar_t** argv) {
    if(argc!=3) return 2;
    try {
        Test t(shader_source(argv[1]),shader_source(argv[2]));
        std::puts("scene,voxels,different,reference_far_min,reference_far_max,candidate_far_min,candidate_far_max");
        std::vector<uint32_t> first;
        for(int scene=0;scene<=4;scene++) {
            auto before=t.capture(scene,t.reference),after=t.capture(scene,t.candidate);
            if(after!=t.capture(scene,t.candidate)) throw std::runtime_error("nondeterministic air output");
            size_t changed=0;float lo=4,hi=0,altLo=4,altHi=0;
            for(UINT z=0;z<D;z++) for(UINT y=0;y<H;y++) for(UINT x=0;x<W;x++) {
                const UINT i=(z*H+y)*W+x; changed+=before[i]!=after[i];
                const float r=red(after[i]);
                const float cx=std::clamp((x+0.5f)*64/W-0.5f,0.0f,63.0f);
                const float expected=scene==4 ? 0.0625f : scene==3 ? 1+(0.25f+1.5f*cx/63-1)*z/D : 1.0f;
                if(std::abs(r-expected)>0.025f) throw std::runtime_error("unexpected interpolated air radiance");
                if(z==D-1){lo=std::min(lo,red(before[i]));hi=std::max(hi,red(before[i]));
                          altLo=std::min(altLo,r);altHi=std::max(altHi,r);}
            }
            if ((scene==0||scene==4) && changed) throw std::runtime_error("flat or below-cap volume changed");
            if(scene==1||scene==2) {
                if(changed<W*H*(D-2)||hi-lo<1) throw std::runtime_error("control missed the stale-point pattern");
                if(scene==1) first=after; else if(first!=after) throw std::runtime_error("prior points affected candidate");
            }
            std::printf("%d,%zu,%zu,%.5f,%.5f,%.5f,%.5f\n",scene,after.size(),changed,lo,hi,altLo,altHi);
        }
        return 0;
    } catch(const std::exception& e) {std::fprintf(stderr,"%s\n",e.what());return 1;}
}
