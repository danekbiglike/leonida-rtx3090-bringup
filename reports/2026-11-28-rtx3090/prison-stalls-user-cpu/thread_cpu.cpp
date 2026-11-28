#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <algorithm>
#include <cstdio>
#include <cwchar>
#include <map>
#include <string>

static unsigned long long ticks(FILETIME t) {
    ULARGE_INTEGER value{};
    value.LowPart = t.dwLowDateTime;
    value.HighPart = t.dwHighDateTime;
    return value.QuadPart;
}

struct Thread {
    unsigned long long created, user, kernel;
    std::wstring name;
};

int wmain(int argc, wchar_t** argv) {
    if (argc != 3) return 2;
    DWORD pid = wcstoul(argv[1], nullptr, 10);
    HANDLE process = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!process) return 3;
    wchar_t path[32768];
    DWORD size = 32768;
    if (!QueryFullProcessImageNameW(process, 0, path, &size)) return 4;
    const wchar_t* name = wcsrchr(path, L'\\');
    if (!name || _wcsicmp(name + 1, L"victory.exe")) return 5;
    FILE* output = nullptr;
    if (_wfopen_s(&output, argv[2], L"wx, ccs=UTF-8") || !output) return 6;
    fwprintf(output, L"utc_us,interval_us,thread_id,thread_name,cpu_us,user_us,kernel_us\n");
    SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS);
    std::map<DWORD, Thread> prior;
    unsigned long long last = 0;
    const auto deadline = GetTickCount64() + 25 * 60 * 1000;
    while (GetTickCount64() < deadline && WaitForSingleObject(process, 0) == WAIT_TIMEOUT) {
        HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        if (snapshot == INVALID_HANDLE_VALUE) break;
        FILETIME now;
        GetSystemTimePreciseAsFileTime(&now);
        const auto stamp = ticks(now) / 10 - 11644473600000000ULL;
        std::map<DWORD, Thread> current;
        THREADENTRY32 entry{sizeof(THREADENTRY32)};
        for (BOOL more = Thread32First(snapshot, &entry); more; more = Thread32Next(snapshot, &entry)) {
            if (entry.th32OwnerProcessID != pid) continue;
            HANDLE h = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, entry.th32ThreadID);
            if (!h) continue;
            FILETIME born, exited, kernel, user;
            if (GetThreadTimes(h, &born, &exited, &kernel, &user)) {
                Thread t{ticks(born), ticks(user), ticks(kernel), {}};
                const auto it = prior.find(entry.th32ThreadID);
                const bool known = it != prior.end() && it->second.created == t.created;
                if (known) t.name = it->second.name;
                if (!known || t.name.empty()) {
                    PWSTR description = nullptr;
                    if (SUCCEEDED(GetThreadDescription(h, &description)) && description) {
                        t.name = description;
                        LocalFree(description);
                        for (wchar_t& c : t.name) if (c == L',' || c == L'"' || c == L'\n' || c == L'\r') c = L' ';
                    }
                }
                if (known && last < stamp && t.user >= it->second.user && t.kernel >= it->second.kernel) {
                    const auto user_ticks = t.user - it->second.user;
                    const auto kernel_ticks = t.kernel - it->second.kernel;
                    if (user_ticks || kernel_ticks)
                        fwprintf(output, L"%llu,%llu,%lu,%ls,%llu,%llu,%llu\n", stamp, stamp-last,
                                 entry.th32ThreadID, t.name.c_str(), (user_ticks + kernel_ticks)/10,
                                 user_ticks/10, kernel_ticks/10);
                }
                current.emplace(entry.th32ThreadID, std::move(t));
            }
            CloseHandle(h);
        }
        CloseHandle(snapshot);
        fflush(output);
        prior.swap(current);
        last = stamp;
        if (WaitForSingleObject(process, 1000) != WAIT_TIMEOUT) break;
    }
    fclose(output);
    CloseHandle(process);
    return 0;
}
