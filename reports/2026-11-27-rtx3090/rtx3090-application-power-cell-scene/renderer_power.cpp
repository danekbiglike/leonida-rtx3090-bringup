// Read or test a single renderer's documented NVIDIA application power preference.
#include <windows.h>
#include <algorithm>
#include <cstdio>
#include <cwchar>
#include <stdexcept>
#include <string>
#include "nvapi.h"
#include "NvApiDriverSettings.h"

constexpr wchar_t testProfile[] = L"VIctory RTX3090 local route measurement";
constexpr wchar_t marker[] = L"rtx3090-escort-power-test.tag";
constexpr wchar_t testImage[] = L"victory-rtx3090-power.exe";

void setText(NvAPI_UnicodeString& target, const wchar_t* value) {
    const auto length = std::wcslen(value);
    if (length >= std::size(target)) throw std::runtime_error("Driver profile text is too long");
    std::copy_n(value, length + 1, target);
}

std::wstring asText(const NvAPI_UnicodeString& value) {
    return std::wstring(value, std::find(std::begin(value), std::end(value), 0));
}

void check(NvAPI_Status status) {
    if (status == NVAPI_OK) return;
    NvAPI_ShortString msg{};
    NvAPI_GetErrorMessage(status, msg);
    std::fprintf(stderr, "NVIDIA status %d: %s\n", status, msg);
    throw std::runtime_error("NVIDIA driver operation failed");
}

NvDRSProfileHandle match(NvDRSSessionHandle session, const wchar_t* path) {
    NvAPI_UnicodeString name{};
    setText(name, path);
    NVDRS_APPLICATION app{};
    app.version = NVDRS_APPLICATION_VER;
    NvDRSProfileHandle profile{};
    auto code = NvAPI_DRS_FindApplicationByName(session, name, &profile, &app);
    if (code == NVAPI_EXECUTABLE_NOT_FOUND) return nullptr;
    check(code);
    return profile;
}

int wmain(int argc, wchar_t** argv) {
    if (argc != 4) return 2;
    const wchar_t* slash = std::wcsrchr(argv[2], L'\\');
    if (!slash || _wcsicmp(slash + 1, testImage) || !_wcsicmp(argv[2], argv[3])) return 2;
    NvDRSSessionHandle session{};
    try {
        check(NvAPI_Initialize());
        check(NvAPI_DRS_CreateSession(&session));
        check(NvAPI_DRS_LoadSettings(session));
        NvAPI_UnicodeString name{};
        setText(name, testProfile);
        NvDRSProfileHandle own{};
        auto found = NvAPI_DRS_FindProfileByName(session, name, &own);
        if (found != NVAPI_PROFILE_NOT_FOUND) check(found);
        auto game = match(session, argv[2]);
        auto control = match(session, argv[3]);
        if (!wcscmp(argv[1], L"query")) {
            auto selected = game;
            if (!selected) check(NvAPI_DRS_GetCurrentGlobalProfile(session, &selected));
            NVDRS_SETTING setting{};
            setting.version = NVDRS_SETTING_VER;
            const auto status = NvAPI_DRS_GetSetting(session, selected, PREFERRED_PSTATE_ID, &setting);
            if (status != NVAPI_SETTING_NOT_FOUND) check(status);
            std::printf("matched_profile=%d test_profile=%d control_matches_test=%d explicit_power=%d value=%u\n",
                        !!game, own && game == own, own && control == own, status == NVAPI_OK,
                        status == NVAPI_OK ? setting.u32CurrentValue : 0);
        } else if (!wcscmp(argv[1], L"enable")) {
            if (own) throw std::runtime_error("The measurement profile already exists");
            NVDRS_PROFILE profile{};
            profile.version = NVDRS_PROFILE_VER;
            setText(profile.profileName, testProfile);
            check(NvAPI_DRS_CreateProfile(session, &profile, &own));
            NVDRS_APPLICATION app{};
            app.version = NVDRS_APPLICATION_VER;
            setText(app.appName, testImage);
            setText(app.fileInFolder, marker);
            check(NvAPI_DRS_CreateApplication(session, own, &app));
            NVDRS_SETTING setting{};
            setting.version = NVDRS_SETTING_VER;
            setting.settingId = PREFERRED_PSTATE_ID;
            setting.settingType = NVDRS_DWORD_TYPE;
            setting.u32CurrentValue = PREFERRED_PSTATE_PREFER_MAX;
            check(NvAPI_DRS_SetSetting(session, own, &setting));
            if (match(session, argv[2]) != own || match(session, argv[3]) != control)
                throw std::runtime_error("Selective renderer match failed; changes were not saved");
            check(NvAPI_DRS_SaveSettings(session));
            std::puts("Saved marker-specific renderer profile.");
        } else if (!wcscmp(argv[1], L"restore")) {
            if (own) {
                NVDRS_PROFILE profile{};
                profile.version = NVDRS_PROFILE_VER;
                check(NvAPI_DRS_GetProfileInfo(session, own, &profile));
                NVDRS_APPLICATION app{};
                app.version = NVDRS_APPLICATION_VER;
                NvU32 count = 1;
                check(NvAPI_DRS_EnumApplications(session, own, 0, &count, &app));
                if (profile.isPredefined || profile.numOfApps != 1 || profile.numOfSettings != 1 ||
                    count != 1 || _wcsicmp(asText(app.appName).c_str(), testImage) || _wcsicmp(asText(app.fileInFolder).c_str(), marker))
                    throw std::runtime_error("Profile contents changed; preserving it");
                check(NvAPI_DRS_DeleteProfile(session, own));
                check(NvAPI_DRS_SaveSettings(session));
            }
            std::puts("No measurement profile remains.");
        } else {
            throw std::runtime_error("Expected query, enable or restore");
        }
        check(NvAPI_DRS_DestroySession(session));
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "%s\n", error.what());
        if (session) NvAPI_DRS_DestroySession(session);
        return 1;
    }
}
