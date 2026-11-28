#pragma once
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
    ComPtr<ID3D12Resource> resource(UINT64 bytes, bool readback = false, DXGI_FORMAT format = DXGI_FORMAT_UNKNOWN, UINT width = 0, UINT height = 0) {
        const bool texture = format != DXGI_FORMAT_UNKNOWN;
        D3D12_HEAP_PROPERTIES heap{};
        heap.Type = readback ? D3D12_HEAP_TYPE_READBACK : D3D12_HEAP_TYPE_DEFAULT;
        heap.CreationNodeMask = heap.VisibleNodeMask = 1;
        D3D12_RESOURCE_DESC desc{};
        desc.Dimension = texture ? D3D12_RESOURCE_DIMENSION_TEXTURE2D : D3D12_RESOURCE_DIMENSION_BUFFER;
        desc.Width = texture ? width : bytes;
        desc.Height = texture ? height : 1;
        desc.DepthOrArraySize = 1;
        desc.MipLevels = 1;
        desc.SampleDesc.Count = 1;
        desc.Format = format;
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
