#include <windows.h>
#include <d3d12.h>
#include <d3dcompiler.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

using Microsoft::WRL::ComPtr;
constexpr UINT pointsBytes = 160 * 90 * 3 * 16;

static void check(HRESULT result) {
    if (FAILED(result)) {
        char message[32];
        std::snprintf(message, sizeof(message), "HRESULT 0x%08lx", static_cast<unsigned long>(result));
        throw std::runtime_error(message);
    }
}

static ComPtr<ID3DBlob> compile(const std::string& source, const char* entry) {
    ComPtr<ID3DBlob> code, errors;
    const HRESULT hr = D3DCompile(source.data(), source.size(), "victory", nullptr, nullptr, entry,
                                  "cs_5_1", 0, 0, &code, &errors);
    if (FAILED(hr) && errors) std::fprintf(stderr, "%s\n", static_cast<const char*>(errors->GetBufferPointer()));
    check(hr);
    return code;
}

struct Gpu {
    ComPtr<ID3D12Device> device;
    ComPtr<ID3D12CommandQueue> queue;
    ComPtr<ID3D12CommandAllocator> allocator;
    ComPtr<ID3D12GraphicsCommandList> list;
    ComPtr<ID3D12Fence> fence;
    UINT64 serial = 0, frequency = 0;
    HANDLE event = nullptr;

    Gpu() {
        ComPtr<IDXGIFactory1> factory;
        check(CreateDXGIFactory1(IID_PPV_ARGS(&factory)));
        for (UINT index = 0; ; ++index) {
            ComPtr<IDXGIAdapter1> adapter;
            HRESULT hr = factory->EnumAdapters1(index, &adapter);
            if (hr == DXGI_ERROR_NOT_FOUND) throw std::runtime_error("RTX 3090 unavailable");
            check(hr);
            DXGI_ADAPTER_DESC1 desc{};
            check(adapter->GetDesc1(&desc));
            if (desc.VendorId != 0x10de || !std::wcsstr(desc.Description, L"RTX 3090")) continue;
            check(D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&device)));
            break;
        }
        D3D12_COMMAND_QUEUE_DESC q{};
        q.Type = D3D12_COMMAND_LIST_TYPE_DIRECT;
        check(device->CreateCommandQueue(&q, IID_PPV_ARGS(&queue)));
        check(queue->GetTimestampFrequency(&frequency));
        check(device->CreateCommandAllocator(q.Type, IID_PPV_ARGS(&allocator)));
        check(device->CreateCommandList(0, q.Type, allocator.Get(), nullptr, IID_PPV_ARGS(&list)));
        check(device->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence)));
        event = CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (!event) throw std::runtime_error("Could not create completion event");
    }
    ~Gpu() { if (event) CloseHandle(event); }
    void submit() {
        check(list->Close());
        ID3D12CommandList* lists[]{list.Get()};
        queue->ExecuteCommandLists(1, lists);
        check(queue->Signal(fence.Get(), ++serial));
        check(fence->SetEventOnCompletion(serial, event));
        if (WaitForSingleObject(event, 12000) != WAIT_OBJECT_0) throw std::runtime_error("GPU timeout");
        check(device->GetDeviceRemovedReason());
        check(allocator->Reset());
        check(list->Reset(allocator.Get(), nullptr));
    }
    ComPtr<ID3D12Resource> resource(UINT64 bytes, bool texture = false, bool readback = false) {
        D3D12_HEAP_PROPERTIES heap{};
        heap.Type = readback ? D3D12_HEAP_TYPE_READBACK : D3D12_HEAP_TYPE_DEFAULT;
        heap.CreationNodeMask = heap.VisibleNodeMask = 1;
        D3D12_RESOURCE_DESC desc{};
        desc.Dimension = texture ? D3D12_RESOURCE_DIMENSION_TEXTURE2D : D3D12_RESOURCE_DIMENSION_BUFFER;
        desc.Width = texture ? 320 : bytes;
        desc.Height = texture ? 180 : 1;
        desc.DepthOrArraySize = desc.MipLevels = desc.SampleDesc.Count = 1;
        desc.Format = texture ? DXGI_FORMAT_R32_FLOAT : DXGI_FORMAT_UNKNOWN;
        desc.Layout = texture ? D3D12_TEXTURE_LAYOUT_UNKNOWN : D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
        if (!readback) desc.Flags = D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
        ComPtr<ID3D12Resource> result;
        check(device->CreateCommittedResource(&heap, D3D12_HEAP_FLAG_NONE, &desc,
            readback ? D3D12_RESOURCE_STATE_COPY_DEST : D3D12_RESOURCE_STATE_UNORDERED_ACCESS,
            nullptr, IID_PPV_ARGS(&result)));
        return result;
    }
    void transition(ID3D12Resource* resource, D3D12_RESOURCE_STATES before, D3D12_RESOURCE_STATES after) {
        D3D12_RESOURCE_BARRIER b{};
        b.Type = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
        b.Transition = {resource, D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES, before, after};
        list->ResourceBarrier(1, &b);
    }
    void barrier() {
        D3D12_RESOURCE_BARRIER b{};
        b.Type = D3D12_RESOURCE_BARRIER_TYPE_UAV;
        list->ResourceBarrier(1, &b);
    }
};

