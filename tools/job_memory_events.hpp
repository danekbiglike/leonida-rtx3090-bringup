// A launcher can attach this to its own empty Windows job before assigning the child.
#pragma once
#include <windows.h>
#include <cstdio>

class JobMemoryEvents {
public:
    JobMemoryEvents() = default;
    JobMemoryEvents(const JobMemoryEvents&) = delete;
    JobMemoryEvents& operator=(const JobMemoryEvents&) = delete;
    ~JobMemoryEvents() {
        if (port_) CloseHandle(port_);
    }

    bool attach(HANDLE job) {
        port_ = CreateIoCompletionPort(INVALID_HANDLE_VALUE, nullptr, 0, 1);
        if (!port_) return false;
        JOBOBJECT_ASSOCIATE_COMPLETION_PORT association{this, port_};
        return SetInformationJobObject(job, JobObjectAssociateCompletionPortInformation,
                                       &association, sizeof(association)) != FALSE;
    }

    // Call on the launcher's sampling thread, and once after the child exits.
    // Hard-limit notifications are best effort. An observed event identifies the limit.
    unsigned drain(DWORD child_pid, FILE* output, ULONGLONG elapsed_ms) {
        unsigned hits = 0;
        DWORD message;
        ULONG_PTR key;
        OVERLAPPED* process_id;
        while (GetQueuedCompletionStatus(port_, &message, &key, &process_id, 0)) {
            if (key != reinterpret_cast<ULONG_PTR>(this) ||
                reinterpret_cast<ULONG_PTR>(process_id) != child_pid) continue;
            if (message == JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT ||
                message == JOB_OBJECT_MSG_JOB_MEMORY_LIMIT) {
                ++hits;
                std::fprintf(output, "%llu,%lu\n", elapsed_ms, message);
                std::fflush(output);
            }
        }
        return hits;
    }
private:
    HANDLE port_ = nullptr;
};
