// Compile with x64 MSVC and run. Only the child created here receives a 32 MiB limit.
#include "job_memory_events.hpp"
#include <string>

static int child_allocation() {
    for (unsigned n = 0; n < 48; ++n) {
        if (!VirtualAlloc(nullptr, 1 << 20, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE)) {
            const DWORD error = GetLastError();
            return error == ERROR_COMMITMENT_LIMIT || error == ERROR_NOT_ENOUGH_MEMORY
                || error == ERROR_NOT_ENOUGH_QUOTA ? 71 : 72;
        }
    }
    return 73;
}

int wmain(int argc, wchar_t** argv) {
    if (argc == 2 && std::wstring(argv[1]) == L"--child") return child_allocation();
    if (argc != 1) return 2;
    HANDLE job = CreateJobObjectW(nullptr, nullptr);
    JobMemoryEvents events;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    limits.ProcessMemoryLimit = 32ULL << 20;
    if (!job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))
        || !events.attach(job)) return 3;
    wchar_t image[32768]{};
    if (!GetModuleFileNameW(nullptr, image, ARRAYSIZE(image))) return 4;
    std::wstring arguments = L"\"" + std::wstring(image) + L"\" --child";
    STARTUPINFOW startup{}; startup.cb = sizeof(startup);
    PROCESS_INFORMATION proc{};
    if (!CreateProcessW(image, arguments.data(), nullptr, nullptr, FALSE,
                        CREATE_SUSPENDED | CREATE_NO_WINDOW, nullptr, nullptr, &startup, &proc)) return 5;
    if (!AssignProcessToJobObject(job, proc.hProcess) || ResumeThread(proc.hThread) == DWORD(-1)) {
        TerminateProcess(proc.hProcess, 6);
        return 6;
    }
    const auto start = GetTickCount64();
    unsigned hits = 0;
    DWORD wait;
    do {
        hits += events.drain(proc.dwProcessId, stdout, GetTickCount64() - start);
        wait = WaitForSingleObject(proc.hProcess, 10);
    } while (wait == WAIT_TIMEOUT && GetTickCount64() - start < 5000);
    hits += events.drain(proc.dwProcessId, stdout, GetTickCount64() - start);
    DWORD result = 0;
    const bool expected = wait == WAIT_OBJECT_0 && GetExitCodeProcess(proc.hProcess, &result) && result == 71;
    std::printf("allocation_denied=%u memory_limit_notifications=%u\n", unsigned(expected), hits);
    CloseHandle(job); CloseHandle(proc.hProcess); CloseHandle(proc.hThread);
    return expected && hits > 0 ? 0 : 7;
}
