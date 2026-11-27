// danekbiglike / leonida-rtx3090-bringup / delayed-directory-slot-v1
// D3D12 API lifetime control. No game files, instructions or shaders are used.
#include <windows.h>
#include <d3d12.h>
#include <d3dcompiler.h>
#include <dxgi1_4.h>
#include <wrl/client.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>

using Microsoft::WRL::ComPtr;

static void check(HRESULT hr, const char* call) {
    if (FAILED(hr)) {
        std::fprintf(stderr, "%s: HRESULT 0x%08lx\n", call, static_cast<unsigned long>(hr));
        throw std::runtime_error(call);
    }
}
#define CHECK(call) check((call), #call)

static ComPtr<ID3D12Resource> buffer(ID3D12Device* device, D3D12_HEAP_TYPE type,
                                     D3D12_RESOURCE_STATES state, D3D12_RESOURCE_FLAGS flags) {
    D3D12_HEAP_PROPERTIES heap{};
    heap.Type = type;
    heap.CreationNodeMask = heap.VisibleNodeMask = 1;
    D3D12_RESOURCE_DESC desc{};
    desc.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
    desc.Width = 256;
    desc.Height = desc.DepthOrArraySize = desc.MipLevels = desc.SampleDesc.Count = 1;
    desc.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
    desc.Flags = flags;
    ComPtr<ID3D12Resource> value;
    CHECK(device->CreateCommittedResource(&heap, D3D12_HEAP_FLAG_NONE, &desc, state,
                                          nullptr, IID_PPV_ARGS(value.GetAddressOf())));
    return value;
}

static void fill(ID3D12Resource* upload, uint32_t value) {
    void* bytes = nullptr;
    D3D12_RANGE noRead{};
    CHECK(upload->Map(0, &noRead, &bytes));
    std::memcpy(bytes, &value, sizeof(value));
    D3D12_RANGE written{0, sizeof(value)};
    upload->Unmap(0, &written);
}

