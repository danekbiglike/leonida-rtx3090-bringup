#define NOMINMAX
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>

using Microsoft::WRL::ComPtr;
using Bytes = std::array<unsigned char, 1024>;
enum class Mode { separated, global, pair_common, pair_copy };

static void check(HRESULT result, const char* operation) {
    if (FAILED(result)) {
        std::fprintf(stderr, "%s failed: %08lx\n", operation, result);
        throw std::runtime_error(operation);
    }
}

struct Device {
    ComPtr<ID3D12Device> device;
    ComPtr<ID3D12CommandQueue> queue;
    ComPtr<ID3D12Fence> fence;
    ComPtr<ID3D12CommandAllocator> allocator;
    ComPtr<ID3D12GraphicsCommandList7> list;
    HANDLE event = nullptr;
    UINT64 submitted = 0;

    Device() {
        ComPtr<IDXGIFactory6> factory;
        check(CreateDXGIFactory1(IID_PPV_ARGS(&factory)), "factory");
        ComPtr<IDXGIAdapter1> selected;
        for (UINT i = 0; ; ++i) {
            ComPtr<IDXGIAdapter1> adapter;
            HRESULT hr = factory->EnumAdapterByGpuPreference(i, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE, IID_PPV_ARGS(&adapter));
            if (hr == DXGI_ERROR_NOT_FOUND) break;
            check(hr, "enumerate adapter");
            DXGI_ADAPTER_DESC1 desc{};
            check(adapter->GetDesc1(&desc), "adapter description");
            if (std::wstring(desc.Description).find(L"RTX 3090") != std::wstring::npos) {
                std::fprintf(stderr, "adapter: %ls\n", desc.Description);
                selected = adapter;
                break;
            }
        }
        if (!selected) throw std::runtime_error("RTX 3090 not found");
        check(D3D12CreateDevice(selected.Get(), D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&device)), "device");
        D3D12_FEATURE_DATA_D3D12_OPTIONS12 opts{};
        check(device->CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS12, &opts, sizeof(opts)), "options12");
        if (!opts.EnhancedBarriersSupported) throw std::runtime_error("no enhanced barriers");
        D3D12_COMMAND_QUEUE_DESC q{};
        check(device->CreateCommandQueue(&q, IID_PPV_ARGS(&queue)), "queue");
        check(device->CreateFence(0, D3D12_FENCE_FLAG_NONE, IID_PPV_ARGS(&fence)), "fence");
        check(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&allocator)), "allocator");
        check(device->CreateCommandList(0, D3D12_COMMAND_LIST_TYPE_DIRECT, allocator.Get(), nullptr, IID_PPV_ARGS(&list)), "list");
        event = CreateEventW(nullptr, FALSE, FALSE, nullptr);
        if (!event) throw std::runtime_error("event");
    }
    ~Device() { if (event) CloseHandle(event); }
    void submit() {
        check(list->Close(), "close");
        ID3D12CommandList* batch[] = {list.Get()};
        queue->ExecuteCommandLists(1, batch);
        check(queue->Signal(fence.Get(), ++submitted), "signal");
        check(fence->SetEventOnCompletion(submitted, event), "fence event");
        if (WaitForSingleObject(event, 6000) != WAIT_OBJECT_0) throw std::runtime_error("fence timeout");
        check(device->GetDeviceRemovedReason(), "device status");
        check(allocator->Reset(), "reset allocator");
        check(list->Reset(allocator.Get(), nullptr), "reset list");
    }
    ComPtr<ID3D12Resource> buffer(bool readback = false) {
        D3D12_HEAP_PROPERTIES heap{};
        heap.Type = readback ? D3D12_HEAP_TYPE_READBACK : D3D12_HEAP_TYPE_CUSTOM;
        if (!readback) {
            heap.CPUPageProperty = D3D12_CPU_PAGE_PROPERTY_WRITE_BACK;
            heap.MemoryPoolPreference = D3D12_MEMORY_POOL_L0;
        }
        D3D12_RESOURCE_DESC d{};
        d.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
        d.Width = 1024;
        d.Height = 1;
        d.DepthOrArraySize = 1;
        d.MipLevels = 1;
        d.SampleDesc.Count = 1;
        d.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
        d.Flags = readback ? D3D12_RESOURCE_FLAG_NONE : D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
        ComPtr<ID3D12Resource> out;
        check(device->CreateCommittedResource(&heap, D3D12_HEAP_FLAG_NONE, &d,
            readback ? D3D12_RESOURCE_STATE_COPY_DEST : D3D12_RESOURCE_STATE_COMMON, nullptr, IID_PPV_ARGS(&out)), "buffer");
        return out;
    }
};