static std::string shader_source(const std::filesystem::path& path) {
    std::ifstream file(path);
    std::string all{std::istreambuf_iterator<char>(file), {}};
    const std::string start = "const SOURCE: &str = r#\"";
    const auto at = all.find(start);
    if (at == all.npos) throw std::runtime_error("Missing shader source");
    const auto end = all.find("\"#;", at + start.size());
    if (end == all.npos) throw std::runtime_error("Missing shader terminator");
    return all.substr(at + start.size(), end - at - start.size());
}

static int run(const std::filesystem::path& path) {
    const std::string source = shader_source(path);
    if (source.find("[numthreads(GATHER_WIDTH, 2, 1)]\nvoid gather(") == source.npos)
        throw std::runtime_error("Expected renderer's parametrized gather shader");
    Gpu g;
    std::array<UINT, 3> widths{8, 16, 32};
    std::array<ComPtr<ID3D12PipelineState>, 3> variants;
    ComPtr<ID3D12RootSignature> root;
    auto pipeline = [&](const std::string& text, const char* entry) {
        const auto shader = compile(text, entry);
        if (!root) check(g.device->CreateRootSignature(0, shader->GetBufferPointer(), shader->GetBufferSize(), IID_PPV_ARGS(&root)));
        D3D12_COMPUTE_PIPELINE_STATE_DESC desc{};
        desc.pRootSignature = root.Get();
        desc.CS = {shader->GetBufferPointer(), shader->GetBufferSize()};
        ComPtr<ID3D12PipelineState> result;
        check(g.device->CreateComputePipelineState(&desc, IID_PPV_ARGS(&result)));
        return result;
    };
    for (size_t i = 0; i < widths.size(); ++i) {
        variants[i] = pipeline("#define GATHER\n#define GATHER_WIDTH " + std::to_string(widths[i]) + "\n" + source, "gather");
    }
    const std::string seedCode = R"(
RWTexture2D<float> depthOut : register(u0);
[RootSignature(RS)]
[numthreads(8, 4, 1)]
void seed(uint3 at : SV_DispatchThreadID) {
    float scene = level;
    depthOut[at.xy] = 0.0005 + 0.08 * frac((at.x*7u + at.y*9u + (uint)scene*11u) / 173.0);
    uint i = at.y * 320 + at.x;
    if (i < CELLS) {
        float z = 1.0 + (i % 113) * (0.12 + 0.09 * scene);
        cells[i] = float4((i % 11) / 4.0, (i % 19) / 8.0, 0.1 + (i % 29) * scene, 1);
        cells[CELLS + 1 + i] = float4(((i % CX)-31.5)*z/40, ((i / CX)-17.5)*z/40, z, z*z);
    }
    if (i < 160*90*3) points[i] = float4(-scene,-scene,-scene,-scene);
})";
    auto seed = pipeline(source + seedCode, "seed");
    auto depth = g.resource(0, true), cells = g.resource((4608 + 1) * 16), output = g.resource(pointsBytes);
    auto back = g.resource(pointsBytes + 16, false, true);
    D3D12_DESCRIPTOR_HEAP_DESC hd{D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV, 2, D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE, 0};
    ComPtr<ID3D12DescriptorHeap> views;
    check(g.device->CreateDescriptorHeap(&hd, IID_PPV_ARGS(&views)));
    auto depthCpu = views->GetCPUDescriptorHandleForHeapStart();
    auto depthGpu = views->GetGPUDescriptorHandleForHeapStart();
    auto uavCpu = depthCpu;
    auto uavGpu = depthGpu;
    const UINT step = g.device->GetDescriptorHandleIncrementSize(hd.Type);
    uavCpu.ptr += step;
    uavGpu.ptr += step;
    g.device->CreateShaderResourceView(depth.Get(), nullptr, depthCpu);
    g.device->CreateUnorderedAccessView(depth.Get(), nullptr, nullptr, uavCpu);
    D3D12_QUERY_HEAP_DESC qd{D3D12_QUERY_HEAP_TYPE_TIMESTAMP, 2, 0};
    ComPtr<ID3D12QueryHeap> ticks;
    check(g.device->CreateQueryHeap(&qd, IID_PPV_ARGS(&ticks)));
    std::puts("scene,round,group_width,group_height,gpu_us,verified_bytes");
    for (int scene = 1; scene <= 2; ++scene) {
        std::vector<unsigned char> reference(pointsBytes);
        for (int round = -1; round < 9; ++round) {
            for (int order = 0; order < 3; ++order) {
                const int index = round < 0 ? order : (round + order) % 3;
                const UINT width = widths[index];
                ID3D12DescriptorHeap* heaps[]{views.Get()};
                g.list->SetDescriptorHeaps(1, heaps);
                g.list->SetComputeRootSignature(root.Get());
                const float base[]{float(scene),0,0,0,0.1f,0.45f};
                UINT words[12]{};
                std::memcpy(words, base, sizeof(base));
                words[6] = 320; words[7] = 180;
                g.list->SetComputeRoot32BitConstants(0, 12, words, 0);
                g.list->SetComputeRootDescriptorTable(1, depthGpu);
                g.list->SetComputeRootDescriptorTable(2, uavGpu);
                g.list->SetComputeRootUnorderedAccessView(3, cells->GetGPUVirtualAddress());
                g.list->SetComputeRootUnorderedAccessView(4, output->GetGPUVirtualAddress());
                g.list->SetPipelineState(seed.Get());
                g.list->Dispatch(40,45,1);
                g.barrier();
                g.transition(depth.Get(), D3D12_RESOURCE_STATE_UNORDERED_ACCESS, D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE);
                g.list->SetPipelineState(variants[index].Get());
                g.list->EndQuery(ticks.Get(), D3D12_QUERY_TYPE_TIMESTAMP, 0);
                g.list->Dispatch(160 / width,45,1);
                g.barrier();
                g.list->EndQuery(ticks.Get(), D3D12_QUERY_TYPE_TIMESTAMP, 1);
                g.list->ResolveQueryData(ticks.Get(), D3D12_QUERY_TYPE_TIMESTAMP, 0, 2, back.Get(), pointsBytes);
                g.transition(output.Get(), D3D12_RESOURCE_STATE_UNORDERED_ACCESS, D3D12_RESOURCE_STATE_COPY_SOURCE);
                g.list->CopyBufferRegion(back.Get(), 0, output.Get(), 0, pointsBytes);
                g.transition(output.Get(), D3D12_RESOURCE_STATE_COPY_SOURCE, D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
                g.transition(depth.Get(), D3D12_RESOURCE_STATE_NON_PIXEL_SHADER_RESOURCE, D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
                g.submit();
                void* data = nullptr;
                const D3D12_RANGE read{0, pointsBytes + 16};
                check(back->Map(0, &read, &data));
                UINT64 times[2];
                std::memcpy(times, static_cast<char*>(data) + pointsBytes, sizeof(times));
                if (round == -1 && order == 0) {
                    auto values = static_cast<const float*>(data);
                    for (UINT i = 0; i < pointsBytes / sizeof(float); ++i)
                        if (!std::isfinite(values[i]) || (i % 4 == 3 && values[i] <= 0))
                            throw std::runtime_error("Invalid baseline light coefficients");
                    std::memcpy(reference.data(), data, pointsBytes);
                } else if (std::memcmp(reference.data(), data, pointsBytes) != 0) {
                    throw std::runtime_error("Gather output differs from the original");
                }
                const D3D12_RANGE none{0,0};
                back->Unmap(0, &none);
                if (times[1] <= times[0]) throw std::runtime_error("Invalid GPU timestamps");
                if (round >= 0) std::printf("%d,%d,%u,2,%.3f,%u\n", scene, round, width,
                    (times[1] - times[0]) * 1e6 / g.frequency, pointsBytes);
            }
        }
    }
    return 0;
}

int wmain(int argc, wchar_t** argv) {
    if (argc != 2) return 2;
    try { return run(argv[1]); }
    catch (const std::exception& error) { std::fprintf(stderr, "%s\n", error.what()); return 1; }
}