int main() try {
    ComPtr<IDXGIFactory4> factory;
    ComPtr<IDXGIAdapter> warp;
    ComPtr<ID3D12Device> device;
    CHECK(CreateDXGIFactory1(IID_PPV_ARGS(factory.GetAddressOf())));
    CHECK(factory->EnumWarpAdapter(IID_PPV_ARGS(warp.GetAddressOf())));
    CHECK(D3D12CreateDevice(warp.Get(), D3D_FEATURE_LEVEL_11_0, IID_PPV_ARGS(device.GetAddressOf())));

    D3D12_COMMAND_QUEUE_DESC queueDesc{};
    ComPtr<ID3D12CommandQueue> queue;
    ComPtr<ID3D12Fence> fence;
    CHECK(device->CreateCommandQueue(&queueDesc, IID_PPV_ARGS(queue.GetAddressOf())));
    CHECK(device->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(fence.GetAddressOf())));
    uint64_t serial = 0;
    auto waitQueue = [&] {
        CHECK(queue->Signal(fence.Get(), ++serial));
        // A null event makes this call wait synchronously.
        CHECK(fence->SetEventOnCompletion(serial, nullptr));
        if (fence->GetCompletedValue() != serial) throw std::runtime_error("fence");
    };

    D3D12_DESCRIPTOR_HEAP_DESC heapDesc{};
    heapDesc.Type = D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV;
    heapDesc.NumDescriptors = 2;
    heapDesc.Flags = D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE;
    ComPtr<ID3D12DescriptorHeap> descriptors;
    CHECK(device->CreateDescriptorHeap(&heapDesc, IID_PPV_ARGS(descriptors.GetAddressOf())));
    const UINT stride = device->GetDescriptorHandleIncrementSize(heapDesc.Type);
    const auto cpu = descriptors->GetCPUDescriptorHandleForHeapStart();
    const auto gpu = descriptors->GetGPUDescriptorHandleForHeapStart();
    auto a = buffer(device.Get(), D3D12_HEAP_TYPE_UPLOAD, D3D12_RESOURCE_STATE_GENERIC_READ, D3D12_RESOURCE_FLAG_NONE);
    auto b = buffer(device.Get(), D3D12_HEAP_TYPE_UPLOAD, D3D12_RESOURCE_STATE_GENERIC_READ, D3D12_RESOURCE_FLAG_NONE);
    constexpr uint32_t oldValue = 0x30900001, newValue = 0x30900002;
    fill(a.Get(), oldValue);
    fill(b.Get(), newValue);
    auto set = [&](UINT slot, ID3D12Resource* resource) {
        D3D12_SHADER_RESOURCE_VIEW_DESC desc{};
        desc.ViewDimension = D3D12_SRV_DIMENSION_BUFFER;
        desc.Format = DXGI_FORMAT_R32_UINT;
        desc.Shader4ComponentMapping = D3D12_DEFAULT_SHADER_4_COMPONENT_MAPPING;
        desc.Buffer.NumElements = 1;
        device->CreateShaderResourceView(resource, &desc, {cpu.ptr + slot * stride});
    };
    set(0, a.Get());
    set(1, a.Get());

    D3D12_DESCRIPTOR_RANGE1 range{};
    range.RangeType = D3D12_DESCRIPTOR_RANGE_TYPE_SRV;
    range.NumDescriptors = 1;
    range.Flags = D3D12_DESCRIPTOR_RANGE_FLAG_DESCRIPTORS_VOLATILE;
    D3D12_ROOT_PARAMETER1 params[2]{};
    params[0].ParameterType = D3D12_ROOT_PARAMETER_TYPE_DESCRIPTOR_TABLE;
    params[0].DescriptorTable = {1, &range};
    params[1].ParameterType = D3D12_ROOT_PARAMETER_TYPE_UAV;
    params[1].Descriptor.Flags = D3D12_ROOT_DESCRIPTOR_FLAG_DATA_VOLATILE;
    D3D12_VERSIONED_ROOT_SIGNATURE_DESC rootDesc{};
    rootDesc.Version = D3D_ROOT_SIGNATURE_VERSION_1_1;
    rootDesc.Desc_1_1.NumParameters = 2;
    rootDesc.Desc_1_1.pParameters = params;
    ComPtr<ID3DBlob> serialized, shader;
    CHECK(D3D12SerializeVersionedRootSignature(&rootDesc, serialized.GetAddressOf(), nullptr));
    ComPtr<ID3D12RootSignature> root;
    CHECK(device->CreateRootSignature(0, serialized->GetBufferPointer(), serialized->GetBufferSize(),
                                      IID_PPV_ARGS(root.GetAddressOf())));
    const char hlsl[] = "Buffer<uint> inputValue : register(t0);"
        "RWByteAddressBuffer outputValue : register(u0);"
        "[numthreads(1,1,1)] void main() { outputValue.Store(0,inputValue[0]); }";
    CHECK(D3DCompile(hlsl, sizeof(hlsl) - 1, nullptr, nullptr, nullptr, "main", "cs_5_0", 0, 0,
                     shader.GetAddressOf(), nullptr));
    D3D12_COMPUTE_PIPELINE_STATE_DESC pipelineDesc{};
    pipelineDesc.pRootSignature = root.Get();
    pipelineDesc.CS = {shader->GetBufferPointer(), shader->GetBufferSize()};
    ComPtr<ID3D12PipelineState> pipeline;
    CHECK(device->CreateComputePipelineState(&pipelineDesc, IID_PPV_ARGS(pipeline.GetAddressOf())));
    auto output0 = buffer(device.Get(), D3D12_HEAP_TYPE_DEFAULT, D3D12_RESOURCE_STATE_UNORDERED_ACCESS,
                          D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
    auto output1 = buffer(device.Get(), D3D12_HEAP_TYPE_DEFAULT, D3D12_RESOURCE_STATE_UNORDERED_ACCESS,
                          D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
    auto readback = buffer(device.Get(), D3D12_HEAP_TYPE_READBACK, D3D12_RESOURCE_STATE_COPY_DEST, D3D12_RESOURCE_FLAG_NONE);
    ComPtr<ID3D12CommandAllocator> allocator;
    ComPtr<ID3D12GraphicsCommandList> held;
    CHECK(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(allocator.GetAddressOf())));
    CHECK(device->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, allocator.Get(), pipeline.Get(),
                                    IID_PPV_ARGS(held.GetAddressOf())));
    held->SetComputeRootSignature(root.Get());
    ID3D12DescriptorHeap* heaps[] = {descriptors.Get()};
    held->SetDescriptorHeaps(1, heaps);
    ID3D12Resource* outputs[] = {output0.Get(), output1.Get()};
    for (UINT slot = 0; slot < 2; ++slot) {
        held->SetComputeRootDescriptorTable(0, {gpu.ptr + slot * stride});
        held->SetComputeRootUnorderedAccessView(1, outputs[slot]->GetGPUVirtualAddress());
        held->Dispatch(1, 1, 1);
        D3D12_RESOURCE_BARRIER barrier{};
        barrier.Transition = {outputs[slot], 0, D3D12_RESOURCE_STATE_UNORDERED_ACCESS, D3D12_RESOURCE_STATE_COPY_SOURCE};
        held->ResourceBarrier(1, &barrier);
        held->CopyBufferRegion(readback.Get(), sizeof(uint32_t) * slot, outputs[slot], 0, sizeof(uint32_t));
    }
    CHECK(held->Close());
    // Real queue fences can advance without ever covering this closed list.
    for (int step = 0; step < 16; ++step) waitQueue();
    set(0, b.Get());
    ID3D12CommandList* submitted[] = {held.Get()};
    queue->ExecuteCommandLists(1, submitted);
    waitQueue();
    D3D12_RANGE read{0, 2 * sizeof(uint32_t)};
    void* bytes = nullptr;
    CHECK(readback->Map(0, &read, &bytes));
    uint32_t values[2]{};
    std::memcpy(values, bytes, sizeof(values));
    D3D12_RANGE noWrite{};
    readback->Unmap(0, &noWrite);
    std::printf("danekbiglike/delayed-directory-slot-v1 WARP completed_before_submit=16 "
                "reused=0x%08x retained=0x%08x\n", values[0], values[1]);
    return values[0] == newValue && values[1] == oldValue ? 0 : 1;
} catch (const std::exception& ex) {
    std::fprintf(stderr, "%s\n", ex.what());
    return 2;
}