static void order(Device& device, Mode mode, bool before, ID3D12Resource* from, ID3D12Resource* to) {
    D3D12_GLOBAL_BARRIER global{D3D12_BARRIER_SYNC_ALL,D3D12_BARRIER_SYNC_ALL,D3D12_BARRIER_ACCESS_COMMON,D3D12_BARRIER_ACCESS_COMMON};
    D3D12_BARRIER_GROUP group{};
    std::array<D3D12_BUFFER_BARRIER, 2> buffers{};
    if (mode == Mode::separated) return;
    if (mode == Mode::global) {
        group.Type = D3D12_BARRIER_TYPE_GLOBAL;
        group.NumBarriers = 1;
        group.pGlobalBarriers = &global;
    } else {
        for (size_t i = 0; i < buffers.size(); ++i) {
            const auto access = i ? D3D12_BARRIER_ACCESS_COPY_DEST : D3D12_BARRIER_ACCESS_COPY_SOURCE;
            auto& b = buffers[i];
            b.SyncBefore = !before && mode == Mode::pair_copy ? D3D12_BARRIER_SYNC_COPY : D3D12_BARRIER_SYNC_ALL;
            b.SyncAfter = before && mode == Mode::pair_copy ? D3D12_BARRIER_SYNC_COPY : D3D12_BARRIER_SYNC_ALL;
            b.AccessBefore = !before && mode == Mode::pair_copy ? access : D3D12_BARRIER_ACCESS_COMMON;
            b.AccessAfter = before && mode == Mode::pair_copy ? access : D3D12_BARRIER_ACCESS_COMMON;
            b.pResource = i ? to : from;
            b.Size = UINT64_MAX;
        }
        group.Type = D3D12_BARRIER_TYPE_BUFFER;
        group.NumBarriers = static_cast<UINT>(buffers.size());
        group.pBufferBarriers = buffers.data();
    }
    device.list->Barrier(1, &group);
}

static std::array<unsigned, 2> run(Device& device, Mode mode, unsigned seed) {
    std::array<Bytes,2> expected{};
    std::array<ComPtr<ID3D12Resource>,2> gpu{device.buffer(), device.buffer()};
    std::array<ComPtr<ID3D12Resource>,2> readback{device.buffer(true), device.buffer(true)};
    std::array<unsigned char*,2> mapped{};
    for (size_t i = 0; i < 2; ++i) {
        for (size_t j = 0; j < expected[i].size(); ++j) {
            seed = seed * 1664525u + 1013904223u;
            expected[i][j] = static_cast<unsigned char>(seed >> 24);
        }
        check(gpu[i]->Map(0, nullptr, reinterpret_cast<void**>(&mapped[i])), "map shared");
        std::memcpy(mapped[i], expected[i].data(), expected[i].size());
    }
    for (size_t i = 0; i < 4; ++i) {
        const size_t a = i % 2, b = 1 - a, from = i * 128, to = from + 128;
        order(device, mode, true, gpu[a].Get(), gpu[b].Get());
        device.list->CopyBufferRegion(gpu[b].Get(), to, gpu[a].Get(), from, 64);
        order(device, mode, false, gpu[a].Get(), gpu[b].Get());
        if (mode == Mode::separated) device.submit();
        std::copy_n(expected[a].begin() + from, 64, expected[b].begin() + to);
    }
    if (mode != Mode::separated) device.submit();
    for (size_t i = 0; i < 2; ++i) {
        device.list->CopyBufferRegion(readback[i].Get(), 0, gpu[i].Get(), 0, expected[i].size());
    }
    device.submit();
    std::array<unsigned,2> errors{};
    for (size_t i = 0; i < 2; ++i) {
        unsigned char* observed = nullptr;
        D3D12_RANGE range{0, expected[i].size()};
        check(readback[i]->Map(0, &range, reinterpret_cast<void**>(&observed)), "map results");
        for (size_t j = 0; j < expected[i].size(); ++j) {
            errors[0] += mapped[i][j] != expected[i][j];
            errors[1] += observed[j] != expected[i][j];
        }
        D3D12_RANGE nothing{0,0};
        readback[i]->Unmap(0, &nothing);
        gpu[i]->Unmap(0, &nothing);
    }
    return errors;
}

int main() {
    try {
        Device d;
        std::puts("mode,iteration,mapped_mismatches,readback_mismatches");
        const char* labels[] = {"fence-between-copies","global-common","buffer-common","buffer-copy-access"};
        bool controls_and_copy_access_match = true;
        for (unsigned m = 0; m < 4; ++m) {
            for (unsigned rep = 0; rep < 5; ++rep) {
                const auto errors = run(d, static_cast<Mode>(m), rep + 1771);
                std::printf("%s,%u,%u,%u\n", labels[m], rep + 1, errors[0], errors[1]);
                if (static_cast<Mode>(m) != Mode::pair_common && (errors[0] || errors[1])) {
                    controls_and_copy_access_match = false;
                }
            }
        }
        return controls_and_copy_access_match ? 0 : 2;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "%s\n", e.what());
        return 1;
    }
}
